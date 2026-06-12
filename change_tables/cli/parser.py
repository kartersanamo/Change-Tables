"""Argument parser and CLI entry point."""

from __future__ import annotations

import argparse
import sys

from change_tables.cli.commands.convert import run_convert
from change_tables.cli.commands.rules import run_rules
from change_tables.cli.commands.shell import run_shell
from change_tables.cli.output import print_error
from change_tables.config import DEFAULT_RULES_PATH


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Change Tables — convert PLC export files using replacement rules.",
        epilog="Run without arguments to open the GUI.",
    )
    common = _common_parser()

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    gui_parser = subparsers.add_parser("gui", help="Open the desktop GUI")
    gui_parser.set_defaults(handler=_run_gui)

    convert_parser = subparsers.add_parser("convert", parents=[common], help="Convert an input file")
    convert_parser.add_argument("-i", "--input", required=True, help="Input text file")
    convert_parser.add_argument("-o", "--output", help="Output text file (default: INPUT_modified.ext)")
    convert_parser.add_argument(
        "--rules-data",
        help="Inline rules JSON, @file path, or - for stdin (overrides --rules file)",
    )
    convert_parser.set_defaults(handler=run_convert)

    rules_parser = subparsers.add_parser("rules", help="View or edit rules")
    rules_sub = rules_parser.add_subparsers(dest="rules_group", required=True, metavar="group")

    show_parser = rules_sub.add_parser("show", parents=[common], help="Show all rules")
    show_parser.set_defaults(handler=run_rules, rules_group="show")

    save_parser = rules_sub.add_parser("save", parents=[common], help="Save rules to disk")
    save_parser.set_defaults(handler=run_rules, rules_group="save")

    reload_parser = rules_sub.add_parser("reload", parents=[common], help="Reload rules from disk")
    reload_parser.add_argument("--force", action="store_true", help="Discard unsaved changes")
    reload_parser.set_defaults(handler=run_rules, rules_group="reload")

    settings_parser = rules_sub.add_parser("settings", help="Rule set settings")
    settings_sub = settings_parser.add_subparsers(dest="settings_action", required=True, metavar="setting")
    word30_parser = settings_sub.add_parser("word30", help="Configure word_30 fallback")
    word30_sub = word30_parser.add_subparsers(dest="settings_action", required=True, metavar="state")
    for name in ("on", "off", "show"):
        item = word30_sub.add_parser(name, parents=[common], help=f"Turn word_30 fallback {name}")
        item.set_defaults(handler=run_rules, rules_group="settings", settings_action=name)

    global_parser = rules_sub.add_parser("global", help="Manage global rules")
    global_sub = global_parser.add_subparsers(dest="global_action", required=True, metavar="action")

    global_list = global_sub.add_parser("list", parents=[common], help="List global rules")
    global_list.set_defaults(handler=run_rules, rules_group="global", global_action="list")

    global_add = global_sub.add_parser("add", parents=[common], help="Add a global rule")
    global_add.add_argument("--old", required=True, help="Text to find")
    global_add.add_argument("--new", default="", help="Replacement text")
    global_add.add_argument("--no-save", action="store_true", help="Do not save after adding")
    global_add.set_defaults(handler=run_rules, rules_group="global", global_action="add")

    global_set = global_sub.add_parser("set", parents=[common], help="Update a global rule")
    global_set.add_argument("--index", type=int, required=True, help="1-based rule index")
    global_set.add_argument("--old", required=True, help="Text to find")
    global_set.add_argument("--new", default="", help="Replacement text")
    global_set.add_argument("--no-save", action="store_true", help="Do not save after updating")
    global_set.set_defaults(handler=run_rules, rules_group="global", global_action="set")

    global_remove = global_sub.add_parser("remove", parents=[common], help="Remove a global rule")
    global_remove.add_argument("--index", type=int, required=True, help="1-based rule index")
    global_remove.add_argument("--no-save", action="store_true", help="Do not save after removing")
    global_remove.set_defaults(handler=run_rules, rules_group="global", global_action="remove")

    line_parser = rules_sub.add_parser("line", help="Manage line rules")
    line_sub = line_parser.add_subparsers(dest="line_action", required=True, metavar="action")

    line_list = line_sub.add_parser("list", parents=[common], help="List line rules")
    line_list.set_defaults(handler=run_rules, rules_group="line", line_action="list")

    line_show = line_sub.add_parser("show", parents=[common], help="Show a line rule in full")
    line_show.add_argument("--index", type=int, required=True, help="1-based rule index")
    line_show.set_defaults(handler=run_rules, rules_group="line", line_action="show")

    for name, defaults in (
        ("add", {"line_action": "add"}),
        ("set", {"line_action": "set"}),
    ):
        item = line_sub.add_parser(name, parents=[common], help=f"{name.capitalize()} a line rule")
        if name == "set":
            item.add_argument("--index", type=int, required=True, help="1-based rule index")
        item.add_argument("--find", help="Anchor text to find in a line")
        item.add_argument("--find-file", help="File containing find text")
        item.add_argument("--replace", help="Replacement line text")
        item.add_argument("--replace-file", help="File containing replacement text")
        item.add_argument("--no-save", action="store_true", help=f"Do not save after {name}")
        item.set_defaults(handler=run_rules, rules_group="line", **defaults)

    line_remove = line_sub.add_parser("remove", parents=[common], help="Remove a line rule")
    line_remove.add_argument("--index", type=int, required=True, help="1-based rule index")
    line_remove.add_argument("--no-save", action="store_true", help="Do not save after removing")
    line_remove.set_defaults(handler=run_rules, rules_group="line", line_action="remove")

    line_move = line_sub.add_parser("move", parents=[common], help="Move a line rule up or down")
    line_move.add_argument("--index", type=int, required=True, help="1-based rule index")
    line_move.add_argument("--direction", choices=["up", "down"], required=True, help="Move direction")
    line_move.add_argument("--no-save", action="store_true", help="Do not save after moving")
    line_move.set_defaults(handler=run_rules, rules_group="line", line_action="move")

    shell_parser = subparsers.add_parser("shell", parents=[common], help="Interactive rules and convert shell")
    shell_parser.set_defaults(handler=run_shell)

    return parser


def _common_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    _add_common_options(common)
    return common


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rules",
        default=str(DEFAULT_RULES_PATH),
        help=f"Rules JSON file (default: {DEFAULT_RULES_PATH})",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress status messages")


def _run_gui(_args: argparse.Namespace) -> int:
    from change_tables.gui.app import run_app

    run_app()
    return 0


def run_cli(argv: list[str] | None = None) -> int:
    """Parse argv and run the selected CLI command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return _run_gui(args)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print_error("Interrupted.")
        return 130


def main() -> None:
    """CLI main entry used by main.py."""
    sys.exit(run_cli())
