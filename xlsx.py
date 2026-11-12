"""엑셀(.xlsx) 파일 쓰기 — 추가 설치 없이 표준 라이브러리만 사용.

write_xlsx(path, sheets)
  sheets: [{"name": 시트 이름, "headers": [...], "rows": [[...], ...],
            "widths": [열 너비...], "link_col": 링크 열 번호(0부터, 없으면 None),
            "sev_col": 등급 열 번호(색칠, 없으면 None)}]
첫 줄 고정, 필터, 링크 클릭, 등급 칸 색 표시를 넣는다.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
SEV_STYLE = {"위반 의심": 2, "확인 필요": 3}  # cellXfs 번호


def _txt(v) -> str:
    s = _BAD.sub("", "" if v is None else str(v))
    return escape(s[:32000])


def _col(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3">
<font><sz val="10"/><name val="맑은 고딕"/><family val="2"/></font>
<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="맑은 고딕"/><family val="2"/></font>
<font><u/><sz val="10"/><color rgb="FF0D5C6C"/><name val="맑은 고딕"/><family val="2"/></font>
</fonts>
<fills count="5">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF0D5C6C"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFBE0DA"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFBEFD5"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="5">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _sheet(sh: dict) -> tuple[str, str]:
    headers, rows = sh["headers"], sh["rows"]
    link_col, sev_col = sh.get("link_col"), sh.get("sev_col")
    ncol = len(headers)
    last = _col(ncol - 1)
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
           f'<dimension ref="A1:{last}{len(rows) + 1}"/>',
           '<sheetViews><sheetView workbookViewId="0" tabSelected="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
           '<selection pane="bottomLeft" activeCell="A2" sqref="A2"/></sheetView></sheetViews>',
           '<sheetFormatPr defaultRowHeight="15"/>']
    widths = sh.get("widths") or [14] * ncol
    out.append("<cols>" + "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths)) + "</cols>")
    out.append("<sheetData>")
    out.append('<row r="1">' + "".join(f'<c r="{_col(i)}1" t="inlineStr" s="1"><is><t>{_txt(h)}</t></is></c>'
                                        for i, h in enumerate(headers)) + "</row>")
    links = []
    for ri, row in enumerate(rows, start=2):
        cells = []
        for ci, v in enumerate(row):
            ref = f"{_col(ci)}{ri}"
            style = 0
            if ci == sev_col:
                style = SEV_STYLE.get(str(v), 0)
            if ci == link_col and v and str(v).startswith(("http://", "https://")) and len(str(v)) < 2000:
                style = 4
                links.append((ref, str(v)))
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f'<c r="{ref}" s="{style}"><v>{v}</v></c>')
            elif v is None or v == "":
                if style:
                    cells.append(f'<c r="{ref}" s="{style}"/>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{_txt(v)}</t></is></c>')
        out.append(f'<row r="{ri}">' + "".join(cells) + "</row>")
    out.append("</sheetData>")
    out.append(f'<autoFilter ref="A1:{last}{max(len(rows), 1) + 1}"/>')
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    if links:
        out.append("<hyperlinks>" + "".join(f'<hyperlink ref="{ref}" r:id="rId{i + 1}"/>' for i, (ref, _) in enumerate(links)) + "</hyperlinks>")
        rels += [f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                 f'Target="{escape(url, {chr(34): "&quot;"})}" TargetMode="External"/>' for i, (_, url) in enumerate(links)]
    out.append('<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>')
    out.append("</worksheet>")
    rels.append("</Relationships>")
    return "".join(out), "".join(rels)


def write_xlsx(path: Path, sheets: list[dict]) -> Path:
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        n = len(sheets)
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
                             'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(n))
                   + "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        names = []
        for sh in sheets:
            nm = re.sub(r"[\[\]\*\?/\\:]", " ", sh["name"])[:31] or "Sheet"
            names.append(nm)
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(nm)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, nm in enumerate(names))
                   + "</sheets><definedNames>"
                   + "".join(f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">'
                             f"'{escape(nm)}'!$A$1:${_col(len(sh['headers']) - 1)}${max(len(sh['rows']), 1) + 1}</definedName>"
                             for i, (nm, sh) in enumerate(zip(names, sheets)))
                   + "</definedNames></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                             f'Target="worksheets/sheet{i + 1}.xml"/>' for i in range(n))
                   + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   "</Relationships>")
        z.writestr("xl/styles.xml", STYLES)
        for i, sh in enumerate(sheets):
            xml, rels = _sheet(sh)
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", xml)
            z.writestr(f"xl/worksheets/_rels/sheet{i + 1}.xml.rels", rels)
    tmp.replace(path)
    return path
