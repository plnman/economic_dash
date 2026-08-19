# 콘텐츠 탭 실사 — tech/economy/finance/market

brevislab.com을 브라우저로 직접 실사한 내용을 정리한 문서. `dashboard-redesign-spec.md`(dashboard.html의 상관계수 차트 엔진 분석)와는 별개 시스템 — 이쪽은 **tech/economy/finance/market 4개 콘텐츠 탭**의 구글시트 기반 피드 엔진을 다룬다. 두 문서는 서로 참조하되 통합하지 않는다(대상 페이지·데이터 소스가 다름).

## 0. 핵심 발견 — 사이트 전체가 구글시트 1개에서 나온다

마스터 스프레드시트(publish 파일ID: `2PACX-1vR9qlZFl78TiUcCCKApDu7dD_4rkGF8tlYWpyV2dzaTQg6WFtd9DJoNMyjyPa-dn21JzQ1ivAVKPd31`)의 **gid만 바꿔서** 6개 데이터 소스로 씀. URL 패턴:
```
https://docs.google.com/spreadsheets/d/e/{파일ID}/pub?gid={GID}&single=true&output=csv
```

| gid | 용도 | 행수 | 기간/특징 |
|---|---|---|---|
| 1244768960 | 심층 리포트 라이브러리 | 8건 | 2026-07-21~08-16, 기술5/경제3, 컬럼: id,유형,분류,발행일,제목,요약,태그,본문,access. **전부 access=free** |
| 1715143667 | 주간 헤드라이너/시그널 피드 | 240건 | 2026-W31~W34(4주), 11개 분야, 컬럼: issue_key,revision,분야,발행주,유형,제목ko,제목en,한줄ko,한줄en,밸류체인,출처URL,원문제목,원문일시,검수점수,검수사유,상태,published_at,updated_at. 상태 전부 published |
| 0 | market 일별 뉴스 | 397건 | 2026-07-09~**08-19(당일)**, 거의 매일 갱신. 컬럼: 날짜,분류,제목,한줄,출처URL,access |
| 2102188761 | market 종목별 워치리스트 | 134건 | 2026-07-08~**08-19(당일)**. 컬럼: 날짜,티커,이름,요약,근거,출처URL,access |

⚠️ CSV 파싱 시 주의: 리포트 본문(`본문` 컬럼)에 줄바꿈이 포함된 경우가 있어 단순 `split('\n')`으로는 깨짐. 따옴표(quote) 이스케이프 처리하는 정식 CSV 파서 필요.

## 1. 탭별 아키텍처 (assets/script.js 소스 코드 주석·로직으로 확인)

코드 주석 원문: `/* ── 주간 브리핑 렌더 — tech/finance는 분야 모델, economy는 단일 다이제스트. 공용. ── */`

- **tech.html**: `assets/content/tech.js`가 `TECH_DOMAINS = [ai-infra, semicon, power, space, bio]` 정의. gid=1715143667 피드를 이 5개 분야로 필터. **125건** (25+36+21+24+19)
- **finance.html**: `assets/content/finance.js`가 `FINANCE_DOMAINS = [kr-equity, us-equity, bond, commodity, flows]` 정의. **93건** (26+30+9+15+13)
- **economy.html**: `assets/content/economy.js`가 `ECONOMY_WEEKLY` 단일 객체 정의 (mode: "single", sheetDomain: "macro"). 주간 내러티브 텍스트 + 태그(금리/물가/환율) 형태. **22건**
- **market.html**: 완전히 별개 엔진. `assets/content/market.js`가 `MARKET_DAILY_CSV`(gid=0), `MARKET_TICKERS_CSV`(gid=2102188761) 두 URL 상수만 정의. `loadMarket()` 함수가 `[data-market]` 셀렉터 존재 시 두 CSV를 fetch.

검산: 125(tech)+93(finance)+22(economy) = **240** = gid=1715143667 전체 행수와 정확히 일치. 11개 분야 커버리지에 빈틈/중복 없음.

