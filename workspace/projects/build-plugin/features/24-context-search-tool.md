# #24 context-search — 섹션 단위 결정적 검색 도구

> source: prompt
> created: 2026-09-04T02:50:24Z
> user_prompt: "feature 생성해줘 — docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md §4 F-A 등록"
> plan: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-A (설계 상세·근거 SSOT. §2 P2·P4 패턴, 부록 A pilot 매핑)

## 요구사항

- **조건**: `workspace/context/` 아래 마크다운 도메인 지식 파일이 1개 이상 존재. 메타데이터(frontmatter) 없이도 동작해야 한다 — #26 보다 먼저 독립 출시.
- **트리거**: 래퍼 에이전트가 도메인 진입 파일(`workspace/context/{domain}/index.md`) 을 로드한 뒤 특정 주제(feature 제목 키워드·클래스명·소스 경로) 의 상세가 필요할 때. orchestrate-load 힌트가 사용을 **권장**한다 (soft — 필수 step 아님).
- **기대결과**:
  - `python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<질의>" [--scope {domain}] [--include features/ docs/] [--limit N] [--format json|md]` 1회로 상위 N 섹션의 `file · heading · level · line_start · line_end · score · matched · snippet(≤240자) · read_hint` 를 받는다.
  - 에이전트는 그중 1~2개를 `Read offset/limit` 부분 Read 한다 — 본문 파일 전체 Read·무차별 Grep 을 대체.
  - `wrapper-protocol.md` §6 의 수동 2단계 부분 로드(목차 → 라인 범위) 가 도구 호출 1단계 권장 문구로 바뀐다.
  - `confluence.py cmd_search` 가 같은 랭커 모듈을 import 해 순위·스니펫·상한을 갖는다 (출력 형식은 기존 유지).

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **색인 단위** = H2·H3 섹션 (헤딩 라인 ~ 같은 레벨 이상 다음 헤딩 직전). H1 만 있는 파일은 파일 전체 1 섹션. 코드블록(``` 펜스) 안의 `#` 는 헤딩이 아니다. frontmatter 는 색인 제외 (description 은 별도 필드 — #26 이후 가중치 신호로만).
- **코퍼스 기본 범위 = 지식 루트만** (`workspace/context/**/*.md`). `--scope {domain}` 은 `{domain}/`·진입 파일·`boundaries/{domain}--*` 로 좁힌다. `features/`·`docs/` 는 `--include` 명시 시에만 (Open Q (d)-1 확정).
- **질의 3형식** (Claude Code ToolSearch 그대로): `select:{path}[#{헤딩 일부}]` 직접 지정(점수 없이 반환) · `키워드 나열` · `+필수어 선택어` (필수어를 헤딩·경로·인용·본문 어디든 가진 섹션만 후보). 토큰이 경로처럼 보이면(`/` 포함 + 확장자) 인용 경로 일치를 자동 가중 — "이 소스 파일을 다루는 지식 섹션" 역방향 질의.
- **토큰화**: 소문자화 · 영숫자/한글/그 외 경계 분리 · `_` `-` `.` `/` 분리 · CamelCase 분리(원형 유지) · 1글자 토큰·최소 불용어 제거. **한글은 공백·구두점 분리만** — 형태소·n-gram 없음 (Open Q (d)-2 확정).
- **점수표** (토큰마다 합산, 신호별 섹션당 1회 — 빈도 미반영):

  | 신호 | 점수 |
  | --- | --- |
  | 헤딩 토큰 정확 일치 | 10 |
  | 파일 경로 세그먼트 정확 일치 (도메인명·파일명) | 8 |
  | 인용 경로 세그먼트 일치 (`file:line` 인용 경로에 토큰 포함) | 6 |
  | 헤딩 토큰 부분 일치 | 5 |
  | frontmatter description 단어경계 일치 (#26 머지 후 자동 활성 — Open Q (d)-3 확정) | 4 |
  | 본문 단어경계 일치 | 2 |

  동점: 얕은 헤딩(H2) → 진입 파일(index) → 경로 사전순. 점수 0 제외. 기본 `--limit 5`, 최대 20.
- **결정적**: 같은 코퍼스·질의 → 같은 출력·순서. 지식 파일 **읽기 전용** (수정 금지). 코퍼스 밖 traversal(`..`·절대경로 인자) 거부. 인용 경로의 존재 검증은 하지 않는다 (#25 의 일).
- **0건 처리**: 토큰별 히트 수 + 안내(`--scope` 제거 / `+필수어` 제거 / 토큰 분리 / 도메인 미등록이면 `/pilot:learn`). 실패가 아니라 상태 안내.
- **구현 제약**: 표준 라이브러리만(`re`·`pathlib`·`json`·`argparse`). 섹션 1,000개 코퍼스에서 300ms 이내. 캐시 없음. 모듈 docstring 필수 (`docs_build.py` 가 `docs/reference/tools/` 자동 생성).
- **soft 배선**: orchestrate-load 힌트 1줄 `[검색] 본문 상세는 python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<키워드>" --scope {domain} 로 섹션 조회 후 라인 범위 Read` + wrapper-protocol §6 권장 문구 교체 + scope-exploration.md 에 Explore 계약(scope 경로 + thoroughness 지정, 결론만 반환) 반영. 래퍼 필수 step 추가 0건, 지시 문서 순증 30줄 이내.

## 예외 케이스

- 헤딩 없는 파일 → 파일 전체 1 섹션, `heading: "(파일 전체)"`.
- 400줄 초과 섹션 → 스니펫만 + `read_hint` 에 "섹션이 크다 — 소제목으로 재질의 권장".
- 질의가 비었거나 토큰이 전부 제거됨 → 사용법 출력 후 exit 2.
- `--scope` 도메인이 MANIFEST 에 없음 → 코퍼스 전체로 fallback + INFO 1줄 (abort 안 함, A2).
- `select:` 대상 부재 → 유사 경로 후보 최대 3개 제시.
- `confluence.py` 재사용 시 docs/ 는 H1/H2 분할이 기존 규약 — 랭커는 공유하되 섹션 분할 규칙은 confluence.py 쪽 기존 값 유지.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] 코퍼스 기본 범위 — 지식 루트만인가, features/·docs/ 도 기본 포함인가 → 지식 루트만. 부속 문서는 `--include` 명시 시에만 (2026-09-04 사용자 확정)
- [x] 한글 토큰화 수준 — 공백·구두점 분리만 vs 2-gram 추가 → 공백·구두점 분리만. 골든 질의 `hit@3` 부족 시에만 보강 검토 (2026-09-04 사용자 확정)
- [x] description 가중치 4점 활성 시점 → #26 머지 후 자동. frontmatter 있는 파일만 가산, 플래그 없음 (2026-09-04 사용자 확정)

## 검증 기준

- 단위 테스트: 토큰화(CamelCase·경로·한글) · 점수 합산 · `+필수어` 사전필터 · 코드블록 내 `#` 무시 · 라인 범위 정확성 · `select:` · 0건 안내 · traversal 거부.
- 골든 질의 3개(`pilot` 도메인): 기대 섹션이 top-3 안 (`hit@3`). 예: "부분 로드 라인 범위" → `pilot/index.md` 또는 `lifecycle.md` 해당 섹션.
- dogfooding: 후속 feature 1건에서 planner 가 도구를 1회 이상 사용해 부분 Read 로 이어진 기록.
- `python3 -m unittest discover -s pilot/tests/tools` 전체 통과 + doctor 클린 + `docs_build.py --check` 통과.

## 관련 파일 범위

- **신규**: `pilot/tools/context-search.py` · `pilot/tests/tools/test_context_search.py`
- **변경**: `pilot/tools/orchestrate-load.py` — `build_load_plan` 4) 도메인 진입 파일 로드 직후 힌트 1줄 (`:467` 부근)
- **변경**: `pilot/skills/context/shared/wrapper-protocol.md` §6 부분 로드 (`:32`) — 도구 호출 권장 문구로 교체
- **변경**: `pilot/skills/context/domain/scope-exploration.md` — Explore 서브에이전트 계약(thoroughness·결론만·scope 경로) 반영
- **변경**: `pilot/tools/confluence.py` `cmd_search` (`:767`) — 랭커 모듈 import, 출력 형식 유지
- **문서**: `pilot/docs/reference/tools/context-search.md` (docs_build 자동 생성) · 필요 시 `pilot/mkdocs.yml` nav
- **버전**: #24~#27 묶음 minor bump (`0.10.0` → `0.11.0`) — 개별 PR 은 bump 없음, 마일스톤 마감 PR 에서 1회
