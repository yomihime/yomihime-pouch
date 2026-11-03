#!/usr/bin/env python3
"""Validate architecture JSON and render an offline, read-only HTML snapshot.

Python 3.9+ standard library only. Never reads evidence paths, fetches URLs,
changes source data, or overwrites an existing output. The bundled JSON Schema
is the structural authority; the local evaluator implements exactly its subset.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys

VERSION = "1.1.0"
MAX_SOURCE_BYTES = 5 * 1024 * 1024
MAX_ERRORS = 100
MAX_SAFE_INTEGER = 9007199254740991
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "architecture.schema.json"


class ArchitectureError(ValueError):
    """Invalid input, unsupported data, or unsafe output request."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArchitectureError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _integer(value):
    number = int(value)
    if abs(number) > MAX_SAFE_INTEGER:
        raise ArchitectureError("Integer exceeds JavaScript safe range; encode large identifiers and exact quantities as strings")
    return -0.0 if value == "-0" else number


def _number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ArchitectureError("JSON numbers must be finite")
    if Decimal(value) != Decimal(str(number)):
        raise ArchitectureError("Decimal loses precision in the viewer; encode exact decimals as strings")
    if number.is_integer() and abs(number) > MAX_SAFE_INTEGER:
        raise ArchitectureError("Integer-valued number exceeds JavaScript safe range; use a string")
    return number


def _constant(value):
    raise ArchitectureError(f"Non-standard JSON constant: {value}")


def load_json(raw: bytes):
    try:
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_object,
                          parse_int=_integer, parse_float=_number, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ArchitectureError(f"Invalid UTF-8 JSON: {exc}") from exc
    _check_data_limits(data)
    return data


def _check_data_limits(data):
    # Apply limits to extension/example payloads as well as schema fields,
    # including callers that pass Python data directly rather than load_json.
    stack = [(data, 0)]
    visited = 0
    while stack:
        value, depth = stack.pop()
        visited += 1
        if visited > 100000 or depth > 60:
            raise ArchitectureError("JSON exceeds the 100000-value or 60-level safety limit")
        if isinstance(value, dict):
            if not all(isinstance(key, str) for key in value):
                raise ArchitectureError("JSON object keys must be strings")
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)
        elif isinstance(value, bool) or value is None or isinstance(value, str):
            continue
        elif isinstance(value, int):
            if abs(value) > MAX_SAFE_INTEGER:
                raise ArchitectureError("Integer exceeds JavaScript safe range; use a string")
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ArchitectureError("JSON numbers must be finite")
            if value.is_integer() and abs(value) > MAX_SAFE_INTEGER:
                raise ArchitectureError("Integer-valued number exceeds JavaScript safe range; use a string")
        else:
            raise ArchitectureError("Source contains a non-JSON value")


