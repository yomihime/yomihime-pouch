"""Run with python -X utf8 -m unittest discover -s .../tests -v."""
import copy
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import subprocess
from pipeline_test_processes import IsolatedProcesses
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pipeline.py"
spec = importlib.util.spec_from_file_location("pipeline", SCRIPT)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def plan():
    return {"rounds": [
        {"id": "r1", "title": "并行工作", "tasks": [
            {"id": "a", "title": "架构", "writes": ["src/core.py"]},
            {"id": "b", "title": "页面", "writes": ["ui"], "resources": ["browser"]},
            {"id": "optional", "title": "可选", "required": False}],
         "gates": [{"id": "review", "title": "首轮审查"}, {"id": "review2", "title": "复查"}]},
        {"id": "r2", "title": "验收", "tasks": [{"id": "c", "title": "构建"}],
         "gates": [{"id": "test", "title": "测试", "kind": "test", "return_to": "r1"}]}]}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.processes = IsolatedProcesses(self)
        self.temp = tempfile.TemporaryDirectory(prefix="pipeline-unit-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.run = self.base / "run"
        self.evidence = self.base / "result.txt"
        self.evidence.write_text("合成结果\n", encoding="utf-8")
        self.call("init", title="合成流水线", demo=True)

    def call(self, kind, **fields):
        return pipeline.mutate(self.run, kind, **fields)

    def start(self, definition=None):
        self.call("plan", plan=definition or plan())
        self.call("start")

    def node(self, kind, entity, status, **fields):
        return self.call(kind, entity_id=entity, status=status, **fields)

    def pass_node(self, kind, entity, candidate="candidate-1"):
        self.node(kind, entity, "running")
        return self.node(kind, entity, "passed", candidate=candidate, evidence_paths=[str(self.evidence)])

    def first_round(self):
        self.pass_node("task", "a")
        self.pass_node("task", "b")
        self.node("task", "optional", "skipped", note="本次不需要")
        self.pass_node("gate", "review")
        self.pass_node("gate", "review2")

    def state(self):
        return pipeline.read_state(self.run)

    def rejected_without_write(self, callback):
        before = (self.run / "events.jsonl").read_bytes()
        with self.assertRaises(pipeline.PipelineError):
            callback()
        self.assertEqual(before, (self.run / "events.jsonl").read_bytes())

    def test_drafts_can_be_revised_but_execution_freezes_structure(self):
        self.call("plan", plan={"rounds": []})
        self.assertEqual(self.state()["rounds"], [])
        self.rejected_without_write(lambda: self.call("start"))
        self.call("plan", plan={"rounds": [{"id": "draft"}]})
        self.assertEqual(self.state()["rounds"][0]["title"], "")
        self.rejected_without_write(lambda: self.call("start"))
        self.call("plan", plan=plan())
        self.call("start")
        self.rejected_without_write(lambda: self.call("plan", plan=plan()))
        self.assertEqual(sum(event["kind"] == "plan" for event in self.state()["events"]), 3)

    def test_project_identity_and_views_are_isolated(self):
        other = self.base / "other-project" / ".agent-workspace" / "one" / "pipeline"
        pipeline.mutate(other, "init", title="other", demo=True)
        first, second = self.state(), pipeline.read_state(other)
        self.assertEqual(second["project"]["root"], str(self.base / "other-project"))
        self.assertNotEqual(first["project"]["id"], second["project"]["id"])
        self.assertNotEqual(first["run_id"], second["run_id"])
        other_bytes = (other / "observer" / "state.js").read_bytes()
        self.call("plan", plan=plan())
        self.assertEqual(other_bytes, (other / "observer" / "state.js").read_bytes())
        data = (self.run / "observer" / "state.js").read_text(encoding="utf-8")
        projected = json.loads(data.removeprefix("window.pipelineReceive(").removesuffix(");\n"))
        self.assertEqual(projected, self.state())
        with self.assertRaises(pipeline.PipelineError):
            pipeline.mutate(self.base / "outside", "init", title="wrong", project_root=other)

    def test_final_report_is_self_contained_and_escapes_payload(self):
        self.call("plan", plan={"rounds": [{"id": "r", "title": "round", "tasks": [{"id": "t", "title": "task"}], "gates": [{"id": "g", "title": "review", "kind": "review"}]}]})
        self.call("start")
        self.pass_node("task", "t")
        self.node("gate", "g", "running")
        payload = '</script><img src=x onerror="globalThis.injected=1">'
        self.node("gate", "g", "passed", candidate="final", evidence_paths=[str(self.evidence)], note=payload)
        report = (self.run / "report.html").read_text(encoding="utf-8")
        self.assertNotIn(payload, report)
        self.assertNotIn('<script src="app.js"', report)
        self.assertNotIn('<link rel="stylesheet" href="styles.css"', report)
        self.assertIn('"transport": "snapshot"', report)
        self.assertEqual(self.state()["status"], "completed")

    def test_projection_failure_preserves_committed_event_and_view_repairs(self):
        before = self.state()["revision"]
        with patch.object(pipeline, "write_observer", side_effect=OSError("simulated full disk")):
            with self.assertRaisesRegex(pipeline.PipelineError, "was recorded"):
                self.call("plan", plan=plan())
        self.assertEqual(self.state()["revision"], before + 1)
        journal = (self.run / "events.jsonl").read_bytes()
        pipeline.build_observer(self.run)
        self.assertEqual(journal, (self.run / "events.jsonl").read_bytes())

    def test_legacy_log_can_build_view_without_fabricating_project(self):
        legacy = self.base / "legacy"
        legacy.mkdir()
        event = copy.deepcopy(self.state()["events"][0])
        event.pop("project")
        (legacy / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
        self.assertIsNone(pipeline.read_state(legacy)["project"])
        self.assertTrue(pipeline.build_observer(legacy).is_file())

    def test_start_requires_final_required_gate(self):
        definition = plan()
        definition["rounds"][-1]["gates"][0]["required"] = False
        self.call("plan", plan=definition)
        self.rejected_without_write(lambda: self.call("start"))

    def test_unique_ids_return_targets_and_unsupported_dependencies(self):
        for mutate_definition in (
            lambda p: p["rounds"][1]["tasks"][0].update(id="a"),
            lambda p: p["rounds"][0]["gates"][0].update(return_to="r2"),
            lambda p: p["rounds"][0]["tasks"][0].update(depends_on=["b"]),
            lambda p: p["rounds"][0]["tasks"][0].update(required="yes"),
        ):
            definition = plan()
            mutate_definition(definition)
            self.rejected_without_write(lambda: self.call("plan", plan=definition))

    def test_round_gate_barriers_and_concurrent_independent_tasks(self):
        self.start()
        self.rejected_without_write(lambda: self.node("task", "c", "running"))
        self.rejected_without_write(lambda: self.node("gate", "review", "running"))
        self.rejected_without_write(lambda: self.node("task", "a", "passed", candidate="x", evidence_paths=[str(self.evidence)]))
        self.node("task", "a", "running")
        self.node("task", "b", "running")
        self.assertEqual([n["status"] for n in self.state()["rounds"][0]["tasks"]][:2], ["running", "running"])
        for entity in ("a", "b"):
            self.node("task", entity, "passed", candidate="x", evidence_paths=[str(self.evidence)])
        self.rejected_without_write(lambda: self.node("gate", "review", "running"))
        self.node("task", "optional", "skipped", note="未纳入范围")
        self.rejected_without_write(lambda: self.node("gate", "review2", "running"))
        self.pass_node("gate", "review")
        self.pass_node("gate", "review2")
        self.assertEqual(self.state()["current_round"], "r2")
        self.pass_node("task", "c")
        self.node("gate", "test", "running")
        self.rejected_without_write(lambda: self.node("gate", "test", "passed", candidate="x"))
        self.rejected_without_write(lambda: self.node("gate", "test", "passed", evidence_paths=[str(self.evidence)]))
        self.node("gate", "test", "passed", candidate="x", evidence_paths=[str(self.evidence)])
        state = self.state()
        self.assertEqual(state["status"], "completed")
        self.assertIsNone(state["current_round"])
        self.assertTrue(all(r["status"] == "passed" for r in state["rounds"]))
        self.rejected_without_write(lambda: self.node("gate", "test", "passed", candidate="x", evidence_paths=[str(self.evidence)]))

    def test_shared_write_parent_case_and_resource_conflicts(self):
        for writes, resources in [(["SRC"], []), (["src\\CORE.py"], []), (["."], []), ([], ["GPU"])]:
            with self.subTest(writes=writes, resources=resources):
                run = self.base / ("conflict-" + str(len(list(self.base.iterdir()))))
                pipeline.mutate(run, "init", title="conflict", demo=True)
                definition = plan()
                definition["rounds"][0]["tasks"][0]["resources"] = ["gpu"]
                definition["rounds"][0]["tasks"][1].update(writes=writes, resources=resources)
                pipeline.mutate(run, "plan", plan=definition)
                pipeline.mutate(run, "start")
                pipeline.mutate(run, "task", entity_id="a", status="running")
                with self.assertRaises(pipeline.PipelineError):
                    pipeline.mutate(run, "task", entity_id="b", status="running")
                self.assertEqual(pipeline.read_state(run)["rounds"][0]["tasks"][1]["status"], "pending")

    def test_plan_rejects_write_aliases_before_they_can_bypass_exclusion(self):
        # These aliases previously admitted two simultaneous writers for one file.
        # Reject them portably at plan time rather than guessing a workspace root.
        invalid = [str((self.base / "src" / "same.py").resolve()),
                   "src/same.py.", "src/same.py ", "src./same.py", "src /same.py",
                   "/", "/src", "src/", "src//same.py", "src\\\\same.py",
                   "C:/src/same.py", "C:src/same.py", "//server/share/src",
                   "\\\\server\\share\\src", "\\\\?\\C:\\src", "\\\\.\\C:\\src",
                   "../src", "src/../same.py", "src/./same.py", "src/file:stream",
                   "src/line\nname", "src/tab\tname", "src/escape\x1b", "src/control\x85",
                   "src/a?b", "src/a*b", 'src/a"b', "src/a<b", "src/a>b", "src/a|b",
                   "NUL", "src/con.txt", "src/PRN.log", "src/AUX", "src/com1.py", "src/LPT9.txt",
                   "src/COM¹.txt", "src/lpt²", "src/CONIN$", "src/CONOUT$", "src/NUL .txt"]
        for write in invalid:
            with self.subTest(write=write):
                definition = plan()
                definition["rounds"][0]["tasks"][0]["writes"] = ["src/same.py"]
                definition["rounds"][0]["tasks"][1]["writes"] = [write]
                self.rejected_without_write(lambda: self.call("plan", plan=definition))
        self.assertEqual(self.state()["status"], "draft")

    def test_portable_logical_write_ranges_allow_dotfiles_and_normalize_slashes(self):
        definition = plan()
        definition["rounds"][0]["tasks"][0]["writes"] = [".gitignore", "src\\same.py", "valid...name", "component space/file"]
        definition["rounds"][0]["tasks"][1]["writes"] = ["SRC/same.PY"]
        self.start(definition)
        self.assertEqual(self.state()["rounds"][0]["tasks"][0]["writes"][1], "src/same.py")
        self.node("task", "a", "running")
        self.rejected_without_write(lambda: self.node("task", "b", "running"))

    def test_failed_requires_reason_for_task_and_gate(self):
        self.start()
        self.node("task", "a", "running")
        for note in ("", " \t\n"):
            self.rejected_without_write(lambda: self.node("task", "a", "failed", note=note))
        self.node("task", "a", "passed", candidate="x", evidence_paths=[str(self.evidence)])
        self.pass_node("task", "b")
        self.node("task", "optional", "skipped", note="不适用")
        self.node("gate", "review", "running")
        self.rejected_without_write(lambda: self.node("gate", "review", "failed"))
        self.node("gate", "review", "failed", note="审查发现冲突")
        self.assertEqual(self.state()["status"], "needs_decision")

    def test_evidence_candidate_and_skips_cannot_bypass_quality(self):
        self.start()
        self.rejected_without_write(lambda: self.node("task", "a", "skipped", note="no"))
        self.rejected_without_write(lambda: self.node("task", "optional", "skipped"))
        self.node("task", "a", "running")
        for fields in ({}, {"candidate": "x"}, {"candidate": " ", "evidence_paths": [str(self.evidence)]},
                       {"candidate": "x", "evidence_paths": [str(self.base / "missing")]},
                       {"candidate": "x", "evidence_paths": [str(self.base)]}):
            self.rejected_without_write(lambda: self.node("task", "a", "passed", **fields))
        self.node("task", "a", "passed", candidate="commit-sha", evidence_paths=[str(self.evidence)])
        record = self.state()["rounds"][0]["tasks"][0]
        self.assertEqual(record["evidence"], [{"path": str(self.evidence.resolve()), "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest()}])
        self.evidence.unlink()
        self.assertEqual(self.state()["rounds"][0]["tasks"][0], record, "historical proof is replayed without requiring old files to survive")

    def test_failure_consult_return_quiescence_and_attempt_history(self):
        self.start()
        self.node("task", "a", "running")
        self.node("task", "b", "running")
        failure, _ = self.node("task", "a", "failed", note="合成失败")
        self.assertEqual(self.state()["status"], "needs_decision")
        self.rejected_without_write(lambda: self.node("task", "optional", "running"))
        self.call("decide", decision="consult", note="分析失败")
        self.assertEqual(self.state()["status"], "consulting")
        self.rejected_without_write(lambda: self.call("decide", decision="return", round_id="r1", note="重做"))
        self.rejected_without_write(lambda: self.call("decide", decision="return", round_id="r2", note="不能跳过" , quiesced=True))
        self.call("decide", decision="return", round_id="r1", note="已实际交接", quiesced=True)
        state = self.state()
        self.assertEqual(state["attempt"], 2)
        self.assertEqual(state["events"][failure["seq"] - 1], failure)
        self.assertTrue(all(n["status"] == "pending" and n["attempt"] == 2 and not n["evidence"] and n["candidate"] is None
                            for r in state["rounds"] for n in r["tasks"] + r["gates"]))
        self.node("task", "a", "running")
        self.rejected_without_write(lambda: self.node("task", "a", "passed"))
        self.node("task", "a", "failed", note="新候选仍然失败")
        self.call("decide", decision="block", note="等待输入")
        self.assertEqual(self.state()["status"], "blocked")
        self.call("decide", decision="return", round_id="r1", note="输入已到")
        self.assertEqual(self.state()["attempt"], 3)

    def test_inflight_terminal_results_preserve_failure_decisions_and_history(self):
        sibling_evidence = self.base / "sibling-result.txt"
        sibling_evidence.write_text("Independent sibling result", encoding="utf-8")
        for failed_id in ("a", "b"):
            sibling_id = "b" if failed_id == "a" else "a"
            for decision in (None, "consult", "block"):
                for outcome in ("passed", "failed"):
                    with self.subTest(first_failure=failed_id, decision=decision, sibling_result=outcome):
                        run = self.base / f"inflight-{failed_id}-{decision}-{outcome}"
                        def call(kind, **fields):
                            return pipeline.mutate(run, kind, **fields)
                        def rejected(kind, **fields):
                            before = (run / "events.jsonl").read_bytes()
                            with self.assertRaises(pipeline.PipelineError):
                                call(kind, **fields)
                            self.assertEqual(before, (run / "events.jsonl").read_bytes())
                        call("init", title="inflight", demo=True)
                        call("plan", plan=plan())
                        call("start")
                        for entity in ("a", "b"):
                            call("task", entity_id=entity, status="running")
                        first_failure, _ = call("task", entity_id=failed_id, status="failed", note="first failure", candidate="first-v1", evidence_paths=[str(self.evidence)])
                        if decision:
                            call("decide", decision=decision, note="unresolved first failure")
                        expected = {None: "needs_decision", "consult": "consulting", "block": "blocked"}[decision]
                        rejected("task", entity_id="optional", status="running")
                        rejected("task", entity_id="optional", status="skipped", note="cannot start or skip pending work")
                        rejected("task", entity_id="c", status="running")
                        rejected("gate", entity_id="review", status="running")
                        rejected("decide", decision="return", round_id="r1", note="sibling still running")
                        rejected("task", entity_id=sibling_id, status="passed", candidate="sibling-v1")
                        rejected("task", entity_id=sibling_id, status="failed")
                        result, state = call("task", entity_id=sibling_id, status=outcome, note="sibling terminal result", candidate="sibling-v1", evidence_paths=[str(sibling_evidence)])
                        sibling = next(node for node in state["rounds"][0]["tasks"] if node["id"] == sibling_id)
                        self.assertEqual(state["status"], expected)
                        self.assertEqual(state["current_round"], "r1")
                        self.assertEqual(state["rounds"][0]["status"], "failed")
                        self.assertEqual((sibling["status"], sibling["candidate"], sibling["attempt"]), (outcome, "sibling-v1", 1))
                        self.assertEqual(sibling["evidence"], [{"path": str(sibling_evidence.resolve()), "sha256": hashlib.sha256(sibling_evidence.read_bytes()).hexdigest()}])
                        projected = json.loads((run / "observer" / "state.js").read_text(encoding="utf-8").removeprefix("window.pipelineReceive(").removesuffix(");\n"))
                        self.assertEqual(projected, state)
                        rejected("gate", entity_id="review", status="running")
                        rejected("task", entity_id=sibling_id, status=outcome, note="duplicate", candidate="sibling-v1", evidence_paths=[str(sibling_evidence)])
                        _, returned = call("decide", decision="return", round_id="r1", note="all in-flight results collected")
                        self.assertEqual(returned["attempt"], 2)
                        self.assertEqual(returned["events"][first_failure["seq"] - 1], first_failure)
                        self.assertEqual(returned["events"][result["seq"] - 1], result)
                        self.assertTrue(all(n["status"] == "pending" and n["attempt"] == 2 for r in returned["rounds"] for n in r["tasks"] + r["gates"]))

    def test_parallel_terminal_arrival_orders_keep_both_results(self):
        for outcome in ("passed", "failed"):
            for order in (("a", "b"), ("b", "a")):
                with self.subTest(sibling_result=outcome, order=order):
                    run = self.base / f"ordered-{outcome}-{''.join(order)}"
                    pipeline.mutate(run, "init", title="ordered", demo=True)
                    pipeline.mutate(run, "plan", plan=plan())
                    pipeline.mutate(run, "start")
                    for entity in ("a", "b"):
                        pipeline.mutate(run, "task", entity_id=entity, status="running")
                    for entity in order:
                        pipeline.mutate(run, "task", entity_id=entity, status="failed" if entity == "a" else outcome, note="terminal result", candidate=entity + "-v1", evidence_paths=[str(self.evidence)])
                    state = pipeline.read_state(run)
                    self.assertEqual(state["status"], "needs_decision")
                    self.assertEqual({n["id"]: n["status"] for n in state["rounds"][0]["tasks"]}, {"a": "failed", "b": outcome, "optional": "pending"})
                    self.assertEqual([e["entity_id"] for e in state["events"][-2:]], list(order))

    def test_concurrent_process_terminal_results_survive_first_failure(self):
        for outcome in ("passed", "failed"):
            with self.subTest(sibling_result=outcome):
                run = self.base / f"concurrent-results-{outcome}"
                pipeline.mutate(run, "init", title="concurrent results", demo=True)
                pipeline.mutate(run, "plan", plan=plan())
                pipeline.mutate(run, "start")
                for entity in ("a", "b"):
                    pipeline.mutate(run, "task", entity_id=entity, status="running")
                children = [self.processes.start([sys.executable, "-X", "utf8", str(SCRIPT), "task", str(run), entity, status, "--note", "terminal result", "--candidate", entity + "-v1", "--evidence", str(self.evidence)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            for entity, status in (("a", "failed"), ("b", outcome))]
                for child in children:
                    out, error = self.processes.communicate(child, timeout=30)
                    self.assertEqual(child.returncode, 0, (out, error))
                state = pipeline.read_state(run)
                self.assertEqual(state["status"], "needs_decision")
                self.assertEqual([e["seq"] for e in state["events"]], list(range(1, 8)))
                self.assertEqual({e["entity_id"] for e in state["events"][-2:]}, {"a", "b"})
                self.assertTrue(all(n["evidence"] and n["candidate"] == n["id"] + "-v1" for n in state["rounds"][0]["tasks"][:2]))

    def test_return_preserves_earlier_pass_identity(self):
        self.start()
        self.first_round()
        earlier = copy.deepcopy(self.state()["rounds"][0])
        self.pass_node("task", "c")
        self.node("gate", "test", "running")
        self.node("gate", "test", "failed", note="合成测试失败")
        self.call("decide", decision="return", round_id="r2", note="仅重做本轮")
        self.assertEqual(earlier, self.state()["rounds"][0])
        self.assertEqual(self.state()["rounds"][1]["tasks"][0]["attempt"], 2)

    def test_corrupt_logs_are_never_silently_repaired_or_appended(self):
        original = (self.run / "events.jsonl").read_bytes()
        corruptions = [original[:-1], original + b"\n", original + b"{bad}\n", original + original,
                       original.replace(b'"seq":1', b'"seq":NaN'),
                       original.replace(b'"seq":1', b'"seq":1,"seq":1'),
                       original.replace(b'"kind":"init"', b'"kind":"task"'),
                       original + b"\xff\n"]
        for data in corruptions:
            with self.subTest(data=data[-30:]):
                (self.run / "events.jsonl").write_bytes(data)
                with self.assertRaises(pipeline.PipelineError):
                    self.state()
                self.rejected_without_write(lambda: self.call("plan", plan=plan()))
        (self.run / "events.jsonl").write_bytes(original)

    def test_parallel_process_writes_have_contiguous_events(self):
        self.start()
        code = ("import importlib.util,sys; s=importlib.util.spec_from_file_location('p',sys.argv[1]);"
                "p=importlib.util.module_from_spec(s);s.loader.exec_module(p);"
                "[p.mutate(sys.argv[2],'note',entity_id='a',note=sys.argv[3]+'-'+str(i)) for i in range(8)]")
        children = [self.processes.start([sys.executable, "-X", "utf8", "-c", code, str(SCRIPT), str(self.run), str(i)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(4)]
        for child in children:
            out, error = self.processes.communicate(child, timeout=30)
            self.assertEqual(child.returncode, 0, (out, error))
        state = self.state()
        self.assertEqual(state["revision"], 35)
        self.assertEqual([event["seq"] for event in state["events"]], list(range(1, 36)))
        self.assertEqual(len({event["note"] for event in state["events"] if event["kind"] == "note"}), 32)

    def test_two_processes_cannot_start_same_node(self):
        self.start()
        commands = [sys.executable, "-X", "utf8", str(SCRIPT), "task", str(self.run), "a", "running"]
        children = [self.processes.start(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = [self.processes.communicate(child, timeout=30) for child in children]
        self.assertEqual(sorted(child.returncode for child in children), [0, 2], results)
        self.assertEqual(self.state()["revision"], 4)

    def test_cli_round_trip_with_utf8_and_decision_flags(self):
        run = self.base / "cli"
        definition = self.base / "plan.json"
        definition.write_text(json.dumps(plan(), ensure_ascii=False), encoding="utf-8")
        def cli(*args, success=True):
            result = self.processes.run([sys.executable, "-X", "utf8", str(SCRIPT), *map(str, args)], capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0 if success else 2, result.stderr)
            return result.stdout
        cli("init", run, "--title", "中文演示", "--demo")
        cli("plan", run, "--file", definition)
        cli("start", run)
        cli("task", run, "a", "running")
        cli("task", run, "a", "failed", "--note", "合成失败")
        cli("decide", run, "return", "--note", "缺少指定轮次", success=False)
        cli("decide", run, "consult", "--round", "r1", "--note", "参数不适用", success=False)
        cli("decide", run, "consult", "--note", "请顾问分析")
        cli("note", run, "--target", "a", "--text", "分析已记录")
        cli("decide", run, "return", "--round", "r1", "--note", "重做")
        cli("task", run, "a", "running")
        cli("task", run, "a", "passed", "--evidence", self.evidence, "--candidate", "新候选")
        state = json.loads(cli("status", run, "--json"))
        self.assertEqual(state["title"], "中文演示")
        self.assertEqual(state["attempt"], 2)
        self.assertEqual(state["rounds"][0]["tasks"][0]["candidate"], "新候选")
        self.assertIn("合成失败", cli("status", run))
        self.assertIn("flowchart TD", cli("status", run, "--mermaid"))

    def test_http_fixed_paths_readonly_host_and_cli_consistency(self):
        definition = plan()
        definition["rounds"][0]["tasks"][0]["title"] = '<script>alert("x")</script>'
        self.start(definition)
        assets = self.base / "assets"
        assets.mkdir()
        for name in ("index.html", "app.js", "styles.css"):
            (assets / name).write_text(name, encoding="utf-8")
        server = pipeline.make_server(self.run, assets_dir=assets)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)
        self.assertEqual(server.server_address[0], "127.0.0.1")
        before = (self.run / "events.jsonl").read_bytes()

        def request(path, method="GET", host=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            headers = {"Host": host} if host else {}
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            result = response.status, response.read(), dict(response.getheaders())
            connection.close()
            return result

        status, body, headers = request("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), self.state())
        cli = self.processes.run([sys.executable, "-X", "utf8", str(SCRIPT), "status", str(self.run), "--json"], capture_output=True, check=True)
        self.assertEqual(json.loads(cli.stdout), json.loads(body))
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertIn("img-src 'self' data:", headers["Content-Security-Policy"])
        self.assertIn("script-src 'self';", headers["Content-Security-Policy"])
        for path in ("/", "/index.html", "/app.js", "/styles.css"):
            self.assertEqual(request(path)[0], 200)
        for path in ("/events.jsonl", "/../events.jsonl", "/%2e%2e/events.jsonl", "/assets/app.js", "/api/state?cmd=task", "/C:/Windows/win.ini"):
            self.assertEqual(request(path)[0], 404, path)
        self.assertEqual(request("http://evil.example/api/state", host=f"127.0.0.1:{server.server_port}")[0], 404)
        for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"):
            self.assertEqual(request("/api/state", method=method)[0], 405)
        for host in ("evil.example", "localhost:" + str(server.server_port), "127.0.0.1:1"):
            self.assertEqual(request("/api/state", host=host)[0], 403)
        self.assertEqual(before, (self.run / "events.jsonl").read_bytes())
        (self.run / "events.jsonl").write_bytes(before[:-1])
        self.assertEqual(request("/api/state")[0], 500)

    def test_http_reply_handles_only_client_disconnects_and_keeps_serving(self):
        server = pipeline.make_server(self.run)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.shutdown)
        for phase in ("headers", "body"):
            for error_type in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                with self.subTest(phase=phase, error=error_type.__name__):
                    handler = object.__new__(server.RequestHandlerClass)
                    handler.send_response = Mock()
                    handler.send_header = Mock()
                    handler.end_headers = Mock(side_effect=error_type("client disconnected") if phase == "headers" else None)
                    handler.wfile = Mock()
                    if phase == "body":
                        handler.wfile.write.side_effect = error_type("client disconnected")
                    handler.close_connection = False
                    handler.reply(200, b"state")
                    self.assertTrue(handler.close_connection)
                    if phase == "headers":
                        handler.wfile.write.assert_not_called()
                    else:
                        handler.wfile.write.assert_called_once_with(b"state")
        handler.end_headers = Mock(side_effect=OSError("unexpected socket failure"))
        with self.assertRaises(OSError):
            handler.reply(200, b"state")
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        self.addCleanup(connection.close)
        connection.request("GET", "/api/state")
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.read()), self.state())

    def test_markdown_mermaid_do_not_interpolate_untrusted_structure(self):
        definition = plan()
        definition["rounds"][0]["id"] = 'r1"] --> injected'
        definition["rounds"][0]["gates"][0]["return_to"] = definition["rounds"][0]["id"]
        definition["rounds"][0]["gates"][1]["return_to"] = definition["rounds"][0]["id"]
        definition["rounds"][1]["gates"][0]["return_to"] = definition["rounds"][0]["id"]
        definition["rounds"][0]["title"] = '<img src=x onerror="alert(1)">\n" --> injected\x1b[2J'
        self.start(definition)
        rendered = pipeline.mermaid(self.state())
        self.assertNotIn('<img', rendered)
        self.assertNotIn('r1"] --> injected', rendered)
        self.assertIn("&quot;", rendered)
        self.assertIn("-. return .->", rendered)
        self.assertNotIn("\x1b", rendered)
        self.assertNotIn('<img', pipeline.markdown(self.state()))
        self.assertNotIn("\x1b", pipeline.markdown(self.state()))


if __name__ == "__main__":
    unittest.main()
