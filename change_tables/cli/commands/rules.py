"""Rules command handler."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from change_tables.cli.text_input import read_line_text
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


def run_rules(args: Namespace) -> int:
    """Dispatch rules subcommands."""
    session = RulesSession(Path(args.rules))
    try:
        session.load()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print_error(str(exc))
        return 2

    handlers = {
        "show": _show,
        "save": _save,
        "reload": _reload,
        "settings": _settings,
        "global": _global_command,
        "line": _line_command,
    }
    group = args.rules_group
    handler = handlers.get(group)
    if handler is None:
        print_error(f"Unknown rules command group: {group}")
        return 1
    return handler(args, session)


def _maybe_save(session: RulesSession, args: Namespace) -> None:
    if getattr(args, "no_save", False):
        session.save_work()
    else:
        session.save()


def _show(args: Namespace, session: RulesSession) -> int:
    print_rule_set(session.get_rule_set(), as_json=args.json)
    return 0


def _save(args: Namespace, session: RulesSession) -> int:
    try:
        session.save()
    except (OSError, ValueError) as exc:
        print_error(str(exc))
        return 1
    print_message("Rules saved", quiet=args.quiet)
    return 0


def _reload(args: Namespace, session: RulesSession) -> int:
    try:
        session.reload(force=args.force)
    except UnsavedChangesError as exc:
        print_error(str(exc))
        return 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print_error(str(exc))
        return 2
    print_message("Rules reloaded", quiet=args.quiet)
    return 0


def _settings(args: Namespace, session: RulesSession) -> int:
    action = args.settings_action
    if action == "show":
        print_word30_setting(session.get_rule_set().word_30_fallback, as_json=args.json)
        return 0

    enabled = action == "on"
    session.set_word_30_fallback(enabled)
    try:
        _maybe_save(session, args)
    except (OSError, ValueError) as exc:
        print_error(str(exc))
        return 1
    print_message(f"word_30_fallback set to {enabled}", quiet=args.quiet)
    return 0


def _global_command(args: Namespace, session: RulesSession) -> int:
    action = args.global_action
    if action == "list":
        print_global_rules(session.get_rule_set(), as_json=args.json)
        return 0

    try:
        if action == "add":
            session.add_global(args.old, args.new or "")
        elif action == "set":
            session.set_global(args.index, args.old, args.new or "")
        elif action == "remove":
            session.remove_global(args.index)
        else:
            print_error(f"Unknown global action: {action}")
            return 1
        _maybe_save(session, args)
    except (OSError, ValueError) as exc:
        print_error(str(exc))
        return 1

    print_message(f"Global rule {action} complete", quiet=args.quiet)
    return 0


def _line_command(args: Namespace, session: RulesSession) -> int:
    action = args.line_action
    if action == "list":
        print_line_rules(session.get_rule_set(), as_json=args.json)
        return 0
    if action == "show":
        try:
            print_line_rule(session.get_rule_set(), args.index, as_json=args.json)
        except ValueError as exc:
            print_error(str(exc))
            return 1
        return 0

    try:
        if action == "add":
            find, replace = read_line_text(
                find=args.find,
                find_file=args.find_file,
                replace=args.replace,
                replace_file=args.replace_file,
            )
            session.add_line(find, replace)
        elif action == "set":
            find, replace = read_line_text(
                find=args.find,
                find_file=args.find_file,
                replace=args.replace,
                replace_file=args.replace_file,
            )
            session.set_line(args.index, find, replace)
        elif action == "remove":
            session.remove_line(args.index)
        elif action == "move":
            direction = -1 if args.direction == "up" else 1
            session.move_line(args.index, direction)
        else:
            print_error(f"Unknown line action: {action}")
            return 1
        _maybe_save(session, args)
    except (OSError, ValueError) as exc:
        print_error(str(exc))
        return 1

    print_message(f"Line rule {action} complete", quiet=args.quiet)
    return 0