def _schema_errors(data, schema):
    # Refuse schema evolution that this deliberately small local evaluator
    # does not implement, rather than silently accepting unchecked fields.
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "const", "enum", "properties", "required", "additionalProperties", "items", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern"}
    pending = [schema]
    while pending:
        spec = pending.pop()
        unsupported = set(spec) - supported
        if unsupported:
            raise ArchitectureError("Bundled schema uses unsupported validation keywords: " + ", ".join(sorted(unsupported)))
        pending.extend(spec.get("$defs", {}).values())
        pending.extend(spec.get("properties", {}).values())
        if "items" in spec:
            pending.append(spec["items"])
    errors = []

    def error(path, message):
        if len(errors) < MAX_ERRORS:
            errors.append(f"{path}: {message}")

    def walk(value, spec, path):
        if len(errors) >= MAX_ERRORS:
            return
        if "$ref" in spec:
            name = spec["$ref"].removeprefix("#/$defs/")
            return walk(value, schema["$defs"][name], path)
        kind = spec.get("type")
        matches = {"object": isinstance(value, dict), "array": isinstance(value, list),
                   "string": isinstance(value, str), "boolean": isinstance(value, bool),
                   "integer": isinstance(value, int) and not isinstance(value, bool),
                   "number": isinstance(value, (int, float)) and not isinstance(value, bool),
                   "null": value is None}
        if kind is not None and not matches.get(kind, False):
            error(path, f"expected {kind}")
            return
        if "const" in spec and value != spec["const"]:
            error(path, f"must equal {spec['const']!r}")
        if "enum" in spec and value not in spec["enum"]:
            error(path, "must be one of " + ", ".join(map(str, spec["enum"])))
        if isinstance(value, str):
            if len(value) < spec.get("minLength", 0):
                error(path, "must not be empty")
            if len(value) > spec.get("maxLength", float("inf")):
                error(path, "string exceeds maximum length")
            if "pattern" in spec and re.search(spec["pattern"], value) is None:
                error(path, "does not match the required format")
        if isinstance(value, dict):
            for key in spec.get("required", []):
                if key not in value:
                    error(path, f"missing required property {key!r}")
            properties = spec.get("properties", {})
            for key, item in value.items():
                if key in properties:
                    walk(item, properties[key], f"{path}.{key}")
                elif spec.get("additionalProperties") is False:
                    error(path, f"unknown property {key!r}; use extensions for custom fields")
        if isinstance(value, list):
            if len(value) < spec.get("minItems", 0):
                error(path, f"requires at least {spec['minItems']} item(s)")
            if len(value) > spec.get("maxItems", float("inf")):
                error(path, "too many items")
            if spec.get("uniqueItems"):
                seen = set()
                for item in value:
                    key = json.dumps(item, sort_keys=True, ensure_ascii=True)
                    if key in seen:
                        error(path, "duplicate array item")
                        break
                    seen.add(key)
            for index, item in enumerate(value):
                if "items" in spec:
                    walk(item, spec["items"], f"{path}[{index}]")

    walk(data, schema, "$")
    return errors


