"""네이버 검색 API로 판매글 후보를 모은다.

- 네이버 카페·블로그: 카페글/블로그 검색 API
- 스마트스토어·당근·쿠팡·11번가·G마켓·옥션: 웹문서 검색 API에 노출된 문서만 사용
  (해당 사이트에는 직접 접속하지 않는다)
"""
from __future__ import annotations

import html
import http.client
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

HUB_BASE = "https://naverapihub.apigw.ntruss.com/search/v1/{kind}"
LEGACY_BASE = "https://openapi.naver.com/v1/search/{kind}.json"  # 2027-06-30까지 기존 키 사용자만

# 웹문서 검색으로 찾는 판매 사이트 (Android 앱 engine.js의 DEFAULT_SITES와 같음).
# config.toml 의 [collect] sites 로 바꿀 수 있다. overseas=True 이면 판정을 '확인 필요'까지만 올린다.
# trade=True 는 쇼핑몰·중고거래처럼 글 자체가 판매 글인 사이트(판매 표현이 없어도 판매글로 본다).
DEFAULT_SITES = [
    {"name": "네이버 쇼핑", "domains": ["smartstore.naver.com", "shopping.naver.com", "brand.naver.com"], "query": "스마트스토어", "trade": True},
    {"name": "당근", "domains": ["daangn.com"], "query": "당근", "trade": True},
    {"name": "번개장터", "domains": ["bunjang.co.kr"], "query": "번개장터", "trade": True},
    {"name": "쿠팡", "domains": ["coupang.com"], "query": "쿠팡", "trade": True},
    {"name": "11번가", "domains": ["11st.co.kr"], "query": "11번가", "trade": True},
    {"name": "G마켓", "domains": ["gmarket.co.kr"], "query": "G마켓", "trade": True},
    {"name": "옥션", "domains": ["auction.co.kr"], "query": "옥션", "trade": True},
    {"name": "롯데ON", "domains": ["lotteon.com"], "query": "롯데온", "trade": True},
    {"name": "SSG닷컴", "domains": ["ssg.com"], "query": "SSG", "trade": True},
    {"name": "카카오 쇼핑", "domains": ["store.kakao.com", "shoppinghow.kakao.com"], "query": "톡딜", "trade": True},
    {"name": "다음 카페", "domains": ["cafe.daum.net"], "query": "다음카페"},
    {"name": "네이버 밴드", "domains": ["band.us"], "query": "밴드"},
    {"name": "테무", "domains": ["temu.com"], "query": "테무", "overseas": True, "trade": True},
    {"name": "알리익스프레스", "domains": ["aliexpress.com"], "query": "알리익스프레스", "overseas": True, "trade": True},
]
API_SITES = [{"name": "네이버 카페", "domains": ["cafe.naver.com"]}, {"name": "네이버 블로그", "domains": ["blog.naver.com"]}]


def active_sites(ccfg: dict) -> list[dict]:
    sites = ccfg.get("sites") or DEFAULT_SITES
    return [s for s in sites if s.get("enabled", True)]


def site_query_words(sites: list[dict]) -> list[str]:
    words: list[str] = []
    for s in sites:
        for w in str(s.get("query") or s["name"]).split(","):
            w = w.strip()
            if w and w not in words:
                words.append(w)
    return words


# 판매·거래·경매 글만 남긴다. 카페·블로그 등은 아래 표현이 있어야 하고, 쇼핑몰(trade) 글은 그 자체로 판매글.
# 판매·거래·경매 글만 남긴다.
# 쇼핑몰·중고거래 사이트(trade) 글은 그 자체로 판매글. 카페·블로그 등은 글쓴이가 직접 파는·거래하는·경매하는 글이어야 한다:
#   ① 제목에 판매·거래·경매 표현이 있거나
#   ② 요약문에 판매·거래·경매 표현이 있고 가격·수량(원, kg, 마리, 미)도 있을 때.
# 가격만 적힌 후기·정보 글(예: "푸딩 5,500원 내돈내산")은 판매글로 보지 않는다.
TRADE_WORDS = re.compile(
    r"판매|팝니다|팔아요|팔아용|팔게요|팔께요|처분|직판|도매|산지\s*직송|직송|공동\s*구매|공구|특가|"
    r"주문\s*(?:가능|받|접수|하세요|주세요)|입금|택배\s*(?:가능|발송|보내)|"
    r"직거래|거래\s*(?:합니다|원해|원합니다|가능|희망|해요)|"
    r"경매|위판|입찰|낙찰|경락|공판장|"
    r"\[\s*(?:판매|팝니다|거래|직거래|경매)\s*\]")
