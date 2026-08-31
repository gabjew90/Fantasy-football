@echo off
title Yahoo draft-room poller (keefamania)
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8

rem Needs Chrome running with CDP enabled AND the Yahoo draft room open.
rem If Chrome is already running normally, close it first, then:
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
echo Open the Yahoo draft room in that Chrome window, then press any key...
pause >nul
venv\Scripts\python.exe scripts\yahoo_draft_poller.py --league keefamania
pause
