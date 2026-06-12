"""Global find-and-replace rule."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalRule:
    """Replace every occurrence of old text anywhere in the file."""

    old: str
    new: str
    kind: str = "global"
