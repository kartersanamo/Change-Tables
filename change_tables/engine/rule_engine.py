"""Core rule application engine."""

from __future__ import annotations

from change_tables.models.rule_set import RuleSet


class RuleEngine:
    """Apply line rules per input line, then global rules on the full text."""

    def apply(self, text: str, rule_set: RuleSet) -> str:
        """Return text after applying all rules in the given rule set."""
        source_lines = self._split_lines(text)
        output_lines: list[str] = []

        for line in source_lines:
            line_body = line.rstrip("\n\r")
            line_ending = line[len(line_body) :]
            _, trailing_ws = self._split_trailing_whitespace(line_body)

            for rule in rule_set.lines:
                if rule.find in line_body:
                    replacement, replace_trailing = self._split_trailing_whitespace(rule.replace)
                    line_body = replacement + (replace_trailing or trailing_ws)
                    break

            output_lines.append(line_body + line_ending)

        result = "".join(output_lines)
        for rule in rule_set.global_rules:
            result = result.replace(rule.old, rule.new)
        return result

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        if not text:
            return []
        lines = text.splitlines(keepends=True)
        if not lines and text:
            return [text]
        return lines

    @staticmethod
    def _split_trailing_whitespace(text: str) -> tuple[str, str]:
        index = len(text)
        while index > 0 and text[index - 1] in " \t":
            index -= 1
        return text[:index], text[index:]
