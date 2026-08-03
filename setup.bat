@echo off
echo =========================================
echo MyRadar24 Setup
echo =========================================
echo.
echo Installing required dependencies...
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo =========================================
echo Installation complete!
echo.
echo To run the application, use:
echo   python myradar24.py
echo or double-click start.bat
echo =========================================
pause
