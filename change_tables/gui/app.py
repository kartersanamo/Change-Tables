"""Main application window."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from change_tables.config import DEFAULT_RULES_PATH
from change_tables.gui.convert_tab import ConvertTab
from change_tables.gui.rules_tab import RulesTab
from change_tables.services.conversion_service import ConversionService
from change_tables.services.rules_session import RulesSession, UnsavedChangesError


class ChangeTablesApp(tk.Tk):
    """Top-level window coordinating conversion and rule editing."""

    def __init__(
        self,
        conversion_service: ConversionService | None = None,
        rules_session: RulesSession | None = None,
    ) -> None:
        super().__init__()
        self.title("Change Tables")
        self.geometry("750x625")

        self._conversion_service = conversion_service or ConversionService()
        self._rules_session = rules_session or RulesSession(DEFAULT_RULES_PATH)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.rules_path = tk.StringVar(value=str(self._rules_session.path))
        self.status_text = tk.StringVar(value="")
        self.rules_dirty = False

        self.rules_tab: RulesTab
        self._build_ui()
        self._load_rules_into_editor()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        convert_tab = ConvertTab(
            notebook,
            input_path=self.input_path,
            output_path=self.output_path,
            rules_path=self.rules_path,
            on_convert=self._apply_changes,
            on_browse_rules=self._browse_rules,
        )
        self.rules_tab = RulesTab(
            notebook,
            on_dirty=self._mark_rules_dirty,
            on_save=self._save_rules,
            on_reload=self._reload_rules,
        )
        notebook.add(convert_tab, text="Convert")
        notebook.add(self.rules_tab, text="Rules")

        tk.Label(self, textvariable=self.status_text).pack(anchor="w", padx=10, pady=(0, 10))

    def _mark_rules_dirty(self) -> None:
        self.rules_dirty = True
        self._rules_session.mark_dirty()
        self.status_text.set("Rules changed (not saved)")

    def _sync_session_from_editor(self) -> None:
        self.rules_tab.editor.commit_edits()
        self._rules_session.set_rule_set(self.rules_tab.editor.get_rule_set(), dirty=self.rules_dirty)

    def _load_rules_into_editor(self) -> None:
        rules_file = Path(self.rules_path.get().strip())
        self._rules_session.path = rules_file
        self._rules_session.work_path = rules_file.parent / f"{rules_file.stem}.work{rules_file.suffix}"
        try:
            self._rules_session.load()
            self.rules_tab.editor.set_rule_set(self._rules_session.get_rule_set())
            self.rules_dirty = self._rules_session.dirty
            self.status_text.set("Rules loaded" if not self.rules_dirty else "Rules changed (not saved)")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _browse_rules(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        if self.rules_dirty and not messagebox.askyesno("Unsaved", "Discard unsaved changes?"):
            return
        self.rules_path.set(path)
        self._load_rules_into_editor()

    def _save_rules(self) -> None:
        rules_file = Path(self.rules_path.get().strip())
        if not rules_file.name:
            messagebox.showerror("Error", "No rules file selected.")
            return
        try:
            self._sync_session_from_editor()
            self._rules_session.path = rules_file
            self._rules_session.work_path = rules_file.parent / f"{rules_file.stem}.work{rules_file.suffix}"
            self._rules_session.save()
            self.rules_dirty = False
            self.status_text.set("Rules saved")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _reload_rules(self) -> None:
        if self.rules_dirty and not messagebox.askyesno("Reload", "Discard unsaved changes?"):
            return
        try:
            self._rules_session.reload(force=True)
            self.rules_tab.editor.set_rule_set(self._rules_session.get_rule_set())
            self.rules_dirty = False
            self.status_text.set("Rules loaded")
        except (OSError, ValueError, json.JSONDecodeError, UnsavedChangesError) as exc:
            messagebox.showerror("Error", str(exc))

    def _on_close(self) -> None:
        if self.rules_dirty:
            answer = messagebox.askyesnocancel("Unsaved", "Save rules before quitting?")
            if answer is None:
                return
            if answer:
                self._save_rules()
                if self.rules_dirty:
                    return
        self.destroy()

    def _apply_changes(self) -> None:
        input_file = Path(self.input_path.get().strip())
        output_file = Path(self.output_path.get().strip())

        if not input_file.is_file():
            messagebox.showerror("Error", "Select an input file.")
            return
        if not output_file.name:
            messagebox.showerror("Error", "Select an output path.")
            return

        try:
            self._sync_session_from_editor()
            self._rules_session.validate()
            source_text = input_file.read_text(encoding="utf-8")
            modified_text = self._conversion_service.convert(source_text, self._rules_session.get_rule_set())
            output_file.write_text(modified_text, encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.status_text.set(f"Saved {output_file.name}")
        messagebox.showinfo("Done", f"Saved to {output_file.name}")


def run_app() -> None:
    """Launch the Change Tables GUI."""
    ChangeTablesApp().mainloop()