def validate_data(data):
    """Return warnings or raise ArchitectureError with actionable locations."""
    _check_data_limits(data)
    schema = load_json(SCHEMA_PATH.read_bytes())
    errors = _schema_errors(data, schema)
    if errors:
        raise ArchitectureError("Schema validation failed:\n  " + "\n  ".join(errors))
    warnings = []
    tables = {}
    global_ids = {}

    def error(path, message):
        if len(errors) < MAX_ERRORS:
            errors.append(f"{path}: {message}")

    def reference(value, table, path):
        if value not in tables[table]:
            error(path, f"unknown {table} reference {value!r}")

    def check_evidence(item, location):
        if item.get("status") == "current" and not item.get("evidence"):
            error(location, "current claims require evidence; use unknown when evidence is missing")
        if item.get("progress", "unknown") != "unknown" and not item.get("progressEvidence"):
            error(location, "declared progress requires progressEvidence; omit progress or use unknown when its source is missing")
        # Progress is a sourced declaration, not acceptance or verification.
        # It never changes design status and never inherits from a parent flow.
        for evidence_key in ("evidence", "progressEvidence"):
            for eindex, evidence in enumerate(item.get(evidence_key, [])):
                path = evidence["path"]
                parts = PurePosixPath(path).parts
                if (not path.strip() or path in (".", "..") or "\\" in path or path.startswith("/")
                        or any(part == ".." for part in parts) or ":" in path
                        or any(ord(char) < 32 for char in path)):
                    error(f"{location}.{evidence_key}[{eindex}].path", "must be a repository-relative POSIX path without traversal, control characters, or URL schemes")
                if "lines" in evidence and "-" in evidence["lines"]:
                    start, end = map(int, evidence["lines"].split("-"))
                    if end < start:
                        error(f"{location}.{evidence_key}[{eindex}].lines", "range must be ascending")

    def check_flow_evidence(item, flow, location):
        # Match viewer inheritance without mutating the authoritative source.
        effective = dict(item)
        effective["status"] = item.get("status", flow["status"])
        effective["evidence"] = item.get("evidence", flow.get("evidence", []) if "status" not in item else [])
        check_evidence(effective, location)

    for collection in ("elements", "relationships", "contracts", "flows", "views", "changes"):
        tables[collection] = {}
        for index, item in enumerate(data.get(collection, [])):
            location = f"$.{collection}[{index}]"
            identifier = item["id"]
            if identifier in global_ids:
                error(location, f"duplicate global id {identifier!r}, first used at {global_ids[identifier]}")
            else:
                global_ids[identifier] = location
            tables[collection][identifier] = item
            if item.get("verification") in ("implemented", "verified") and not item.get("evidence"):
                error(location, "implemented/verified claims require evidence")
            if item.get("decision") == "rejected" and item.get("verification") == "verified":
                error(location, "rejected change cannot be verified")
            check_evidence(item, location)

    for identifier, item in tables["elements"].items():
        if "parentId" in item:
            reference(item["parentId"], "elements", identifier + ".parentId")
        for value in item.get("contractIds", []):
            reference(value, "contracts", identifier + ".contractIds")
        if "drilldownViewId" in item:
            reference(item["drilldownViewId"], "views", identifier + ".drilldownViewId")
            target = tables["views"].get(item["drilldownViewId"])
            if target and (target["kind"] != "module" or target.get("focusElementId") != identifier):
                error(identifier + ".drilldownViewId", "must point to a module view whose focusElementId is this element")
        visited = set()
        current = identifier
        while current in tables["elements"]:
            if current in visited:
                error(identifier, "parentId hierarchy contains a cycle")
                break
            visited.add(current)
            current = tables["elements"][current].get("parentId")

    for identifier, item in tables["relationships"].items():
        reference(item["from"], "elements", identifier + ".from")
        reference(item["to"], "elements", identifier + ".to")
        for value in item.get("contractIds", []):
            reference(value, "contracts", identifier + ".contractIds")

    for identifier, contract in tables["contracts"].items():
        for field in ("inputs", "outputs"):
            names = [item["name"] for item in contract[field]]
            if len(set(names)) != len(names):
                error(identifier + "." + field, "field names must be unique")
        codes = [item["code"] for item in contract.get("errors", [])]
        if len(set(codes)) != len(codes):
            error(identifier + ".errors", "error codes must be unique")

    for identifier, flow in tables["flows"].items():
        steps = set()
        for step in flow["steps"]:
            check_flow_evidence(step, flow, identifier + "." + step["id"])
            if step["id"] in steps:
                error(identifier + ".steps", f"duplicate scoped step id {step['id']!r}")
            steps.add(step["id"])
            reference(step["elementId"], "elements", identifier + "." + step["id"])
            for value in step.get("contractIds", []):
                reference(value, "contracts", identifier + "." + step["id"] + ".contractIds")
        used = set()
        for index, transition in enumerate(flow["transitions"]):
            check_flow_evidence(transition, flow, f"{identifier}.transitions[{index}]")
            for endpoint in ("from", "to"):
                value = transition[endpoint]
                if value not in steps:
                    error(identifier + ".transitions", f"unknown step {value!r}")
                used.add(value)
        if len(steps) > 1 and steps - used:
            warnings.append(f"{identifier}: disconnected flow steps: {', '.join(sorted(steps - used))}")
        if not any(s.get("outcome") in ("failure", "recovery") for s in flow["steps"]) and not any(t.get("outcome") in ("failure", "recovery") for t in flow["transitions"]):
            warnings.append(f"{identifier}: no failure or recovery path modeled; confirm whether applicable")

    def is_descendant(identifier, ancestor):
        visited = set()
        current = tables["elements"].get(identifier, {}).get("parentId")
        while current in tables["elements"] and current not in visited:
            if current == ancestor:
                return True
            visited.add(current)
            current = tables["elements"][current].get("parentId")
        return False

    focused_views = {}
    for identifier, view in tables["views"].items():
        focus = view.get("focusElementId")
        context = set(view.get("contextElementIds", []))
        if focus is not None:
            if view["kind"] != "module":
                error(identifier, "focusElementId is only valid on module views")
            reference(focus, "elements", identifier + ".focusElementId")
            if focus in focused_views:
                error(identifier, f"duplicate focused module view for {focus!r}")
            focused_views[focus] = identifier
            owner = tables["elements"].get(focus)
            if owner and owner.get("drilldownViewId") != identifier:
                error(identifier, "focus element must link back through drilldownViewId")
            internal = set(view.get("elementIds", [])) - context
            if not internal:
                error(identifier, "focused module view requires at least one internal descendant")
            for element_id in internal:
                if element_id in tables["elements"] and not is_descendant(element_id, focus):
                    error(identifier, f"internal element {element_id!r} is not a strict descendant of focusElementId")
        if "contextElementIds" in view:
            if view["kind"] != "module" or focus is None:
                error(identifier, "contextElementIds requires a focused module view")
            if not context.issubset(set(view.get("elementIds", []))):
                error(identifier, "contextElementIds must be a subset of elementIds")
            for element_id in context:
                reference(element_id, "elements", identifier + ".contextElementIds")
                if focus is not None and is_descendant(element_id, focus):
                    error(identifier, f"context element {element_id!r} belongs to the focus subtree; list it as internal")
        if view["kind"] == "flow":
            if "flowId" not in view:
                error(identifier, "flow view requires flowId")
            else:
                reference(view["flowId"], "flows", identifier + ".flowId")
            if "elementIds" in view or "relationshipIds" in view:
                error(identifier, "flow view derives its scope from flowId; omit elementIds/relationshipIds")
        else:
            if "flowId" in view:
                error(identifier, "overview/module view must not declare flowId")
            for key, target in (("elementIds", "elements"), ("relationshipIds", "relationships")):
                if key not in view:
                    error(identifier, f"{view['kind']} view requires {key}")
                for value in view.get(key, []):
                    reference(value, target, identifier + "." + key)
            scope = set(view.get("elementIds", []))
            for rel_id in view.get("relationshipIds", []):
                rel = tables["relationships"].get(rel_id)
                if rel and (rel["from"] not in scope or rel["to"] not in scope):
                    error(identifier, f"relationship {rel_id!r} has endpoints outside this view's elementIds")
    # Check the actual navigation graph as well as the ownership hierarchy.
    # Context nodes intentionally have no drilldown edge in this graph.
    adjacency = {identifier: set() for identifier in tables["views"]}
    incoming = {identifier: 0 for identifier in tables["views"]}
    for identifier, view in tables["views"].items():
        for element_id in set(view.get("elementIds", [])) - set(view.get("contextElementIds", [])):
            target = tables["elements"].get(element_id, {}).get("drilldownViewId")
            if target in adjacency and target not in adjacency[identifier]:
                adjacency[identifier].add(target)
                incoming[target] += 1
    ready = [identifier for identifier, count in incoming.items() if count == 0]
    visited_count = 0
    while ready:
        identifier = ready.pop()
        visited_count += 1
        for target in adjacency[identifier]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    if visited_count != len(adjacency):
        error("$.views", "drilldown navigation contains a cycle")

    if not any(view["kind"] == "overview" for view in data["views"]):
        error("$.views", "at least one overview view is required")

    for identifier, change in tables["changes"].items():
        for key, target in (("elementIds", "elements"), ("contractIds", "contracts"), ("flowIds", "flows")):
            for value in change.get(key, []):
                reference(value, target, identifier + "." + key)
        if not change.get("acceptance"):
            warnings.append(f"{identifier}: change has no acceptance criteria")
    if errors:
        raise ArchitectureError("Semantic validation failed:\n  " + "\n  ".join(errors))
    return warnings


