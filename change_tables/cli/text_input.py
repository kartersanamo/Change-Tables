"""Shared CLI text input helpers."""

from __future__ import annotations

from pathlib import Path


def read_text_arg(value: str | None, file_path: str | None, label: str) -> str:
    """Read line rule text from a literal value or file path."""
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    if value is not None:
        return value
    raise ValueError(f"Line rule requires --{label} or --{label}-file.")


def read_line_text(
    find: str | None = None,
    find_file: str | None = None,
    replace: str | None = None,
    replace_file: str | None = None,
) -> tuple[str, str]:
    """Read find and replace text for a line rule."""
    return (
        read_text_arg(find, find_file, "find"),
        read_text_arg(replace, replace_file, "replace"),
    )
