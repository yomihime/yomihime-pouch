"""Structural regression checks for the ui-design skill and designer handoff.

These checks verify documented markers and links, not agent behavior, legal
compliance, actual accessibility, or the visual quality of a delivered UI.
Run with: python -m unittest discover -s skills/ui-design/tests -v
"""

from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "ui-design"
MULTI = ROOT / "skills" / "multi-agent-engineering"


def read(path):
    return path.read_text(encoding="utf-8")


def paragraphs(text):
    return re.split(r"\n\s*\n", text)


def has_paragraph(text, *patterns):
    return any(all(re.search(p, paragraph, re.I) for p in patterns)
               for paragraph in paragraphs(text))


class DesignSkillStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = read(SKILL / "SKILL.md")
        cls.resources = read(SKILL / "references" / "resources.md")
        cls.role = read(MULTI / "SKILL.md")
        cls.task_cards = read(MULTI / "references" / "task-cards.md")

    def test_required_files_and_frontmatter(self):
        for path in (SKILL / "README.md", SKILL / "LICENSE", SKILL / "agents" / "openai.yaml",
                     SKILL / "references" / "examples.md",
                     SKILL / "references" / "resources.md"):
            self.assertTrue(path.is_file(), path)
        match = re.match(r"\A---\n(.*?)\n---\n", self.skill, re.S)
        self.assertIsNotNone(match, "SKILL.md needs delimited YAML frontmatter")
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name:\s*ui-design\s*$")
        self.assertRegex(frontmatter, r"(?m)^description:\s*\S")
        self.assertRegex(read(SKILL / "agents" / "openai.yaml"), r"(?m)^interface:\s*$")

    @unittest.skipUnless(yaml, "PyYAML is not installed; YAML syntax parse skipped")
    def test_yaml_metadata_parses(self):
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", self.skill, re.S).group(1)
        skill_metadata = yaml.safe_load(frontmatter)
        interface = yaml.safe_load(read(SKILL / "agents" / "openai.yaml"))
        self.assertEqual(skill_metadata.get("name"), "ui-design")
        self.assertIsInstance(skill_metadata.get("description"), str)
        self.assertTrue(skill_metadata["description"].strip())
        self.assertIsInstance(interface.get("interface"), dict)
        for key in ("display_name", "short_description", "default_prompt"):
            self.assertTrue(interface["interface"].get(key), key)

    def test_local_markdown_links_resolve(self):
        docs = list(SKILL.rglob("*.md")) + [MULTI / "SKILL.md", MULTI / "references" / "task-cards.md"]
        for doc in docs:
            for target in re.findall(r"\]\(([^)]+)\)", read(doc)):
                path = target.split("#", 1)[0]
                if not path or urlsplit(path).scheme or path.startswith("/"):
                    continue
                with self.subTest(doc=doc, target=target):
                    self.assertTrue((doc.parent / path).exists(), f"Broken relative link: {doc}: {target}")
        for target in re.findall(r"`(references/[^`]+\.md)`", self.skill):
            with self.subTest(target=target):
                self.assertTrue((SKILL / target).is_file())

    def test_guidance_preserves_existing_ui_and_guide(self):
        self.assertTrue(has_paragraph(self.skill, r"已有项目", r"保留", r"视觉", r"行为|功能", r"建议"))
        self.assertTrue(has_paragraph(self.skill, r"已有指南", r"不静默覆盖"))
        self.assertTrue(has_paragraph(self.skill, r"保留已有内容", r"授权", r"局部"))
        self.assertTrue(has_paragraph(self.skill, r"AGENTS\.md", r"保留", r"简短", r"实际路径", r"不可读", r"不擅自重建"))

    def test_design_guides_use_unified_workspace_without_duplicate_rules(self):
        # Structural checks only; they do not prove that an agent follows the
        # documented migration or authorization policy.
        self.assertTrue(has_paragraph(
            self.skill, r"统一", r"\.agent-workspace/design/ui-guide\.md"))
        self.assertTrue(has_paragraph(
            self.skill, r"按需.*同目录.*resources\.md",
            r"同级.*writing-guide\.md", r"不要求一次性创建全部文件",
            r"不默认生成重复规则"))
        self.assertTrue(has_paragraph(
            self.skill, r"权威", r"引用", r"不复制|不重复", r"不.*迁移"))
        self.assertTrue(has_paragraph(
            self.skill, r"按需读取项目现有资源记录",
            r"\.agent-workspace/design/resources\.md", r"项目记录", r"不替代.*许可"))
        self.assertTrue(has_paragraph(
            read(SKILL / "README.md"), r"统一", r"\.agent-workspace/design/ui-guide\.md",
            r"同目录.*resources\.md", r"同级.*writing-guide\.md", r"不要求全部创建"))

    def test_init_owns_safe_migration_without_legacy_fallback(self):
        self.assertTrue(has_paragraph(
            self.skill, r"init", r"盘点", r"安全整理", r"本技能不自行迁移",
            r"保留已有指南", r"不自动覆盖", r"冲突先报告并确认", r"验证新位置与入口"))
        self.assertTrue(has_paragraph(
            self.skill, r"不建立旧路径的长期兼容", r"回退查找", r"不重建另一份指南"))
        for path in SKILL.rglob("*.md"):
            with self.subTest(path=path):
                self.assertNotIn(".local-dev/", read(path))

    def test_local_artifacts_keep_scoped_cleanup_and_authorized_delivery(self):
        self.assertTrue(has_paragraph(
            self.skill, r"\.agent-workspace/<work-id>/scratch/", r"只清理本次创建",
            r"绝不删除用户文件", r"正式设计文档", r"指定位置", r"不强制私有化"))
        self.assertTrue(has_paragraph(
            self.skill, r"默认是本地工作区", r"不默认暂存、提交、发布", r"明确授权", r"共享约定"))

    def test_resource_limit_and_license_provenance(self):
        self.assertTrue(has_paragraph(self.skill, r"每次用户请求最多获取一个资源库", r"来源", r"版本", r"许可证"))
        self.assertTrue(has_paragraph(self.resources, r"每次用户请求最多获取一个资源库", r"来源 URL", r"版本|访问日期", r"许可证", r"归属声明"))
        self.assertTrue(has_paragraph(self.resources, r"离线", r"无法核实", r"不要虚构"))
        links = re.findall(r"\]\((https?://[^)]+)\)", self.resources)
        self.assertGreaterEqual(len(links), 1)
        for link in links:
            with self.subTest(link=link):
                self.assertEqual(urlsplit(link).scheme, "https")
                self.assertTrue(urlsplit(link).netloc)

    def test_license_declarations_are_present(self):
        self.assertIn("Apache License", read(SKILL / "LICENSE"))
        self.assertTrue(has_paragraph(read(SKILL / "README.md"), r"Apache-2\.0", r"第三方", r"许可"))
        self.assertTrue(has_paragraph(read(ROOT / "README.md"), r"MIT", r"skills/ui-design/", r"Apache-2\.0"))
        self.assertIn("./skills/ui-design/LICENSE", read(ROOT / "README.md"))

    def test_no_bundled_third_party_assets(self):
        # The current skill is text-only. New asset types need deliberate review
        # rather than silently adding fonts, images, archives, or vendored code.
        allowed = {".md", ".yaml", ".py"}
        for path in SKILL.rglob("*"):
            if path.is_file() and path.name != "LICENSE" and "__pycache__" not in path.parts:
                with self.subTest(path=path):
                    self.assertIn(path.suffix, allowed, f"Unexpected bundled asset: {path}")

    def test_designer_role_loads_skill_if_available_and_falls_back(self):
        self.assertTrue(has_paragraph(self.role, r"设计师", r"可用", r"ui-design", r"缺失", r"继续设计", r"不.*安装"))
        self.assertTrue(has_paragraph(self.task_cards, r"设计师", r"ui-design", r"缺少", r"继续", r"不自行安装"))


if __name__ == "__main__":
    unittest.main()
