"""Subprocess tests for the CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from change_tables.config import DEFAULT_RULES_PATH, PROJECT_ROOT


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main_py = PROJECT_ROOT / "main.py"
        self.python = sys.executable

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.python, str(self.main_py), *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

    def test_convert_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.txt"
            output_path = temp_path / "output.txt"
            rules_path = temp_path / "rules.json"
            rules_path.write_text(DEFAULT_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            input_path.write_text("OR_WORD_30 test\n", encoding="utf-8")

            result = self._run(
                "convert",
                "-i",
                str(input_path),
                "-o",
                str(output_path),
                "--rules",
                str(rules_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.is_file())
            self.assertIn("OR_WORD 1", output_path.read_text(encoding="utf-8"))

    def test_convert_missing_input_exits_nonzero(self) -> None:
        result = self._run("convert", "-i", "missing.txt", "-o", "out.txt", "--rules", str(DEFAULT_RULES_PATH))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr.lower())

    def test_rules_show_json(self) -> None:
        result = self._run("rules", "show", "--rules", str(DEFAULT_RULES_PATH), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("lines", payload)
        self.assertIn("global", payload)
        self.assertIn("word_30_fallback", payload)

    def test_rules_global_add_and_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = Path(temp_dir) / "rules.json"
            rules_path.write_text(DEFAULT_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            add_result = self._run(
                "rules",
                "global",
                "add",
                "--old",
                "TEST_TOKEN",
                "--new",
                "REPLACED",
                "--rules",
                str(rules_path),
            )
            self.assertEqual(add_result.returncode, 0, add_result.stderr)

            settings_result = self._run(
                "rules",
                "settings",
                "word30",
                "off",
                "--rules",
                str(rules_path),
            )
            self.assertEqual(settings_result.returncode, 0, settings_result.stderr)

            payload = json.loads(rules_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["word_30_fallback"])
            self.assertEqual(payload["global"][-1]["old"], "TEST_TOKEN")

    def test_rules_line_move(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = Path(temp_dir) / "rules.json"
            rules_path.write_text(DEFAULT_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            before = json.loads(rules_path.read_text(encoding="utf-8"))
            first = before["lines"][0]

            result = self._run(
                "rules",
                "line",
                "move",
                "--index",
                "1",
                "--direction",
                "down",
                "--rules",
                str(rules_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            after = json.loads(rules_path.read_text(encoding="utf-8"))
            self.assertEqual(after["lines"][1], first)

    def test_rules_reload_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = Path(temp_dir) / "rules.json"
            rules_path.write_text(DEFAULT_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            work_path = rules_path.parent / f"{rules_path.stem}.work{rules_path.suffix}"

            dirty_result = self._run(
                "rules",
                "global",
                "add",
                "--old",
                "TEMP",
                "--new",
                "X",
                "--no-save",
                "--rules",
                str(rules_path),
            )
            self.assertEqual(dirty_result.returncode, 0, dirty_result.stderr)
            self.assertTrue(work_path.is_file())

            reload_result = self._run("rules", "reload", "--force", "--rules", str(rules_path))
            self.assertEqual(reload_result.returncode, 0, reload_result.stderr)
            self.assertFalse(work_path.is_file())


if __name__ == "__main__":
    unittest.main()
