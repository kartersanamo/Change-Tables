"""Persistence layer for rule sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from change_tables.models.rule_set import RuleSet


class RulesRepository(Protocol):
    """Interface for loading and saving rule sets."""

    def load(self, path: Path) -> RuleSet:
        """Load a rule set from disk."""

    def save(self, path: Path, rule_set: RuleSet) -> None:
        """Persist a rule set to disk."""


class JsonRulesRepository:
    """Load and save rule sets as JSON files."""

    def load(self, path: Path) -> RuleSet:
        """Read and parse a JSON rules file."""
        if not path.is_file():
            raise FileNotFoundError(f"Rules file not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        rule_set = RuleSet.from_dict(data)
        rule_set.validate()
        return rule_set

    def save(self, path: Path, rule_set: RuleSet) -> None:
        """Write a rule set to a JSON file."""
        rule_set.validate()
        path.write_text(
            json.dumps(rule_set.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
