"""Repository-level structural checks; not a simulation of agent behavior."""
import datetime
import re
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[1]


class SkillStandardTests(unittest.TestCase):
    def test_yomihime_init_identity_and_agent_execution(self):
        root = SKILLS / 'yomihime-init'
        skill = (root / 'SKILL.md').read_text(encoding='utf-8')
        interface = (root / 'agents' / 'openai.yaml').read_text(encoding='utf-8')
        self.assertIn('name: yomihime-init', skill)
        self.assertIn('不是已安装的 shell 命令', skill)
        self.assertIn('不自带联网程序', skill)
        self.assertIn('由使用该技能的 Agent', skill)
        self.assertIn('display_name: "yomihime init"', interface)
        self.assertNotIn('project-init', interface)

    def test_each_skill_has_release_version_update_time_author_and_license(self):
        entries = sorted(SKILLS.glob('*/SKILL.md'))
        self.assertEqual(len(entries), 8)
        version_pattern = r'(?:0|[1-9][0-9]{0,8})(?:\.(?:0|[1-9][0-9]{0,8})){2}'
        for entry in entries:
            with self.subTest(skill=entry.parent.name):
                text = entry.read_text(encoding='utf-8')
                front = text.split('---', 2)[1]
                self.assertIn('metadata:', front)
                # The single version authority is nested metadata.version.
                self.assertNotRegex(front, r'(?m)^version:')
                version = re.findall(r'^  version: "(' + version_pattern + r')"$', front, re.M)
                self.assertEqual(len(version), 1)
                self.assertEqual(len(re.findall(r'^  version:', front, re.M)), 1)
                updated = re.findall(r'^  updated_at: "(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)"$', front, re.M)
                self.assertEqual(len(updated), 1)
                datetime.datetime.strptime(updated[0], '%Y-%m-%dT%H:%M:%SZ')
                self.assertIn('  author: "yomihime（如月怜） <evenia@evenia.moe>"', front)
                self.assertTrue((entry.parent / 'LICENSE').is_file())

    def test_planning_english_mirror_has_same_release_metadata(self):
        root = SKILLS / 'interactive-planning-doc'
        fronts = [(root / name).read_text(encoding='utf-8').split('---', 2)[1]
                  for name in ('SKILL.md', 'SKILL.en.md')]
        for key in ('version', 'updated_at', 'author'):
            values = [re.search(r'^  ' + key + r': "([^\n]+)"$', f, re.M).group(1)
                      for f in fronts]
            self.assertEqual(values[0], values[1], key)

    def test_skill_local_markdown_links_do_not_escape_install(self):
        for root in sorted(p.parent for p in SKILLS.glob('*/SKILL.md')):
            for path in root.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                    if target.startswith(('http:', 'https:', '#', 'mailto:')):
                        continue
                    destination = (path.parent / target.split('#')[0]).resolve()
                    with self.subTest(file=str(path), target=target):
                        self.assertTrue(destination.is_relative_to(root.resolve()))
                        self.assertTrue(destination.exists())

    def test_legacy_paths_only_appear_in_init_migration_guidance(self):
        old = ('.agent-work/', '.project-memory/', '.local-dev/', '.local_dev/')
        for root in sorted(p.parent for p in SKILLS.glob('*/SKILL.md')):
            if root.name == 'yomihime-init':
                continue
            for path in root.rglob('*.md'):
                with self.subTest(file=str(path)):
                    content = path.read_text(encoding='utf-8')
                    for legacy in old:
                        self.assertNotIn(legacy, content)


if __name__ == '__main__':
    unittest.main()