# '오늘 잡은·당일 잡은·갓 잡은·오늘 조업·당일바리' 처럼 갓 잡은 것을 내놓는 표현
CATCH_FRESH = re.compile(
    r"(?:오늘|당일|금일|방금|갓|막|새벽(?:에)?|아침(?:에)?|어제|직접)\s*(?:잡은|잡아\s*온|잡아온|잡았|건진|채취한|조업한|"
    r"들어온|입고된|올라온|따온)|(?:오늘|당일|금일)\s*(?:조업|입고|입항|위판|경매|바리|물량)|당일\s*바리|당일\s*발송|"
    r"선도\s*(?:최상|좋)|살아\s*있(?:는|어요|습니다)|활\s*(?:상태|어)\s*(?:좋|최상)")
# 사 갈 사람을 찾는 표현
CONTACT = re.compile(r"필요하신\s*분|원하시는\s*분|가져가실\s*분|드실\s*분|구매\s*(?:가능|원하)|연락\s*(?:주세요|주시면|바랍니다|부탁)|"
                     r"문의\s*(?:주세요|주시면|바랍니다|환영)|쪽지\s*(?:주세요|주시면)|댓글\s*(?:주세요|남겨)|보내\s*드립니다|"
                     r"보내\s*드려요|물량\s*(?:있|확보|가능|한정)|선착순|예약\s*(?:받|가능)")
PRICE_QTY = re.compile(r"\d[\d,]*\s*원|\d+\s*만\s*원|\d+(?:\.\d+)?\s*(?:kg|키로|킬로|마리|미(?![가-힣])|박스|상자|짝)")
# 판매와 무관한 글. 제목에 있으면 판매 표현이 있어도 뺀다.
NOT_TRADE = re.compile(
    r"레시피|요리법|만드는\s*법|만들기|손질법|맛집|먹방|조리법|안주|술상|집밥|"
    r"내돈내산|후기|리뷰|방문기|다녀왔|다녀온|브이로그|일상|디저트|푸딩|카페\s*(?:추천|투어)|"
    r"뉴스|기자|기사|보도|칼럼|소식|단속|적발|압수|검거|입건|해경|해양경찰|"
    r"탄소|기후|배출권|정책|연구|시대|주목|전망|세미나|포럼|교육|해먹|먹었|먹은|맛보|"
    r"금어기\s*(?:안내|시작|해제|돌입|끝)|조황|낚시\s*(?:포인트|후기)|여행|캠핑|축제|"
    # 수협·위판장 시세·현황 기록 (예: "제주 한림수협 11월 6일 (금요일, 3물)")
    r"수협\s*\d{1,2}\s*월|\d{1,2}\s*월\s*\d{1,2}\s*일\s*\(|\(\s*[월화수목금토일]요일|\d+\s*물\s*\)|물때|"
    r"시세\s*(?:정보|표|동향|현황|조회)|(?:위판|경매)\s*(?:현황|시세|결과|정보|동향|가격|일지)|"
    # 후원·봉사·공익 활동 글
    r"굿네이버스|후원|기부|봉사|캠페인|공익|자선|"
    # 수산물과 무관한 공동구매·생활 서비스
    r"방충망|시공|입주|아파트|분양|청소|이사\b|학원|과외|부동산|렌탈|보험|대출|채용|구인|구직|"
    # 자동차·법률 등 다른 주제 (예: "중고차 3자 사기", "필랑트 누아르 에디션 1,000대")
    r"중고차|자동차|신차|에디션|시승|출고|전시장|대리점|딜러|리스\b|타이어|르노|현대차|기아|"
    r"\d자\s*사기|사기\s*(?:피해|사건|당|수법|예방|죄)|소송|변호사|법률|법무|판례|판결|고소|전세|월세|청약")
SALE_INTENT = TRADE_WORDS  # 이전 이름 호환


