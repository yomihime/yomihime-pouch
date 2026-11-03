"""Check that key guide-convention instructions remain documented.

These are structural checks of the skill text, not an execution or evaluation of
an agent's compliance, judgment, or language quality. Wording can change while the
key concepts remain present in the same topic paragraph.
"""

import re
from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]


def section(text, title_pattern):
    match = re.search(rf"(?m)^##\s+{title_pattern}\s*$", text)
    if not match:
        raise AssertionError(f"Missing section: {title_pattern}")
    end = re.search(r"(?m)^##\s+", text[match.end():])
    return text[match.end():match.end() + end.start()] if end else text[match.end():]


def paragraph_containing(text, *patterns):
    paragraphs = re.split(r"\n\s*\n", text)
    return next((p for p in paragraphs if all(re.search(pattern, p) for pattern in patterns)), None)


class GuideDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.guide = section(cls.skill, r"项目风格指南.*")
        cls.readme = (SKILL_DIR / "README.md").read_text(encoding="utf-8")

    def assertParagraph(self, *patterns):
        self.assertIsNotNone(paragraph_containing(self.guide, *patterns), patterns)

    def test_agents_is_a_short_authorized_index_with_missing_fallback(self):
        self.assertParagraph(r"AGENTS\.md", r"授权", r"简短", r"路径")
        self.assertParagraph(r"AGENTS\.md", r"缺失", r"现有文案", r"提示")
        self.assertParagraph(r"AGENTS\.md", r"保留原有", r"不.*完整指南")
        self.assertParagraph(r"路径失效|不可读", r"不要声称已读取", r"不要.*重建|不要.*覆盖")

    def test_existing_guide_is_scoped_and_new_guide_uses_unified_workspace(self):
        self.assertParagraph(r"AGENTS\.md", r"相关章节", r"不.*全仓扫描")
        self.assertParagraph(r"没有指南", r"分析", r"授权", r"\.agent-workspace/design/writing-guide\.md")
        self.assertParagraph(r"已有文件", r"授权", r"不自动覆盖")

    def test_design_layout_keeps_responsibilities_distinct(self):
        for marker in (r"\.agent-workspace/design/writing-guide\.md", r"ui-guide\.md", r"resources\.md"):
            with self.subTest(marker=marker):
                self.assertRegex(self.guide, marker)
        self.assertParagraph(r"ui-guide\.md", r"resources\.md", r"按需", r"不默认生成重复规则")
        self.assertParagraph(r"权威", r"引用", r"不复制")
        self.assertParagraph(r"中间材料", r"\.agent-workspace/<work-id>/scratch/", r"正式文档", r"指定目的地")

    def test_init_owns_safe_migration_without_legacy_fallback(self):
        self.assertParagraph(r"init", r"盘点", r"安全整理", r"本技能不自行迁移")
        self.assertParagraph(r"保留已有指南", r"不自动覆盖", r"冲突先报告并确认", r"验证新位置和入口")
        self.assertParagraph(r"不建立旧路径的长期兼容", r"回退查找", r"不新建重复指南")
        for text in (self.skill, self.readme):
            with self.subTest(document=text[:40]):
                self.assertNotIn(".local-dev/", text)

    def test_guide_is_persistent_work_cleanup_is_narrow(self):
        self.assertParagraph(r"指南", r"持久", r"不删除指南")
        self.assertParagraph(r"临时", r"清理", r"自建", r"不删除用户已有")
        self.assertParagraph(r"不放密钥", r"隐私|敏感")

    def test_staleness_requires_evidence_and_authorized_targeted_update(self):
        self.assertParagraph(r"具体证据", r"实质变化", r"受影响章节", r"授权.*局部更新")
        self.assertParagraph(r"文件时间", r"不足以判定", r"不静默重写")

    def test_ignored_and_untracked_guides_have_sharing_warning(self):
        self.assertParagraph(r"Git", r"忽略", r"未跟踪", r"本地", r"提交|克隆")
        self.assertParagraph(r"隐私", r"不擅自更改忽略规则", r"授权", r"分享")

    def test_readme_signposts_the_guide_convention(self):
        guide = section(self.readme, r"项目风格指南.*")
        for marker in (r"AGENTS\.md", r"\.agent-workspace/", r"init", r"授权", r"缺失", r"Git", r"隐私"):
            with self.subTest(marker=marker):
                self.assertRegex(guide, marker)


if __name__ == "__main__":
    unittest.main()
