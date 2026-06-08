"""Load conversion rules from rules.json and apply them."""

from __future__ import annotations

import json
import re
from pathlib import Path

from engine import GlobalRule, LineRule, Rule, apply_rules

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules.json"
_WORD_30_PATTERN = re.compile(r"\b([A-Z][A-Z0-9_]*_WORD)_30\b")

_cached_rules: list[Rule] | None = None
_cached_word_30_fallback: bool = True
_cached_path: Path | None = None


def load_rules(path: Path = DEFAULT_RULES_PATH) -> list[Rule]:
    """Load rules from a JSON file."""
    global _cached_rules, _cached_word_30_fallback, _cached_path

    if not path.is_file():
        raise FileNotFoundError(f"Rules file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    rules: list[Rule] = []

    for entry in data.get("lines", []):
        find = entry.get("find", "")
        replace = entry.get("replace", "")
        if not find:
            raise ValueError("Each line rule needs a 'find' value.")
        if replace is None or replace == "":
            raise ValueError(f"Line rule missing 'replace' for find: {find!r}")
        rules.append(LineRule(find=find, replace=replace))

    for entry in data.get("global", []):
        old = entry.get("old", "")
        new = entry.get("new", "")
        if not old:
            raise ValueError("Each global rule needs an 'old' value.")
        rules.append(GlobalRule(old=old, new=new))

    if not rules:
        raise ValueError(f"No rules found in {path}")

    _cached_rules = rules
    _cached_word_30_fallback = bool(data.get("word_30_fallback", True))
    _cached_path = path
    return rules


def get_rules(path: Path | None = None) -> list[Rule]:
    """Return cached rules, loading from the default or given path if needed."""
    rules_path = path or _cached_path or DEFAULT_RULES_PATH
    if _cached_rules is not None and (path is None or path == _cached_path):
        return _cached_rules
    return load_rules(rules_path)


def _apply_word_30_fallbacks(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        instruction = match.group(1)
        if instruction == "MASK_COMP_WORD":
            return "MASK_COMP_WORD"
        return f"{instruction} 1"

    return _WORD_30_PATTERN.sub(replace, text)


def convert(text: str, rules_path: Path | None = None) -> str:
    """Apply rules from rules.json, with optional *_WORD_30 fallback."""
    rules = get_rules(rules_path)
    result = apply_rules(text, rules)
    if _cached_word_30_fallback:
        result = _apply_word_30_fallbacks(result)
    return result
