@echo off
echo [INFO] Creating Python Virtual Environment...
python -m venv venv

echo [INFO] Installing Dependencies (Stubs & PySide)...
.\venv\Scripts\pip install -r requirements.txt

echo.
echo [SUCCESS] Environment Setup Complete!
echo Now restart VS Code and select the interpreter in './venv/Scripts/python.exe'
pause