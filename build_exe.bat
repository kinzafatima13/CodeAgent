@echo off
REM Build CodeAgent.exe (Windows, Python 3.10+)
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name CodeAgent --clean app.py
echo.
echo Built: dist\CodeAgent.exe