def safe_json(data):
    """JSON in an inert script element, safe even for hostile text and tags."""
    _check_data_limits(data)
    return (json.dumps(data, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def render_document(data, raw: bytes, source_name: str, warnings):
    paths = {"template": ROOT / "assets" / "viewer.html", "css": ROOT / "assets" / "viewer.css", "js": ROOT / "assets" / "viewer.js"}
    contents = {key: path.read_bytes() for key, path in paths.items()}
    assets = {key: value.decode("utf-8") for key, value in contents.items()}
    if re.search(r"</script\s*", assets["js"], flags=re.I) or re.search(r"</style\s*", assets["css"], flags=re.I):
        raise ArchitectureError("Bundled JS/CSS contains an unsafe closing HTML tag")
    asset_hash = hashlib.sha256()
    for key in sorted(contents):
        asset_hash.update(key.encode("ascii") + b"\0" + contents[key] + b"\0")
    metadata = {"sourceName": source_name, "sourceSha256": hashlib.sha256(raw).hexdigest(),
                "assetsSha256": asset_hash.hexdigest(), "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "rendererVersion": VERSION, "warnings": warnings}
    replacements = {"@@ARCHITECTURE_DATA@@": safe_json(data), "@@RENDER_METADATA@@": safe_json(metadata),
                    "@@VIEWER_CSS@@": assets["css"], "@@VIEWER_JS@@": assets["js"]}
    for marker in replacements:
        if assets["template"].count(marker) != 1:
            raise ArchitectureError(f"Bundled viewer template must contain {marker} exactly once")
    # A single substitution pass prevents source text that resembles a marker
    # from being replaced or executed as a second template operation.
    pattern = "|".join(re.escape(marker) for marker in replacements)
    return re.sub(pattern, lambda match: replacements[match.group(0)], assets["template"])


def _can_pin_output_directory():
    return os.name == "posix" and os.open in os.supports_dir_fd and all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW"))


def _open_output_directory(parent):
    """Pin every ancestor without following symlinks; caller closes result."""
    if not _can_pin_output_directory():
        raise ArchitectureError("Directory descriptors unavailable on this platform")
    if ".." in parent.parts:
        raise ArchitectureError("Output directory must not contain '..'; provide an explicit normalized path")
    absolute = Path(os.path.abspath(parent))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="authoritative UTF-8 architecture JSON")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="explicit NEW .html or .htm file; never overwritten")
    mode.add_argument("--validate-only", action="store_true", help="validate without writing any files")
    args = parser.parse_args(argv)
    try:
        with args.source.open("rb") as source:
            raw = source.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise ArchitectureError(f"Source exceeds {MAX_SOURCE_BYTES} bytes")
        data = load_json(raw)
        warnings = validate_data(data)
        for warning in warnings:
            print("WARNING: " + warning, file=sys.stderr)
        if args.validate_only:
            print(f"Valid architecture {data['revision']}: {len(data['elements'])} elements, {len(data['views'])} views; {len(warnings)} warning(s)")
            return 0
        output = args.output
        if output.suffix.lower() not in (".html", ".htm"):
            raise ArchitectureError("Output must have a .html or .htm suffix")
        if output.resolve() == args.source.resolve():
            raise ArchitectureError("Output must not be the source file")
        if output.exists() or output.is_symlink():
            raise ArchitectureError(f"Refusing to overwrite existing output: {output}")
        if not output.parent.is_dir():
            raise ArchitectureError("Output parent directory must already exist")
        document = render_document(data, raw, args.source.name, warnings).encode("utf-8")
        # O_EXCL atomically refuses existing files/final symlinks. POSIX can
        # additionally pin every ancestor against parent-path redirection.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        if _can_pin_output_directory():
            parent_fd = _open_output_directory(output.parent)
            try:
                fd = os.open(output.name, flags | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
            finally:
                os.close(parent_fd)
        else:
            # Native Windows support: no overwrite and no cleanup deletion,
            # but this is not a hostile-directory race containment sandbox.
            print("WARNING: directory pinning is unavailable; use a stable output directory controlled by you", file=sys.stderr)
            fd = os.open(output, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(document)
        except BaseException:
            # Never unlink by path: a concurrent actor may have replaced it.
            print(f"WARNING: output may be incomplete at {output}; retained for inspection", file=sys.stderr)
            raise
        print(f"Rendered {output} ({len(document)} bytes); source SHA-256 {hashlib.sha256(raw).hexdigest()}")
        return 0
    except (ArchitectureError, OSError, UnicodeError, RecursionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
