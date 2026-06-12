"""Aggregate of all conversion rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from change_tables.models.global_rule import GlobalRule
from change_tables.models.line_rule import LineRule


@dataclass
class RuleSet:
    """Typed collection of line rules, global rules, and fallback settings."""

    lines: list[LineRule] = field(default_factory=list)
    global_rules: list[GlobalRule] = field(default_factory=list)
    word_30_fallback: bool = True

    def validate(self) -> None:
        """Raise ValueError when any rule is incomplete."""
        for line_rule in self.lines:
            if not line_rule.find.strip():
                raise ValueError("Each line rule needs a 'find' value.")
            if not line_rule.replace.strip():
                raise ValueError(f"Line rule missing 'replace' for find: {line_rule.find!r}")

        for global_rule in self.global_rules:
            if not global_rule.old.strip():
                raise ValueError("Each global rule needs an 'old' value.")

        if not self.lines and not self.global_rules:
            raise ValueError("No rules defined.")

    def line_count(self) -> int:
        """Return the number of line rules."""
        return len(self.lines)

    def global_count(self) -> int:
        """Return the number of global rules."""
        return len(self.global_rules)

    @classmethod
    def empty(cls) -> RuleSet:
        """Return an empty rule set with defaults enabled."""
        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSet:
        """Build a rule set from JSON-compatible data."""
        lines = [
            LineRule(find=entry["find"], replace=entry["replace"])
            for entry in data.get("lines", [])
        ]
        global_rules = [
            GlobalRule(old=entry["old"], new=entry.get("new", ""))
            for entry in data.get("global", [])
        ]
        return cls(
            lines=lines,
            global_rules=global_rules,
            word_30_fallback=bool(data.get("word_30_fallback", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the rule set to JSON-compatible data."""
        return {
            "word_30_fallback": self.word_30_fallback,
            "lines": [{"find": rule.find, "replace": rule.replace} for rule in self.lines],
            "global": [{"old": rule.old, "new": rule.new} for rule in self.global_rules],
        }
