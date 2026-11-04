"""Structural checks for documented lifecycle; not an agent behavior test."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LifecycleContractTests(unittest.TestCase):
    def test_persistent_source_discovery_and_protection(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        contract = (ROOT / 'references/source-contract.md').read_text(encoding='utf-8')
        self.assertIn('.agent-workspace/architecture/architecture.json', skill)
        for phrase in ('有效 AGENTS 或项目记忆入口', '唯一图纸 writer', '入口可达性',
                       '旧规范源即使仍位于任务目录', '不删除或搬走', '不自动同步'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill + contract)
        self.assertIn('已存在有效唯一源时复用其实际位置', contract)
        self.assertIn('不能把计划升级成已确认现状', contract)

    def test_default_layout_does_not_make_task_copy_authoritative(self):
        example = (ROOT / 'references/examples.md').read_text(encoding='utf-8')
        self.assertIn('architecture/', example)
        self.assertIn('不再创建默认位置的副本', example)
        self.assertIn('快照', example)


if __name__ == '__main__':
    unittest.main()
