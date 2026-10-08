@echo off
title draftkit - yahoo sync
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
rem The Yahoo credentials live in the local .env and token file (never in
rem CI). This pulls every Yahoo resource the fantasy commands read into
rem state\keefamania\yahoo\ and pushes it, so a host without the credentials
rem (manager.yahoo_api.read_cached) reads a recent copy instead of nothing.
rem Hourly at :50 from Task Scheduler. (The scheduled Actions jobs it was
rem first built for were retired on 2026-10-08, DECISIONS #212.) An unchanged
rem payload set is an empty commit and is skipped.
if not exist data\logs mkdir data\logs
venv\Scripts\python.exe -m manager --league keefamania yahoo-sync >> data\logs\yahoo_sync.log 2>&1
git add state\keefamania\yahoo >> data\logs\yahoo_sync.log 2>&1
git diff --cached --quiet || git commit -m "state: yahoo sync %date% %time%" >> data\logs\yahoo_sync.log 2>&1
git pull --rebase --autostash >> data\logs\yahoo_sync.log 2>&1
git push >> data\logs\yahoo_sync.log 2>&1
