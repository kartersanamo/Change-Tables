"""High-level conversion orchestration."""

from __future__ import annotations

from change_tables.engine.rule_engine import RuleEngine
from change_tables.engine.word30_fallback import Word30Fallback
from change_tables.models.rule_set import RuleSet


class ConversionService:
    """Coordinate rule application and optional fallback transforms."""

    def __init__(self, engine: RuleEngine | None = None, word30: Word30Fallback | None = None) -> None:
        self._engine = engine or RuleEngine()
        self._word30 = word30 or Word30Fallback()

    def convert(self, text: str, rule_set: RuleSet) -> str:
        """Apply all configured transforms and return the converted text."""
        rule_set.validate()
        result = self._engine.apply(text, rule_set)
        if rule_set.word_30_fallback:
            result = self._word30.apply(result)
        return result
