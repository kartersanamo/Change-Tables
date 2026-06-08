"""Load, save, and apply conversion rules from JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from engine import GlobalRule, LineRule, Rule, apply_rules

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules.json"
_WORD_30_PATTERN = re.compile(r"\b([A-Z][A-Z0-9_]*_WORD)_30\b")

_cached_rules: list[Rule] | None = None
_cached_word_30_fallback: bool = True
_cached_path: Path | None = None
_cached_data: dict[str, Any] | None = None


def default_rules_data() -> dict[str, Any]:
    return {"word_30_fallback": True, "lines": [], "global": []}


def read_rules_data(path: Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Rules file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_rules_data(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_rules_data(data: dict[str, Any]) -> None:
    for entry in data.get("lines", []):
        if not entry.get("find", "").strip():
            raise ValueError("Each line rule needs a 'find' value.")
        if not entry.get("replace", "").strip():
            raise ValueError(f"Line rule missing 'replace' for find: {entry.get('find')!r}")
    for entry in data.get("global", []):
        if not entry.get("old", "").strip():
            raise ValueError("Each global rule needs an 'old' value.")


def rules_from_data(data: dict[str, Any]) -> tuple[list[Rule], bool]:
    validate_rules_data(data)
    rules: list[Rule] = []

    for entry in data.get("lines", []):
        rules.append(LineRule(find=entry["find"], replace=entry["replace"]))

    for entry in data.get("global", []):
        rules.append(GlobalRule(old=entry["old"], new=entry.get("new", "")))

    if not rules:
        raise ValueError("No rules defined.")

    return rules, bool(data.get("word_30_fallback", True))


def cache_rules(data: dict[str, Any], path: Path | None = None) -> list[Rule]:
    global _cached_rules, _cached_word_30_fallback, _cached_path, _cached_data
    rules, fallback = rules_from_data(data)
    _cached_rules = rules
    _cached_word_30_fallback = fallback
    _cached_path = path
    _cached_data = data
    return rules


def load_rules(path: Path = DEFAULT_RULES_PATH) -> list[Rule]:
    data = read_rules_data(path)
    return cache_rules(data, path)


def get_rules(path: Path | None = None) -> list[Rule]:
    rules_path = path or _cached_path or DEFAULT_RULES_PATH
    if _cached_rules is not None and (path is None or path == _cached_path):
        return _cached_rules
    return load_rules(rules_path)


def get_cached_data() -> dict[str, Any] | None:
    return _cached_data


def _apply_word_30_fallbacks(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        instruction = match.group(1)
        if instruction == "MASK_COMP_WORD":
            return "MASK_COMP_WORD"
        return f"{instruction} 1"

    return _WORD_30_PATTERN.sub(replace, text)


def convert(text: str, rules_path: Path | None = None, data: dict[str, Any] | None = None) -> str:
    if data is not None:
        rules, fallback = rules_from_data(data)
    else:
        rules = get_rules(rules_path)
        fallback = _cached_word_30_fallback

    result = apply_rules(text, rules)
    if fallback:
        result = _apply_word_30_fallbacks(result)
    return result
