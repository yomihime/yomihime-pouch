"""Repository-level structural checks; not a simulation of agent behavior."""
import datetime
import re
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[1]


class SkillStandardTests(unittest.TestCase):
    def test_each_skill_has_utc_version_and_license(self):
        entries = sorted(SKILLS.glob('*/SKILL.md'))
        self.assertTrue(entries)
        for entry in entries:
            with self.subTest(skill=entry.parent.name):
                text = entry.read_text(encoding='utf-8')
                front = text.split('---', 2)[1]
                match = re.search(r'^  version: "(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)"$', front, re.M)
                self.assertIsNotNone(match)
                datetime.datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%SZ')
                self.assertTrue((entry.parent / 'LICENSE').is_file())

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
            if root.name == 'project-init':
                continue
            for path in root.rglob('*.md'):
                with self.subTest(file=str(path)):
                    content = path.read_text(encoding='utf-8')
                    for legacy in old:
                        self.assertNotIn(legacy, content)


if __name__ == '__main__':
    unittest.main()
