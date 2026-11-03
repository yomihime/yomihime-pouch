"""Regression tests for the optional, intentionally heuristic CLI helpers.

Run with: python -m unittest discover -s skills/auto-style-string-resources/tests
These checks do not judge whether text is natural or safe to rewrite.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TREE = SCRIPTS / "draft_string_tree.py"
CONSTRAINTS = SCRIPTS / "check_string_constraints.py"


def run_script(script, *args):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        check=False,
        text=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


class ConstraintCheckerTests(unittest.TestCase):
    def check(self, before, after):
        result = run_script(CONSTRAINTS, before, after)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_chinese_and_japanese_copy_can_change_when_tokens_are_preserved(self):
        for before, after in [
            ("正在处理 {count} 个文件：%s", "正在处理 %s，共 {count} 个文件"),
            ("{name} さん、残り %d 件です", "残り %d 件です。{name} さん"),
            ("保存到 $path 后按 Ctrl+S", "按 Ctrl+S 保存到 $path"),
        ]:
            with self.subTest(before=before):
                code, payload = self.check(before, after)
                self.assertEqual(code, 0)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["mismatches"], {})

    def test_missing_or_changed_constraints_fail_even_with_readable_text(self):
        for before, after, category in [
            ("已处理 {count} 个文件", "已处理文件", "brace_placeholders"),
            ("残り %d 件", "残り %s 件", "percent_placeholders"),
            ("保存到 ${path}", "保存到 ${location}", "dollar_placeholders"),
            ("按 Ctrl+S 保存", "按 Ctrl+P 保存", "shortcuts"),
            ("请查看 [帮助](https://example.com/help)", "请查看帮助", "markdown_links"),
            ("<b>注意</b>", "注意", "html_tags"),
            ("打开 /tmp/output", "打开 /tmp/result", "paths"),
            ("错误 E123", "错误 E124", "error_codes"),
        ]:
            with self.subTest(category=category):
                code, payload = self.check(before, after)
                self.assertEqual(code, 1)
                self.assertFalse(payload["ok"])
                self.assertIn(category, payload["mismatches"])

    def test_token_multiplicity_is_preserved_but_order_is_not_significant(self):
        code, payload = self.check("{a} {b} {a}", "{b} {a} {a}")
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        code, payload = self.check("{a} {b} {a}", "{b} {a}")
        self.assertEqual(code, 1)
        self.assertEqual(payload["mismatches"]["brace_placeholders"]["before"], ["{a}", "{b}", "{a}"])

    def test_positional_placeholder_reordering_can_pass_but_change_meaning(self):
        # The first and second %s are bound by position. Moving their surrounding
        # labels swaps the displayed source and destination, despite equal tokens.
        before = "从 %s 复制到 %s"
        after = "目标是 %s，来源是 %s"
        code, payload = self.check(before, after)
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        # A pass only reports equal detected token multisets; it is not a
        # semantic-safety guarantee or a check of runtime argument bindings.

    def test_success_is_not_a_naturalness_or_semantic_safety_verdict(self):
        # No detected tokens were lost, but the warning's meaning was reversed.
        code, payload = self.check("删除后无法恢复", "删除后可以恢复")
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])


class DraftTreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def scan(self, *args):
        result = run_script(TREE, "--root", self.root, "--format", "jsonl", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_locale_filter_nested_json_and_unicode(self):
        self.write("i18n/zh_CN.json", json.dumps({"home": {"button_save": "保存 {name}", "items": ["取消", 1, "确定"]}}, ensure_ascii=False))
        self.write("i18n/ja_JP.json", json.dumps({"home": {"button_save": "保存する {name}"}}, ensure_ascii=False))
        self.write("i18n/broken.json", "{invalid")
        rows = self.scan("--locale", "zh_CN")
        self.assertEqual([r["key"] for r in rows], ["zh_CN:home.button_save", "zh_CN:home.items.0", "zh_CN:home.items.2"])
        self.assertEqual(rows[0]["text"], "保存 {name}")
        self.assertEqual(rows[0]["source"], "i18n/zh_CN.json")
        self.assertEqual(rows[0]["tags"], ["i18n", "zh_CN"])
        self.assertEqual((rows[0]["page"], rows[0]["group"]), ("home", "button"))
        both = self.scan("--locale", "zh_CN", "--locale", "ja_JP")
        self.assertEqual(len(both), 4)
        self.assertTrue(any(r["text"] == "保存する {name}" for r in both))

    def test_python_scan_is_a_draft_not_a_complete_ui_or_docs_audit(self):
        self.write("gui/pages/home.py", '''\nwidget.setText("保存")\nwidget.setToolTip("ファイルを開く")\nunknown("not collected from an unknown call")\nloose_literal = "CONFIG_KEY"\nwidget.setText(f"处理中 {count} 个文件")\n''')
        self.write("gui/build/generated.py", 'widget.setText("skip generated")\n')
        self.write("gui/broken.py", "def broken(:\n")
        self.write("elsewhere/window.py", 'widget.setText("outside scanned roots")\n')
        self.write("README.md", "This visible product wording is not scanned")
        self.write("docs/help.md", "This help text is not scanned either")
        rows = self.scan()
        texts = [r["text"] for r in rows]
        self.assertIn("保存", texts)
        self.assertIn("ファイルを開く", texts)
        # A standalone technical literal is a possible false positive.
        self.assertIn("CONFIG_KEY", texts)
        self.assertNotIn("not collected from an unknown call", texts)
        self.assertNotIn("skip generated", texts)
        self.assertNotIn("outside scanned roots", texts)
        self.assertFalse(any("README" in r["source"] or r["source"].startswith("docs/") for r in rows))
        self.assertTrue(all("style_score" not in r for r in rows))
        # F-strings are AST fragments; the output must not be treated as a full message.
        self.assertNotIn("处理中 {count} 个文件", texts)
        self.assertTrue(all(r["source"] == "gui/pages/home.py" for r in rows))

    def test_max_entries_and_markdown_preview(self):
        self.write("i18n/zh_CN.json", '{"home_title":"欢迎来到这里", "home_save":"保存"}')
        rows = self.scan("--max-entries", "1")
        self.assertEqual(len(rows), 1)
        result = run_script(TREE, "--root", self.root, "--locale", "zh_CN", "--max-entries", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Draft UI/UX String Tree", result.stdout)
        self.assertIn("Project strings", result.stdout)
        self.assertNotIn("CharaPicker strings", result.stdout)
        self.assertIn("欢迎来到这里", result.stdout)
        self.assertNotIn("zh_CN:home_save", result.stdout)


if __name__ == "__main__":
    unittest.main()
