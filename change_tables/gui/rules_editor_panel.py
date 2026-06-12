"""Editable panel for managing line and global rules."""

from __future__ import annotations

import copy
import tkinter as tk
from typing import Callable

from change_tables.models.global_rule import GlobalRule
from change_tables.models.line_rule import LineRule
from change_tables.models.rule_set import RuleSet


class RulesEditorPanel(tk.Frame):
    """UI for editing a RuleSet in memory."""

    def __init__(self, master: tk.Misc, on_dirty: Callable[[], None], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.on_dirty = on_dirty
        self._rule_set = RuleSet.empty()
        self._selected_line_index: int | None = None
        self._loading = False
        self.word_30_var = tk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        tk.Checkbutton(
            self,
            text="Auto-convert *_WORD_30",
            variable=self.word_30_var,
            command=self._mark_dirty,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        global_frame = tk.LabelFrame(self, text="Global rules (find and replace anywhere)")
        global_frame.grid(row=1, column=0, sticky="ew", pady=5)
        global_frame.columnconfigure(1, weight=1)
        global_frame.columnconfigure(3, weight=1)

        self.global_old_var = tk.StringVar()
        self.global_new_var = tk.StringVar()
        tk.Label(global_frame, text="Find:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(global_frame, textvariable=self.global_old_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        tk.Label(global_frame, text="Replace:").grid(row=0, column=2, padx=5, pady=5)
        tk.Entry(global_frame, textvariable=self.global_new_var).grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        tk.Button(global_frame, text="Add", command=self._add_global).grid(row=0, column=4, padx=5, pady=5)

        list_row = tk.Frame(global_frame)
        list_row.grid(row=1, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
        list_row.columnconfigure(0, weight=1)

        self.global_list = tk.Listbox(list_row, height=5)
        self.global_list.grid(row=0, column=0, sticky="ew")
        self.global_list.bind("<Double-1>", lambda _event: self._edit_global())

        scroll = tk.Scrollbar(list_row, command=self.global_list.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.global_list.config(yscrollcommand=scroll.set)

        btn_row = tk.Frame(global_frame)
        btn_row.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=5)
        tk.Button(btn_row, text="Edit", command=self._edit_global).pack(side=tk.LEFT)
        tk.Button(btn_row, text="Remove", command=self._remove_global).pack(side=tk.LEFT, padx=5)

        line_frame = tk.LabelFrame(self, text="Line rules (replace whole line when find text matches)")
        line_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        line_frame.columnconfigure(1, weight=1)
        line_frame.rowconfigure(0, weight=1)

        left = tk.Frame(line_frame)
        left.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        self.line_list = tk.Listbox(left, width=30, height=10)
        self.line_list.pack()
        self.line_list.bind("<<ListboxSelect>>", self._on_line_selected)

        line_btns = tk.Frame(left)
        line_btns.pack(pady=5)
        tk.Button(line_btns, text="Add", command=self._add_line_rule).pack(side=tk.LEFT)
        tk.Button(line_btns, text="Remove", command=self._remove_line_rule).pack(side=tk.LEFT, padx=3)
        tk.Button(line_btns, text="Up", command=lambda: self._move_line_rule(-1)).pack(side=tk.LEFT, padx=3)
        tk.Button(line_btns, text="Down", command=lambda: self._move_line_rule(1)).pack(side=tk.LEFT)

        right = tk.Frame(line_frame)
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=2)

        tk.Label(right, text="Find:").grid(row=0, column=0, sticky="w")
        self.find_text = tk.Text(right, height=4, width=50)
        self.find_text.grid(row=1, column=0, sticky="nsew", pady=5)
        self.find_text.bind("<KeyRelease>", self._on_line_field_changed)

        tk.Label(right, text="Replace:").grid(row=2, column=0, sticky="w")
        self.replace_text = tk.Text(right, height=8, width=50)
        self.replace_text.grid(row=3, column=0, sticky="nsew", pady=5)
        self.replace_text.bind("<KeyRelease>", self._on_line_field_changed)

    def set_rule_set(self, rule_set: RuleSet) -> None:
        """Load a rule set into the editor."""
        self._loading = True
        self._rule_set = copy.deepcopy(rule_set)
        self.word_30_var.set(self._rule_set.word_30_fallback)
        self._refresh_global_list()
        self._refresh_line_list(select_index=0 if self._rule_set.lines else None)
        self._loading = False

    def get_rule_set(self) -> RuleSet:
        """Return a copy of the current editor state."""
        rule_set = copy.deepcopy(self._rule_set)
        rule_set.word_30_fallback = self.word_30_var.get()
        return rule_set

    def commit_edits(self) -> None:
        """Persist open text fields into the in-memory rule set."""
        self._save_current_line_rule()
        self._rule_set.word_30_fallback = self.word_30_var.get()

    def validate(self) -> None:
        """Validate the current editor state."""
        self.commit_edits()
        self._rule_set.validate()

    def _mark_dirty(self) -> None:
        if not self._loading:
            self.on_dirty()

    def _refresh_global_list(self) -> None:
        self.global_list.delete(0, tk.END)
        for rule in self._rule_set.global_rules:
            self.global_list.insert(tk.END, f"{rule.old}  ->  {rule.new}")

    def _add_global(self) -> None:
        old = self.global_old_var.get().strip()
        new = self.global_new_var.get()
        if not old:
            return
        self._rule_set.global_rules.append(GlobalRule(old=old, new=new))
        self.global_old_var.set("")
        self.global_new_var.set("")
        self._refresh_global_list()
        self._mark_dirty()

    def _edit_global(self) -> None:
        selection = self.global_list.curselection()
        if not selection:
            return
        index = selection[0]
        rule = self._rule_set.global_rules[index]
        self.global_old_var.set(rule.old)
        self.global_new_var.set(rule.new)
        del self._rule_set.global_rules[index]
        self._refresh_global_list()
        self._mark_dirty()

    def _remove_global(self) -> None:
        selection = self.global_list.curselection()
        if not selection:
            return
        del self._rule_set.global_rules[selection[0]]
        self._refresh_global_list()
        self._mark_dirty()

    def _refresh_line_list(self, select_index: int | None = None) -> None:
        self.line_list.delete(0, tk.END)
        for index, rule in enumerate(self._rule_set.lines):
            preview = rule.find.replace("\t", " ").strip()[:40] or "(empty)"
            self.line_list.insert(tk.END, f"{index + 1}. {preview}")

        if select_index is not None and self._rule_set.lines:
            index = max(0, min(select_index, len(self._rule_set.lines) - 1))
            self.line_list.selection_clear(0, tk.END)
            self.line_list.selection_set(index)
            self._load_line_rule(index)
        else:
            self._selected_line_index = None
            self._set_line_fields("", "")

    def _set_line_fields(self, find: str, replace: str) -> None:
        self._loading = True
        self.find_text.delete("1.0", tk.END)
        self.find_text.insert("1.0", find)
        self.replace_text.delete("1.0", tk.END)
        self.replace_text.insert("1.0", replace)
        self._loading = False

    def _load_line_rule(self, index: int) -> None:
        if 0 <= index < len(self._rule_set.lines):
            self._selected_line_index = index
            rule = self._rule_set.lines[index]
            self._set_line_fields(rule.find, rule.replace)

    def _on_line_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.line_list.curselection()
        if selection:
            self._save_current_line_rule()
            self._load_line_rule(selection[0])

    def _save_current_line_rule(self) -> None:
        if self._selected_line_index is None:
            return
        if self._selected_line_index < len(self._rule_set.lines):
            self._rule_set.lines[self._selected_line_index] = LineRule(
                find=self.find_text.get("1.0", "end-1c"),
                replace=self.replace_text.get("1.0", "end-1c"),
            )

    def _on_line_field_changed(self, _event: tk.Event | None = None) -> None:
        if self._loading or self._selected_line_index is None:
            return
        self._save_current_line_rule()
        self._refresh_line_list(select_index=self._selected_line_index)
        self._mark_dirty()

    def _add_line_rule(self) -> None:
        self._save_current_line_rule()
        self._rule_set.lines.append(LineRule(find="", replace=""))
        self._refresh_line_list(select_index=len(self._rule_set.lines) - 1)
        self._mark_dirty()

    def _remove_line_rule(self) -> None:
        selection = self.line_list.curselection()
        if not selection:
            return
        index = selection[0]
        del self._rule_set.lines[index]
        next_index = min(index, len(self._rule_set.lines) - 1)
        self._refresh_line_list(select_index=next_index if next_index >= 0 else None)
        self._mark_dirty()

    def _move_line_rule(self, direction: int) -> None:
        selection = self.line_list.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + direction
        if 0 <= new_index < len(self._rule_set.lines):
            self._save_current_line_rule()
            lines = self._rule_set.lines
            lines[index], lines[new_index] = lines[new_index], lines[index]
            self._refresh_line_list(select_index=new_index)
            self._mark_dirty()
