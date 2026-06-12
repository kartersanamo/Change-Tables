#!/usr/bin/env python3
"""Change Tables application entry point."""

from __future__ import annotations

import sys

from change_tables.cli.parser import run_cli
from change_tables.gui.app import run_app


def main(argv: list[str] | None = None) -> None:
    """Start the GUI by default, or run CLI subcommands when provided."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in {"gui", "--gui"}:
        run_app()
        return
    sys.exit(run_cli(argv))


if __name__ == "__main__":
    main()
