"""Rules tab for editing and saving rule sets."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from change_tables.gui.rules_editor_panel import RulesEditorPanel


class RulesTab(tk.Frame):
    """Toolbar and rule editor for managing conversion rules."""

    def __init__(
        self,
        master: tk.Misc,
        on_dirty: Callable[[], None],
        on_save: Callable[[], None],
        on_reload: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.on_save = on_save
        self.on_reload = on_reload
        self.editor = RulesEditorPanel(self, on_dirty=on_dirty)
        self._build_ui()

    def _build_ui(self) -> None:
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        bar = tk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        tk.Button(bar, text="Save Rules", command=self.on_save).pack(side=tk.LEFT)
        tk.Button(bar, text="Reload", command=self.on_reload).pack(side=tk.LEFT, padx=5)

        self.editor.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
