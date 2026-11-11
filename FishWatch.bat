@echo off
chcp 65001 >nul
title FishWatch
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 app.py
  goto end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python app.py
  goto end
)
echo Python 3.11 이상이 필요합니다. https://www.python.org/downloads/ 에서 설치하세요.
echo 설치할 때 "Add python.exe to PATH"를 꼭 체크하세요.
:end
pause
