"""In-memory rule set editing with persistence."""

from __future__ import annotations

import copy
from pathlib import Path

from change_tables.models.global_rule import GlobalRule
from change_tables.models.line_rule import LineRule
from change_tables.models.rule_set import RuleSet
from change_tables.persistence.rules_repository import JsonRulesRepository, RulesRepository


class UnsavedChangesError(Exception):
    """Raised when an operation would discard unsaved edits."""


class RulesSession:
    """Manage a rule set in memory with load, save, reload, and mutations."""

    def __init__(
        self,
        path: Path,
        repository: RulesRepository | None = None,
    ) -> None:
        self.path = path
        self.work_path = path.parent / f"{path.stem}.work{path.suffix}"
        self._repository = repository or JsonRulesRepository()
        self._rule_set = RuleSet.empty()
        self._dirty = False

    @property
    def dirty(self) -> bool:
        """Return whether the session has unsaved changes."""
        return self._dirty

    def get_rule_set(self) -> RuleSet:
        """Return a deep copy of the current rule set."""
        return copy.deepcopy(self._rule_set)

    def set_rule_set(self, rule_set: RuleSet, *, dirty: bool = False) -> None:
        """Replace the in-memory rule set."""
        self._rule_set = copy.deepcopy(rule_set)
        self._dirty = dirty

    def load(self) -> None:
        """Load rules from disk into the session."""
        if self.work_path.is_file():
            self._rule_set = self._repository.load(self.work_path)
            self._dirty = True
            return
        self._rule_set = self._repository.load(self.path)
        self._dirty = False

    def save(self) -> None:
        """Validate and persist the current rule set."""
        self._rule_set.validate()
        self._repository.save(self.path, self._rule_set)
        self._clear_work_file()
        self._dirty = False

    def save_work(self) -> None:
        """Persist unsaved edits to a sidecar work file."""
        self._rule_set.validate()
        self._repository.save(self.work_path, self._rule_set)
        self._dirty = True

    def reload(self, *, force: bool = False) -> None:
        """Reload rules from disk, optionally discarding unsaved changes."""
        if self._dirty and not force:
            raise UnsavedChangesError("Unsaved changes would be discarded. Use --force to reload.")
        self._clear_work_file()
        self._rule_set = self._repository.load(self.path)
        self._dirty = False

    def validate(self) -> None:
        """Validate the current rule set."""
        self._rule_set.validate()

    def mark_dirty(self) -> None:
        """Mark the session as having unsaved changes."""
        self._mark_dirty()

    def set_word_30_fallback(self, enabled: bool) -> None:
        """Enable or disable the word_30 fallback transform."""
        self._rule_set.word_30_fallback = enabled
        self._mark_dirty()

    def add_global(self, old: str, new: str) -> None:
        """Append a global find-and-replace rule."""
        old = old.strip()
        if not old:
            raise ValueError("Each global rule needs an 'old' value.")
        self._rule_set.global_rules.append(GlobalRule(old=old, new=new))
        self._mark_dirty()

    def remove_global(self, index: int) -> None:
        """Remove a global rule by 1-based index."""
        self._rule_set.global_rules.pop(self._to_zero_index(index, len(self._rule_set.global_rules)))
        self._mark_dirty()

    def set_global(self, index: int, old: str, new: str) -> None:
        """Replace a global rule by 1-based index."""
        zero_index = self._to_zero_index(index, len(self._rule_set.global_rules))
        old = old.strip()
        if not old:
            raise ValueError("Each global rule needs an 'old' value.")
        self._rule_set.global_rules[zero_index] = GlobalRule(old=old, new=new)
        self._mark_dirty()

    def add_line(self, find: str, replace: str) -> int:
        """Append a line rule and return its 1-based index."""
        self._rule_set.lines.append(LineRule(find=find, replace=replace))
        self._mark_dirty()
        return len(self._rule_set.lines)

    def remove_line(self, index: int) -> None:
        """Remove a line rule by 1-based index."""
        self._rule_set.lines.pop(self._to_zero_index(index, len(self._rule_set.lines)))
        self._mark_dirty()

    def set_line(self, index: int, find: str, replace: str) -> None:
        """Replace a line rule by 1-based index."""
        zero_index = self._to_zero_index(index, len(self._rule_set.lines))
        self._rule_set.lines[zero_index] = LineRule(find=find, replace=replace)
        self._mark_dirty()

    def move_line(self, index: int, direction: int) -> None:
        """Move a line rule up (-1) or down (+1) by 1-based index."""
        zero_index = self._to_zero_index(index, len(self._rule_set.lines))
        new_index = zero_index + direction
        if not 0 <= new_index < len(self._rule_set.lines):
            raise ValueError("Cannot move line rule in that direction.")
        lines = self._rule_set.lines
        lines[zero_index], lines[new_index] = lines[new_index], lines[zero_index]
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _clear_work_file(self) -> None:
        if self.work_path.is_file():
            self.work_path.unlink()

    @staticmethod
    def _to_zero_index(index: int, length: int) -> int:
        if index < 1 or index > length:
            raise ValueError(f"Invalid index {index}. Must be between 1 and {length}.")
        return index - 1
