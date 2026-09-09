# context-search 고도화 — 적대적 검토와 적용 플랜

- 작성: 2026-09-08 · 브랜치 `claude/dp-skills-context-search-enhance-qp02xo`
- 입력: 작업 지시 v1(요구사항 5개) · v2(파트 A 5항 + 파트 B 2단계 선별 지침)
- 대상: `pilot/tools/context-search.py`. 지시서의 `dp-skills` 경로, 함수명 `parse_frontmatter_description`·`_word_boundary_hit`, 문서 `docs/reference/tools/context-search.md` 는 이 저장소에 없다. 실제 이름은 `split_sections` 안의 `_DESCRIPTION_RE`, `boundary_search` 이고 reference 문서는 `docs_build.py` 가 모듈 docstring 에서 생성하는 gitignore 대상이다. 동일 엔진으로 가정하고 pilot 경로 기준으로 쓴다.
- 기준선: `python3 -m unittest pilot/tests/tools/test_context_search.py` 87/87 · `discover -s pilot/tests/tools` 603/603 · Python 3.11 (CI 3.12)
- 설계 SSOT: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` · features #27~#30 · `27-context-search-tool.plan.md` D1~D8 · critic C1~C8
- 상태: **적용 완료 + critic 합의 반영** (2026-09-08 — 사용자 결정 E1~E11 승인 · pilot 우선 검증 · red-team 12건 처리) → § 4

## 0. 한 줄 결론

효과가 있는 것은 **B(2단계 선별 지침)** 와 그것을 받쳐주는 **A5(`select:` 다중 + `--inject`)** · **A4(manifest)** 다. **A3(mtime 점수)** 는 기각, **A1(type/sources 점수)** 은 점수가 아니라 출력 필드 + glob 보너스로 재설계, **A2(복합어)** 는 방향을 뒤집어 축소 채택한다. 점수표를 건드리는 항목은 A2 하나로 줄이고 나머지는 출력·프로토콜 층에서 푼다.

## 1. 판정표

| 항목 | 지시 내용 | 판정 | 핵심 근거 |
|---|---|---|---|
| A1 | frontmatter `type` +4 · `sources` 세그먼트 +5 | **재설계** — 점수 X. 출력 필드 + `sources` glob 보너스(역방향 경로 질의 한정) | 코퍼스 전체 frontmatter 0건(#29 미구현) · `type` 은 영문 enum 8종이라 한글 질의 0매칭 · `sources` 세그먼트는 path(8)·citation(6) 과 중복 · 파일 단위 신호 누적이 섹션 랭킹을 뒤집음 · #29 예시의 트레일링 `# 주석` 이 정규식 파서 함정 |
| A2 | 인접 토큰 결합어 +3 | **축소·방향 수정 채택** — 본문·description 한정, 양방향, 가중치 2, 중복 가산 금지 | 헤딩은 부분일치가 이미 처리(실측 15점) · 실제 hit@3 이 깨지는 방향은 "붙여 쓴 질의 ↔ 띄어 쓴 본문" 인데 제안은 반대 방향만 해결 · 불용어 제거 뒤 인접쌍은 거짓 결합 |
| A3 | mtime 신선도 ≤1.0 | **기각** — `age_days` 정보 표기로만 | 결정성 위반(clone/CI 는 전 파일 mtime 동일, 날짜 경과로 점수 표류) · 정수 score 스키마 파괴 · #28 사용자 확정은 "힌트" · memdir 도 mtime 을 나이 표시·절단 순서에만 사용 |
| A4 | `--format manifest` | **채택(얇게)** | 현재 md 표와 정보량 차이 거의 없음. "1줄 요약" 은 섹션 단위 출처가 없어 heading·matched·snippet 80자로 대체 |
| A5 | `select:` 다중 + `--inject` | **채택(상한 필수)** | 결정적·랭킹 무영향. 단 병렬 Read 대비 턴 절감은 0에 가깝고 가치는 "헤딩 주소 지정 1회 호출" 의 프로토콜 단순화 |
| v1-R4 | 키워드 검색 상위 N 본문 자동 주입 | **기각** (A5 로 대체) | "도구가 좁히고 AI 가 고른다" 원칙 위반, 매 호출 12KB 소모 |
| B | 2단계 선별 지침 | **채택(수정)** | 형태는 옳음. `--scope` 누락 · rules/boundary 를 "과감히 버리는" 정책 위험 · 서브에이전트에는 "대화 히스토리" 가 없음 · 배선 파일이 범위에 없으면 효과 0 |

## 2. 항목별 적대적 검토

### A1. frontmatter 다차원 점수

실측 사실:

