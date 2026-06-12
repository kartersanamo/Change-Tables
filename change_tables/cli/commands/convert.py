"""Convert command handler."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from change_tables.cli.output import print_error, print_message
from change_tables.models.rule_set import RuleSet
from change_tables.services.conversion_service import ConversionService
from change_tables.services.rules_session import RulesSession


def run_convert(args: Namespace, session: RulesSession | None = None) -> int:
    """Convert an input file using the configured rules."""
    input_path = Path(args.input)
    if not input_path.is_file():
        print_error(f"Input file not found: {input_path}")
        return 2

    output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_modified{input_path.suffix}")

    try:
        if session is not None:
            rule_set = session.get_rule_set()
            session.validate()
        else:
            rules_path = Path(args.rules)
            if args.rules_data:
                rule_set = _load_rules_from_data(args.rules_data)
            else:
                working_session = RulesSession(rules_path)
                working_session.load()
                rule_set = working_session.get_rule_set()

        source_text = input_path.read_text(encoding="utf-8")
        result = ConversionService().convert(source_text, rule_set)
        output_path.write_text(result, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print_error(str(exc))
        return 1

    print_message(f"Saved {output_path.name}", quiet=args.quiet)
    return 0


def _load_rules_from_data(rules_data: str) -> RuleSet:
    if rules_data == "-":
        import sys

        payload = json.load(sys.stdin)
    elif rules_data.startswith("@"):
        payload = json.loads(Path(rules_data[1:]).read_text(encoding="utf-8"))
    else:
        payload = json.loads(rules_data)
    rule_set = RuleSet.from_dict(payload)
    rule_set.validate()
    return rule_set
