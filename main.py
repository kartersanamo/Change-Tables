#!/usr/bin/env python3
"""Change Tables application entry point."""

from __future__ import annotations

import sys

from change_tables.cli.parser import run_cli
from change_tables.gui.app import run_app
from change_tables.persistence.rules_repository import ensure_default_rules

CLI_COMMANDS = frozenset({"convert", "rules", "shell", "-h", "--help"})


def _needs_console(argv: list[str]) -> bool:
    """Return whether argv should run in CLI mode."""
    return bool(argv) and argv[0] in CLI_COMMANDS


def _attach_console_if_needed() -> None:
    """Attach a console on Windows frozen builds for CLI output."""
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return

    import ctypes

    ctypes.windll.kernel32.AllocConsole()


def main(argv: list[str] | None = None) -> None:
    """Start the GUI by default, or run CLI subcommands when provided."""
    if argv is None:
        argv = list(sys.argv[1:])
    else:
        argv = list(argv)

    if argv and argv[0] == "--cli":
        argv.pop(0)

    ensure_default_rules()

    if _needs_console(argv):
        _attach_console_if_needed()
        sys.exit(run_cli(argv))
        return

    if not argv or argv[0] in {"gui", "--gui"}:
        run_app()
        return

    _attach_console_if_needed()
    sys.exit(run_cli(argv))


if __name__ == "__main__":
    main()