# ---------- 불법 수산물 점검과 무관한 상품 제외 ----------
# 수산물이 아닌 상품: 장식·부적, 낚시용품, 사료·미끼, 기념품 등 (제목 기준)
NON_SEAFOOD = re.compile(
    r"액막이|소코뚜레|소뚜레|도어벨|부적|고사용|장식|인테리어|오브제|모빌|풍경종|키링|인형|피규어|모형|굿즈|스티커|티셔츠|"
    r"액자|쿠션|장난감|자석|문패|"
    r"낚시대|낚싯대|전용대|선상대|갯바위대|로드\b|채비|루어|에기|지그|웜\b|봉돌|원줄|목줄|바늘|집어등|뜰채|살림망|"
    r"낚시\s*(?:용품|세트|가방|의자|조끼)|구명조끼|"
    r"사료|미끼|떡밥|비료|영양제|캡슐|건강기능|오메가|화장품|비누|"
    r"책\b|도서|교재|어항|수족관|관상어|열대어|"
    # 낚시용품: 장비 용어, 낚싯대 규격(802L, 1002M, S862ML), 낚시 브랜드, '대부분 어종' 같은 장비 문구
    r"인쇼어|오프쇼어|쇼어|라이트\s*게임|에깅|타이라바|지깅|캐스팅|베이트|스피닝|릴\b|합사|카본|라인\b|싱커|스냅|도래|"
    r"구멍찌|전자찌|민장대|태클|미노우|훅\b|"
    r"[A-Za-z]?\d{3,4}\s*-?\s*(?:UL|L|ML|M|MH|H|XH)(?![A-Za-z])|"
    r"씨호크|시마노|다이와|바낙스|엔에스|해동조구|아부가르시아|메이저크래프트|테일워크|제이에스컴퍼니|한조|은성|용성|쯔리겐|"
    r"가마가츠|도요피싱|썬라인|요즈리|듀엘|"
    r"대부분\s*어종|전\s*어종|다\s*어종|어종\s*불문")
# 낚시용품일 때가 많지만 잡은 고기를 파는 글에도 나오는 말: 제목에 '잡은·조과·팝니다·kg·마리' 등이 없을 때만 낚시용품으로 본다
GEAR_WEAK = re.compile(r"[가-힣]{1,3}낚시(?![가-힣])|원투|메탈|스푼|바이브|만능|선상\s*전용")
CATCH_SALE = re.compile(r"잡은|잡아|잡았|조과|팝니다|판매합니다|팔아요|\d\s*(?:kg|키로|마리|미(?![가-힣]))")
# 판매자 홈·상점 첫 화면 (상품 글이 아님)
STORE_HOME_TITLE = re.compile(r"^(?:G마켓|옥션|11번가|쿠팡)\s*[-:|]|미니샵|스토어\s*홈|:\s*네이버\s*(?:스마트)?스토어$|판매자\s*홈")


def is_store_home(link: str, title: str) -> bool:
    u = urllib.parse.urlsplit(link or "")
    host = (u.hostname or "").lower()
    segs = [x for x in u.path.split("/") if x]
    if host.startswith("minishop.") or host.startswith("shop.11st") or "/store/" in u.path:
        return True
    if host.endswith(("smartstore.naver.com", "brand.naver.com")) and len(segs) <= 1:
        return True
    return bool(STORE_HOME_TITLE.search(title or ""))


def many_species(title: str) -> bool:
    """제목에 규제 어종이 5종 이상 나열돼 있으면 낚시용품 등 여러 어종용 상품으로 본다."""
    from analyzer import _find_hits, _mask
    ids = {r["id"] for h in _find_hits(_mask(title or "")) for r in h["rules"]}
    return len(ids) >= 5
# 가공품: 말리거나 절이거나 조리한 것 (제목·요약 기준). 냉동·손질·회는 가공으로 보지 않는다.
PROCESSED = re.compile(
    r"가공|반건조|건조|말린|훈제|젓갈|액젓|[가-힣]+젓(?![가-힣])|염장|절임|장아찌|통조림|어묵|어포|쥐포|북어포|황태포|"
    r"오징어채|진미채|조림|양념|무침|튀김|밀키트|간편식|레토르트|엑기스|분말|가루|"
    r"황태|북어|먹태|코다리|과메기|굴비|노가리\s*(?:구이|안주)")
IMPORTED = re.compile(r"수입|러시아|노르웨이|중국산|베트남|칠레|아르헨티나|미국산|캐나다|페루|일본산|원양|모리타니|세네갈|"
                      r"인도네시아|태국|아이슬란드|알래스카|뉴질랜드|호주산|외국산|해외\s*직구")
