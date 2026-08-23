@echo off
title draftkit - daily ADP diff
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
rem the redirect target dir must exist BEFORE cmd opens the log file,
rem or the whole line fails and python never runs (fresh-clone trap)
if not exist data\raw\adp_history mkdir data\raw\adp_history
venv\Scripts\python.exe -m draftkit adpdiff >> data\raw\adp_history\run.log 2>&1
