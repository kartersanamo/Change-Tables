"""Interactive shell command handler."""

from __future__ import annotations

import json
import shlex
from argparse import Namespace
from pathlib import Path

from change_tables.cli.commands.convert import run_convert
from change_tables.cli.output import (
    print_error,
    print_global_rules,
    print_line_rule,
    print_line_rules,
    print_message,
    print_rule_set,
    print_word30_setting,
)
from change_tables.services.rules_session import RulesSession, UnsavedChangesError


HELP_TEXT = """Commands:
  show                          Show all rules
  save                          Save rules to disk
  reload [--force]              Reload rules from disk
  convert -i INPUT [-o OUTPUT]  Convert using in-memory rules
  settings word30 on|off|show   Toggle or show word_30 fallback
  global list                   List global rules
  global add --old X [--new Y]  Add a global rule
  global set --index N --old X [--new Y]
  global remove --index N       Remove a global rule
  line list                     List line rules
  line show --index N           Show full line rule text
  line add --find X --replace Y Add a line rule
  line set --index N --find X --replace Y
  line remove --index N         Remove a line rule
  line move --index N --direction up|down
  help                          Show this help
  quit | exit                   Exit the shell
"""


def run_shell(args: Namespace) -> int:
    """Start an interactive rules editing shell."""
    session = RulesSession(Path(args.rules))
    try:
        session.load()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print_error(str(exc))
        return 2

    print_message(f"Change Tables shell ({session.path})", quiet=False)
    print_message("Type 'help' for commands.", quiet=False)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print_message("", quiet=False)
            return _quit(session, args)

        if not raw:
            continue

        tokens = shlex.split(raw)
        command = tokens[0].lower()
        if command in {"quit", "exit"}:
            return _quit(session, args)

        try:
            _dispatch_shell_command(tokens, session, args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print_error(str(exc))
        except UnsavedChangesError as exc:
            print_error(str(exc))


def _quit(session: RulesSession, args: Namespace) -> int:
    if session.dirty:
        answer = input("Unsaved changes. Save before quitting? [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            try:
                session.save()
            except (OSError, ValueError) as exc:
                print_error(str(exc))
                return 1
    return 0


def _dispatch_shell_command(tokens: list[str], session: RulesSession, args: Namespace) -> None:
    command = tokens[0].lower()
    rest = tokens[1:]

    if command == "help":
        print_message(HELP_TEXT.strip(), quiet=False)
        return

    if command == "show":
        print_rule_set(session.get_rule_set(), as_json=args.json)
        return

    if command == "save":
        session.save()
        print_message("Rules saved", quiet=args.quiet)
        return

    if command == "reload":
        force = "--force" in rest
        session.reload(force=force)
        print_message("Rules reloaded", quiet=args.quiet)
        return

    if command == "convert":
        convert_args = _parse_convert_args(rest, args)
        exit_code = run_convert(convert_args, session=session)
        if exit_code != 0:
            raise ValueError("Convert failed.")
        return

    if command == "settings":
        _handle_settings(rest, session, args)
        return

    if command == "global":
        _handle_global(rest, session, args)
        return

    if command == "line":
        _handle_line(rest, session, args)
        return

    raise ValueError(f"Unknown command: {command}. Type 'help' for commands.")


def _parse_flag_value(tokens: list[str], flag: str) -> str | None:
    if flag in tokens:
        index = tokens.index(flag)
        if index + 1 >= len(tokens):
            raise ValueError(f"Missing value for {flag}")
        return tokens[index + 1]
    return None


def _parse_convert_args(tokens: list[str], parent_args: Namespace) -> Namespace:
    input_path = _parse_flag_value(tokens, "-i") or _parse_flag_value(tokens, "--input")
    output_path = _parse_flag_value(tokens, "-o") or _parse_flag_value(tokens, "--output")
    if not input_path:
        raise ValueError("convert requires -i INPUT")
    return Namespace(
        input=input_path,
        output=output_path,
        rules=parent_args.rules,
        rules_data=None,
        quiet=parent_args.quiet,
        json=parent_args.json,
    )


def _handle_settings(tokens: list[str], session: RulesSession, args: Namespace) -> None:
    if len(tokens) < 2 or tokens[0] != "word30":
        raise ValueError("Usage: settings word30 on|off|show")
    action = tokens[1].lower()
    if action == "show":
        print_word30_setting(session.get_rule_set().word_30_fallback, as_json=args.json)
        return
    if action not in {"on", "off"}:
        raise ValueError("Usage: settings word30 on|off|show")
    session.set_word_30_fallback(action == "on")
    print_message(f"word_30_fallback set to {action == 'on'}", quiet=args.quiet)


def _handle_global(tokens: list[str], session: RulesSession, args: Namespace) -> None:
    if not tokens:
        raise ValueError("Usage: global list|add|set|remove ...")
    action = tokens[0].lower()
    if action == "list":
        print_global_rules(session.get_rule_set(), as_json=args.json)
        return

    old = _parse_flag_value(tokens, "--old")
    new = _parse_flag_value(tokens, "--new") or ""
    index_text = _parse_flag_value(tokens, "--index")
    index = int(index_text) if index_text else None

    if action == "add":
        if old is None:
            raise ValueError("global add requires --old")
        session.add_global(old, new)
    elif action == "set":
        if index is None or old is None:
            raise ValueError("global set requires --index and --old")
        session.set_global(index, old, new)
    elif action == "remove":
        if index is None:
            raise ValueError("global remove requires --index")
        session.remove_global(index)
    else:
        raise ValueError(f"Unknown global action: {action}")
    print_message(f"Global rule {action} complete (not saved)", quiet=args.quiet)


def _handle_line(tokens: list[str], session: RulesSession, args: Namespace) -> None:
    if not tokens:
        raise ValueError("Usage: line list|show|add|set|remove|move ...")
    action = tokens[0].lower()
    if action == "list":
        print_line_rules(session.get_rule_set(), as_json=args.json)
        return

    index_text = _parse_flag_value(tokens, "--index")
    index = int(index_text) if index_text else None

    if action == "show":
        if index is None:
            raise ValueError("line show requires --index")
        print_line_rule(session.get_rule_set(), index, as_json=args.json)
        return

    find = _parse_flag_value(tokens, "--find")
    find_file = _parse_flag_value(tokens, "--find-file")
    replace = _parse_flag_value(tokens, "--replace")
    replace_file = _parse_flag_value(tokens, "--replace-file")
    direction = _parse_flag_value(tokens, "--direction")

    if action == "add":
        find_text, replace_text = _read_shell_line_text(find, find_file, replace, replace_file)
        session.add_line(find_text, replace_text)
    elif action == "set":
        if index is None:
            raise ValueError("line set requires --index")
        find_text, replace_text = _read_shell_line_text(find, find_file, replace, replace_file)
        session.set_line(index, find_text, replace_text)
    elif action == "remove":
        if index is None:
            raise ValueError("line remove requires --index")
        session.remove_line(index)
    elif action == "move":
        if index is None or direction not in {"up", "down"}:
            raise ValueError("line move requires --index and --direction up|down")
        session.move_line(index, -1 if direction == "up" else 1)
    else:
        raise ValueError(f"Unknown line action: {action}")
    print_message(f"Line rule {action} complete (not saved)", quiet=args.quiet)


def _read_shell_line_text(
    find: str | None,
    find_file: str | None,
    replace: str | None,
    replace_file: str | None,
) -> tuple[str, str]:
    if find_file:
        find_text = Path(find_file).read_text(encoding="utf-8")
    elif find is not None:
        find_text = find
    else:
        raise ValueError("Line rule requires --find or --find-file")

    if replace_file:
        replace_text = Path(replace_file).read_text(encoding="utf-8")
    elif replace is not None:
        replace_text = replace
    else:
        raise ValueError("Line rule requires --replace or --replace-file")
    return find_text, replace_text
