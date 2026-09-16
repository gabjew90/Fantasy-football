@echo off
title draftkit - yahoo sync
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
rem The Yahoo credentials live in the local .env and token file (never in
rem CI). This pulls every Yahoo resource the manager reads into
rem state\keefamania\yahoo\ and pushes it, so the scheduled Actions jobs read
rem Yahoo without holding a secret. Hourly at :50 from Task Scheduler, ahead
rem of the hourly Actions tick. An unchanged payload set is an empty commit
rem and is skipped.
if not exist data\logs mkdir data\logs
venv\Scripts\python.exe -m manager --league keefamania yahoo-sync >> data\logs\yahoo_sync.log 2>&1
git add state\keefamania\yahoo >> data\logs\yahoo_sync.log 2>&1
git diff --cached --quiet || git commit -m "state: yahoo sync %date% %time%" >> data\logs\yahoo_sync.log 2>&1
git pull --rebase --autostash >> data\logs\yahoo_sync.log 2>&1
git push >> data\logs\yahoo_sync.log 2>&1
