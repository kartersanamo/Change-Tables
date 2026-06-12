"""Tests for Word30Fallback."""

from __future__ import annotations

import unittest

from change_tables.engine.word30_fallback import Word30Fallback


class Word30FallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fallback = Word30Fallback()

    def test_converts_word_30_to_operand_one(self) -> None:
        result = self.fallback.apply("OR_WORD_30 DEV")
        self.assertEqual(result, "OR_WORD 1 DEV")

    def test_mask_comp_word_has_no_extra_operand(self) -> None:
        result = self.fallback.apply("MASK_COMP_WORD_30 2")
        self.assertEqual(result, "MASK_COMP_WORD 2")


if __name__ == "__main__":
    unittest.main()
