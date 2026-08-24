@echo off
title draftkit - season brief: %1
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
if not exist reports mkdir reports
venv\Scripts\python.exe -m draftkit %1 >> data\raw\season_briefs.log 2>&1
rem push the fresh brief so the GitHub app on the phone can read it anywhere
git add reports\waiver_brief.md reports\lineup_brief.md reports\early_check.md 2>nul
git commit -m "brief: %1 %date% %time%" >> data\raw\season_briefs.log 2>&1
git pull --rebase --autostash >> data\raw\season_briefs.log 2>&1
git push >> data\raw\season_briefs.log 2>&1
