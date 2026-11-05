"""Regression tests for the optional, intentionally heuristic CLI helpers.

Run with: python -m unittest discover -s skills/auto-style-string-resources/tests
These checks do not judge whether text is natural or safe to rewrite.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TREE = SCRIPTS / "draft_string_tree.py"
CONSTRAINTS = SCRIPTS / "check_string_constraints.py"


from subprocess_support import minimal_environment, run_script


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
        self.assertIn("scan complete:", result.stderr)
        return [json.loads(line) for line in result.stdout.split("\n") if line]

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
        result = run_script(TREE, "--root", self.root, "--format", "jsonl")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("scan partial:", result.stderr)
        self.assertIn("broken.py", result.stderr)
        self.assertIn("SyntaxError", result.stderr)
        rows = [json.loads(line) for line in result.stdout.split("\n") if line]
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


    def test_text_limit_includes_ellipsis_and_handles_small_limits(self):
        self.write("i18n/zh.json", json.dumps({"label": "文" * 100}))
        for limit in (1, 2, 3, 4, 80, 100, 101):
            with self.subTest(limit=limit):
                result = run_script(TREE, "--root", self.root, "--text-limit", limit)
                self.assertEqual(result.returncode, 0, result.stderr)
                text = next(line.split(" text=", 1)[1] for line in result.stdout.splitlines() if " text=" in line)
                self.assertEqual(len(text), min(limit, 100))
                if limit < 100:
                    marker = "." * min(3, limit)
                    self.assertEqual(text, "文" * (limit - len(marker)) + marker)
                else:
                    self.assertEqual(text, "文" * 100)

    def test_nonpositive_text_limits_are_rejected_before_scan(self):
        for limit in (0, -1):
            with self.subTest(limit=limit):
                result = run_script(TREE, "--root", self.root / "missing", "--text-limit", limit)
                self.assertEqual(result.returncode, 2)
                self.assertIn("text limit must be positive", result.stderr)
                self.assertNotIn("invalid root", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_preview_limit_never_truncates_jsonl_resources(self):
        self.write("i18n/zh.json", json.dumps({"label": "完整文字" * 30}))
        self.assertEqual(self.scan("--text-limit", 1)[0]["text"], "完整文字" * 30)

    def test_invalid_roots_fail_without_output(self):
        self.write("plain-file", "not a directory")
        for root in (self.root / "missing", self.root / "plain-file"):
            with self.subTest(root=root):
                result = run_script(TREE, "--root", root)
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid root", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_valid_empty_projects_and_files_are_successful(self):
        self.assertEqual(self.scan(), [])
        self.write("i18n/en.json", "{}")
        self.write("gui/empty.py", "# no strings\n")
        result = run_script(TREE, "--root", self.root, "--format", "jsonl")
        self.assertEqual(result.returncode, 0)
        self.assertIn("2 file(s) parsed, 0 error(s), 0 candidate(s)", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_bad_json_and_python_are_all_failed_not_empty_success(self):
        self.write("i18n/en.json", "{invalid")
        self.write("gui/broken.py", "def broken(:\n")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = run_script(TREE, "--root", self.root)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("scan failed: 0 file(s) parsed, 2 error(s)", result.stderr)
        self.assertIn("JSONDecodeError", result.stderr)
        self.assertIn("SyntaxError", result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_jsonl_parses_multiple_records_and_reports_physical_lines(self):
        self.write("i18n/zh.jsonl", '{"home_title":"欢迎"}\n\n{"home_save":"保存"}\n')
        rows = self.scan()
        self.assertEqual([r["text"] for r in rows], ["欢迎", "保存"])
        self.assertEqual([r["page"] for r in rows], ["home", "home"])
        self.assertEqual([r["key"] for r in rows], ["zh:L1.home_title", "zh:L3.home_save"])
        self.assertTrue(all(r["source"] == "i18n/zh.jsonl" for r in rows))

    def test_jsonl_unicode_separators_are_string_content_not_record_boundaries(self):
        for separator in ("\u0085", "\u2028", "\u2029"):
            with self.subTest(separator=repr(separator)):
                text = f"before{separator}after"
                self.write("i18n/en.jsonl", json.dumps({"home_title": text}, ensure_ascii=False) + "\n")
                rows = self.scan()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["text"], text)
                self.assertEqual(rows[0]["key"], "en:L1.home_title")

    def test_jsonl_crlf_and_blank_lines_preserve_physical_line_numbers(self):
        path = self.root / "i18n/en.jsonl"
        path.parent.mkdir()
        path.write_bytes(b'\r\n{"home_title":"first"}\r\n \t\r\n{"home_save":"second"}\r\n')
        rows = self.scan()
        self.assertEqual([r["key"] for r in rows], ["en:L2.home_title", "en:L4.home_save"])
        self.assertEqual([r["text"] for r in rows], ["first", "second"])
        path.write_bytes(b'\r\n{"home_title":"first"}\r\n \t\r\n{invalid\r\n')
        result = run_script(TREE, "--root", self.root, "--format", "jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSONL line 4", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_jsonl_bare_cr_is_not_a_record_separator(self):
        path = self.root / "i18n/en.jsonl"
        path.parent.mkdir()
        path.write_bytes(b'{"home_title":"first"}\r{"home_save":"second"}')
        result = run_script(TREE, "--root", self.root, "--format", "jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSONL line 1", result.stderr)

    def test_bad_jsonl_is_atomic_and_good_file_still_emitted(self):
        self.write("i18n/en.jsonl", '{"title":"discard this"}\n{invalid\n')
        self.write("i18n/zh.json", '{"title":"保留"}')
        result = run_script(TREE, "--root", self.root, "--format", "jsonl")
        self.assertEqual(result.returncode, 1)
        self.assertIn("JSONL line 2", result.stderr)
        self.assertIn("scan partial: 1 file(s) parsed, 1 error(s)", result.stderr)
        self.assertEqual([json.loads(line)["text"] for line in result.stdout.split("\n") if line], ["保留"])

    def test_each_parser_failure_alone_fails(self):
        for filename, content, diagnostic in (
            ("i18n/en.json", "{bad", "JSONDecodeError"),
            ("gui/broken.py", "def broken(:", "SyntaxError"),
            ("i18n/en.jsonl", '{"ok":"discard"}\n{bad', "JSONL line 2"),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / filename
                path.parent.mkdir(parents=True)
                path.write_text(content, encoding="utf-8")
                result = run_script(TREE, "--root", folder, "--format", "jsonl")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(diagnostic, result.stderr)

    def test_successful_scan_does_not_modify_sources(self):
        self.write("i18n/zh.jsonl", '{"home_title":"欢迎"}\n{"home_save":"保存"}\n')
        self.write("gui/home.py", 'widget.setText("保存")\n')
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.scan()
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_bad_encoding_is_reported(self):
        (self.root / "i18n").mkdir()
        (self.root / "i18n/en.json").write_bytes(b"\xff")
        result = run_script(TREE, "--root", self.root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("UnicodeDecodeError", result.stderr)

    def test_scan_locations_must_be_directories(self):
        self.write("i18n", "not a directory")
        self.write("gui", "not a directory")
        result = run_script(TREE, "--root", self.root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("NotADirectoryError", result.stderr)


class SubprocessSafetyTests(unittest.TestCase):
    def test_sensitive_environment_and_python_hooks_are_not_inherited(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "inspect_env.py"
            script.write_text("import json, os; print(json.dumps(dict(os.environ)))", encoding="utf-8")
            with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "sentinel", "OPENAI_API_KEY": "sentinel",
                                         "PRIVATE_TOKEN": "sentinel", "PYTHONPATH": "sentinel",
                                         "LANG": "C.UTF-8"}):
                result = run_script(script)
                self.assertEqual(result.returncode, 0, result.stderr)
                env = json.loads(result.stdout)
                for name in ("AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY", "PRIVATE_TOKEN", "PYTHONPATH"):
                    self.assertNotIn(name, env)
                self.assertEqual(env["LANG"], "C.UTF-8")

    def test_platform_environment_preserves_only_explicit_allowlist(self):
        with patch.dict(os.environ, {"SystemRoot": "C:\\Windows", "LC_CTYPE": "C", "HOME": "private"}, clear=True):
            env = minimal_environment()
            self.assertEqual(env["SystemRoot"], "C:\\Windows")
            self.assertEqual(env["LC_CTYPE"], "C")
            self.assertNotIn("HOME", env)

    def test_timeout_is_enforced(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "wait.py"
            script.write_text("import time; time.sleep(30)", encoding="utf-8")
            with self.assertRaises(subprocess.TimeoutExpired):
                run_script(script, timeout=0.1)


if __name__ == "__main__":
    unittest.main()
