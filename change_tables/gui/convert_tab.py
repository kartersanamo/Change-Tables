"""Convert tab for selecting files and running conversion."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Callable


class ConvertTab(tk.Frame):
    """File selection UI and convert action."""

    def __init__(
        self,
        master: tk.Misc,
        input_path: tk.StringVar,
        output_path: tk.StringVar,
        rules_path: tk.StringVar,
        on_convert: Callable[[], None],
        on_browse_rules: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.input_path = input_path
        self.output_path = output_path
        self.rules_path = rules_path
        self.on_convert = on_convert
        self.on_browse_rules = on_browse_rules
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)

        self._file_row(0, "Input:", self.input_path, self._browse_input)
        self._file_row(1, "Output:", self.output_path, self._browse_output)
        self._file_row(2, "Rules:", self.rules_path, self.on_browse_rules)

        tk.Button(self, text="Convert", command=self.on_convert).grid(
            row=3, column=0, columnspan=3, pady=15, sticky="w", padx=5
        )

    def _file_row(self, row: int, label: str, variable: tk.StringVar, command: Callable[[], None]) -> None:
        tk.Label(self, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=5)
        tk.Entry(self, textvariable=variable, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self, text="Browse", command=command).grid(row=row, column=2, padx=5, pady=5)

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.input_path.set(path)
            if not self.output_path.get():
                file_path = Path(path)
                self.output_path.set(str(file_path.with_name(f"{file_path.stem}_modified{file_path.suffix}")))

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            self.output_path.set(path)
