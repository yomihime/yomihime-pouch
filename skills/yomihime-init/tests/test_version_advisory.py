"""Read-only comparison fixtures; no installation, networking, or publication."""
import importlib.util
import io
from contextlib import ExitStack, redirect_stdout
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from version_test_processes import IsolatedProcesses, minimal_environment

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'version_advisory.py'
SPEC = importlib.util.spec_from_file_location('version_advisory', SCRIPT)
advisory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(advisory)
REPO = SCRIPT.parents[3]
PYTHON = str(Path(os.sys.executable).resolve())
GIT = str(Path(shutil.which('git')).resolve()) if shutil.which('git') else None


def skill_text(version='1.0.0', updated_at='2026-11-04T12:24:49Z', name='example'):
    return (f'---\nname: {name}\ndescription: >-\n  Test skill.\nmetadata:\n'
            f'  version: "{version}"\n  updated_at: "{updated_at}"\n---\n# Test\n')


class VersionGrammarTests(unittest.TestCase):
    def test_integer_comparison_not_text_order(self):
        self.assertGreater(advisory.parse_version('1.10.0'), advisory.parse_version('1.9.9'))
        self.assertGreater(advisory.parse_version('10.0.0'), advisory.parse_version('9.999.999'))
        self.assertEqual(advisory.parse_version('999999999.0.42'), (999999999, 0, 42))
        self.assertEqual(advisory.parse_version('0.0.0'), (0, 0, 0))

    def test_invalid_and_unbounded_versions_are_unknown(self):
        for value in (None, 1, 1.0, True, [], {}, '', '1', '1.2', '1.2.3.4', '01.2.3',
                      '1.02.3', '1.2.03', 'v1.2.3', '1.2.3-rc.1', '1.2.3+build',
                      '+1.2.3', '-1.2.3', ' 1.2.3', '1.2.3 ', '1.2.3\n',
                      '１.2.3', '1.2.٣', '1000000000.0.0', '9' * 10000 + '.0.0',
                      '2026-11-03T17:20:00Z'):
            with self.subTest(value=str(value)[:70]):
                self.assertIsNone(advisory.parse_version(value))

    def test_real_utc_timestamp(self):
        self.assertTrue(advisory.is_utc_timestamp('2024-02-29T23:59:59Z'))
        for value in (None, '2026-02-29T00:00:00Z', '2026-11-04T24:00:00Z',
                      '2026-11-04T00:00:60Z', '2026-11-04', '2026-11-04T00:00:00+00:00',
                      '2026-11-04T00:00:00z', '2026-11-04T00:00:00Z\n'):
            self.assertFalse(advisory.is_utc_timestamp(value), value)

    def test_metadata_is_only_authority(self):
        self.assertEqual(advisory.frontmatter(skill_text())['version'], '1.0.0')
        for content in (
            skill_text().replace('name: example', 'name: example\nversion: "999.0.0"'),
            skill_text().replace('metadata:', 'version: "1.0.0"\nother:'),
            skill_text().replace('  version: "1.0.0"', '  version: 1.0.0'),
            skill_text().replace('  updated_at: "2026-11-04T12:24:49Z"', '  updated_at: 2026-11-04T12:24:49Z'),
            skill_text().replace('  version: "1.0.0"', '  version: "1.0.0"\n  version: "2.0.0"'),
            skill_text().replace('  updated_at:', '  version: "2.0.0"\n  updated_at:'),
            skill_text().replace('---\n# Test', 'metadata:\n  version: "2.0.0"\n---\n# Test'),
            skill_text().replace('metadata:', 'metadata: {version: "1.0.0"}'),
            skill_text().replace('metadata:', 'metadata: &alias'),
            skill_text().replace('  version:', '  <<: *alias\n  version:'),
            skill_text().replace('  version:', '    version:'),
            skill_text().replace('metadata:', '"metadata":'),
        ):
            with self.subTest(content=content):
                with self.assertRaises(advisory.EvidenceError):
                    advisory.frontmatter(content)

    def test_duplicate_timestamp_and_non_string_values_fail_closed(self):
        for value in ('42', 'null', 'true', '["1.0.0"]', '{version: "1.0.0"}', '|'):
            with self.assertRaises(advisory.EvidenceError):
                advisory.frontmatter(skill_text().replace('"1.0.0"', value))
        duplicate = skill_text().replace('---\n# Test', '  updated_at: "2026-11-04T00:00:00Z"\n---\n# Test')
        with self.assertRaises(advisory.EvidenceError):
            advisory.frontmatter(duplicate)


