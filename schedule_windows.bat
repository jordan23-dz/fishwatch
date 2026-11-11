@echo off
chcp 65001 >nul
REM 매일 오전 8시 47분에 점검을 실행하는 Windows 작업 스케줄러 작업을 등록합니다.
REM 시간을 바꾸려면 /st 값을 수정하세요. 지우려면: schtasks /delete /tn FishWatch /f
set HERE=%~dp0
schtasks /create /tn FishWatch /sc daily /st 08:47 /f ^
  /tr "cmd /c cd /d \"%HERE%\" && python run.py >> \"%HERE%run.log\" 2>&1"
echo.
echo 등록 완료. 결과는 reports\latest.html, 실행 기록은 run.log 에 남습니다.
pause
