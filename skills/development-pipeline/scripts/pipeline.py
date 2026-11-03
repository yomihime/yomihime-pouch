#!/usr/bin/env python3
"""Local event recorder and read-only observer; never executes project work."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit


WORKSPACE_NAME = ".agent-workspace"
WORKSPACE_RESERVED_DIRS = frozenset({"memory", "design", "architecture", "plans", "work", WORKSPACE_NAME})


class PipelineError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PipelineError(message)


def text(value, name, nonempty=False):
    require(isinstance(value, str), f"{name} must be text")
    require(not nonempty or bool(value.strip()), f"{name} must not be empty")
    return value


def printable(value):
    """Keep reported text from injecting terminal controls into human projections."""
    return "".join(f"\\u{ord(char):04x}" if ord(char) < 32 or ord(char) == 127 else char for char in str(value))


def normalize_write(value):
    """A portable logical range in one workspace, not an OS path sandbox."""
    value = text(value, "writes", True).replace("\\", "/")
    if value == ".":
        return value
    components = value.split("/")
    devices = {"con", "prn", "aux", "nul", "conin$", "conout$"}
    devices.update(prefix + suffix for prefix in ("com", "lpt") for suffix in "123456789¹²³")
    for component in components:
        require(component not in {"", ".", ".."}, "writes must be workspace-relative ranges without empty, dot or parent components; use '.' for the entire workspace")
        require(not component.endswith((".", " ")), "writes components cannot end with a dot or space")
        require(not any(char in '<>:"|?*' or unicodedata.category(char) == "Cc" for char in component), "writes contains a forbidden path character")
        require(component.split(".", 1)[0].rstrip(" .").casefold() not in devices, "writes cannot use Windows device names")
    return "/".join(components)


def strict_json(value):
    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = item
        return result
    def invalid_constant(value):
        raise PipelineError(f"invalid JSON constant: {value}")
    return json.loads(value, object_pairs_hook=pairs, parse_constant=invalid_constant)


@contextmanager
def locked(run_dir, create=False, lock_name=".pipeline.lock"):
    """The same OS lock protects readers and writers, including separate servers."""
    directory = Path(run_dir).resolve()
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    require(directory.is_dir(), f"run directory does not exist: {directory}")
    with (directory / lock_name).open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.02)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield directory
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def normalize_plan(plan, complete=False):
    require(isinstance(plan, dict) and isinstance(plan.get("rounds"), list), "plan requires rounds array")
    require(set(plan) == {"rounds"}, "unsupported plan fields")
    result = {"rounds": []}
    seen = set()
    for index, source in enumerate(plan["rounds"]):
        require(isinstance(source, dict), "round must be an object")
        require(set(source) <= {"id", "title", "tasks", "gates"}, "unsupported round fields")
        round_ = {"id": source.get("id"), "title": source.get("title", ""), "tasks": [], "gates": []}
        for key in ("id", "title"):
            text(round_[key], f"round {key}", key == "id" or complete)
        require(round_["id"] not in seen, "IDs must be globally unique")
        seen.add(round_["id"])
        for collection in ("tasks", "gates"):
            require(isinstance(source.get(collection, []), list), f"{collection} must be an array")
            for node in source.get(collection, []):
                require(isinstance(node, dict), "node must be an object")
                common = {"id", "title", "required"}
                extra = {"role", "writes", "resources"} if collection == "tasks" else {"kind", "return_to"}
                require(set(node) <= common | extra, "unsupported node fields (use separate rounds for dependencies)")
                item = {"id": node.get("id"), "title": node.get("title", ""), "required": node.get("required", True)}
                text(item["id"], "node id", True)
                text(item["title"], "node title", complete)
                require(item["id"] not in seen, "IDs must be globally unique")
                seen.add(item["id"])
                require(type(item["required"]) is bool, "required must be boolean")
                if collection == "tasks":
                    item["role"] = text(node.get("role", ""), "role")
                    for key in ("writes", "resources"):
                        values = node.get(key, [])
                        require(isinstance(values, list), f"{key} must be an array")
                        item[key] = [normalize_write(value) if key == "writes" else text(value, key, True) for value in values]
                else:
                    item["kind"] = text(node.get("kind", "review"), "kind", True)
                    item["return_to"] = text(node.get("return_to", round_["id"]), "return_to", True)
                round_[collection].append(item)
        result["rounds"].append(round_)
    ids = [round_["id"] for round_ in result["rounds"]]
    for index, round_ in enumerate(result["rounds"]):
        for gate in round_["gates"]:
            require(gate["return_to"] in ids[:index + 1], "return_to must name this or an earlier round")
    if complete:
        require(bool(ids), "start requires at least one round")
        require(all(round_["tasks"] for round_ in result["rounds"]), "each round requires tasks")
        require(any(gate["required"] and gate["kind"] in {"test", "review"}
                    for gate in result["rounds"][-1]["gates"]), "final round requires a required test or review gate")
    return result


def reset_node(node, attempt):
    node.update(status="pending", note="", evidence=[], candidate=None, updated_at=None, attempt=attempt)


def done(node):
    return node["status"] in {"passed", "skipped"}


def project_rounds(state):
    first = None
    for round_ in state["rounds"]:
        nodes = round_["tasks"] + round_["gates"]
        if nodes and all(done(node) for node in nodes):
            round_["status"] = "passed"
        elif any(node["status"] == "failed" for node in nodes):
            round_["status"] = "failed"
        elif any(node["status"] != "pending" for node in nodes):
            round_["status"] = "running"
        else:
            round_["status"] = "pending"
        if first is None and round_["status"] != "passed":
            first = round_["id"]
            if round_["status"] == "pending" and state["status"] != "draft":
                round_["status"] = "ready"
    state["current_round"] = first if state["status"] != "draft" else None
    if state["status"] == "running" and first is None:
        state["status"] = "completed"


def find_node(state, entity_id, collection):
    for round_ in state["rounds"]:
        for node in round_[collection]:
            if node["id"] == entity_id:
                return round_, node
    raise PipelineError(f"unknown {collection}: {entity_id}")


def conflict(left, right):
    for a in left["writes"]:
        for b in right["writes"]:
            a, b = normalize_write(a).casefold(), normalize_write(b).casefold()
            if a == b or a.startswith(b + "/") or b.startswith(a + "/") or a == "." or b == ".":
                return True
    return bool({value.casefold() for value in left["resources"]} & {value.casefold() for value in right["resources"]})


def apply_event(state, event):
    require(isinstance(event, dict), "event must be an object")
    require(type(event.get("seq")) is int and event["seq"] == (state["revision"] + 1 if state else 1), "invalid event sequence")
    text(event.get("time"), "event time", True)
    try:
        require(datetime.fromisoformat(event["time"]).tzinfo is not None, "event time must include timezone")
    except ValueError as error:
        raise PipelineError("invalid event timestamp") from error
    kind = event.get("kind")
    fields = {
        "init": {"version", "run_id", "title", "demo", "project"}, "plan": {"plan"}, "start": set(),
        "task": {"status", "evidence", "candidate"}, "gate": {"status", "evidence", "candidate"},
        "decide": {"decision", "quiesced"}, "note": set(),
    }
    require(kind in fields, f"unknown event kind: {kind}")
    base_fields = {"seq", "time", "kind", "entity_id", "round_id", "attempt", "note"}
    require(base_fields <= set(event) <= base_fields | fields[kind], "missing or unsupported event fields")
    require(type(event["attempt"]) is int and event["attempt"] >= 1, "invalid event attempt")
    for key in ("entity_id", "round_id"):
        require(event[key] is None or isinstance(event[key], str), f"invalid {key}")
    if kind in {"init", "plan", "start"}:
        require(event["entity_id"] is None and event["round_id"] is None, "unexpected event target")
    if kind == "decide":
        require(event["entity_id"] is None, "unexpected decision entity")
        require(type(event.get("quiesced", False)) is bool, "quiesced must be boolean")
        if event.get("decision") != "return":
            require(event["round_id"] is None and not event.get("quiesced", False), "only return accepts round/quiesced")
    if kind == "note":
        require(event["round_id"] is None, "unexpected note round")
    text(event.get("note"), "event note")
    require("entity_id" in event and "round_id" in event, "missing event identity")
    if not state:
        require(kind == "init", "first event must initialize run")
        text(event.get("run_id"), "run_id", True)
        text(event.get("title"), "title", True)
        require(type(event.get("version")) is int and event["version"] == 1 and type(event.get("demo")) is bool, "invalid init metadata")
        require(event.get("attempt") == 1, "initial attempt must be 1")
        project = event.get("project")
        if project is not None:
            require(isinstance(project, dict) and set(project) == {"id", "name", "root"}, "invalid project identity")
            for key in project:
                text(project[key], f"project {key}", True)
        state = {"version": 1, "run_id": event["run_id"], "title": event["title"], "demo": event["demo"],
                 "project": copy.deepcopy(project),
                 "status": "draft", "revision": 0, "attempt": 1, "current_round": None, "rounds": [], "events": [], "updated_at": None}
    else:
        expected_attempt = state["attempt"] + (1 if kind == "decide" and event.get("decision") == "return" else 0)
        require(type(event.get("attempt")) is int and event["attempt"] == expected_attempt, "invalid event attempt")
        if kind == "plan":
            require(state["status"] == "draft", "plan cannot change after start")
            plan = normalize_plan(event.get("plan"))
            state["rounds"] = copy.deepcopy(plan["rounds"])
            for index, round_ in enumerate(state["rounds"]):
                round_["index"] = index
                for node in round_["tasks"] + round_["gates"]:
                    reset_node(node, state["attempt"])
        elif kind == "start":
            require(state["status"] == "draft", "run already started")
            # The source plan is kept in the event stream; strip projection fields.
            definition = {"rounds": []}
            for round_ in state["rounds"]:
                item = {key: round_[key] for key in ("id", "title")}
                for collection in ("tasks", "gates"):
                    keys = ("id", "title", "required", "role", "writes", "resources") if collection == "tasks" else ("id", "title", "required", "kind", "return_to")
                    item[collection] = [{key: node[key] for key in keys} for node in round_[collection]]
                definition["rounds"].append(item)
            normalize_plan(definition, complete=True)
            state["status"] = "running"
        elif kind in {"task", "gate"}:
            collection = "tasks" if kind == "task" else "gates"
            round_, node = find_node(state, event["entity_id"], collection)
            require(event["round_id"] == round_["id"] == state["current_round"], "round barrier is not satisfied")
            status = event.get("status")
            require(status in {"running", "passed", "failed", "skipped"}, "invalid node status")
            inflight_result = (state["status"] in {"needs_decision", "consulting", "blocked"}
                               and node["status"] == "running" and status in {"passed", "failed"})
            require(state["status"] == "running" or inflight_result, "run is not accepting new work; only in-flight terminal results are allowed during failure decisions")
            require(node["status"] == ("pending" if status in {"running", "skipped"} else "running"), "invalid or repeated node transition")
            if kind == "gate":
                require(all(done(task) for task in round_["tasks"]), "tasks must complete before gates")
                require(all(done(gate) for gate in round_["gates"][:round_["gates"].index(node)]), "earlier gates must complete first")
            if status == "running" and kind == "task":
                require(not any(other["status"] == "running" and conflict(node, other) for other in round_["tasks"]), "running task has overlapping writes or resources")
            if status == "skipped":
                require(not node["required"], "required node cannot be skipped")
                text(event["note"], "skip reason", True)
            if status == "failed":
                text(event["note"], "failure reason", True)
            evidence = event.get("evidence", [])
            require(isinstance(evidence, list), "evidence must be an array")
            for item in evidence:
                require(isinstance(item, dict) and set(item) == {"path", "sha256"}, "invalid evidence record")
                text(item["path"], "evidence path", True)
                require(isinstance(item["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]), "invalid evidence hash")
            candidate = event.get("candidate")
            require(candidate is None or isinstance(candidate, str), "candidate must be text")
            if status == "passed":
                require(bool(evidence), "passed requires evidence")
                text(candidate, "candidate", True)
            node.update(status=status, note=event["note"], evidence=evidence, candidate=candidate,
                        updated_at=event["time"], attempt=state["attempt"])
            if status == "failed" and state["status"] == "running":
                state["status"] = "needs_decision"
        elif kind == "decide":
            require(state["status"] in {"needs_decision", "consulting", "blocked"}, "decision requires unresolved failure")
            text(event["note"], "decision reason", True)
            decision = event.get("decision")
            require(decision in {"consult", "return", "block"}, "invalid decision")
            if decision == "return":
                ids = [round_["id"] for round_ in state["rounds"]]
                require(event["round_id"] in ids and ids.index(event["round_id"]) <= ids.index(state["current_round"]), "return target must be current or earlier round")
                running = any(node["status"] == "running" for round_ in state["rounds"] for node in round_["tasks"] + round_["gates"])
                require(not running or event.get("quiesced") is True, "running work requires --quiesced confirmation before return")
                state["attempt"] = event["attempt"]
                for round_ in state["rounds"][ids.index(event["round_id"]):]:
                    for node in round_["tasks"] + round_["gates"]:
                        reset_node(node, state["attempt"])
                state["status"] = "running"
            else:
                require(state["status"] in {"needs_decision", "consulting"}, "blocked run requires return to resume")
                require(not (decision == "consult" and state["status"] == "consulting"), "already consulting")
                state["status"] = "consulting" if decision == "consult" else "blocked"
        elif kind == "note":
            ids = {state["run_id"]} | {round_["id"] for round_ in state["rounds"]}
            for round_ in state["rounds"]:
                ids.update(node["id"] for node in round_["tasks"] + round_["gates"])
            require(event["entity_id"] in ids, "unknown note target")
            text(event["note"], "note", True)
            for round_ in state["rounds"]:
                for node in round_["tasks"] + round_["gates"]:
                    if node["id"] == event["entity_id"]:
                        node["note"] = event["note"]
                        node["updated_at"] = event["time"]
        else:
            raise PipelineError(f"unknown event kind: {kind}")
    state["events"].append(copy.deepcopy(event))
    state["revision"] = event["seq"]
    state["updated_at"] = event["time"]
    project_rounds(state)
    return state


def replay(directory):
    source = directory / "events.jsonl"
    require(source.is_file() and not source.is_symlink(), f"event log must be a regular non-symlink file: {source}")
    data = source.read_bytes()
    require(bool(data) and data.endswith(b"\n"), "corrupt event log: missing final newline or empty log")
    state = None
    for line_number, line in enumerate(data.splitlines(), 1):
        try:
            require(bool(line), "empty event line")
            state = apply_event(state, strict_json(line.decode("utf-8")))
        except (ValueError, KeyError, TypeError, UnicodeError, AttributeError, IndexError, RecursionError) as error:
            raise PipelineError(f"corrupt event log at line {line_number}: {error}") from error
    return state


def read_state(run_dir):
    with locked(run_dir) as directory:
        return replay(directory)


def evidence_records(paths):
    records = []
    for value in paths or []:
        path = Path(value).resolve()
        require(path.is_file(), f"evidence file does not exist: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append({"path": str(path), "sha256": digest.hexdigest()})
    return records


def mutate(run_dir, kind, **payload):
    with locked(run_dir, create=kind == "init") as directory:
        if kind == "init":
            require(not (directory / "events.jsonl").exists(), "run already initialized")
            require(not (directory / "observer").exists() and not (directory / "report.html").exists(), "observer output already exists; choose a new run directory")
            state = None
        else:
            state = replay(directory)
        event = {"seq": state["revision"] + 1 if state else 1,
                 "time": datetime.now(timezone.utc).isoformat(), "kind": kind,
                 "entity_id": None, "round_id": None, "attempt": state["attempt"] if state else 1, "note": ""}
        event.update(payload)
        if kind == "init":
            project_root = event.pop("project_root", None)
            if project_root is None:
                workspace = enclosing_work_dir(directory)
                project_root = workspace.parent if workspace is not None else directory.parent
            project_root = Path(project_root).resolve()
            require(project_root.is_dir() and directory.is_relative_to(project_root), "run directory must be inside its project root")
            identity = str(project_root)
            key = os.path.normcase(identity)
            event["project"] = {"id": hashlib.sha256(key.encode("utf-8")).hexdigest(), "name": project_root.name or identity, "root": identity}
            event.update(version=1, run_id=str(uuid.uuid4()))
        elif kind in {"task", "gate"}:
            round_, _ = find_node(state, event["entity_id"], "tasks" if kind == "task" else "gates")
            event["round_id"] = round_["id"]
            event["evidence"] = evidence_records(event.pop("evidence_paths", []))
        elif kind == "decide" and event.get("decision") == "return":
            event["attempt"] += 1
        next_state = apply_event(copy.deepcopy(state), event)
        encoded = (json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        with (directory / "events.jsonl").open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            write_observer(directory, next_state, refresh_assets=kind == "init")
        except (OSError, PipelineError) as error:
            raise PipelineError(f"event #{event['seq']} was recorded, but observer output failed: {error}; run 'view' to rebuild without repeating the event") from error
    # Never acquire the project lock while holding a run lock. The index takes
    # that project lock before replaying runs, so concurrent writers cannot
    # deadlock or publish an older projection after a newer one.
    try:
        rebuild_enclosing_index(directory)
    except (OSError, PipelineError) as error:
        raise PipelineError(f"event #{event['seq']} was recorded, but index output failed: {error}; run 'index' to rebuild without repeating the event") from error
    return event, next_state


def atomic_text(path, content):
    require(not path.is_symlink(), f"observer output cannot be a symlink: {path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def script_json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def write_observer(directory, state, refresh_assets=False):
    """Disposable projection of the journal; no server, global registry or storage."""
    target = directory / "observer"
    require(not target.is_symlink(), "observer directory cannot be a symlink")
    target.mkdir(exist_ok=True)
    assets = Path(__file__).resolve().parents[1] / "assets" / "observer"
    config = {"transport": "script", "run_id": state["run_id"], "project_id": (state.get("project") or {}).get("id")}
    if refresh_assets or not (target / "index.html").exists():
        template = (assets / "index.html").read_text(encoding="utf-8")
        settings = '<script id="observer-config" type="application/json">' + script_json(config) + '</script>'
        atomic_text(target / "index.html", template.replace("<!-- observer-config -->", settings))
        for name in ("app.js", "styles.css"):
            atomic_text(target / name, (assets / name).read_text(encoding="utf-8"))
    atomic_text(target / "state.js", "window.pipelineReceive(" + script_json(state) + ");\n")
    if state["status"] == "completed":
        template = (assets / "index.html").read_text(encoding="utf-8")
        settings = '<script id="observer-config" type="application/json">' + script_json({**config, "transport": "snapshot", "state": state}) + '</script>'
        report = template.replace("<!-- observer-config -->", settings)
        report = report.replace('<link rel="stylesheet" href="styles.css">', "<style>" + (assets / "styles.css").read_text(encoding="utf-8") + "</style>")
        report = report.replace('<script src="app.js" defer></script>', "")
        # The app needs the body nodes before initialization when embedded inline.
        embedded_app = "<script>" + (assets / "app.js").read_text(encoding="utf-8") + "</script>"
        atomic_text(directory / "report.html", report.replace("</body>", embedded_app + "\n</body>"))
    return target / "index.html"


def build_observer(run_dir):
    with locked(run_dir) as directory:
        target = write_observer(directory, replay(directory), refresh_assets=True)
    rebuild_enclosing_index(directory)
    return target


def enclosing_work_dir(directory):
    directory = Path(directory).resolve()
    return next((p for p in (directory, *directory.parents) if p.name == WORKSPACE_NAME), None)


def rebuild_enclosing_index(directory):
    work = enclosing_work_dir(directory)
    if work is not None:
        return build_index(work)
    return None


def build_index(work_dir):
    """Index canonical work-id/pipeline journals, never backups or a registry."""
    work = Path(work_dir)
    require(not work.is_symlink(), "index directory cannot be a symlink")
    require(work.name == WORKSPACE_NAME, f"index directory must be named {WORKSPACE_NAME}")
    work.mkdir(parents=True, exist_ok=True)
    entries = []
    with locked(work, lock_name=".pipeline-index.lock") as work:
        for work_item in sorted(work.iterdir()):
            if work_item.name in WORKSPACE_RESERVED_DIRS or work_item.is_symlink():
                continue
            root = work_item / "pipeline"
            try:
                # A journal copied into init/staging, init/backups, memory, or a
                # nested project is not a live project run. Explicit paths still
                # work with run commands, but only this layout is discoverable.
                if not work_item.is_dir() or root.is_symlink() or not root.is_dir():
                    continue
                journal = root / "events.jsonl"
                if not journal.exists() and not journal.is_symlink():
                    continue
                state = read_state(root)
                relative = root.relative_to(work)
                def link(name):
                    path = root / name
                    if path.is_symlink() or not path.is_file():
                        return None
                    return "./" + quote((relative / name).as_posix(), safe="/")
                observer = root / "observer"
                observer_link = None if observer.is_symlink() else link("observer/index.html")
                entries.append({"title": state["title"], "run_id": state["run_id"],
                                "project": (state.get("project") or {}).get("name"),
                                "round": state["current_round"], "status": state["status"],
                                "updated_at": state["updated_at"], "revision": state["revision"],
                                "demo": state["demo"], "path": relative.as_posix(),
                                "observer": observer_link, "report": link("report.html") if state["status"] == "completed" else None})
            except (OSError, PipelineError, ValueError) as error:
                # Surface corrupt/inaccessible journals without pretending their last
                # known state is current. No cached status is substituted.
                entries.append({"path": root.relative_to(work).as_posix(), "error": str(error)})
        assets = Path(__file__).resolve().parents[1] / "assets" / "index"
        template = (assets / "index.html").read_text(encoding="utf-8")
        template = template.replace("<!-- index-style -->", "<style>" + (assets / "styles.css").read_text(encoding="utf-8") + "</style>")
        template = template.replace("<!-- index-app -->", "<script>" + (assets / "app.js").read_text(encoding="utf-8") + "</script>")
        # Do not overwrite a pre-existing project file that is not ours.
        for filename, signature in (("index.html", "<!-- generated by development-pipeline index -->"),
                                    ("pipeline-index-data.js", "/* generated by development-pipeline index */")):
            output = work / filename
            require(not output.is_symlink(), f"index output cannot be a symlink: {output}")
            if output.exists():
                require(output.is_file(), f"refusing to overwrite unowned index output: {output}")
                with output.open("rb") as existing:
                    require(existing.read(len(signature)) == signature.encode("ascii"),
                            f"refusing to overwrite unowned index output: {output}")
        # The data file is replaced first: a reader sees a complete old or new
        # projection, never a partially-written script.
        atomic_text(work / "pipeline-index-data.js", "/* generated by development-pipeline index */\nwindow.pipelineIndexReceive(" + script_json({"generated_at": datetime.now(timezone.utc).isoformat(), "runs": entries}) + ");\n")
        atomic_text(work / "index.html", "<!-- generated by development-pipeline index -->\n" + template)
    return work / "index.html"


def mermaid(state):
    def label(value):
        return html.escape(printable(str(value).replace("\n", " ").replace("\r", " ")), quote=True).replace("`", "&#96;")
    lines = ["flowchart TD"]
    previous = None
    for index, round_ in enumerate(state["rounds"]):
        rid = f"r{index}"
        lines.append(f'  subgraph {rid}["{label(round_["title"])} · {round_["status"]}"]')
        nodes = []
        for offset, task in enumerate(round_["tasks"]):
            nid = f"{rid}t{offset}"
            nodes.append(nid)
            lines.append(f'    {nid}["{label(task["title"])} · {task["status"]}"]')
        for offset, gate in enumerate(round_["gates"]):
            nid = f"{rid}g{offset}"
            lines.append(f'    {nid}{{"{label(gate["title"])} · {gate["status"]}"}}')
            for source in nodes:
                lines.append(f"    {source} --> {nid}")
            nodes = [nid]
        lines.append("  end")
        if previous:
            for source in previous:
                for offset in range(len(round_["tasks"])):
                    lines.append(f"  {source} --> {rid}t{offset}")
        previous = nodes
    ids = {round_["id"]: i for i, round_ in enumerate(state["rounds"])}
    for index, round_ in enumerate(state["rounds"]):
        for offset, gate in enumerate(round_["gates"]):
            target = ids[gate["return_to"]]
            destination = f"r{target}t0" if state["rounds"][target]["tasks"] else f"r{target}"
            lines.append(f"  r{index}g{offset} -. return .-> {destination}")
    return "\n".join(lines)


def markdown(state):
    def safe(value):
        return html.escape(printable(str(value).replace("\n", " ").replace("\r", " "))).replace("|", "&#124;").replace("`", "&#96;")
    lines = [f"# {safe(state['title'])}", "", f"状态: {state['status']} · revision {state['revision']} · attempt {state['attempt']} · 当前轮次: {safe(state['current_round'] or '-')}", ""]
    if state["demo"]:
        lines += ["**合成演示记录，不代表真实项目验收。**", ""]
    for round_ in state["rounds"]:
        lines += [f"## {safe(round_['id'])}: {safe(round_['title'])} [{round_['status']}]", ""]
        for node in round_["tasks"] + round_["gates"]:
            lines.append(f"- {safe(node['id'])}: {safe(node['title'])} — {node['status']} (attempt {node['attempt']})")
            if node["note"]:
                lines.append(f"  备注: {safe(node['note'])}")
            if node["candidate"]:
                lines.append(f"  候选: {safe(node['candidate'])}")
            for record in node["evidence"]:
                lines.append(f"  证据: {safe(record['path'])} SHA256 {record['sha256']}")
        lines.append("")
    lines += ["## 事件", ""]
    for event in state["events"]:
        lines.append(f"- #{event['seq']} {event['time']} {event['kind']} {safe(event['entity_id'] or event['round_id'] or '')} {safe(event.get('status', event.get('decision', '')))} {safe(event['note'])}")
    return "\n".join(lines)


def make_server(run_dir, port=0, assets_dir=None):
    # Resolve once; request paths are never mapped to filesystem paths.
    directory = Path(run_dir).resolve()
    read_state(directory)
    assets = Path(assets_dir) if assets_dir else Path(__file__).resolve().parents[1] / "assets" / "observer"
    files = {"/": ("index.html", "text/html; charset=utf-8"), "/index.html": ("index.html", "text/html; charset=utf-8"),
             "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/styles.css": ("styles.css", "text/css; charset=utf-8")}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, body, content_type="text/plain; charset=utf-8", head=False):
            try:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                if not head:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                # Poll cancellation can close the client while a locked read waits.
                # Only response socket disconnects are normal; reads still report errors.
                self.close_connection = True

        def valid_host(self):
            return self.headers.get_all("Host", []) == [f"127.0.0.1:{self.server.server_port}"]

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, b"invalid Host")
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or parsed.fragment or parsed.query or "%" in self.path or "\\" in self.path:
                return self.reply(404, b"not found")
            if parsed.path == "/api/state":
                try:
                    body = json.dumps(read_state(directory), ensure_ascii=False, allow_nan=False).encode("utf-8")
                    return self.reply(200, body, "application/json; charset=utf-8")
                except (OSError, PipelineError) as error:
                    return self.reply(500, json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            if parsed.path not in files:
                return self.reply(404, b"not found")
            filename, mime = files[parsed.path]
            try:
                path = assets / filename
                if path.is_symlink() or path.resolve().parent != assets.resolve():
                    return self.reply(404, b"not found")
                return self.reply(200, path.read_bytes(), mime)
            except OSError:
                return self.reply(404, b"static resource unavailable")

        def reject_write(self):
            self.close_connection = True
            self.reply(405, b"read-only observer")

        do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = do_CONNECT = reject_write

        def do_HEAD(self):
            self.reply(405, b"read-only observer", head=True)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "plan", "start", "task", "gate", "decide", "note", "status", "view", "serve"):
        sub = commands.add_parser(command)
        sub.add_argument("run_dir")
        if command == "init":
            sub.add_argument("--title", required=True)
            sub.add_argument("--demo", action="store_true")
            sub.add_argument("--project-root")
        elif command == "plan":
            sub.add_argument("--file", required=True)
        elif command in {"task", "gate"}:
            sub.add_argument("entity_id")
            sub.add_argument("status", choices=("running", "passed", "failed", "skipped"))
            sub.add_argument("--note", default="")
            sub.add_argument("--evidence", action="append", default=[])
            sub.add_argument("--candidate")
        elif command == "decide":
            sub.add_argument("decision", choices=("consult", "return", "block"))
            sub.add_argument("--round", dest="round_id")
            sub.add_argument("--note", required=True)
            sub.add_argument("--quiesced", action="store_true")
        elif command == "note":
            sub.add_argument("--target", dest="entity_id", required=True)
            sub.add_argument("--text", dest="note", required=True)
        elif command == "status":
            group = sub.add_mutually_exclusive_group()
            group.add_argument("--json", action="store_true")
            group.add_argument("--mermaid", action="store_true")
        elif command == "serve":
            sub.add_argument("--port", type=int, default=8765)
    index = commands.add_parser("index", help=f"rebuild the project {WORKSPACE_NAME} index")
    index.add_argument("project_root", help=f"project root containing {WORKSPACE_NAME}")
    args = parser.parse_args(argv)
    try:
        if args.command == "index":
            project_root = Path(args.project_root).resolve()
            require(project_root.is_dir(), "project root must exist")
            print(build_index(project_root / WORKSPACE_NAME))
        elif args.command == "status":
            state = read_state(args.run_dir)
            print(json.dumps(state, ensure_ascii=False, indent=2) if args.json else mermaid(state) if args.mermaid else markdown(state))
        elif args.command == "view":
            print(build_observer(args.run_dir))
        elif args.command == "serve":
            require(0 <= args.port <= 65535, "port must be 0..65535")
            with make_server(args.run_dir, args.port) as server:
                print(f"Read-only observer: http://127.0.0.1:{server.server_port}/", flush=True)
                server.serve_forever()
        else:
            fields = vars(args).copy()
            command, run_dir = fields.pop("command"), fields.pop("run_dir")
            if command == "plan":
                fields = {"plan": normalize_plan(strict_json(Path(fields["file"]).read_text(encoding="utf-8")))}
            elif command in {"task", "gate"}:
                fields["evidence_paths"] = fields.pop("evidence")
            elif command == "decide":
                require(fields["decision"] == "return" or (fields["round_id"] is None and not fields["quiesced"]), "--round/--quiesced apply only to return")
                require(fields["decision"] != "return" or fields["round_id"] is not None, "return requires --round")
            event, state = mutate(run_dir, command, **fields)
            print(printable(f"#{event['seq']} {event['kind']} {event['entity_id'] or event['round_id'] or ''} {event.get('status', event.get('decision', ''))} → {state['status']} (attempt {state['attempt']})"))
            if command == "init":
                print(printable(str(Path(run_dir).resolve() / "observer" / "index.html")))
                work = enclosing_work_dir(run_dir)
                if work is not None:
                    print(printable(f"Project index: {work / 'index.html'}"))
            elif state["status"] == "completed":
                print(printable(f"Final static report: {Path(run_dir).resolve() / 'report.html'}"))
        return 0
    except (PipelineError, OSError, ValueError) as error:
        print(f"pipeline: {printable(error)}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
