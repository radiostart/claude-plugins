# 도메인 지식 검색·계층 탐색 강화 — feature 생성용 계획서 (포터블 작업 프롬프트)

- 작성일: 2026-09-04
- 상태: **Open Questions 6건 결정 반영 (2026-09-04)** → 본 문서의 §4 블록을 **수동으로 feature 로 등록**하는 단계
- 근거: Claude Code 소스 스냅샷(2026-03-31 노출본, `Claude-code-soruce/src/`) 의 검색·컨텍스트 로드 메커니즘 조사 (2026-09-04). 근거 표는 부록 B
- 적용 범위: A(검색 도구) · B(frontmatter 매니페스트) · C(경로 트리거) · D(신선도 힌트) 전부 + E(문서/코드 정합 부수 항목)
- 적용 강도: **soft** — 힌트·선택 사용. 기존 에이전트 절차를 필수 단계로 바꾸지 않는다
- 이식성: 이 문서는 **특정 플러그인에 귀속되지 않는다.** §0 의 변수를 채우면 "마크다운 계층으로 도메인 지식을 누적하고 에이전트가 작업 전 그 지식을 로드하는" 어떤 프로젝트에도 같은 프롬프트로 실행할 수 있다. pilot 은 첫 적용 인스턴스이며 매핑은 부록 A 에만 둔다

---

## 0. 이 문서를 프롬프트로 실행하는 방법

### 0.1 대상 프로젝트 조건

다음 셋을 모두 갖춘 프로젝트가 대상이다. 하나라도 없으면 그 요소를 먼저 만드는 것이 선행 과제다.

1. **지식 계층** — 도메인 지식이 마크다운으로 누적되고 `색인 → 도메인 진입 파일 → 본문 파일` 계층을 가진다.
2. **로더** — 에이전트(또는 래퍼)가 작업 전에 "어떤 지식 파일을 읽을지" 결정하는 스크립트나 절차가 있다.
3. **생성기** — 코드나 문서에서 지식 파일을 생산·갱신하는 스킬/스크립트가 있다 (수작업만이어도 되지만 B·C 의 자동 기입 범위가 줄어든다).

### 0.2 변수 표 — 실행 전 채운다

| 변수 | 의미 | 예 (pilot, 부록 A) |
| --- | --- | --- |
| `{{KNOWLEDGE_ROOT}}` | 지식 파일 루트 | `workspace/context` |
| `{{INDEX_FILE}}` | 항상 로드되는 최상위 색인 | `workspace/context/MANIFEST.md` |
| `{{ENTRY_RULE}}` | 도메인 → 진입 파일을 찾는 규칙 | MANIFEST `## 도메인 분류` 3컬럼 표 |
| `{{LOADER}}` | 로드 대상을 결정하는 스크립트/절차 | `pilot/tools/orchestrate-load.py` |
| `{{LOADER_OUTPUT}}` | 로더가 에이전트에 넘기는 구조 | JSON `files_to_read` + `hints` |
| `{{AGENT_WRAPPERS}}` | 로더 결과를 소비하는 에이전트 정의 | `pilot/agents/pilot-*.md` + `wrapper-protocol.md` |
| `{{DOC_GENERATOR}}` | 지식 파일 생성기 | `/pilot:learn` |
| `{{HEALTH_CHECK}}` | 워크스페이스 정합성 점검기 | `/pilot:doctor` (`tools/doctor/integrity.py`) |
| `{{HOOK_MECHANISM}}` | 도구 호출 전후 훅 배선 | `pilot/hooks/hooks.json` (PreToolUse/PostToolUse) |
| `{{LEGACY_SEARCH}}` | 이미 있는 부속 문서 검색 (재사용·대체 대상) | `confluence.py cmd_search` |
| `{{TOOLS_DIR}}` / `{{TEST_DIR}}` / `{{TEST_STYLE}}` | 도구·테스트 위치와 스타일 | `pilot/tools/` · `pilot/tests/tools/` · unittest |
| `{{FEATURE_FORMAT}}` | feature 명세 포맷 | 요구사항(조건·트리거·기대결과)·상태 전환·비즈니스 규칙·예외 케이스·Open Questions |
| `{{CITATION_STYLE}}` | 지식 파일이 소스를 인용하는 형식 | `` `path/file.ext:12` `` 또는 `:12-34` |
| `{{SOURCE_ROOT}}` | 인용 경로의 기준 루트 | 저장소 루트 (config `source_root` 보조) |

### 0.3 실행 지시 (AI 에게 그대로 준다)

> §1~§3 을 읽고 현재 프로젝트의 격차를 §1 의 5 항목에 대해 확인한다. 격차가 확인된 항목에 대응하는 §4 feature 블록을 `{{FEATURE_FORMAT}}` 으로 변환해 등록한다. 등록 순서와 완료 기준은 §5 를 따른다. §6 Open Questions 는 등록 **전에** 사용자에게 묻고 답을 feature 본문에 기록한다. 구현은 하지 않는다 — 등록까지가 이 프롬프트의 범위다.

### 0.4 불변 원칙 (모든 feature 공통)

- **도구가 후보를 좁히고, AI 는 후보 위에서 선택·해석한다.** 랭킹·필터·나이 계산은 결정적 스크립트로, "무엇을 읽을지" 최종 판단은 에이전트가.
- **색인은 항상, 본문은 요청 시.** 항상 로드되는 것은 얇은 색인·매니페스트·힌트만. 본문은 섹션·라인 범위 단위로 내려간다.
- **SSOT 위치를 바꾸지 않는다.** 지식 파일은 `{{KNOWLEDGE_ROOT}}` 에 그대로 둔다. 파생물(규칙 포인터, 매니페스트, 캐시)은 재생성 가능해야 한다.
- **자동 편집 금지.** 어떤 컴포넌트도 지식 파일 본문을 승인 없이 고치지 않는다. 신호(WARN·힌트)만 낸다.
- **표준 라이브러리 우선, 외부 인덱스 없음.** 벡터 DB·임베딩·외부 검색 서버를 도입하지 않는다 (§2 P7).
- **soft.** 래퍼 절차에 필수 step 을 추가하지 않는다. 로더 힌트와 프로토콜 문서의 "권장" 절만 갱신한다.

---

## 1. 문제 정의 (일반형)

계층 구조를 잘 만들어도 다음 다섯 가지가 AI 판단에만 맡겨져 있으면 규모가 커질수록 "전부 로드하거나, 놓친다" 로 귀결된다.

