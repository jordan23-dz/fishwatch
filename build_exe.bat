@echo off
chcp 65001 >nul
title FishWatch.exe 만들기
cd /d "%~dp0"
echo FishWatch.exe를 만듭니다. 처음에는 PyInstaller 설치 때문에 1~3분 걸립니다.
echo.
set PY=py -3
where py >nul 2>nul || set PY=python
%PY% -m pip install --upgrade "pyinstaller==6.11.1"
if errorlevel 1 (
  echo PyInstaller를 설치하지 못했습니다. 인터넷 연결과 Python 설치를 확인하세요.
  pause
  exit /b 1
)
%PY% -m PyInstaller --noconfirm --clean fishwatch.spec
if errorlevel 1 (
  echo 만들지 못했습니다. 위 오류 메시지를 확인하세요.
  pause
  exit /b 1
)
echo.
echo 완료: %~dp0dist\FishWatch.exe
echo 이 파일 하나만 다른 사람에게 보내면 됩니다.
explorer "%~dp0dist"
pause
