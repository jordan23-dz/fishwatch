"""판독 결과를 HTML(브라우저용)과 CSV(엑셀용) 보고서로 쓴다."""
from __future__ import annotations

import csv
import html
import json
from datetime import date
from pathlib import Path

from analyzer import SEV, SEV_LABEL

CSS = """
:root{--paper:#EDF1F0;--surface:#fff;--sunk:#F5F8F7;--ink:#13201E;--muted:#5A6A67;--line:#D2DBD9;--accent:#0D5C6C;
--danger:#B8321C;--warn:#9A6410;--info:#2F5F8F;--ok:#2C7349;--danger-bg:#FBE9E5;--warn-bg:#FBF1DE;--info-bg:#E6EEF7;--ok-bg:#E3F2E8}
@media (prefers-color-scheme:dark){:root{--paper:#0E1615;--surface:#15201E;--sunk:#111B1A;--ink:#E3ECEA;--muted:#91A39F;--line:#293A37;
--accent:#5DB0BF;--danger:#F07D66;--warn:#E2B158;--info:#86AEDA;--ok:#6CC18F;--danger-bg:#3A1C16;--warn-bg:#352812;--info-bg:#172839;--ok-bg:#15301F;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 "Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;padding:24px max(16px,3vw) 48px}
.wrap{max-width:1100px;margin:0 auto}h1{font-size:26px;margin:4px 0}.muted{color:var(--muted);font-size:13px}
.sum{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.pill{font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap}
.s-danger{background:var(--danger-bg);color:var(--danger)}.s-warn{background:var(--warn-bg);color:var(--warn)}.s-info{background:var(--info-bg);color:var(--info)}.s-ok{background:var(--ok-bg);color:var(--ok)}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:10px 0 16px}select,label{font:inherit;font-size:14px}select{padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--ink)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:12px;display:grid;grid-template-columns:4px minmax(0,1fr);gap:12px}
.stripe{border-radius:2px}.danger .stripe{background:var(--danger)}.warn .stripe{background:var(--warn)}.info .stripe{background:var(--info)}.ok .stripe{background:var(--ok)}
.top{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}.top a{font-weight:700;color:var(--ink);text-decoration:none;word-break:break-word}.top a:hover{text-decoration:underline}
.site{font-size:12px;padding:2px 8px;border:1px solid var(--line);border-radius:5px;color:var(--muted)}.new{font-size:11px;font-weight:700;color:var(--accent);border:1px solid var(--accent);border-radius:4px;padding:0 5px}
.desc{font-size:13.5px;color:var(--muted);margin:6px 0;word-break:break-word}.f{margin-top:6px}.f b{font-size:14px}.f ul{margin:3px 0 0;padding-left:18px;font-size:13.5px}
.law{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--muted)}.meta{font-size:12px;color:var(--muted);margin-top:6px}
.empty{padding:20px;text-align:center;color:var(--muted)}
"""


def _card(x: dict) -> str:
    it, r = x["item"], x["result"]
    fs = []
    for f in r["findings"]:
        if SEV[f["sev"]] < SEV["warn"]:
            continue
        lis = "".join(f'<li>{html.escape(i["txt"])}</li>' for i in f["items"] if i["sev"] in ("danger", "warn"))
        fs.append(f'<div class="f"><b>{html.escape(f["name"])}</b> <span class="pill s-{f["sev"]}">{SEV_LABEL[f["sev"]]}</span> '
                  f'<span class="law">{html.escape(f["law"])}</span><ul>{lis}</ul></div>')
    who = it.extra.get("cafename") or it.extra.get("bloggername") or ""
    meta = " · ".join(filter(None, [who, f"작성일 {it.post_date}" if it.post_date else "작성일 미상(수집일 기준 판독)",
                                    f"검색어 “{it.query}”", f"최초 발견 {x['first_seen']}"]))
    return (f'<article class="card {r["sev"]}" data-sev="{r["sev"]}" data-site="{html.escape(it.site)}" data-new="{int(x["new"])}">'
            f'<div class="stripe"></div><div style="min-width:0"><div class="top"><span class="pill s-{r["sev"]}">{SEV_LABEL[r["sev"]]}</span>'
            f'<span class="site">{html.escape(it.site)}</span>{"<span class=new>NEW</span>" if x["new"] else ""}'
            f'<a href="{html.escape(it.link)}" target="_blank" rel="noopener">{html.escape(it.title) or "(제목 없음)"}</a></div>'
            f'<div class="desc">{html.escape(it.description)}</div>{"".join(fs)}<div class="meta">{html.escape(meta)}</div></div></article>')