| # | 격차 | 증상 |
| --- | --- | --- |
| G1 | **로드가 정적이다.** 로더가 phase·domain 만 보고 진입 파일·경계 문서를 통째로 넘긴다. 지금 다루는 작업(feature) 의 키워드로 본문 섹션을 고르는 단계가 없다 | 도메인 문서가 커지면 로드 토큰이 선형 증가. 무관한 본문이 컨텍스트를 채움 |
| G2 | **색인 → 본문 이동이 산문 의존이다.** 진입 파일의 링크를 보고 에이전트가 판단. 본문 파일에 한 줄 요약(description) 메타가 없어 열어보기 전엔 내용을 모른다 | 잘못된 본문을 열거나, 열어보지 않고 추측 |
| G3 | **경로 트리거가 없다.** 특정 소스 파일을 수정하는 순간에 그 파일이 속한 도메인의 규칙·경계 문서가 따라오지 않는다 | 구현 단계에서 규칙 누락 → 리뷰·평가 단계에서 반려 |
| G4 | **신선도 신호가 점검 시점에만 있다.** 지식 파일에 `file:line` 인용이 있어도 로드 시점에 "이 문서가 몇 살이고 인용 파일 중 몇 개가 이후 바뀌었는지" 를 알려주지 않는다 | 삭제된 스크립트를 현행으로 서술한 문서를 에이전트가 사실로 인용 |
| G5 | **부속 문서 검색이 무순위 substring 이다.** 기획서 등 부속 문서 검색이 일치 섹션을 순위 없이 덤프한다 | 결과가 길어 결국 사람이 고른다 |

---

## 2. 참조 패턴 — Claude Code 소스에서 검증된 것 (핵심 수치 포함)

아래 수치·규칙은 그대로 채택 기준으로 쓴다. 파일 근거는 부록 B.

### P1. 2단 색인 + 매니페스트 선별 (memdir)

- 색인(`MEMORY.md`) 은 **항상 로드**. 캡 **200줄 · 25KB**, 항목은 1줄 **~150자** `- [제목](file.md) — 한 줄 훅`. 색인에 본문을 쓰지 않는다. 캡 초과 시 잘라내고 "항목이 너무 길다 — 상세는 본문 파일로" 경고를 붙인다.
- 본문 파일은 frontmatter(`name` · `description` · `type`) 를 가진다. 선별 시 각 파일의 **앞 30줄만** 읽어 `- [type] path (mtime): description` 매니페스트를 만든다 (최대 200 파일, 최신순).
- 매니페스트 + 질의를 저가 모델에 주고 **최대 5개** 를 고르게 한다. "확실히 유용한 것만, 불확실하면 제외". 이미 노출된 파일과 현재 사용 중인 도구의 사용법 문서는 제외(경고·함정 메모는 유지).
- 선별 결과는 라인·바이트 캡으로 읽어 **신선도 헤더**와 함께 주입한다. 비동기 prefetch 로 턴을 막지 않는다.
- 주기적 **consolidation**: 색인을 캡 아래로 유지, 200자 넘는 항목은 본문으로 강등, 모순은 원본에서 수정, 상대 날짜는 절대 날짜로.

### P2. 지연 로드 + 결정적 키워드 랭커 (ToolSearch)

- 도구는 **이름만** 노출하고 정의(스키마) 는 검색 뒤에 붙인다. 정의 총량이 컨텍스트의 **10%** 를 넘으면 자동으로 이 모드가 켜진다.
- 질의 3형식: `select:A,B` (직접 지정, 쉼표 다중) · `키워드 나열` · `+필수어 선택어` (필수어를 이름·설명에 모두 가진 후보만 남긴 뒤 나머지로 순위).
- 점수(질의 토큰마다 합산): 이름 파트 정확 일치 **10** (MCP 12) · 이름 파트 부분 일치 **5** (6) · 전체 이름 fallback **3** · 큐레이션 힌트 문구 **4** · 설명 **단어경계** 일치 **2**. 점수 0 은 제외, 내림차순, 기본 top **5**.
- 질의가 도구 이름과 정확히 같으면 즉시 반환(fast path). 결과 0건이면 "아직 연결 중인 서버가 있다" 같은 **상태 안내**를 함께 준다.

### P3. 경로 조건부 컨텍스트 (CLAUDE.md conditional rules · 조건부 스킬)

- `.claude/rules/*.md` 의 frontmatter `paths:` 에 glob 을 두면 그 규칙은 **매칭 파일을 Read/Edit/Write 하는 순간에만** 로드된다. `paths` 가 없거나 `**` 만이면 무조건 로드.
- 매칭은 gitignore 스타일(`ignore` 라이브러리). `/**` 접미는 제거해 디렉토리 자체와 하위를 모두 매칭. 기준 경로는 규칙 파일이 속한 `.claude` 의 부모.
- 트리거: 파일 도구가 대상 경로를 `nestedMemoryAttachmentTriggers` 에 넣고, 턴 끝에 **cwd → 대상 파일 디렉토리 체인**을 걸으며 각 디렉토리의 `CLAUDE.md` · 무조건 규칙 · 조건부 규칙을 모은다. 가까운 디렉토리가 우선, `processedPaths` 로 중복 방지.
- 스킬도 같은 `paths:` frontmatter 로 조건부 활성화되고, 파일에서 cwd 방향으로 `.claude/skills` 를 올라가며 발견한다(gitignore 된 디렉토리는 제외).
- 훅으로도 같은 효과: `PostToolUse` 훅이 `hookSpecificOutput.additionalContext` (문자열, 선택) 를 돌려주면 컨텍스트에 주입된다. `UserPromptSubmit` 은 필수 문자열.

### P4. 검색 전용 저가 서브에이전트 (Explore)

- 읽기 전용, 파일 생성·수정·`/tmp` 쓰기 금지. 저가 모델(외부 사용자는 haiku). CLAUDE.md 생략(`omitClaudeMd`) — 호출자가 해석한다.
- 호출자는 **thoroughness** 를 지정: `quick` / `medium` / `very thorough`. 병렬 도구 호출을 강제. **결론만** 반환, 파일 덤프 금지.
- 안티패턴 규칙: 경로를 알면 Read, 클래스 정의 하나는 Grep/Glob, 2~3 파일이면 Read — 서브에이전트를 쓰지 않는다.

### P5. 신선도·인용 검증 규율

