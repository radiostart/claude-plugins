# 경로 트리거 도메인 규칙 주입 — 플랜 v2 (#30 C1 + 최소 보완 훅)

- 작성: 2026-09-09 · 브랜치 `claude/dp-skills-context-search-enhance-qp02xo` · v1 `2026-09-08-path-triggered-rules-plan.md` 를 대체 (critic `…-plan.critic.md` 10건 반영 — 처리 내역은 critic 합의 표)
- 대상·SSOT·지시서 대비 판정은 v1 § 0~2 를 그대로 계승한다. 본 문서는 **바뀐 설계와 적용 절차**만 다시 쓴다.
- 상태: **v2 확정 · 적용 진행** (사용자 결정 2026-09-09: "v2 개정 후 적용 순서대로 진행")

## 0. v1 → v2 변경 요약

| critic | v1 | v2 |
|---|---|---|
| C1 (blocking) | "Write 의 틈은 `coding-rules.sh` 가 보완" | Read 만 발화한다는 실측을 인정. **최소 보완 훅 `domain-pointer.sh`**(PostToolUse `Edit\|Write`) 신설 — 생성된 규칙 파일의 `paths:` 만 대조해 같은 포인터를 **세션·도메인당 1회** 주입(본문 아님, ≤2 도메인). `coding-rules.sh` 는 무변경, 회귀 테스트 10건 |
| C2 (blocking) | 인용 디렉토리 빈도 → `dir/**` | doctor #28 인용 해석 체인(`_iter_cited_paths`·`_resolve_cited`·`_is_workspace_internal`)으로 **실파일만** 집계 → 하위 트리 합산 → 상위 디렉토리에서 시작해 **탐욕 분할**(가장 큰 glob 을 자식 ≥2파일 디렉토리로 쪼개되 8개·커버리지 90% 유지). `**`·`workspace/**`·`.claude/**`·`## Ignore`·`test_path_convention` 제외. 해석 파일 < 2 → 생성 skip |
| C3 | — | "규칙은 세션당 1회 로드 — 재생성분은 새 세션부터" 를 learn INFO·문서·doctor 힌트에 명시 |
| C4 | 검색 줄에 `${CLAUDE_PLUGIN_ROOT}` | `- 상세 조회: /pilot:ask (메인) · wrapper-protocol §6 3단계 (래퍼)` — 치환 불필요 |
| C5 | Phase 5 "MANIFEST 갱신 직전", "Phase 5 batch" | **MANIFEST 등록 후·doctor 직전** `rules-pointer.py --all --write`. 미등록 도메인은 exit 2(전 코퍼스 폴백 없음). Boundary 모드도 `--all --write`. batch 표현 삭제 |
| C6 | "서브에이전트 모두" | 실측 기록을 종류별로: 메인 ✓ · general-purpose 서브 ✓ · Explore/Plan 은 문서상 프로젝트 규칙 skip(미실측) · `claudeMdExcludes`·`--setting-sources` 미검증. doctor: `.claude/settings*.json` 의 `claudeMdExcludes` 가 `.claude/rules` 를 가리키면 INFO. ask·scope-exploration 에 "Explore 결과엔 포인터 없음" 1줄 |
| C7 | 도메인별 독립 도출 | `--all` 이 전 도메인을 한 번에 집계: 동일 glob 이 2도메인 이상이면 하위 트리 파일 수 최대 도메인에만 배정, 동률이면 제외 + INFO. doctor: 규칙 파일 간 동일 glob INFO |
| C8 | Phase 0 6건 · G4/G6 대화 기록 | Phase 0 10건(스켈레톤 `source_root` fail-open · `예:` 벗기기 · `session_id` 부재 · `CLAUDE_PLUGIN_ROOT` 미설정 추가). G4 는 프로브 절차·주입 블록 원문을 #30 실측 기록에 남기고, `InstructionsLoaded` 훅 로그는 후속 |
| C9 | `tools/rules-pointer.py` 가 판정 소유 | **판정·생성 로직 = `pilot/tools/doctor/rules_pointer.py`**, `pilot/tools/rules-pointer.py` 는 CLI 래퍼(`doctor.py` 와 같은 sys.path 방식). #30 조항 변경을 § 6 에 열거 |
| C10 | 캡 = 파일 줄 수 | 캡 = **주입되는 본문**(frontmatter·HTML 주석 제외) ≤ 500자 · ≤ 8줄. 마커는 주석 1줄. doctor 는 마커 없는 파일을 먼저 걸러 INFO 만 |

## 1. 실측 기록

