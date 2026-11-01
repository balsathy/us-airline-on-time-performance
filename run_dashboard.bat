@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 goto no_python
    set "PYTHON=python"
)

echo [1/3] Downloading available BTS monthly files...
%PYTHON% download_bts_data.py
if errorlevel 1 goto failed

echo.
echo [2/3] Building dashboard data...
%PYTHON% build_airport_summary.py
if errorlevel 1 goto failed

echo.
echo [3/3] Starting the dashboard...
start "Airline dashboard server" /min cmd /c "%PYTHON% -m http.server 8000 --bind 127.0.0.1"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000/index.html"
echo Dashboard opened at http://127.0.0.1:8000/index.html
echo Close the minimized server window to stop the local web server.
exit /b 0

:no_python
echo Python 3 was not found. Install Python 3 and try again.
echo During installation, enable the option to add Python to PATH.
pause
exit /b 1

:failed
echo.
echo The dashboard setup failed. Review the error above, then try again.
pause
exit /b 1