- 로드된 메모리마다 나이를 붙인다: `today` / `yesterday` / `N days ago`. 하루를 넘으면 문구 추가: "이 메모리는 N일 전 것이다. 시점 관찰이지 현재 상태가 아니다 — 코드 동작·file:line 인용은 바뀌었을 수 있다. 사실로 단언하기 전에 현재 코드로 검증하라."
- "파일·함수·플래그를 지칭하는 메모리는 **그것이 존재했다는 주장**이다. 추천 전에 파일은 존재 확인, 함수는 grep. 사용자가 그 추천으로 행동할 참이면 먼저 검증한다." 저장소 상태 요약은 스냅샷 — 최근 상태는 `git log` 나 코드가 우선.

### P6. 하이브리드 검색 (agenticSessionSearch)

- 1단계 substring 사전 필터(제목·태그·브랜치·요약·첫 메시지·발췌), 상위 **100건**, 부족하면 최신으로 채움. 2단계 저가 모델이 관련 인덱스를 고른다. 우선순위: 태그 정확 > 태그 부분 > 제목 > 브랜치 > 요약·본문 > 의미 유사. "의심스러우면 포함" — 회수 우선.

### P7. 비채택 패턴 (근거 있는 제외)

- **벡터·임베딩 색인 없음.** 소스에 검색용 임베딩이 없다. `codeIndexing.ts` 는 외부 인덱서 사용을 감지하는 텔레메트리일 뿐. ripgrep + 결정적 점수 + 저가 모델 선별로 충분함을 보여준다.
- **MagicDocs 식 자동 문서 갱신은 채택하지 않는다.** `# MAGIC DOC:` 헤더 문서를 읽으면 유휴 턴마다 서브에이전트가 in-place 편집한다. "승인 없는 편집" 이라 §0.4 의 자동 편집 금지, 추측 금지 원칙과 충돌한다. 문구 철학("간결, 아키텍처·진입점·이유·연결 관계, 코드에서 자명한 것 기록 금지") 은 B 의 description 작성 규칙으로만 차용한다.

---

## 3. 설계 개요

### 3.1 컴포넌트와 의존

```
             ┌──────────────── D. 신선도 힌트 (신호) ────────────────┐
             │  인용 file:line 파싱 → stat/git → 나이·변경 수 힌트    │
             └───────────────▲───────────────────────────────────────┘
                             │ learned_at 이 있으면 정확도 ↑
{{INDEX_FILE}} ──▶ 진입 파일 ──▶ 본문 섹션 ◀── A. context-search (도구)
 (항상 로드)     (도메인 단위)   (라인 범위)     결정적 랭커 · 질의 3형식 · top-N
                                   ▲              ▲ description 가중치 (B 이후)
                                   │              │
                     B. frontmatter 매니페스트 (데이터) ── 본문 1줄 요약 · sources · learned_at
                                   │
                     C. 경로 트리거 (배선) ── sources glob → 규칙 포인터 파일 / 훅 additionalContext
```

- **A 와 D 는 서로 독립**이고 메타데이터 없이 동작한다 (A 는 헤딩·경로·인용, D 는 인용·mtime).
- **B 는 A 의 정밀도와 D 의 정확도를 올리는 데이터**다. B 없이도 A·D 는 성립한다.
- **C 는 B 의 `sources` 를 쓰면 정확하고**, 없으면 지식 파일의 인용 경로에서 역으로 도메인 glob 을 추정한다.

### 3.2 공통 인터페이스 원칙

- 모든 도구 출력은 **다음 행동**을 포함한다: 어떤 파일의 어느 라인 범위를 Read 하면 되는지. 에이전트가 결과를 해석해 다시 찾는 비용을 없앤다.
- 도구는 `--format json|md` 를 제공한다. 로더·훅·점검기는 json 을, 사람은 md 를 본다.
- 결과 0건은 실패가 아니다. "범위를 넓혀라 / 유사 토큰 / 도메인 미등록" 같은 **상태 안내**를 준다 (P2).
- 상한을 명시한다: 결과 수, 스니펫 길이, 힌트 길이, 규칙 포인터 수. 상한 초과는 "외 N건" 으로 접는다.

---

## 4. feature 블록

각 블록은 `{{FEATURE_FORMAT}}` 으로 그대로 옮길 수 있게 **요구사항 · 상세 · 규칙 · 예외 · 검증 · 관련 파일** 순으로 쓴다. "관련 파일" 은 일반형으로 적고, pilot 실제 경로는 부록 A 표에서 치환한다.

### F-A. `context-search` — 섹션 단위 결정적 검색 도구

**목적** — G1·G2·G5 해소. 지식 계층의 본문을 "열어보지 않고" 섹션 단위로 좁혀 라인 범위 Read 로 내려간다.

**요구사항**

- **조건**: `{{KNOWLEDGE_ROOT}}` 아래 마크다운 지식 파일이 1개 이상 있다.
- **트리거**: 에이전트가 도메인 진입 파일을 로드한 뒤 특정 주제(feature 제목 키워드, 클래스명, 소스 경로) 의 상세가 필요할 때. 로더 힌트가 사용을 권장한다(soft).
- **기대결과**: 질의 1회로 상위 N 섹션의 `파일 · 헤딩 · 라인 범위 · 점수 · 스니펫` 을 받고, 그중 1~2개를 부분 Read 한다. 전체 파일 Read 나 무차별 Grep 을 대체한다.

**상세 설계**