- `workspace/context/**/*.md` 8개와 fixture 6개 모두 frontmatter 키 0개. `description` 조차 없다. #29 가 머지되기 전까지 A1 은 실행되지 않는 코드다.
- #29 규칙: `scope/{domain}.md`·`rules/{domain}.md` 는 사용자 커스텀 layer 라 frontmatter 강제 대상이 아니다. 지시서 예시 파일 `scope/retail.md` 가 바로 그 부류다.
- `type` 값은 `index|routes|models|services|rules|enums|boundary|free`. 한글 질의 `서비스`·`규칙` 은 정확일치 불가, 단수 `service` 도 불가.
- `sources: app/services/wms/**` 의 세그먼트 토큰 `app`·`services`·`wms` 는 본문 인용 `app/services/wms/x.rb:12` 의 citation 토큰과 같고 도메인 폴더 `wms/` 의 path 토큰과 같다. `boundaries/wms--schoice.md` 도 파일명에 도메인이 있다. pilot 레이아웃에서 `sources` 세그먼트가 새로 잡는 파일은 없다. `app` 같은 공통 접두는 모든 파일에 +5 를 주는 노이즈다.
- `type: services            # index | routes | ...` (#29 예시 그대로)를 `^type:\s*(.+)$` 로 읽으면 enum 8단어 전부가 모든 파일의 type 토큰이 된다.

구조적 문제 — 파일 단위 신호 누적:

| 층위 | 현재 토큰당 최대 | A1 적용 후 |
|---|---|---|
| 파일 단위 (path 8 + description 4 [+ type 4 + sources 5]) | 12 | 21 |
| 섹션 단위 (heading 10 + citation 6 + body 2) | 18 | 18 |

파일 단위가 섹션 단위를 넘으면 "어느 파일이냐" 가 "어느 섹션이냐" 를 이긴다. critic C2 가 서문 decoy 6개(57점)를 잡아낸 것과 같은 현상이 재발한다. 같은 파일의 모든 섹션이 동일 보너스를 받아 top-5 를 한 파일이 채우는 형태로 나타난다.

재설계:

- `type`·`domain` 은 파싱해 **출력 필드**로 노출한다(B 의 2차 판단 입력). `sources` 는 파싱하되 E7 보너스 전용이며 JSON 에는 싣지 않는다 (critic C12-d 정정). `type`·`domain` 은 점수 X.
- `sources` 는 glob 이다. 역방향 경로 질의(`raw_paths`)가 glob 에 `fnmatch` 되면 기존 인용 경로 suffix 보너스와 같은 층위의 파일 보너스 1회. 토큰 세그먼트 매칭 X.
- `domain` 은 `--scope` 소속 판정에 쓰는 것이 맞는 자리다(폴더 밖 파일 편입). #29 이후 별도 결정.

### A2. 한글 복합어

실측 (fixture, `--scope pilot`, 2026-09-08):

| 질의 | 결과 |
|---|---|
| `도메인 진입 파일 자동 로드` (골든 Q4) | `index.md ## Cluster 진입` 14점 1위 |
| `도메인 진입파일 자동 로드` | 정답 top-3 이탈 (`진입파일` 히트 0, 1위 `lifecycle.md /pilot:project` 6점) |
| `진입파일` · `정합성검사` | 0건 (fixture 본문은 `진입 파일`·`정합성 검사` 로 띄어 씀) |
| score_text: heading=`선발송접수 상태값`, 질의 `선발송 접수 상태` | 15점 (헤딩 부분일치가 이미 처리) |
| score_text: body=`선발송접수 상태값 확인`, 같은 질의 | 4점 (`접수` 만 누락, 좌측 경계 규칙으로 `선발송` 은 매칭) |
| score_text: 질의 `선발송접수`, body 또는 heading `선발송 접수 상태` | 0점 |

- 지시서 방향(띄어 쓴 질의 → 붙여 쓴 본문)은 헤딩에서 이미 해결돼 있고 본문에서만 +2 손실이다. 반대 방향(붙여 쓴 질의 → 띄어 쓴 본문)은 헤딩·본문 모두 0점이며 골든 hit@3 이 실제로 깨진다. 이것이 Open Q (d)-2 의 재검토 조건("골든 hit@3 부족 시에만 보강") 을 처음 충족하는 사례다.
- 인접쌍을 `tokenize` 결과에서 만들면 불용어가 빠진 뒤라 `선발송 및 접수` 도 `선발송접수` 가 된다. 원문 공백 분리 단어에서 만들어야 한다.
- 가중치 3 을 개별 히트 위에 누적하면 붙여 쓴 본문(2+3=5) 이 띄어 쓴 본문(2+2=4) 을 이긴다. 역전이다. 가중치 = body(2) 이고 중복 가산 금지면 4 = 4.
- 결합어 히트가 `matched`·`token_hits`·`+필수어` 게이트(D6)에 반영되지 않으면 `+접수 선발송` 은 여전히 0점이다.
- `score_text` 는 `confluence.py` 가 공유한다(C4). 시그니처를 바꾸지 않고 `Query` 에 결합어를 실어야 한다.

### A3. mtime 신선도

- 도구 docstring 의 보증: "같은 코퍼스·질의 → 같은 출력·순서". mtime 은 내용이 아니다. 실측: 라이브 코퍼스 6파일 mtime 전부 `2026-09-02 05:27:08`(clone 시각), git 상 마지막 내용 변경은 전부 `2026-08-01`. fixture 6파일은 전부 `2026-09-08 06:42:02`(오늘 checkout). 두 경우 모두 신선도는 상수다.
- `/pilot:learn` 은 도메인 폴더를 통째로 재생성하고 knowledge-sync 는 사이클 종료마다 문서를 갱신한다. 도메인 안에서 mtime 차이는 거의 없고 도메인 사이 차이는 `--scope` 가 이미 지운다.
- 경과 일수 기반이면 아무것도 바뀌지 않아도 날짜가 지나면 점수가 변한다. `test_determinism_same_directory_reversed_creation_order` 는 두 코퍼스를 밀리초 차이로 쓰므로 실수 일수 계산이면 JSON 이 달라져 flaky 가 된다.
- `score` 가 float 이 된다. JSON 타입·md 표·confluence 공유 함수까지 번진다. "동점·유사 점수 보정" 이 목적이면 점수가 아니라 `rank()` 정렬 키가 맞는 자리인데 그것도 clone 마다 순서가 달라진다.
- 벤치마크 오독: memdir 은 mtime 을 매니페스트의 `(age)` 표기와 200개 절단 시 최신순 정렬에만 쓴다. 관련도 점수에는 넣지 않는다. #28 도 2026-09-04 사용자 승인으로 "힌트" 로 확정됐고 `learned_at` 은 스키마에서 삭제됐다.
- 결론: `age_days` 를 manifest 줄에 정보로만 싣는다. 판단은 B 의 AI 가 한다.

### A4. manifest

- 현재 md 출력은 이미 `# | file | heading | lines | score | matched` 표 + snippet + read_hint 다. manifest 가 빼는 것은 표 골격뿐이다.
- 예시의 `(요약: 선발송 접수 시 유효성 검증 규칙)` 은 섹션 단위 요약이다. 이런 데이터는 어디에도 없다. #29 의 `description` 은 파일 단위라 같은 파일의 섹션 8줄에 같은 문장이 반복된다. 대체: `heading` + `matched` + snippet 앞 80자.
- 예시의 `score=18.5` 는 A3 의 float 를 전제한다. A3 기각과 함께 정수로 둔다.
- 가치는 "B 의 2차 판단 입력을 후보당 1줄로 고정" 하는 데 있다. 얇게 만들고 `--limit` 상한 20 은 유지한다.

### A5. `select:` 다중 + `--inject` (v1-R4 포함)

- 턴 절감 주장: Claude Code 는 독립 도구 호출을 한 턴에 병렬 실행한다. `read_hint` 3개를 병렬 Read 하면 1턴이다. `--inject` 도 1턴. 절감은 "순차 Read 하는 습관" 을 막는 프로토콜 효과이지 도구 효과가 아니다. 프로토콜 §6 은 애초에 "1~2개 Read" 라 "3~5회" 전제는 실측이 없다.
- 그래도 채택하는 이유: 헤딩으로 주소 지정하는 1회 호출이 offset/limit 계산보다 지시를 따르기 쉽고, B 의 3단계 흐름을 한 명령으로 고정한다. 랭킹 무영향·결정적.
- 함정:
  - 현재 `select:` 는 경로 1개, 헤딩은 substring. `#접수` 가 섹션 여러 개에 걸리고 H2 본문은 하위 H3 본문을 포함한다(`test_h2_body_includes_nested_h3`). 부모·자식을 함께 고르면 본문이 중복 주입된다. 라인 범위 포함 관계로 dedupe 해야 한다.
  - 400줄 초과 섹션은 read_hint 가 "재질의 권장" 을 내는데 inject 는 잘라야 한다. 잘린 사실과 나머지 Read 힌트를 명시하지 않으면 AI 는 전체를 봤다고 믿는다.
  - 이 세션에서 Bash 출력 45.8KB 가 파일로 스왑되고 2KB 미리보기만 남는 것을 관찰했다. `--max-bytes` 를 크게 주면 inject 의 목적이 무너진다. 하드 상한 24,000B.
  - v1-R4 처럼 키워드 검색 상위 N 을 자동 주입하면 AI 의 선택 단계가 사라진다. 계획서 §0.4 "도구가 후보를 좁히고 AI 가 선택" 위반. 키워드 + `--inject` 는 허용하되 기본 limit 3, 프로토콜 기본은 `select:` 경유.

### B. 2단계 선별 지침

- 형태는 옳다. 랭커의 구조적 약점(파일 단위 decoy·한글 토큰화)을 실제 맥락이 있는 단계에서 보정한다. 점수표 조정 5개보다 이 한 항목의 기대 효과가 크다.
- 수정 필요:
  - 명령에 `--scope {domain}` 이 없다. scope 없이 검색하면 도메인 밖 decoy 가 섞인다. 경로도 `${CLAUDE_PLUGIN_ROOT}/tools/...` 여야 한다.
  - "직접 관련 없는 섹션은 과감히 버린다" 는 P1(불확실하면 제외) 를 그대로 옮긴 것인데, 지식 계층의 존재 이유는 G3 "규칙 누락 → 평가 단계 반려" 방지다. `rules`·`boundary` 유형은 필수어가 맞으면 버리지 않는 예외가 필요하다. 이 판단에 A1 의 `type` 출력 필드가 쓰인다.
  - "최근 대화 히스토리·코드 수정 맥락" 은 메인 에이전트의 것이다. pilot 의 planner·generator·evaluator 는 서브에이전트라 호출 프롬프트만 받는다. 지침은 두 벌 필요: wrapper-protocol §6(서브에이전트, 맥락 = feature 명세·plan) 과 `/pilot:ask`(메인 에이전트).
  - 후보 8개 중 관련 0개일 때의 행동이 없다. "질의를 넓혀 1회 재검색, 그래도 0 이면 진입 파일 목차로 회귀" 를 명시해야 맹목 진행을 막는다.
  - 선별 결과와 사유 1줄 보고를 넣어야 dogfooding 에서 효과를 측정할 수 있다.
  - v1 의 변경 파일 3개에는 배선 문서가 없다. 플래그를 아무도 쓰지 않으면 효과는 0 이다. v2 가 `skills/` 를 넣은 것은 맞다.

### 공통

- 하위 호환: 필수 키 유지는 쉽다. 위험은 `score` 타입(A3)과 `score_text` 공유(A2). 새 키는 값이 있을 때만 넣어 frontmatter 없는 코퍼스의 JSON 을 바이트 단위로 동일하게 유지한다.
- 측정 부재: 두 지시서 모두 완료 기준이 "테스트 통과" 뿐이다. 가중치 4·5·3·1.0 은 보정 근거가 없다. #27 은 골든 hit@3 + 라이브 실측 + critic 을 거쳤다. 같은 게이트를 건다.
- 스펙-코드 불일치: 함수명·문서 경로가 이 저장소와 다르다. dp-skills 가 분기했더라도 랭커 엔진이 같으면 본 검토는 그대로 적용된다.

## 3. 적용 플랜

### 3.0 원칙

- 점수표 변경은 A2 하나. 나머지는 출력·프로토콜 층.
- 모든 단계에서 골든 4질의 hit@3 유지 + 기존 md/json 출력 바이트 동일(Phase 0 스냅샷 대조).
- 표준 라이브러리만. 실행 간 캐시 없음. 읽기 전용. 전역 가변 상태 없음.
- Phase 1(출력) → Phase 2(랭킹) → Phase 3(frontmatter) → Phase 4(배선) 순. Phase 마다 독립 커밋.

### 3.1 결정 사항 (사용자 확인으로 뒤집을 수 있음)

| # | 결정 | 근거 |
|---|---|---|
| E1 | `score` 는 정수 유지. mtime 은 점수·정렬 어디에도 넣지 않는다. `age_days` 는 manifest 줄에만 표기 | A3 검토 |
| E2 | 결합어 가중치 `W_COMPOUND = 2`(= body). 본문·description 에서 좌측 경계 검색. 헤딩 제외. 구성 토큰이 개별로 body 히트한 경우 그 토큰과 중복 가산하지 않는다 | 역전 방지 |
| E3 | 결합어는 원문 공백 분리 단어의 인접쌍 중 양쪽이 순수 한글 토큰 1개씩일 때만 생성. 불용어·1글자·ASCII 가 끼면 쌍을 끊는다 | 거짓 결합 방지 |
| E4 | 역방향: 질의 한글 토큰(길이 ≥ 4)이 개별 히트 0 이면 `compact`(한글 사이 공백 제거) 본문·헤딩에서 좌측 경계 검색. 본문 히트 = body 2, 헤딩 히트 = heading_partial 5 | Q4 변형 실측 |
| E5 | 결합어·compact 히트는 `matched`·`token_hits`·required 게이트에 구성 토큰 이름으로 반영. snippet 위치 계산도 compact 히트를 본다 | D6 유지 |
| E6 | frontmatter 파서: `description`·`domain`·`type` 스칼라 + `sources` 블록/인라인 리스트. 따옴표 밖 `#` 이후 제거. 미지 키 무시. 값 없으면 None 이고 JSON 키 생략 | 파서 함정, 바이트 동일 |
| E7 | `sources` 보너스: `raw_paths` 의 경로가 glob 에 `fnmatch.fnmatchcase` 되면 파일 보너스 `SCORE["citation"]`(6) 1회. 토큰 세그먼트 매칭 없음. `type`·`domain` 은 점수 없음 | A1 재설계. `**` 는 fnmatch `*` 가 `/` 를 포함하므로 그대로 동작. `pathlib.full_match` 는 3.13 전용이라 미사용 |
| E8 | `select:` 다중: `select:a.md#h1,b.md#h2` 쉼표 구분(P2 ToolSearch 규약). 헤딩 부분은 substring 이므로 쉼표 앞 접두만 쓰면 된다 | 헤딩에 쉼표가 흔하면 `--select` 반복 플래그로 전환 |
| E9 | `--inject`: 결과 순서대로 본문 주입. `--max-bytes` 기본 12,000·하드 상한 24,000(초과 시 클램프 + INFO). 섹션당 400줄 초과 또는 잔여 예산 초과 시 잘라내고 `[잘림 …]` 줄 + 나머지 read_hint. 같은 파일에서 라인 범위가 다른 선택 섹션에 포함되면 제외. 키워드 질의 + `--inject` 는 허용하되 `--limit` 미지정 시 3 | A5 함정 |
| E10 | `--format manifest` 줄: `[#n] {score} | {file} :: {heading} | L{start}-{end} | {age}d | matched: a,b | {snippet≤80}`. `type` 있으면 `[type]` 을 score 뒤에. 0건은 md 와 같은 안내 | A4 |
| E11 | 문서는 모듈 docstring 갱신 → `docs_build.py` 실행 → `--check`. `docs/reference/tools/` 는 생성물·gitignore 라 손대지 않는다 | 저장소 규약 |

### 3.2 변경 파일

- `pilot/tools/context-search.py` — `Query.compounds`·`Query.select_targets` · `_compact_hangul` · frontmatter 파서 · `Section.meta` · sources 보너스 · select 다중 · inject · manifest · docstring
- `pilot/tests/tools/test_context_search.py` — 신규 테스트 + 골든 2질의
- `pilot/tests/fixtures/context-search/README.md` — 골든 6질의 표기
- `pilot/skills/context/shared/wrapper-protocol.md` §6 — 3단계 프로토콜
- `pilot/skills/ask/SKILL.md` — 메인 에이전트용 동일 프로토콜 1절
- `pilot/tools/orchestrate-load.py` `:527` 힌트 1줄 — `--format manifest` 언급
- `pilot/tests/tools/test_orchestrate_load.py` — 힌트 문구 테스트 있으면 갱신
- `pilot/docs/release-notes.md` — 항목 1개 (버전은 사용자 결정)
- 불변: `confluence.py`(시그니처 유지로 자동 수혜) · `doctor/*` · `agents/*.md`(잔류 최소 셋 규칙)

### 3.3 구현 순서

**Phase 0 — 기준선 고정 (변경 없음)**

1. 골든 4질의 + 아래 2질의의 `--format json`·`md` 출력을 scratch 에 스냅샷.
2. 신규 골든 확정: Q5 `도메인 진입파일 자동 로드` → `index.md ## Cluster 진입` (현재 top-3 이탈, E4 로 복구 기대) · Q6 `doctor 정합성검사` → `lifecycle.md ## /pilot:doctor` (현재 통과, 회귀 감시용). 붙여 쓴 본문 케이스는 fixture 에 없으므로 단위 테스트로만 검증.

**Phase 1 — 출력 확장 (랭킹 무영향)**

3. `parse_query`: `select:` 쉼표 다중 → `Query.select_targets: list[tuple[str, str | None]]`. 기존 `select_path`·`select_heading` 은 첫 대상으로 채워 호환 유지.
4. `_select_result`: 대상별 매칭·부재 suggestions 합산.
5. `--inject`/`--max-bytes`: `results[i]["text"]`·`["truncated"]`, md 는 `<context-snippet file heading lines>` 블록, 속성값 따옴표 escape. E9 dedupe·절단.
6. `--format manifest` + `render_manifest`. `age_days` 는 파일당 `os.stat` 1회.
7. 테스트 12건 내외. `--inject`·manifest 미사용 시 출력 바이트 동일 확인.

**Phase 2 — 한글 양방향 결합 (E2~E5)**

8. `parse_query`: `compounds` 생성. `_compact_hangul(text)` 헬퍼.
9. `score_text`: 결합어 본문·description 검색, 역방향 compact 검색, matched 반영. 시그니처 불변.
10. `build_zero_hit`: 한글 토큰 0히트 시 "띄어쓰기/붙여쓰기 변형 재질의" 안내 1항 추가.
11. 골든 6/6 + 기존 4질의 점수 불변 확인 + confluence 테스트 6건.

**Phase 3 — frontmatter (E6·E7)**

12. `split_sections`: 블록 파서 확장. `Section.meta: dict`. 기존 `description` 필드·테스트 유지.
13. `score_text(..., sources=())` kwarg 추가(기본 빈 튜플 — confluence 코드 무변경. 단 같은 `parse_query`·`score_text` 를 쓰므로 한글 결합·역방향 규칙은 confluence 검색 거동에도 적용된다, critic C3). raw_paths glob 보너스.
14. 결과 JSON 에 `type`·`domain` 조건부 키. manifest `[type]`.
15. 합성 fixture(임시 디렉토리)로 테스트 8건. 라이브 코퍼스는 frontmatter 없어 출력 불변.

**Phase 4 — 배선 (B)**

16. wrapper-protocol §6 을 3단계로 교체(초안 §3.5). 잔류 최소 셋 규칙상 `agents/*.md` 는 손대지 않는다.
17. `/pilot:ask` 에 같은 절차 1절.
18. orchestrate-load 힌트 문구에 `--format manifest` 추가 + 테스트.
19. docstring → `docs_build.py` → `--check`. release-notes.

### 3.4 테스트 목록 (신규)

- parse_query: 쉼표 다중 select · 결합어 생성(한글쌍만·불용어 단절·ASCII 제외)
- score_text: 붙여 쓴 본문 결합어 +2 · 띄어 쓴 본문과 동점 · 역방향 본문 +2 · 역방향 헤딩 +5 · `+필수어` 결합 경유 통과 · 기존 신호 6종 값 불변
- frontmatter: 트레일링 주석 제거 · 따옴표 · 블록 리스트 · 인라인 리스트 · 부재 시 None 과 JSON 키 생략 · description 기존 테스트 유지
- sources: glob 일치 +6 · 불일치 0 · `**` 하위 경로
- select 다중: 2개 모두 · 1개 부재 시 나머지 반환 + suggestions
- inject: text/truncated 키 · 예산 초과 절단 문구 · 400줄 절단 · H2/H3 포함 dedupe · `--max-bytes` 클램프 INFO · 미지정 시 출력 바이트 동일 · 속성 escape
- manifest: 줄 형식 · 정수 score · snippet 80자 · 0건 안내 · select 와 병용
- CLI: `--format manifest` 수용 · `--inject` 기본 limit 3 · exit 코드 불변
- 골든: Q1~Q4 유지 · Q5·Q6 추가
- 결정성·성능 기존 테스트 통과

### 3.5 wrapper-protocol §6 초안

```
## 6. 본문 부분 로드 (권장 — 필수 step 아님)

1. 탐색: python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<feature 키워드>" --scope {domain} --format manifest --limit 8
2. 선별: 후보 8줄을 feature 명세·plan 의 현재 단계와 대조해 결정적인 1~3개만 고른다.
   - type 이 rules·boundary 인 후보는 필수어가 맞으면 버리지 않는다.
   - 관련 후보가 0 이면 질의를 넓혀 1회 재검색, 그래도 0 이면 진입 파일 목차로 회귀.
   - 고른 섹션과 사유를 1줄 보고한다.
3. 주입: python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "select:{file}#{heading},{file}#{heading}" --inject
   400줄 초과 섹션은 잘려 나오므로 출력의 read_hint 로 나머지를 Read 한다.
```

### 3.6 게이트

| G | 기준 |
|---|---|
| G1 | `python3 -m unittest discover -s pilot/tests/tools` 전부 통과. 신규 ≥ 30건 |
| G2 | 골든 hit@3 6/6. Q1~Q4 의 점수·순서가 Phase 0 스냅샷과 동일 |
| G3 | 라이브 코퍼스 같은 질의 2회 `--format json` diff 0. 1,000섹션 성능 테스트 < 1s |
| G4 | `--inject`·`--format manifest` 미사용 시 md/json 출력이 Phase 0 스냅샷과 바이트 동일 (frontmatter 없는 코퍼스) |
| G5 | `docs_build.py --check` 통과 · doctor 클린 |
| G6 | dogfooding 1건: 래퍼가 manifest → select --inject 흐름을 쓴 기록과 턴 수 |

### 3.7 제외 항목

- A3 mtime 점수·정렬 키 (E1)
- v1-R4 키워드 상위 N 자동 주입
- `type` 점수 · `sources` 세그먼트 점수
- `domain` frontmatter 로 `--scope` 확장 (#29 이후 별도 결정)
- 형태소 분석·일반 n-gram (Open Q (d)-2 유지, 결합어는 인접쌍 한정)

### 3.8 사용자 결정 필요

1. E1 (mtime 기각) 동의 여부.
2. E7 (`type` 점수 없음, `sources` 는 glob 보너스) 동의 여부.
3. E8 select 구분자 쉼표.
4. E2 결합어 가중치 2 (지시서 3).
5. Phase 4 의 `/pilot:ask` 포함 여부와 release-notes 버전.
6. dp-skills 가 실제 대상이면 경로 치환만으로 같은 플랜을 적용할지, 이 저장소 pilot 에 먼저 적용해 검증할지.

## 4. 적용 기록 (2026-09-08)

브랜치 `claude/dp-skills-context-search-enhance-qp02xo`, Phase 별 커밋 4건. 코드 변경은 `pilot/tools/context-search.py` 한 파일에 집중되고 `confluence.py` 는 `score_text` 시그니처 호환으로 무변경.

| 커밋 | Phase | 내용 |
|---|---|---|
| `770cc3e` | 1 | `select:` 다중 대상 · `--inject`/`--max-bytes` · `--format manifest` (테스트 +25) |
| `7aaff08` | 2 | 한글 결합어 양방향 E2~E5 · 골든 Q5·Q6 (+22) |
| `b2dfe7b` | 3 | frontmatter 파서 E6 · `sources` glob 보너스 E7 (+15) |
| `cf5f8b8` | 4 | wrapper-protocol §6 · `/pilot:ask` · orchestrate-load 힌트 · docstring · release-notes · select 경로 정규화 (+1) |

### 게이트 실측

| G | 결과 |
|---|---|
| G1 | `python3 -m unittest discover -s pilot/tests/tools` 603 → 666 통과. context-search 87 → 150 (+63) |
| G2 | 골든 hit@3 6/6. Q1~Q4 md/json 이 Phase 0 스냅샷과 바이트 동일. Q5 `도메인 진입파일 자동 로드`: 도입 전 정답 top-3 이탈(`진입파일` 히트 0, 1위 `lifecycle.md /pilot:project` 6점) → 도입 후 `index.md ## Cluster 진입` 1위 7점. Q6 `doctor 정합성검사`: 1위 유지, 18 → 20점 |
| G3 | 라이브 코퍼스 같은 질의 2회 `--format json` diff 0. 1,000섹션 성능 테스트 < 1s 통과 |
| G4 | 신규 플래그 미사용 시 md/json 바이트 동일 — 범위는 한글 결합·역방향 규칙에 해당하지 않는 질의(Q1~Q4·`select:`·라이브 3질의). Q5·Q6 와 4자+ 한글 토큰·인접 한글쌍이 있는 질의는 E2~E5 로 점수·0건 안내가 바뀐다(설계 의도, critic C3 정정) |
| G5 | `docs_build.py --check` 통과 (reference 40 파일 재생성, gitignore 대상). doctor 4 PASS · 3 WARN · 1 ERROR — ERROR `STATE.md 없음` 은 변경 전 커밋(`37ab524`) 에서도 동일(워크스페이스 로컬 파일 부재, 본 변경과 무관). WARN 3건은 인용 stale 신호: 이번에 고친 `wrapper-protocol.md`·`orchestrate-load.py` 를 `context/pilot/{index,review,spec}.md` 가 인용 — drift-protocol §A 에 따라 지식 파일을 직접 수정하지 않았다(`/pilot:learn` 재실행은 사용자 승인 사항) |
| G6 | 미실측 — 후속 feature 사이클에서 래퍼가 manifest → select --inject 흐름을 쓴 기록과 턴 수를 남긴다 |

### 결정 사항 보정 (구현 중 확정한 세부)

- **E4 세부**: 헤딩 역방향은 "글자 사이 공백 허용 대조" 에 더해 **헤딩의 한글 토큰이 질의 토큰에 포함**될 때도 부분 일치(5)로 친다. Q5 의 정답 헤딩 `Cluster 진입` 은 `진입파일` 과 공백 대조로는 맞지 않아 이 규칙이 없으면 본문 2점뿐이라 top-3 밖(경쟁 6점). 길이 제한은 **질의 토큰**에만(4자 이상·순수 한글) 걸리고 헤딩 토큰은 2글자부터 참여한다 — 조사가 붙은 4자+ 질의 토큰(`도메인을`)이 헤딩 `도메인 분류` 에서 부분 일치할 수 있다(본문은 여전히 조사 미흡수, 0건 안내의 "조사 제거 재질의" 유지). 헤딩 토큰 길이 제한(≥3)을 두면 Q5 정답 토큰 `진입` 이 2글자라 깨지므로 현행 유지 (critic C10). E4 의 'compact' 방식은 공백을 지우면 좌측 경계도 사라져 부적합 — 글자 사이 `\s*` 를 허용하는 flex 정규식으로 구현 (critic C6).
- **E8 보강**: `select:` 대상이 md·manifest 표시 경로(CWD 기준)여도 root 표시 접두를 떼어 코퍼스 루트 기준으로 정규화 — 에이전트가 manifest 줄의 경로를 그대로 붙여 넣을 수 있어야 3단계 흐름이 실제로 돈다. traversal 판정은 접두를 뗀 뒤 수행.
- **E9 세부**: 포함 관계 dedupe 는 **앞선** 결과의 주입 범위가 뒤 섹션 전체를 덮을 때만 적용(부모가 400줄 캡·예산으로 잘려 자식 범위에 못 미치면 자식은 그대로 주입). 주입 텍스트는 H2/H3 헤딩 라인을 복원해 앞에 붙이고, level 1 은 H1 텍스트가 있을 때만 `# {H1}`.
- **E10 세부**: `[type]` 태그는 score 뒤, age 는 `{n}d` (stat 실패 시 `?d`). 0건·INFO 렌더는 md 와 공유.

### critic 합의 반영 (2026-09-08)

별도 에이전트의 red-team 검토(`2026-09-08-context-search-enhancement-plan.critic.md`, 챌린지 12건)를 사용자 승인 순서대로 4라운드에 반영했다. 전 라운드에서 골든 Q1~Q4·select·라이브 3질의 바이트 동일, 전체 unittest 통과.

| 라운드 | 커밋 | 반영 |
|---|---|---|
| 1 | `8e72217` | C1 쉘 인용 안전 select(작은따옴표 프로토콜 · `_heading_key` · 빈 헤딩 INFO · manifest 백틱 제거) · C4 include 후보 select 도달(workspace 봉쇄 기준) · C8 렌더 총량 예산(스왑 임계 실측 28,000B 인라인·31,200B 스왑, 상한에서 md 19.9K·manifest 22.6K·json 21.5K) |
| 2 | `754459a` | C5 뒤 H2 가 앞선 H3 범위를 1줄 표지로 접기 · C6 정규식 lru_cache + flex 빠른 거부(한글 joined 5토큰 314 → 274ms, 한글 성능 테스트) · C7 gitignore 의미 glob |
| 3 | `df02ee2` | C2 경로 기반 `[rules?]`·`[boundary?]` 태그 + 규칙 문구 통일 · C3 바이트 동일·confluence 문구 정정 · C9 `golden-expected.json` + `GoldenSnapshotTest` + 힌트 assert |
| 4 | (본 커밋) | C10 E4 문구 정정 · C11 2~3단어 연쇄 + 헤딩 정확 일치 승격 · C12 400줄 캡 off-by-one, 쉼표 헤딩·`context` 도메인 테스트, snippet 필드 주석, §2 A1 정정 · 경계 검색 리터럴 빠른 거부(한글 joined 5토큰 최종 164ms, ASCII 118ms) |

구현 중 바뀐 결정: E4 의 compact 방식 → flex 정규식(C6) · E7 의 fnmatch → gitignore 의미(C7) · E9 의 예산 단위 본문 합 → 렌더 총량(C8) · E8 봉쇄 기준 루트 → workspace(C4).

### 남은 일 (사용자 결정)

1. 릴리스 시 `plugin.json` 버전 확정 → release-notes 미배포 절을 버전 절로 전환하고 버전 목록 표에 행 추가.
2. `context/pilot/{index,review,spec}.md` 인용 stale WARN — `/pilot:learn` 재실행 여부.
3. G6 dogfooding 실측 (래퍼 1건).
4. dp-skills 이식: 경로 치환(`pilot/` → `dp-skills/`) 외 차이 없어야 하나, 지시서의 함수명(`parse_frontmatter_description`·`_word_boundary_hit`)이 그쪽 코드에 실재하면 이 저장소와 분기된 것이므로 diff 확인 후 이식.
