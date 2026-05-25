#!/usr/bin/env python3
"""Compare source and candidate text for preserved string constraints."""

from __future__ import annotations

import argparse
import json
import re


PATTERNS = {
    "brace_placeholders": re.compile(r"\{[^{}\n]*\}"),
    "percent_placeholders": re.compile(r"%(?:\([^)]+\))?[#0 +\-]?(?:\d+|\*)?(?:\.\d+)?[sdrfioxXeEgGcr%]"),
    "dollar_placeholders": re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*|\$\{[^}]+\}"),
    "html_tags": re.compile(r"</?[A-Za-z][^>]*>"),
    "markdown_links": re.compile(r"\[[^\]]+\]\([^)]+\)"),
    "shortcuts": re.compile(r"\b(?:Ctrl|Alt|Shift|Meta|Cmd)\s*\+\s*[A-Za-z0-9]\b"),
    "paths": re.compile(r"(?:[A-Za-z]:\\|/)[^\s\"'<>]+"),
    "error_codes": re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b|\bE\d{3,}\b"),
}


def collect(text: str) -> dict[str, list[str]]:
    return {name: pattern.findall(text) for name, pattern in PATTERNS.items()}


def diff_constraints(before: str, after: str) -> dict[str, object]:
    before_tokens = collect(before)
    after_tokens = collect(after)
    mismatches = {}
    for name, tokens in before_tokens.items():
        if sorted(tokens) != sorted(after_tokens[name]):
            mismatches[name] = {
                "before": tokens,
                "after": after_tokens[name],
            }
    return {
        "ok": not mismatches,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether candidate text preserves constraints.")
    parser.add_argument("before")
    parser.add_argument("after")
    args = parser.parse_args()

    result = diff_constraints(args.before, args.after)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
