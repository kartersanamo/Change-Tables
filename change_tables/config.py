"""Application-wide constants and runtime paths."""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


def app_dir() -> Path:
    """Return the writable directory beside the executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def bundled_resource(name: str) -> Path:
    """Return a read-only bundled resource path."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name
    return PROJECT_ROOT / name


DEFAULT_RULES_PATH = app_dir() / "rules.json"