- **색인 단위**: H2·H3 섹션. 섹션 = 헤딩 라인부터 같은 레벨 이상 다음 헤딩 직전까지. H1 만 있는 파일은 파일 전체 1 섹션. 코드블록(``` 펜스) 안의 `#` 는 헤딩으로 보지 않는다. frontmatter 는 색인 대상에서 제외하되 description 은 별도 필드로 보관(B).
- **코퍼스**: 기본 `{{KNOWLEDGE_ROOT}}/**/*.md`. `--scope {domain}` 으로 도메인 폴더·진입 파일·`boundaries/{domain}--*` 로 좁힌다. `--include features/ docs/` 로 프로젝트 부속 문서를 추가(기본 제외 — Open Q (a)).
- **질의 문법** (P2 그대로):
  - `select:{path}` 또는 `select:{path}#{헤딩 일부}` — 직접 지정. 존재하면 그 섹션(들) 을 점수 없이 반환.
  - `키워드 나열` — 공백 분리. 
  - `+필수어` — 필수어를 헤딩·경로·인용·본문 어디든 가진 섹션만 후보. 나머지 토큰으로 순위.
  - 질의 토큰이 경로처럼 보이면(`/` 포함 + 확장자) **인용 경로 일치**를 자동 가중한다 → "이 소스 파일을 다루는 지식 섹션" 을 찾는 역방향 질의.
- **토큰화**: 소문자화 · 영숫자/한글/그 외 경계로 분리 · `_` `-` `.` `/` 분리 · CamelCase 분리(`CyberBongoRegister` → `cyber bongo register` + 원형 유지). 1글자 토큰과 불용어(`the` `및` `의` 등 최소 목록) 제거.
- **점수표** (토큰마다 합산, 신호별 섹션당 1회 — 빈도 미반영):

  | 신호 | 점수 |
  | --- | --- |
  | 헤딩 토큰 정확 일치 | 10 |
  | 파일 경로 세그먼트 정확 일치 (도메인명·파일명) | 8 |
  | 인용 경로 세그먼트 일치 (`{{CITATION_STYLE}}` 로 인용된 경로에 토큰 포함) | 6 |
  | 헤딩 토큰 부분 일치 | 5 |
  | frontmatter description 단어경계 일치 (B 이후 활성) | 4 |
  | 본문 단어경계 일치 | 2 |

  동점: 얕은 헤딩(H2) 우선 → 진입 파일(index) 우선 → 경로 사전순. 점수 0 제외.
- **출력**: 기본 `--limit 5` (최대 20). json 항목 = `{file, heading, level, line_start, line_end, score, matched: [토큰], snippet(≤240자, 첫 일치 주변), read_hint: "Read {file} offset={line_start} limit={n}"}`. md 는 같은 정보를 표 + 스니펫으로.
- **0건 처리**: 토큰별 히트 수를 보여주고 "`--scope` 제거 / `+필수어` 제거 / 토큰 분리(`cyber_bongo` → `cyber bongo`) / 도메인 미등록이면 `{{DOC_GENERATOR}}` 실행" 을 안내.
- **성능·구현**: 표준 라이브러리만(`re` `pathlib` `json` `argparse`). 섹션 1,000개 코퍼스에서 300ms 이내. 캐시 없음(선택 과제: mtime 키 캐시).
- **배선 (soft)**:
  1. `{{LOADER}}` 가 도메인 진입 파일을 로드한 직후 힌트 1줄: `[검색] 본문 상세는 python3 {{TOOLS_DIR}}/context-search.py "<키워드>" --scope {domain} 로 섹션 조회 후 라인 범위 Read (예: "<현재 feature 제목 키워드>")`.
  2. `{{AGENT_WRAPPERS}}` 의 "부분 로드" 절(목차 → 라인 범위 수동 2단계) 을 도구 호출 1단계로 대체하는 **권장** 문구로 갱신. 필수화하지 않는다.
  3. `{{LEGACY_SEARCH}}` 가 같은 랭커 모듈을 import 해 순위·스니펫·상한을 갖도록 교체(출력 형식은 기존 유지).
  4. 탐색 규칙 문서에 P4 계약을 반영: Explore 류 서브에이전트에 scope 경로 + thoroughness 지정, 결론만 반환.

**비즈니스 규칙**

- 결정적: 같은 코퍼스·질의 → 같은 출력·순서.
- 코퍼스 밖 경로 traversal 금지(`..`·절대경로 인자 거부).
- 인용 경로 일치는 존재 여부를 검증하지 않는다(그것은 D 의 일).
- 지식 파일을 수정하지 않는다(읽기 전용).

**예외 케이스**

- 헤딩 없는 파일 → 파일 전체 1 섹션, `heading: "(파일 전체)"`.
- 400줄 넘는 섹션 → 스니펫만 주고 `read_hint` 에 "섹션이 크다 — 소제목으로 재질의 권장" 표기.
- 한글·영문 혼합 토큰(`배송취소`) → 공백·구두점 분리만 하고 형태소 분석은 하지 않는다(Open Q (f)).
- 질의가 비었거나 토큰이 전부 제거되면 사용법 출력 후 종료(exit 2).

**검증**

- 단위: 토큰화(CamelCase·경로·한글) · 점수 합산 · `+필수어` 사전필터 · 코드블록 내 `#` 무시 · 라인 범위 정확성 · `select:` · 0건 안내 · traversal 거부.
- 골든 질의 3개(도메인당): 기대 섹션이 top-3 안에 드는지 (`hit@3`).
- dogfooding: 실제 feature 1건에서 planner 가 도구를 1회 이상 사용하고 부분 Read 로 이어졌는지 기록.

**관련 파일 (일반형)**

- 신규 `{{TOOLS_DIR}}/context-search.py` (모듈 docstring 필수 — 참조 문서 자동 생성 대상)
- 신규 `{{TEST_DIR}}/test_context_search.py`
- 변경 `{{LOADER}}` (힌트 1줄) · `{{AGENT_WRAPPERS}}` 부분 로드 절 · 탐색 규칙 문서 · `{{LEGACY_SEARCH}}`

---

### F-D. 로드 시 신선도 힌트 — 인용 기반 변경 감지

**목적** — G4 해소. P5 규율을 "매 로드마다 자동으로 붙는 신호" 로 만든다.

**요구사항**

- **조건**: 로드 대상 지식 파일이 `{{CITATION_STYLE}}` 인용을 포함한다(없으면 나이만 표기).
- **트리거**: `{{LOADER}}` 가 지식 파일을 `files_to_read` 에 넣을 때마다. `{{HEALTH_CHECK}}` 실행 시에도 같은 로직으로 WARN.
- **기대결과**: 파일마다 힌트 1줄: `[신선도] {file}: 학습 {age}일 전 · 인용 {changed}/{total} 파일이 이후 변경 · 미존재 {missing} — 인용 전 현재 코드 확인`. 나이 1일 이하이고 변경 0이면 생략(노이즈 억제 — P5).

**상세 설계**

- **기준 시각**: frontmatter `learned_at`(B) > 없으면 파일의 최근 git 커밋 시각(`git log -1 --format=%cI -- {file}`) > 그것도 없으면 mtime. git 을 우선하는 이유: clone·checkout 이 mtime 을 흔든다(Open Q (d)).
- **인용 파싱**: `` `?([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`? `` — 경로·시작 라인·끝 라인. 코드블록 안 인용도 포함(예시 코드가 아닌 실제 인용이 코드블록에 놓이는 경우가 있다). 같은 경로는 1회로 합친다.
- **경로 해석**: 저장소 루트 기준 → 실패 시 `{{SOURCE_ROOT}}` 기준 → 실패 시 지식 파일의 디렉토리 기준. 셋 다 실패면 `missing`.
- **변경 판정**: 인용 파일의 기준 시각(git 커밋 시각 > mtime) 이 지식 파일 기준 시각보다 뒤면 `changed`. 라인 번호 유효성(`line_end ≤ 파일 줄 수`) 도 함께 검사해 `line_out_of_range` 카운트.
- **상한**: 파일당 인용 500개 초과 시 앞 500개만 검사하고 `(표본 500/{n})` 표기. stat 실패는 skip 하고 카운트에 넣지 않는다.
- **점검기 연동**: `{{HEALTH_CHECK}}` 가 지식 파일 단위로 같은 계산을 수행. 임계: `changed/total ≥ 30%` 또는 `missing ≥ 1` → WARN "재학습 권장: `{{DOC_GENERATOR}}` …"; 그 외 INFO. 기존 "analyzed_at 보다 최근에 바뀐 지식 파일" 검사와 별개 축(그쪽은 파생물 재생성, 이쪽은 지식 자체의 부패).

**비즈니스 규칙**

- 신호만 낸다. 자동 수정·자동 재학습을 트리거하지 않는다(drift 절차 유지).
- 로더 지연 상한 200ms. 넘으면 나이만 표기하고 인용 검사는 `{{HEALTH_CHECK}}` 로 위임한다는 힌트를 낸다.

**예외 케이스**

- 인용 경로가 glob 이나 디렉토리(`app/services/wms/`) → 디렉토리의 최신 변경 시각으로 판정.
- 심볼릭 링크 → 대상 기준.
- git 이 없는 환경 → mtime 만 사용, 힌트에 `(mtime 기준)` 표기.

**검증**

- 픽스처: 지식 파일 1 + 인용 소스 3 (변경 1 · 미변경 1 · 삭제 1) → 힌트 문구·카운트 정확성. mtime 조작은 `os.utime`, git 경로는 임시 저장소.
- 점검기 출력 스냅샷 테스트.

**관련 파일 (일반형)**

- 신규 `{{TOOLS_DIR}}/freshness.py` (라이브러리 + CLI, `{{LOADER}}`·`{{HEALTH_CHECK}}` 공용)
- 변경 `{{LOADER}}` (힌트 생성) · `{{HEALTH_CHECK}}` (WARN 규칙) · drift 대응 문서(자동 신호 절 추가)
- 신규 `{{TEST_DIR}}/test_freshness.py`

---

### F-B. 본문 frontmatter 매니페스트 — 열기 전에 아는 한 줄

**목적** — G2 해소. P1 의 "30줄 스캔 → 매니페스트" 를 지식 계층에 적용한다.

**요구사항**

- **조건**: `{{DOC_GENERATOR}}` 가 본문 파일을 생성·재생성한다.
- **트리거**: 생성 시 자동 기입. 기존 파일은 `{{HEALTH_CHECK}} --fix` 에서 opt-in 마이그레이션.
- **기대결과**: 본문 파일마다 frontmatter 가 있고, `{{LOADER}}` 출력에 활성 도메인 본문의 `context_manifest` 가 추가된다. 에이전트는 매니페스트를 보고 필요한 본문만 Read 한다(진입 파일 로드는 그대로 — soft).

**상세 설계**

- **스키마** (본문·진입 파일 공통):

  ```yaml
  ---
  description: 배송 취소 서비스 3종의 호출 순서와 상태 전환 규칙   # ≤150자, 1줄, "무엇을 알 수 있나"
  domain: wms
  type: services            # index | routes | models | services | rules | enums | boundary | free
  sources:                  # 이 문서가 다루는 소스 범위 (glob 허용) — C 의 paths 로 재사용
    - app/services/wms/**
    - app/models/wms/shipment.rb
  learned_at: 2026-09-04T03:12:00Z
  ---
  ```

- **description 작성 규칙** (P7 에서 차용): 무엇을 알 수 있는지 한 문장. 파일명 반복 금지, 헤딩 나열 금지, 코드에서 자명한 것 금지.
- **매니페스트 생성**: `{{LOADER}}` 가 활성 도메인 폴더(+ `boundaries/{domain}--*`) 의 `*.md` 를 훑어 **앞 30줄만** 읽고 `- [type] path (age): description` 1줄씩. 최대 200개, 초과 시 최신순 절단 + 표기. frontmatter 없는 파일은 `(description 없음 — 첫 H1: …)` 으로 대체.
- **캡 검증** (`{{HEALTH_CHECK}}`): description 부재 WARN · 150자 초과 WARN · 색인 파일(`{{INDEX_FILE}}`, 진입 index) 200줄 또는 25KB 초과 WARN(P1 캡 그대로) · `sources` 경로 미존재 INFO.
- **마이그레이션**: `--fix` 가 description 부재 파일에 대해 첫 H1 + 첫 문단 40자로 후보를 제안하고 사용자 승인 후 기입(자동 기입 금지 — Open Q (b)).
- **A·D 연동**: A 점수표의 description 4점 활성. D 의 기준 시각으로 `learned_at` 사용.

**비즈니스 규칙**

- `{{INDEX_FILE}}` 자체는 frontmatter 를 두지 않는다(형식 자유 원칙 유지). 도메인 진입 index 파일에는 둔다.
- 사용자가 손으로 만든 파일은 frontmatter 없이 허용. 점검기는 WARN 만.
- frontmatter 는 생성기의 관리 영역이지만 본문은 아니다 — 재생성 시 본문 병합 규칙은 기존 생성기 정책을 따른다.

**예외 케이스**

- 같은 도메인 폴더에 200개 넘는 본문 → 매니페스트를 sub-folder 단위로 접고 "폴더별 N개" 표기.
- `type` 미지 값 → `free` 로 취급, INFO.
- description 에 개행 → 첫 줄만 사용, WARN.

**검증**

- 생성기 골든 출력에 frontmatter 포함 확인. 점검기 WARN 3종 테스트. 매니페스트 30줄 스캔이 본문을 읽지 않는지(대용량 파일 픽스처로 시간 측정).

**관련 파일 (일반형)**

- 변경 `{{DOC_GENERATOR}}` (Phase: 구조 결정·생성) · `{{LOADER}}` (`context_manifest`) · `{{HEALTH_CHECK}}` (캡·마이그레이션) · 생성 휴리스틱 문서(description 규칙)
- 변경 `{{TEST_DIR}}` 의 생성기·점검기 테스트

---

### F-C. 경로 트리거 — 소스 파일을 건드리는 순간 도메인 포인터 로드

**목적** — G3 해소. P3 을 지식 계층에 연결한다. **SSOT 는 옮기지 않고 포인터만** 만든다.

**요구사항**

- **조건**: 도메인별 `sources`(B) 가 있거나, 없으면 지식 파일 인용 경로에서 도메인 glob 을 추정할 수 있다.
- **트리거**: 에이전트가 `sources` 에 매칭되는 소스 파일을 Read/Edit/Write 한다.
- **기대결과**: 해당 도메인의 진입 파일·관련 본문·경계 문서·`context-search` 사용 1줄로 구성된 **포인터 3~8줄**이 컨텍스트에 나타난다. 본문 복사는 없다.

**상세 설계 — C1 (기본, 하네스 네이티브)**

- `{{DOC_GENERATOR}}` 가 도메인마다 `.claude/rules/{prefix}-{domain}.md` 를 생성:

  ```markdown
  ---
  paths:
    - app/services/wms/**
    - app/models/wms/**
  ---
  <!-- managed by {{DOC_GENERATOR}} — 수동 편집 금지. 재생성으로 갱신 -->
  이 경로는 `wms` 도메인이다. 수정 전 확인:
  - 진입: {{KNOWLEDGE_ROOT}}/wms/index.md
  - 서비스 규칙: {{KNOWLEDGE_ROOT}}/wms/services.md
  - 경계 계약: {{KNOWLEDGE_ROOT}}/boundaries/wms--schoice.md
  - 상세 조회: python3 {{TOOLS_DIR}}/context-search.py "<키워드>" --scope wms
  ```

- 포인터 대상 선정: 진입 index 1 + `type` 이 rules·services·enums 인 본문 최대 3 + 경계 문서 최대 2 + 검색 1줄. 초과는 "그 외 N개 — index 참조".
- idempotent: 관리 마커가 있는 파일만 덮어쓴다. 마커 없는 파일(사용자 수정) 은 건드리지 않고 INFO.
- `{{HEALTH_CHECK}}`: 포인터 경로 존재 검증, 도메인이 삭제됐는데 규칙 파일이 남은 경우(stale) WARN, `paths` 와 `sources` 불일치 INFO.
- **선행 검증 항목(필수)**: 조건부 규칙이 **서브에이전트(래퍼) 안에서도 발화하는지** 실측한다. 절차: 규칙 파일 1개 생성 → 래퍼로 매칭 경로 파일을 Read 하는 최소 작업 실행 → 래퍼 응답에 규칙 본문이 반영됐는지 확인. 소스상 `nested_memory` 첨부는 메인/서브 공통 첨부 목록에 있어 발화가 기대되지만(부록 B), 실측 전엔 확정하지 않는다. 실패 시 C2 로 전환.

**상세 설계 — C2 (대체, 플러그인 훅)**

- `{{HOOK_MECHANISM}}` 의 `PostToolUse`(matcher `Edit|Write|Read`) 에 스크립트를 추가. stdin JSON 의 `tool_input.file_path` → `sources`(B) 또는 인용 역색인으로 도메인 판정 → `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"<포인터 3줄>"}}` 출력.
- 상한: 같은 턴·같은 도메인은 1회(상태 파일에 최근 발화 기록, 세션 종료 시 폐기). 총 500자.
- 매칭 실패는 침묵(exit 0, 출력 없음). 실행 시간 100ms 이내.

**비즈니스 규칙**

- 포인터만. 지식 본문을 규칙 파일이나 additionalContext 에 복사하지 않는다.
- 규칙 파일은 파생물이다 — `{{DOC_GENERATOR}}` 재실행으로 언제든 재생성 가능해야 한다.

**예외 케이스**

- 한 소스 파일이 여러 도메인에 매칭 → 최대 2 도메인 포인터 + "그 외 N".
- `sources` 없는 도메인 → 인용 경로의 공통 디렉토리 접두를 glob 으로 추정, INFO 로 추정 사실을 표기.
- 모노레포에서 `.claude` 가 여러 층 → 규칙 파일은 `{{KNOWLEDGE_ROOT}}` 와 같은 저장소 루트의 `.claude/rules/` 한 곳에만 둔다.

**검증**

- 생성기 골든 출력(규칙 파일 1개) · 관리 마커 보존 테스트 · 점검기 stale 감지 테스트.
- C1 발화 실측 결과를 feature 본문에 기록(성공/실패, 사용한 하네스 버전).

**관련 파일 (일반형)**

- 변경 `{{DOC_GENERATOR}}` (규칙 파일 생성) · `{{HEALTH_CHECK}}`
- C2 시 신규 `{{HOOK_MECHANISM}}` 스크립트 + `hooks.json` 매처 추가 + 테스트

---

### F-E. (부수) 로드 정책 문서와 코드의 정합

**목적** — 조사 중 발견한 문서/코드 불일치를 P1 기준으로 정리한다.

- **현상**: 프로젝트 가이드·상태 스키마 문서는 "분석 완료 상태(`analyzed: true`) 면 진입 파일 재로드를 생략" 이라 서술하지만, `{{LOADER}}` 는 그 값을 받지 않고 도메인이 정해지면 항상 진입 파일을 로드한다.
- **결정**: **코드가 옳다.** "색인·진입은 항상 로드" 가 P1 과 정합한다. 문서를 코드에 맞춘다. 구현 변경 없음.
- **범위**: 문서 2곳 수정 + `{{HEALTH_CHECK}}` 에 "문서가 서술한 로드 정책 ≠ 코드" 를 잡는 검사는 두지 않는다(과잉). D 와 같은 PR 에 묶어도 된다.

---

## 5. 실행 순서·마일스톤·완료 기준

### 5.1 순서와 이유

| 순서 | feature | 이유 |
| --- | --- | --- |
| 1 | **F-A** context-search | 메타데이터 없이 독립 동작. 가장 큰 격차(G1·G2·G5) 를 한 번에 줄인다 |
| 2 | **F-D** 신선도 힌트 | 작고 즉시 효과. 실제 stale 사례(부록 A 의 feature #22) 가 있다 |
| 3 | **F-B** frontmatter 매니페스트 | A 의 정밀도·D 의 정확도를 올리는 데이터. 생성기 변경이 들어가므로 A·D 로 가치를 먼저 확인한 뒤 |
| 4 | **F-C** 경로 트리거 | B 의 `sources` 에 의존. 서브에이전트 발화 검증이 선행 |
| 5 | **F-E** 문서 정합 | 독립. D 와 묶어 처리 가능 |

### 5.2 릴리스 단위

- 새 도구 2개(context-search · freshness) + frontmatter 스키마 추가 + 규칙 파일 생성은 **하위호환** 이다(없어도 기존 동작 유지). **minor bump** 1회로 묶는다.
- 각 feature 는 독립 PR. A 만으로도 릴리스 가능.

### 5.3 전체 완료 기준 (Definition of Done)

1. 테스트 전부 통과(신규 2 + 변경분).
2. `{{HEALTH_CHECK}}` 클린(신규 WARN 규칙 포함).
3. **dogfooding 1 사이클**: 실제 feature 1건을 파이프라인으로 완주하며 (a) planner 가 context-search 를 1회 이상 사용해 부분 Read 로 이어지고 (b) 신선도 힌트가 출력되고 (c) C 가 있으면 소스 수정 시 포인터가 나타난 기록을 남긴다.
4. **soft 보증**: 래퍼·프로토콜 문서의 순증이 합계 30줄 이내, 필수 step 추가 0건.
5. **비도입 확인**: 벡터·임베딩·외부 인덱스 0, 지식 파일 자동 편집 0.
6. 측정 2개를 before/after 로 기록: (i) 도메인 로드 줄수(진입+본문 전체 vs 진입+매니페스트+선별 섹션) (ii) 골든 질의 `hit@3`.

---

## 6. Open Questions — 결정 기록 (2026-09-04 사용자 확정)

- **(a) 코퍼스 기본 범위** — `{{KNOWLEDGE_ROOT}}` 만인가, 프로젝트 부속 문서(features·docs) 도 기본 포함인가. 기본은 지식만, 부속은 `--include` 를 제안한다. → **결정(2026-09-04): 지식 루트만.** features/·docs/ 는 `--include` 명시 시에만 포함.
- **(b) description 마이그레이션** — 기존 파일의 description 을 점검기가 제안만 하고 승인 후 기입(제안) vs 자동 기입. → **결정(2026-09-04): 제안 후 승인 기입.** `{{HEALTH_CHECK}} --fix` 는 후보만 제시하고 승인 시 기입.
- **(c) C1/C2 선택** — 서브에이전트 발화 실측 결과에 따른다. 실측 전 등록 시 feature 본문에 "실측 후 결정" 으로 남긴다. → **결정(2026-09-04): 실측 후 결정.** F-C feature 본문에 서브에이전트 발화 검증 절차를 넣고 결과로 C1/C2 확정.
- **(d) 신선도 기준 시각** — git 커밋 시각 우선(제안) vs mtime 만. clone 이 잦은 환경이면 git. → **결정(2026-09-04): git 커밋 시각 우선.** `learned_at` > `git log -1` > mtime.
- **(e) 랭커의 description 가중치 활성 시점** — B 머지 후 자동(제안) vs 플래그. → **결정(2026-09-04): B 머지 후 자동.** description 이 있는 파일만 4점 가산, 플래그 없음.
- **(f) 한글 토큰화 수준** — 공백·구두점 분리만(제안) vs 간단 n-gram 추가. 골든 질의 `hit@3` 로 판단. → **결정(2026-09-04): 공백·구두점 분리만.** 골든 질의 `hit@3` 가 부족할 때만 보강을 검토.

---

## 부록 A. pilot 적용 매핑 (첫 인스턴스)

변수 치환과 정확한 앵커. 다른 프로젝트에서는 이 부록만 자기 것으로 갈아 쓴다.

| 변수 | pilot 값 · 앵커 |
| --- | --- |
| `{{KNOWLEDGE_ROOT}}` | `workspace/context/` |
| `{{INDEX_FILE}}` · `{{ENTRY_RULE}}` | `workspace/context/MANIFEST.md` · `## 도메인 분류` 표 → `{domain}/index.md`, 경계 문서 `boundaries/{A}--{B}.md` |
| `{{LOADER}}` | `pilot/tools/orchestrate-load.py` — `build_load_plan` 4) 진입 파일 로드(`:467`) · 5) 경계 문서(`:487`, `MAX_BOUNDARY_DOCS = 6`). 힌트·매니페스트·신선도는 이 두 단계 직후에 추가 |
| `{{LOADER_OUTPUT}}` | JSON `files_to_read` · `hints` · `instructions` (`:13-27`). B 는 `context_manifest` 키 신설 |
| `{{AGENT_WRAPPERS}}` | `pilot/agents/pilot-{planner,planner-critic,generator,evaluator}.md` + `pilot/skills/context/shared/wrapper-protocol.md` **§6 부분 로드**(`:32`) → A 권장 문구로 교체. 탐색 규칙 `pilot/skills/context/domain/scope-exploration.md` → P4 계약 반영 |
| `{{DOC_GENERATOR}}` | `/pilot:learn` — `pilot/skills/learn/SKILL.md` Phase 4(`:66`, 구조 결정·생성 → B frontmatter) · Phase 5(`:75`, MANIFEST 갱신 → C 규칙 파일 생성). 휴리스틱 `references/heuristics.md` 에 description 규칙 |
| `{{HEALTH_CHECK}}` | `/pilot:doctor` — `pilot/tools/doctor/integrity.py` `check_workspace`(`:320`, B 캡·C stale) · `check_project`(`:456`; 기존 context mtime drift `:718-770` 옆에 D 인용 검사) |
| `{{HOOK_MECHANISM}}` | `pilot/hooks/hooks.json` — `PreToolUse Edit|Write`(scope-guard) 존재. C2 는 `PostToolUse Edit|Write|Read` 매처 추가. stdin 파싱 예: `hooks/scope-guard.sh:10` |
| `{{LEGACY_SEARCH}}` | `pilot/tools/confluence.py` `cmd_search`(`:767`) — 무순위 substring, 섹션당 2000자 덤프 → A 랭커 import |
| `{{TOOLS_DIR}}` · `{{TEST_DIR}}` · `{{TEST_STYLE}}` | `pilot/tools/` · `pilot/tests/tools/` · unittest + `importlib` 로 하이픈 파일 로드(`test_orchestrate_load.py` 참조). `pilot/tools/docs_build.py` 가 `tools/*.py` 모듈 docstring 을 `docs/reference/tools/` 로 자동 추출 — 새 도구는 docstring 필수 |
| `{{FEATURE_FORMAT}}` | `workspace/projects/build-plugin/features/NN-{slug}.md` — `> source:` 메타 + 요구사항(조건·트리거·기대결과)·상태 전환·비즈니스 규칙·예외 케이스·Open Questions (a)(b)(c)(d) + 관련 파일 범위. 다음 번호 **#24** |
| `{{CITATION_STYLE}}` · `{{SOURCE_ROOT}}` | `` `pilot/skills/confl/SKILL.md:9` `` · `:18-21` 형식(`workspace/context/pilot/spec.md` 실측). 기준은 저장소 루트, 보조로 `config.md` `source_root` |
| 버전 | `pilot/.claude-plugin/plugin.json` `0.10.0` → `0.11.0` (minor). `mkdocs.yml extra.version` · `docs/index.md` highlights 동기화 |
| F-E 앵커 | `pilot/skills/context/lifecycle/projects/GUIDE.md:51-58` · `pilot/skills/context/lifecycle/state-schema.md` `analyzed` 절 → "진입 파일은 항상 로드, analyze 는 prompts/ 압축본 신뢰 여부만" 으로 정정 |
| 실사례 | `features/22-context-drift-relearn.md` — 삭제된 스크립트 3종을 현행으로 서술한 stale 문서. D 가 있었다면 로드 시 `미존재 3` 으로 즉시 노출 |

