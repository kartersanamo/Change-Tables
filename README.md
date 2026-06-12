# Change Tables

Convert PLC export text files using editable replacement rules.

## Requirements

- Python 3
- tkinter (included with most Python installs; GUI only)

## Setup and run

```bash
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
python -m pip install -r requirements.txt
python main.py               # opens GUI
```

On Windows PowerShell: `.venv\Scripts\Activate.ps1`

## Usage

### GUI

```bash
python main.py
```

**Convert tab**
1. Choose an **input** `.txt` file
2. Choose an **output** path
3. Click **Convert**

**Rules tab**
- Edit **global rules** (find/replace anywhere)
- Edit **line rules** (replace a whole line when it contains a match)
- Toggle **auto-convert** for leftover `*_WORD_30` tokens
- Click **Save Rules** to write to `rules.json`

Convert uses the current editor state, even before saving.

### CLI

Run CLI commands by passing a subcommand to `main.py`:

```bash
python main.py convert -i input.txt -o output.txt
python main.py rules show
python main.py shell
```

Global options (where applicable):

- `--rules PATH` — rules JSON file (default: `rules.json`)
- `--json` — machine-readable output
- `--quiet` — suppress status messages

#### Convert

```bash
python main.py convert -i Modflt_old.txt -o Modflt_modified.txt
python main.py convert -i input.txt                    # writes input_modified.txt
python main.py convert -i input.txt --rules custom.json
```

#### Rules

```bash
python main.py rules show
python main.py rules save
python main.py rules reload --force

python main.py rules settings word30 show
python main.py rules settings word30 on
python main.py rules settings word30 off

python main.py rules global list
python main.py rules global add --old OR_WORD_30 --new "OR_WORD 1"
python main.py rules global set --index 1 --old FOO --new BAR
python main.py rules global remove --index 2

python main.py rules line list
python main.py rules line show --index 1
python main.py rules line add --find "anchor" --replace "new line"
python main.py rules line set --index 1 --find-file find.txt --replace-file replace.txt
python main.py rules line remove --index 3
python main.py rules line move --index 2 --direction up
```

Use `--find-file` and `--replace-file` for multiline PLC rung text (tabs and newlines preserved).

**Batch edits without saving each step:**

```bash
python main.py rules global add --old TEMP --new X --no-save
python main.py rules line move --index 1 --direction down --no-save
python main.py rules save
```

`--no-save` writes to a sidecar `rules.work.json` until you run `rules save` or `rules reload --force`.

#### Interactive shell

The shell mirrors the GUI workflow — edit rules in memory, convert without saving, then save when ready:

```bash
python main.py shell --rules rules.json
```

Shell commands: `show`, `save`, `reload [--force]`, `convert -i INPUT [-o OUTPUT]`, `global list|add|set|remove`, `line list|show|add|set|remove|move`, `settings word30 on|off|show`, `help`, `quit`.

## Project structure

```
change_tables/
  config.py              # paths and constants
  models/                # RuleSet, LineRule, GlobalRule
  engine/                # RuleEngine, Word30Fallback
  persistence/           # JsonRulesRepository
  services/              # ConversionService, RulesSession
  cli/                   # argparse CLI (convert, rules, shell)
  gui/                   # Tkinter UI (one class per file)
main.py                  # entry point (GUI default, CLI subcommands)
rules.json               # default rules
tests/                   # unit tests
```

## Rules format (`rules.json`)

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

## Tests

```bash
python -m unittest discover -s tests -v
```
