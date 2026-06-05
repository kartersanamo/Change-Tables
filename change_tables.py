#!/usr/bin/env python3
"""Change Tables — apply find/replace rules from a change table to a text file."""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


CHANGE_LINE_PATTERN = re.compile(
    r"""^\s*
    (?:
        (?P<q1>["'])(?P<old_quoted>.*?)(?P=q1)
        |
        (?P<old_plain>[^=]+?)
    )
    \s*=\s*
    (?:
        (?P<q2>["'])(?P<new_quoted>.*?)(?P=q2)
        |
        (?P<new_plain>.+?)
    )
    \s*$
    """,
    re.VERBOSE,
)


def parse_change_table(path: Path) -> list[tuple[str, str]]:
    """Parse a change table file into ordered (old, new) replacement pairs."""
    rules: list[tuple[str, str]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = CHANGE_LINE_PATTERN.match(raw_line.rstrip("\n\r"))
        if not match:
            raise ValueError(f"Line {line_no}: could not parse rule: {raw_line!r}")

        old = match.group("old_quoted") if match.group("old_quoted") is not None else match.group("old_plain")
        new = match.group("new_quoted") if match.group("new_quoted") is not None else match.group("new_plain")
        rules.append((old.strip(), new.strip()))

    if not rules:
        raise ValueError("Change table has no rules.")

    return rules


def apply_rules(text: str, rules: list[tuple[str, str]]) -> str:
    """Apply replacement rules in order."""
    result = text
    for old, new in rules:
        result = result.replace(old, new)
    return result


class ChangeTablesApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Change Tables")
        self.minsize(520, 420)

        self.input_path = tk.StringVar()
        self.change_table_path = tk.StringVar()
        self.output_path = tk.StringVar()

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
            text="Apply find/replace rules from a change table to a text file.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._add_file_row(main, row=2, label="Input file (.txt):", variable=self.input_path, command=self._browse_input)
        self._add_file_row(
            main,
            row=3,
            label="Change table (.txt):",
            variable=self.change_table_path,
            command=self._browse_change_table,
        )
        self._add_file_row(
            main,
            row=4,
            label="Output file (.txt):",
            variable=self.output_path,
            command=self._browse_output,
        )

        ttk.Label(
            main,
            text='Change table format: one rule per line, e.g. "X" = "Y" or X = Y',
            foreground="#555555",
        ).grid(row=5, column=0, columnspan=3, sticky="w", **padding)

        button_row = ttk.Frame(main)
        button_row.grid(row=6, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Button(button_row, text="Apply Changes", command=self._apply_changes).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Clear", command=self._clear).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(main, text="Log:").grid(row=7, column=0, sticky="nw", **padding)
        self.log = tk.Text(main, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log.grid(row=7, column=1, columnspan=2, sticky="nsew", **padding)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(7, weight=1)

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

    def _browse_change_table(self) -> None:
        path = filedialog.askopenfilename(
            title="Select change table",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.change_table_path.set(path)

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save output as",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _clear(self) -> None:
        self.input_path.set("")
        self.change_table_path.set("")
        self.output_path.set("")
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _apply_changes(self) -> None:
        input_file = Path(self.input_path.get().strip())
        change_table_file = Path(self.change_table_path.get().strip())
        output_file = Path(self.output_path.get().strip())

        if not input_file.is_file():
            messagebox.showerror("Missing file", "Please select a valid input text file.")
            return
        if not change_table_file.is_file():
            messagebox.showerror("Missing file", "Please select a valid change table file.")
            return
        if not output_file.name:
            messagebox.showerror("Missing file", "Please choose an output file path.")
            return

        try:
            rules = parse_change_table(change_table_file)
            source_text = input_file.read_text(encoding="utf-8")
            modified_text = apply_rules(source_text, rules)
            output_file.write_text(modified_text, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("File error", str(exc))
            self._log(f"Error: {exc}")
            return
        except ValueError as exc:
            messagebox.showerror("Change table error", str(exc))
            self._log(f"Error: {exc}")
            return

        self._log(f"Loaded {len(rules)} rule(s) from {change_table_file.name}")
        for index, (old, new) in enumerate(rules, start=1):
            self._log(f"  {index}. {old!r} -> {new!r}")
        self._log(f"Read {input_file.name} ({len(source_text)} characters)")
        self._log(f"Wrote {output_file.name} ({len(modified_text)} characters)")
        messagebox.showinfo("Done", f"Saved modified file to:\n{output_file}")


def main() -> None:
    app = ChangeTablesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
