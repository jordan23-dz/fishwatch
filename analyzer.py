"""판매글 텍스트를 수산자원관리법 시행령 금어기·금지체장 기준으로 판독한다.

웹 판독기(금어기·체장 판독기)의 판정 로직을 그대로 옮긴 모듈이다.
규칙 데이터는 같은 폴더의 rules.json 에 있다.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

from paths import RES  # noqa: E402

_DATA = json.loads((RES / "rules.json").read_text(encoding="utf-8"))
RULES: list[dict] = _DATA["rules"]
RULE = {r["id"]: r for r in RULES}

EXCLUDE = ['갑오징어', '대왕오징어', '반딧불오징어', '한치오징어', '창오징어', '화살오징어', '부세조기', '부세굴비', '부세',
           '부시리', '흰다리새우', '홍가리비', '방어진', '방어력', '방어전', '농어촌', '농어민', '농어업', '대구광역시', '대구시',
           '대구에서', '대구 지역', '대구지역', '소라게', '소라색', '생태계', '생태적', '동태적', '대하여', '대하는', '도미노',
           '하모니', '생태마을', '우럭조개', '왕우럭', '생태 다큐', '생태계', '생태학', '생태 쫌', '환경과 생태', '생태터널', '생태공원', '생태하천', '생태환경', '생태관', '생태체험', '생태교육', '생태복원', '생태보전',
           '생태탐방', '생태숲', '생태원', '생태통로', '생태관광', '조기 마감', '조기마감', '조기 품절', '조기품절', '조기 종료', '조기종료', '조기 소진', '조기소진', '열기']
REGION_LABEL = {'전국': '전국', '제주': '제주', '추자': '추자도', '울릉': '울릉·독도', '강원': '강원', '경북': '경북', '경남': '경남',
                '부산': '부산', '울산': '울산', '전남': '전남', '무안영광': '무안·영광', '여수삼산': '여수 삼산면',
                '백령대청': '백령·대청', '인천': '인천', '포항지정': '포항 지정해역'}
REGION_DETECT = [
    ('추자', r'추자'), ('제주', r'제주|서귀포|성산포|한림|모슬포|우도'), ('울릉', r'울릉|독도'),
    ('강원', r'강원|속초|강릉|삼척|양양|주문진|묵호|거진'), ('경북', r'경북|경상북도|포항|영덕|울진|경주|구룡포|감포|후포|강구'),
    ('경남', r'경남|경상남도|통영|거제|남해|사천|마산|창원|삼천포'), ('부산', r'부산|기장|자갈치'), ('울산', r'울산|방어진'),
    ('무안영광', r'무안|영광'), ('여수삼산', r'삼산면|거문도'),
    ('전남', r'전남|전라남도|여수|완도|목포|신안|진도|고흥|해남|흑산|벌교'), ('백령대청', r'백령|대청도'), ('인천', r'인천|연평|소래'),
]
RE_IMPORT = re.compile(r'수입|러시아|노르웨이|중국산|베트남|칠레|아르헨티나|미국산|캐나다|페루|일본산|원양|모리타니|세네갈|인도네시아|태국산|아이슬란드|알래스카|뉴질랜드|호주산')
RE_DOMESTIC = re.compile(r'국산|국내산|연근해|동해안|동해산|서해산|남해산|우리\s*바다')
RE_FARM = re.compile(r'양식')
RE_WILD = re.compile(r'자연산|해녀|물질|낚시|선상|직접\s*(?:잡|채취)|조업|갓\s*잡|잡은|잡아')
RE_FRESH = re.compile(r'활어|활[전대꽃문낙해소홍광우]|\(활\)|산지\s*직송|당일|오늘|금일|갓\s*잡|방금|조업|생물|선어|위판|산낙지|살아\s*있|채취')
RE_FROZEN = re.compile(r'냉동|급냉|동결|작년|지난해|지난\s*시즌|비축|재고|반건조|건조|말린|젓갈|염장|훈제|통조림|금어기\s*(?:전|이전|직전)')
RE_JUV = re.compile(r'새끼|치어|어린|꼬마|미니|아기|잔챙이')
SEV = {'ok': 0, 'info': 1, 'warn': 2, 'danger': 3}
SEV_LABEL = {'danger': '위반 의심', 'warn': '확인 필요', 'info': '참고', 'ok': '기준 내'}
SPECIAL_MEASURE = ['항문장', '두흉갑장', '체반폭', '외투장']

ALIAS: list[tuple[str, str, bool]] = []
for _r in RULES:
    for _a in _r.get('al', []):
        ALIAS.append((_a, _r['id'], False))
    for _a in _r.get('weak', []):
        ALIAS.append((_a, _r['id'], True))
    for _a in _r.get('female', []):
        if _a not in _r['al']:
            ALIAS.append((_a, _r['id'], False))
ALIAS.sort(key=lambda x: -len(x[0]))


def _mask(text: str) -> str:
    w = text
    for ex in EXCLUDE:
        w = w.replace(ex, '□' * len(ex))
    return w


# 어종 이름 바로 뒤에 붙으면 별명·상호로 보고 어종으로 세지 않는다 (예: 고도리맘, 풀치아빠, 대게수산, 광어횟집)
NICK_SUFFIX = re.compile(r'(?:맘|대디|아빠|엄마|님|네(?![가-힣])|공주|왕자|짱|러버|매니아|마니아|티비|TV|tv|닷컴|마켓|상회|수산|스토어|샵|몰|'
                         r'하우스|컴퍼니|상사|유통|가게|식당|횟집|회관|회센터|포차|이네|씨네|패밀리|월드|랜드|피싱|낚시|'
                         r'슈즈|김밥|카페|공방|스튜디오|북스|미디어|게임|퍼즐|빵|나(?![가-힣])|아노|\d+(?!\s*(?:kg|키로|킬로|마리|미|g|cm|개|팩|박스|상자|짝|인분|%)))')


def _find_hits(w: str) -> list[dict]:
    hits, i = [], 0
    while i < len(w):
        found = next((A for A in ALIAS if w.startswith(A[0], i)), None)
        if found and NICK_SUFFIX.match(w, i + len(found[0])):
            i += len(found[0])  # 별명·상호의 일부
            continue
        if found:
            same = [A for A in ALIAS if A[0] == found[0]]
            hits.append({'start': i, 'end': i + len(found[0]), 'text': found[0],
                         'rules': [{'id': s[1], 'weak': s[2]} for s in same]})
            i += len(found[0])
        else:
            i += 1
    return hits


def _to_g(v: float, u: str) -> float:
    return v * 1000 if re.search(r'k|키로|킬로', u) else v


def _fmt_num(v: float):
    return int(v) if float(v).is_integer() else round(v, 1)


def find_measures(t: str) -> list[dict]:
    out = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:cm|㎝|센치|센티)?\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(cm|CM|Cm|㎝|센티미터|센티|센치|mm|㎜)', t):
        a = float(m.group(1)); b = float(m.group(2)) if m.group(2) else a
        if re.search(r'mm|㎜', m.group(3)):
            a, b = a / 10, b / 10
        out.append({'kind': 'cm', 'start': m.start(), 'end': m.end(), 'raw': m.group(0), 'val': min(a, b), 'hi': max(a, b)})
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(kg|㎏|키로|킬로|g|그램)\s*(?:에|당)?\s*(\d+)\s*(?:미|마리)(?![가-힣])', t):
        cnt = float(m.group(3))
        if cnt == 0:
            continue
        g = round(_to_g(float(m.group(1)), m.group(2)) / cnt)
        out.append({'kind': 'g', 'start': m.start(), 'end': m.end(), 'raw': m.group(0), 'val': g, 'hi': g, 'derived': True})
    for pat in (r'(?:마리당|미당|개당|한\s*마리|1\s*마리)\s*(?:약|평균)?\s*(\d+(?:\.\d+)?)\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(kg|㎏|키로|킬로|g|그램)',
                r'(\d+(?:\.\d+)?)\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(kg|㎏|키로|킬로|g|그램)\s*(?:내외|정도|급)?\s*짜리'):
        for m in re.finditer(pat, t):
            a = _to_g(float(m.group(1)), m.group(3)); b = _to_g(float(m.group(2)), m.group(3)) if m.group(2) else a
            out.append({'kind': 'g', 'start': m.start(), 'end': m.end(), 'raw': m.group(0), 'val': min(a, b), 'hi': max(a, b)})
    out.sort(key=lambda x: x['start'])
    return [x for i, x in enumerate(out) if not any(j < i and y['end'] > x['start'] and y['kind'] == x['kind'] for j, y in enumerate(out))]


def detect_regions(t: str) -> list[str]:
    s = [k for k, p in REGION_DETECT if re.search(p, t)]
    if '추자' in s and '제주' not in s:
        s.append('제주')
    return s


def _in_range(d: str, f: str, t: str) -> bool:
    return (f <= d <= t) if f <= t else (d >= f or d <= t)


def _fmt_md(s: str) -> str:
    m, d = s.split('-')
    return f'{int(m)}.{int(d)}'


def _days_until(day: date, f: str) -> int:
    m, d = map(int, f.split('-'))
    s = date(day.year, m, d)
    if s < day:
        s = date(day.year + 1, m, d)
    return (s - day).days


def pick_season(rule: dict, regions: list[str]) -> dict:
    E = rule.get('season') or []
    if not E:
        return {'mode': 'none', 'entries': []}
    specific = [e for e in E if e.get('r') and any(x in regions for x in e['r'])]
    if specific:
        return {'mode': 'regional', 'entries': [specific[0]]}
    defs = [e for e in E if not e.get('r')]
    if defs:
        ok = [e for e in defs if not (e.get('ex') and any(x in regions for x in e['ex']))]
        if not ok:
            return {'mode': 'excluded', 'entries': [], 'ex': defs[0]['ex']}
        return {'mode': 'default', 'entries': ok}
    if not regions or '전국' in regions:
        return {'mode': 'unknownRegional', 'entries': E}
    return {'mode': 'na', 'entries': []}


def pick_size(rule: dict, regions: list[str]):
    s = rule.get('size')
    if not s:
        return None
    lim, scope, unknown = s['lim'], '전국', False
    if s.get('only'):
        if any(x in s['only'] for x in regions):
            scope = '·'.join(REGION_LABEL[x] for x in s['only'] if x in regions)
        elif not regions or '전국' in regions:
            unknown = True
            scope = '·'.join(REGION_LABEL[x] for x in s['only']) + ' 한정'
        else:
            return {**s, 'na': True}
    for b in s.get('by', []):
        if any(x in regions for x in b['r']):
            lim = b['lim']
            scope = '·'.join(REGION_LABEL[x] for x in b['r'] if x in regions)
            break
    return {**s, 'lim': lim, 'scope': scope, 'unknown': unknown}


def season_text(e: dict) -> str:
    t = f"{_fmt_md(e['f'])}~{_fmt_md(e['t'])}"
    if e.get('r'):
        t += f" ({'·'.join(REGION_LABEL[x] for x in e['r'])})"
    if e.get('ex'):
        t += f" ({'·'.join(REGION_LABEL[x] for x in e['ex'])} 제외)"
    return t


def _max_sev(sevs) -> str:
    out = 'ok'
    for s in sevs:
        if SEV[s] > SEV[out]:
            out = s
    return out


def analyze(text: str, post_date: date, region_override: str | None = None) -> dict:
    """한 판매글을 판독한다. 반환값의 sev 는 ok/info/warn/danger 중 하나."""
    w = _mask(text)
    hits = _find_hits(w)
    meas = find_measures(text)
    line_of = lambda p: text.count('\n', 0, p)
    for h in hits:
        h['line'] = line_of(h['start'])
    distinct = {r['id'] for h in hits for r in h['rules']}
    for m in meas:
        m['line'] = line_of(m['start'])
        same = [h for h in hits if h['line'] == m['line']]
        prev = sorted([h for h in same if h['end'] <= m['start']], key=lambda h: -h['end'])
        target = prev[0] if prev else None
        if not target:
            nxt = sorted([h for h in same if h['start'] >= m['end'] and h['start'] - m['end'] <= 15], key=lambda h: h['start'])
            target = nxt[0] if nxt else None
        if not target:
            p2 = sorted([h for h in hits if h['end'] <= m['start']], key=lambda h: -h['end'])
            if p2 and m['start'] - p2[0]['end'] < 40:
                target = p2[0]
        if not target and len(distinct) == 1:
            target = hits[0]
        m['hit'] = target

    regions = [region_override] if region_override else detect_regions(text)
    ctx = {k: bool(r.search(text)) for k, r in
           {'imp': RE_IMPORT, 'dom': RE_DOMESTIC, 'farm': RE_FARM, 'wild': RE_WILD, 'fresh': RE_FRESH, 'frozen': RE_FROZEN}.items()}
    d = post_date.strftime('%m-%d')
    lines = text.split('\n')

    by_rule: dict[str, dict] = {}
    for h in hits:
        for r in h['rules']:
            g = by_rule.setdefault(r['id'], {'hits': [], 'weakOnly': True})
            g['hits'].append(h)
            if not r['weak']:
                g['weakOnly'] = False

    findings = []
    for rid, g in by_rule.items():
        rule = RULE[rid]
        items: list[dict] = []
        add = lambda sev, txt: items.append({'sev': sev, 'txt': txt})
        aliases = list(dict.fromkeys(h['text'] for h in g['hits']))
        ms = [m for m in meas if m['hit'] is not None and any(m['hit'] is h for h in g['hits'])]
        my_lines = '\n'.join(lines[i] for i in sorted({h['line'] for h in g['hits']}))
        l_imp, l_farm = bool(RE_IMPORT.search(my_lines)), bool(RE_FARM.search(my_lines))
        not_caught = 'imp' if l_imp else ('farm' if (l_farm and rule.get('farm')) else None)

        def cap(sev):
            s = sev
            if g['weakOnly'] and SEV[s] > SEV['warn']:
                s = 'warn'
            if not_caught and SEV[s] > SEV['info']:
                s = 'info'
            if rule.get('importDefault') and not ctx['dom'] and SEV[s] > SEV['info']:
                s = 'info'
            if rule.get('farm') and not ctx['wild'] and not l_farm and SEV[s] > SEV['warn']:
                s = 'warn'
            return s

        gauge = None
        if rule.get('yearRound'):
            domestic_hint = ctx['dom'] or bool(re.search(r'강원|고성|속초|주문진|동해', text))
            if l_imp and not domestic_hint:
                add('info', '수입산(러시아 등) 표기가 있어 국내 포획 금지 대상이 아닐 가능성이 큽니다.')
            elif domestic_hint:
                add('danger', '국내산 명태로 보이는 표현이 있습니다. 국내 해역 명태는 1.1~12.31 연중 포획 금지입니다.')
            else:
                add('warn', '명태는 국내 해역에서 연중 포획 금지입니다. 원산지(수입산 여부)를 확인하세요.')

        juv_hit = next((a for a in aliases if a in rule.get('juv', [])), None)
        if juv_hit and not rule.get('yearRound'):
            add(cap('warn' if rid == 'bangeo' else 'danger'), f'"{juv_hit}"는 금지체장 미만 어린 {rule["n"]}를 부르는 말입니다.')
        elif rule.get('size'):
            if any(RE_JUV.search(text[max(0, h['start'] - 6):h['start']]) for h in g['hits']):
                add(cap('warn'), f'어린 개체를 뜻하는 표현(새끼·치어·미니 등)이 {rule["n"]} 앞에 붙어 있습니다.')

        fem = next((f for f in rule.get('female', []) if f in text), None)
        if fem:
            add(cap('danger'), f'"{fem}" 표기: 대게 암컷은 크기·시기와 관계없이 연중 포획 금지입니다.')

        sz = pick_size(rule, regions)
        if sz and not sz.get('na'):
            unit = 'g' if sz['u'] == 'g' else 'cm'
            rel = [m for m in ms if m['kind'] == unit]
            if rel:
                mn = min(rel, key=lambda m: m['val'])
                under = mn['val'] <= sz['lim']
                gauge = {'val': mn['val'], 'hi': mn['hi'], 'lim': sz['lim'], 'unit': unit, 'under': under}
                scope = f", {sz['scope']}" if sz['scope'] != '전국' else ''
                if under:
                    s = cap('danger')
                    if sz['unknown'] and SEV[s] > SEV['warn']:
                        s = 'warn'
                    add(s, f"표기 크기 {mn['raw'].strip()} → 기준({sz['m']} {_fmt_num(sz['lim'])}{unit} 이하 포획 금지{scope})에 걸립니다."
                           + (' (총중량÷마릿수로 계산한 마리당 무게)' if mn.get('derived') else ''))
                    if sz.get('pct'):
                        add('info', '단, 어획량 중 해당 크기가 20% 미만인 경우는 예외로 규정되어 있습니다(어업 현장 기준).')
                    if sz['m'] in SPECIAL_MEASURE:
                        add('info', f"법정 계측 기준은 {sz['m']}입니다. 판매글 수치가 전장(전체 길이)이면 실제 {sz['m']}은 더 짧습니다.")
                else:
                    add('ok', f"표기 크기 {mn['raw'].strip()}는 기준({sz['m']} {_fmt_num(sz['lim'])}{unit} 이하 금지)보다 큽니다.")
                    if sz['m'] in SPECIAL_MEASURE:
                        add('info', f"법정 기준은 {sz['m']}입니다. 표기 수치가 전체 길이라면 {sz['m']} 기준으로는 미달일 수 있습니다.")
                if rule.get('sizeSusp'):
                    add('info', rule['sizeSusp'] + ' (TAC 참여 어선 한정).')
            elif not juv_hit:
                scope = f" ({sz['scope']})" if sz['scope'] != '전국' else ''
                add('info', f"크기 표기가 없습니다. 기준: {sz['m']} {_fmt_num(sz['lim'])}{unit} 이하 포획 금지{scope}.")
        elif sz and sz.get('na'):
            add('ok', f"금지체장은 {'·'.join(REGION_LABEL[x] for x in sz['only'])}산에만 적용되어 이 지역과는 무관합니다.")

        ps = pick_season(rule, regions)
        if ps['mode'] == 'excluded':
            add('ok', f"{'·'.join(REGION_LABEL[x] for x in ps['ex'])}는 금어기 적용에서 제외됩니다.")
        in_season = next((e for e in ps['entries'] if _in_range(d, e['f'], e['t'])), None)
        if in_season:
            s = 'danger' if ctx['fresh'] else ('info' if ctx['frozen'] else 'warn')
            if (in_season.get('notice') or ps['mode'] == 'unknownRegional' or rule.get('seasonSusp')) and SEV[s] > SEV['warn']:
                s = 'warn'
            s = cap(s)
            why = ('당일·활어·산지직송 등 최근 어획을 뜻하는 표현이 있습니다.' if ctx['fresh'] else
                   '냉동·건조 등 표현이 있어 금어기 이전 어획분일 수 있습니다(어획일 증빙 확인).' if ctx['frozen'] else
                   '어획 시점이 글에 드러나지 않습니다.')
            lab = f", {in_season['lab']}" if in_season.get('lab') else ''
            add(s, f"게시일 {_fmt_md(d)}은 금어기({season_text(in_season)}{lab}) 기간입니다. {why}")
            if in_season.get('notice'):
                add('info', f"기간은 {in_season['notice']}.")
            if ps['mode'] == 'unknownRegional':
                add('info', '이 금어기는 특정 지역에만 적용됩니다. 어획 지역을 지정하면 더 정확해집니다.')
            if rule.get('seasonSusp'):
                add('info', rule['seasonSusp'] + '.')
        elif ps['entries']:
            left = _days_until(post_date, ps['entries'][0]['f'])
            if left <= 14:
                add('info', f"{left}일 뒤 금어기({season_text(ps['entries'][0])}) 시작.")
            else:
                add('ok', f"게시일은 금어기({', '.join(season_text(e) for e in ps['entries'])}) 밖입니다.")

        if not_caught == 'imp':
            add('info', '수입산 표현이 있습니다. 금어기·금지체장은 국내 해역 포획물에 적용됩니다.')
        if not_caught == 'farm':
            add('info', '양식산 표현이 있습니다. 양식 수산물은 포획 규제 대상이 아닙니다.')
        if rule.get('farm') and not ctx['wild'] and not l_farm and any(i['sev'] == 'warn' for i in items):
            add('info', f"{rule['n']}은 양식품이 많이 유통됩니다. 자연산 여부를 확인하세요.")
        if g['weakOnly']:
            add('info', f'"{", ".join(aliases)}"만으로는 정확한 종을 알 수 없어 {rule["n"]} 기준을 가정했습니다.')
        if rule.get('note') and not juv_hit:
            add('info', rule['note'] + '.')
        if not items:
            add('ok', '적용되는 금어기·금지체장 문제를 찾지 못했습니다.')
        findings.append({'id': rid, 'name': rule['n'], 'law': rule['law'], 'aliases': aliases, 'items': items,
                         'sev': _max_sev(i['sev'] for i in items), 'gauge': gauge,
                         'first': min(h['start'] for h in g['hits'])})

    findings.sort(key=lambda f: (-SEV[f['sev']], f['first']))
    return {'text': text, 'findings': findings, 'regions': regions, 'ctx': ctx,
            'sev': _max_sev(f['sev'] for f in findings)}


def in_season_rules(day: date) -> list[dict]:
    """해당 날짜에 전국 기본 기준으로 금어기인 어종(연중 금지 포함)."""
    d = day.strftime('%m-%d')
    out = []
    for r in RULES:
        if r.get('yearRound'):
            out.append(r)
            continue
        ps = pick_season(r, [])
        if any(_in_range(d, e['f'], e['t']) for e in ps['entries']):
            out.append(r)
    return out
