# Change Tables

Convert PLC export text files using editable replacement rules.

Change Tables applies **line rules** (replace a whole line when it contains a match), **global rules** (find and replace anywhere in the file), and an optional **word_30 fallback** that converts leftover `*_WORD_30` tokens. Use the desktop app or the built-in CLI.

## Download

Get the latest release from [GitHub Releases](https://github.com/kartersanamo/Change-Tables/releases).

| Platform | File | What you get |
|----------|------|--------------|
| macOS | `ChangeTables-mac-v1.0.0.zip` | `Change Tables.app` |
| Windows | `Change Tables.exe` | Standalone app (build on Windows) |

## Install from release

### macOS

1. Download and unzip `ChangeTables-mac-v1.0.0.zip`
2. Drag **Change Tables.app** to Applications
3. Double-click to open

If macOS blocks the app: **System Settings → Privacy & Security → Open Anyway**.

### Windows

1. Download `Change Tables.exe`
2. Run it (or place it in a folder of your choice)

If SmartScreen warns you, choose **More info → Run anyway**.

## Run from release

**GUI** — double-click the app (no arguments).

**CLI** — run from a terminal:

```bash
# macOS
"/Applications/Change Tables.app/Contents/MacOS/Change Tables" --cli rules show
"/Applications/Change Tables.app/Contents/MacOS/Change Tables" --cli convert -i input.txt -o output.txt

# Windows
"Change Tables.exe" --cli rules show
"Change Tables.exe" --cli convert -i input.txt -o output.txt
```

You can also pass subcommands directly without `--cli`:

```bash
"Change Tables.app/Contents/MacOS/Change Tables" convert -i input.txt -o output.txt
```

Rules are stored in `rules.json` beside the executable. On first launch, a default rules file is created automatically.

## Run from source

**Requirements:** Python 3.10+, tkinter (included with most Python installs)

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate             # Windows

python main.py                       # GUI
python main.py convert -i in.txt -o out.txt
python main.py rules show
python main.py --help
```

## Build from source

```bash
python3 -m venv .venv
source .venv/bin/activate

# macOS → dist/Change Tables.app + dist/ChangeTables-mac-v1.0.0.zip
bash scripts/build_mac.sh

# Windows → dist/Change Tables/Change Tables.exe
scripts\build_windows.bat
```

Build dependencies are in `requirements-dev.txt` (PyInstaller only). The runtime uses the Python standard library.

## Rules

Rules live in `rules.json`:

```json
{
  "word_30_fallback": true,
  "lines": [
    { "find": "anchor text", "replace": "full new line" }
  ],
  "global": [
    { "old": "OR_WORD_30", "new": "OR_WORD 1" }
  ]
}
```

Edit rules in the **Rules** tab (GUI) or with `rules` CLI commands. See `python main.py --help` for the full CLI reference.

## Tests

```bash
python -m unittest discover -s tests -v
```
