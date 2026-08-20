@echo off
title draftkit - daily ADP diff
cd /d "%~dp0.."
venv\Scripts\python.exe -m draftkit adpdiff >> data\raw\adp_history\run.log 2>&1
