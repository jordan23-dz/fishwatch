#!/bin/sh
# macOS: 더블클릭으로 FishWatch 실행
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 app.py
fi
echo "Python 3.11 이상이 필요합니다. https://www.python.org/downloads/ 에서 설치하세요."
read -r _
