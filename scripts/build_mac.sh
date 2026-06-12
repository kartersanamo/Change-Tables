#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m PyInstaller ChangeTables.spec --noconfirm --clean

APP_PATH="dist/Change Tables.app"
ZIP_PATH="dist/ChangeTables-mac-v1.0.0.zip"

rm -f "$ZIP_PATH"
(
  cd dist
  COPYFILE_DISABLE=1 zip -r -X "$(basename "$ZIP_PATH")" "Change Tables.app" >/dev/null
)

echo "Built: $APP_PATH"
echo "Release zip: $ZIP_PATH"
