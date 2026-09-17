@echo off
title draftkit - push repository secrets
cd /d "%~dp0.."
rem Sets the repository secrets GitHub Actions needs to read Yahoo and the
rem Odds API live, from the keys already on this machine. Values never
rem appear on screen: gh reads .env directly and the refresh token is piped.
rem Requires a one-time `gh auth login -w` (browser) by the repo owner.
rem gh from PATH, or the portable copy under %USERPROFILE%\tools\gh
for /d %%d in ("%USERPROFILE%\tools\gh\*") do if exist "%%d\bin\gh.exe" set "PATH=%%d\bin;%PATH%"
if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "PATH=%ProgramFiles%\GitHub CLI;%PATH%"
where gh >nul 2>nul || (echo gh is not installed & exit /b 1)
gh auth status >nul 2>nul || (echo run:  gh auth login -w   and then this again & exit /b 1)
echo setting ODDS_API_KEY, FANTASYPROS_API_KEY, YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET from .env ...
gh secret set -f .env || exit /b 1
echo setting YAHOO_REFRESH_TOKEN from the token file ...
venv\Scripts\python.exe scripts\yahoo_auth.py refresh-token | gh secret set YAHOO_REFRESH_TOKEN || exit /b 1
echo.
gh secret list
echo.
echo done -- Actions now reads Yahoo and Vegas live; the local sync jobs can be disabled.
