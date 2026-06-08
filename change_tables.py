"""Tkinter GUI for Change Tables."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from engine import GlobalRule, LineRule, rule_summary
from rules import DEFAULT_RULES_PATH, convert, get_rules, load_rules


class ChangeTablesApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Change Tables")
        self.minsize(480, 360)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.rules_path = tk.StringVar(value=str(DEFAULT_RULES_PATH))

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Change Tables", font=("Helvetica", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            main,
            text="Convert a text file using rules from rules.json.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._add_file_row(main, row=2, label="Input file (.txt):", variable=self.input_path, command=self._browse_input)
        self._add_file_row(
            main,
            row=3,
            label="Output file (.txt):",
            variable=self.output_path,
            command=self._browse_output,
        )
        self._add_file_row(
            main,
            row=4,
            label="Rules file (.json):",
            variable=self.rules_path,
            command=self._browse_rules,
        )

        button_row = ttk.Frame(main)
        button_row.grid(row=5, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Button(button_row, text="Apply Changes", command=self._apply_changes).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Clear", command=self._clear).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(main, text="Log:").grid(row=6, column=0, sticky="nw", **padding)
        self.log = tk.Text(main, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log.grid(row=6, column=1, columnspan=2, sticky="nsew", **padding)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(6, weight=1)

    def _add_file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=6)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=6)
        ttk.Button(parent, text="Browse…", command=command).grid(row=row, column=2, padx=(0, 12), pady=6)

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select input text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.input_path.set(path)
            if not self.output_path.get():
                input_file = Path(path)
                self.output_path.set(str(input_file.with_name(f"{input_file.stem}_modified{input_file.suffix}")))

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save output as",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _browse_rules(self) -> None:
        path = filedialog.askopenfilename(
            title="Select rules file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.rules_path.set(path)

    def _log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _clear(self) -> None:
        self.input_path.set("")
        self.output_path.set("")
        self.rules_path.set(str(DEFAULT_RULES_PATH))
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _apply_changes(self) -> None:
        input_file = Path(self.input_path.get().strip())
        output_file = Path(self.output_path.get().strip())
        rules_file = Path(self.rules_path.get().strip())

        if not input_file.is_file():
            messagebox.showerror("Missing file", "Please select a valid input text file.")
            return
        if not output_file.name:
            messagebox.showerror("Missing file", "Please choose an output file path.")
            return
        if not rules_file.is_file():
            messagebox.showerror("Missing file", "Please select a valid rules.json file.")
            return

        try:
            load_rules(rules_file)
            source_text = input_file.read_text(encoding="utf-8")
            modified_text = convert(source_text, rules_file)
            output_file.write_text(modified_text, encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Error", str(exc))
            self._log(f"Error: {exc}")
            return

        rules = get_rules()
        line_count, global_count = rule_summary(rules)
        self._log(f"Loaded {line_count} line rule(s) and {global_count} global rule(s) from {rules_file.name}")
        for index, rule in enumerate(rules, start=1):
            if isinstance(rule, LineRule):
                self._log(f"  {index}. [line] {rule.find!r}")
            elif isinstance(rule, GlobalRule):
                self._log(f"  {index}. {rule.old!r} -> {rule.new!r}")
        self._log(f"Read {input_file.name} ({len(source_text)} characters)")
        self._log(f"Wrote {output_file.name} ({len(modified_text)} characters)")
        messagebox.showinfo("Done", f"Saved modified file to:\n{output_file}")


def run_app() -> None:
    app = ChangeTablesApp()
    app.mainloop()
