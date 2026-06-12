"""Tests for RuleEngine."""

from __future__ import annotations

import unittest

from change_tables.engine.rule_engine import RuleEngine
from change_tables.models.global_rule import GlobalRule
from change_tables.models.line_rule import LineRule
from change_tables.models.rule_set import RuleSet


class RuleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RuleEngine()

    def test_line_rules_run_before_global_rules(self) -> None:
        rule_set = RuleSet(
            lines=[LineRule(find="ALPHA_30", replace="ALPHA 1")],
            global_rules=[GlobalRule(old="ALPHA_30", new="ALPHA 9")],
        )
        result = self.engine.apply("line with ALPHA_30 value\n", rule_set)
        self.assertEqual(result, "ALPHA 1\n")

    def test_preserves_trailing_whitespace_on_replaced_lines(self) -> None:
        rule_set = RuleSet(lines=[LineRule(find="OLD", replace="NEW")])
        result = self.engine.apply("prefix OLD suffix\t\r\n", rule_set)
        self.assertEqual(result, "NEW\t\r\n")


if __name__ == "__main__":
    unittest.main()
