# Change Tables

A simple Python app that converts PLC export text files using rules from `rules.json`.

## Requirements

- Python 3
- tkinter (included with most Python installs)

## Run the app

```bash
python3 main.py
```

1. Choose an **input** `.txt` file
2. Choose an **output** path
3. Click **Apply Changes**

Rules load from `rules.json` by default. You can pick a different rules file in the GUI.

## Rules format (`rules.json`)

```json
{
  "word_30_fallback": true,
  "lines": [
    {
      "find": "text that appears in a line",
      "replace": "the full new line"
    }
  ],
  "global": [
    { "old": "OR_WORD_30", "new": "OR_WORD 1" }
  ]
}
```

- **lines** — if a line contains `find`, the whole line is replaced with `replace` (checked top to bottom)
- **global** — find-and-replace anywhere in the file (runs after line rules)
- **word_30_fallback** — when `true`, any leftover `*_WORD_30` tokens are auto-converted (e.g. `FOO_WORD_30` → `FOO_WORD 1`)

Add, remove, or edit entries in the JSON file — no code changes needed.