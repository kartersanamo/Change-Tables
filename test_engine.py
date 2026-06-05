"""Tests for the Change Tables rule engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine import GlobalRule, LineRule, apply_rules, parse_change_table, rule_summary


from rules import convert


ROOT = Path(__file__).resolve().parent


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

    def test_line_block(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write("[line]\n")
            handle.write("find: OLD_TOKEN\n")
            handle.write("replace: NEW_TOKEN\n")
            handle.write("X => Y\n")
            path = Path(handle.name)

        try:
            rules = parse_change_table(path)
            self.assertEqual(rule_summary(rules), (1, 1))
            self.assertIsInstance(rules[0], LineRule)
            self.assertEqual(rules[0].find, "OLD_TOKEN")
            self.assertEqual(rules[0].replace, "NEW_TOKEN")
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

    def test_preserves_trailing_whitespace_on_replaced_lines(self) -> None:
        rules = [LineRule(find="OLD", replace="NEW")]
        text = "prefix OLD suffix\t\r\n"
        self.assertEqual(apply_rules(text, rules), "NEW\t\r\n")


class ModfltExampleTests(unittest.TestCase):
    def test_modflt_old_to_new(self) -> None:
        old_text = (ROOT / "Modflt_old.txt").read_text(encoding="utf-8")
        expected = (ROOT / "Modflt_New.txt").read_text(encoding="utf-8")
        result = convert(old_text)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
