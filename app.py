"""FishWatch 앱. 내 컴퓨터에서만 열리는 화면(http://127.0.0.1:8765)을 띄운다.

더블클릭: Windows는 FishWatch.bat, macOS는 FishWatch.command
"""
from __future__ import annotations

import json
import sys
import threading
import time
import traceback
import webbrowser
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

if sys.version_info < (3, 11):
    input("Python 3.11 이상이 필요합니다. python.org 에서 설치 후 다시 실행하세요. [Enter]")
    sys.exit(1)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import DATA, EXE_DIR, FROZEN, RES, VERSION  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
from analyzer import RULES, analyze  # noqa: E402
from collector import NaverSearch  # noqa: E402
from pipeline import cleanup_posts, load_config, open_db, run_once, save_config  # noqa: E402

PORT = 8765
STATE = {"running": False, "log": [], "last": None, "error": None, "progress": None}
LOCK = threading.Lock()


def log(msg: str) -> None:
    STATE["log"].append(f"{datetime.now().strftime('%H:%M:%S')}  {msg}")
    STATE["log"] = STATE["log"][-200:]


def start_run(mock: bool) -> bool:
    with LOCK:
        if STATE["running"]:
            return False
        STATE.update(running=True, log=[], error=None, progress=None)

    def work():
        try:
            def progress(done, total, cand):
                STATE["progress"] = {"done": done, "total": total, "candidates": cand}
            STATE["last"] = run_once(load_config(), mock=mock, log=log, progress=progress)
        except Exception as e:  # 화면에 그대로 보여 준다
            STATE["error"] = str(e)
            log(f"오류: {e}")
            if not isinstance(e, ValueError):
                traceback.print_exc()
        finally:
            STATE["running"] = False
    threading.Thread(target=work, daemon=True).start()
    return True


def scheduler() -> None:
    """앱이 켜져 있는 동안 설정한 시각에 하루 한 번 자동 점검."""
    last_day = None
    while True:
        try:
            a = load_config().get("app", {})
            now = datetime.now()
            if a.get("auto_run") and now.strftime("%H:%M") == a.get("run_time", "08:47") and last_day != now.date():
                last_day = now.date()
                log("예약 시각이 되어 자동 점검을 시작합니다.")
                start_run(False)
        except Exception:
            traceback.print_exc()
        time.sleep(20)


