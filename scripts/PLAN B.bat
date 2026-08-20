@echo off
title draftkit - PLAN B (terminal tracker)
cd /d "%~dp0.."
venv\Scripts\python.exe -m draftkit track
pause
