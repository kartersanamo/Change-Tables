"""CLI output formatting helpers."""

from __future__ import annotations

import json
import sys
from typing import TextIO

from change_tables.models.rule_set import RuleSet


def line_preview(find: str, max_length: int = 40) -> str:
    """Return a short preview of a line rule find text."""
    preview = find.replace("\t", " ").strip()[:max_length] or "(empty)"
    return preview


def print_rule_set(rule_set: RuleSet, *, as_json: bool = False, stream: TextIO | None = None) -> None:
    """Print a full rule set in human-readable or JSON form."""
    out = stream or sys.stdout
    if as_json:
        out.write(json.dumps(rule_set.to_dict(), indent=2, ensure_ascii=False) + "\n")
        return

    out.write(f"word_30_fallback: {rule_set.word_30_fallback}\n\n")

    out.write("Global rules:\n")
    if not rule_set.global_rules:
        out.write("  (none)\n")
    else:
        for index, rule in enumerate(rule_set.global_rules, start=1):
            out.write(f"  {index}. {rule.old}  ->  {rule.new}\n")

    out.write("\nLine rules:\n")
    if not rule_set.lines:
        out.write("  (none)\n")
    else:
        for index, rule in enumerate(rule_set.lines, start=1):
            out.write(f"  {index}. {line_preview(rule.find)}\n")


def print_global_rules(rule_set: RuleSet, *, as_json: bool = False, stream: TextIO | None = None) -> None:
    """Print global rules only."""
    out = stream or sys.stdout
    if as_json:
        payload = [{"index": index, "old": rule.old, "new": rule.new} for index, rule in enumerate(rule_set.global_rules, start=1)]
        out.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return

    if not rule_set.global_rules:
        out.write("(none)\n")
        return
    for index, rule in enumerate(rule_set.global_rules, start=1):
        out.write(f"{index}. {rule.old}  ->  {rule.new}\n")


def print_line_rules(rule_set: RuleSet, *, as_json: bool = False, stream: TextIO | None = None) -> None:
    """Print line rule previews."""
    out = stream or sys.stdout
    if as_json:
        payload = [
            {"index": index, "find": rule.find, "replace": rule.replace}
            for index, rule in enumerate(rule_set.lines, start=1)
        ]
        out.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return

    if not rule_set.lines:
        out.write("(none)\n")
        return
    for index, rule in enumerate(rule_set.lines, start=1):
        out.write(f"{index}. {line_preview(rule.find)}\n")


def print_line_rule(rule_set: RuleSet, index: int, *, as_json: bool = False, stream: TextIO | None = None) -> None:
    """Print one line rule with full find/replace text."""
    out = stream or sys.stdout
    if index < 1 or index > len(rule_set.lines):
        raise ValueError(f"Invalid index {index}. Must be between 1 and {len(rule_set.lines)}.")
    rule = rule_set.lines[index - 1]
    if as_json:
        out.write(json.dumps({"index": index, "find": rule.find, "replace": rule.replace}, indent=2, ensure_ascii=False) + "\n")
        return

    out.write(f"Line rule {index}:\n")
    out.write("--- find ---\n")
    out.write(rule.find)
    if not rule.find.endswith("\n"):
        out.write("\n")
    out.write("--- replace ---\n")
    out.write(rule.replace)
    if not rule.replace.endswith("\n"):
        out.write("\n")


def print_word30_setting(enabled: bool, *, as_json: bool = False, stream: TextIO | None = None) -> None:
    """Print the word_30_fallback setting."""
    out = stream or sys.stdout
    if as_json:
        out.write(json.dumps({"word_30_fallback": enabled}, indent=2) + "\n")
        return
    out.write(f"word_30_fallback: {enabled}\n")


def print_message(message: str, *, quiet: bool = False, stream: TextIO | None = None) -> None:
    """Print a status message unless quiet mode is enabled."""
    if quiet:
        return
    out = stream or sys.stdout
    out.write(message + "\n")


def print_error(message: str, stream: TextIO | None = None) -> None:
    """Print an error message to stderr."""
    err = stream or sys.stderr
    err.write(message + "\n")