def masked(cfg: dict) -> dict:
    c = json.loads(json.dumps(cfg))
    s = c["naver"].get("client_secret", "")
    c["naver"]["client_secret"] = ""
    c["naver"]["has_secret"] = bool(s)
    return c


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n).decode("utf-8") or "{}")

    def _local_only(self) -> bool:
        # 다른 사이트가 이 앱으로 요청을 보내지 못하게 막는다
        host = (self.headers.get("Host") or "").split(":")[0]
        origin = self.headers.get("Origin")
        ok = host in ("127.0.0.1", "localhost") and (origin is None or urlparse(origin).hostname in ("127.0.0.1", "localhost"))
        if not ok:
            self._json({"error": "forbidden"}, 403)
        return ok

    def do_GET(self):
        try:
            self._get()
        except Exception as e:  # 한 요청이 실패해도 빈 응답 대신 오류를 돌려준다
            traceback.print_exc()
            self._json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            self._post()
        except Exception as e:
            traceback.print_exc()
            self._json({"error": str(e)}, 500)

    def _get(self):
        if not self._local_only():
            return
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            b = (RES / "ui" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/api/state":
            db = open_db(load_config())
            runs = [dict(zip([c[0] for c in db.execute("SELECT * FROM runs LIMIT 0").description], r))
                    for r in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 10")]
            totals = dict(db.execute("SELECT sev, COUNT(*) FROM posts GROUP BY sev").fetchall())
            open_cnt = db.execute("SELECT COUNT(*) FROM posts WHERE sev IN ('danger','warn') AND COALESCE(review,'')=''").fetchone()[0]
            db.close()
            self._json({"running": STATE["running"], "log": STATE["log"], "error": STATE["error"], "progress": STATE["progress"],
                        "runs": runs, "totals": totals, "open": open_cnt, "config": masked(load_config()),
                        "today": date.today().isoformat(), "version": VERSION, "data_dir": str(DATA),
                        "frozen": FROZEN, "windows": os.name == "nt"})
        elif u.path == "/api/posts":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            sql, args = "SELECT * FROM posts WHERE 1=1", []
            if q.get("sev"):
                sql += " AND sev=?"; args.append(q["sev"])
            else:
                sql += " AND sev IN ('danger','warn')"
            if q.get("site"):
                sql += " AND site=?"; args.append(q["site"])
            if q.get("review") == "open":
                sql += " AND COALESCE(review,'')=''"
            elif q.get("review"):
                sql += " AND review=?"; args.append(q["review"])
            db = open_db(load_config())
            total = db.execute(sql.replace("SELECT *", "SELECT COUNT(*)", 1), args).fetchone()[0]
            limit = max(1, min(int(q.get("limit") or 500), 5000))
            offset = max(0, int(q.get("offset") or 0))
            sql += f" ORDER BY CASE sev WHEN 'danger' THEN 0 WHEN 'warn' THEN 1 ELSE 2 END, first_seen DESC, link LIMIT {limit} OFFSET {offset}"
            cols = [c[0] for c in db.execute("SELECT * FROM posts LIMIT 0").description]
            rows = [dict(zip(cols, r)) for r in db.execute(sql, args)]
            sites = [r[0] for r in db.execute("SELECT DISTINCT site FROM posts ORDER BY site")]
            db.close()
            for r in rows:
                r["findings"] = json.loads(r["findings"] or "[]")
                r["extra"] = json.loads(r["extra"] or "{}")
            self._json({"posts": rows, "sites": sites, "total": total, "offset": offset})
        elif u.path == "/api/rules":
            self._json(RULES)
        else:
            self._json({"error": "not found"}, 404)

    def _post(self):
        if not self._local_only():
            return
        u = urlparse(self.path)
        body = self._body()
        if u.path == "/api/run":
            ok = start_run(bool(body.get("mock")))
            self._json({"started": ok, "message": None if ok else "이미 점검이 진행 중입니다."})
        elif u.path == "/api/config":
            cfg = load_config()
            secret_before = cfg["naver"].get("client_secret", "")
            for sec, vals in body.items():
                if sec in cfg and isinstance(vals, dict):
                    cfg[sec].update({k: v for k, v in vals.items() if k != "has_secret"})
            if not body.get("naver", {}).get("client_secret"):
                cfg["naver"]["client_secret"] = secret_before  # 빈칸이면 기존 값 유지
            save_config(cfg)
            if not STATE["running"]:
                db = open_db(cfg)
                cleanup_posts(db, cfg["collect"], log)
                db.close()
            self._json({"saved": True, "config": masked(cfg)})
        elif u.path == "/api/review":
            db = open_db(load_config())
            db.execute("UPDATE posts SET review=? WHERE link=?", (body.get("review", ""), body.get("link")))
            db.commit(); db.close()
            self._json({"ok": True})
        elif u.path == "/api/testkey":
            # 화면에 입력 중인 값으로 시험. Secret 칸이 비어 있으면 저장된 값 사용
            n = load_config()["naver"]
            cid = (body.get("client_id") or n.get("client_id") or "").strip()
            sec = (body.get("client_secret") or n.get("client_secret") or "").strip()
            if not cid or not sec:
                self._json({"ok": False, "message": "Client ID와 Client Secret을 입력하세요."})
            else:
                self._json(NaverSearch(cid, sec, body.get("provider") or n.get("provider", "hub")).test())
        elif u.path == "/api/open-folder":
            target = DATA / "reports" if body.get("which") == "reports" else DATA
            target.mkdir(parents=True, exist_ok=True)
            open_folder(target)
            self._json({"ok": True, "path": str(target)})
        elif u.path == "/api/os-schedule":
            self._json(os_schedule(bool(body.get("enable")), body.get("time") or "08:47"))
        elif u.path == "/api/analyze":
            d = date.fromisoformat(body.get("date") or date.today().isoformat())
            posts = [p.strip() for p in (body.get("text") or "").split("\n---\n") if p.strip()]
            self._json([analyze(p, d, body.get("region") or None) for p in posts])
        else:
            self._json({"error": "not found"}, 404)


def open_folder(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # noqa: S606 - 탐색기로 폴더 열기
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def self_command(*args: str) -> list[str]:
    """이 앱을 다시 실행하는 명령 (exe면 exe, 아니면 python app.py)"""
    if FROZEN:
        return [sys.executable, *args]
    return [sys.executable, str(HERE / "app.py"), *args]


def os_schedule(enable: bool, hhmm: str) -> dict:
    """Windows 작업 스케줄러에 매일 점검 등록/해제. 앱을 꺼 두어도 컴퓨터가 켜져 있으면 돈다."""
    if os.name != "nt":
        return {"ok": False, "message": "Windows에서만 쓸 수 있습니다. macOS·Linux는 schedule_unix.sh를 쓰세요."}
    try:
        if enable:
            cmd = subprocess.list2cmdline(self_command("--run-once"))
            r = subprocess.run(["schtasks", "/create", "/tn", "FishWatch", "/sc", "daily", "/st", hhmm, "/f", "/tr", cmd],
                               capture_output=True, text=True)
        else:
            r = subprocess.run(["schtasks", "/delete", "/tn", "FishWatch", "/f"], capture_output=True, text=True)
        ok = r.returncode == 0
        msg = (f"Windows 작업 스케줄러에 매일 {hhmm} 점검을 등록했습니다. 앱을 꺼 두어도 컴퓨터가 켜져 있으면 실행됩니다."
               if enable else "Windows 작업 스케줄러에서 FishWatch 점검을 지웠습니다.") if ok else (r.stderr or r.stdout).strip()
        return {"ok": ok, "message": msg}
    except OSError as e:
        return {"ok": False, "message": f"등록하지 못했습니다: {e}"}


def run_once_cli() -> None:
    """작업 스케줄러가 부르는 화면 없는 1회 점검: FishWatch.exe --run-once [--mock]"""
    try:
        s = run_once(load_config(), mock="--mock" in sys.argv)
        print(f"보고서: {s['report']}")
    except Exception as e:
        print(f"점검 실패: {e}")
        sys.exit(1)


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    if "--run-once" in sys.argv:
        run_once_cli()
        return
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(f"FishWatch {VERSION} - 이 창을 닫으면 앱이 종료됩니다")
        except Exception:
            pass
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:
        print(f"FishWatch가 이미 실행 중입니다. 브라우저에서 http://127.0.0.1:{PORT} 를 여세요.")
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        return
    threading.Thread(target=scheduler, daemon=True).start()
    try:  # 앱을 켤 때 지금 기준에 맞지 않는 이전 글 정리
        cfg = load_config()
        db = open_db(cfg)
        n = cleanup_posts(db, cfg["collect"], lambda m: None)
        db.close()
        if n:
            print(f"지금 기준에 맞지 않는 이전 글 {n}건을 목록에서 정리했습니다.")
    except Exception:
        traceback.print_exc()
    url = f"http://127.0.0.1:{PORT}"
    print(f"FishWatch {VERSION} 실행 중: {url}\n데이터 폴더: {DATA}\n이 창을 닫으면 앱이 종료됩니다.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
