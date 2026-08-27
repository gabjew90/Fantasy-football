@echo off
title draftkit auto-manager
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
venv\Scripts\python.exe -m manager run
