"""Tests for the Change Tables rule engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine import GlobalRule, LineRule, apply_rules, parse_change_table, rule_summary
from rules import DEFAULT_RULES_PATH, convert, load_rules, read_rules_data, save_rules_data, validate_rules_data


ROOT = Path(__file__).resolve().parent


class JsonRulesTests(unittest.TestCase):
    def test_load_rules_json(self) -> None:
        rules = load_rules(DEFAULT_RULES_PATH)
        self.assertGreater(len(rules), 0)
        line_count, global_count = rule_summary(rules)
        self.assertEqual(line_count, 5)
        self.assertEqual(global_count, 5)

    def test_save_and_validate(self) -> None:
        data = read_rules_data(DEFAULT_RULES_PATH)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            path = Path(handle.name)
        try:
            save_rules_data(path, data)
            loaded = read_rules_data(path)
            validate_rules_data(loaded)
        finally:
            path.unlink()


class ParseChangeTableTests(unittest.TestCase):
    def test_global_rules_with_multiple_separators(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write('"foo" = "bar"\n')
            handle.write("hello => world\n")
            handle.write("a -> b\n")
            path = Path(handle.name)

        try:
            rules = parse_change_table(path)
            self.assertEqual(len(rules), 3)
            self.assertIsInstance(rules[0], GlobalRule)
            self.assertEqual(rules[0].old, "foo")
            self.assertEqual(rules[2].new, "b")
        finally:
            path.unlink()


class ApplyRulesTests(unittest.TestCase):
    def test_line_rules_run_before_global_rules(self) -> None:
        rules = [
            LineRule(find="ALPHA_30", replace="ALPHA 1"),
            GlobalRule(old="ALPHA_30", new="ALPHA 9"),
        ]
        text = "line with ALPHA_30 value\n"
        self.assertEqual(apply_rules(text, rules), "ALPHA 1\n")


class ModfltExampleTests(unittest.TestCase):
    def test_modflt_old_to_new(self) -> None:
        old_path = ROOT / "Modflt_old.txt"
        expected_path = ROOT / "Modflt_New.txt"
        if not expected_path.is_file():
            expected_path = ROOT / "Modflt_old_modified.txt"
        if not old_path.is_file() or not expected_path.is_file():
            self.skipTest("ModFLT example files not available")

        data = read_rules_data(DEFAULT_RULES_PATH)
        result = convert(old_path.read_text(encoding="utf-8"), data=data)
        expected = expected_path.read_text(encoding="utf-8")
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
