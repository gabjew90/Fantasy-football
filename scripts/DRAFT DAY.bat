@echo off
title draftkit - DRAFT DAY
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PY=venv\Scripts\python.exe

echo.
echo === draftkit draft day ===
echo Refreshing market data (if this fails, the dashboard still opens
echo with the last good data and shows a banner about it)...
echo.
rem re-verify league rules against the board's assumptions: any commissioner
rem rule change since the last build shows up here as a red X
%PY% -m draftkit verify
%PY% -m draftkit market
%PY% -m draftkit tiers

start "" http://localhost:8723

:loop
%PY% -m draftkit web --port 8723
rem exact match only: "if errorlevel 3" would swallow ANY crash code >= 3
rem (e.g. 9009 missing python) as "already running" and exit silently
if "%errorlevel%"=="3" exit /b 0
echo.
echo Dashboard server stopped - restarting in 2 seconds (close this window to quit)...
timeout /t 2 /nobreak >nul
goto loop
