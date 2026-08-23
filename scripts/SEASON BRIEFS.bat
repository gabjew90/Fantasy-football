@echo off
title draftkit - season brief: %1
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
if not exist reports mkdir reports
venv\Scripts\python.exe -m draftkit %1 >> data\raw\season_briefs.log 2>&1
