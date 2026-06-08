# Change Tables

A simple Python app that converts PLC export text files using built-in transformation rules.

## Requirements

- Python 3
- tkinter (included with most Python installs)

## Run the app

```bash
python3 change_tables.py
```

1. Choose an **input** `.txt` file (old format)
2. Choose an **output** path
3. Click **Apply Changes**

Rules are stored in `rules.py` — no separate change table file needed.

## Compare output (temporary)

Check your output against `Modflt_New.txt`:

- In the GUI: click **Compare Output**
- From the terminal:

```bash
python3 compare_tool.py Modflt_old_modified.txt
```

## Tests

```bash
python3 -m unittest test_engine.py -v
```

## Adding new rules

Edit `rules.py`:

- `_LINE_RULES` — whole-line replacements (for rungs that need more than a simple find/replace)
- `_GLOBAL_RULES` — simple token swaps applied everywhere
