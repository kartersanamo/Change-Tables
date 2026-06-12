"""Tests for RuleSet model."""

from __future__ import annotations

import unittest

from change_tables.models.global_rule import GlobalRule
from change_tables.models.line_rule import LineRule
from change_tables.models.rule_set import RuleSet


class RuleSetTests(unittest.TestCase):
    def test_from_dict_and_to_dict_round_trip(self) -> None:
        original = {
            "word_30_fallback": False,
            "lines": [{"find": "OLD", "replace": "NEW"}],
            "global": [{"old": "A", "new": "B"}],
        }
        rule_set = RuleSet.from_dict(original)
        self.assertEqual(rule_set.to_dict(), original)

    def test_validate_requires_find_and_replace(self) -> None:
        rule_set = RuleSet(lines=[LineRule(find="", replace="NEW")])
        with self.assertRaises(ValueError):
            rule_set.validate()

    def test_counts(self) -> None:
        rule_set = RuleSet(
            lines=[LineRule(find="a", replace="b")],
            global_rules=[GlobalRule(old="x", new="y"), GlobalRule(old="1", new="2")],
        )
        self.assertEqual(rule_set.line_count(), 1)
        self.assertEqual(rule_set.global_count(), 2)


if __name__ == "__main__":
    unittest.main()
