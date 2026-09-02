@echo off
title KEEFAMANIA DRAFT (Yahoo) - Sat Sep 5, 7:00 PM PT
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set DRAFTKIT_LEAGUE=keefamania

rem Draft-morning board refresh (Yahoo ADP + tiers). Comment out if offline.
venv\Scripts\python.exe -m draftkit market
venv\Scripts\python.exe -m draftkit tiers

start "" http://localhost:8724
rem Port 8724: keefamania's own port so Omnibeta's dashboard guard (8723)
rem never collides. This dashboard is the human view only; the draft itself
rem is made by the in-page driver per docs/draft-day-runbook.md (bridge +
rem driver.js). The old CDP poller was retired 2026-09-02.
venv\Scripts\python.exe -m draftkit --league keefamania web --port 8724
if "%errorlevel%"=="3" (
  echo dashboard already running - browser tab opened.
  timeout /t 4 >nul
)