def write_reports(shown: list[dict], all_rows: list[dict], out_dir: Path, day: date, now: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shown = sorted(shown, key=lambda x: (-SEV[x["result"]["sev"]], not x["new"], x["item"].site))
    sites = sorted({x["item"].site for x in shown})
    cnt = {k: sum(1 for x in shown if x["result"]["sev"] == k) for k in ("danger", "warn")}
    new = sum(1 for x in shown if x["new"])
    body = "".join(_card(x) for x in shown) or '<div class="empty">기준 이상으로 걸린 판매글이 없습니다.</div>'
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>판매글 점검 {day}</title><style>{CSS}</style></head><body><div class="wrap">
<div class="muted">수산자원관리법 시행령 별표 1·2 기준 · 실행 {html.escape(now)} · 판독 기준일 {day}</div>
<h1>수산물 판매글 점검 보고서</h1>
<div class="sum"><span class="pill s-danger">위반 의심 {cnt['danger']}</span><span class="pill s-warn">확인 필요 {cnt['warn']}</span>
<span class="pill s-info">신규 {new}</span><span class="pill s-ok">판독한 판매글 {len(all_rows)}</span></div>
<div class="bar"><select id="fs"><option value="">모든 사이트</option>{"".join(f'<option>{html.escape(s)}</option>' for s in sites)}</select>
<select id="fv"><option value="">모든 등급</option><option value="danger">위반 의심만</option><option value="warn">확인 필요만</option></select>
<label><input type="checkbox" id="fn"> 신규만</label></div>{body}
<p class="muted">검색 결과의 제목·요약문만 판독한 1차 선별 결과입니다. 원문과 사진, 원산지·어획일을 확인한 뒤 판단하세요.</p></div>
<script>const f=()=>{{const s=fs.value,v=fv.value,n=fn.checked;document.querySelectorAll('.card').forEach(c=>{{c.hidden=(s&&c.dataset.site!==s)||(v&&c.dataset.sev!==v)||(n&&c.dataset.new!=='1')}})}};
fs.onchange=fv.onchange=fn.onchange=f;</script></body></html>"""
    stamp = now.replace("-", "").replace(":", "").replace(" ", "-")
    html_path = out_dir / f"report-{stamp}.html"
    html_path.write_text(page, encoding="utf-8")
    (out_dir / "latest.html").write_text(page, encoding="utf-8")

    csv_path = out_dir / f"report-{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["등급", "신규", "사이트", "제목", "링크", "작성일", "어종", "사유", "검색어", "최초 발견"])
        for x in sorted(all_rows, key=lambda x: -SEV[x["result"]["sev"]]):
            it, r = x["item"], x["result"]
            bad = [f for f in r["findings"] if SEV[f["sev"]] >= SEV["warn"]]
            w.writerow([SEV_LABEL[r["sev"]], "Y" if x["new"] else "", it.site, it.title, it.link,
                        it.post_date or "", ", ".join(f["name"] for f in (bad or r["findings"])),
                        " / ".join(i["txt"] for f in bad for i in f["items"] if i["sev"] in ("danger", "warn")),
                        it.query, x["first_seen"]])
    return [html_path, csv_path]
