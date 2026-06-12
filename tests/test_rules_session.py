"""Tests for RulesSession."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from change_tables.config import DEFAULT_RULES_PATH
from change_tables.models.rule_set import RuleSet
from change_tables.persistence.rules_repository import JsonRulesRepository
from change_tables.services.rules_session import RulesSession, UnsavedChangesError


class RulesSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = JsonRulesRepository()
        self.base_rule_set = self.repository.load(DEFAULT_RULES_PATH)

    def _make_session(self, rule_set: RuleSet | None = None) -> tuple[RulesSession, Path]:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            path = Path(handle.name)
        if rule_set is not None:
            self.repository.save(path, rule_set)
        session = RulesSession(path, repository=self.repository)
        return session, path

    def test_load_and_save_round_trip(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        try:
            session.load()
            self.assertFalse(session.dirty)
            session.set_word_30_fallback(False)
            session.save()
            reloaded = self.repository.load(path)
            self.assertFalse(reloaded.word_30_fallback)
        finally:
            path.unlink()

    def test_reload_requires_force_when_dirty(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        try:
            session.load()
            session.set_word_30_fallback(False)
            with self.assertRaises(UnsavedChangesError):
                session.reload()
            session.reload(force=True)
            self.assertTrue(session.get_rule_set().word_30_fallback)
        finally:
            path.unlink()

    def test_global_mutations(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        try:
            session.load()
            initial_count = session.get_rule_set().global_count()
            session.add_global("FOO", "BAR")
            session.remove_global(initial_count + 1)
            self.assertEqual(session.get_rule_set().global_count(), initial_count)
        finally:
            path.unlink()

    def test_line_mutations_and_move(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        try:
            session.load()
            first_find = session.get_rule_set().lines[0].find
            session.add_line("anchor", "replacement")
            index = session.get_rule_set().line_count()
            session.set_line(index, "updated", "replacement")
            session.move_line(index, -1)
            self.assertEqual(session.get_rule_set().lines[-2].find, "updated")
            session.remove_line(index - 1)
            self.assertEqual(session.get_rule_set().lines[0].find, first_find)
        finally:
            path.unlink()

    def test_save_work_creates_sidecar(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        work_path = path.parent / f"{path.stem}.work{path.suffix}"
        try:
            session.load()
            session.set_word_30_fallback(False)
            session.save_work()
            self.assertTrue(work_path.is_file())
            self.assertTrue(session.dirty)
            session.save()
            self.assertFalse(work_path.is_file())
            self.assertFalse(session.dirty)
        finally:
            if path.is_file():
                path.unlink()
            if work_path.is_file():
                work_path.unlink()

    def test_invalid_index_raises(self) -> None:
        session, path = self._make_session(self.base_rule_set)
        try:
            session.load()
            with self.assertRaises(ValueError):
                session.remove_line(999)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
