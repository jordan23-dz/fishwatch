"""수집 → 판독 → 저장 → 보고서. 앱(app.py)과 명령줄(run.py)이 함께 쓴다."""
from __future__ import annotations

import json
import os
import sqlite3
import tomllib
from datetime import date, datetime
from pathlib import Path

from analyzer import SEV, analyze, in_season_rules
from collector import (DEFAULT_EXCLUDE, EXCLUDE_LABEL, AuthError, MockSearch, NaverSearch, active_sites, collect,
                       exclude_reason, is_trade, site_query_words, title_has_species)
from report import write_reports

from paths import DATA, RES

HERE = DATA  # 설정·DB·보고서는 사용자 데이터 폴더에
CONFIG_PATH = DATA / "config.toml"

# 금지체장 미만 개체를 직접 가리키는 은어 등 상시 감시어
RISK_TERMS = ["총알오징어", "한입오징어", "풀치", "고도리", "상사리", "뺀찌", "깔따구", "빵게", "대게 암컷",
              "국산 명태", "국내산 생태", "동해 명태"]

DEFAULT_CONFIG = {
    "naver": {"provider": "hub", "client_id": "", "client_secret": ""},
    "collect": {"sources": ["cafearticle", "blog", "webkr"], "max_calls": 800, "region": "",
                "extra_queries": ["자연산 광어 판매", "자연산 우럭 판매", "자연산 전복 판매", "대문어 판매"],
                "exclude": list(DEFAULT_EXCLUDE), "title_species": True},
    "report": {"min_severity": "warn", "out_dir": "reports", "database": "fishwatch.db"},
    "app": {"auto_run": False, "run_time": "08:47"},
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path.exists():
        user = tomllib.loads(path.read_text(encoding="utf-8"))
        for sec, vals in user.items():
            cfg.setdefault(sec, {}).update(vals)
    return cfg


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    if isinstance(v, dict):  # 판매 사이트 같은 표는 인라인 테이블로
        return "{" + ", ".join(f"{k} = {_toml_value(x)}" for k, x in v.items()) + "}"
    return json.dumps(str(v), ensure_ascii=False)


def save_config(cfg: dict, path: Path = CONFIG_PATH) -> None:
    lines = ["# FishWatch 설정 (앱의 설정 화면에서 저장됨)"]
    for sec, vals in cfg.items():
        lines.append(f"\n[{sec}]")
        for k, v in vals.items():
            lines.append(f"{k} = {_toml_value(v)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_queries(day: date, ccfg: dict) -> tuple[list[str], list[str]]:
    season_terms = []
    for r in in_season_rules(day):
        if r.get("yearRound"):
            continue
        for a in r["al"][:4]:
            season_terms.append(f"{a} 판매")
    extra = [q for q in ccfg.get("extra_queries", []) if q.strip()]
    # 카페·블로그 검색은 '판매'를 붙여 판매·거래 글 위주로 찾는다
    # '오늘 잡은 ○○'도 함께 찾는다 ('판매'라는 말 없이 갓 잡은 것을 내놓는 글)
    species = list(dict.fromkeys(RISK_TERMS + [t.replace(" 판매", "") for t in season_terms]))
    queries = list(dict.fromkeys([f"{t} 판매" for t in RISK_TERMS] + season_terms
                                 + [f"오늘 잡은 {t}" for t in species] + extra))
    core = list(dict.fromkeys(species + extra))
    words = site_query_words(active_sites(ccfg))
    site_queries = [f"{t} {s}" for t in core for s in words]
    return queries, site_queries


def overseas_cap(r: dict, site: str) -> None:
    """해외 판매 사이트 상품은 수입품일 가능성이 커서 '위반 의심'으로 올리지 않는다."""
    for f in r["findings"]:
        if f["sev"] == "danger":
            f["sev"] = "warn"
        for i in f["items"]:
            if i["sev"] == "danger":
                i["sev"] = "warn"
        f["items"].append({"sev": "info", "txt": f"{site}은(는) 해외 판매 사이트라 상품이 수입품일 가능성이 큽니다. 금어기·금지체장은 국내 해역 포획물에 적용됩니다."})
    r["sev"] = max((f["sev"] for f in r["findings"]), key=lambda s: SEV[s], default="ok")


_SCHEMA_READY: set = set()


def cleanup_posts(db: sqlite3.Connection, ccfg: dict, log=print) -> int:
    """지금 기준(판매 글 아님·제목에 어종 없음·수산물 아님·가공·수입·양식·무관한 주제)에 맞지 않는 이전 글을 목록에서 정리한다.
    검토 표시(확인 완료·제보함·오탐)한 글은 남긴다. 앱을 켤 때·설정을 저장할 때·점검할 때 실행."""
    trade_names = {s["name"] for s in active_sites(ccfg) if s.get("trade")}
    overseas_names = {s["name"] for s in (ccfg.get("sites") or []) if s.get("overseas")} | {"테무", "알리익스프레스"}
    excl = ccfg.get("exclude", DEFAULT_EXCLUDE)
    stale = [row[0] for row in db.execute("SELECT link, title, description, site FROM posts WHERE COALESCE(review,'')='' AND demo=0")
             if not is_trade(row[1] or "", row[2] or "", row[3] in trade_names)
             or (ccfg.get("title_species", True) and not title_has_species(row[1] or ""))
             or exclude_reason(row[1] or "", row[2] or "", row[3] in overseas_names, excl, row[0])]
    if stale:
        db.executemany("DELETE FROM posts WHERE link=?", [(x,) for x in stale])
        db.commit()
        log(f"지금 기준에 맞지 않는 이전 글 {len(stale)}건을 목록에서 정리했습니다.")
    return len(stale)


def open_db(cfg: dict) -> sqlite3.Connection:
    """DB 연결. 점검이 저장하는 동안에도 화면이 읽을 수 있게 WAL 모드 + 잠금 대기 30초.
    표 만들기·고치기는 처음 한 번만 한다(읽기 요청이 쓰기 잠금을 기다리지 않게)."""
    path = HERE / cfg["report"].get("database", "fishwatch.db")
    db = sqlite3.connect(path, check_same_thread=False, timeout=30)
    if str(path) in _SCHEMA_READY:
        return db
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS posts(
        link TEXT PRIMARY KEY, site TEXT, source TEXT, query TEXT, title TEXT, description TEXT,
        post_date TEXT, first_seen TEXT, last_seen TEXT, sev TEXT, findings TEXT, extra TEXT)""")
    cols = {r[1] for r in db.execute("PRAGMA table_info(posts)")}
    if "review" not in cols:
        db.execute("ALTER TABLE posts ADD COLUMN review TEXT DEFAULT ''")
    if "demo" not in cols:  # 예시 데이터로 만든 글 표시 (실제 점검 때 지움)
        db.execute("ALTER TABLE posts ADD COLUMN demo INTEGER DEFAULT 0")
    db.execute("""CREATE TABLE IF NOT EXISTS runs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT, finished TEXT, mock INTEGER,
        calls INTEGER, candidates INTEGER, danger INTEGER, warn INTEGER, new INTEGER, report TEXT, error TEXT)""")
    rcols = {r[1] for r in db.execute("PRAGMA table_info(runs)")}
    for col, typ in (("info", "INTEGER DEFAULT 0"), ("funnel", "TEXT")):
        if col not in rcols:
            db.execute(f"ALTER TABLE runs ADD COLUMN {col} {typ}")
    db.commit()
    _SCHEMA_READY.add(str(path))
    return db


def run_once(cfg: dict, mock: bool = False, day: date | None = None, log=print, progress=None) -> dict:
    """점검 1회. 실패하면 실패 기록을 남기고 예외를 그대로 올린다."""
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        return _run(cfg, mock, day or date.today(), started, log, progress)
    except Exception as e:
        db = open_db(cfg)
        db.execute("INSERT INTO runs(started,finished,mock,calls,candidates,danger,warn,new,error) VALUES(?,?,?,?,?,?,?,?,?)",
                   (started, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(mock), 0, 0, 0, 0, 0, str(e)))
        db.commit()
        db.close()
        raise


def _run(cfg: dict, mock: bool, day: date, started: str, log, progress=None) -> dict:
    ncfg, ccfg, rcfg = cfg["naver"], cfg["collect"], cfg["report"]
    if mock:
        api = MockSearch(RES / "sample_api")
        log("예시 데이터(sample_api)로 시험 점검합니다.")
    else:
        cid = os.environ.get("NAVER_CLIENT_ID") or ncfg.get("client_id")
        sec = os.environ.get("NAVER_CLIENT_SECRET") or ncfg.get("client_secret")
        if not cid or not sec:
            raise ValueError("네이버 API 키가 없습니다. 설정 화면에서 Client ID와 Client Secret을 입력하세요.")
        api = NaverSearch(cid, sec, provider=ncfg.get("provider", "hub"))

    queries, site_queries = build_queries(day, ccfg)
    log(f"기준일 {day} · 검색어 {len(queries)}개 · 사이트 검색어 {len(site_queries)}개")
    stats: dict = {}
    items = collect(api, queries, ccfg.get("sources", ["cafearticle", "blog", "webkr"]), site_queries,
                    max_calls=int(ccfg.get("max_calls", 800)), log=log, sites=active_sites(ccfg), stats=stats,
                    progress=progress, exclude=ccfg.get("exclude", DEFAULT_EXCLUDE),
                    title_species=bool(ccfg.get("title_species", True)))
    if not mock and stats["ok"] == 0 and stats["failed"] > 0:
        raise RuntimeError(f"검색 {stats['failed']}건이 모두 실패해 결과가 없습니다. 인터넷 연결과 API 키를 확인하세요. "
                           f"첫 오류: {stats['first_error']}")
    log(f"검색 성공 {stats['ok']}건" + (f" · 실패 {stats['failed']}건" if stats["failed"] else ""))
    funnel = (f"검색 결과 {stats['items']}개 → 대상 사이트 글 {stats['in_site']}개 → "
              f"판매·거래·경매 글 {len(items) + sum(stats['excluded'].values())}개 (그 밖의 글 {stats['not_sale']}개 제외) → "
              f"점검 대상 {len(items)}개"
              + (" (" + " · ".join(f"{EXCLUDE_LABEL[k]} {v}" for k, v in stats["excluded"].items() if v) + " 제외)"
                 if any(stats["excluded"].values()) else ""))
    log(funnel)

    region = ccfg.get("region") or None
    db = open_db(cfg)
    # 예시 데이터 결과는 다음 점검(예시든 실제든) 때 지운다. 실제 결과와 섞이지 않게.
    db.execute("DELETE FROM posts WHERE demo=1")
    cleanup_posts(db, ccfg, log)
    rows, new_links = [], set()
    no_species = 0
    for it in items:
        r = analyze(it.text, it.post_date or day, region)
        if not r["findings"]:
            no_species += 1
            continue
        if it.extra.get("overseas"):
            overseas_cap(r, it.site)
        prev = db.execute("SELECT first_seen FROM posts WHERE link=?", (it.link,)).fetchone()
        first = prev[0] if prev else started
        if not prev:
            new_links.add(it.link)
        db.execute("""INSERT INTO posts(link,site,source,query,title,description,post_date,first_seen,last_seen,sev,findings,extra,demo)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(link) DO UPDATE SET last_seen=excluded.last_seen, sev=excluded.sev, findings=excluded.findings,
            title=excluded.title, description=excluded.description""",
                   (it.link, it.site, it.source, it.query, it.title, it.description,
                    it.post_date.isoformat() if it.post_date else None, first, started, r["sev"],
                    json.dumps(r["findings"], ensure_ascii=False), json.dumps(it.extra, ensure_ascii=False), int(mock)))
        rows.append({"item": it, "result": r, "first_seen": first, "new": it.link in new_links})

    min_sev = rcfg.get("min_severity", "warn")
    shown = [x for x in rows if SEV[x["result"]["sev"]] >= SEV[min_sev]]
    paths = write_reports(shown, rows, HERE / rcfg.get("out_dir", "reports"), day, started)
    summary = {"started": started, "finished": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mock": mock,
               "calls": api.calls, "candidates": len(items),
               "danger": sum(1 for x in rows if x["result"]["sev"] == "danger"),
               "warn": sum(1 for x in rows if x["result"]["sev"] == "warn"),
               "info": sum(1 for x in rows if x["result"]["sev"] in ("info", "ok")),
               "new": len(new_links), "report": str(paths[0])}
    summary["funnel"] = funnel + f" → 규제 어종이 나온 글 {len(rows)}개 (위반 의심 {summary['danger']} · 확인 필요 {summary['warn']} · 참고 {summary['info']})"
    db.execute("INSERT INTO runs(started,finished,mock,calls,candidates,danger,warn,new,report,info,funnel) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
               (summary["started"], summary["finished"], int(mock), summary["calls"], summary["candidates"],
                summary["danger"], summary["warn"], summary["new"], summary["report"], summary["info"], summary["funnel"]))
    db.commit()
    db.close()
    log(f"규제 어종이 나온 글 {len(rows)}개 (어종 없음 {no_species}개) · 위반 의심 {summary['danger']} · 확인 필요 {summary['warn']} · 참고 {summary['info']} · 신규 {summary['new']}")
    return summary
