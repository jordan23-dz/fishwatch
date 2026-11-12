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
    r"차이점|가이드|활용\s*팁|총정리|알아보|정리했|효능|칼로리|영양|백과|사전|수산학|"
    r"KBS|MBC|SBS|JTBC|tvN|생생정보|방송|메뉴|아르바이트|알바|모집|모임|찾아요|주인\s*찾|분실|실종|"
    r"탐방|전시|박람회|엑스포|엑스코|"
    # 사는 곳을 묻는 질문, 당근 동네생활 글("… | ○○동")
    r"아시는\s*분|아실까요|아는\s*분|어디서|어디\s*(?:있|가|서)|파는\s*곳|판매하는\s*곳|살\s*수\s*있는|먹을\s*수\s*있는|먹을수있는|살수있는|"
    r"추천\s*(?:해|좀|부탁)|질문|궁금|\|\s*[가-힣0-9]+(?:동|읍|면|리|가)\s*$|"
    # 시세 정리·방문 안내 글
    r"뜻\s*[:은]|선택\s*방법|올바른\s*선택|먹는\s*법|받은\s*상품|받았는데|이건\s*사야|사야\s*돼|소소한\s*한잔|의\s*진수|보는\s*법|가격\s*20\d\d|첫\s*위판|솔직한|싶었던|"
    r"시세\s*(?:·|정리|체크|비교|확인)|기준\s*정리|가기\s*전에|비용\s*체크|"
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
    r"대부분\s*어종|전\s*어종|다\s*어종|어종\s*불문|"
    # 낚시 소품: 쇼크리더·와이어·케미·배터리·웜 등과 미끼·채비 브랜드
    r"쇼크리더|와이어|케미|캐미|밧데리|배터리|건전지|다운샷|티탄|낚시줄|낚싯줄|\d+(?:\.\d+)?\s*파이|\d+\s*인치|\d+\s*mm\b|"
    r"[가-힣]{1,4}(?:용품|채비)\s*판매|(?:광어|우럭|갈치|풀치|쭈꾸미|주꾸미|문어)\s*(?:우럭|광어)?\s*용(?![가-힣])|[가-힣]{1,3}전용(?![가-힣])|"
    r"슈어캐치|워터맨|버클리|엘리게이터|비글|조구|샌드사딘|얼라이브|"
    # 화투·놀이·문화 상품 ('고도리'는 화투 용어로도 쓰임)
    r"화투|고스톱|맞고|오광|홍단|청단|피박|퍼즐|보드게임|게임|소설|장편|만화|웹툰|굿즈|"
    # 반려동물 간식·용품
    r"강아지|고양이|반려견|반려묘|반려동물|애견|애묘|펫(?=[가-힣\s])|트릿|"
    # 주방·생활용품
    r"찜기|찜솥|냄비|무시깡|모카포트|커피메이커|알레시|Alessi|가위|집게|도마|"
    # 수집품·전자 장난감
    r"우표|수집품|기념주화|엽서|RC|rc카|알씨|송수신기|드론|"
    # 신발·옷
    r"운동화|스니커즈|방한화|부츠|슬리퍼|신발|의류|티셔츠|후드|모자|"
    # '뺀찌'는 공구(펜치)로도 쓰임
    r"펜치|뺀치|뻰지|뺀지|밴찌|니빠|니뻐|니퍼|플라이어|공구|롱노즈|롱노우즈|압착|컷팅|절단기|스패너|몽키|망치|로보스터|로보스타|LOBSTER|고바야시|타바타|"
    r"(?:공업|전기|작업|다용도|전공|강력)\s*뺀찌|뺀찌\s*(?:깡|공구|세트)|"
    # '톳'은 김을 세는 단위(1톳=100장)로도 쓰임
    r"[가-힣]*김(?=\s|$|\d|\()|김밥|\d+\s*톳|톳\s*\(?\s*\d+\s*(?:장|매|g)|"
    # '천초'는 향신료(초피), '깔따구'는 벌레로도 쓰임
    r"초피|제피|젠피|산초|약초|열매|유충|샤워기|세면대|수전|필터|정수|모기|해충|벌레|방충|하루살이|단열\s*필름|"
    # 화장품·장신구·공예, 노래·음원, 음료·빨대, 상품권, 술
    r"클렌징|폼\b|화장|세안|목걸이|귀걸이|팔찌|반지|액세서리|공예|껍질|골동품|노래(?!미)|메들리|음원|앨범|USB|음향|"
    r"채칼|채반|채망|틀\b|젤리|스트로우|빨대|슬러시|음료|기프티콘|상품권|금액권|\d+\s*만원권|와인|소주|맥주|막걸리|"
    # 사람 구함·동행 모집, 결제창
    r"구합니다|동출|동행|결제창|소통방|단톡|오픈채팅|보러가기|"
    # 바로 먹는 조리 식품
    r"덮밥|냉면|라면|컵면|미역국|국물용|한상(?!자)|크랩\s*스톡|풀치대|갈치대|낚싯대|크래미|맛살|게살|대게살|붉은대게살|파지|"
    # 포장 용기·선물 이벤트·귀금속·교육기관
    r"용기(?![가-힣])|포장재|아이스팩|용돈|이벤트\s*박스|실버바|골드바|인증\d+|어린이집|유치원|학급|학원|"
    # 과자·사탕, 벌레 퇴치, 앞치마, 축하 화분
    r"캬라멜|카라멜|캔디|사탕|누룽지|칩(?![가-힣])|과자|트랩|퇴치|날파리|초파리|거세|앞치마|비닐가운|승진\s*축하|개업\s*(?:식|축하)|화분|유정란|펜션|페스룸|날자!?\s*고도리|"
    # 반려동물 사료·간식
    r"독(?![가-힣])|DOG|[Dd]og|도그|캣|[Cc]at(?![a-z])|고양이|강아지|반려|애견|애묘|키블|어덜트|인도어|퍼피|키튼|져키|저키|육포|"
    r"껌(?![가-힣])|츄르|쉬바|ANF|anf|식스프리|뉴트리나|네츄럴|내추럴\s*발란스|로얄캐닌|트릿|간식|"
    # 화장품·건강식품
    r"앰플|PDRN|pdrn|크림(?![가-힣])|콜라겐|컨실러|스킨|세럼|에센스|로션|토너|마스크팩|글루타치온|부스터|모공|미백|주름|"
    # 조리·가공 간식, 반찬
    r"치즈|부추전|해물전|닭강정|까스|후토마키|초밥(?!\s*(?:필렛|용))|쿠키|[가-힣]*칩(?![가-힣])|스낵|소프트(?![가-힣])|오징어링|링\s*\d|소면|귀채|진미|명엽채|"
    r"낫또|샐러드(?!용)|밥\s*지을|볶음|연어장|식해|순살\s*유아|유아|돌아기|"
    # 생활용품·옷·여행·책·구인
    r"수저|받침|도자기|복대|쁘라이어|우산|양산(?!시)|셔츠|고도리\s*티|반팔티|긴팔티|맨투맨|피라미드|료칸|호텔\s*\d+\s*박|뷔페|투어|우화|그림책|동화|"
    r"[가-힣]?\s*이야기\s*\d*$|주방\s*직원|직원\s*(?:구|모집)|[남여]\s*\d{2}\s*년|천초근|꼭두서니|묵칼|"
    # 낚시 소품(집어제·찌·초릿대), 해외 쇼핑 낚시 검색
    r"집어제|유인제|초릿대|카고|[가-힣]{1,3}돔찌|구멍찌|막대찌|낚시\s*-\s*AliExpress|AliExpress\s*에서|"
    r"애자|진주볼|진주펄|릴대|모든\s*어종|그물망|던질찌|[가-힣]{1,6}(?<!뺀)(?<!빤)찌(?=\s*(?:-|$))|"
    # 생활·공구·기타 (수건, 체험, 해부 교재, 포크, 깔때기, 다큐, 오일·영양제)
    r"Fukin|[가-힣]*칼(?=\s|$)|다용도칼|접도|캇타|나사|볼트|댄스|무한\s*리필|미친\s*자들|체험|다이빙|해부|포크(?![가-힣])|스텐|깔때기|주입기|도구(?:는|가|를|\s*세트)|다큐|오일(?![가-힣])|DNA|케어|[가-힣]*츄(?![가-힣])|미운영|"
    # 단체 대화방 인용글: 고도리 "6월~7월사이 …"
    r"\"[^\"]*…\"?$")
# 낚시용품일 때가 많지만 잡은 고기를 파는 글에도 나오는 말: 제목에 '잡은·조과·팝니다·kg·마리' 등이 없을 때만 낚시용품으로 본다
GEAR_WEAK = re.compile(r"[가-힣]{1,3}낚시(?![가-힣])|원투|메탈|스푼|바이브|만능|선상\s*전용")
CATCH_SALE = re.compile(r"잡은|잡아|잡았|조과|팝니다|판매합니다|팔아요|\d\s*(?:kg|키로|마리|미(?![가-힣]))")
# 판매자 홈·상점 첫 화면 (상품 글이 아님)
STORE_HOME_TITLE = re.compile(
    r"^(?:G마켓|옥션|11번가|쿠팡)\s*[-:|]|미니샵|스토어\s*홈|:\s*네이버\s*(?:스마트)?스토어$|판매자\s*홈|"
    r"님의\s*프로필|의\s*(?:상점|가게|프로필)(?:\s*[-|]|$)|\|\s*당근\s*검색|검색\s*결과|기획전\s*>|카카오톡\s*스토어\s*\S+$|의\s*판매\s*물품|\|\s*수산물/건해산$|"
    # 분류 경로(빵 부스러기): "매생이/톳/해조류 | 김/미역/기타해조류 | 수산물/건해산"
    r"^[^|\d]*/[^|\d]*\|[^|\d]*/[^|\d]*\|")
# 상품 글이 아닌 분류(목록) 페이지: "꽃게/대게/킹크랩", "대게/홍게 - 옥션", "대게 - 새우/게/갑각류"
LISTING_TITLE = re.compile(r"^[가-힣A-Za-z]{1,8}(?:\s*[/ㆍ·,]\s*[가-힣A-Za-z]{1,8})*(?:\s+-\s+[^-|]{1,25})?$")
# 당근 업체 글: "글 제목 | 시·군·구 동네 | 업종"
DAANGN_BIZ = re.compile(r"^([^|]{1,60}?)\s*\|\s*[^|]*[가-힣]+(?:시|도|군|구)\s[^|]*\|\s*[^|]*$")
BIZ_SALE = re.compile(r"\d|[!?~]|예약|입고|왔어|도착|판매|팝니다|팔아|생물|활|국내산|자연산|원가|털|특가|할인|개시|오픈|마감|남았|드세요|"
                      r"챙겨|드실|주문|배송|택배|산지|당일|오늘|싱싱|제철|가격|세일|이벤트")


def daangn_biz(title: str) -> str | None:
    """당근 업체 글이면 'sale'(소식·판매 글) 또는 'home'(가게 이름만 있는 업체 소개)."""
    m = DAANGN_BIZ.match(title or "")
    if not m:
        return None
    return "sale" if BIZ_SALE.search(m.group(1)) else "home"
SEARCH_LINK = re.compile(r"^search\.|^browse\.|/total-search|/search(?:/|\?|$)|/categories/|DisplayCategory|[?&](?:kwd|keyword|searchKeyword|query)=", re.I)
BIZ_SHOP_CATEGORY = re.compile(r"소매|판매|마트|식자재|과일|농|수산|횟|해산|건어물|정육|반찬|기타")
LISTING_SALE = re.compile(r"특가|입고|활|생물|직송|당일|판매|할인|팝니다|팔아요|자연산|국내산|제철|\d")


def bare_listing(title: str) -> bool:
    t = (title or "").strip()
    if not LISTING_TITLE.match(t) or LISTING_SALE.search(t):
        return False
    return "/" in t or "ㆍ" in t or bool(re.search(r"\s-\s", t))
# 쇼핑몰 제목 끝의 " - 분류" 가 수산물 분류가 아니면 수산물 상품이 아니다 (예: "… - 운동화/스니커즈", "… - 직소퍼즐")
CATEGORY_TAIL = re.compile(r"\s[-|]\s([^-|]{2,30})$")
SEAFOOD_CATEGORY = re.compile(r"생선|수산|해산|게|새우|조개|굴|전복|오징어|문어|낙지|주꾸미|쭈꾸미|어란|회|갈치|고등어|명태|동태|"
                              r"해조|미역|톳|다시마|김\b|멸치|농수축산|건어물|장어|연어|참치|광어|우럭|방어|어류|활어|선어|홍합|소라|해삼|성게|멍게")
SITE_NAMES = re.compile(r"^(?:옥션|G마켓|11번가|쿠팡|당근|번개장터|SSG|SSG닷컴|롯데ON|롯데온|다음\s*카페|네이버\s*블로그|네이버\s*카페|"
                        r"네이버\s*쇼핑|스마트\s*스토어|브랜드\s*스토어|위메프|티몬|인터파크|톡딜|카카오|테무|알리익스프레스)")


def non_seafood_category(title: str) -> bool:
    # 업종이 '과일판매·식자재'여도 수산물을 판다고 쓴 글은 남긴다 (업종이 건설·학원 등이면 뺀다)
    cat = title.rsplit("|", 1)[-1]
    if daangn_biz(title) == "sale" and (BIZ_SHOP_CATEGORY.search(cat) or re.search(r"\.\.|…", cat)):
        return False
    m = CATEGORY_TAIL.search(title or "")
    if not m:
        return False
    cat = m.group(1).strip()
    if SITE_NAMES.match(cat) or "모바일" in cat:
        return False
    return not SEAFOOD_CATEGORY.search(cat)


def is_store_home(link: str, title: str) -> bool:
    u = urllib.parse.urlsplit(link or "")
    host = (u.hostname or "").lower()
    segs = [x for x in u.path.split("/") if x]
    if host.startswith("minishop.") or host.startswith("shop.11st") or "/store/" in u.path:
        return True
    if SEARCH_LINK.search(f"{host}{u.path}?{u.query}"):   # 쇼핑몰 검색 결과·분류 페이지 (상품 글이 아님)
        return True
    if host.endswith(("smartstore.naver.com", "brand.naver.com")) and len(segs) <= 1:
        return True
    return bool(STORE_HOME_TITLE.search(title or "")) or daangn_biz(title) == "home"


def many_species(title: str) -> bool:
    """제목에 규제 어종이 5종 이상 나열돼 있으면 낚시용품 등 여러 어종용 상품으로 본다."""
    from analyzer import _find_hits, _mask
    ids = {r["id"] for h in _find_hits(_mask(title or "")) for r in h["rules"]}
    return len(ids) >= 5
# 가공품: 말리거나 절이거나 조리한 것 (제목·요약 기준). 냉동·손질·회는 가공으로 보지 않는다.
PROCESSED = re.compile(
    r"가공|반건조|건조|말린|훈제|젓갈|액젓|[가-힣]+젓(?![가-힣])|염장|절임|장아찌|통조림|어묵|어포|쥐포|북어포|황태포|"
    r"오징어채|진미채|조림|양념|무침|튀김|밀키트|간편식|레토르트|엑기스|분말|가루|"
    r"황태|북어|먹태|코다리|과메기|굴비|노가리\s*(?:구이|안주)|"
    r"이유식|볶음밥|솥밥|죽\s*키트|[가-힣]{0,4}죽(?![가-힣])|김치|만두|어육|부각|튀각|명태전|동태전|생선전|게장|간장게장|양념게장|전복장|새우장|"
    r"알포|어포|스틱|소시지|햄|통조림|캔(?![가-힣])|간편|즉석|데우기만|"
    r"소금|국수|쌀국수|묵(?![가-힣])|묵채|콩물|다시팩|간장|맛간장|[가-힣]*탕(?![가-힣])|빵(?![가-힣])|밥톳|톳밥|[가-힣]{1,3}밥(?![가-힣])|"
    r"찐톳|데친|숙회|내장|해초\s*모듬|모듬\s*해초|명태녹차|수제\s*간식|"
    r"굴소스|소스|육수|진액|농축액|엑기스|추출물|딱지장|명란장|장조림|한천|우무채|우무(?![가-힣])|녹미채|조미|노가리|숏다리|구이|계란말이|스팀볼|순대|오징어집|버터|후리카케|새콤달콤|바베큐|구운|[가-힣]*국\s*\d|재첩국|마른\s*오징어|건\s*오징어|건오징어|피데기|오다리|백족|칼맞은|마른\s*[가-힣]{1,4}|오징어\s*링")
# 수입산 표시: 나라·산지 이름, 수입·통관, 외국에서만 나는 품종 (제목에 있으면 '국산'이라는 말이 함께 있어도 수입산으로 본다)
IMPORTED = re.compile(r"수입|직수입|병행|러시아|러샤|노르웨이|중국|베트남|칠레|아르헨티나|미국|캐나다|페루|일본|원양|모리타니|세네갈|"
                      r"인도네시아|인도산|태국|대만|필리핀|파키스탄|에콰도르|아이슬란드|알래스카|뉴질랜드|호주|외국산|해외\s*직구|직구|"
                      r"북해도|홋카이도|마가단|프리모리|캄차카|캄챠카|사할린|오호츠크|베링|바렌츠|페로\s*제도|대서양|태평양산|"
                      r"정식\s*통관|통관(?!자)|스노우\s*크랩|킹\s*크랩|골든\s*크랩|레드\s*크랩|랍스터|MSC|ASC|AliExpress|알리익스프레스|테무")
