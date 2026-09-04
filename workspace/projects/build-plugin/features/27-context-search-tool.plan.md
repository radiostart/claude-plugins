# 구현 계획: #27 context-search — 섹션 단위 결정적 검색 도구

> mode: standard (tdd=false · mode=null) · 작성: 2026-09-04 planner · focus: 없음 (`.focus.md` 부재)
> 대상 spec: [27-context-search-tool.md](27-context-search-tool.md) · 설계 SSOT: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-A · §2 P2/P4 · 부록 A
> 브랜치 권고: `skills/24-context-search` — `skills/24-pilot-update-tool` 은 폐기된 구 #27 (번호 회수, slug 상이) 라 혼용 금지
> critic 반영: 2026-09-04 재호출 — C1~C8 전건 accepted (합의 표: [27-context-search-tool.plan.critic.md](27-context-search-tool.plan.critic.md)). 사용자 결정: C1 필수 반영 · C2~C8 planner 위임

## 실측 baseline (2026-09-04)

- `python3 -m unittest discover -s pilot/tests/tools` → **292 tests OK**
- `python3 pilot/tools/doctor.py workspace` → **11 PASS · 0 WARN · 0 ERROR**
- `python3 pilot/tools/docs_build.py --check` → exit 0 (tools 8종: auto_pilot·confluence·docs_build·doctor·orchestrate-load·plan-validate·regen-verify·slack-notify)
- 코퍼스 `workspace/context/`: `MANIFEST.md` + `config.md` + `pilot/{index,lifecycle,spec,modes,review,delivery}.md` — 605줄 · 43KB · **H2 26개(pilot/* 20 · MANIFEST 1 · config 5) · H3 2개(`config.md:40`·`:45` — H3 포함 규칙이 라이브 G2 에서 실제로 실행됨) · frontmatter 0개 · `boundaries/` 없음** (C7 정정). 펜스 12쌍(들여쓴 펜스 포함, 펜스 안 `#` 헤딩 없음).
- 앵커 확인(spec 인용 그대로 실재): `orchestrate-load.py:463-486` (4) 진입 파일 로드 블록, 루프 종료 `:478`) · `confluence.py:767-812` (`cmd_search`) · `wrapper-protocol.md:32-39` (§6, 8줄) · `scope-exploration.md:7-11` (공통 원칙 1~3).
- 기존 테스트는 `hints` 를 `any(... in h for h in hints)` 로만 검사 — 힌트 1줄 추가에 무손. `test_confluence.py` 에 `cmd_search` 테스트 없음.

## 결정 사항 (spec 이 위임한 세부 — 확인 응답으로 뒤집을 수 있음)

| # | 결정 | 근거 |
| --- | --- | --- |
| D1 | 본문·description "단어경계" — ASCII 토큰은 **양측 경계**(`[0-9A-Za-z가-힣]` 외 문자), **한글 포함 토큰은 좌측 경계만** (우측 조사 허용: `섹션을`·`로드의` 에 `섹션`·`로드` 매칭) | 형태소·n-gram 없이(Open Q (d)-2 확정) 조사 때문에 본문 신호가 사실상 0 이 되는 것을 막는 최소 규칙. 헤딩은 토큰 정확/부분 일치라 별도 규칙 불필요 |
| D2 | 골든 질의 3개는 **고정 스냅샷 fixture** (`pilot/tests/fixtures/context-search/workspace/context/` ← 현재 `workspace/context/{MANIFEST.md,pilot/*.md}` 복사) 로 단위 테스트. 라이브 코퍼스 `hit@3` 는 evaluator 가 실측해 기록 | #22 재학습이 라이브 코퍼스를 바꿔도 테스트가 흔들리지 않음. unittest 는 hermetic |
| D3 | `--format` 기본값 `md` | 에이전트 transcript 가독성. json 은 로더·훅·점검기용 |
| D4 | `confluence.py cmd_search`: 랭커 점수순 · **상한 5건** + `… 외 N건` 1줄 · 본문은 **첫 일치 주변 2,000자 창**(기존 `[:2000]` 상한 유지, 시작점만 이동). 랭커 로드 실패 시 stderr `[WARN]` + 기존 substring 거동 (A2) | "순위·스니펫·상한을 갖되 출력 형식 유지" — 헤더·`### [file] heading`·본문 블록·0건 문구 골격 불변 |
| D5 | 랭커는 단일 파일 `context-search.py` 안의 순수 함수 (별도 `_lib.py` 신설 없음). 하이픈 파일이므로 `confluence.py` 는 `importlib.util.spec_from_file_location` 으로 지연 로드 (테스트 로더와 동일 패턴) | spec 관련 파일 범위 준수. docs_build 가 `_` 접두 파일을 제외하므로 분리해도 문서 이득 없음 |
| D6 | `+필수어` 는 사전필터 **겸** 점수 기여 (필수어만 있는 질의도 순위가 생김) | ToolSearch 는 필수어를 필터로만 쓰지만 pilot 질의는 대개 1~3 토큰이라 필터만 두면 동점 과다 |
| D7 | H2 가 있는 파일의 **서문(H1 ~ 첫 H2 직전)** 도 `level: 1`, `heading = H1 텍스트` 섹션으로 색인 (H1 제외 본문이 비어 있으면 생략). H1 만 있는 파일 = 파일 전체 1 섹션(H1 텍스트) · 헤딩 없는 파일 = `(파일 전체)`. **level 1 섹션은 heading 신호(+10/+5) 를 받지 않는다** — `heading` 은 표시용, 점수는 경로·인용·description·본문만. 동점 정렬도 H2 → H3 → level 1 순 (C2) | 진입 파일 서문이 요약을 갖는다 (`pilot/index.md:3`). critic C2 실측: 모든 H1 이 "pilot — X skills" 라 서문 6개가 `pilot`·`skills` 헤딩 정확 일치로 57점 decoy 가 되어 top-5 의 60% 를 차지 → heading 신호 차단으로 ≤ 37 로 해소, 골든 1위 불변. H1-only 파일은 제목이 path 신호(+8)·본문으로 대표된다는 trade-off 수용 |
| D8 | `--scope` 의 MANIFEST 진입 파일 조회와 `--project` 기본값(STATE.md 진행중)은 `orchestrate-load.py` 의 `parse_manifest_domain_files`·`parse_state_md_active` 를, `--scope`·`--project` 인자의 traversal 판정은 같은 모듈의 `has_path_traversal()` (`:365` — `/`·`\`·`..` 중 하나라도 있으면 True; orchestrate-load 자신도 `:662`·`:729` 에서 project·domain 에 같은 검사) 를 importlib 로 **재사용** (C1). 로드 실패 시 INFO 1줄 + 폴더 기반 scope 만 (A2) — 단 traversal 판정은 동등한 로컬 1줄(`"/" in v or "\\" in v or ".." in v`) 로 **항상** 수행 | MANIFEST 표 파서 SSOT 유지 — #06/#20 anchored 정규식 실버그를 세 번째 복제본으로 재발시키지 않음 |

## 변경 파일

- [x] `pilot/tools/context-search.py` — **신규**. 랭커 라이브러리 + CLI (표준 라이브러리만 · 모듈 docstring 필수)
- [x] `pilot/tests/tools/test_context_search.py` — **신규**. 단위 테스트 + 골든 `hit@3` 4질의(`--scope pilot`)
- [x] `pilot/tests/fixtures/context-search/workspace/context/{MANIFEST.md,pilot/*.md}` + `README.md` — **신규** 스냅샷 (D2, 7파일 복사 + 안내 1)
- [x] `pilot/tools/orchestrate-load.py` — `build_load_plan` 4) 진입 파일 로드 루프 직후 힌트 1줄 (`:478` 뒤, `if entries:` 안) + 4) 주석 1줄
- [x] `pilot/tests/tools/test_orchestrate_load.py` — 힌트 존재/부재 테스트 2건
- [x] `pilot/tools/confluence.py` — `cmd_search` (`:767-812`) 를 `search_docs()` 순수 함수 + 출력으로 분리, 랭커 지연 import (D4)
- [x] `pilot/tests/tools/test_confluence.py` — `search_docs` 순위·상한·폴백 2종·`match_pos` 5건 (C4)
- [x] `pilot/skills/context/shared/wrapper-protocol.md` — §6 (`:32-39`) 권장 문구 교체 (순증 ≤ +2)
- [x] `pilot/skills/context/domain/scope-exploration.md` — 공통 원칙 2 에 Explore(P4) 계약 + 비사용 규칙 + 지식 파일 탐색 1줄 (순증 ≤ +8)
- [x] `pilot/docs/reference/index.md:25` — Tools 카드 목록에 `context-search` 삽입 (알파벳순)
- [x] `pilot/docs/reference/tools/{context-search.md,index.md}` — `docs_build.py` 재생성 (git 미추적 — 상태 기반 증거, G6)

무변경 확정 (의도적):

- `pilot/agents/*.md` — 필수 step 추가 0 (G4). "부분 로드" 라는 절 이름은 유지되므로 wrapper 상단 인용문도 그대로 유효.
- `pilot/mkdocs.yml` — `Tools: reference/tools/` 는 literate-nav 자동 색인.
- `pilot/.claude-plugin/plugin.json`·`mkdocs.yml extra.version`·`docs/index.md` — minor bump(0.10.0 → 0.11.0) 는 #27~#30 마일스톤 마감 PR 1회.
- `workspace/context/**` — 읽기 전용 (drift-protocol § A). 골든 fixture 는 복사본.
- `orchestrate-load.py` `build_instructions` — instructions 무변경 (soft: hints 만).

## 구현 순서

구간 A (스텝 1~3) 완료 후 체크포인트(G1·G2) → 구간 B (스텝 4~6). 한 구간에 3 스텝 초과 금지.

### 1. `context-search.py` — 랭커 + CLI

모두 순수 함수, 모듈 레벨 실행 코드 없음(importlib 로 로드돼도 부작용 0). 진입 `if __name__ == "__main__": sys.exit(main())`, `main(argv=None) -> int`.

**상수**

- `DEFAULT_LIMIT = 5` · `MAX_LIMIT = 20` · `SNIPPET_CHARS = 240` · `LARGE_SECTION_LINES = 400`
- `SCORE = {"heading_exact": 10, "path": 8, "citation": 6, "heading_partial": 5, "description": 4, "body": 2}`
- `STOPWORDS_EN = {the, a, an, and, or, of, to, in, on, for, is, are, be, with, as, at, by, from, this, that, it}` · `STOPWORDS_KO = {및, 등, 또는, 그리고, 경우, 때, 것, 수, 위한, 대한, 통해, 따라, 이후, 이전, 모든}` — 최소 목록. 확장은 골든 `hit@3` 근거가 있을 때만.
- `WORD = "[0-9A-Za-z가-힣]"` — 경계 판정 문자 클래스. `\w` 는 `_` 를 포함하므로 사용 금지.

**토큰화** `tokenize(text) -> list[str]`

1. `re.findall(r"[A-Za-z0-9]+|[가-힣]+", text)` — 영숫자 런/한글 런 분리. `_`·`-`·`.`·`/`·`:`·공백·구두점·백틱은 자동 분리, 영숫자↔한글 경계도 분리.
2. 영숫자 런은 CamelCase 분리 `re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", run)` → 조각들 + **원형** (`CyberBongoRegister` → `cyber bongo register cyberbongoregister`).
3. 소문자화 → 길이 1 제거 → 불용어 제거 → 순서 보존 dedupe.
- `path_tokens(path_str)`: 마지막 세그먼트의 확장자(`\.[A-Za-z0-9]{1,5}$`) 를 떼고 `tokenize` — `md`·`py` 같은 확장자 토큰이 경로·인용 신호를 오염시키지 않게.

**질의** `parse_query(raw) -> Query` (dataclass: kind, optional, required, raw_paths, select_path, select_heading)

- `raw.strip()` 이 `select:` 로 시작 → `kind="select"`, `select_path` = `select:` 뒤 `#` 앞, `select_heading` = `#` 뒤(없으면 None). 이후 토큰 무시.
- 그 외 공백 분리: `+w` → `required += tokenize(w)` (`+orchestrate-load` → `orchestrate`,`load` 둘 다 필수) · 나머지 → `optional`. 단어가 **경로형**(`/` 포함 + 확장자) 이면 `path_tokens(w)` 를 토큰으로 넣고 원문을 `raw_paths` 에 보존.
- 토큰 0개(빈 질의·불용어만) → `main` 이 사용법 출력 + **exit 2**.

**섹션 분할** `split_sections(text, rel_path) -> list[Section]` (`Section` dataclass: file, heading, level, line_start, line_end, body_lines, description)

- frontmatter: 1행이 `---` 이고 닫는 `---` 가 있으면 그 범위 색인 제외, `^description:\s*(.+)$` **첫 줄만** 보관(양끝 따옴표 제거). 없어도 정상 (#29 이전 코퍼스).
- 펜스 추적: `^\s*(```|~~~)` 로 열고 **같은 문자**로 닫는다(info string 무시). 펜스 안 `#` 라인은 헤딩이 아니다.
- 헤딩: `^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$`. 색인 레벨 = 2·3. 섹션 범위 = 헤딩 라인 ~ **레벨 숫자가 같거나 작은** 다음 헤딩 직전 (H2 본문은 하위 H3 포함). `line_start`/`line_end` 1-based inclusive, 끝의 빈 줄 포함(Read 편의 우선).
- D7: 첫 H2/H3 이전 구간 → `level 1` 섹션(heading = H1 텍스트, H1 없으면 `(서문)`), H1 제외 본문이 비어 있으면 생략. H2/H3 이 하나도 없으면 파일 전체 1 섹션(heading = H1 텍스트 또는 `(파일 전체)`, level 1). **level 1 섹션은 heading 신호 미적용** (C2 — 「점수」 참조).

**신호 추출** (섹션당 1회 계산, 소문자)

- `heading_tokens = set(tokenize(heading))`
- `path_tokens_set = set(path_tokens(rel_path))` — 코퍼스 루트 기준 상대경로 세그먼트 전체 (`pilot/index.md` → `pilot`,`index`)
- **공개 함수** `extract_citations(body, memo=None) -> (citation_tokens: set[str], citation_paths: list[str])` (C4-3 — 스텝 4 의 confluence 가 이 이름으로 호출): 본문에서 `re.findall(r"[A-Za-z0-9_.\-]*(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]{1,5}(?::\d+(?:-\d+)?)?", body)` — `/` 를 1개 이상 포함하고 확장자를 가진 경로(선택적 `:N[-M]`). `${CLAUDE_PLUGIN_ROOT}/tools/doctor.py` 처럼 앞에 비허용 문자가 있으면 `/tools/doctor.py` 부분만 잡힌다 — 세그먼트 토큰 목적이라 충분. 존재 검증 없음(#28 의 일). `citation_tokens = ∪ path_tokens(p)` · `citation_paths = [p without :line]`. `memo` 는 `search()` 1회 안에서 만들어 넘기는 dict — 같은 인용 문자열의 `path_tokens` 재계산을 막는 **실행 내 memo** (C5: 1,000섹션·인용 30/섹션 고밀도에서 `path_tokens` 31k회 = 총 0.83s 의 52% 가 이 경로. "캐시 없음" 은 실행 간 영속 캐시 금지를 뜻한다 — 주의사항 참조).
- `body_lc` = 헤딩 라인 제외 본문 소문자 · `description_lc`.

**점수** `score_text(query, *, heading, body, path_tokens=(), citation_tokens=(), citation_paths=(), description=None) -> (score, matched)` — 문자열 기반 진입점(스텝 4 의 confluence 재사용용). `score_section(section, query)` 는 이를 호출. 토큰 t 마다, 신호별 최대 1회:

| 조건 | 점수 |
| --- | --- |
| t ∈ heading_tokens | +10 (정확 — 이때 부분 판정 생략) |
| t ∈ path_tokens_set | +8 |
| t ∈ citation_tokens | +6 |
| 정확 아님 && `any(t in h for h in heading_tokens)` | +5 |
| description 경계 일치 (D1) | +4 |
| body 경계 일치 (D1) | +2 |
| `raw_paths` 의 p 가 어떤 `citation_paths` c 의 **세그먼트 정렬 suffix** (`c == p` 또는 `c.endswith("/" + p)`) | +6 (인용 신호, `matched` 에 원문 p 기록) |

- **level 1 섹션**(서문·파일 전체)에는 heading 정확/부분 행을 적용하지 않는다 (C2). 나머지 신호는 동일.
- 경계 정규식 (D1): ASCII 토큰 `(?<!{WORD}){re.escape(t)}(?!{WORD})` · 한글 포함 토큰 `(?<!{WORD}){re.escape(t)}`. `re.search` 1회 → 빈도 미반영.
- `required` 토큰은 위 신호 중 하나라도 있어야 후보(사전필터). 통과 시 점수도 합산 (D6).
- `matched` = 일치한 토큰(질의 순서) + 일치한 raw path.

**순위** `rank(sections, query, limit)` — `score > 0` 만. 정렬 키 `(-score, level_rank, 0 if is_entry else 1, file, line_start)`; `level_rank = {2: 0, 3: 1}.get(level, 2)` — H2 → H3 → level 1(서문·파일 전체) 순, 헤딩 섹션 우선 (C2). `is_entry` = 파일명 `index.md`; `--scope d` 지정 시 MANIFEST 의 d 진입 파일도 포함(D8). scope 미지정 시 MANIFEST 조회 없음 — `parse_manifest_domain_files` 가 도메인 인자를 요구하고 전 도메인 순회 함수는 없다 (C6-a). `limit` 을 `[1, MAX_LIMIT]` 로 clamp — 초과는 20 + INFO, 1 미만은 exit 2.

**스니펫·힌트**

- `snippet`: 본문(헤딩 제외)을 공백 정규화한 1줄에서, 가장 앞선 본문 일치 위치 기준 `[pos-80, pos+160)` 창, 잘린 쪽에 `…`, 총 ≤ 240자. 본문 일치가 없으면(헤딩·경로만 일치) 앞 240자.
- `read_hint`: `Read {file} offset={line_start} limit={line_end-line_start+1}`. 섹션이 400줄 초과면 `섹션이 크다({n}줄) — 소제목으로 재질의 권장 (앞부분만: Read {file} offset={line_start} limit=80)`.
- `file` = CWD 기준 상대경로(`os.path.relpath`) — 에이전트가 그대로 Read 인자로 붙일 수 있게.

**코퍼스** `collect_files(workspace, scope, includes, project) -> (files, info, entry_files)`

- **인자 traversal 거부 (C1 — spec 비즈니스 규칙 "코퍼스 밖 traversal 거부")**: `--scope`·`--project` 는 식별자다. `has_path_traversal(v)` (D8 재사용; 로드 실패 시 동등 로컬 판정) 가 True 면 stderr `scope/project 인자에 경로 구분자·'..' 사용 불가: {v}` + **exit 2**. 이유: `pathlib` 는 `Path(root) / "/etc"` → `/etc`, `root / "../projects"` → 루트 밖으로 **조용히** 샌다 — `--scope /etc` 는 코퍼스 루트를 통째로 바꿔치기하고 `--scope ../projects` 는 Open Q (d)-1 "지식 루트만" 을 무력화하므로 보간 전에 막는다. `--workspace` 는 코퍼스 루트를 정의하는 인자라 검사 대상이 아니다.
- 기본: `root = {workspace}/context` 의 `**/*.md`. `config.md` 도 포함(지식 루트 안).
- `--scope d`: `{root}/d/**/*.md` + `{root}/d.md` + MANIFEST 진입 파일(D8) + `{root}/boundaries/{d}--*.md`·`*--{d}.md` (orchestrate-load 5) 와 동일 양방향). 어느 것도 없고 MANIFEST 행도 없으면 → 전체 코퍼스 + INFO `scope '{d}' 가 MANIFEST/폴더에 없음 — 코퍼스 전체로 검색. 도메인 미등록이면 /pilot:learn {진입점}` (abort 없음, A2).
- `--include X ...`: X 에 `..` 세그먼트 또는 절대경로 → stderr 거부 + **exit 2**. 해석 순서 `{workspace}/projects/{project}/X` → `{workspace}/X`; 둘 다 없으면 INFO skip. `project` = `--project` 또는 STATE.md 진행중 첫 항목(D8; 없으면 INFO).
- **수집 후 봉쇄 검증 (C1)**: 모든 후보 파일은 `resolve()` 결과가 지식 루트 `root.resolve()` 안이어야 하고, `--include` 파일은 `{workspace}.resolve()` 안이어야 한다. 밖으로 나가는 파일(심볼릭 링크 탈출 등)은 **제외 + INFO `코퍼스 밖 링크 {n}건 제외`**. glob 은 symlink 를 따르므로 이 검증이 두 번째 방어선이다.
- **dedupe·정렬 (C6-b)**: 후보는 `set` 으로 모은 뒤 상대경로 오름차순 `sorted` — `--scope d` 의 `{root}/d/**` 와 MANIFEST 진입 파일(`pilot/index.md` 는 이미 `d/` 안) 중복 수집으로 같은 섹션이 두 번 나오지 않게. 결정성의 근거이기도 하다.
- 파일 read `encoding="utf-8", errors="replace"`. 실행 간 캐시 없음. 코퍼스 루트 부재 → stderr + exit 2.

**select** — `select_path` 에서 `workspace/context/` 접두 제거 후 코퍼스 파일 상대경로와 비교(`..`·절대경로 → exit 2). 존재: 해당 파일의 섹션 전부(`select_heading` 지정 시 헤딩 텍스트 대소문자 무시 부분 일치만), `score: null`, `matched: []`. 부재: 결과 0 + `suggestions` ≤ 3 (경로 세그먼트 토큰 공유 수 내림차순 → 경로 오름차순 — `difflib` 미사용).

**0건 안내** — `zero_hit: {token_hits: {t: 일치 섹션 수}, guidance: [...]}`. guidance 는 조건부: `--scope` 제거(scope 지정 시) · `+필수어` 제거(필수어 있을 때) · 토큰 분리 예(원 질의에 `_`/`-` 있을 때, 예 `cyber_bongo` → `cyber bongo`) · **`token_hits` 가 0 인 한글 토큰이 있으면 조사 제거 재질의 (예: `섹션을` → `섹션`)** (C8 — D1 은 본문 쪽 조사만 흡수하고 질의 쪽 조사는 흡수하지 않는다; 랭커 변경 없음) · 도메인 미등록이면 `/pilot:learn`. **exit 0** (실패가 아니라 상태 안내).

**출력**

- json: `{"query", "root", "scope", "include": [...], "candidates": N, "returned": k, "results": [{file, heading, level, line_start, line_end, score, matched, snippet, read_hint}], "info": [...], "zero_hit": {...} | null}` — `json.dumps(ensure_ascii=False, indent=2)`.
- md: 1줄 헤더(질의·scope·후보/표시 수) + 결과 표 `# | file | heading | lines | score | matched` + 결과별 `> snippet` 과 `read_hint` 줄 + INFO/0건 안내 블록. 필수 요소만 고정, 레이아웃은 Generator 재량.
- exit: **0** (0건 포함) · **2** (빈 질의·토큰 전멸·traversal·`--limit < 1`·`--format` 오류·코퍼스 루트 부재).

**CLI** (`argparse`): `query` positional(**첫 인자** — `--include` 가 `nargs="+"` 라 뒤에 오면 흡수됨, docstring 에 명시) · `--workspace` (기본 `workspace`) · `--project` · `--scope` · `--include` (`nargs="+"`) · `--limit` (int, 기본 5) · `--format` (`md|json`, 기본 `md`, D3).

**docstring** (docs_build 가 그대로 reference 페이지로 추출 — **첫 줄이 tools/index 설명**): 용도 1줄 → Usage → 질의 3형식 → 점수표 → 출력 스키마 → exit 코드 → 제약(읽기 전용·결정적·stdlib·캐시 없음).

### 2. `test_context_search.py` + 골든 fixture

로더: `importlib.util.spec_from_file_location("context_search_mod", PLUGIN_ROOT / "tools" / "context-search.py")` (`test_orchestrate_load.py` 패턴). 단위 테스트는 `tempfile.TemporaryDirectory()` 에 소형 코퍼스를 만들어 검증 — MANIFEST(`## 도메인 분류` 표에 alpha·beta) + `alpha/index.md`(H2 2·H3 2) · `alpha/services.md` · `beta/index.md` · `boundaries/alpha--beta.md` · `boundaries/gamma--alpha.md` · frontmatter+description 파일 · 펜스 안 `# not heading` 파일(들여쓴 펜스 포함) · H1-only 파일 · 헤딩 없는 파일 · `projects/P/features/01-x.md` + `STATE.md`(P 진행중).

케이스 (spec 검증 기준 1:1 — 각 항목 최소 1 테스트):

- 토큰화: CamelCase 조각+원형 · 경로 세그먼트(확장자 제외) · 한글 공백 분리(`배송취소 서비스` → 정확히 2토큰, 형태소 분리 없음) · 1글자·불용어 제거 · 소문자·dedupe.
- 섹션: H2/H3 라인 범위 정확(1-based inclusive) · H2 본문이 H3 포함 · 펜스 안 `#` 무시 · frontmatter 제외 + description 보관 · H1-only 1섹션 · 헤딩 없음 `(파일 전체)` · D7 서문 level 1(본문 비면 생략).
- 점수: 신호값 6종 정확 · 빈도 미반영(같은 토큰 3회 = 2점) · 정확 시 부분 미가산 · ASCII 양측 경계(`load` ≠ `payload`) · 한글 좌측 경계(`섹션을` 매칭, `가섹션` 미매칭) · 경로형 질의 suffix +6 (`services/x.rb` ↔ 인용 `app/services/x.rb:12`) · **level 1 섹션은 heading 신호 0** (H1 토큰 질의 → path/본문 점수만) (C2).
- `+필수어` 사전필터 · 필수어만 있는 질의도 순위 존재(D6).
- 순위: 동점 H2 → H3 → level 1 → index → 경로순 (C2) · 점수 0 제외 · `--limit 25` → 20 + INFO · `--limit 0` → exit 2.
- scope: alpha 폴더+진입+boundaries 양방향 포함, beta 제외 · 미등록 scope → 전체 + INFO · **dedupe**(진입 파일이 `alpha/` 안에 있어도 섹션 1회) (C6-b) · scope 미지정 시 `is_entry` 는 `index.md` 파일명만 (C6-a).
- **traversal (C1)**: `--scope ../projects` · `--scope /etc` · `--project ../x` → `main([...])` 반환 2 + stderr 문구 · D8 로드 실패를 흉내낸 상태(로더가 `None` 을 돌려주게 패치)에서도 동일 판정 · **심볼릭 링크 탈출**: `{root}/evil` → 외부 임시 폴더(`x.md` 포함) 링크 → 결과·`candidates` 에 `x.md` 없음 + INFO `코퍼스 밖 링크 1건 제외`.
- include: `features` → `projects/P/features` 해석 · `..`·절대경로 → `main([...])` 반환 2 · 없는 include → INFO skip.
- select: 파일 전부 / `#헤딩일부` / 부재 시 후보 ≤3 / traversal → 2.
- 0건: `token_hits` 카운트 + guidance 조건부 항목 존재/부재.
- 빈 질의·불용어만 → 2 + 사용법(stdout/stderr 캡처).
- 스니펫 ≤240 · 일치 토큰 포함 · `read_hint` 형식 · 401줄 섹션 → "섹션이 크다" 문구.
- 결정성: 파일 생성 순서를 바꿔 두 코퍼스 → json 문자열 동일.
- 성능: 200파일 × 5섹션 = 1,000섹션 임시 코퍼스, **섹션당 `file:line` 인용 ≥ 5**(병목 경로를 실제로 측정, C5) → `search()` 1회 **< 1.0s** (완화 상한; 300ms 목표는 G3 에서 `time` 실측·기록). memo 유무 결과 동일성(같은 json) 1건.
- 골든 (D2 fixture — **`--scope pilot` 으로 실행**해 G2 라이브 실측과 조건을 맞춘다: fixture 에는 `config.md` 가 없어 무-scope 후보 집합이 라이브와 다르다 (C3). `hit@3` 에 (file, heading 부분문자열) 포함):
  1. `"doctor 정합성 검사"` → `pilot/lifecycle.md` · `/pilot:doctor`
  2. `"slack webhook 알림"` → `pilot/delivery.md` · `/pilot:slack`
  3. `"pilot/skills/learn/SKILL.md"` (역방향 경로 질의) → `pilot/spec.md` · `/pilot:learn`
  4. `"도메인 진입 파일 자동 로드"` (**한글 단독** — Open Q (d)-2 의 재검토 트리거가 한글 질의를 실제로 측정하도록, C3) → `pilot/index.md` · `Cluster 진입`

  기대 점수(critic C2 프로토타입 실측 + C2 반영 재계산): 1) 22 (heading 10 + citation 6 + body 2 + 정합성 2 + 검사 2) vs 차순위 10 (`lifecycle.md ## /pilot:project`) · 2) 22 vs ≤ 10 · 3) 66 vs `index.md ## 스킬 17 개` 46, 다른 `## /pilot:x` 42, 서문 6개는 heading 신호 차단으로 ≤ 37 (차단 전 57 — decoy) · 4) 14 (진입 heading 10 + 진입·파일 본문 2+2) vs ≤ 4 (`## /pilot:project`·`## /pilot:issue` 의 "도메인 컨텍스트 로드"; MANIFEST `## 도메인 분류` 16 은 `--scope pilot` 밖). 공통 토큰 `pilot`·`skills`·`skill` 은 상수 오프셋. spec 예시 질의 "부분 로드 라인 범위" 를 쓰지 않는 사유: 코퍼스가 `pilot/skills/` 만 학습해 wrapper-protocol 본문이 없다 — 실측 최고점 4(`## /pilot:project`) 로 정답이 존재하지 않는 질의. `"조건부 인터뷰"` 는 `## /pilot:analyze` = `## /pilot:create-feature` 동점이라 채택하지 않음. **미달 시 랭커를 임의 조정하지 말고** 실측 표를 이 plan 에 기록 후 보고 — Open Q (d)-2 는 `hit@3` 부족 시에만 보강 검토를 허용한다.

fixture 생성: `mkdir -p pilot/tests/fixtures/context-search/workspace/context/pilot && cp workspace/context/MANIFEST.md pilot/tests/fixtures/context-search/workspace/context/ && cp workspace/context/pilot/*.md pilot/tests/fixtures/context-search/workspace/context/pilot/` + `README.md`(스냅샷 일자 2026-09-04 · 용도 = 랭커 골든 · 갱신 규칙 = 재학습 후 갱신은 선택이되 갱신 시 `hit@3` 재확인 필수 · #22 드리프트 3건이 그대로 들어 있어도 랭킹 테스트에는 무관).

### 3. `orchestrate-load.py` 힌트 1줄 + 테스트

`build_load_plan` 4) 블록 — `for rel in entries:` 루프 종료 직후(`:478` 뒤, 여전히 `if entries:` 안):

```python
            hints.append(
                f"[검색] 본문 상세는 python3 {plugin_root()}/tools/context-search.py "
                f'"<키워드>" --scope {domain} 로 섹션 조회 후 라인 범위 Read'
            )
```

- `plugin_root()` 사용 → `files_to_read` 와 같은 `${CLAUDE_PLUGIN_ROOT}` 리터럴/해석값 규칙.
- 진입 파일 0건(미등록) 이면 힌트 없음 — 기존 부트스트랩 안내가 우선.
- 4) 주석 블록에 1줄: `#    진입 파일 로드 직후 context-search 권장 힌트 1줄 (#27, soft — instructions 불변)`.
- 테스트(`test_orchestrate_load.py`, 기존 `ManifestDomainFiles`/`BuildLoadPlan` 류 픽스처 재사용): `test_domain_entry_adds_context_search_hint` (힌트에 `context-search.py` 와 `--scope orders` 포함, 정확히 1줄) · `test_no_domain_no_context_search_hint` (`domain=None` → 부재) · 기존 `build_instructions` 테스트 무손.

**체크포인트 G1·G2** — 여기서 `python3 -m unittest discover -s pilot/tests/tools` 전체 통과 확인 후 구간 B 진입.

### 4. `confluence.py cmd_search` 랭커 공유 (D4)

- `_load_context_search()`: `importlib.util` 로 `Path(__file__).resolve().parent / "context-search.py"` 로드, 실패(`OSError`·`ImportError`·`AttributeError`) 시 `None`. **모듈 상단 import 아님** — `fetch`/`all` 경로 무영향.
- `search_docs(md_files: list[Path], keyword: str, limit: int = 5, ranker=None) -> tuple[list[dict], int]` **순수 함수** 신설: 기존 분할 규칙 그대로(`re.split(r"\n(?=#{1,2} )", text)`, 헤딩 추출, `(서문)`), 조각마다 `tokens, paths = ranker.extract_citations(body)` → `ranker.score_text(query, heading=..., body=..., path_tokens=ranker.path_tokens(md_file.name), citation_tokens=tokens, citation_paths=paths)` 채점 → `score > 0` 만 `(-score, file, 등장순)` 정렬 → `(상위 limit, 총 일치 수)`. 각 결과 dict 에 `match_pos` 포함.
  - **substring 폴백 조건 (C4-1)**: ① `ranker is None` (로드 실패) → stderr `[WARN] context-search 랭커 로드 실패 — 무순위 substring 검색으로 대체` · ② `ranker.parse_query(keyword)` 가 `kind == "select"` 이거나 토큰 0개(1글자·불용어만 — 기존 substring 은 "A" 한 글자도 찾았으므로 조용한 회귀 방지) → **무음**으로 기존 substring 경로(`kw_lower in section.lower()`, 등장순, `match_pos = section.lower().find(kw_lower)`). `select:` 의 `workspace/context/` 상대경로 의미는 docs/ 에 없으므로 해석하지 않는다.
  - **`match_pos` 정의 (C4-2)**: 소문자화한 섹션 문자열(헤딩 라인 포함)에서 `matched` 토큰들의 D1 경계 일치 위치 중 **가장 앞선 것**; 본문 일치가 없으면(헤딩·경로·인용 신호만) `0`. 출력 창 = `start = max(0, match_pos - 200)`, `section[start : start + 2000]`.
- `cmd_search(keyword)`: 프로젝트·docs/ 존재 검사는 기존 그대로 → `search_docs(...)` → 출력. 헤더 `'{kw}' 검색 결과: {총}개 섹션` 유지 → 결과별 `### [{file}] {heading}` 유지 → 본문은 위 `match_pos` 기준 2,000자 창(기존 상한 유지, 시작점만 이동) + 창 뒤에 내용이 남으면 `... (이하 생략)` 유지 → 총 > limit 이면 마지막에 `… 외 {N}건 — 검색어를 좁히거나 +필수어 를 쓰세요` 1줄. 0건 문구 `'{kw}' 검색 결과 없음` 유지.
- 테스트 `test_confluence.py` 5건(`tempfile` docs 디렉터리, `search_docs` 직접 호출): 순위(헤딩 일치 섹션이 본문만 일치 섹션보다 먼저) · 상한(7섹션 일치 → 5 반환, 총 7) · 폴백-로드실패(`ranker=None` → substring 결과·WARN 1줄) · 폴백-토큰0(`"A"` → substring 결과, WARN 없음) (C4-1) · `match_pos`(본문 일치 없는 헤딩 일치 섹션 → 0, 있는 섹션 → 첫 경계 일치 인덱스) (C4-2).

### 5. 지시 문서·docs (soft 배선)

- `wrapper-protocol.md` §6 (`:32-39`, 8줄) → 아래로 교체 (≤ 10줄, 순증 ≤ +2):

  ```markdown
  ## 6. 본문 부분 로드 (권장 — 필수 step 아님)

  진입 파일 로드 후 특정 주제(feature 키워드·클래스명·소스 경로)의 상세가 필요하면 본문 파일 전체 Read·무차별 Grep 대신 섹션을 좁힌다:

  1. `python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<키워드>" --scope {domain}` → 상위 섹션의 `file · heading · 라인 범위 · read_hint` (`select:{path}#{헤딩}` 직접 지정 · `+필수어` 사전필터 · `--include features/ docs/` 부속 문서).
  2. 그중 1~2개를 `read_hint` 대로 `Read offset/limit` 부분 Read. 상태값(`enums` 등) 확인도 같은 절차.

  0건이면 도구가 `--scope`·`+필수어` 제거 등 상태 안내를 낸다 — 실패가 아니다. 도구 부재 시 진입 파일 목차 → 라인 범위 수동 2단계로 대체.
  ```

- `scope-exploration.md` 공통 원칙 (`:9-11`) — 2 를 P4 계약으로 확장 + 항목 2개 추가 (≤ +8):
  - 2. Explore 서브에이전트 호출 시 prompt 에 **(a) scope 경로 목록 (b) thoroughness `quick` / `medium` / `very thorough` (c) "결론만 반환 — 파일 덤프 금지"** 를 명시한다. scope 없이 전체 codebase 스캔 금지.
  - 2-bis. Explore 를 쓰지 않는 경우 — 경로를 알면 Read · 클래스/정의 1개는 Grep/Glob · 2~3 파일이면 직접 Read.
  - 4. `workspace/context/` 지식 파일 본문은 Grep 대신 `context-search.py` (wrapper-protocol §6) 로 섹션을 좁힌 뒤 라인 범위 Read.
- `pilot/docs/reference/index.md:25` — `auto_pilot`, `confluence`, `context-search`, `docs_build`, … (알파벳순 삽입).
- `python3 pilot/tools/docs_build.py` → `docs/reference/tools/context-search.md`·`tools/index.md` 재생성 → `--check` exit 0.
- 링크 규칙: `test_doc_links.py` 가 `skills/`·`agents/` 를 스캔한다 — 두 문서에서 `${CLAUDE_PLUGIN_ROOT}/tools/context-search.py` 는 **코드 스팬으로만** 쓰고 마크다운 링크로 만들지 않는다.

### 6. 게이트 실측 (순서 고정)

- **G1 단위**: `python3 -m unittest discover -s pilot/tests/tools` 전체 통과 (baseline 292 + 신규 ≥ 30) · `python3 pilot/tests/tools/test_context_search.py` 단독 통과.
- **G2 골든**: fixture `hit@3` **4/4** (`--scope pilot`) + **라이브 코퍼스** 동일 4질의(`--scope pilot --format json`) 결과(top-5 file·heading·level·score — level 1 서문의 순위 포함, C2) 를 이 plan 하단 `## 실측 기록` 에 기록(evaluator 증거 · DoD 측정 (ii)).
- **G3 결정성·성능**: 라이브 코퍼스 동일 질의 2회 `--format json` diff 0 · 1,000섹션 임시 코퍼스(**섹션당 인용 ≥ 5**, C5) `time python3 …` 실측 ≤ 300ms(초과 시 수치 기록 — 300ms 는 목표, 테스트 게이트는 1.0s). critic 프로토타입 참고치: 라이브 밀도 1,000섹션 ≈ 190ms(인터프리터 20ms + D8 import 11ms 포함) · 고밀도(인용 30/섹션) memo 없이 0.83s.
- **G4 soft 보증**: `git diff --numstat -- pilot/skills/context/shared/wrapper-protocol.md pilot/skills/context/domain/scope-exploration.md` 의 (added − deleted) 합 **≤ 30** · `git diff --stat -- pilot/agents/` **비어 있음** · `build_instructions` 반환 무변경.
- **G5 읽기 전용·traversal**: 도구 실행 전후 `git status --short workspace/context/` 변화 0 · `select:../x`·`--include /etc`·`--include ../../x` → exit 2 · **(C1 추가 3케이스)** `--scope /etc`(절대경로) · `--scope ../projects`(`../`) · `--project ../x` → exit 2 + stderr 문구 · **심볼릭 링크 탈출**: `workspace/context/` 안에 외부 폴더 링크를 임시로 만들어 실행 → 링크 안 `.md` 가 결과·`candidates` 에 없음 + INFO 1줄 (실측 후 링크 제거, `git status` 변화 0 재확인).
- **G6 docs**: `docs_build.py --check` exit 0 + `ls pilot/docs/reference/tools/` 에 `context-search.md` 실재 (**git 미추적 — 커밋 diff 증거 요구 금지, 상태 기반 증거**; 전달사항 :167 소비) · `test_doc_links` 통과.
- **G7 정합**: `doctor.py workspace` 11 PASS · 0 WARN · 0 ERROR 유지 · `.agent-state.yml` diff 0 · `python3 pilot/tools/confluence.py` 인자 없이 실행 시 docstring 출력(랭커 미로드 확인).

## 주의사항

- 지식 파일 **읽기 전용** — 도구·테스트·Generator 어느 경로도 `workspace/context/**` 를 쓰지 않는다 (drift-protocol § A). fixture 는 복사본.
- 표준 라이브러리만 — `re`·`pathlib`·`json`·`argparse` + `os`·`sys`·`dataclasses`·`importlib.util`(형제 모듈 로드). `difflib`·`yaml`·서드파티 금지(후보 유사도는 세그먼트 토큰 공유 수).
- **캐시 없음 = 실행 간 영속 캐시 없음** (파일·mtime 키 캐시 금지). 실행 내 memo(`extract_citations` 의 `path_tokens` dict) 는 허용 (C5). 전역 가변 상태 금지 — memo 는 `search()` 지역 객체로 만들어 넘긴다.
- 빈도 미반영·신호별 1회 — 긴 섹션이 반복 등장만으로 이기지 않게. 점수표 숫자는 spec 그대로(변경 금지).
- `pilot`·`skills`·`skill` 처럼 코퍼스 전반에 깔린 토큰은 모든 `## /pilot:x` 섹션에 같은 점수를 주는 상수 오프셋 — 순위 무영향(골든 계산에 반영). **불용어로 넣지 않는다**(코퍼스 종속).
- `--include features/` 는 `.plan.md`·`.plan.critic.md` 파생물도 색인 — 이번 범위에서 spec/파생 구분 없음(전달사항 :171 의 `is_feature_spec_file` 은 doctor 전용, 재사용 안 함). 결과가 파생물에 치우치면 후속 검토.
- `--include` 는 `nargs="+"` — 질의를 첫 인자로 두는 관례를 docstring·§6 문구에 명시.
- 삭제된 스크립트(`diagnose.py`·`memory-hint.py`·`init_detect.py`·`verify-report-lint.py`) 호출 금지.
- 계획 확정 후 generator/critic 자동 호출 금지 (guardrails § A16). Generator 는 `project.md` `## 목표` 체크박스를 건드리지 않는다(evaluator 단독 권한).
- 버전 bump 없음 — #30 마감 PR 에서 1회. 커밋 분리: 코드(`pilot/`) 와 workspace 산출물 별도 커밋, `main` 직접 커밋 금지.

## 에이전트 간 전달사항 소비 (2026-09-04)

| project.md 항목 | 판정 | 처리 |
| --- | --- | --- |
| :167 `docs/reference/*` git 미추적 → 상태 기반 증거 (from #20) | **관련** — 본 feature 가 tool 페이지 1개 신설 | G6 에 반영 → `[x]` 처리 |
| :172 orchestrate-load placeholder leak (from #23) | 파일은 겹치나 범위 밖 | **이월 확정** (2026-09-04 사용자 처분 — project.md 에 이월 표기) — 별건 feature |
| :168 #20 dogfooding 체크 조건 · :170 "소화됨" 고지 (from #21·#23) | 장부 불일치 — :170 이 :168 소화를 선언했으나 둘 다 `[ ]` | **`[x]` 정리 완료** (2026-09-04 사용자 처분) |
| :163 context/pilot 라인 인용 stale (from #19) · :171 features 명명 경계 (from #23) | #22 / doctor 소관 | 이월 |
| :112·:122·:124·:128·:131·:132·:135·:138·:141·:149·:150·:151·:153·:155·:158·:165·:169 | 무관 | 이월 — RESUME.md:78 "미처리 전달사항은 v0.4.0 이월로 사용자 승인됨" 기존 승인 범위 |

무관 항목의 체크박스는 planner 가 건드리지 않았다 — 2026-09-04 사용자 처분 완료(:168·:170 `[x]`, :172 이월 표기, 나머지 이월 유지).

## 드리프트 보고 (drift-protocol § A/B — 직접 Edit 안 함 · 2건 < 임계 3 → 개별 보고)

1. `workspace/context/pilot/lifecycle.md:79` — `--fix` 를 "v0.1.0→v0.2.0 마이그레이션 질의 (상세: `references/migration.md`)" 로 서술. 실제 `pilot/skills/doctor/SKILL.md:34` 는 "`.gitignore` secret 패턴 주입·STATE.md 이력 정리·schema 업그레이드" 이고 `pilot/skills/doctor/references/` 폴더 자체가 없다(#20 마이그레이션 삭제). #22 재학습 대상 **4번째 항목**으로 편입 — **완료** (2026-09-04 사용자 결정, `features/22-context-drift-relearn.md` 표 4행). 기존 3건(memory-hint·init_detect·diagnose.py)은 이미 등록, 재보고 아님.
2. `workspace/projects/build-plugin/RESUME.md:18·65-69` — "#27 update 도구 보류 / #28 스키마 중복" 행이 현행 features(#27 context-search·#28 freshness) 와 번호 충돌. 사람용 인수인계 노트라 자동 소비 대상은 아니지만 재개 시 혼동 유발 — **정정 완료** (2026-09-04 번호 회수: RESUME.md 행을 `(구 #27)`·`(구 #28)` 로 표기, 구 산출물은 브랜치 `skills/24-pilot-update-tool` 커밋 `8d3a868` 에 보존).

## 교차 의존

- **#28 freshness** — 같은 `build_load_plan` 4)·5) 직후에 힌트 추가 예정. 본 힌트는 4) `if entries:` 블록 끝이라 #28 가 그 뒤에 이어 붙이면 된다. 본 도구의 `citations` 정규식(`/` 필수·라인 선택)은 #28 의 인용 파서(F-D: `` `?(path):(\d+)(?:-(\d+))?`? ``, 라인 필수) 와 목적이 달라 **공유하지 않는다**. dogfooding 기록(검증 기준 3항 "후속 feature 1건에서 planner 가 도구 1회 이상 사용") 은 **#28 planner** 가 남긴다.
- **#29 frontmatter** — description 4점은 이미 배선(frontmatter 있으면 자동, 플래그 없음 — Open Q (d)-3). #29 은 `learn` 이 frontmatter 를 쓰면 끝. "`hit@3` 저하 없음" 게이트는 #29 이 fixture 로 재측정.
- **#30 경로 트리거** — 규칙 포인터의 "상세 조회" 1줄이 본 CLI 를 인용 → 인자 이름(`--scope`) 변경 금지.
- **#22 relearn** — 라이브 코퍼스가 바뀌어도 fixture 골든은 불변. 재학습 후 라이브 4질의 1회 재실행·기록 권고.
- **v0.11.0 마일스톤** — bump 는 #30 마감 PR.

## critic 합의 반영 (2026-09-04 재호출)

`@pilot-planner-critic` 실행 완료 — C1~C8 전건 **accepted** (합의 표: `27-context-search-tool.plan.critic.md` § 합의). 반영 위치:

| C# | 반영 절 |
| --- | --- |
| C1 blocking traversal | D8 · 스텝 1 「코퍼스」 인자 거부 + 수집 후 봉쇄 검증 · 스텝 2 traversal 케이스 · G5 3케이스 + 심링크 |
| C2 서문 decoy | D7(level 1 heading 신호 차단 + 정렬 H2→H3→L1) · 스텝 1 「섹션 분할」「점수」「순위」 · 골든 수치 정정(차순위 10 · 서문 57→≤37) |
| C3 한글 골든 | 스텝 2 골든 4번 `"도메인 진입 파일 자동 로드"` + `--scope pilot` 실행 + spec 예시 제외 사유 · G2 4/4 |
| C4 confluence 경계 | 스텝 1 `extract_citations` 공개 함수 · 스텝 4 폴백 조건 ②·`match_pos` 정의·테스트 5건 |
| C5 성능 병목 | 스텝 1 memo · 스텝 2 성능 코퍼스 인용 ≥5 · G3 · 주의사항 "캐시 없음" 정의 |
| C6 D8 빈틈 | 스텝 1 「순위」 `is_entry` scope 규칙 · 「코퍼스」 set+정렬 dedupe · 스텝 2 케이스 |
| C7 헤딩 수 | baseline 정정 (H2 26 · H3 2) |
| C8 질의 조사 | 스텝 1 「0건 안내」 guidance 1항 |

다음 단계 = `@pilot-generator` (사용자 명시 호출 — A16). Generator 는 이 plan 과 critic 합의 표를 함께 Read 한다.

## 실측 기록

_(Generator/Evaluator 가 채움 — G2 라이브 4질의 top-5(level 1 서문 순위 포함) · G3 결정성 diff · 1,000섹션(인용 ≥5/섹션) 시간 · G4 numstat · G5 심링크 실측)_

### G1 단위 (2026-09-04, generator, 구간 A 완료 시점)

`python3 -m unittest discover -s pilot/tests/tools` → **380 tests OK** (baseline 292 + 신규 88 — `test_context_search.py` 86 · `test_orchestrate_load.py` 힌트 테스트 2). `python3 pilot/tests/tools/test_context_search.py` 단독 → 86 OK.

### G2 골든 (2026-09-04, generator)

fixture `hit@3` (`pilot/tests/tools/test_context_search.py::GoldenHitAtThree`, `--scope pilot`) — **4/4 pass**.

라이브 코퍼스 동일 4질의(`--scope pilot --format json`) top-5:

1. `"doctor 정합성 검사"` — 22 `lifecycle.md` `` `/pilot:doctor` `` (L2) · 10 `lifecycle.md` `` `/pilot:project` `` (L2) · 8 `index.md` "스킬 17 개 — 역할별 cluster" (L2) · 8 `delivery.md` `` `/pilot:slack` `` (L2) · 6 `lifecycle.md` "pilot — Lifecycle skills"(서문, **L1**)
2. `"slack webhook 알림"` — 22 `delivery.md` `` `/pilot:slack` `` (L2) · 10 `delivery.md` `` `/pilot:pr` `` (L2) · 8 `index.md` "스킬 17 개 — 역할별 cluster" (L2) · 2 `index.md` "Cluster 진입" (L2) · 2 `index.md` "공통 사전 확인 (P-N) 매트릭스" (L2)
3. `"pilot/skills/learn/SKILL.md"` — 66 `spec.md` `` `/pilot:learn` `` (L2) · 46 `index.md` "스킬 17 개 — 역할별 cluster" (L2) · 44 `lifecycle.md` `` `/pilot:init` `` (L2) · 42 `delivery.md` `` `/pilot:commit` `` (L2) · 42 `delivery.md` `` `/pilot:pr` `` (L2) — critic C2 예측(66 vs 서문 decoy 57)대로 **서문(level 1) 이 top-5 밖으로 밀려남** — D7 heading 신호 차단이 실측으로 확인됨.
4. `"도메인 진입 파일 자동 로드"` — 14 `index.md` "Cluster 진입" (L2) · 8 `spec.md` `` `/pilot:learn` `` (L2) · 6 `index.md` "공통 사전 확인 (P-N) 매트릭스" (L2) · 6 `lifecycle.md` `` `/pilot:project` `` (L2) · 6 `lifecycle.md` `` `/pilot:issue` `` (L2) — critic 프로토타입 추정치(2·3위 ≤4)보다 실측이 다소 높게(6점) 나왔으나 1위와 마진이 충분해 hit@3 영향 없음.

4/4 전건 top-1 정답 일치 (fixture·라이브 모두).

### G3 결정성·성능 (2026-09-04, generator)

- 라이브 코퍼스 동일 질의(`"도메인 진입 파일 자동 로드" --scope pilot --format json`) 2회 실행 `diff` → **빈 결과** (결정적).
- 합성 코퍼스 200파일×5섹션=1,000섹션, 섹션당 인용 6개(≥5 조건 충족) → `search()` 1회 **70.8ms** (목표 300ms, 게이트 1.0s 대비 여유).

### G4 soft 보증 (2026-09-04, generator)

`git diff --numstat -- pilot/skills/context/shared/wrapper-protocol.md pilot/skills/context/domain/scope-exploration.md` → `scope-exploration.md` +3/-1 · `wrapper-protocol.md` +5/-5. **(added−deleted) 합 = 2** (≤30 충족). `git diff --stat -- pilot/agents/` → **빈 결과** (무변경). `build_instructions` 반환은 미변경(테스트 `BuildInstructions` 그대로 통과).

### G5 읽기 전용·traversal (2026-09-04, generator)

- 실제 `workspace/context/` 에 대해 도구 실행 전후 `git status --short workspace/context` → **변화 없음** (도구가 파일을 쓰지 않음 확인).
- `select:../x` · `--include /etc` · `--include ../../x` · `--scope /etc` · `--scope ../projects` · `--project ../x` 6케이스 전부 exit 2 + stderr 문구 (CLI `main()` 레벨 확인, `MainCliTest`/`CollectFilesTest` 로 고정).
- **심볼릭 링크 탈출 (실제 `workspace/context/` 에서 1회 실측)**: `workspace/context/evil-symlink` → 외부 임시 폴더(`evil-leak.md` 포함) 링크 생성 → `context-search.py "leaked evil" --workspace workspace` 실행 → `candidates=0`, `info=["코퍼스 밖 링크 1건 제외"]`, 결과에 `evil` 파일 부재 확인 → 링크 제거 후 `git status --short workspace/context` 재확인 → **빈 출력** (원복 완료).

### G6 docs (2026-09-04, generator)

`python3 pilot/tools/docs_build.py --check` → **exit 0**. `pilot/docs/reference/tools/context-search.md` 실재(3,192 bytes, docstring 그대로 추출) · `pilot/docs/reference/tools/index.md` 에 `context-search` 항목 실재. `test_doc_links.py` 16 tests 통과(코드 스팬만 사용 확인).

### G7 정합 (2026-09-04, generator)

`doctor.py workspace` → **11 PASS · 0 WARN · 0 ERROR** (baseline 그대로 유지). `.agent-state.yml` 무변경(diff 0). `python3 pilot/tools/confluence.py` 인자 없이 실행 → docstring 출력 + exit 1 (기존 진입 분기 무손상 확인).
