"""Tests for ConversionService."""

from __future__ import annotations

import unittest
from pathlib import Path

from change_tables.config import DEFAULT_RULES_PATH, PROJECT_ROOT
from change_tables.persistence.rules_repository import JsonRulesRepository
from change_tables.services.conversion_service import ConversionService


class ConversionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ConversionService()
        self.repository = JsonRulesRepository()

    def test_modflt_old_to_new_when_examples_exist(self) -> None:
        old_path = PROJECT_ROOT / "Modflt_old.txt"
        expected_path = PROJECT_ROOT / "Modflt_New.txt"
        if not expected_path.is_file():
            expected_path = PROJECT_ROOT / "Modflt_old_modified.txt"
        if not old_path.is_file() or not expected_path.is_file():
            self.skipTest("ModFLT example files not available")

        rule_set = self.repository.load(DEFAULT_RULES_PATH)
        result = self.service.convert(old_path.read_text(encoding="utf-8"), rule_set)
        expected = expected_path.read_text(encoding="utf-8")
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