DOMESTIC = re.compile(r"국산|국내산|연근해|동해안|동해산|서해산|남해산|제주산|우리\s*바다")
FARMED = re.compile(r"양식")
NOT_FARMED = re.compile(r"자연산|비양식|양식\s*(?:아님|아닌|아니|X|x|no)|무양식")
EXCLUDE_LABEL = {"notitle": "제목에 규제 어종 없음", "nonfood": "수산물이 아닌 상품·판매자 홈", "processed": "가공품",
                 "imported": "수입산", "farmed": "양식"}


def title_has_species(title: str) -> bool:
    """제목에 규제 어종(별명·상호 제외)이 있는지. 판매글이면 파는 수산물 이름이 제목에 있다."""
    from analyzer import _find_hits, _mask
    return bool(_find_hits(_mask(title or "")))
DEFAULT_EXCLUDE = ["nonfood", "processed", "imported", "farmed"]


def exclude_reason(title: str, description: str, overseas: bool = False, exclude=None, link: str = "") -> str | None:
    """점검에서 뺄 글이면 이유(nonfood/processed/imported/farmed), 아니면 None."""
    ex = set(DEFAULT_EXCLUDE if exclude is None else exclude)
    t, d = title or "", description or ""
    text = f"{t}\n{d}"
    if "nonfood" in ex and (NON_SEAFOOD.search(t) or is_store_home(link, t) or many_species(t)
                            or (GEAR_WEAK.search(t) and not CATCH_SALE.search(t))):
        return "nonfood"
    if "processed" in ex and PROCESSED.search(text):
        return "processed"
    if "imported" in ex and (overseas or (IMPORTED.search(text) and not DOMESTIC.search(text))):
        return "imported"
    if "farmed" in ex and FARMED.search(text) and not NOT_FARMED.search(text):
        return "farmed"
    return None


def is_trade(title: str, description: str, trade_site: bool = False) -> bool:
    """판매·거래·경매 글인지."""
    t, d = title or "", description or ""
    if NOT_TRADE.search(t):
        return False
    if trade_site or TRADE_WORDS.search(t) or CATCH_FRESH.search(t) or CONTACT.search(t):
        return True
    sale_d = TRADE_WORDS.search(d) or CATCH_FRESH.search(d) or CONTACT.search(d)
    return bool((sale_d and PRICE_QTY.search(f"{t}\n{d}")) or (CATCH_FRESH.search(d) and CONTACT.search(d)))


TAG = re.compile(r"<[^>]+>")


def clean(s: str) -> str:
    return html.unescape(TAG.sub("", s or "")).strip()


def site_of(link: str, sites: list[dict] | None = None) -> dict | None:
    host = (urllib.parse.urlparse(link).hostname or "").lower()
    host = re.sub(r"^(m|www)\.", "", host)
    for s in API_SITES + (sites if sites is not None else DEFAULT_SITES):
        for d in s["domains"]:
            if host == d or host.endswith("." + d):
                return s
    return None


@dataclass
class Item:
    link: str
    title: str
    description: str
    site: str
    source: str          # cafearticle / blog / webkr
    query: str
    post_date: date | None = None
    extra: dict = field(default_factory=dict)

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.description}"


class AuthError(Exception):
    """키가 틀려 더 진행할 수 없음"""


