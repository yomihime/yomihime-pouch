#!/usr/bin/env python3
"""Read-only skill comparison. Never install, overwrite, download, or run a skill.

The versions command compares supplied values without reading skill files.
Directory commands support canonical frontmatter, not arbitrary YAML, and require
POSIX no-follow descriptors. No result is installation approval.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SEMVER = re.compile(r"(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\Z", re.ASCII)
UTC_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z", re.ASCII)
KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?\Z")
SOURCE_COMMIT = "a890a0b69e7f518922591cc42e39d91f9b2a99ec"
MANIFEST = Path(__file__).with_name("legacy-version-map.json")


class EvidenceError(ValueError):
    """Evidence cannot be safely or unambiguously interpreted."""


class MissingSkill(EvidenceError):
    """The selected root (not an entry read during inspection) is absent."""


def parse_version(value):
    """Only numerical MAJOR.MINOR.PATCH strings, bounded before int parsing."""
    match = SEMVER.fullmatch(value) if isinstance(value, str) else None
    return tuple(int(part) for part in match.groups()) if match else None


def is_utc_timestamp(value):
    if not isinstance(value, str) or not UTC_TIME.fullmatch(value):
        return False
    try:
        dt.datetime(int(value[0:4]), int(value[5:7]), int(value[8:10]),
                    int(value[11:13]), int(value[14:16]), int(value[17:19]))
    except ValueError:
        return False
    return True


def compare_version_values(local, candidate):
    """Compare only supplied values, independently of platform or filesystem.

    Equal values do not establish equal contents. Numerical order is never an
    upgrade recommendation. Legacy ISO values require a separate trusted map;
    this command neither loads nor validates that map.
    """
    def classify(value):
        parsed = parse_version(value)
        kind = "numerical" if parsed is not None else (
            "legacy_iso" if is_utc_timestamp(value) else "unknown")
        return {"value": value, "kind": kind, "tuple": parsed}

    installed, proposed = classify(local), classify(candidate)
    result = {"values_only": True, "advisory_only": True, "mutated": False,
              "local": installed, "candidate": proposed,
              "checks_not_performed": ["directory", "content", "source", "trust", "authorization"],
              "installation_recommendation": None, "overwrite_authorized": False,
              "content_drift": "not_checked", "relation": None}
    if "unknown" in (installed["kind"], proposed["kind"]):
        decision, reason = "unorderable", "invalid or unknown value; no version order inferred"
    elif "legacy_iso" in (installed["kind"], proposed["kind"]):
        decision, reason = "mapping_required", "legacy ISO values require explicit trusted mapping and full-directory verification; neither performed"
    elif installed["tuple"] == proposed["tuple"]:
        decision, reason = "equal_values", "equal numerical values only; content equality and drift are unknown"
        result["relation"] = "equal"
    elif installed["tuple"] < proposed["tuple"]:
        decision, reason = "candidate_value_newer", "candidate numerical value is greater; not an upgrade or overwrite recommendation"
        result["relation"] = "candidate_greater"
    else:
        decision, reason = "local_value_newer", "local numerical value is greater; not a downgrade or overwrite recommendation"
        result["relation"] = "local_greater"
    return {**result, "decision": decision, "reason": reason}


def quoted_string(value):
    if value is None:
        raise EvidenceError("metadata values must be quoted strings")
    if value.startswith('"'):
        try:
            result = json.loads(value)
        except (ValueError, TypeError) as error:
            raise EvidenceError("unsupported quoted metadata value") from error
        if isinstance(result, str):
            return result
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        inner = value[1:-1]
        if "'" not in inner.replace("''", ""):
            return inner.replace("''", "'")
    raise EvidenceError("metadata values must be quoted strings")


def frontmatter(text):
    """Read only plain top-level keys and a flat, quoted metadata mapping.

    Plain scalar / folded description fields are allowed at top level. Complex
    YAML, duplicate keys, aliases, merge keys, and noncanonical indentation are
    deliberately unsupported rather than silently interpreted as a version.
    """
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise EvidenceError("missing frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise EvidenceError("unterminated frontmatter") from error
    roots, metadata, current, in_block = {}, {}, None, False
    block_indent, leading_blank_indent = None, 0
    for line in lines[1:end]:
        indent = len(line) - len(line.lstrip(" "))
        if not line.strip():
            if in_block and block_indent is None:
                leading_blank_indent = max(leading_blank_indent, indent)
            continue
        if "\t" in line:
            raise EvidenceError("tabs in frontmatter are unsupported")
        if in_block:
            # Implicit YAML block indentation comes from the first nonempty
            # content line. Indented '#' is content, not a YAML comment.
            if indent and (block_indent is None or indent >= block_indent):
                if block_indent is None:
                    if leading_blank_indent > indent:
                        raise EvidenceError("leading blank line exceeds block indentation")
                    block_indent = indent
                continue
            if indent and not line.lstrip().startswith("#"):
                raise EvidenceError("invalid block scalar indentation")
            # A root key or an outdented comment ends the scalar. Subsequent
            # indented content cannot silently resume it.
            in_block = False
        if line.lstrip().startswith("#"):
            continue
        if line.startswith(" "):
            if current == "metadata":
                match = KEY.fullmatch(line[2:]) if line.startswith("  ") else None
                if not match or match[1] in metadata:
                    raise EvidenceError("ambiguous or duplicate metadata key")
                metadata[match[1]] = quoted_string(match[2])
            elif not in_block:
                raise EvidenceError("unsupported nested frontmatter")
            continue
        match = KEY.fullmatch(line)
        if not match or match[1] in roots:
            raise EvidenceError("ambiguous or duplicate top-level key")
        current, value = match.groups()
        if current == "version":
            raise EvidenceError("top-level version is forbidden; use metadata.version only")
        roots[current] = value
        in_block = value in ("|", ">", "|-", ">-", "|+", ">+")
        block_indent, leading_blank_indent = None, 0
        if current == "metadata" and value is not None:
            raise EvidenceError("metadata must be a plain block mapping")
        if value and value[0] in "&*!{[":
            raise EvidenceError("complex YAML frontmatter is unsupported")
    if "metadata" not in roots:
        raise EvidenceError("missing metadata mapping")
    name = roots.get("name")
    if name and name.startswith(('"', "'")):
        name = quoted_string(name)
    if not name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name, re.ASCII):
        raise EvidenceError("invalid skill name")
    return {"name": name, "version": metadata.get("version"),
            "updated_at": metadata.get("updated_at")}


def tree_digest(entries):
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def open_root(root):
    """Anchor every path component to no-follow directory descriptors."""
    if (os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
            or os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd
            or os.listdir not in os.supports_fd):
        raise EvidenceError("platform lacks descriptor-based no-follow inspection; manual review required")
    root = Path(root)
    if ".." in root.parts:
        raise EvidenceError("parent traversal is unsupported; pass an unambiguous path")
    absolute = Path(os.path.abspath(root))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            following = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = following
    except FileNotFoundError as error:
        os.close(fd)
        raise MissingSkill("skill directory absent") from error
    except BaseException:
        os.close(fd)
        raise
    return fd


def file_state(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def inspect_tree(root):
    """Hash the whole tree through no-follow descriptors, with no exclusions.

    Additions (including caches), removals, executable bits and empty directories
    count as drift. Symlinks, special files and nested repositories are refused.
    Concurrent edits detected here fail closed, but this is not a filesystem
    snapshot or lock: the entire tree must be checked again before any install.
    """
    root_fd = open_root(root)
    entries, skill_text = [], None

    def visit(directory_fd, prefix):
        nonlocal skill_text
        before = os.fstat(directory_fd)
        for name in sorted(os.listdir(directory_fd)):
            relative = prefix + name
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if name == ".git":
                raise EvidenceError("nested repository requires review")
            if stat.S_ISDIR(info.st_mode):
                child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                try:
                    if file_state(os.fstat(child_fd)) != file_state(info):
                        raise EvidenceError("directory changed during inspection")
                    entries.append({"path": relative, "type": "directory"})
                    visit(child_fd, relative + "/")
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(info.st_mode):
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                with os.fdopen(fd, "rb") as source:
                    if file_state(os.fstat(source.fileno())) != file_state(info):
                        raise EvidenceError("file changed during inspection")
                    data = source.read()
                    if file_state(os.fstat(source.fileno())) != file_state(info):
                        raise EvidenceError("file changed during inspection")
                entries.append({"path": relative, "type": "file",
                                "mode": "100755" if info.st_mode & 0o111 else "100644",
                                "sha256": hashlib.sha256(data).hexdigest()})
                if relative == "SKILL.md":
                    skill_text = data.decode("utf-8")
            else:
                raise EvidenceError("symlink or special file requires review")
            if file_state(os.stat(name, dir_fd=directory_fd, follow_symlinks=False)) != file_state(info):
                raise EvidenceError("entry changed during inspection")
        if file_state(before) != file_state(os.fstat(directory_fd)):
            raise EvidenceError("directory changed during inspection")

    try:
        try:
            visit(root_fd, "")
        except FileNotFoundError as error:
            raise EvidenceError("entry disappeared during inspection") from error
    finally:
        os.close(root_fd)
    if skill_text is None:
        raise EvidenceError("missing SKILL.md")
    entries.sort(key=lambda entry: entry["path"])
    metadata = frontmatter(skill_text)
    # Staging directory names may differ. The caller verifies the actual install
    # path/name and runtime loading rules; comparisons require matching names.
    return {**metadata, "version_tuple": parse_version(metadata["version"]),
            "updated_at_valid": is_utc_timestamp(metadata["updated_at"]),
            "tree_sha256": tree_digest(entries), "entries": entries}


def load_legacy_map():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or manifest.get("source_commit") != SOURCE_COMMIT
            or manifest.get("target_version") != "1.0.0"):
        raise EvidenceError("legacy map anchor or schema mismatch")
    for name, entry in manifest["skills"].items():
        if (not is_utc_timestamp(entry["legacy_version"])
                or tree_digest(entry["entries"]) != entry["tree_sha256"]):
            raise EvidenceError("legacy map digest or timestamp mismatch: " + name)
    return manifest


def compare(local, candidate, trusted_baseline=None, use_legacy_map=False):
    """Return an advisory decision; caller establishes all source trust first."""
    result = {"advisory_only": True, "mutated": False,
              "requires_before_install": ["verify pinned source and complete resources",
                  "obtain required authorization", "recheck full local tree and concurrent writers",
                  "verified backup, transactional replacement, readback and recovery"]}
    remote = inspect_tree(candidate)
    result["candidate"] = {key: remote[key] for key in ("name", "version", "updated_at", "tree_sha256")}

    def finish(decision, reason):
        return {**result, "decision": decision, "reason": reason}

    if remote["version_tuple"] is None or not remote["updated_at_valid"]:
        return finish("candidate_invalid", "candidate requires numerical version and real ISO UTC updated_at")
    try:
        installed = inspect_tree(local)
    except MissingSkill:
        return finish("new_install_candidate", "installation absent; validation and authorization remain")
    result["local"] = {key: installed[key] for key in ("name", "version", "updated_at", "updated_at_valid", "tree_sha256")}
    if not installed["updated_at_valid"]:
        result["warnings"] = ["local metadata.updated_at missing or invalid; never used for version ordering"]
    if installed["name"] != remote["name"]:
        return finish("identity_conflict", "skill names differ; preserve local directory")
    local_version, remote_version = installed["version_tuple"], remote["version_tuple"]
    if local_version is None:
        if not is_utc_timestamp(installed["version"]):
            return finish("unknown_version", "local metadata.version cannot be ordered; preserve local")
        if not use_legacy_map:
            return finish("legacy_mapping_required", "ISO version cannot be compared with semver; verify explicit legacy mapping")
        manifest = load_legacy_map()
        mapping = manifest["skills"].get(installed["name"])
        if not mapping or remote["version"] != manifest["target_version"]:
            return finish("legacy_mapping_required", "no mapping to this target version")
        if (installed["version"] != mapping["legacy_version"]
                or installed["tree_sha256"] != mapping["tree_sha256"]):
            return finish("legacy_local_changes_or_unknown", "entire directory does not match trusted mapped source; preserve local")
        result["legacy_source_commit"] = manifest["source_commit"]
        return finish("legacy_migration_candidate", "entire local tree matches explicitly selected source-to-1.0.0 mapping; not installed")
    if local_version == remote_version:
        if installed["tree_sha256"] == remote["tree_sha256"]:
            return finish("unchanged", "same numerical version and full directory content")
        return finish("same_version_drift", "same version but full directory differs; preserve local")
    if local_version > remote_version:
        return finish("local_newer", "numerical local version is newer; no automatic downgrade")
    if trusted_baseline is None:
        return finish("unknown_local_changes", "older version does not prove clean local content; trusted baseline required")
    baseline = inspect_tree(trusted_baseline)
    if baseline["name"] != installed["name"] or baseline["version_tuple"] != local_version:
        return finish("baseline_conflict", "baseline does not identify this local version; preserve local")
    if baseline["tree_sha256"] != installed["tree_sha256"]:
        return finish("local_changes", "full directory differs from supplied trusted baseline; preserve local")
    return finish("upgrade_candidate", "numerically newer candidate and full local directory matches trusted baseline; not installed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    values = sub.add_parser("versions", help="cross-platform value comparison only; no directory or trust checks")
    values.add_argument("--local", required=True, help="local metadata.version value, not a path")
    values.add_argument("--candidate", required=True, help="candidate metadata.version value, not a path")
    inspect = sub.add_parser("inspect", help="read and hash a complete skill directory")
    inspect.add_argument("directory", type=Path)
    check = sub.add_parser("compare", help="read-only advisory, not an installer")
    check.add_argument("--local", required=True, type=Path)
    check.add_argument("--candidate", required=True, type=Path)
    check.add_argument("--trusted-baseline", type=Path, help="caller-verified full original installation directory")
    check.add_argument("--use-legacy-map", action="store_true", help="caller has verified this helper and bundled map provenance")
    args = parser.parse_args(argv)
    if args.command == "versions":
        result = compare_version_values(args.local, args.candidate)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["decision"] == "unorderable" else 0
    try:
        result = inspect_tree(args.directory) if args.command == "inspect" else compare(
            args.local, args.candidate, args.trusted_baseline, args.use_legacy_map)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (EvidenceError, OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"advisory_only": True, "mutated": False,
                          "decision": "unknown", "reason": str(error)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
