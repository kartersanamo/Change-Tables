"""Temporary tool to compare converted output against Modflt_New.txt."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXPECTED = Path(__file__).resolve().parent / "Modflt_New.txt"


@dataclass
class CompareResult:
    match: bool
    actual_path: Path
    expected_path: Path
    actual_lines: int
    expected_lines: int
    diff_lines: list[str]

    @property
    def summary(self) -> str:
        if self.match:
            return (
                f"Match: {self.actual_path.name} is identical to {self.expected_path.name} "
                f"({self.actual_lines} lines)."
            )
        return (
            f"Mismatch: {self.actual_path.name} differs from {self.expected_path.name} "
            f"({self.actual_lines} vs {self.expected_lines} lines, "
            f"{len(self.diff_lines)} diff line(s))."
        )


def compare_files(actual: Path, expected: Path = DEFAULT_EXPECTED) -> CompareResult:
    if not actual.is_file():
        raise FileNotFoundError(f"Output file not found: {actual}")
    if not expected.is_file():
        raise FileNotFoundError(f"Expected file not found: {expected}")

    actual_text = actual.read_text(encoding="utf-8")
    expected_text = expected.read_text(encoding="utf-8")
    actual_lines = actual_text.splitlines(keepends=True)
    expected_lines = expected_text.splitlines(keepends=True)
    match = actual_text == expected_text

    diff_lines = list(
        difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile=expected.name,
            tofile=actual.name,
            lineterm="",
        )
    )

    return CompareResult(
        match=match,
        actual_path=actual,
        expected_path=expected,
        actual_lines=len(actual_lines),
        expected_lines=len(expected_lines),
        diff_lines=diff_lines,
    )


def format_report(result: CompareResult, max_diff_lines: int = 80) -> str:
    lines = [result.summary, ""]
    if result.match:
        return lines[0]

    if not result.diff_lines:
        lines.append("Files differ but no unified diff was produced.")
        return "\n".join(lines)

    lines.append("Diff (expected -> actual):")
    shown = result.diff_lines[:max_diff_lines]
    lines.extend(line.rstrip() for line in shown)
    if len(result.diff_lines) > max_diff_lines:
        remaining = len(result.diff_lines) - max_diff_lines
        lines.append(f"... {remaining} more diff line(s) not shown")
    return "\n".join(lines)


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Compare converted output with Modflt_New.txt")
    parser.add_argument(
        "actual",
        nargs="?",
        default="Modflt_old_modified.txt",
        help="Converted output file to check (default: Modflt_old_modified.txt)",
    )
    parser.add_argument(
        "--expected",
        default=str(DEFAULT_EXPECTED),
        help="Expected reference file (default: Modflt_New.txt in project folder)",
    )
    args = parser.parse_args()

    result = compare_files(Path(args.actual), Path(args.expected))
    print(format_report(result))
    sys.exit(0 if result.match else 1)


if __name__ == "__main__":
    main()
