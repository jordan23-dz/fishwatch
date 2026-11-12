# FishWatch Android — Play 스토어 출시 가이드

온라인 수산물 판매글을 수산자원관리법 시행령 금어기·금지체장 기준으로 점검하는 Android 앱입니다. PC 앱과 판정 로직이 같습니다(`app/src/main/assets/engine.js`).

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `app/src/main/assets/index.html` | 앱 화면 (점검 현황·직접 판독·기준표·설정) |
| `app/src/main/assets/engine.js` | 판독 규칙 51종 + 검색 계획·결과 처리 |
| `app/src/main/java/kr/fishwatch/checker/` | 화면 띄우기, 네이버 API 호출, 저장(SQLite), 매일 자동 점검(WorkManager), 알림 |
| `store/` | Play 등록용 아이콘·그래픽·스크린샷·설명문·개인정보처리방침 |
| `.github/workflows/build-android.yml` | GitHub에서 시험용 APK·Play용 AAB 자동 빌드 (저장소 맨 위 `.github/workflows/`에 두어야 동작) |

기술 사양: targetSdk 36(2026-08-31 Play 요건 충족), minSdk 26(Android 8.0 이상), AGP 8.13.2, Gradle 8.14.3, Java 17.

## 1단계. 출시 전에 바꿀 것 (3곳)

1. **패키지 이름** — `app/build.gradle`의 `applicationId 'kr.fishwatch.checker'`. Play에 한 번 올리면 영원히 못 바꿉니다. 원하는 이름이 있으면 지금 바꾸세요(예: `com.내이름.fishwatch`).
2. **개인정보처리방침** — `store/privacy-policy.html`의 `[개발자 이름]`, `[연락처 이메일]`을 채우고 공개 주소에 올립니다(GitHub Pages, Google Sites, Notion 공개 페이지 등). PDF는 안 됩니다.
3. **앱 안의 방침 링크** — `app/src/main/assets/index.html`에서 `const PRIVACY_URL='';`에 2번 주소를 넣습니다.

## 2단계. AAB 파일 만들기 (Android Studio)

1. [Android Studio](https://developer.android.com/studio) 설치 → **Open** → 이 폴더 선택. 처음 열면 필요한 SDK를 자동으로 내려받습니다(몇 분).
2. 휴대폰을 USB로 연결(개발자 옵션 → USB 디버깅 켜기)하고 ▶ Run으로 먼저 실제 기기에서 확인합니다. **예시로 시험** → 키 입력 → **지금 점검** 순서로 확인하세요.
3. 메뉴 **Build → Generate Signed App Bundle or APK → Android App Bundle**
4. **Create new...** 로 업로드 키(.jks)를 만듭니다. 이 파일과 비밀번호는 **절대 잃어버리지 말고** 안전한 곳에 백업하세요(업데이트 때마다 필요).
5. **release** 선택 → Create. 결과물: `app/release/app-release.aab`

Android Studio 없이 만들려면 이 폴더를 GitHub 저장소에 `android` 폴더로 올리고, `build-android.yml`을 저장소의 `.github/workflows/`에 둔 뒤 Actions에서 **Build Android → Run workflow**를 누르면 시험용 APK가 나옵니다. Play용 AAB는 파일 상단 설명대로 비밀값 4개를 등록하면 함께 만들어집니다.

## 3단계. Play Console 등록

1. [Play Console](https://play.google.com/console) 개발자 계정 생성 — 등록비 25달러(1회), 신분증 인증, (2023-11-13 이후 개인 계정은) 실제 Android 기기 인증
2. **앱 만들기** → 기본 언어 한국어, 앱, 무료
3. `store/스토어-등록정보.md`대로 스토어 등록정보·앱 콘텐츠·데이터 보안 양식 작성
4. **비공개 테스트** 트랙 생성 → AAB 업로드 → 테스터 이메일 목록 등록 → 참여 링크 공유
5. **테스터 12명 이상이 14일 연속 참여** (2023-11-13 이후 만든 개인 계정 필수, 내부 테스트 트랙은 인정 안 됨)
6. 14일이 지나면 **프로덕션 액세스 신청** → 질문지 작성 → 보통 7일 안팎 심사
7. 승인 후 프로덕션 트랙에 출시

조직(사업자) 계정은 5번 비공개 테스트 요건이 없습니다.

## 업데이트할 때

`app/build.gradle`의 `versionCode`를 1씩 올리고(`versionName`도 함께), 같은 업로드 키로 서명해 올립니다. 시행령이 개정되면 `engine.js`의 `RULES` 배열만 고치면 됩니다.

## 알려진 한계

- 첫 빌드는 GitHub Actions에서 하게 됩니다. 오류가 나면 실패한 단계의 로그를 그대로 알려 주세요.
- 판독 엔진은 Android System WebView의 격리 JavaScript 엔진(JavaScriptSandbox)으로 백그라운드 점검을 돌립니다. WebView가 아주 오래된 기기에서는 점검 화면에 업데이트 안내가 뜹니다.
- 자동 점검 시각은 Android 절전 정책에 따라 조금 늦어질 수 있습니다.