class PureVersionValueTests(unittest.TestCase):
    def assert_values_only(self, result):
        self.assertTrue(result['values_only'])
        self.assertTrue(result['advisory_only'])
        self.assertFalse(result['mutated'])
        self.assertFalse(result['overwrite_authorized'])
        self.assertIsNone(result['installation_recommendation'])
        self.assertEqual(result['content_drift'], 'not_checked')
        self.assertEqual(result['checks_not_performed'],
                         ['directory', 'content', 'source', 'trust', 'authorization'])

    def test_numerical_relations_do_not_recommend_installation(self):
        for local, candidate, decision in (
            ('1.9.9', '1.10.0', 'candidate_value_newer'),
            ('9.9.9', '10.0.0', 'candidate_value_newer'),
            ('0.0.0', '0.0.1', 'candidate_value_newer'),
            ('0.9.0', '0.10.0', 'candidate_value_newer'),
            ('999999999.999999999.999999998', '999999999.999999999.999999999', 'candidate_value_newer'),
            ('1.10.0', '1.9.9', 'local_value_newer'),
            ('2.0.0', '1.999999999.999999999', 'local_value_newer'),
            ('0.0.0', '0.0.0', 'equal_values'),
            ('999999999.999999999.999999999', '999999999.999999999.999999999', 'equal_values'),
        ):
            with self.subTest(local=local, candidate=candidate):
                result = advisory.compare_version_values(local, candidate)
                self.assertEqual(result['decision'], decision)
                self.assert_values_only(result)

    def test_invalid_boundaries_are_unorderable_in_either_position(self):
        invalid = (None, True, 1, 1.0, [], {}, '', '1', '1.2', '1.2.3.4',
                   '01.2.3', '1.02.3', '1.2.03', '-1.2.3', '+1.2.3', 'v1.2.3',
                   '1.2.3-rc.1', '1.2.3+build', ' 1.2.3', '1.2.3 ', '1.2.3\n',
                   '１.2.3', '1.2.٣', '1000000000.0.0', '0.1000000000.0',
                   '0.0.1000000000', '9' * 10000 + '.0.0', '2026-02-30T00:00:00Z',
                   '2026-11-04T00:00:00+00:00', 'C:\\skills\\SKILL.md', '/path/to/skill')
        for value in invalid:
            for pair in ((value, '1.0.0'), ('1.0.0', value)):
                with self.subTest(value=str(value)[:50], left=pair[0] == value):
                    result = advisory.compare_version_values(*pair)
                    self.assertEqual(result['decision'], 'unorderable')
                    self.assertIsNone(result['relation'])
                    self.assert_values_only(result)

    def test_all_valid_legacy_iso_pairs_require_mapping_without_date_order(self):
        for local, candidate in (
            ('2026-11-03T17:20:00Z', '1.0.0'),
            ('1.0.0', '2026-11-03T17:20:00Z'),
            ('2026-11-03T17:20:00Z', '2026-11-03T17:20:00Z'),
            ('2026-11-04T00:00:00Z', '2025-01-01T00:00:00Z'),
            ('2024-02-29T23:59:59Z', '1.0.0'),
        ):
            result = advisory.compare_version_values(local, candidate)
            self.assertEqual(result['decision'], 'mapping_required')
            self.assertIsNone(result['relation'])
            self.assert_values_only(result)
        self.assertEqual(advisory.compare_version_values('invalid', '2026-11-03T17:20:00Z')['decision'],
                         'unorderable')

    def test_simulated_windows_pure_values_never_inspect_files(self):
        with ExitStack() as stack:
            stack.enter_context(patch.object(advisory.os, 'name', 'nt'))
            for target in ('builtins.open', 'os.open', 'os.stat', 'os.listdir', 'pathlib.Path.read_text'):
                stack.enter_context(patch(target, side_effect=AssertionError('filesystem access forbidden')))
            for name in ('inspect_tree', 'open_root', 'load_legacy_map'):
                stack.enter_context(patch.object(advisory, name, side_effect=AssertionError('directory checks forbidden')))
            for pair in (('1.9.9', '1.10.0'), ('1.0.0', '1.0.0'),
                         ('2026-11-03T17:20:00Z', '1.0.0'), ('01.0.0', '1.0.0')):
                self.assert_values_only(advisory.compare_version_values(*pair))

    def test_simulated_windows_cli_values_only_and_directory_guard(self):
        output = io.StringIO()
        with patch.object(advisory.os, 'name', 'nt'):
            with patch.object(advisory, 'inspect_tree', side_effect=AssertionError('no directory read')):
                with redirect_stdout(output):
                    status = advisory.main(['versions', '--local', '1.9.9', '--candidate', '1.10.0'])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())['decision'], 'candidate_value_newer')
            with patch.object(advisory.os, 'open', side_effect=AssertionError('no filesystem access')):
                with self.assertRaisesRegex(advisory.EvidenceError, 'manual review required'):
                    advisory.open_root('C:\\skills\\example')

    def test_simulated_windows_directory_commands_exit_two_for_manual_review(self):
        for arguments in (['inspect', 'C:/skills/example'],
                          ['compare', '--local', 'C:/skills/local', '--candidate', 'C:/skills/candidate']):
            output = io.StringIO()
            with patch.object(advisory.os, 'name', 'nt'), patch.object(advisory, 'Path', PureWindowsPath):
                with patch.object(advisory.os, 'open', side_effect=AssertionError('no filesystem access')):
                    with redirect_stdout(output):
                        status = advisory.main(arguments)
            self.assertEqual(status, 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result['decision'], 'unknown')
            self.assertIn('manual review required', result['reason'])
            self.assertFalse(result['mutated'])

    def test_isolated_cli_reports_value_boundaries_and_exit_codes(self):
        processes = IsolatedProcesses(self)
        for local, candidate, decision, status in (
            ('1.9.9', '1.10.0', 'candidate_value_newer', 0),
            ('1.0.0', '1.0.0', 'equal_values', 0),
            ('2.0.0', '1.0.0', 'local_value_newer', 0),
            ('2026-11-03T17:20:00Z', '1.0.0', 'mapping_required', 0),
            ('01.0.0', '1.0.0', 'unorderable', 2),
        ):
            with self.subTest(local=local, candidate=candidate):
                child = processes.run([PYTHON, str(SCRIPT), 'versions', '--local', local,
                                       '--candidate', candidate], capture_output=True, text=True)
                self.assertEqual(child.returncode, status, child.stderr)
                result = json.loads(child.stdout)
                self.assertEqual(result['decision'], decision)
                self.assert_values_only(result)


