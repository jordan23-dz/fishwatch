#!/bin/sh
# macOS·Linux: 매일 오전 8시 47분에 점검을 실행하도록 crontab에 등록합니다.
# 지우려면: crontab -l | grep -v fishwatch-run | crontab -
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3)"
LINE="47 8 * * * cd \"$HERE\" && \"$PY\" run.py >> \"$HERE/run.log\" 2>&1 # fishwatch-run"
( crontab -l 2>/dev/null | grep -v fishwatch-run; echo "$LINE" ) | crontab -
echo "등록 완료: $LINE"
echo "결과는 $HERE/reports/latest.html"
