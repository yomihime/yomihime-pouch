#!/usr/bin/env python3
"""Draft a UI/UX-oriented string tree for CharaPicker-style repositories.

This helper is intentionally heuristic. Use it to bootstrap an audit, then
verify each candidate against real call context before proposing rewrites.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path


VISIBLE_CALL_HINTS = {
    "setText",
    "setTitle",
    "setContent",
    "setPlaceholderText",
    "setToolTip",
    "addItem",
    "addItems",
    "InfoBar",
    "MessageBox",
    "QLabel",
    "PushButton",
    "PrimaryPushButton",
    "SubtitleLabel",
    "BodyLabel",
    "CaptionLabel",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "release",
    ".ruff_cache",
    ".pytest_cache",
}


@dataclass(frozen=True)
class Entry:
    page: str
    group: str
    key: str
    text: str
    source: str
    tags: tuple[str, ...]


def short_text(text: str, limit: int) -> str:
    normalized = " ".join(text.replace("\n", "\\n").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "..."


def flatten_json_strings(value: object, prefix: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        rows: list[tuple[str, str]] = []
        for key, child in value.items():
            rows.extend(flatten_json_strings(child, (*prefix, str(key))))
        return rows
    if isinstance(value, list):
        rows = []
        for index, child in enumerate(value):
            rows.extend(flatten_json_strings(child, (*prefix, str(index))))
        return rows
    if isinstance(value, str):
        return [(".".join(prefix), value)]
    return []


def classify_i18n_key(key: str) -> tuple[str, str]:
    parts = [part for chunk in key.split(".") for part in chunk.split("_") if part]
    page = parts[0] if parts else "misc"
    group = parts[1] if len(parts) > 1 else "general"
    return page, group


def collect_i18n(root: Path, locales: set[str] | None) -> list[Entry]:
    entries: list[Entry] = []
    i18n_dir = root / "i18n"
    for path in sorted(i18n_dir.glob("*.json")):
        locale = path.stem
        if locales is not None and locale not in locales:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key, text in flatten_json_strings(data):
            page, group = classify_i18n_key(key)
            entries.append(
                Entry(
                    page=page,
                    group=group,
                    key=f"{locale}:{key}",
                    text=text,
                    source=str(path.relative_to(root)),
                    tags=("i18n", locale),
                )
            )
    return entries


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute):
            return func.attr
        if isinstance(func, ast.Name):
            return func.id
    return ""


def module_page(path: Path) -> str:
    stem = path.stem
    parent = path.parent.name
    if parent in {"pages", "widgets", "workers"}:
        return stem
    return parent if parent else stem


class VisibleStringVisitor(ast.NodeVisitor):
    def __init__(self, root: Path, path: Path) -> None:
        self.root = root
        self.path = path
        self.stack: list[ast.AST] = []
        self.entries: list[Entry] = []

    def visit(self, node: ast.AST) -> None:  # noqa: D401 - keep visitor hook compact
        self.stack.append(node)
        super().visit(node)
        self.stack.pop()

    def visit_Constant(self, node: ast.Constant) -> None:
        if not isinstance(node.value, str):
            return
        text = node.value.strip()
        if not text or len(text) < 2:
            return
        parent_call = next((item for item in reversed(self.stack[:-1]) if isinstance(item, ast.Call)), None)
        name = call_name(parent_call) if parent_call else ""
        if name and name not in VISIBLE_CALL_HINTS and not any(hint in name for hint in VISIBLE_CALL_HINTS):
            return
        if not name and len(text) > 120:
            return
        rel = self.path.relative_to(self.root)
        page = module_page(self.path)
        group = name or "literal"
        self.entries.append(
            Entry(
                page=page,
                group=group,
                key=f"L{getattr(node, 'lineno', '?')}",
                text=text,
                source=str(rel),
                tags=("hardcoded",),
            )
        )


def collect_python(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for base in ("gui", "core", "utils"):
        folder = root / base
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*.py")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except Exception:
                continue
            visitor = VisibleStringVisitor(root, path)
            visitor.visit(tree)
            entries.extend(visitor.entries)
    return entries


def build_tree(entries: list[Entry]) -> dict[str, dict[str, list[Entry]]]:
    tree: dict[str, dict[str, list[Entry]]] = {}
    for entry in entries:
        tree.setdefault(entry.page, {}).setdefault(entry.group, []).append(entry)
    return tree


def emit_markdown(entries: list[Entry], limit: int) -> str:
    tree = build_tree(entries)
    lines = ["# Draft UI/UX String Tree", "", "```text", "CharaPicker strings"]
    for page in sorted(tree):
        lines.append(f"├─ {page}")
        groups = tree[page]
        for group in sorted(groups):
            lines.append(f"│  ├─ {group}")
            for entry in groups[group]:
                tags = "".join(f"[{tag}]" for tag in entry.tags)
                text = short_text(entry.text, limit)
                lines.append(f"│  │  ├─ {entry.key} {tags} {entry.source} text={text}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def emit_jsonl(entries: list[Entry]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            json.dumps(
                {
                    "page": entry.page,
                    "group": entry.group,
                    "key": entry.key,
                    "text": entry.text,
                    "source": entry.source,
                    "tags": list(entry.tags),
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(rows) + ("\n" if rows else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft a UI/UX string tree.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--format", choices=("markdown", "jsonl"), default="markdown")
    parser.add_argument(
        "--locale",
        action="append",
        default=[],
        help="Only include i18n files for this locale. Repeat for multiple locales.",
    )
    parser.add_argument("--text-limit", type=int, default=80)
    parser.add_argument("--max-entries", type=int, default=0, help="Limit entries for preview runs.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    locales = set(args.locale) if args.locale else None
    entries = collect_i18n(root, locales) + collect_python(root)
    if args.max_entries > 0:
        entries = entries[: args.max_entries]
    if args.format == "jsonl":
        print(emit_jsonl(entries), end="")
    else:
        print(emit_markdown(entries, args.text_limit), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
