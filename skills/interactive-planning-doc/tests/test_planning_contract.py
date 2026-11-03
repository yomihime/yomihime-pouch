"""Structural checks for the bilingual planning skill's workspace contract.

These tests check documented boundaries and examples, not actual agent behavior.
Run with: python -m unittest discover -s skills/interactive-planning-doc/tests -v
"""

from pathlib import Path
import re
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]


def read(name):
    return (SKILL_DIR / name).read_text(encoding="utf-8")


def has_paragraph(text, *patterns):
    return any(all(re.search(pattern, paragraph, re.I) for pattern in patterns)
               for paragraph in re.split(r"\n\s*\n", text))


class PlanningContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chinese = read("SKILL.md")
        cls.english = read("SKILL.en.md")
        cls.readme = read("README.md")

    def test_both_languages_and_readme_use_one_task_plan(self):
        for text in (self.chinese, self.english, self.readme):
            with self.subTest(document=text[:60]):
                self.assertIn(".agent-workspace/<work-id>/plan.md", text)
                self.assertIn("scratch/", text)
                for legacy_path in (".local-dev/", ".agent-work/", ".project-memory/"):
                    self.assertNotIn(legacy_path, text)
        self.assertTrue(has_paragraph(
            self.chinese, r"复用.*主计划", r"不创建并行权威", r"默认重复规则"))
        self.assertTrue(has_paragraph(
            self.english, r"reuse one main plan", r"duplicate\s+authorities", r"default duplicate rules"))

    def test_init_owns_migration_and_preserves_existing_work(self):
        self.assertTrue(has_paragraph(
            self.chinese, r"init", r"盘点", r"安全整理", r"不建立长期兼容路径",
            r"保留既有计划", r"不自动覆盖", r"冲突先报告并确认", r"不.*自行迁移"))
        self.assertTrue(has_paragraph(
            self.english, r"init", r"inventory", r"safely consolidate", r"long-term compatibility",
            r"Preserve existing plans", r"without overwriting", r"report conflicts", r"does\s+not migrate"))

    def test_local_default_does_not_privatize_requested_deliverables(self):
        self.assertTrue(has_paragraph(
            self.chinese, r"正式规划文档", r"目的地交付", r"不强制.*私有"))
        self.assertTrue(has_paragraph(
            self.english, r"formal planning documents", r"specified destination", r"do not force"))
        self.assertTrue(has_paragraph(
            self.chinese, r"默认本地", r"不默认暂存、提交、发布", r"共享约定", r"明确授权"))
        self.assertTrue(has_paragraph(
            self.english, r"local by default", r"do not stage, commit, publish", r"sharing arrangements",
            r"explicit\s+authorization"))

    def test_docs_only_and_current_decision_boundaries_remain(self):
        self.assertIn("不编辑实现文件", self.chinese)
        self.assertIn("用户最新消息", self.chinese)
        self.assertRegex(self.english, r"do not edit\s+implementation files")
        self.assertIn("user's latest message", self.english)
        self.assertIn("已知 bug 已修复", self.chinese)
        self.assertIn("Known bugs are fixed", self.english)

    def test_both_languages_exclude_tasks_that_do_not_need_planning(self):
        cases = (
            (self.chinese, "不适用场景", (
                r"简短回答.*命令输出.*代码解释",
                r"直接实现.*未要求.*计划.*方案.*架构文档",
                r"局部 bug 修复.*不需要.*里程碑.*提交节奏.*验收标准.*收尾规划",
                r"完整计划.*只要求.*执行.*计划本身需要更新",
            )),
            (self.english, "When Not to Use This Skill", (
                r"short answer, command output, or code explanation",
                r"asks for implementation.*does not ask for a plan.*proposal.*architecture document",
                r"local bug fix.*does not need.*milestones.*commit\s+cadence.*acceptance criteria.*cleanup planning",
                r"complete plan.*only asks for code execution.*plan itself needs to be updated",
            )),
        )
        for text, heading, patterns in cases:
            with self.subTest(heading=heading):
                section = re.search(
                    rf"(?m)^## {re.escape(heading)}\n(.*?)(?=\n## |\Z)",
                    text, re.S,
                )
                self.assertIsNotNone(section, f"Missing exclusions: {heading}")
                for pattern in patterns:
                    self.assertRegex(section.group(1), re.compile(pattern, re.S))

    def test_both_languages_reserve_managed_work_ids(self):
        names = (r"`memory`", r"`design`", r"`plans`", r"`work`")
        self.assertTrue(has_paragraph(
            self.chinese, r"<work-id>", r"不得占用", *names, r"已有工具保留名称"))
        self.assertTrue(has_paragraph(
            self.english, r"work ID", r"must not use", *names,
            r"other names reserved by existing tools"))

    def test_cleanup_keeps_main_plan_and_unrelated_edits(self):
        self.assertTrue(has_paragraph(
            self.chinese, r"只清理本次创建", r"不删除.*主计划", r"已有用户文件"))
        self.assertTrue(has_paragraph(
            self.english, r"Clean up only disposable", r"preserve the main plan", r"existing user files"))
        self.assertTrue(has_paragraph(
            self.chinese, r"提交、amend 或 push", r"授权发布", r"保留其他并行或用户修改"))
        self.assertTrue(has_paragraph(
            self.english, r"commit, amend, or push", r"authorized\s+for publication", r"preserve unrelated user or concurrent edits"))


if __name__ == "__main__":
    unittest.main()
