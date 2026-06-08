# Change Tables

A simple Python app that converts PLC export text files using editable replacement rules.

## Requirements

- Python 3
- tkinter (included with most Python installs)

## Run the app

```bash
python3 main.py
```

### Convert tab
1. Choose an **input** `.txt` file
2. Choose an **output** path
3. Click **Apply Changes**

### Edit Rules tab
- Edit **global rules** (simple find/replace anywhere in the file)
- Edit **line rules** (replace an entire line when it contains a matching anchor)
- Toggle **auto-convert** for leftover `*_WORD_30` tokens
- Click **Save Rules** to write changes to `rules.json`

Apply Changes uses the current rules in the editor, even before saving.

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

You can edit rules in the GUI or directly in the JSON file.

## Tests

```bash
python3 -m unittest test_engine.py -v
```