@unittest.skipUnless(os.name == 'posix', 'helper intentionally requires POSIX no-follow descriptors')
class AdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.processes = IsolatedProcesses(self)
        self.local = self.make('local')
        self.candidate = self.make('candidate')

    def make(self, path, version='1.0.0', timestamp='2026-11-04T12:24:49Z', name='example'):
        root = self.root / path
        root.mkdir()
        (root / 'SKILL.md').write_text(skill_text(version, timestamp, name))
        (root / 'references').mkdir()
        (root / 'references' / 'guide.md').write_text('Original reference\n')
        return root

    def decide(self, **kwargs):
        return advisory.compare(self.local, self.candidate, **kwargs)['decision']

    def set_version(self, root, version, timestamp='2026-11-04T12:24:49Z', name='example'):
        (root / 'SKILL.md').write_text(skill_text(version, timestamp, name))

    def test_same_version_identical_is_idempotent_and_read_only(self):
        before = [advisory.inspect_tree(root) for root in (self.local, self.candidate)]
        for _ in range(2):
            result = advisory.compare(self.local, self.candidate)
            self.assertEqual(result['decision'], 'unchanged')
            self.assertTrue(result['advisory_only'])
            self.assertFalse(result['mutated'])
        self.assertEqual(before, [advisory.inspect_tree(root) for root in (self.local, self.candidate)])

    def test_updated_at_only_change_is_same_version_drift(self):
        self.set_version(self.candidate, '1.0.0', '2026-11-04T13:00:00Z')
        self.assertEqual(self.decide(), 'same_version_drift')

    def test_older_timestamp_does_not_block_numerical_upgrade(self):
        self.set_version(self.local, '1.9.9', '2026-11-04T23:00:00Z')
        self.set_version(self.candidate, '1.10.0', '2026-11-04T00:00:00Z')
        baseline = self.root / 'baseline'
        shutil.copytree(self.local, baseline)
        self.assertEqual(self.decide(trusted_baseline=baseline), 'upgrade_candidate')
        self.assertEqual(self.decide(), 'unknown_local_changes')

    def test_newer_local_never_downgrades(self):
        self.set_version(self.local, '2.0.0', '2025-01-01T00:00:00Z')
        self.assertEqual(self.decide(), 'local_newer')

    def test_missing_local_is_only_a_candidate(self):
        result = advisory.compare(self.root / 'absent', self.candidate)
        self.assertEqual(result['decision'], 'new_install_candidate')
        self.assertFalse((self.root / 'absent').exists())

    def test_missing_skill_file_is_not_missing_install(self):
        (self.local / 'SKILL.md').unlink()
        with self.assertRaises(advisory.EvidenceError):
            self.decide()

    def test_unknown_local_and_invalid_candidate_preserved(self):
        self.set_version(self.local, 'nonsense')
        self.assertEqual(self.decide(), 'unknown_version')
        self.set_version(self.candidate, '1.0.0', '2026-02-30T00:00:00Z')
        self.assertEqual(self.decide(), 'candidate_invalid')
        self.set_version(self.candidate, '1.0.0-rc.1')
        self.assertEqual(self.decide(), 'candidate_invalid')

    def test_invalid_local_timestamp_does_not_reorder_version(self):
        self.set_version(self.local, '2.0.0', 'invalid')
        result = advisory.compare(self.local, self.candidate)
        self.assertEqual(result['decision'], 'local_newer')
        self.assertFalse(result['local']['updated_at_valid'])
        self.assertTrue(result['warnings'])

    def test_identity_and_baseline_conflicts(self):
        self.set_version(self.candidate, '1.1.0', name='other')
        self.assertEqual(self.decide(), 'identity_conflict')
        self.set_version(self.candidate, '1.1.0')
        baseline = self.make('baseline', '0.9.0')
        self.assertEqual(self.decide(trusted_baseline=baseline), 'baseline_conflict')

    def test_customization_outside_skill_file_blocks_upgrade(self):
        baseline = self.root / 'baseline'
        shutil.copytree(self.local, baseline)
        self.set_version(self.candidate, '1.1.0')
        (self.local / 'references' / 'guide.md').write_text('Local customization\n')
        self.assertEqual(self.decide(trusted_baseline=baseline), 'local_changes')

    def test_full_directory_addition_deletion_mode_and_empty_directory_drift(self):
        for kind in ('added', 'deleted', 'mode', 'empty_directory'):
            with self.subTest(kind=kind):
                local = self.root / kind
                shutil.copytree(self.candidate, local)
                if kind == 'added':
                    (local / 'custom.txt').write_text('keep me')
                elif kind == 'deleted':
                    (local / 'references' / 'guide.md').unlink()
                elif kind == 'mode':
                    (local / 'references' / 'guide.md').chmod(0o755)
                else:
                    (local / 'custom-directory').mkdir()
                self.assertEqual(advisory.compare(local, self.candidate)['decision'], 'same_version_drift')

    def test_symlink_and_parent_traversal_rejected(self):
        (self.root / 'link').symlink_to(self.local, target_is_directory=True)
        with self.assertRaises((advisory.EvidenceError, OSError)):
            advisory.inspect_tree(self.root / 'link')
        with self.assertRaises(advisory.EvidenceError):
            advisory.inspect_tree(self.local / '..' / 'local')
        (self.local / 'references' / 'escape').symlink_to(self.candidate)
        with self.assertRaises(advisory.EvidenceError):
            advisory.inspect_tree(self.local)

    def test_nested_repository_and_special_file_rejected(self):
        (self.local / '.git').write_text('gitdir: elsewhere')
        with self.assertRaises(advisory.EvidenceError):
            advisory.inspect_tree(self.local)
        (self.local / '.git').unlink()
        os.mkfifo(self.local / 'fifo')
        with self.assertRaises(advisory.EvidenceError):
            advisory.inspect_tree(self.local)

    def test_root_symlink_swap_cannot_read_external_target(self):
        original_open = os.open
        original_supports = os.supports_dir_fd
        triggered = False

        def swap_before_open(path, flags, *args, **kwargs):
            nonlocal triggered
            if path == 'local' and not triggered:
                triggered = True
                self.local.rename(self.root / 'original')
                self.local.symlink_to(self.candidate, target_is_directory=True)
            return original_open(path, flags, *args, **kwargs)

        with patch.object(os, 'open', side_effect=swap_before_open) as mocked:
            with patch.object(os, 'supports_dir_fd', original_supports | {mocked}):
                with self.assertRaises((OSError, advisory.EvidenceError)):
                    advisory.inspect_tree(self.local)
        self.assertTrue(triggered)

    def test_child_symlink_swap_cannot_read_external_target(self):
        original_open = os.open
        original_supports = os.supports_dir_fd
        triggered = False

        def swap_before_open(path, flags, *args, **kwargs):
            nonlocal triggered
            if path == 'references' and not triggered:
                triggered = True
                (self.local / 'references').rename(self.root / 'original-references')
                (self.local / 'references').symlink_to(self.candidate, target_is_directory=True)
            return original_open(path, flags, *args, **kwargs)

        with patch.object(os, 'open', side_effect=swap_before_open) as mocked:
            with patch.object(os, 'supports_dir_fd', original_supports | {mocked}):
                with self.assertRaises((OSError, advisory.EvidenceError)):
                    advisory.inspect_tree(self.local)
        self.assertTrue(triggered)

    def test_unsupported_platform_fails_closed(self):
        with patch.object(os, 'supports_dir_fd', set()):
            with self.assertRaises(advisory.EvidenceError):
                advisory.inspect_tree(self.local)

    def test_cli_unknown_has_explicit_nonzero_status_and_no_mutation(self):
        before = advisory.inspect_tree(self.local)
        command = [PYTHON, str(SCRIPT), 'inspect', str(self.local / '..' / 'local')]
        result = self.processes.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['decision'], 'unknown')
        self.assertEqual(advisory.inspect_tree(self.local), before)


