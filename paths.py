"""파일 위치.

- RES : 앱에 들어 있는 읽기 전용 파일(rules.json, ui/, sample_api/)
- DATA: 사용자가 바꾸는 파일(config.toml, fishwatch.db, reports/)

그냥 실행(python app.py)하면 둘 다 이 폴더.
exe로 실행하면 RES는 exe 안(임시 폴더), DATA는 %APPDATA%\\FishWatch (없으면 홈 폴더 아래 FishWatch).
exe 옆에 'portable.txt' 파일을 두면 DATA를 exe가 있는 폴더로 쓴다(USB 등에 넣고 다닐 때).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

VERSION = "1.1.5"
FROZEN = bool(getattr(sys, "frozen", False))

MAC = sys.platform == "darwin"

if FROZEN:
    RES = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    EXE_DIR = Path(sys.executable).resolve().parent
    # 맥 앱(FishWatch.app/Contents/MacOS/FishWatch)이면 .app이 놓인 폴더를 기준으로
    if MAC and EXE_DIR.name == "MacOS" and EXE_DIR.parent.parent.suffix == ".app":
        EXE_DIR = EXE_DIR.parent.parent.parent
    if (EXE_DIR / "portable.txt").exists():
        DATA = EXE_DIR
    elif MAC:
        DATA = Path.home() / "Library" / "Application Support" / "FishWatch"
    else:
        base = os.environ.get("APPDATA") or os.environ.get("XDG_CONFIG_HOME") or str(Path.home())
        DATA = Path(base) / "FishWatch"
else:
    RES = DATA = Path(__file__).resolve().parent
    EXE_DIR = DATA
    # exe판을 쓰다가 파이썬 실행으로 바꾼 경우: exe판의 설정·기록 폴더를 그대로 이어서 쓴다
    if not (DATA / "config.toml").exists() and not (DATA / "portable.txt").exists():
        if MAC:
            _shared = Path.home() / "Library" / "Application Support" / "FishWatch"
        else:
            _shared = Path(os.environ.get("APPDATA") or Path.home()) / "FishWatch"
        if (_shared / "config.toml").exists():
            DATA = _shared

DATA.mkdir(parents=True, exist_ok=True)


def warm_up() -> None:
    """점검 도중에야 처음 불러오는 표준 모듈을 시작할 때 미리 불러 둔다.
    (exe에서 실행 중 모듈을 늦게 불러오다 백신 잠금에 걸리는 일을 막음)"""
    import datetime as _dt
    import urllib.request as _ur
    try:
        _dt.datetime.strptime("20260101", "%Y%m%d")   # _strptime
        "naver.com".encode("idna")                     # encodings.idna, unicodedata
        "가".encode("utf-8-sig"); "가".encode("cp949")  # CSV 보고서, 한국어 Windows
        _ur.getproxies()                                # Windows 프록시 설정(winreg)
        import csv, html, http.client, json, ssl, sqlite3, tomllib, webbrowser  # noqa: F401,E401
        ssl.create_default_context()
    except Exception:
        pass

# 예전 폴더판에서 옮겨 올 때: exe 옆에 둔 config.toml / fishwatch.db 를 처음 한 번 DATA로 복사
if FROZEN and DATA != EXE_DIR:
    for name in ("config.toml", "fishwatch.db"):
        src, dst = EXE_DIR / name, DATA / name
        if src.exists() and not dst.exists():
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass
