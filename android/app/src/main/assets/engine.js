/* FishWatch 판독 엔진 — 수산자원관리법 시행령 별표 1·2 기준. 웹 판독기·PC 앱과 같은 규칙 */

/* ---------- 법정 기준 데이터 ---------- */
const RULES = [
// 어류
{id:'daegu',n:'대구',g:'어류',al:['대구','생대구','왕대구'],season:[{f:'01-16',t:'02-15'}],size:{lim:35,u:'cm',m:'전장'},law:'별표1 2.나 · 별표2 1.차'},
{id:'munchi',n:'문치가자미',g:'어류',al:['문치가자미','도다리','봄도다리'],season:[{f:'12-01',t:'01-31'}],size:{lim:20,u:'cm',m:'전장'},law:'별표1 2.다 · 별표2 1.나'},
{id:'cham_gaja',n:'참가자미',g:'어류',al:['참가자미'],weak:['가자미','가자미류'],size:{lim:20,u:'cm',m:'전장'},law:'별표2 1.다',note:'문치·참·용·기름가자미 4종 모두 20cm 이하 금지'},
{id:'yong_gaja',n:'용가자미',g:'어류',al:['용가자미'],size:{lim:20,u:'cm',m:'전장'},law:'별표2 1.퍼'},
{id:'gireum_gaja',n:'기름가자미',g:'어류',al:['기름가자미','물가자미'],size:{lim:20,u:'cm',m:'전장'},law:'별표2 1.허',note:'동해안에서는 물가자미로 부르기도 함'},
{id:'yeoneo',n:'연어',g:'어류',al:['연어'],season:[{f:'10-01',t:'11-30'}],importDefault:true,law:'별표1 2.라',note:'대상은 국내 하천 회귀 연어(Oncorhynchus keta). 노르웨이·칠레산 대서양연어나 양식 연어는 해당 없음'},
{id:'jeoneo',n:'전어',g:'어류',al:['전어','떡전어'],season:[{f:'05-01',t:'07-15',ex:['강원','경북']}],law:'별표1 2.마',note:'강원·경북은 금어기 적용 제외'},
{id:'nore',n:'쥐노래미',g:'어류',al:['쥐노래미','노래미','놀래미'],season:[{f:'11-15',t:'12-14',r:['백령대청']},{f:'11-01',t:'12-31'}],size:{lim:20,u:'cm',m:'전장'},law:'별표1 2.바 · 별표2 1.러'},
{id:'hongeo',n:'참홍어',g:'어류',al:['참홍어','홍어','흑산홍어'],season:[{f:'06-01',t:'07-15'}],size:{lim:42,u:'cm',m:'체반폭'},law:'별표1 2.사 · 별표2 1.버',note:'칠레·아르헨티나 등 수입 홍어는 해당 없음. 체반폭 = 양쪽 가슴지느러미 사이 너비'},
{id:'jogi',n:'참조기',g:'어류',al:['참조기','조기','굴비','영광굴비'],season:[{f:'07-01',t:'07-31',lab:'근해유자망은 4.22~8.10'}],size:{lim:15,u:'cm',m:'전장',pct:true},law:'별표1 2.아 · 별표2 1.저',note:'부세·부세굴비는 다른 종'},
{id:'galchi',n:'갈치',g:'어류',al:['갈치','은갈치','먹갈치','풀치','제주갈치','목포갈치'],juv:['풀치'],season:[{f:'07-01',t:'07-31',lab:'북위 33° 이북 해역'}],seasonSusp:'근해연승 갈치 금어기는 2027.6.30까지 유예, 근해채낚기·연안복합은 원래 제외',size:{lim:18,u:'cm',m:'항문장',pct:true},law:'별표1 2.자 · 별표2 1.서',note:'항문장 = 주둥이~항문 길이. 판매글의 "지(손가락 폭)" 표기는 체장과 다름'},
{id:'godeung',n:'고등어',g:'어류',al:['고등어','고도리','망치고등어','고갈비'],juv:['고도리'],season:[{f:'04-01',t:'06-30',notice:'4.1~6.30 중 1개월, 해양수산부 고시로 매년 지정'}],size:{lim:21,u:'cm',m:'전장',pct:true},sizeSusp:'대형선망 고등어 금지체장은 2027.6.30까지 유예',law:'별표1 2.차 · 별표2 1.어'},
{id:'maljwichi',n:'말쥐치',g:'어류',al:['말쥐치'],weak:['쥐치'],season:[{f:'05-01',t:'07-31',lab:'정치망·연안·구획어업은 6.1~7.31'}],size:{lim:18,u:'cm',m:'전장'},law:'별표1 2.카 · 별표2 1.처'},
{id:'okdom',n:'옥돔',g:'어류',al:['옥돔','옥도미'],season:[{f:'07-21',t:'08-20'}],law:'별표1 2.타'},
{id:'myeongtae',n:'명태',g:'어류',al:['명태','생태','동태','코다리','노가리','황태','먹태','북어','짝태'],juv:['노가리'],yearRound:true,law:'별표1 2.하',note:'국내 해역 명태는 연중 포획 금지. 시중 동태·황태·노가리는 대부분 러시아산'},
{id:'samchi',n:'삼치',g:'어류',al:['삼치'],season:[{f:'05-01',t:'05-31'}],law:'별표1 2.거'},
{id:'gamseong',n:'감성돔',g:'어류',al:['감성돔','감생이'],season:[{f:'05-01',t:'05-31'}],size:{lim:25,u:'cm',m:'전장'},farm:true,law:'별표1 2.너 · 별표2 1.라'},
{id:'doldom',n:'돌돔',g:'어류',al:['돌돔','뺀찌','뻰찌'],juv:['뺀찌','뻰찌'],size:{lim:24,u:'cm',m:'전장'},farm:true,law:'별표2 1.마'},
{id:'chamdom',n:'참돔',g:'어류',al:['참돔','참도미','상사리'],weak:['도미'],juv:['상사리'],size:{lim:24,u:'cm',m:'전장'},farm:true,law:'별표2 1.바'},
{id:'neopchi',n:'넙치',g:'어류',al:['넙치','광어'],size:{lim:35,u:'cm',m:'전장'},farm:true,law:'별표2 1.아',note:'양식 광어는 포획 규제 대상 아님'},
{id:'nongeo',n:'농어',g:'어류',al:['농어','깔따구'],juv:['깔따구'],size:{lim:30,u:'cm',m:'전장'},law:'별표2 1.자'},
{id:'dorumuk',n:'도루묵',g:'어류',al:['도루묵','도루메기'],size:{lim:11,u:'cm',m:'전장'},sizeSusp:'동해구외끌이중형저인망 도루묵 금지체장은 2027.6.30까지 유예',law:'별표2 1.카'},
{id:'mineo',n:'민어',g:'어류',al:['민어'],size:{lim:33,u:'cm',m:'전장'},law:'별표2 1.파'},
{id:'bangeo',n:'방어',g:'어류',al:['방어','대방어','마래미'],juv:['마래미'],size:{lim:30,u:'cm',m:'전장'},farm:true,law:'별표2 1.하',note:'부시리는 다른 종'},
{id:'bollak',n:'볼락',g:'어류',al:['볼락','뽈락'],size:{lim:15,u:'cm',m:'전장'},law:'별표2 1.거'},
{id:'bungjang',n:'붕장어',g:'어류',al:['붕장어','아나고','바다장어'],size:{lim:35,u:'cm',m:'전장'},law:'별표2 1.너'},
{id:'ureok',n:'조피볼락',g:'어류',al:['조피볼락','우럭'],size:{lim:23,u:'cm',m:'전장'},farm:true,law:'별표2 1.더',note:'양식 우럭은 포획 규제 대상 아님'},
{id:'gaetjang',n:'갯장어',g:'어류',al:['갯장어','하모'],size:{lim:40,u:'cm',m:'전장'},law:'별표2 1.커'},
{id:'migeoji',n:'미거지',g:'어류',al:['미거지','물메기','물곰'],weak:['꼼치'],size:{lim:40,u:'cm',m:'전장'},law:'별표2 1.터',note:'꼼치는 다른 종이지만 함께 물메기로 유통됨'},
{id:'cheongeo',n:'청어',g:'어류',al:['청어'],size:{lim:20,u:'cm',m:'전장'},law:'별표2 1.고'},
// 갑각류
{id:'kkotge',n:'꽃게',g:'갑각류',al:['꽃게','암꽃게','수꽃게','숫꽃게','알꽃게','살꽃게'],season:[{f:'06-21',t:'08-20',notice:'6.1~9.30 중 2개월 이내 해양수산부 고시(통상 6.21~8.20)'}],size:{lim:6.4,u:'cm',m:'두흉갑장'},law:'별표1 3.가 · 별표2 2.가',note:'두흉갑장 = 등딱지 세로 길이(가로 폭과 다름)'},
{id:'daege',n:'대게',g:'갑각류',al:['대게','영덕대게','울진대게','박달대게','너도대게','대게류','빵게','암대게'],female:['빵게','암대게','대게 암컷','대게암컷'],season:[{f:'06-01',t:'11-30',lab:'동경 131°30′ 이동은 6.1~10.31, 일부 지정 해역은 별도'}],size:{lim:9,u:'cm',m:'두흉갑장'},law:'별표1 3.나 · 별표2 2.나',note:'대게 암컷(빵게)은 연중 포획 금지. 러시아산 수입 대게는 해당 없음'},
{id:'hongge',n:'붉은대게',g:'갑각류',al:['붉은대게','홍게'],season:[{f:'07-10',t:'08-25',lab:'강원 연안자망은 6.1~7.10'}],seasonSusp:'근해통발 붉은대게 금어기는 2027.6.30까지 유예',law:'별표1 3.다'},
{id:'daeha',n:'대하',g:'갑각류',al:['대하','자연산대하'],season:[{f:'05-01',t:'06-30'}],farm:true,law:'별표1 3.바',note:'양식 흰다리새우를 대하로 파는 경우는 해당 없음'},
// 패류
{id:'saejogae',n:'새조개',g:'패류',al:['새조개'],season:[{f:'06-01',t:'09-30',r:['부산','울산','경남','전남','제주','추자']},{f:'06-16',t:'09-30'}],law:'별표1 4.나'},
{id:'sora',n:'소라',g:'패류',al:['소라','뿔소라'],season:[{f:'07-01',t:'08-31',r:['추자']},{f:'06-01',t:'08-31',r:['제주']},{f:'06-01',t:'07-31',r:['울릉']},{f:'06-01',t:'06-30',r:['여수삼산']}],size:{lim:5,u:'cm',m:'각고',by:[{r:['제주','추자','울릉'],lim:7}]},law:'별표1 4.다 · 별표2 3.나'},
{id:'obunjagi',n:'오분자기',g:'패류',al:['오분자기','마대오분자기'],season:[{f:'07-01',t:'08-31',r:['제주','추자']}],size:{lim:4,u:'cm',m:'각장',only:['제주','추자']},law:'별표1 4.아 · 별표2 3.다'},
{id:'jeonbok',n:'전복',g:'패류',al:['전복','참전복','말전복','까막전복','활전복','전복류'],season:[{f:'10-01',t:'12-31',r:['제주','추자']},{f:'09-01',t:'10-31'}],size:{lim:7,u:'cm',m:'각장',by:[{r:['제주','추자'],lim:10}]},farm:true,law:'별표1 4.라 · 별표2 3.라',note:'시중 전복은 대부분 양식(포획 규제 대상 아님)'},
{id:'jaecheop',n:'기수재첩',g:'패류',al:['기수재첩','재첩'],size:{lim:1.5,u:'cm',m:'각장'},law:'별표2 3.마'},
{id:'kijogae',n:'키조개',g:'패류',al:['키조개'],season:[{f:'07-01',t:'08-31'}],size:{lim:18,u:'cm',m:'각장',only:['부산','울산','강원','경북','경남']},sizeSusp:'제1·2구잠수기 키조개 금지체장은 2027.6.30까지 유예',law:'별표1 4.바 · 별표2 3.바'},
{id:'kokkiri',n:'코끼리조개',g:'패류',al:['코끼리조개'],season:[{f:'05-01',t:'06-30',r:['강원','경북']}],law:'별표1 4.마'},
{id:'garibi',n:'참가리비',g:'패류',al:['참가리비'],season:[{f:'03-01',t:'06-30',r:['포항지정']}],farm:true,law:'별표1 4.사',note:'포항 영일만 일대 지정 해역에만 적용. 시중품은 대부분 양식·수입'},
// 해조류
{id:'neopmiyeok',n:'넓미역',g:'해조류',al:['넓미역'],season:[{f:'09-01',t:'11-30',r:['제주','추자']}],law:'별표1 5.가',note:'제주도지사 고시로 기간 변경 가능'},
{id:'umut',n:'우뭇가사리',g:'해조류',al:['우뭇가사리','천초'],season:[{f:'11-01',t:'03-31'}],law:'별표1 5.나'},
{id:'tot',n:'톳',g:'해조류',al:['톳','생톳'],season:[{f:'10-01',t:'01-31'}],farm:true,law:'별표1 5.다'},
// 그 밖의 수산자원
{id:'haesam',n:'해삼',g:'두족류·기타',al:['해삼','홍해삼','돌기해삼'],season:[{f:'07-01',t:'07-31'}],farm:true,law:'별표1 6.가'},
{id:'ojing',n:'살오징어',g:'두족류·기타',al:['살오징어','오징어','총알오징어','한입오징어','미니오징어','꼬마오징어','피데기','물오징어','생물오징어','동해오징어'],juv:['총알오징어','한입오징어','미니오징어','꼬마오징어'],season:[{f:'04-01',t:'05-31',lab:'근해채낚기·연안복합·정치망은 4.1~4.30'}],size:{lim:15,u:'cm',m:'외투장',pct:true},law:'별표1 6.나 · 별표2 4.나',note:'"총알·한입오징어"는 금지체장 미만 어린 살오징어를 부르는 말'},
{id:'nakji',n:'낙지',g:'두족류·기타',al:['낙지','산낙지','세발낙지','뻘낙지'],season:[{f:'06-01',t:'06-30',lab:'시·도지사가 4.1~9.30 중 1개월 이상 따로 고시 가능'}],law:'별표1 6.다'},
{id:'jukkumi',n:'주꾸미',g:'두족류·기타',al:['주꾸미','쭈꾸미','쭈구미','알주꾸미'],season:[{f:'05-11',t:'08-31'}],law:'별표1 6.라'},
{id:'chammuneo',n:'참문어',g:'두족류·기타',al:['참문어','돌문어'],weak:['문어'],season:[{f:'05-16',t:'06-30',lab:'시·도지사가 5.1~9.15 중 46일 이상 따로 고시 가능'}],law:'별표1 6.마'},
{id:'daemuneo',n:'대문어',g:'두족류·기타',al:['대문어','피문어','왕문어','동해문어'],weak:['문어'],size:{lim:600,u:'g',m:'체중'},law:'별표2 4.가'},
];
const GROUPS=['어류','갑각류','패류','두족류·기타','해조류'];

// 다른 뜻이나 다른 종을 가리키는 표현은 미리 가려 둔다
const EXCLUDE=["갑오징어", "대왕오징어", "반딧불오징어", "한치오징어", "창오징어", "화살오징어", "부세조기", "부세굴비", "부세", "부시리", "흰다리새우", "홍가리비", "방어진", "방어력", "방어전", "농어촌", "농어민", "농어업", "대구광역시", "대구시", "대구에서", "대구 지역", "대구지역", "소라게", "소라색", "생태계", "생태적", "동태적", "대하여", "대하는", "도미노", "하모니", "생태마을", "우럭조개", "왕우럭", "생태 다큐", "생태계", "생태학", "생태 쫌", "환경과 생태", "생태터널", "생태공원", "생태하천", "생태환경", "생태관", "생태체험", "생태교육", "생태복원", "생태보전", "생태탐방", "생태숲", "생태원", "생태통로", "생태관광", "조기 마감", "조기마감", "조기 품절", "조기품절", "조기 종료", "조기종료", "조기 소진", "조기소진", "열기"];
const REGION_LABEL={'전국':'전국','제주':'제주','추자':'추자도','울릉':'울릉·독도','강원':'강원','경북':'경북','경남':'경남','부산':'부산','울산':'울산','전남':'전남','무안영광':'무안·영광','여수삼산':'여수 삼산면','백령대청':'백령·대청','인천':'인천','포항지정':'포항 지정해역'};
const REGION_DETECT=[['추자',/추자/],['제주',/제주|서귀포|성산포|한림|모슬포|우도/],['울릉',/울릉|독도/],['강원',/강원|속초|강릉|삼척|양양|주문진|묵호|거진/],['경북',/경북|경상북도|포항|영덕|울진|경주|구룡포|감포|후포|강구/],['경남',/경남|경상남도|통영|거제|남해|사천|마산|창원|삼천포/],['부산',/부산|기장|자갈치/],['울산',/울산|방어진/],['무안영광',/무안|영광/],['여수삼산',/삼산면|거문도/],['전남',/전남|전라남도|여수|완도|목포|신안|진도|고흥|해남|흑산|벌교/],['백령대청',/백령|대청도/],['인천',/인천|연평|소래/]];

const RE_IMPORT=/수입|러시아|노르웨이|중국산|베트남|칠레|아르헨티나|미국산|캐나다|페루|일본산|원양|모리타니|세네갈|인도네시아|태국산|아이슬란드|알래스카|뉴질랜드|호주산/;
const RE_DOMESTIC=/국산|국내산|연근해|동해안|동해산|서해산|남해산|우리\s*바다/;
const RE_FARM=/양식/;
const RE_WILD=/자연산|해녀|물질|낚시|선상|직접\s*(?:잡|채취)|조업|갓\s*잡|잡은|잡아/;
const RE_FRESH=/활어|활[전대꽃문낙해소홍광우]|\(활\)|산지\s*직송|당일|오늘|금일|갓\s*잡|방금|조업|생물|선어|위판|산낙지|살아\s*있|채취/;
const RE_FROZEN=/냉동|급냉|동결|작년|지난해|지난\s*시즌|비축|재고|반건조|건조|말린|젓갈|염장|훈제|통조림|금어기\s*(?:전|이전|직전)/;
const RE_JUV=/새끼|치어|어린|꼬마|미니|아기|잔챙이/;
const SEV={ok:0,info:1,warn:2,danger:3};
const SEV_LABEL={danger:'위반 의심',warn:'확인 필요',info:'참고',ok:'기준 내'};

const ALIAS=[];
RULES.forEach(r=>{
  (r.al||[]).forEach(a=>ALIAS.push({a,id:r.id,weak:false}));
  (r.weak||[]).forEach(a=>ALIAS.push({a,id:r.id,weak:true}));
  (r.female||[]).forEach(a=>{ if(!r.al.includes(a)) ALIAS.push({a,id:r.id,weak:false}); });
});
ALIAS.sort((x,y)=>y.a.length-x.a.length);
const RULE=Object.fromEntries(RULES.map(r=>[r.id,r]));

function mask(text){
  let w=text;
  EXCLUDE.forEach(ex=>{ let i=w.indexOf(ex); while(i>=0){ w=w.slice(0,i)+'□'.repeat(ex.length)+w.slice(i+ex.length); i=w.indexOf(ex,i+ex.length);} });
  return w;
}
/* 어종 이름 바로 뒤에 붙으면 별명·상호로 보고 어종으로 세지 않는다 (예: 고도리맘, 풀치아빠, 대게수산, 광어횟집) */
const NICK_SUFFIX=new RegExp("^(?:맘|대디|아빠|엄마|님|네(?![가-힣])|공주|왕자|짱|러버|매니아|마니아|티비|TV|tv|닷컴|마켓|상회|수산|스토어|샵|몰|하우스|컴퍼니|상사|유통|가게|식당|횟집|회관|회센터|포차|이네|씨네|패밀리|월드|랜드|피싱|낚시|슈즈|김밥|카페|공방|스튜디오|북스|미디어|게임|퍼즐|빵|나(?![가-힣])|아노|\\d+(?!\\s*(?:kg|키로|킬로|마리|미|g|cm|개|팩|박스|상자|짝|인분|%)))");
function findHits(w){
  const hits=[]; let i=0;
  while(i<w.length){
    let found=null;
    for(const A of ALIAS){ if(w.startsWith(A.a,i)){ found=A; break; } }
    if(found && NICK_SUFFIX.test(w.slice(i+found.a.length, i+found.a.length+4))){ i+=found.a.length; continue; } // 별명·상호의 일부
    if(found){
      const same=ALIAS.filter(A=>A.a===found.a);
      hits.push({start:i,end:i+found.a.length,text:found.a,rules:same.map(s=>({id:s.id,weak:s.weak}))});
      i+=found.a.length;
    } else i++;
  }
  return hits;
}
function num(s){return parseFloat(s);}
function findMeasures(t){
  const out=[];
  const lenRe=/(\d+(?:\.\d+)?)\s*(?:cm|㎝|센치|센티)?\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(cm|CM|Cm|㎝|센티미터|센티|센치|mm|㎜)/g;
  let m;
  while((m=lenRe.exec(t))){
    let a=num(m[1]), b=m[2]?num(m[2]):null; const u=m[3];
    if(/mm|㎜/.test(u)){a/=10; if(b!=null)b/=10;}
    out.push({kind:'cm',start:m.index,end:m.index+m[0].length,raw:m[0],val:Math.min(a,b??a),hi:Math.max(a,b??a)});
  }
  const toG=(v,u)=>/k|키로|킬로/.test(u)?v*1000:v;
  const perCount=/(\d+(?:\.\d+)?)\s*(kg|㎏|키로|킬로|g|그램)\s*(?:에|당)?\s*(\d+)\s*(?:미|마리)(?![가-힣])/g;
  while((m=perCount.exec(t))){
    const g=toG(num(m[1]),m[2])/num(m[3]);
    out.push({kind:'g',start:m.index,end:m.index+m[0].length,raw:m[0],val:Math.round(g),hi:Math.round(g),derived:true});
  }
  const perAnimal=/(?:마리당|미당|개당|한\s*마리|1\s*마리)\s*(?:약|평균)?\s*(\d+(?:\.\d+)?)\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(kg|㎏|키로|킬로|g|그램)/g;
  while((m=perAnimal.exec(t))){
    const a=toG(num(m[1]),m[3]), b=m[2]?toG(num(m[2]),m[3]):a;
    out.push({kind:'g',start:m.index,end:m.index+m[0].length,raw:m[0],val:Math.min(a,b),hi:Math.max(a,b)});
  }
  const suffix=/(\d+(?:\.\d+)?)\s*(?:[~\-–∼]\s*(\d+(?:\.\d+)?))?\s*(kg|㎏|키로|킬로|g|그램)\s*(?:내외|정도|급)?\s*짜리/g;
  while((m=suffix.exec(t))){
    const a=toG(num(m[1]),m[3]), b=m[2]?toG(num(m[2]),m[3]):a;
    out.push({kind:'g',start:m.index,end:m.index+m[0].length,raw:m[0],val:Math.min(a,b),hi:Math.max(a,b)});
  }
  // 겹치는 측정값 제거
  out.sort((x,y)=>x.start-y.start);
  return out.filter((x,i)=>!out.some((y,j)=>j<i && y.end>x.start && y.kind===x.kind));
}
function detectRegions(t){
  const set=[]; REGION_DETECT.forEach(([k,re])=>{ if(re.test(t)) set.push(k); });
  if(set.includes('추자') && !set.includes('제주')) set.push('제주');
  return set;
}
function md(dateStr){return dateStr.slice(5);}
function inRange(d,f,t){return f<=t ? (d>=f&&d<=t) : (d>=f||d<=t);}
function fmtMD(s){const [m,d]=s.split('-').map(Number);return `${m}.${d}`;}
function daysUntil(dateStr,f){
  const base=new Date(dateStr+'T00:00:00'); let y=base.getFullYear();
  let s=new Date(`${y}-${f}T00:00:00`); if(s<base) s=new Date(`${y+1}-${f}T00:00:00`);
  return Math.round((s-base)/86400000);
}
function pickSeason(rule,regions){
  const E=rule.season||[]; if(!E.length) return {mode:'none',entries:[]};
  const specific=E.filter(e=>e.r && e.r.some(x=>regions.includes(x)));
  if(specific.length) return {mode:'regional',entries:[specific[0]]};
  const defs=E.filter(e=>!e.r);
  if(defs.length){
    const ok=defs.filter(e=>!(e.ex && e.ex.some(x=>regions.includes(x))));
    if(!ok.length) return {mode:'excluded',entries:[],ex:defs[0].ex};
    return {mode:'default',entries:ok};
  }
  if(!regions.length || regions.includes('전국')) return {mode:'unknownRegional',entries:E};
  return {mode:'na',entries:[]};
}
function pickSize(rule,regions){
  const s=rule.size; if(!s) return null;
  let lim=s.lim, scope='전국', unknown=false;
  if(s.only){
    if(regions.some(x=>s.only.includes(x))) scope=s.only.filter(x=>regions.includes(x)).map(x=>REGION_LABEL[x]).join('·');
    else if(!regions.length || regions.includes('전국')) {unknown=true; scope=s.only.map(x=>REGION_LABEL[x]).join('·')+' 한정';}
    else return {na:true,...s};
  }
  if(s.by){ const b=s.by.find(b=>b.r.some(x=>regions.includes(x))); if(b){lim=b.lim; scope=b.r.filter(x=>regions.includes(x)).map(x=>REGION_LABEL[x]).join('·');} }
  return {...s,lim,scope,unknown};
}
function seasonText(e){return `${fmtMD(e.f)}~${fmtMD(e.t)}${e.r?` (${e.r.map(x=>REGION_LABEL[x]).join('·')})`:''}${e.ex?` (${e.ex.map(x=>REGION_LABEL[x]).join('·')} 제외)`:''}`;}
function sizeText(s){
  if(!s) return '없음';
  const unit=s.u==='g'?'g':'cm';
  let t=`${s.m} ${s.lim}${unit} 이하`;
  if(s.by) t+=` (${s.by.map(b=>b.r.map(x=>REGION_LABEL[x]).join('·')+' '+b.lim+unit).join(', ')} 이하)`;
  if(s.only) t+=` · ${s.only.map(x=>REGION_LABEL[x]).join('·')}산 한정`;
  return t;
}

function analyzePost(text,dateStr,regionOverride){
  const w=mask(text);
  const hits=findHits(w);
  const meas=findMeasures(text);
  const lineOf=p=>{let n=0;for(let i=0;i<p;i++) if(text[i]==='\n') n++; return n;};
  hits.forEach(h=>h.line=lineOf(h.start));
  const distinct=[...new Set(hits.flatMap(h=>h.rules.map(r=>r.id)))];
  meas.forEach(m=>{
    m.line=lineOf(m.start);
    const same=hits.filter(h=>h.line===m.line);
    let target=same.filter(h=>h.end<=m.start).sort((a,b)=>b.end-a.end)[0];
    if(!target) target=same.filter(h=>h.start>=m.end && h.start-m.end<=15).sort((a,b)=>a.start-b.start)[0];
    if(!target){ const prev=hits.filter(h=>h.end<=m.start).sort((a,b)=>b.end-a.end)[0]; if(prev && m.start-prev.end<40) target=prev; }
    if(!target && distinct.length===1) target=hits[0];
    m.hit=target||null;
  });
  const regions=regionOverride?[regionOverride]:detectRegions(text);
  const ctx={imp:RE_IMPORT.test(text),dom:RE_DOMESTIC.test(text),farm:RE_FARM.test(text),wild:RE_WILD.test(text),fresh:RE_FRESH.test(text),frozen:RE_FROZEN.test(text)};
  const d=md(dateStr);
  const findings=[];
  const byRule={};
  hits.forEach(h=>h.rules.forEach(r=>{ (byRule[r.id]=byRule[r.id]||{hits:[],weakOnly:true}).hits.push(h); if(!r.weak) byRule[r.id].weakOnly=false; }));
  Object.entries(byRule).forEach(([id,g])=>{
    const rule=RULE[id]; const items=[]; const add=(sev,txt)=>items.push({sev,txt});
    const aliases=[...new Set(g.hits.map(h=>h.text))];
    const ms=meas.filter(m=>m.hit && g.hits.includes(m.hit));
    const lines=text.split('\n'); const myLines=[...new Set(g.hits.map(h=>h.line))].map(i=>lines[i]).join('\n');
    const lImp=RE_IMPORT.test(myLines), lFarm=RE_FARM.test(myLines);
    const notCaught = lImp ? 'imp' : (lFarm && rule.farm) ? 'farm' : null;
    const cap=(sev)=>{
      let s=sev;
      if(g.weakOnly && SEV[s]>SEV.warn) s='warn';
      if(notCaught && SEV[s]>SEV.info) s='info';
      if(rule.importDefault && !ctx.dom && SEV[s]>SEV.info) s='info';
      if(rule.farm && !ctx.wild && !lFarm && SEV[s]>SEV.warn) s='warn';
      return s;
    };
    let gauge=null;
    // 1) 연중 금지(명태)
    if(rule.yearRound){
      const domesticHint=ctx.dom || /강원|고성|속초|주문진|동해/.test(text);
      if(lImp && !domesticHint) add('info','수입산(러시아 등) 표기가 있어 국내 포획 금지 대상이 아닐 가능성이 큽니다.');
      else if(domesticHint) add('danger','국내산 명태로 보이는 표현이 있습니다. 국내 해역 명태는 1.1~12.31 연중 포획 금지입니다.');
      else add('warn','명태는 국내 해역에서 연중 포획 금지입니다. 원산지(수입산 여부)를 확인하세요.');
    }
    // 2) 어린 개체 은어
    const juvHit=aliases.find(a=>(rule.juv||[]).includes(a));
    if(juvHit && !rule.yearRound){
      const sev = id==='bangeo'?'warn':'danger';
      add(cap(sev),`"${juvHit}"는 금지체장 미만 어린 ${rule.n}를 부르는 말입니다.`);
    } else if(rule.size){
      const near=g.hits.some(h=>RE_JUV.test(text.slice(Math.max(0,h.start-6),h.start)));
      if(near) add(cap('warn'),`어린 개체를 뜻하는 표현(새끼·치어·미니 등)이 ${rule.n} 앞에 붙어 있습니다.`);
    }
    // 3) 암컷 대게
    const fem=(rule.female||[]).find(f=>text.includes(f));
    if(fem) add(cap('danger'),`"${fem}" 표기: 대게 암컷은 크기·시기와 관계없이 연중 포획 금지입니다.`);
    // 4) 체장·체중
    const sz=pickSize(rule,regions);
    if(sz && !sz.na){
      const unit=sz.u==='g'?'g':'cm';
      const rel=ms.filter(m=>m.kind===(sz.u==='g'?'g':'cm'));
      if(rel.length){
        const minM=rel.reduce((a,b)=>a.val<=b.val?a:b);
        const under=minM.val<=sz.lim;
        gauge={val:minM.val,hi:minM.hi,lim:sz.lim,unit,under};
        if(under){
          let s=cap('danger'); if(sz.unknown && SEV[s]>SEV.warn) s='warn';
          add(s,`표기 크기 ${minM.raw.trim()} → 기준(${sz.m} ${sz.lim}${unit} 이하 포획 금지${sz.scope!=='전국'?', '+sz.scope:''})에 걸립니다.${minM.derived?' (총중량÷마릿수로 계산한 마리당 무게)':''}`);
          if(sz.pct) add('info','단, 어획량 중 해당 크기가 20% 미만인 경우는 예외로 규정되어 있습니다(어업 현장 기준).');
          if(['항문장','두흉갑장','체반폭','외투장'].includes(sz.m)) add('info',`법정 계측 기준은 ${sz.m}입니다. 판매글 수치가 전장(전체 길이)이면 실제 ${sz.m}은 더 짧습니다.`);
        } else {
          add('ok',`표기 크기 ${minM.raw.trim()}는 기준(${sz.m} ${sz.lim}${unit} 이하 금지)보다 큽니다.`);
          if(['항문장','두흉갑장','체반폭','외투장'].includes(sz.m)) add('info',`법정 기준은 ${sz.m}입니다. 표기 수치가 전체 길이라면 ${sz.m} 기준으로는 미달일 수 있습니다.`);
        }
        if(rule.sizeSusp) add('info',rule.sizeSusp+' (TAC 참여 어선 한정).');
      } else if(!juvHit) {
        add('info',`크기 표기가 없습니다. 기준: ${sz.m} ${sz.lim}${unit} 이하 포획 금지${sz.scope!=='전국'?' ('+sz.scope+')':''}.`);
      }
    } else if(sz && sz.na){
      add('ok',`금지체장은 ${sz.only.map(x=>REGION_LABEL[x]).join('·')}산에만 적용되어 이 지역과는 무관합니다.`);
    }
    // 5) 금어기
    const ps=pickSeason(rule,regions);
    if(ps.mode==='excluded') add('ok',`${ps.ex.map(x=>REGION_LABEL[x]).join('·')}는 금어기 적용에서 제외됩니다.`);
    let inSeason=null;
    ps.entries.forEach(e=>{ if(!inSeason && inRange(d,e.f,e.t)) inSeason=e; });
    if(inSeason){
      let s = ctx.fresh ? 'danger' : ctx.frozen ? 'info' : 'warn';
      if(inSeason.notice && SEV[s]>SEV.warn) s='warn';
      if(ps.mode==='unknownRegional' && SEV[s]>SEV.warn) s='warn';
      if(rule.seasonSusp && SEV[s]>SEV.warn) s='warn';
      s=cap(s);
      let why = ctx.fresh ? '당일·활어·산지직송 등 최근 어획을 뜻하는 표현이 있습니다.' : ctx.frozen ? '냉동·건조 등 표현이 있어 금어기 이전 어획분일 수 있습니다(어획일 증빙 확인).' : '어획 시점이 글에 드러나지 않습니다.';
      add(s,`게시일 ${fmtMD(d)}은 금어기(${seasonText(inSeason)}${inSeason.lab?', '+inSeason.lab:''}) 기간입니다. ${why}`);
      if(inSeason.notice) add('info',`기간은 ${inSeason.notice}.`);
      if(ps.mode==='unknownRegional') add('info','이 금어기는 특정 지역에만 적용됩니다. 어획 지역을 지정하면 더 정확해집니다.');
      if(rule.seasonSusp) add('info',rule.seasonSusp+'.');
    } else if(ps.entries.length){
      const e=ps.entries[0]; const left=daysUntil(dateStr,e.f);
      if(left<=14) add('info',`${left}일 뒤 금어기(${seasonText(e)}) 시작.`);
      else add('ok',`게시일은 금어기(${ps.entries.map(seasonText).join(', ')}) 밖입니다.`);
    }
    if(notCaught==='imp') add('info','수입산 표현이 있습니다. 금어기·금지체장은 국내 해역 포획물에 적용됩니다.');
    if(notCaught==='farm') add('info','양식산 표현이 있습니다. 양식 수산물은 포획 규제 대상이 아닙니다.');
    if(rule.farm && !ctx.wild && !lFarm && items.some(i=>i.sev==='warn')) add('info',`${rule.n}은 양식품이 많이 유통됩니다. 자연산 여부를 확인하세요.`);
    if(g.weakOnly) add('info',`"${aliases.join(', ')}"만으로는 정확한 종을 알 수 없어 ${rule.n} 기준을 가정했습니다.`);
    if(rule.note && !juvHit) add('info',rule.note+'.');
    if(!items.length) add('ok','적용되는 금어기·금지체장 문제를 찾지 못했습니다.');
    const sev=items.reduce((a,b)=>SEV[b.sev]>SEV[a]?b.sev:a,'ok');
    findings.push({rule,aliases,items,sev,gauge,first:Math.min(...g.hits.map(h=>h.start))});
  });
  findings.sort((a,b)=>SEV[b.sev]-SEV[a.sev]||a.first-b.first);
  const sevOfRule=Object.fromEntries(findings.map(f=>[f.rule.id,f.sev]));
  hits.forEach(h=>{ h.sev=h.rules.map(r=>sevOfRule[r.id]).reduce((a,b)=>SEV[b]>SEV[a]?b:a,'ok'); });
  const sev=findings.reduce((a,b)=>SEV[b.sev]>SEV[a]?b.sev:a,'ok');
  return {text,hits,meas,findings,regions,ctx,sev};
}

/* ---------- 수집 파이프라인 (앱의 백그라운드 점검과 화면이 함께 사용) ---------- */
var FW_PIPE = (function () {
  var RISK_TERMS = ['총알오징어', '한입오징어', '풀치', '고도리', '상사리', '뺀찌', '깔따구', '빵게', '대게 암컷',
    '국산 명태', '국내산 생태', '동해 명태'];
  /* 웹문서 검색으로 찾는 판매 사이트. 설정에서 켜고 끄거나 새로 추가할 수 있다.
     domains: 링크 주소로 사이트를 알아보는 도메인(하위 도메인 포함)
     query: 검색어 뒤에 붙여 그 사이트 글을 끌어올리는 말 (쉼표로 여러 개)
     overseas: 해외 판매 사이트 → 상품이 수입품이라 판정을 '확인 필요'까지만 올린다
     trade: 쇼핑몰·중고거래처럼 글 자체가 판매 글인 사이트 (판매 표현이 없어도 판매글로 본다) */
  var DEFAULT_SITES = [
    { name: '네이버 쇼핑', domains: ['smartstore.naver.com', 'shopping.naver.com', 'brand.naver.com'], query: '스마트스토어', enabled: true, trade: true },
    { name: '당근', domains: ['daangn.com'], query: '당근', enabled: true, trade: true },
    { name: '번개장터', domains: ['bunjang.co.kr'], query: '번개장터', enabled: true, trade: true },
    { name: '쿠팡', domains: ['coupang.com'], query: '쿠팡', enabled: true, trade: true },
    { name: '11번가', domains: ['11st.co.kr'], query: '11번가', enabled: true, trade: true },
    { name: 'G마켓', domains: ['gmarket.co.kr'], query: 'G마켓', enabled: true, trade: true },
    { name: '옥션', domains: ['auction.co.kr'], query: '옥션', enabled: true, trade: true },
    { name: '롯데ON', domains: ['lotteon.com'], query: '롯데온', enabled: true, trade: true },
    { name: 'SSG닷컴', domains: ['ssg.com'], query: 'SSG', enabled: true, trade: true },
    { name: '카카오 쇼핑', domains: ['store.kakao.com', 'shoppinghow.kakao.com'], query: '톡딜', enabled: true, trade: true },
    { name: '다음 카페', domains: ['cafe.daum.net'], query: '다음카페', enabled: true },
    { name: '네이버 밴드', domains: ['band.us'], query: '밴드', enabled: true },
    { name: '테무', domains: ['temu.com'], query: '테무', enabled: true, trade: true, overseas: true },
    { name: '알리익스프레스', domains: ['aliexpress.com'], query: '알리익스프레스', enabled: true, trade: true, overseas: true }
  ];
  /* 카페·블로그 검색 API로 오는 글의 이름표 (설정과 무관하게 항상 인식) */
  var API_SITES = [
    { name: '네이버 카페', domains: ['cafe.naver.com'] },
    { name: '네이버 블로그', domains: ['blog.naver.com'] }
  ];
  var sites = DEFAULT_SITES;

  function normDomain(d) {
    return String(d || '').trim().toLowerCase().replace(/^https?:\/\//, '').replace(/[\/?#:].*$/, '').replace(/^(m|www)\./, '');
  }
  /* 설정의 사이트 목록을 적용한다. 없으면 기본 목록 */
  function configure(cfg) {
    var exl = cfg && cfg.collect && cfg.collect.exclude;
    exclude = Array.isArray(exl) ? exl : DEFAULT_EXCLUDE;
    titleSpecies = !(cfg && cfg.collect && cfg.collect.title_species === false);
    var list = cfg && cfg.collect && cfg.collect.sites;
    if (!list || !list.length) { sites = DEFAULT_SITES; return sites.length; }
    sites = list.filter(function (x) { return x && x.name && x.domains && x.domains.length; }).map(function (x) {
      return { name: String(x.name).trim(), domains: x.domains.map(normDomain).filter(Boolean), query: String(x.query || x.name).trim(),
        enabled: x.enabled !== false, overseas: !!x.overseas, trade: !!x.trade };
    });
    return sites.length;
  }
  function matchSite(host, list) {
    for (var i = 0; i < list.length; i++) {
      var ds = list[i].domains;
      for (var j = 0; j < ds.length; j++) {
        if (host === ds[j] || host.slice(-(ds[j].length + 1)) === '.' + ds[j]) return list[i];
      }
    }
    return null;
  }
  /* 판매·거래·경매 글만 남긴다. 카페·블로그 등은 아래 표현이 있어야 하고, 쇼핑몰(trade) 글은 그 자체로 판매글 */
  /* ---------- 판매글·제외 기준: PC 앱 collector.py에서 그대로 옮겨 온 것 (genfilters.py로 생성) ---------- */
  var TRADE_WORDS = new RegExp("판매|팝니다|팔아요|팔아용|팔게요|팔께요|처분|직판|도매|산지\\s*직송|직송|공동\\s*구매|공구|특가|주문\\s*(?:가능|받|접수|하세요|주세요)|입금|택배\\s*(?:가능|발송|보내)|직거래|거래\\s*(?:합니다|원해|원합니다|가능|희망|해요)|경매|위판|입찰|낙찰|경락|공판장|\\[\\s*(?:판매|팝니다|거래|직거래|경매)\\s*\\]", '');
  var CATCH_FRESH = new RegExp("(?:오늘|당일|금일|방금|갓|막|새벽(?:에)?|아침(?:에)?|어제|직접)\\s*(?:잡은|잡아\\s*온|잡아온|잡았|건진|채취한|조업한|들어온|입고된|올라온|따온)|(?:오늘|당일|금일)\\s*(?:조업|입고|입항|위판|경매|바리|물량)|당일\\s*바리|당일\\s*발송|선도\\s*(?:최상|좋)|살아\\s*있(?:는|어요|습니다)|활\\s*(?:상태|어)\\s*(?:좋|최상)", '');
  var CONTACT = new RegExp("필요하신\\s*분|원하시는\\s*분|가져가실\\s*분|드실\\s*분|구매\\s*(?:가능|원하)|연락\\s*(?:주세요|주시면|바랍니다|부탁)|문의\\s*(?:주세요|주시면|바랍니다|환영)|쪽지\\s*(?:주세요|주시면)|댓글\\s*(?:주세요|남겨)|보내\\s*드립니다|보내\\s*드려요|물량\\s*(?:있|확보|가능|한정)|선착순|예약\\s*(?:받|가능)", '');
  var PRICE_QTY = new RegExp("\\d[\\d,]*\\s*원|\\d+\\s*만\\s*원|\\d+(?:\\.\\d+)?\\s*(?:kg|키로|킬로|마리|미(?![가-힣])|박스|상자|짝)", '');
  var NOT_TRADE = new RegExp("레시피|요리법|만드는\\s*법|만들기|손질법|맛집|먹방|조리법|안주|술상|집밥|내돈내산|후기|리뷰|방문기|다녀왔|다녀온|브이로그|일상|디저트|푸딩|카페\\s*(?:추천|투어)|뉴스|기자|기사|보도|칼럼|소식|단속|적발|압수|검거|입건|해경|해양경찰|탄소|기후|배출권|정책|연구|시대|주목|전망|세미나|포럼|교육|해먹|먹었|먹은|맛보|금어기\\s*(?:안내|시작|해제|돌입|끝)|조황|낚시\\s*(?:포인트|후기)|여행|캠핑|축제|수협\\s*\\d{1,2}\\s*월|\\d{1,2}\\s*월\\s*\\d{1,2}\\s*일\\s*\\(|\\(\\s*[월화수목금토일]요일|\\d+\\s*물\\s*\\)|물때|시세\\s*(?:정보|표|동향|현황|조회)|(?:위판|경매)\\s*(?:현황|시세|결과|정보|동향|가격|일지)|굿네이버스|후원|기부|봉사|캠페인|공익|자선|방충망|시공|입주|아파트|분양|청소|이사(?![가-힣A-Za-z0-9_])|학원|과외|부동산|렌탈|보험|대출|채용|구인|구직|중고차|자동차|신차|에디션|시승|출고|전시장|대리점|딜러|리스(?![가-힣A-Za-z0-9_])|타이어|르노|현대차|기아|차이점|가이드|활용\\s*팁|총정리|알아보|정리했|효능|칼로리|영양|백과|사전|수산학|KBS|MBC|SBS|JTBC|tvN|생생정보|방송|메뉴|아르바이트|알바|모집|모임|찾아요|주인\\s*찾|분실|실종|탐방|전시|박람회|엑스포|엑스코|아시는\\s*분|아실까요|아는\\s*분|어디서|어디\\s*(?:있|가|서)|파는\\s*곳|판매하는\\s*곳|살\\s*수\\s*있는|먹을\\s*수\\s*있는|먹을수있는|살수있는|추천\\s*(?:해|좀|부탁)|질문|궁금|\\|\\s*[가-힣0-9]+(?:동|읍|면|리|가)\\s*$|뜻\\s*[:은]|선택\\s*방법|올바른\\s*선택|먹는\\s*법|받은\\s*상품|받았는데|이건\\s*사야|사야\\s*돼|소소한\\s*한잔|의\\s*진수|보는\\s*법|가격\\s*20\\d\\d|첫\\s*위판|솔직한|싶었던|시세\\s*(?:·|정리|체크|비교|확인)|기준\\s*정리|가기\\s*전에|비용\\s*체크|\\d자\\s*사기|사기\\s*(?:피해|사건|당|수법|예방|죄)|소송|변호사|법률|법무|판례|판결|고소|전세|월세|청약", '');
  var NON_SEAFOOD = new RegExp("액막이|소코뚜레|소뚜레|도어벨|부적|고사용|장식|인테리어|오브제|모빌|풍경종|키링|인형|피규어|모형|굿즈|스티커|티셔츠|액자|쿠션|장난감|자석|문패|낚시대|낚싯대|전용대|선상대|갯바위대|로드(?![가-힣A-Za-z0-9_])|채비|루어|에기|지그|웜(?![가-힣A-Za-z0-9_])|봉돌|원줄|목줄|바늘|집어등|뜰채|살림망|낚시\\s*(?:용품|세트|가방|의자|조끼)|구명조끼|사료|미끼|떡밥|비료|영양제|캡슐|건강기능|오메가|화장품|비누|책(?![가-힣A-Za-z0-9_])|도서|교재|어항|수족관|관상어|열대어|인쇼어|오프쇼어|쇼어|라이트\\s*게임|에깅|타이라바|지깅|캐스팅|베이트|스피닝|릴(?![가-힣A-Za-z0-9_])|합사|카본|라인(?![가-힣A-Za-z0-9_])|싱커|스냅|도래|구멍찌|전자찌|민장대|태클|미노우|훅(?![가-힣A-Za-z0-9_])|[A-Za-z]?\\d{3,4}\\s*-?\\s*(?:UL|L|ML|M|MH|H|XH)(?![A-Za-z])|씨호크|시마노|다이와|바낙스|엔에스|해동조구|아부가르시아|메이저크래프트|테일워크|제이에스컴퍼니|한조|은성|용성|쯔리겐|가마가츠|도요피싱|썬라인|요즈리|듀엘|대부분\\s*어종|전\\s*어종|다\\s*어종|어종\\s*불문|쇼크리더|와이어|케미|캐미|밧데리|배터리|건전지|다운샷|티탄|낚시줄|낚싯줄|\\d+(?:\\.\\d+)?\\s*파이|\\d+\\s*인치|\\d+\\s*mm(?![가-힣A-Za-z0-9_])|[가-힣]{1,4}(?:용품|채비)\\s*판매|(?:광어|우럭|갈치|풀치|쭈꾸미|주꾸미|문어)\\s*(?:우럭|광어)?\\s*용(?![가-힣])|[가-힣]{1,3}전용(?![가-힣])|슈어캐치|워터맨|버클리|엘리게이터|비글|조구|샌드사딘|얼라이브|화투|고스톱|맞고|오광|홍단|청단|피박|퍼즐|보드게임|게임|소설|장편|만화|웹툰|굿즈|강아지|고양이|반려견|반려묘|반려동물|애견|애묘|펫(?=[가-힣\\s])|트릿|찜기|찜솥|냄비|무시깡|모카포트|커피메이커|알레시|Alessi|가위|집게|도마|우표|수집품|기념주화|엽서|RC|rc카|알씨|송수신기|드론|운동화|스니커즈|방한화|부츠|슬리퍼|신발|의류|티셔츠|후드|모자|펜치|뺀치|뻰지|뺀지|밴찌|니빠|니뻐|니퍼|플라이어|공구|롱노즈|롱노우즈|압착|컷팅|절단기|스패너|몽키|망치|로보스터|로보스타|LOBSTER|고바야시|타바타|(?:공업|전기|작업|다용도|전공|강력)\\s*뺀찌|뺀찌\\s*(?:깡|공구|세트)|[가-힣]*김(?=\\s|$|\\d|\\()|김밥|\\d+\\s*톳|톳\\s*\\(?\\s*\\d+\\s*(?:장|매|g)|초피|제피|젠피|산초|약초|열매|유충|샤워기|세면대|수전|필터|정수|모기|해충|벌레|방충|하루살이|단열\\s*필름|클렌징|폼(?![가-힣A-Za-z0-9_])|화장|세안|목걸이|귀걸이|팔찌|반지|액세서리|공예|껍질|골동품|노래(?!미)|메들리|음원|앨범|USB|음향|채칼|채반|채망|틀(?![가-힣A-Za-z0-9_])|젤리|스트로우|빨대|슬러시|음료|기프티콘|상품권|금액권|\\d+\\s*만원권|와인|소주|맥주|막걸리|구합니다|동출|동행|결제창|소통방|단톡|오픈채팅|보러가기|덮밥|냉면|라면|컵면|미역국|국물용|한상(?!자)|크랩\\s*스톡|풀치대|갈치대|낚싯대|크래미|맛살|게살|대게살|붉은대게살|파지|용기(?![가-힣])|포장재|아이스팩|용돈|이벤트\\s*박스|실버바|골드바|인증\\d+|어린이집|유치원|학급|학원|캬라멜|카라멜|캔디|사탕|누룽지|칩(?![가-힣])|과자|트랩|퇴치|날파리|초파리|거세|앞치마|비닐가운|승진\\s*축하|개업\\s*(?:식|축하)|화분|유정란|펜션|페스룸|날자!?\\s*고도리|독(?![가-힣])|DOG|[Dd]og|도그|캣|[Cc]at(?![a-z])|고양이|강아지|반려|애견|애묘|키블|어덜트|인도어|퍼피|키튼|져키|저키|육포|껌(?![가-힣])|츄르|쉬바|ANF|anf|식스프리|뉴트리나|네츄럴|내추럴\\s*발란스|로얄캐닌|트릿|간식|앰플|PDRN|pdrn|크림(?![가-힣])|콜라겐|컨실러|스킨|세럼|에센스|로션|토너|마스크팩|글루타치온|부스터|모공|미백|주름|치즈|부추전|해물전|닭강정|까스|후토마키|초밥(?!\\s*(?:필렛|용))|쿠키|[가-힣]*칩(?![가-힣])|스낵|소프트(?![가-힣])|오징어링|링\\s*\\d|소면|귀채|진미|명엽채|낫또|샐러드(?!용)|밥\\s*지을|볶음|연어장|식해|순살\\s*유아|유아|돌아기|수저|받침|도자기|복대|쁘라이어|우산|양산(?!시)|셔츠|고도리\\s*티|반팔티|긴팔티|맨투맨|피라미드|료칸|호텔\\s*\\d+\\s*박|뷔페|투어|우화|그림책|동화|[가-힣]?\\s*이야기\\s*\\d*$|주방\\s*직원|직원\\s*(?:구|모집)|[남여]\\s*\\d{2}\\s*년|천초근|꼭두서니|묵칼|집어제|유인제|초릿대|카고|[가-힣]{1,3}돔찌|구멍찌|막대찌|낚시\\s*-\\s*AliExpress|AliExpress\\s*에서|애자|진주볼|진주펄|릴대|모든\\s*어종|그물망|던질찌|[가-힣]{1,6}(?<!뺀)(?<!빤)찌(?=\\s*(?:-|$))|Fukin|[가-힣]*칼(?=\\s|$)|다용도칼|접도|캇타|나사|볼트|댄스|무한\\s*리필|미친\\s*자들|체험|다이빙|해부|포크(?![가-힣])|스텐|깔때기|주입기|도구(?:는|가|를|\\s*세트)|다큐|오일(?![가-힣])|DNA|케어|[가-힣]*츄(?![가-힣])|미운영|\\\"[^\\\"]*…\\\"?$", '');
  var GEAR_WEAK = new RegExp("[가-힣]{1,3}낚시(?![가-힣])|원투|메탈|스푼|바이브|만능|선상\\s*전용", '');
  var CATCH_SALE = new RegExp("잡은|잡아|잡았|조과|팝니다|판매합니다|팔아요|\\d\\s*(?:kg|키로|마리|미(?![가-힣]))", '');
  var STORE_HOME_TITLE = new RegExp("^(?:G마켓|옥션|11번가|쿠팡)\\s*[-:|]|미니샵|스토어\\s*홈|:\\s*네이버\\s*(?:스마트)?스토어$|판매자\\s*홈|님의\\s*프로필|의\\s*(?:상점|가게|프로필)(?:\\s*[-|]|$)|\\|\\s*당근\\s*검색|검색\\s*결과|기획전\\s*>|카카오톡\\s*스토어\\s*\\S+$|의\\s*판매\\s*물품|\\|\\s*수산물/건해산$|^[^|\\d]*/[^|\\d]*\\|[^|\\d]*/[^|\\d]*\\|", '');
  var LISTING_TITLE = new RegExp("^[가-힣A-Za-z]{1,8}(?:\\s*[/ㆍ·,]\\s*[가-힣A-Za-z]{1,8})*(?:\\s+-\\s+[^-|]{1,25})?$", '');
  var LISTING_SALE = new RegExp("특가|입고|활|생물|직송|당일|판매|할인|팝니다|팔아요|자연산|국내산|제철|\\d", '');
  var SEARCH_LINK = new RegExp("^search\\.|^browse\\.|/total-search|/search(?:/|\\?|$)|/categories/|DisplayCategory|[?&](?:kwd|keyword|searchKeyword|query)=", 'i');
  var BIZ_SHOP_CATEGORY = new RegExp("소매|판매|마트|식자재|과일|농|수산|횟|해산|건어물|정육|반찬|기타", '');
  var DAANGN_BIZ = new RegExp("^([^|]{1,60}?)\\s*\\|\\s*[^|]*[가-힣]+(?:시|도|군|구)\\s[^|]*\\|\\s*[^|]*$", '');
  var BIZ_SALE = new RegExp("\\d|[!?~]|예약|입고|왔어|도착|판매|팝니다|팔아|생물|활|국내산|자연산|원가|털|특가|할인|개시|오픈|마감|남았|드세요|챙겨|드실|주문|배송|택배|산지|당일|오늘|싱싱|제철|가격|세일|이벤트", '');
  var CATEGORY_TAIL = new RegExp("\\s[-|]\\s([^-|]{2,30})$", '');
  var SEAFOOD_CATEGORY = new RegExp("생선|수산|해산|게|새우|조개|굴|전복|오징어|문어|낙지|주꾸미|쭈꾸미|어란|회|갈치|고등어|명태|동태|해조|미역|톳|다시마|김(?![가-힣A-Za-z0-9_])|멸치|농수축산|건어물|장어|연어|참치|광어|우럭|방어|어류|활어|선어|홍합|소라|해삼|성게|멍게", '');
  var SITE_NAMES = new RegExp("^(?:옥션|G마켓|11번가|쿠팡|당근|번개장터|SSG|SSG닷컴|롯데ON|롯데온|다음\\s*카페|네이버\\s*블로그|네이버\\s*카페|네이버\\s*쇼핑|스마트\\s*스토어|브랜드\\s*스토어|위메프|티몬|인터파크|톡딜|카카오|테무|알리익스프레스)", '');
  var PROCESSED = new RegExp("가공|반건조|건조|말린|훈제|젓갈|액젓|[가-힣]+젓(?![가-힣])|염장|절임|장아찌|통조림|어묵|어포|쥐포|북어포|황태포|오징어채|진미채|조림|양념|무침|튀김|밀키트|간편식|레토르트|엑기스|분말|가루|황태|북어|먹태|코다리|과메기|굴비|노가리\\s*(?:구이|안주)|이유식|볶음밥|솥밥|죽\\s*키트|[가-힣]{0,4}죽(?![가-힣])|김치|만두|어육|부각|튀각|명태전|동태전|생선전|게장|간장게장|양념게장|전복장|새우장|알포|어포|스틱|소시지|햄|통조림|캔(?![가-힣])|간편|즉석|데우기만|소금|국수|쌀국수|묵(?![가-힣])|묵채|콩물|다시팩|간장|맛간장|[가-힣]*탕(?![가-힣])|빵(?![가-힣])|밥톳|톳밥|[가-힣]{1,3}밥(?![가-힣])|찐톳|데친|숙회|내장|해초\\s*모듬|모듬\\s*해초|명태녹차|수제\\s*간식|굴소스|소스|육수|진액|농축액|엑기스|추출물|딱지장|명란장|장조림|한천|우무채|우무(?![가-힣])|녹미채|조미|노가리|숏다리|구이|계란말이|스팀볼|순대|오징어집|버터|후리카케|새콤달콤|바베큐|구운|[가-힣]*국\\s*\\d|재첩국|마른\\s*오징어|건\\s*오징어|건오징어|피데기|오다리|백족|칼맞은|마른\\s*[가-힣]{1,4}|오징어\\s*링", '');
  var IMPORTED = new RegExp("수입|직수입|병행|러시아|러샤|노르웨이|중국|베트남|칠레|아르헨티나|미국|캐나다|페루|일본|원양|모리타니|세네갈|인도네시아|인도산|태국|대만|필리핀|파키스탄|에콰도르|아이슬란드|알래스카|뉴질랜드|호주|외국산|해외\\s*직구|직구|북해도|홋카이도|마가단|프리모리|캄차카|캄챠카|사할린|오호츠크|베링|바렌츠|페로\\s*제도|대서양|태평양산|정식\\s*통관|통관(?!자)|스노우\\s*크랩|킹\\s*크랩|골든\\s*크랩|레드\\s*크랩|랍스터|MSC|ASC|AliExpress|알리익스프레스|테무", '');
  var DOMESTIC = new RegExp("(?<![중외])국산|국내산|연근해|동해안|동해산|서해산|남해산|제주산|우리\\s*바다|한국산|우리나라", '');
  var NOT_IMPORTED = new RegExp("(?:수입|러시아|중국|일본|북해도|마가단)\\s*(?:산\\s*)?(?:아님|아닙니다|아니에요|아닌|아니고|X|x|절대\\s*아)|(?:수입|러시아|중국|일본|북해도|마가단)\\s*산?\\s*(?:과|와)\\s*(?:비교|다른|다릅)", '');
  var MOSTLY_IMPORTED = new RegExp("명태|동태|생태|황태|코다리|연어", '');
  var FARMED = new RegExp("(?<![서한중일])양식|가두리|축양|육상\\s*수조", '');
  var NOT_FARMED = new RegExp("자연산|비양식|양식\\s*(?:아님|아닌|아니|X|x|no)|무양식", '');
  var WILD = new RegExp("자연산|비양식|무양식|양식\\s*(?:아님|아닌|아니)|해녀|채취|물질|잡은|잡아|잡았|조업|낚시로|낚은|선상|자연\\s*그대로|야생|통발|자망|정치망|어획", '');
  var MIXED_FRESH = /활[가-힣]|생물|당일|산지직송/;
  function isStoreHome(link, title) {
    var m = /^https?:\/\/([^\/?#:]+)([^?#]*)/i.exec(link || '');
    if (m) {
      var host = m[1].toLowerCase(), path = m[2] || '', segs = path.split('/').filter(Boolean);
      if (/^minishop\./.test(host) || /^shop\.11st/.test(host) || path.indexOf('/store/') >= 0) return true;
      var q = (/\?([^#]*)/.exec(link) || [])[1] || '';
      if (SEARCH_LINK.test(host + path + '?' + q)) return true;
      if (/(^|\.)(smartstore|brand)\.naver\.com$/.test(host) && segs.length <= 1) return true;
    }
    return STORE_HOME_TITLE.test(title || '') || daangnBiz(title) === 'home';
  }
  /* 당근 업체 글: 'sale'(소식·판매 글) 또는 'home'(가게 이름만 있는 업체 소개) */
  function daangnBiz(title) {
    var m = DAANGN_BIZ.exec(title || '');
    if (!m) return null;
    return BIZ_SALE.test(m[1]) ? 'sale' : 'home';
  }
  /* 상품 글이 아닌 분류(목록) 페이지: "꽃게/대게/킹크랩", "대게/홍게 - 옥션" */
  function bareListing(title) {
    var t = (title || '').trim();
    if (!LISTING_TITLE.test(t) || LISTING_SALE.test(t)) return false;
    return t.indexOf('/') >= 0 || t.indexOf('ㆍ') >= 0 || /\s-\s/.test(t);
  }
  /* 쇼핑몰 제목 끝의 " - 분류"가 수산물 분류가 아니면 수산물 상품이 아니다 */
  function nonSeafoodCategory(title) {
    var bcat = (title || '').split('|').pop();
    if (daangnBiz(title) === 'sale' && (BIZ_SHOP_CATEGORY.test(bcat) || /\.\.|…/.test(bcat))) return false;
    var m = CATEGORY_TAIL.exec(title || '');
    if (!m) return false;
    var cat = m[1].trim();
    if (SITE_NAMES.test(cat) || cat.indexOf('모바일') >= 0) return false;
    return !SEAFOOD_CATEGORY.test(cat);
  }
  /* 생물 여러 가지를 파는 글에 가공품이 하나 섞인 경우 */
  function speciesIds(t) {
    var ids = {};
    findHits(mask(t || '')).forEach(function (h) { h.rules.forEach(function (r) { ids[r.id] = 1; }); });
    return Object.keys(ids);
  }
  function mixedFreshList(title) {
    var t = title || '';
    if (!MIXED_FRESH.test(t)) return false;
    if ((t.match(/[,·\/]/g) || []).length >= 3) return true;
    return speciesIds(t).length >= 2;
  }
  /* 수입산 판단 (PC 앱 imported_reason과 같음) */
  var MOSTLY_IMPORTED_IDS = { myeongtae: 1, yeoneo: 1 };
  /* 양식 판단 (PC 앱 farmed_reason과 같음): 광어·우럭·참돔·전복·참가리비·톳·연어는 자연산이라고 밝히지 않으면 양식 */
  var MOSTLY_FARMED_IDS = { neopchi: 1, ureok: 1, chamdom: 1, jeonbok: 1, garibi: 1, tot: 1, yeoneo: 1 };
  function farmedReason(t, d) {
    t = t || ''; d = d || '';
    var text = t + '\n' + d;
    if (FARMED.test(t) && !NOT_FARMED.test(t)) return true;
    if (FARMED.test(d) && !NOT_FARMED.test(text) && !WILD.test(t)) return true;
    if (WILD.test(text)) return false;
    var ids = speciesIds(t);
    return ids.length > 0 && ids.every(function (i) { return MOSTLY_FARMED_IDS[i]; });
  }
  function importedReason(t, d, overseas) {
    t = t || ''; d = d || '';
    if (overseas) return true;
    if (IMPORTED.test(t) && !NOT_IMPORTED.test(t)) return true;
    if (IMPORTED.test(d) && !DOMESTIC.test(t) && !DOMESTIC.test(d) && !NOT_IMPORTED.test(d)) return true;
    if (!MOSTLY_IMPORTED.test(t) || DOMESTIC.test(t + '\n' + d) || /자연산|동해|강원|고성|속초|주문진/.test(t)) return false;
    var ids = speciesIds(t);
    return ids.length > 0 && ids.every(function (i) { return MOSTLY_IMPORTED_IDS[i]; });
  }
  /* 제목에 규제 어종이 5종 이상 나열되면 낚시용품 등 여러 어종용 상품으로 본다 */
  function manySpecies(title) {
    var ids = {};
    findHits(mask(title || '')).forEach(function (h) { h.rules.forEach(function (r) { ids[r.id] = 1; }); });
    return Object.keys(ids).length >= 5;
  }
  var DEFAULT_EXCLUDE = ['nonfood', 'processed', 'imported', 'farmed'];
  var EXCLUDE_LABEL = { notitle: '제목에 규제 어종 없음', nonfood: '수산물이 아닌 상품·판매자 홈', processed: '가공품', imported: '수입산', farmed: '양식' };
  var exclude = DEFAULT_EXCLUDE;
  var titleSpecies = true;  /* 제목에 규제 어종이 없는 글 빼기 (설정에서 끌 수 있음) */
  var excluded = {};
  function excludeReason(title, description, overseas, ex, link) {
    ex = ex || exclude;
    var t = title || '', text = t + '\n' + (description || '');
    if (ex.indexOf('nonfood') >= 0 && (NON_SEAFOOD.test(t) || isStoreHome(link, t) || manySpecies(t) || nonSeafoodCategory(t) || bareListing(t) ||
        (GEAR_WEAK.test(t) && !CATCH_SALE.test(t)))) return 'nonfood';
    if (ex.indexOf('processed') >= 0 && PROCESSED.test(text) && !mixedFreshList(t)) return 'processed';
    if (ex.indexOf('imported') >= 0 && importedReason(t, description, overseas)) return 'imported';
    if (ex.indexOf('farmed') >= 0 && farmedReason(t, description)) return 'farmed';
    return null;
  }
  function isTrade(title, description, tradeSite) {
    var t = title || '', d = description || '';
    if (NOT_TRADE.test(t)) return false;
    if (tradeSite || TRADE_WORDS.test(t) || CATCH_FRESH.test(t) || CONTACT.test(t)) return true;
    var saleD = TRADE_WORDS.test(d) || CATCH_FRESH.test(d) || CONTACT.test(d);
    return (saleD && PRICE_QTY.test(t + '\n' + d)) || (CATCH_FRESH.test(d) && CONTACT.test(d));
  }
  var ENT = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&apos;': "'", '&nbsp;': ' ' };

  function clean(s) {
    return String(s || '').replace(/<[^>]+>/g, '').replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, function (m, e) {
      if (e[0] === '#') {
        var n = (e[1] === 'x' || e[1] === 'X') ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
        return isFinite(n) ? String.fromCodePoint(n) : m;
      }
      var v = ENT[m.toLowerCase()];
      return v === undefined ? m : v;
    }).trim();
  }
  /* 링크가 어느 사이트인지. 꺼 둔 사이트는 null */
  function siteOf(link) {
    var m = /^https?:\/\/([^\/?#:]+)/i.exec(link || '');
    if (!m) return null;
    var host = m[1].toLowerCase().replace(/^(m|www)\./, '');
    var a = matchSite(host, API_SITES);
    if (a) return a;
    var s = matchSite(host, sites);
    return s && s.enabled !== false ? s : null;
  }
  function inSeasonRules(dateStr) {
    var d = dateStr.slice(5);
    return RULES.filter(function (r) {
      return r.yearRound || pickSeason(r, []).entries.some(function (e) { return inRange(d, e.f, e.t); });
    });
  }
  function uniq(a) { return a.filter(function (x, i) { return x && a.indexOf(x) === i; }); }

  /* 오늘 날짜와 설정으로 돌릴 검색 목록을 만든다: [{kind, query, sort}] */
  function plan(dateStr, cfg) {
    configure(cfg);
    var c = (cfg && cfg.collect) || {};
    var sources = c.sources || ['cafearticle', 'blog', 'webkr'];
    var seasonTerms = [];
    inSeasonRules(dateStr).forEach(function (r) {
      if (r.yearRound) return;
      r.al.slice(0, 4).forEach(function (a) { seasonTerms.push(a + ' 판매'); });
    });
    var extra = (c.extra_queries || []).map(function (q) { return String(q).trim(); }).filter(Boolean);
    /* 카페·블로그 검색은 '판매'를 붙여 판매·거래 글 위주로 찾는다 */
    /* '오늘 잡은 ○○'도 함께 찾는다 ('판매'라는 말 없이 갓 잡은 것을 내놓는 글) */
    var species = uniq(RISK_TERMS.concat(seasonTerms.map(function (t) { return t.replace(' 판매', ''); })));
    var queries = uniq(RISK_TERMS.map(function (t) { return t + ' 판매'; }).concat(seasonTerms,
      species.map(function (t) { return '오늘 잡은 ' + t; }), extra));
    var core = uniq(RISK_TERMS.concat(seasonTerms.map(function (t) { return t.replace(' 판매', ''); }), extra));
    var out = [];
    queries.forEach(function (q) {
      sources.forEach(function (s) { if (s === 'cafearticle' || s === 'blog') out.push({ kind: s, query: q, sort: 'date' }); });
    });
    if (sources.indexOf('webkr') >= 0) {
      var words = [];
      sites.forEach(function (x) {
        if (x.enabled === false) return;
        String(x.query || x.name).split(',').forEach(function (w) { w = w.trim(); if (w && words.indexOf(w) < 0) words.push(w); });
      });
      core.forEach(function (t) { words.forEach(function (w) { out.push({ kind: 'webkr', query: t + ' ' + w, sort: '' }); }); });
    }
    var max = parseInt(c.max_calls, 10) || 800;
    return out.slice(0, max);
  }

  var seen = {};
  var order = [];
  var dropped = {};
  function reset() { seen = {}; order = []; dropped = {}; excluded = {}; }

  /* 검색 API 응답(JSON 문자열) 하나를 받아 판매글 후보를 쌓는다 */
  function ingest(kind, query, text) {
    var data;
    try { data = typeof text === 'string' ? JSON.parse(text) : text; } catch (e) { return 0; }
    var n = 0;
    (data.items || []).forEach(function (it) {
      var link = it.link || '';
      var hit = siteOf(link);
      var site = hit ? hit.name : ({ cafearticle: '네이버 카페', blog: '네이버 블로그' })[kind];
      if (!site || seen[link] || dropped[link]) return;
      var title = clean(it.title), description = clean(it.description);
      if (!isTrade(title, description, hit && hit.trade)) { dropped[link] = 1; return; }
      /* 판매글이면 파는 수산물 이름이 제목에 있다: 제목에 규제 어종(별명·상호 제외)이 없으면 뺀다 */
      var why = (!titleSpecies || findHits(mask(title)).length) ? excludeReason(title, description, hit && hit.overseas, null, link) : 'notitle';
      if (why) { dropped[link] = 1; excluded[why] = (excluded[why] || 0) + 1; return; }
      var pd = /^\d{8}$/.test(it.postdate || '') ? it.postdate.slice(0, 4) + '-' + it.postdate.slice(4, 6) + '-' + it.postdate.slice(6) : null;
      var extra = {};
      ['cafename', 'bloggername'].forEach(function (k) { if (it[k]) extra[k] = clean(it[k]); });
      seen[link] = { link: link, title: title, description: description, site: site, overseas: !!(hit && hit.overseas), source: kind, query: query, post_date: pd, extra: extra };
      order.push(link);
      n++;
    });
    return n;
  }

  function compact(r) {
    return {
      sev: r.sev, regions: r.regions,
      findings: r.findings.map(function (f) {
        return { id: f.rule.id, name: f.rule.n, law: f.rule.law, aliases: f.aliases, items: f.items, sev: f.sev, gauge: f.gauge };
      })
    };
  }

  /* 해외 판매 사이트 상품은 수입품이므로 국내 포획 규제의 '위반 의심'으로 올리지 않는다 */
  var SEVN = { ok: 0, info: 1, warn: 2, danger: 3 };
  function overseasCap(c, siteName) {
    c.findings.forEach(function (f) {
      if (f.sev === 'danger') f.sev = 'warn';
      f.items.forEach(function (i) { if (i.sev === 'danger') i.sev = 'warn'; });
      f.items.push({ sev: 'info', txt: siteName + '은(는) 해외 판매 사이트라 상품이 수입품일 가능성이 큽니다. 금어기·금지체장은 국내 해역 포획물에 적용됩니다.' });
    });
    c.sev = c.findings.reduce(function (a, f) { return SEVN[f.sev] > SEVN[a] ? f.sev : a; }, 'ok');
  }

  /* 쌓인 후보를 판독해 어종이 걸린 글만 돌려준다 */
  function finish(dateStr, region) {
    var out = [];
    order.forEach(function (link) {
      var it = seen[link];
      var r = analyzePost(it.title + '\n' + it.description, it.post_date || dateStr, region || '');
      if (!r.findings.length) return;
      var c = compact(r);
      if (it.overseas) overseasCap(c, it.site);
      out.push({ link: it.link, title: it.title, description: it.description, site: it.site, source: it.source,
        query: it.query, post_date: it.post_date, extra: it.extra, sev: c.sev, findings: c.findings });
    });
    return out;
  }

  function excludedSummary() {
    return Object.keys(excluded).map(function (k) { return EXCLUDE_LABEL[k] + ' ' + excluded[k]; }).join(' · ');
  }
  return { excludeReason: excludeReason, excludedSummary: excludedSummary, DEFAULT_EXCLUDE: DEFAULT_EXCLUDE, isTrade: isTrade, DEFAULT_SITES: DEFAULT_SITES, configure: configure, normDomain: normDomain, plan: plan, ingest: ingest, finish: finish, reset: reset, compact: compact,
    count: function () { return order.length; }, inSeasonRules: inSeasonRules };
})();
if (typeof module !== 'undefined') module.exports = { analyzePost: analyzePost, RULES: RULES, FW_PIPE: FW_PIPE };