@unittest.skipUnless(os.name == 'posix' and shutil.which('git'), 'requires read-only Git baseline fixture')
class LegacyMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.processes = IsolatedProcesses(self)
        self.manifest = advisory.load_legacy_map()

    def git(self, *args):
        return self.processes.run([GIT, '-C', str(REPO), *args], check=True, capture_output=True).stdout

    def materialize(self, name):
        root = self.root / name
        root.mkdir()
        prefix = 'skills/' + name + '/'
        records = self.git('ls-tree', '-r', '-z', advisory.SOURCE_COMMIT, '--', prefix).split(b'\0')
        for record in records:
            if not record:
                continue
            meta, path = record.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            self.assertEqual(kind, 'blob')
            relative = path.decode()[len(prefix):]
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.git('cat-file', 'blob', oid))
            target.chmod(0o755 if mode == '100755' else 0o644)
        return root

    def test_all_manifest_content_matches_pinned_git_baseline(self):
        actual_skills = self.git('ls-tree', '-d', '--name-only', advisory.SOURCE_COMMIT, 'skills/').decode().splitlines()
        mapped = self.manifest['skills']
        expected = []
        for path in actual_skills:
            exists = self.processes.run([GIT, '-C', str(REPO), 'cat-file', '-e', advisory.SOURCE_COMMIT + ':' + path + '/SKILL.md'], capture_output=True)
            if exists.returncode == 0:
                expected.append(Path(path).name)
        self.assertEqual(sorted(mapped), sorted(expected))
        self.assertEqual(len(mapped), 8)
        for name, entry in mapped.items():
            with self.subTest(name=name):
                tree = advisory.inspect_tree(self.materialize(name))
                self.assertEqual(tree['version'], entry['legacy_version'])
                self.assertEqual(tree['entries'], entry['entries'])
                self.assertEqual(tree['tree_sha256'], entry['tree_sha256'])

    def test_explicit_map_required_and_no_general_format_upgrade(self):
        local = self.materialize('yomihime-init')
        candidate = self.root / 'candidate'
        shutil.copytree(local, candidate)
        text = (candidate / 'SKILL.md').read_text()
        legacy = self.manifest['skills']['yomihime-init']['legacy_version']
        (candidate / 'SKILL.md').write_text(text.replace(f'  version: "{legacy}"', '  version: "1.0.0"\n  updated_at: "2026-11-04T12:24:49Z"'))
        before = advisory.inspect_tree(local)
        self.assertEqual(advisory.compare(local, candidate)['decision'], 'legacy_mapping_required')
        result = advisory.compare(local, candidate, use_legacy_map=True)
        self.assertEqual(result['decision'], 'legacy_migration_candidate')
        self.assertEqual(result['legacy_source_commit'], advisory.SOURCE_COMMIT)
        self.assertEqual(advisory.inspect_tree(local), before)
        (local / 'private-customization.txt').write_text('preserve')
        self.assertEqual(advisory.compare(local, candidate, use_legacy_map=True)['decision'], 'legacy_local_changes_or_unknown')
        (local / 'private-customization.txt').unlink()
        (candidate / 'SKILL.md').write_text((candidate / 'SKILL.md').read_text().replace('"1.0.0"', '"1.1.0"'))
        self.assertEqual(advisory.compare(local, candidate, use_legacy_map=True)['decision'], 'legacy_mapping_required')

    def test_tampered_map_rejected(self):
        bad = json.loads(json.dumps(self.manifest))
        bad['source_commit'] = '0' * 40
        with patch.object(Path, 'read_text', return_value=json.dumps(bad)):
            with self.assertRaises(advisory.EvidenceError):
                advisory.load_legacy_map()
        bad = json.loads(json.dumps(self.manifest))
        bad['skills']['yomihime-init']['entries'][0]['path'] = 'changed'
        with patch.object(Path, 'read_text', return_value=json.dumps(bad)):
            with self.assertRaises(advisory.EvidenceError):
                advisory.load_legacy_map()


class SubprocessBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.processes = IsolatedProcesses(self)

    def test_minimal_environment_excludes_secrets_hooks_and_real_user_paths(self):
        source = {'LANG': 'C.UTF-8', 'TEST_SECRET': 'secret', 'PYTHONPATH': '/bad',
                  'NODE_OPTIONS': '--bad', 'HTTP_PROXY': 'secret', 'GIT_CONFIG_COUNT': '1',
                  'HOME': '/real-user', 'TMPDIR': '/real-tmp', 'PATH': '/untrusted'}
        with tempfile.TemporaryDirectory() as directory:
            env = minimal_environment(directory, source)
            for key in ('TEST_SECRET', 'PYTHONPATH', 'NODE_OPTIONS', 'HTTP_PROXY', 'GIT_CONFIG_COUNT'):
                self.assertNotIn(key, env)
            self.assertEqual(env['PATH'], os.defpath)
            self.assertEqual(env['GIT_ALLOW_PROTOCOL'], '')
            self.assertEqual(env['GIT_CONFIG_NOSYSTEM'], '1')
            for key in ('HOME', 'USERPROFILE', 'TMPDIR', 'TMP', 'TEMP', 'APPDATA', 'LOCALAPPDATA',
                        'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'XDG_RUNTIME_DIR'):
                self.assertTrue(Path(env[key]).is_relative_to(Path(directory).resolve()))

    def test_child_does_not_receive_parent_secret_or_startup_hook(self):
        with patch.dict(os.environ, {'TEST_SECRET': 'sentinel', 'PYTHONPATH': '/bad'}):
            processes = IsolatedProcesses(self)
            result = processes.run([PYTHON, '-c', 'import json,os; print(json.dumps(dict(os.environ)))'],
                                   check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)
        self.assertNotIn('TEST_SECRET', actual)
        self.assertNotIn('PYTHONPATH', actual)
        self.assertEqual(actual['HOME'], processes.env['HOME'])

    def test_default_deadline_and_resolved_executable(self):
        with patch('version_test_processes.subprocess.run') as run:
            self.processes.run([PYTHON, '-c', 'pass'])
            self.assertEqual(run.call_args.kwargs['timeout'], 15)
            self.assertIs(run.call_args.kwargs['env'], self.processes.env)
        with self.assertRaises(ValueError):
            self.processes.run(['python3', '-c', 'pass'])

    def test_timeout_and_unbounded_deadlines(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.processes.run([PYTHON, '-c', 'import time; time.sleep(10)'], timeout=0.05,
                               capture_output=True)
        for timeout in (None, 0, -1, float('inf'), float('nan')):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.processes.run([PYTHON, '-c', 'pass'], timeout=timeout)


if __name__ == '__main__':
    unittest.main()