v1 § 1 표 + critic 재현: Write 만·Edit 만·Bash 읽기 = 미발화, 같은 파일 Read = 발화, 같은 세션 재-Read 시 재주입 없음, frontmatter·HTML 주석은 벗겨져 주입, 슬래시 없는 `*.py` 는 중첩 경로에 발화(gitignore 의미). 서브에이전트는 general-purpose 1종만 확인(critic 세션에는 Agent 도구가 없어 재현 불가). 하네스 바이너리 2.1.263.

## 2. 설계 v2

### 2.1 산출물 `.claude/rules/pilot-{domain}.md` (저장소 루트 = `workspace/` 의 부모)

```markdown
---
paths:
  - app/services/wms/**
  - app/models/wms/**
---
<!-- managed by /pilot:learn — 수동 편집 금지. 재생성: python3 {plugin}/tools/rules-pointer.py --all --write · 점검: /pilot:doctor. 규칙은 세션당 1회 로드 — 재생성분은 새 세션부터 -->
<!-- paths: 인용 경로 추정 (sources frontmatter 없음) -->            ← 추정일 때만
이 경로는 `wms` 도메인이다. 수정 전 확인:
- 진입: workspace/context/wms/index.md
- 규칙: workspace/context/rules/wms.md
- 본문: workspace/context/wms/services.md
- 경계: workspace/context/boundaries/wms--schoice.md
- 그 외 2개 — index 참조
- 상세 조회: /pilot:ask (메인) · wrapper-protocol §6 3단계 (래퍼)
```

- **포인터 순서**: 진입 파일(MANIFEST, 모두) → `rules/{domain}.md`(존재 시) → 본문 ≤2(frontmatter `type` ∈ rules·services·enums, 없으면 파일명 stem 이 rules·services·enums) → `boundaries/{domain}--*.md`·`*--{domain}.md` ≤2 → 초과분 "그 외 N개 — index 참조" → 상세 조회 1줄(고정).
- **캡**: 본문 ≤ 500자·≤ 8줄 — 초과 시 경계 → 본문 순으로 줄여 "그 외 N개" 에 합산. `paths` ≤ 8.
- **도메인명**: `[A-Za-z0-9_-]+` 만(learn Phase 1 sanitize 와 동일). 그 외는 exit 2.

### 2.2 `paths` 도출 (`doctor/rules_pointer.py`, 결정적·읽기 전용)

1. 등록 도메인 = MANIFEST `## 도메인 분류` 표 행(첫 셀). 도메인 문서 집합 = 진입 파일 + `{domain}.md` + `{domain}/**/*.md` (경계 문서는 포인터에만 쓰고 glob 집계에서 제외 — A→B 호출 표면이라 B 소스를 가리킨다).
2. **sources 우선**: 문서 frontmatter `sources` 합집합(끝 `/` → `/**`, 정렬·중복 제거). 있으면 그대로(캡 8 초과 시 앞 8 + INFO).
3. **인용 추정**(sources 0건): 각 문서의 인용을 `_iter_cited_paths` → `_resolve_cited(repo, source_root)` 로 **실파일**로 해석, `_is_workspace_internal`·`.claude/`·`## Ignore` 행·`test_path_convention` 매칭 제외. 해석 파일 < 2 → skip + INFO.
4. 집계: 파일마다 조상 디렉토리 전부에 +1(하위 트리 합산). 초기 glob = 최상위 디렉토리(`dir/**`, 루트 직속 파일은 파일명 그대로). **탐욕 분할**: glob 수 < 8 인 동안 하위 트리가 가장 큰 glob 을 자식 디렉토리(각 ≥2파일)로 쪼개되, 쪼갠 뒤 glob 수 ≤ 8 이고 커버리지 ≥ 90% 일 때만 채택(동률은 이름순). 쪼갤 것이 없으면 종료. 2파일 미만 glob 은 제거(유일하면 유지). `**` 단독·`workspace/**`·`.claude/**` 는 절대 내지 않는다.
5. **도메인 간 배타**(`--all`): 동일 glob 이 2도메인 이상 → 그 하위 트리 파일 수가 가장 큰 도메인에만, 동률이면 전부 제거 + INFO "공유 경로 — index 참조".
6. glob 의미 = gitignore(하네스·`context-search._glob_regex` 동일).

### 2.3 코드 배치 (C9)