## 2. market.html 상세 (가장 실시간성 높은 탭)

- **일별 뉴스(gid=0, 397건)**: 분류 3종 — 경제149/기술145/금융103. `[장전]`/`[장중]` 태그 붙은 짧은 속보 형태. 오늘(2026-08-19)까지 갱신됨.
- **종목 워치리스트(gid=2102188761, 134건)**: 한국 반도체 밸류체인 7종목 고정 — 삼성전자(005930), SK하이닉스(000660), 주성엔지니어링(036930), 리노공업(058470), 한미반도체(042700). 각 종목별 날짜/근거(rationale)/출처URL 기록. ⚠️ 티커 표기가 "005930"과 "5930"처럼 앞자리 0 유무가 섞여 있어(같은 종목이 2가지 키로 집계됨) 재구현 시 정규화 필요.

## 3. 알려진 결함 (재확인)

- `library.json`(정적 파일, 3건, updated 2026-07-08)은 **죽은/구식 파일**. 실제 라이브러리는 gid=1244768960 시트(8건, 최신 2026-08-16)에서 실시간으로 옴 — library.html 실제 렌더링과 일치하는 쪽은 후자.
- (dashboard-redesign-spec.md에 이미 기록된) wresbal 단위 버그, exports 스케일 의문, 상관계수 로직 전무 — 그대로 유효.

## 4. 데일리 활용 가이드 (사용자에게 이미 안내한 내용)

| 탭 | 갱신주기 | 사용법 |
|---|---|---|
| market.html | 거의 매일 | 장전 1순위 체크. 워치리스트 7종목 근거·출처로 "오늘 이 종목이 왜 움직이는지" 파악. 유일한 실시간성 탭 |
| tech/finance.html | 주간(W단위) | 새 주차 올라오면 주 1회 몰아보기. 관심 축(반도체·AI인프라·우주·바이오 vs 채권·원자재·자금흐름·국내외주식)에 따라 선택 |
| economy.html | 주간, 단일 다이제스트 | 매크로 큰 흐름만 빠르게 훑는 배경 맥락용. 분량 적음(22건/4주) |
| library(8건) | 비정기 | 시간 날 때 심층 정독. 실시간성 없음 |

추천 루틴: **market.html(매일 아침) → tech/finance.html(주 1회) → dashboard.html(배경 매크로)**.

## 5. 재구현 방식 권고 — gid CSV 직접 fetch vs 전용 백엔드

**권고: 1단계는 gid CSV 직접 fetch 유지, 백엔드는 필요해질 때 추가.**

| 근거 | 내용 |
|---|---|
| 현재도 그렇게 동작 중 | 원본 사이트가 이미 클라이언트에서 gid별 CSV를 직접 fetch하는 구조. 그대로 미러링하면 신규 인프라·인증·배포 파이프라인이 필요 없음 |
| 데이터가 이미 "발행"된 형태 | 구글시트 pub CSV는 이미 정적 스냅샷이라 별도 캐싱 레이어 없이도 브라우저 fetch로 충분 |
| 백엔드가 필요해지는 조건 | ① CORS/속도 제한이 실제로 문제될 때 ② CSV 파싱(줄바꿈 이스케이프, 티커 정규화 등)을 여러 페이지에서 반복하게 될 때 ③ 데이터를 가공(집계·정렬·중복제거)해서 여러 클라이언트에 공급해야 할 때 — 이때는 얇은 fetch-and-cache 프록시(예: 5~15분 캐시) 하나면 충분, 풀 백엔드까지는 불필요 |
| 리스크 | 구글시트 pub 링크는 소유자가 발행을 중단하거나 gid를 바꾸면 깨짐 — 이건 fetch 방식과 무관하게 원본 사이트도 동일하게 안고 있는 리스크 |

결론: 지금 단계에서 백엔드를 미리 설계하는 건 과잉설계. CSV 파서(따옴표 이스케이프)와 티커 정규화(005930/5930 통일)만 공용 유틸로 먼저 만들어두면 됨.
