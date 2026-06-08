"""Rules editor using plain tkinter widgets."""

from __future__ import annotations

import copy
import tkinter as tk
from typing import Callable

from rules import default_rules_data, validate_rules_data


class RulesEditorPanel(tk.Frame):
    def __init__(self, master: tk.Misc, on_dirty: Callable[[], None], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.on_dirty = on_dirty
        self.rules_data = default_rules_data()
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
        self.global_list.bind("<Double-1>", lambda _e: self._edit_global())

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

    def set_rules_data(self, data: dict) -> None:
        self._loading = True
        self.rules_data = copy.deepcopy(data)
        self.word_30_var.set(bool(self.rules_data.get("word_30_fallback", True)))
        self._refresh_global_list()
        self._refresh_line_list(select_index=0 if self.rules_data.get("lines") else None)
        self._loading = False

    def get_rules_data(self) -> dict:
        data = copy.deepcopy(self.rules_data)
        data["word_30_fallback"] = self.word_30_var.get()
        return data

    def _mark_dirty(self) -> None:
        if not self._loading:
            self.on_dirty()

    def _refresh_global_list(self) -> None:
        self.global_list.delete(0, tk.END)
        for entry in self.rules_data.get("global", []):
            old = entry.get("old", "")
            new = entry.get("new", "")
            self.global_list.insert(tk.END, f"{old}  ->  {new}")

    def _add_global(self) -> None:
        old = self.global_old_var.get().strip()
        new = self.global_new_var.get()
        if not old:
            return
        self.rules_data.setdefault("global", []).append({"old": old, "new": new})
        self.global_old_var.set("")
        self.global_new_var.set("")
        self._refresh_global_list()
        self._mark_dirty()

    def _edit_global(self) -> None:
        selection = self.global_list.curselection()
        if not selection:
            return
        index = selection[0]
        entry = self.rules_data["global"][index]
        self.global_old_var.set(entry.get("old", ""))
        self.global_new_var.set(entry.get("new", ""))
        del self.rules_data["global"][index]
        self._refresh_global_list()
        self._mark_dirty()

    def _remove_global(self) -> None:
        selection = self.global_list.curselection()
        if not selection:
            return
        del self.rules_data["global"][selection[0]]
        self._refresh_global_list()
        self._mark_dirty()

    def _refresh_line_list(self, select_index: int | None = None) -> None:
        self.line_list.delete(0, tk.END)
        lines = self.rules_data.get("lines", [])
        for index, entry in enumerate(lines):
            preview = entry.get("find", "").replace("\t", " ").strip()[:40] or "(empty)"
            self.line_list.insert(tk.END, f"{index + 1}. {preview}")

        if select_index is not None and lines:
            index = max(0, min(select_index, len(lines) - 1))
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
        lines = self.rules_data.get("lines", [])
        if 0 <= index < len(lines):
            self._selected_line_index = index
            entry = lines[index]
            self._set_line_fields(entry.get("find", ""), entry.get("replace", ""))

    def _on_line_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.line_list.curselection()
        if selection:
            self._save_current_line_rule()
            self._load_line_rule(selection[0])

    def _save_current_line_rule(self) -> None:
        if self._selected_line_index is None:
            return
        lines = self.rules_data.setdefault("lines", [])
        if self._selected_line_index < len(lines):
            lines[self._selected_line_index] = {
                "find": self.find_text.get("1.0", "end-1c"),
                "replace": self.replace_text.get("1.0", "end-1c"),
            }

    def _on_line_field_changed(self, _event: tk.Event | None = None) -> None:
        if self._loading or self._selected_line_index is None:
            return
        self._save_current_line_rule()
        self._refresh_line_list(select_index=self._selected_line_index)
        self._mark_dirty()

    def _add_line_rule(self) -> None:
        self._save_current_line_rule()
        self.rules_data.setdefault("lines", []).append({"find": "", "replace": ""})
        self._refresh_line_list(select_index=len(self.rules_data["lines"]) - 1)
        self._mark_dirty()

    def _remove_line_rule(self) -> None:
        selection = self.line_list.curselection()
        if not selection:
            return
        index = selection[0]
        del self.rules_data["lines"][index]
        next_index = min(index, len(self.rules_data["lines"]) - 1)
        self._refresh_line_list(select_index=next_index if next_index >= 0 else None)
        self._mark_dirty()

    def _move_line_rule(self, direction: int) -> None:
        selection = self.line_list.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + direction
        lines = self.rules_data.get("lines", [])
        if 0 <= new_index < len(lines):
            self._save_current_line_rule()
            lines[index], lines[new_index] = lines[new_index], lines[index]
            self._refresh_line_list(select_index=new_index)
            self._mark_dirty()

    def commit_edits(self) -> None:
        self._save_current_line_rule()
        self.rules_data["word_30_fallback"] = self.word_30_var.get()

    def validate(self) -> None:
        self.commit_edits()
        validate_rules_data(self.rules_data)
