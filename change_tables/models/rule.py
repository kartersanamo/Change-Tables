"""Base rule protocol shared by all replacement rule types."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Rule(Protocol):
    """Common interface for rules applied during text conversion."""

    @property
    def kind(self) -> str:
        """Return the rule category identifier."""
