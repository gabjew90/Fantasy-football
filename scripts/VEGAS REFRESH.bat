@echo off
title draftkit - vegas refresh
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
rem The Odds API key lives in the local .env (never in CI). This pulls the
rem current week's implied totals into state/vegas/<season>-wk<NN>.json and
rem commits them so the scheduled Actions jobs read lines they cannot fetch.
rem Scheduled twice a week (Tue + Sat morning) from Task Scheduler; safe to
rem re-run -- an unchanged snapshot is an empty commit and is skipped.
if not exist data\logs mkdir data\logs
venv\Scripts\python.exe -m manager vegas-refresh >> data\logs\vegas_refresh.log 2>&1
git add state\vegas >> data\logs\vegas_refresh.log 2>&1
git diff --cached --quiet || git commit -m "state: vegas snapshot %date%" >> data\logs\vegas_refresh.log 2>&1
git pull --rebase --autostash >> data\logs\vegas_refresh.log 2>&1
git push >> data\logs\vegas_refresh.log 2>&1