**feature 번호 제안**: #24 F-A · #25 F-D(+F-E) · #26 F-B · #27 F-C. 등록은 `/pilot:create-feature` 로 수동, 이후 `@pilot-planner → critic → generator → evaluator`.

**pilot 고유 제약**: `workspace/context/` 산출물 직접 Edit 금지(drift-protocol §A) — B 마이그레이션·C 규칙 생성은 `/pilot:learn`·`/pilot:doctor --fix` 경로로만. `scope/{domain}.md`·`rules/{domain}.md` 는 사용자 커스텀 layer — 생성기가 만들지 않으며 frontmatter 도 강제하지 않는다.

---

## 부록 B. Claude Code 소스 근거 표

경로는 `Claude-code-soruce/src/` 기준. 수치·규칙의 출처.

| 패턴 | 파일 | 확인한 내용 |
| --- | --- | --- |
| P1 | `memdir/memdir.ts` | `MAX_ENTRYPOINT_LINES = 200`, `MAX_ENTRYPOINT_BYTES = 25_000`, 색인 항목 "1줄 ~150자", 잘림 경고 문구, "Searching past context" 절(좁은 검색어로 grep, 트랜스크립트는 최후) |
| P1 | `memdir/memoryScan.ts` | `FRONTMATTER_MAX_LINES = 30`, `MAX_MEMORY_FILES = 200`, 매니페스트 포맷 `- [type] filename (ts): description` |
| P1 | `memdir/findRelevantMemories.ts` | Sonnet side query, 최대 5개, "확실할 때만", 최근 사용 도구의 참조 문서 제외, `alreadySurfaced` 필터, JSON 스키마 출력 |
| P1 | `utils/attachments.ts` `getRelevantMemoryAttachments` · `readMemoriesForSurfacing` | 5개 캡, 라인·바이트 캡 읽기, 잘림 안내, 신선도 헤더, 비동기 prefetch |
| P1 | `services/autoDream/consolidationPrompt.ts` | 4 phase consolidation, 200자 넘는 색인 항목 강등, 절대 날짜 변환, 모순 원본 수정 |
| P2 | `tools/ToolSearchTool/ToolSearchTool.ts` | `select:` 다중, `+필수어` 사전필터, 점수 12/10 · 6/5 · 3 · 4 · 2, 단어경계 정규식, 기본 `max_results 5`, exact-name fast path, pending 서버 안내 |
| P2 | `utils/toolSearch.ts` | `DEFAULT_AUTO_TOOL_SEARCH_PERCENTAGE = 10` |
| P3 | `utils/claudemd.ts` | 로드 순서(managed→user→project→local), 상향 탐색, `@include` depth 5, `parseFrontmatterPaths`(`/**` 제거, `**` 만이면 무조건), `processConditionedMdRules`(`ignore()` 매칭, 기준 = `.claude` 부모) |
| P3 | `utils/attachments.ts` `getNestedMemoryAttachmentsForFile` · `getNestedMemoryAttachments` | 트리거 집합 → cwd→대상 디렉토리 체인 걷기, `processedPaths` 중복 방지. `maybe('nested_memory', …)` 가 메인/서브 공통 첨부 목록(`:872`) 에 위치 — C1 서브에이전트 발화의 정황 근거(실측 필요) |
| P3 | `tools/FileReadTool/FileReadTool.ts:848,870,1038` | Read 가 `nestedMemoryAttachmentTriggers.add(path)` |
| P3 | `skills/loadSkillsDir.ts` | 스킬 `paths:` 조건부 활성(`activateConditionalSkillsForPaths`), 파일→cwd 상향 `.claude/skills` 발견(gitignore 제외), frontmatter 토큰만으로 비용 추정 |
| P3 | `utils/hooks.ts:434-438,621-652` | `hookSpecificOutput.additionalContext` — PostToolUse 선택, UserPromptSubmit 필수 |
| P4 | `tools/AgentTool/built-in/exploreAgent.ts` | 읽기 전용 금지 목록, haiku, `omitClaudeMd`, thoroughness 3단계, 병렬 호출 강제 |
| P4 | `tools/AgentTool/prompt.ts` | "When NOT to use Agent" 3규칙, 브리핑 원칙("이해를 위임하지 말라") |
| P4 | `tools/GrepTool/prompt.ts` · `tools/GlobTool/prompt.ts` | 출력 모드 3종, "여러 라운드 필요하면 Agent" |
| P5 | `memdir/memoryAge.ts` · `memdir/memoryTypes.ts` `TRUSTING_RECALL_SECTION` | 나이 문구, 1일 초과 staleness caveat, "존재했다는 주장 ≠ 지금 존재" 검증 규율 |
| P6 | `utils/agenticSessionSearch.ts` | substring 사전필터 → 100건 → 저가 모델 재랭킹, 우선순위 목록, 회수 우선 |
| P7 | `utils/codeIndexing.ts` | 외부 인덱서 감지 텔레메트리만. 자체 임베딩 없음 |
| P7 | `services/MagicDocs/magicDocs.ts` · `prompts.ts` | `# MAGIC DOC:` 감지 → 유휴 턴 서브에이전트 in-place 편집(비채택), 문서 철학 문구(차용) |
| 보조 | `native-ts/file-index/index.ts` | nucleo 식 퍼지 경로 매칭(경계 보너스·test 페널티) — @-멘션 파일 제안. 필요 시 A 의 `select:` 경로 보정에 차용 가능(이번 범위 밖) |
