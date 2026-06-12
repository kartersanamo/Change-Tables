@echo off
setlocal

cd /d "%~dp0\.."

if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
python -m PyInstaller ChangeTables.spec --noconfirm --clean

echo Built: dist\Change Tables\Change Tables.exe
