"""Tkinter GUI for Change Tables."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from rule_editor import RulesEditorPanel
from rules import (
    DEFAULT_RULES_PATH,
    cache_rules,
    convert,
    read_rules_data,
    save_rules_data,
)


class ChangeTablesApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Change Tables")
        self.geometry("750x625")

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.rules_path = tk.StringVar(value=str(DEFAULT_RULES_PATH))
        self.status_text = tk.StringVar(value="")
        self.rules_dirty = False

        self._build_ui()
        self._load_rules_into_editor()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        convert_tab = tk.Frame(notebook)
        rules_tab = tk.Frame(notebook)
        notebook.add(convert_tab, text="Convert")
        notebook.add(rules_tab, text="Rules")

        self._build_convert_tab(convert_tab)
        self._build_rules_tab(rules_tab)

        tk.Label(self, textvariable=self.status_text).pack(anchor="w", padx=10, pady=(0, 10))

    def _build_convert_tab(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        self._file_row(parent, 0, "Input:", self.input_path, self._browse_input)
        self._file_row(parent, 1, "Output:", self.output_path, self._browse_output)
        self._file_row(parent, 2, "Rules:", self.rules_path, self._browse_rules)

        tk.Button(parent, text="Convert", command=self._apply_changes).grid(
            row=3, column=0, columnspan=3, pady=15, sticky="w", padx=5
        )

    def _build_rules_tab(self, parent: tk.Frame) -> None:
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        bar = tk.Frame(parent)
        bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        tk.Button(bar, text="Save Rules", command=self._save_rules).pack(side=tk.LEFT)
        tk.Button(bar, text="Reload", command=self._reload_rules).pack(side=tk.LEFT, padx=5)

        self.rules_editor = RulesEditorPanel(parent, on_dirty=self._mark_rules_dirty)
        self.rules_editor.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def _file_row(self, parent: tk.Frame, row: int, label: str, variable: tk.StringVar, command) -> None:
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=5)
        tk.Entry(parent, textvariable=variable, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(parent, text="Browse", command=command).grid(row=row, column=2, padx=5, pady=5)

    def _mark_rules_dirty(self) -> None:
        self.rules_dirty = True
        self.status_text.set("Rules changed (not saved)")

    def _load_rules_into_editor(self) -> None:
        rules_file = Path(self.rules_path.get().strip())
        try:
            data = read_rules_data(rules_file)
            cache_rules(data, rules_file)
            self.rules_editor.set_rules_data(data)
            self.rules_dirty = False
            self.status_text.set("Rules loaded")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.input_path.set(path)
            if not self.output_path.get():
                p = Path(path)
                self.output_path.set(str(p.with_name(f"{p.stem}_modified{p.suffix}")))

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            self.output_path.set(path)

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
            self.rules_editor.commit_edits()
            self.rules_editor.validate()
            data = self.rules_editor.get_rules_data()
            save_rules_data(rules_file, data)
            cache_rules(data, rules_file)
            self.rules_dirty = False
            self.status_text.set("Rules saved")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _reload_rules(self) -> None:
        if self.rules_dirty and not messagebox.askyesno("Reload", "Discard unsaved changes?"):
            return
        self._load_rules_into_editor()

    def _current_rules_data(self) -> dict:
        self.rules_editor.commit_edits()
        data = self.rules_editor.get_rules_data()
        cache_rules(data, Path(self.rules_path.get().strip()) if self.rules_path.get().strip() else None)
        return data

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
            data = self._current_rules_data()
            self.rules_editor.validate()
            source_text = input_file.read_text(encoding="utf-8")
            modified_text = convert(source_text, data=data)
            output_file.write_text(modified_text, encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.status_text.set(f"Saved {output_file.name}")
        messagebox.showinfo("Done", f"Saved to {output_file.name}")


def run_app() -> None:
    ChangeTablesApp().mainloop()
