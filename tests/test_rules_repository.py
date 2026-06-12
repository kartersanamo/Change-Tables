"""Tests for JsonRulesRepository."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from change_tables.config import DEFAULT_RULES_PATH
from change_tables.persistence.rules_repository import JsonRulesRepository


class JsonRulesRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = JsonRulesRepository()

    def test_load_default_rules_file(self) -> None:
        rule_set = self.repository.load(DEFAULT_RULES_PATH)
        self.assertEqual(rule_set.line_count(), 5)
        self.assertEqual(rule_set.global_count(), 5)

    def test_save_and_load_round_trip(self) -> None:
        rule_set = self.repository.load(DEFAULT_RULES_PATH)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            path = Path(handle.name)
        try:
            self.repository.save(path, rule_set)
            loaded = self.repository.load(path)
            self.assertEqual(loaded.to_dict(), rule_set.to_dict())
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
