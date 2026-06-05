"""Change table parsing and rule application."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


GLOBAL_LINE_PATTERN = re.compile(
    r"""^\s*
    (?:
        (?P<q1>["'])(?P<old_quoted>.*?)(?P=q1)
        |
        (?P<old_plain>[^=]+?)
    )
    \s*(?:=>|->|=)\s*
    (?:
        (?P<q2>["'])(?P<new_quoted>.*?)(?P=q2)
        |
        (?P<new_plain>.+?)
    )
    \s*$
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class LineRule:
    kind: Literal["line"] = "line"
    find: str = ""
    replace: str = ""


@dataclass(frozen=True)
class GlobalRule:
    kind: Literal["global"] = "global"
    old: str = ""
    new: str = ""


Rule = LineRule | GlobalRule


def _split_trailing_whitespace(text: str) -> tuple[str, str]:
    index = len(text)
    while index > 0 and text[index - 1] in " \t":
        index -= 1
    return text[:index], text[index:]


def _parse_global_line(raw_line: str, line_no: int) -> GlobalRule | None:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = GLOBAL_LINE_PATTERN.match(raw_line.rstrip("\n\r"))
    if not match:
        raise ValueError(f"Line {line_no}: could not parse rule: {raw_line!r}")

    old = match.group("old_quoted") if match.group("old_quoted") is not None else match.group("old_plain")
    new = match.group("new_quoted") if match.group("new_quoted") is not None else match.group("new_plain")
    return GlobalRule(old=old.strip(), new=new.strip())


def _parse_labeled_value(line: str) -> tuple[str, str, bool] | None:
    for prefix in ("find:", "replace:"):
        if line.lower().startswith(prefix):
            preserve_trailing = prefix == "replace:"
            value = line[len(prefix) :].lstrip()
            if not preserve_trailing:
                value = value.rstrip()
            return prefix[:-1], value, preserve_trailing
    return None


def parse_change_table(path: Path) -> list[Rule]:
    """Parse a change table file into ordered line and global rules."""
    rules: list[Rule] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    index = 0
    while index < len(lines):
        line_no = index + 1
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#"):
            index += 1
            continue

        if stripped.lower() == "[line]":
            index += 1
            find_text: str | None = None
            replace_text: str | None = None

            while index < len(lines):
                inner = lines[index].strip()
                if not inner or inner.startswith("#"):
                    index += 1
                    continue
                if inner.lower() == "[line]":
                    break

                labeled = _parse_labeled_value(inner)
                if labeled is None:
                    break

                key, value, _preserve = labeled
                if key == "find":
                    find_text = value
                else:
                    replace_text = value
                index += 1

            if not find_text or replace_text is None:
                raise ValueError(f"Line {line_no}: [line] block requires both find: and replace:")
            rules.append(LineRule(find=find_text, replace=replace_text))
            continue

        global_rule = _parse_global_line(raw_line, line_no)
        if global_rule is not None:
            rules.append(global_rule)
        index += 1

    if not rules:
        raise ValueError("Change table has no rules.")

    return rules


def apply_rules(text: str, rules: list[Rule]) -> str:
    """Apply line rules per input line, then global rules on the full text."""
    line_rules = [rule for rule in rules if isinstance(rule, LineRule)]
    global_rules = [rule for rule in rules if isinstance(rule, GlobalRule)]

    if text:
        source_lines = text.splitlines(keepends=True)
        if not source_lines and text:
            source_lines = [text]
    else:
        source_lines = []

    output_lines: list[str] = []
    for line in source_lines:
        line_body = line.rstrip("\n\r")
        line_ending = line[len(line_body) :]
        _, trailing_ws = _split_trailing_whitespace(line_body)
        for rule in line_rules:
            if rule.find in line_body:
                replacement, replace_trailing = _split_trailing_whitespace(rule.replace)
                line_body = replacement + (replace_trailing or trailing_ws)
                break
        output_lines.append(line_body + line_ending)

    result = "".join(output_lines)
    for rule in global_rules:
        result = result.replace(rule.old, rule.new)

    return result


def rule_summary(rules: list[Rule]) -> tuple[int, int]:
    line_count = sum(1 for rule in rules if isinstance(rule, LineRule))
    global_count = sum(1 for rule in rules if isinstance(rule, GlobalRule))
    return line_count, global_count