# 국산 표시 ('중국산'의 '국산'은 빼고 본다)
DOMESTIC = re.compile(r"(?<![중외])국산|국내산|연근해|동해안|동해산|서해산|남해산|제주산|우리\s*바다|한국산|우리나라")
# '수입산 아님', '러시아산 아닌 국산'처럼 수입산이 아니라고 밝힌 표현
NOT_IMPORTED = re.compile(r"(?:수입|러시아|중국|일본|북해도|마가단)\s*(?:산\s*)?(?:아님|아닙니다|아니에요|아닌|아니고|X|x|절대\s*아)|(?:수입|러시아|중국|일본|북해도|마가단)\s*산?\s*(?:과|와)\s*(?:비교|다른|다릅)")
# 유통되는 것이 거의 다 수입산인 어종: 국산이라고 밝히지 않으면 수입산으로 본다
#  - 명태: 2019년부터 연중 포획 금지라 시중 명태·동태·황태는 러시아산
#  - 연어: 시중 연어는 노르웨이·칠레 양식이 대부분
MOSTLY_IMPORTED = re.compile(r"명태|동태|생태|황태|코다리|연어")
MOSTLY_IMPORTED_NAMES = {"myeongtae", "yeoneo"}


def imported_reason(title: str, description: str, overseas: bool = False) -> bool:
    """수입산이면 True."""
    t, d = title or "", description or ""
    if overseas:
        return True
    if IMPORTED.search(t) and not NOT_IMPORTED.search(t):
        return True
    if IMPORTED.search(d) and not DOMESTIC.search(t) and not DOMESTIC.search(d) and not NOT_IMPORTED.search(d):
        return True
    if not MOSTLY_IMPORTED.search(t) or DOMESTIC.search(f"{t}\n{d}") or re.search(r"자연산|동해|강원|고성|속초|주문진", t):
        return False
    # 제목의 규제 어종이 명태·연어뿐일 때만 (광어·우럭 등과 함께 파는 글은 남긴다)
    from analyzer import _find_hits, _mask
    names = {r["id"] for h in _find_hits(_mask(t)) for r in h["rules"]}
    return bool(names) and names <= MOSTLY_IMPORTED_NAMES
FARMED = re.compile(r"(?<![서한중일])양식|가두리|축양|육상\s*수조")
NOT_FARMED = re.compile(r"자연산|비양식|양식\s*(?:아님|아닌|아니|X|x|no)|무양식")
# 자연에서 잡았다고 밝힌 표현
WILD = re.compile(r"자연산|비양식|무양식|양식\s*(?:아님|아닌|아니)|해녀|채취|물질|잡은|잡아|잡았|조업|낚시로|낚은|선상|자연\s*그대로|야생|통발|자망|정치망|어획")
# 시중에 도는 것이 거의 다 양식인 어종: 자연산이라고 밝히지 않으면 양식으로 본다
#  광어(넙치)·우럭(조피볼락)·참돔·전복·참가리비·톳·연어
MOSTLY_FARMED_IDS = {"neopchi", "ureok", "chamdom", "jeonbok", "garibi", "tot", "yeoneo"}


def farmed_reason(title: str, description: str) -> bool:
    """양식이면 True."""
    t, d = title or "", description or ""
    text = f"{t}\n{d}"
    if FARMED.search(t) and not NOT_FARMED.search(t):
        return True
    if FARMED.search(d) and not NOT_FARMED.search(text) and not WILD.search(t):
        return True
    if WILD.search(text):
        return False
    from analyzer import _find_hits, _mask
    ids = {r["id"] for h in _find_hits(_mask(t)) for r in h["rules"]}
    return bool(ids) and ids <= MOSTLY_FARMED_IDS
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
    if "nonfood" in ex and (NON_SEAFOOD.search(t) or is_store_home(link, t) or many_species(t) or non_seafood_category(t) or bare_listing(t)
                            or (GEAR_WEAK.search(t) and not CATCH_SALE.search(t))):
        return "nonfood"
    if "processed" in ex and PROCESSED.search(text) and not mixed_fresh_list(t):
        return "processed"
    if "imported" in ex and imported_reason(t, d, overseas):
        return "imported"
    if "farmed" in ex and farmed_reason(t, d):
        return "farmed"
    return None


def mixed_fresh_list(title: str) -> bool:
    """'파갈치, 한치, 자연산 활감성돔, 간장게장 …'처럼 생물 여러 가지를 파는 글에 가공품이 하나 섞인 경우."""
    t = title or ""
    if not re.search(r"활[가-힣]|생물|당일|산지직송", t):
        return False
    if len(re.findall(r"[,·/]", t)) >= 3:
        return True
    from analyzer import _find_hits, _mask   # 어종을 여러 가지 함께 파는 글
    return len({r["id"] for h in _find_hits(_mask(t)) for r in h["rules"]}) >= 2


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
