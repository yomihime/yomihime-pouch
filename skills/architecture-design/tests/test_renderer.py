"""Regression tests. Run: python3 -m unittest discover -s tests -v"""
import copy
import io
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("architecture_renderer", ROOT / "scripts" / "render_architecture.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def fixture():
    return json.loads((ROOT / "assets" / "demo.json").read_text(encoding="utf-8"))


class ParsedHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = {}
        self.remote_attributes = []
        self.current_script = None
        self.metas = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script":
            self.current_script = values.get("id", "anonymous")
            self.scripts[self.current_script] = ""
        if tag == "meta":
            self.metas.append(values)
        if any(key in values and not values[key].startswith("#") for key in ("src", "href")):
            self.remote_attributes.append((tag, values))

    def handle_endtag(self, tag):
        if tag == "script":
            self.current_script = None

    def handle_data(self, data):
        if self.current_script is not None:
            self.scripts[self.current_script] += data


class ValidationTests(unittest.TestCase):
    def assert_invalid(self, data, phrase):
        with self.assertRaisesRegex(renderer.ArchitectureError, phrase):
            renderer.validate_data(data)

    def test_demo_has_three_scopes_and_no_claimed_current_facts(self):
        data = fixture()
        self.assertEqual(renderer.validate_data(data), [])
        self.assertEqual({view["kind"] for view in data["views"]}, {"overview", "module", "flow"})
        self.assertTrue(all(item["status"] != "current" for item in data["elements"]))
        self.assertIn("合成示例", data["summary"])

    def test_invalid_schema_version_and_unknown_keys(self):
        data = fixture()
        data["schemaVersion"] = "2.0"
        self.assert_invalid(data, "must equal")
        data = fixture()
        data["silentTypo"] = True
        self.assert_invalid(data, "unknown property")

    def test_missing_and_wrong_type_required_fields(self):
        for mutation in (lambda d: d.pop("contracts"), lambda d: d.update(elements={}),
                         lambda d: d["contracts"][0].update(inputs=None),
                         lambda d: d["elements"][0].update(status="implemented")):
            data = fixture()
            mutation(data)
            self.assert_invalid(data, "Schema validation failed")

    def test_empty_arrays_and_names(self):
        for key in ("elements", "views"):
            data = fixture()
            data[key] = []
            self.assert_invalid(data, "at least")
        data = fixture()
        data["elements"][0]["name"] = ""
        self.assert_invalid(data, "must not be empty")

    def test_rejects_duplicate_global_and_scoped_ids(self):
        data = fixture()
        data["contracts"][0]["id"] = data["elements"][0]["id"]
        self.assert_invalid(data, "duplicate global id")
        data = fixture()
        data["flows"][0]["steps"][1]["id"] = data["flows"][0]["steps"][0]["id"]
        self.assert_invalid(data, "duplicate scoped step")

    def test_references_and_scoped_view_endpoints(self):
        mutations = [lambda d: d["relationships"][0].update(to="missing"),
                     lambda d: d["elements"][0].update(contractIds=["missing"]),
                     lambda d: d["flows"][0]["steps"][0].update(elementId="missing"),
                     lambda d: d["flows"][0]["transitions"][0].update(to="missing"),
                     lambda d: d["views"][0]["elementIds"].remove("orders"),
                     lambda d: d["changes"][0].update(flowIds=["missing"])]
        for mutate in mutations:
            data = fixture()
            mutate(data)
            self.assert_invalid(data, "Semantic validation failed")

    def test_identifiers_and_line_ranges_reject_trailing_newlines(self):
        data = fixture()
        data["elements"][0]["id"] += "\n"
        self.assert_invalid(data, "required format")
        data = fixture()
        data["elements"][0]["evidence"] = [{"path": "src/example.py", "lines": "1\n"}]
        self.assert_invalid(data, "required format")

    def test_hierarchy_cycles_and_self_parent(self):
        data = fixture()
        data["elements"][0]["parentId"] = "orders"
        self.assert_invalid(data, "cycle")
        data = fixture()
        data["elements"][0]["parentId"] = "system"
        self.assert_invalid(data, "cycle")

    def test_view_kind_scope_rules(self):
        data = fixture()
        data["views"][2].pop("flowId")
        self.assert_invalid(data, "flow view requires")
        data = fixture()
        data["views"][2]["elementIds"] = ["orders"]
        self.assert_invalid(data, "derives its scope")
        data = fixture()
        data["views"][0]["flowId"] = "flow-submit"
        self.assert_invalid(data, "must not declare flowId")
        data = fixture()
        data["views"] = data["views"][1:]
        self.assert_invalid(data, "overview view is required")

    def test_evidence_required_for_current_and_verified(self):
        for collection in ("elements", "relationships", "contracts", "flows", "changes"):
            data = fixture()
            data[collection][0]["status"] = "current"
            self.assert_invalid(data, "current claims require evidence")
            data[collection][0]["evidence"] = [{"path": "src/example.py", "lines": "1-20"}]
            renderer.validate_data(data)
        data = fixture()
        data["changes"][0]["verification"] = "verified"
        self.assert_invalid(data, "claims require evidence")
        data["changes"][0]["evidence"] = [{"path": "reports/test-result.txt"}]
        renderer.validate_data(data)
        data["changes"][0]["decision"] = "rejected"
        self.assert_invalid(data, "rejected change cannot be verified")

    def test_flow_status_inherits_but_explicit_current_needs_evidence(self):
        data = fixture()
        flow = data["flows"][0]
        flow["status"] = "current"
        flow["evidence"] = [{"path": "src/order.py"}]
        renderer.validate_data(data)
        flow["steps"][0]["status"] = "current"
        self.assert_invalid(data, "current claims require evidence")
        flow["steps"][0]["evidence"] = [{"path": "src/access.py"}]
        renderer.validate_data(data)
        flow["transitions"][0]["status"] = "current"
        self.assert_invalid(data, "current claims require evidence")

    def test_empty_evidence_cannot_hide_inherited_current_provenance(self):
        for collection in ("steps", "transitions"):
            data = fixture()
            flow = data["flows"][0]
            flow["status"] = "current"
            flow["evidence"] = [{"path": "src/order.py"}]
            flow[collection][0]["evidence"] = []
            self.assert_invalid(data, "current claims require evidence")
            flow[collection][0]["evidence"] = [{"path": "src/specific.py"}]
            renderer.validate_data(data)

    def test_evidence_is_display_only_and_paths_are_relative(self):
        for path in ("../secret", "/tmp/secret", "https://example.com", "C:\\secret", "foo/../secret", ".", "file\x00name"):
            data = fixture()
            data["elements"][0]["evidence"] = [{"path": path}]
            self.assert_invalid(data, "repository-relative POSIX")
        data = fixture()
        data["elements"][0]["evidence"] = [{"path": "not-present/no-file.py", "lines": "20-10"}]
        self.assert_invalid(data, "ascending")
        data["elements"][0]["evidence"][0]["lines"] = "9" * 5000
        self.assert_invalid(data, "maximum length")
        data["elements"][0]["evidence"][0]["lines"] = "10-20"
        # Validation deliberately does not open or assert existence of evidence.
        renderer.validate_data(data)

    def test_duplicate_fields_and_errors(self):
        for field in ("inputs", "outputs", "errors"):
            data = fixture()
            data["contracts"][0][field].append(copy.deepcopy(data["contracts"][0][field][0]))
            self.assert_invalid(data, "must be unique")

    def test_warnings_for_unmodeled_paths_and_acceptance(self):
        data = fixture()
        data["flows"][0]["transitions"] = []
        for step in data["flows"][0]["steps"]:
            step.pop("outcome", None)
        data["changes"][0].pop("acceptance")
        warnings = renderer.validate_data(data)
        self.assertTrue(any("disconnected" in warning for warning in warnings))
        self.assertTrue(any("failure or recovery" in warning for warning in warnings))
        self.assertTrue(any("acceptance" in warning for warning in warnings))

    def test_rejects_duplicate_keys_and_non_json_numbers(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', b'\xff', b'{'):
            with self.assertRaises(renderer.ArchitectureError):
                renderer.load_json(raw)

    def test_numbers_never_silently_lose_viewer_precision(self):
        for raw in (b'{"x":9007199254740993}', b'{"x":-9007199254740993}', b'{"x":1e20}', b'{"x":0.123456789012345678901}', b'{"x":1e-999}'):
            with self.assertRaises(renderer.ArchitectureError):
                renderer.load_json(raw)
        self.assertEqual(renderer.load_json(b'{"x":0.1,"y":9007199254740991}'), {"x": 0.1, "y": 9007199254740991})
        self.assertEqual(renderer.safe_json(renderer.load_json(b'{"x":-0}')), '{"x":-0.0}')
        data = fixture()
        data["contracts"][0]["examples"][0]["input"] = {"id": 9007199254740993}
        self.assert_invalid(data, "safe range")
        with self.assertRaisesRegex(renderer.ArchitectureError, "safe range"):
            renderer.safe_json({"id": 9007199254740993})

    def test_depth_limit(self):
        with self.assertRaisesRegex(renderer.ArchitectureError, "safety limit"):
            renderer.load_json(("[" * 65 + "0" + "]" * 65).encode())


class RenderTests(unittest.TestCase):
    def test_single_file_html_embeds_exact_data_and_provenance(self):
        data = fixture()
        raw = json.dumps(data, ensure_ascii=False, indent=3).encode()
        before = copy.deepcopy(data)
        document = renderer.render_document(data, raw, "source.json", [])
        parsed = ParsedHTML()
        parsed.feed(document)
        self.assertEqual(json.loads(parsed.scripts["architecture-data"]), data)
        meta = json.loads(parsed.scripts["render-metadata"])
        self.assertEqual(meta["sourceSha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(meta["sourceName"], "source.json")
        self.assertEqual(len(meta["assetsSha256"]), 64)
        self.assertEqual(parsed.remote_attributes, [])
        self.assertTrue(any(m.get("http-equiv") == "Content-Security-Policy" for m in parsed.metas))
        self.assertNotIn("@@VIEWER_", document)
        self.assertEqual(data, before)

    def test_script_breakout_and_template_marker_injection_are_inert(self):
        data = fixture()
        poison = '</script><script>alert("x")</script><img src=x onerror=alert(1)> & \u2028 @@VIEWER_JS@@ @@ARCHITECTURE_DATA@@'
        data["title"] = poison
        data["contracts"][0]["examples"][0]["input"] = {"text": poison}
        raw = json.dumps(data).encode()
        document = renderer.render_document(data, raw, "</script>", [poison])
        parsed = ParsedHTML()
        parsed.feed(document)
        self.assertEqual(len(parsed.scripts), 3)
        self.assertNotIn('<img src=x', document)
        self.assertEqual(json.loads(parsed.scripts["architecture-data"]), data)
        self.assertEqual(json.loads(parsed.scripts["render-metadata"])["warnings"], [poison])
        self.assertIn("\\u003c/script\\u003e", parsed.scripts["architecture-data"])

    def test_template_markers_are_required_exactly_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "assets").mkdir()
            (root / "assets" / "viewer.html").write_text("broken")
            (root / "assets" / "viewer.css").write_text("")
            (root / "assets" / "viewer.js").write_text("")
            with patch.object(renderer, "ROOT", root):
                with self.assertRaisesRegex(renderer.ArchitectureError, "exactly once"):
                    renderer.render_document(fixture(), b"{}", "source", [])

    def test_unsafe_asset_closing_tags_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "assets").mkdir()
            for kind in ("html", "css", "js"):
                (root / "assets" / ("viewer." + kind)).write_text("</script>" if kind == "js" else "")
            with patch.object(renderer, "ROOT", root):
                with self.assertRaisesRegex(renderer.ArchitectureError, "unsafe closing"):
                    renderer.render_document(fixture(), b"{}", "source", [])


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.json"
        self.raw = (ROOT / "assets" / "demo.json").read_bytes()
        self.source.write_bytes(self.raw)
        self.output = self.root / "view.html"

    def run_cli(self, *args, source=None):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "render_architecture.py"), str(source or self.source), *map(str, args)], capture_output=True, text=True)

    def test_validate_and_render_workflow_preserves_source(self):
        result = self.run_cli("--validate-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.output.exists())
        result = self.run_cli("--output", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertIn("architecture-data", self.output.read_text())
        original = self.output.read_bytes()
        result = self.run_cli("--output", self.output)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Refusing to overwrite", result.stderr)
        self.assertEqual(self.output.read_bytes(), original)

    def test_write_failure_never_unlinks_concurrent_replacement(self):
        output = self.output
        original_fdopen = renderer.os.fdopen

        class ReplacedWriter:
            def __init__(self, fd, mode):
                self.stream = original_fdopen(fd, mode)

            def __enter__(self):
                return self

            def write(self, data):
                self.stream.close()  # Permit the replacement simulation on Windows.
                output.rename(output.with_suffix(".partial"))
                output.write_text("another actor's file")
                raise OSError("simulated disk failure")

            def __exit__(self, *_):
                self.stream.close()

        stderr = io.StringIO()
        with patch.object(renderer.os, "fdopen", ReplacedWriter), patch.object(renderer.sys, "stderr", stderr):
            self.assertEqual(renderer.main([str(self.source), "--output", str(output)]), 2)
        self.assertEqual(output.read_text(), "another actor's file")
        self.assertTrue(output.with_suffix(".partial").exists())
        self.assertIn("retained for inspection", stderr.getvalue())
        self.assertEqual(self.source.read_bytes(), self.raw)

    @unittest.skipUnless(renderer._can_pin_output_directory(), "POSIX directory descriptors required")
    def test_parent_swap_cannot_redirect_output(self):
        selected = self.root / "selected"
        moved = self.root / "moved"
        foreign = self.root / "foreign"
        selected.mkdir()
        foreign.mkdir()
        output = selected / "view.html"
        original_open_parent = renderer._open_output_directory

        def swap_after_pin(parent):
            descriptor = original_open_parent(parent)
            selected.rename(moved)
            selected.symlink_to(foreign, target_is_directory=True)
            return descriptor

        with patch.object(renderer, "_open_output_directory", swap_after_pin), patch.object(renderer.sys, "stdout", io.StringIO()):
            self.assertEqual(renderer.main([str(self.source), "--output", str(output)]), 0)
        self.assertTrue((moved / "view.html").is_file())
        self.assertFalse((foreign / "view.html").exists())

    @unittest.skipUnless(renderer._can_pin_output_directory(), "POSIX hardened directory path only")
    def test_symlink_ancestors_and_parent_traversal_are_rejected(self):
        actual = self.root / "actual"
        actual.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(actual, target_is_directory=True)
        result = self.run_cli("--output", alias / "view.html")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((actual / "view.html").exists())
        result = self.run_cli("--output", actual / ".." / "view.html")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not contain", result.stderr)
        self.assertFalse(self.output.exists())

    def test_native_fallback_exclusive_creation_and_warning(self):
        stderr = io.StringIO()
        with patch.object(renderer, "_can_pin_output_directory", lambda: False), patch.object(renderer.sys, "stdout", io.StringIO()), patch.object(renderer.sys, "stderr", stderr):
            self.assertEqual(renderer.main([str(self.source), "--output", str(self.output)]), 0)
            original = self.output.read_bytes()
            self.assertEqual(renderer.main([str(self.source), "--output", str(self.output)]), 2)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertIn("stable output directory", stderr.getvalue())

    def test_requires_explicit_output_or_validation_mode(self):
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.run_cli("--output", self.output, "--validate-only").returncode, 2)

    def test_rejects_output_symlinks_including_dangling(self):
        for target in (self.source, self.root / "not-created"):
            try:
                self.output.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlink creation is unavailable: {exc}")
            result = self.run_cli("--output", self.output)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(self.output.is_symlink())
            self.output.unlink()
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_same_source_target_suffix_and_missing_parent(self):
        source = self.root / "source.html"
        source.write_bytes(self.raw)
        result = self.run_cli("--output", source, source=source)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(source.read_bytes(), self.raw)
        self.assertEqual(self.run_cli("--output", self.root / "output.json").returncode, 2)
        self.assertEqual(self.run_cli("--output", self.root / "absent" / "out.html").returncode, 2)
        self.assertFalse((self.root / "absent").exists())

    def test_invalid_source_never_creates_output(self):
        for raw in (b"{bad", b'{"schemaVersion":"unsupported"}', b"x" * (renderer.MAX_SOURCE_BYTES + 1)):
            self.source.write_bytes(raw)
            result = self.run_cli("--output", self.output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