class NaverSearch:
    """네이버 검색 API 호출.

    헤더 이름을 문서 철자 그대로(X-NCP-APIGW-API-KEY-ID) 보내야 하므로 urllib 대신 http.client를 쓴다.
    urllib는 헤더 이름을 X-Ncp-Apigw-Api-Key-Id 처럼 바꿔 보내 API 게이트웨이가 인증 정보를 못 찾는다
    ("Authentication information are missing").
    """

    def __init__(self, client_id: str, client_secret: str, provider: str = "hub", pause: float = 0.12):
        self.id, self.secret, self.provider, self.pause = client_id.strip(), client_secret.strip(), provider, pause
        self.calls = 0

    def _headers(self) -> dict:
        if self.provider == "legacy":
            return {"X-Naver-Client-Id": self.id, "X-Naver-Client-Secret": self.secret, "Accept": "application/json"}
        return {"X-NCP-APIGW-API-KEY-ID": self.id, "X-NCP-APIGW-API-KEY": self.secret, "Accept": "application/json"}

    def url(self, kind: str, query: str, display: int = 100, start: int = 1, sort: str | None = None) -> str:
        base = (LEGACY_BASE if self.provider == "legacy" else HUB_BASE).format(kind=kind)
        params = {"query": query, "display": display, "start": start}
        if sort:
            params["sort"] = sort
        return base + "?" + urllib.parse.urlencode(params)

    _conn = None
    _conn_host = None

    def get(self, url: str) -> tuple[int, str]:
        """GET 한 번. (상태 코드, 응답 본문). 헤더 이름은 대소문자 그대로 보낸다.
        같은 서버에는 연결을 재사용해 수백 번 호출해도 빠르게 끝나게 한다."""
        u = urllib.parse.urlsplit(url)
        path = u.path + ("?" + u.query if u.query else "")
        key = (u.scheme, u.hostname, u.port)
        for attempt in range(2):
            if self._conn is None or self._conn_host != key:
                self.close()
                self._conn, self._conn_host = self._connect(u), key
            try:
                self._conn.request("GET", path, headers=self._headers())
                r = self._conn.getresponse()
                body = r.read().decode("utf-8", "replace")
                if r.getheader("Connection", "").lower() == "close":
                    self.close()
                return r.status, body
            except (OSError, http.client.HTTPException):
                self.close()  # 끊긴 연결이면 새로 연결해 한 번 더
                if attempt == 1:
                    raise
        raise OSError("요청 실패")

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None

    @staticmethod
    def _connect(u):
        proxy = urllib.request.getproxies().get("https") if u.scheme == "https" else None
        if proxy:
            pu = urllib.parse.urlsplit(proxy if "://" in proxy else "http://" + proxy)
            conn = http.client.HTTPSConnection(pu.hostname, pu.port or 8080, timeout=20, context=ssl.create_default_context())
            conn.set_tunnel(u.hostname, u.port or 443)
        elif u.scheme == "https":
            conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=20, context=ssl.create_default_context())
        else:
            conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=20)
        return conn

    def search(self, kind: str, query: str, display: int = 100, start: int = 1, sort: str | None = None) -> dict:
        url = self.url(kind, query, display, start, sort)
        for attempt in range(3):
            try:
                code, body = self.get(url)
            except (OSError, http.client.HTTPException) as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                raise RuntimeError(f"{kind} '{query}' 네트워크 오류: {e}")
            if code == 200:
                self.calls += 1
                time.sleep(self.pause)
                return json.loads(body)
            if code == 429 and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            if code in (401, 403):
                raise AuthError(f"네이버 API 인증 실패({code}). 설정의 Client ID·Secret과 키 종류를 확인하세요. "
                                f"계정 IAM 키가 아니라 API HUB 앱의 [인증 정보] 값이어야 합니다. 응답: {body[:300]}")
            raise RuntimeError(f"{kind} '{query}' 검색 실패 HTTP {code}: {body[:300]}")
        return {"items": []}

    def sent_info(self) -> str:
        """실제로 보낸 값을 가린 형태로 (콘솔의 값과 비교용)"""
        def mask(v: str) -> str:
            return f"{v[:4]}…{v[-2:]} ({len(v)}자)" if len(v) > 6 else f"{len(v)}자"
        names = ("X-Naver-Client-Id", "X-Naver-Client-Secret") if self.provider == "legacy" else ("X-NCP-APIGW-API-KEY-ID", "X-NCP-APIGW-API-KEY")
        return f"보낸 주소: {self.url('cafearticle', '전복', display=1).split('?')[0]} · {names[0]}: {mask(self.id)} · {names[1]}: {mask(self.secret)}"

    def test(self) -> dict:
        """키 확인: 카페글 검색을 1건만 호출해 결과를 그대로 돌려준다."""
        try:
            r = self._test()
        finally:
            self.close()
        r["sent"] = self.sent_info()
        return r

    def _test(self) -> dict:
        url = self.url("cafearticle", "전복", display=1)
        try:
            code, body = self.get(url)
        except (OSError, http.client.HTTPException) as e:
            return {"ok": False, "status": None, "message": f"네이버 서버에 연결하지 못했습니다: {e}", "body": ""}
        if code == 200:
            try:
                total = json.loads(body).get("total")
            except ValueError:
                total = None
            return {"ok": True, "status": code, "message": f"키가 정상입니다. 카페글 검색 '전복' 결과 {total}건.", "body": body[:300]}
        hint = {
            401: "Client ID·Secret 값이 틀렸거나, Application에 이 검색 API를 체크하지 않았습니다.",
            403: "이 API를 쓸 권한이 없습니다. Application의 API 선택에 카페글·블로그·웹문서 검색이 있는지 확인하세요.",
            404: "요청 주소가 맞지 않습니다. 키 종류(API HUB / 기존 개발자센터)가 맞는지 확인하세요.",
            429: "호출 한도를 넘었습니다. 잠시 후 다시 시도하세요.",
        }.get(code, "")
        return {"ok": False, "status": code, "message": f"실패(HTTP {code}). {hint}".strip(), "body": body[:300]}


