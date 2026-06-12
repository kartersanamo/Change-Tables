"""Persistence layer for rule sets."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Protocol

from change_tables.config import DEFAULT_RULES_PATH, bundled_resource
from change_tables.models.rule_set import RuleSet


def ensure_default_rules() -> None:
    """Copy bundled rules.json beside the app when missing."""
    if DEFAULT_RULES_PATH.is_file():
        return

    source = bundled_resource("rules.json")
    if not source.is_file():
        return

    DEFAULT_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEFAULT_RULES_PATH)


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
