"""명령줄 실행용. 앱 없이 작업 스케줄러·cron으로 돌릴 때 쓴다.

  python run.py                 # 설정대로 한 번 실행
  python run.py --mock          # API 키 없이 예시 데이터로 시험
  python run.py --date 2026-06-25
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("Python 3.11 이상이 필요합니다.")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collector import AuthError  # noqa: E402
from pipeline import load_config, run_once  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="수산물 판매글 금어기·금지체장 자동 점검")
    ap.add_argument("--config", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--date")
    a = ap.parse_args()
    cfg = load_config(Path(a.config)) if a.config else load_config()
    try:
        s = run_once(cfg, mock=a.mock, day=date.fromisoformat(a.date) if a.date else None)
    except (ValueError, AuthError, RuntimeError) as e:
        sys.exit(str(e))
    print(f"보고서: {s['report']}")


if __name__ == "__main__":
    main()