class MockSearch:
    """--mock 실행용. sample_api/ 의 JSON을 검색 결과처럼 돌려준다."""
    def __init__(self, folder: Path):
        self.data = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in folder.glob("*.json")}
        self.calls = 0

    def search(self, kind, query, display=100, start=1, sort=None):
        self.calls += 1
        items = [it for it in self.data.get(kind, {}).get("items", []) if any(w in clean(it["title"] + it["description"]) for w in query.split())]
        return {"items": items}


def parse_postdate(s: str | None) -> date | None:
    if s and re.fullmatch(r"\d{8}", s):
        try:
            return datetime.strptime(s, "%Y%m%d").date()
        except ValueError:
            return None
    return None


def collect(api, queries: list[str], sources: list[str], site_queries: list[str], max_calls: int, log=print,
            sites: list[dict] | None = None, stats: dict | None = None, progress=None, exclude=None,
            title_species: bool = True) -> list[Item]:
    """검색을 돌려 사이트 대상 글만 걸러 Item 목록을 돌려준다.
    stats 에 성공(ok)·실패(failed) 건수, 첫 오류(first_error), 응답 항목 수(items)를 채운다."""
    stats = stats if stats is not None else {}
    stats.update(ok=0, failed=0, first_error=None, items=0, in_site=0, not_sale=0, total=0,
                 excluded={k: 0 for k in EXCLUDE_LABEL})
    seen: dict[str, Item] = {}
    plan: list[tuple[str, str]] = []
    for q in queries:
        for src in sources:
            if src in ("cafearticle", "blog"):
                plan.append((src, q))
    if "webkr" in sources:
        for q in site_queries:
            plan.append(("webkr", q))
    if len(plan) > max_calls:
        log(f"  검색 {len(plan)}건 중 상한 {max_calls}건만 실행합니다(config의 max_calls).")
        plan = plan[:max_calls]
    stats["total"] = len(plan)
    dropped: set[str] = set()  # 걸러낸 글은 다른 검색어로 또 나와도 한 번만 센다
    for i, (src, q) in enumerate(plan, 1):
        if progress:
            progress(i - 1, len(plan), len(seen))
        try:
            res = api.search(src, q, display=100, sort="date" if src != "webkr" else None)
        except RuntimeError as e:
            stats["failed"] += 1
            stats["first_error"] = stats["first_error"] or str(e)
            log(f"  ! {e}")
            continue
        stats["ok"] += 1
        stats["items"] += len(res.get("items", []))
        for it in res.get("items", []):
            link = it.get("link", "")
            hit = site_of(link, sites)
            site = hit["name"] if hit else {"cafearticle": "네이버 카페", "blog": "네이버 블로그"}.get(src)
            if not site or link in seen or link in dropped:
                continue
            stats["in_site"] += 1
            item = Item(link=link, title=clean(it.get("title")), description=clean(it.get("description")), site=site,
                        source=src, query=q, post_date=parse_postdate(it.get("postdate")),
                        extra={**{k: it[k] for k in ("cafename", "bloggername") if k in it},
                               **({"overseas": True} if hit and hit.get("overseas") else {})})
            if not is_trade(item.title, item.description, bool(hit and hit.get("trade"))):
                stats["not_sale"] += 1
                dropped.add(link)
                continue  # 요리·정보 글 등 판매와 무관한 글 제외
            why = ("notitle" if title_species and not title_has_species(item.title)
                   else exclude_reason(item.title, item.description, bool(hit and hit.get("overseas")), exclude, link))
            if why:
                stats["excluded"][why] += 1
                dropped.add(link)
                continue  # 수산물 아님·가공·수입·양식
            seen[link] = item
        if i % 20 == 0:
            log(f"  검색 {i}/{len(plan)} 완료, 후보 {len(seen)}건")
    if progress:
        progress(len(plan), len(plan), len(seen))
    if hasattr(api, "close"):
        api.close()
    return list(seen.values())