- `pilot/tools/doctor/rules_pointer.py` — `list_domains(workspace)` · `derive_paths(workspace, domains) -> dict` · `build_rules_file(workspace, domain, paths, info) -> str` · `write_rules_files(workspace, ...)`(마커 보존·동일 내용 무변경) · `check_rules_pointer(workspace) -> list[Result]` · `match_hook(workspace, file_path, session_id) -> str | None`. `context-search.py` 의 `parse_frontmatter`·`_glob_regex` 는 importlib 지연 로드(단일 의미 유지), 인용 체인은 `doctor.integrity` 직접 import.
- `pilot/tools/rules-pointer.py` — CLI: `--all | --domain D` × `--write | --check | (미리보기)` · `--hook`(stdin JSON) · `--workspace`. exit: 0 · 1(`--check` 불일치) · 2(인자·미등록 도메인).
- `pilot/hooks/domain-pointer.sh` — `exec python3 "$CLAUDE_PLUGIN_ROOT/tools/rules-pointer.py" --hook --workspace "$CLAUDE_PROJECT_DIR/workspace"`. `hooks.json` PostToolUse `Edit|Write` 에 추가(`coding-rules.sh` 뒤, timeout 5).
- `--hook` 규칙: 프로젝트 밖·`workspace/`·`.claude/` 파일 skip · 규칙 파일 `paths:` 매칭(gitignore) · 세션·도메인 마커 `{TMPDIR}/pilot-domain-pointer.{session}.{domain}` · 최대 2 도메인 + "그 외 N 도메인" · 출력 = 규칙 본문(주입되는 부분과 동일) · 규칙 디렉토리 부재·`session_id` 부재 시 무음(누적 방지 — coding-rules 와 다름).
- learn SKILL.md Phase 5: 3(외부 reference) 다음에 **4. 규칙 포인터 재생성** `python3 ${CLAUDE_PLUGIN_ROOT}/tools/rules-pointer.py --all --write` → INFO 보고("새 세션부터 반영" 포함) → 5. doctor → 6. 결과 출력. Boundary 모드 절차 3 에도 같은 명령.
- doctor `check_workspace` 끝에 `check_rules_pointer` 추가. 판정: 마커 없는 파일 → INFO 만; 관리 파일 → (a) 미등록 도메인 WARN (b) 포인터 경로 부재 WARN (c) 재생성 결과와 불일치 INFO (e) `claudeMdExcludes` INFO (f) 규칙 파일 간 동일 glob INFO.

## 3. 적용 순서

- **Phase 0**: `test_coding_rules.py`(10건) · #30 § 실측 기록 기입 + 조항 변경(§ 6).
- **Phase 1**: `doctor/rules_pointer.py` + `tools/rules-pointer.py` + `test_rules_pointer.py`(도출·캡·템플릿·write/check/hook·결정성·배타).
- **Phase 2**: `domain-pointer.sh` + `hooks.json` · learn Phase 5·Boundary · heuristics 절 · doctor 배선 + `test_doctor_rules_pointer.py` · ask·scope-exploration 1줄 · workspace-layout · release-notes.
- **Phase 3**: 라이브 `--all --write` → 생성 파일로 발화 재확인(메인·서브) → doctor → 기록. 생성 파일은 커밋(v1 § 3.9-1 제안 채택 — 되돌리기 쉬움).

## 4. 게이트

| G | 기준 |
|---|---|
| G1 | 전체 unittest 통과, 신규 ≥ 30건 |
| G2 | 라이브 `--all` 2회 생성 diff 0 · `workspace/context` 무수정 |
| G3 | 생성 < 200ms · `--hook` < 100ms(라이브) |
| G4 | 생성 파일로 메인·서브 발화 재확인, 주입 본문 ≤ 500자, #30 에 원문 기록 |
| G5 | `docs_build.py --check` · doctor(기존 `STATE.md` 부재 ERROR 제외) |
| G6 | 후속 사이클 generator 기록(후속) |

## 5. 제외

v1 § 3.8 유지. 추가: `InstructionsLoaded` 훅 로그 계측(후속), Explore/Plan·`--bare`·`--setting-sources` 실측(환경 부재).

## 6. #30 조항 변경 (C9)

- 예외 "최대 2 도메인 + 그 외 N" → C1 에서는 하네스가 모두 로드(파일당 캡이 총량 상한), **훅 보완에만** 2 도메인 상한 유지.
- 예외 "gitignore 되면 로드 안 함 → doctor WARN" → 실측상 무관, 삭제.
- doctor 검사 3종 → 6종(§ 2.3). `paths`↔`sources` 불일치 INFO 는 (c) 재생성 불일치에 흡수.
- 검증 기준 "`paths` 3줄 이내" → ≤ 8 globs.
- C2 훅 → 폐기가 아니라 **보완 훅**으로 축소(포인터 1회, 본문 없음).
- Open Q (c) → 해소: general-purpose 서브에이전트 발화 실측. Explore/Plan 은 문서상 skip.
