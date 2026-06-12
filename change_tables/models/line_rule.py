"""Whole-line replacement rule."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineRule:
    """Replace an entire line when it contains the find anchor text."""

    find: str
    replace: str
    kind: str = "line"
