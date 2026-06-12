"""Fallback transformer for leftover *_WORD_30 instruction tokens."""

from __future__ import annotations

import re


class Word30Fallback:
    """Convert unmatched *_WORD_30 tokens using the standard operand pattern."""

    _PATTERN = re.compile(r"\b([A-Z][A-Z0-9_]*_WORD)_30\b")

    def apply(self, text: str) -> str:
        """Return text with remaining *_WORD_30 tokens normalized."""
        return self._PATTERN.sub(self._replace_match, text)

    @staticmethod
    def _replace_match(match: re.Match[str]) -> str:
        instruction = match.group(1)
        if instruction == "MASK_COMP_WORD":
            return "MASK_COMP_WORD"
        return f"{instruction} 1"
