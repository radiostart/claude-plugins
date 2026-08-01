# #26 issue 단건 사이클 + 폴더 slug 자동 명명 (dp-skills 0.25.0/0.30.0 포팅)

> mode: standard (`tdd: false` · `mode: null`)
> source: `features/26-issue-cycle-slug.md` (요구사항·이식 제외·게이트 SSOT)
> 포팅 원본: `/Users/jay-p/Projects/deali-skills-plugin` HEAD `7dc24fb` (0.30.2) — 범위 특정 `cf54939`(0.25.0)·`c1febc6`(0.30.0), **HEAD 파일 상태 기준 + 이식 제외 7항 적용**
> planner_at: 2026-07-31 · critic 합의 반영: 2026-08-01 (C1~C5 전건 accepted — `.plan.critic.md` § 합의)
> focus 반영 사항: focus 없음 (orchestrate-load 반환 `focus: null`)

## 구현 계획: #26 issue 단건 사이클 + 폴더 slug 자동 명명

### 결정 (확정 — planner 위임분)

- **D1 — commit 의 issue 모드 거동: P1 판정 "예외 목록" 방식.** commit SKILL 본문(`pilot/skills/commit/SKILL.md:10-22` 전문 실독)은 `{PROJECT}` 를 **실사용하지 않는다** — P1 은 전제 게이트로만 쓰인다. 적용표(commit P1 ✅)는 불변, preamble P1 issue 판정에 예외(`focus`·`commit`) 명시 + commit SKILL 사전 확인에 예외 1줄. 적용표 조정(P1 제거)은 commit 의 "활성 없음 시 종료" 거동까지 바꿔 배제 (스코프 초과).
- **D2 — evaluator test_run 의 test_command 미설정 케이스.** dp 는 `verify-report-lint.py` 가 `phase: issue` 의 `test_run: pass|fail` 을 기계 강제했으나 pilot 은 #20 에서 삭제 — **모델 계약으로 대체** (skip 금지, `config.test_command` 미설정이어도 plan 스텝의 실행 방법으로 직접 실행). 구현 소재: 스텝 5 planner ⑦·evaluator ②·step 7 자기 점검 (spec (2) 명시 요구).
- **D3 — REPORT 모드 표기.** pilot REPORT 에 dp 의 `phase:` 필드 없음 (qa 미보유) — 기존 `mode:` 에 `issue` 기록, enum 주석 `{red_contract | characterize | standard | issue}` 확장 (기존 계약 삭제 없음). `feature:` → `{이슈명}`.
- **D4 — evaluator 이슈 블록에 "회귀영향 평가" 계약 포함.** spec (2) evaluator 항목이 명시 열거하지 않았지만, ① spec planner 항목의 "영향 범위 후보 필수 — evaluator 가 반려 게이트로 사용" 이 판정자를 전제하고 ② 이식 원칙이 "HEAD 파일 상태 기준" 이며 dp HEAD evaluator 이슈 블록에 존재한다. dp 가 qa 블록 참조로 승계한 3분류·반려 기준을 **전문 인라인** (자기완결 원칙 — 내용은 스텝 5 evaluator ①).
- **D5 — critic 후보 탐색 glob 은 dp HEAD 원문 유지.** `ls -t workspace/issues/{이슈명}/issue.plan*.md` 는 critic 파일도 매칭하지만 dp HEAD 동일 거동으로 이식 (식별·제외는 모델 판단 — 임의 개선 금지).
- **D6 — doctor `--fix` 는 무변경 + 회귀 테스트만 추가.** `_fix_state_md_prune_history` 는 상태 열만 보고 행을 보존 (실독 확인) — 코드 수정 없이 보존 테스트 1건으로 고정 (spec (7) "확인" 이행).

### 사전 실측 (baseline)

| 항목 | 값 | 근거 |
| --- | --- | --- |
| `parse_state_md_all_rows` | `pilot/tools/doctor/_common.py:116` 실재 — spec 인용 정확 | 실독 |
| `parse_state_md` (mode-blind) 소비처 | 정확히 2곳: `integrity.py:343`(check_workspace — 표시 전용, 무변경) · `integrity.py:979`(determine_active_project — 전환 대상) | grep 전수 |
| orchestrate-load 의 `_common` import | `parse_state_yml`·`_parse_semver` 기존 재사용 중 (`orchestrate-load.py:55`) — `parse_state_md_all_rows` 추가만 필요 | 실독 |
| plan-validate | 제목 헤딩(any heading) + standard 필수 H3 **없음** → 경로 임의 — **도구 무변경**으로 issue plan 검증 가능 | `plan-validate.py:63-110` 실독 |
| pilot 훅 도구 분기 | Write·Bash 만 처리 (Edit 미처리) → dp 의 Edit 분기 불요 — Edit 통과는 구조적 보장 (주석으로만 명시) | `protect-managed.sh:80-191` 실독 |
| pilot-planner 에 dp "모드 가드" | **없음** → dp planner 이슈 블록의 "[모드 가드] 재질의 해제" 문구는 이식 대상 아님 (해제할 대상 부재) | 실독 |
| 버전 표기 지점 | 3곳: `pilot/.claude-plugin/plugin.json:3` · `pilot/mkdocs.yml:122` (`extra.version`) · `pilot/docs/index.md:11` (`v0.11.0 highlights`) | grep `0\.11\.0` |
| docs 의 issue 서술 | tutorial/·explanation/·how-to/ 에 issue **모드 서술 0건** (무관 예시 slug 1건 — `how-to/create-feature.md:22` — 제외, C4) → 신설 외 stale 화 위험 없음. `docs/index.md` 는 highlights 갱신으로 충당 | grep 재확인 |
| 사내 식별자 sweep 기존 | 2건 — `auto_pilot.py:82`·`pilot-evaluator.md:54` 의 "구 verify-report-lint 이관" 자기 서술 (evaluator 의 "자기 서술 제외" 대상) | 게이트 grep 실행 |
| 테스트 baseline | `/opt/homebrew/bin/python3.12 -m unittest discover -s pilot/tests/tools` → **OK (309)** (C1 정정 — 근거 상세는 critic § 합의). 기본 `python3`(3.14) 은 PyYAML 부재로 `test_docs_build` 수집 탈락 (환경 이슈 — 본 작업 무관) | 재실측 2026-08-01 |
| docs_build baseline | `python3.12 pilot/tools/docs_build.py --check` → **exit 1 (fresh worktree 정상)** — 미추적 reference 34페이지 부재 (전달사항 ②). exit 0 은 스텝 10 생성 실행 **후** 성립 — 게이트 5 (C1 정정) | 재실측 2026-08-01 |
| dp 0.30.0 파서 영향 | "파서·orchestrate-load·doctor 계약 무변경 — slug 는 SKILL 규약" (커밋 메시지 명시) → slug 는 스크립트 검증 없음, SKILL·GUIDE 문서 계약 | `git show c1febc6` |

### 변경 파일

- [x] `pilot/tools/orchestrate-load.py` — work_mode 계약 (스텝 1)
- [x] `pilot/tests/tools/test_orchestrate_load.py` — ParseStateMdActive 개편 + MainIssueMode 신설 + DetermineDomain 한글 라벨 (스텝 2)
- [x] `pilot/tools/doctor/integrity.py` — 활성 판정 mode 인식 + 스킵 안내 + hint 문구 1줄 정정 (스텝 3)
- [x] `pilot/tests/tools/test_doctor_issue_mode.py` — 신규 (스텝 3)
- [x] `pilot/hooks/protect-managed.sh` — issues/ 보호 확장 (스텝 4)
- [x] `pilot/tests/tools/test_protect_managed.py` — ProtectManagedIssues 신설 (스텝 4)
- [x] `pilot/agents/pilot-planner.md` — work_mode 확인 + 이슈 수정 모드 H2 + step 6 저장 경로 1줄 (스텝 5)
- [x] `pilot/agents/pilot-planner-critic.md` — work_mode 확인 + 절차 2·3·5 issue 분기 (스텝 5)
- [x] `pilot/agents/pilot-generator.md` — work_mode 확인 + 이슈 수정 모드 블록 (스텝 5)
- [x] `pilot/agents/pilot-evaluator.md` — work_mode 확인 + 이슈 수정 모드 블록 + REPORT enum·자기 점검 확장 (스텝 5)
- [x] `pilot/skills/context/shared/wrapper-protocol.md` — § 4 에 work_mode 1줄 (스텝 6)
- [x] `pilot/skills/context/shared/preamble.md` — P1 issue 판정 + P2 slug·이력 원칙 정정 + P3 issue 분기 (스텝 6)
- [x] `pilot/skills/context/shared/messages.md` — `issue_active_not_project` 신설 (스텝 6)
- [x] `pilot/skills/commit/SKILL.md` — P1 issue 판정 예외 1줄 (스텝 6)
- [x] `pilot/skills/focus/SKILL.md` — issue 분기 (사전 확인 예외·bare 안내·경로 계약) (스텝 7)
- [x] `pilot/skills/issue/SKILL.md` — 사이클 지원 재정의 + slug 절차 (스텝 8)
- [x] `pilot/skills/context/lifecycle/issues/GUIDE.md` — 재정의 + § 폴더명 (slug) 규약 (스텝 8)
- [x] `pilot/docs/how-to/issue-cycle.md` — 신설 (스텝 9)
- [x] `pilot/docs/how-to/index.md` — 운영 grid card 1건 추가 (스텝 9)
- [x] `pilot/mkdocs.yml` — nav 행 + `extra.version` 0.13.0 (스텝 9·10)
- [x] `pilot/docs/index.md` — v0.13.0 highlights (issue 사이클·slug 반영) (스텝 10)
- [x] `pilot/.claude-plugin/plugin.json` — 0.11.0 → 0.13.0 (스텝 10)

### 구현 순서

1. **`pilot/tools/orchestrate-load.py` — STATE.md mode 열 인식 (work_mode 계약)** — 이후 모든 문서 계약이 이 반환 JSON 을 전제하므로 최선행.
   - import 에 `parse_state_md_all_rows` 추가 (`from doctor._common import ...` 기존 라인 확장).
   - `parse_state_md_active` 재작성: `(mode, 이름)` 튜플 목록 반환, 본문은 `parse_state_md_all_rows(state_md)` 필터 (`status == "진행중"`) — **인라인 파서 제거**. docstring 에 "mode 열 값 `project`|`issue`. legacy 표(첫 칸 순번 숫자)는 소비부가 `issue` 외 값을 project 로 폴백해 하위호환. 행 파싱 SSOT 는 doctor/_common.parse_state_md_all_rows" 명시 (dp :212-223 대응).
   - `result` dict 에 `"work_mode": "project"` 키 신설 (`"project"` 키 직후).
   - main P1 재작성 (dp :837-878 대응, TEAM 제거): `--project` 명시 시 활성 조회 자체를 건너뛰어 project 모드 강제 (work_mode 초기값 유지) · 단일 활성 행 unpack `(active_mode, project)`, `active_mode == "issue"` 면 `work_mode = "issue"` (그 외 값은 project 폴백) · 0건 에러를 "활성 project/issue 없음. `/pilot:project {이름}` 또는 `/pilot:issue {이슈명}` 으로 활성화." 로 갱신 · 2건 이상 에러의 이름 나열을 `", ".join(name for _, name in active)` 로 수정.
   - bare 검사 (traversal 검사 **앞**): `work_mode == "issue" and project == "-"` → 에러 "이슈명 없는 issue 모드 (STATE.md `| issue | - |`) 는 사이클 비지원. `/pilot:issue {이슈명}` 으로 이슈를 생성한 뒤 재시도." + exit 1. slug 는 기존 `has_path_traversal(project)` 검사를 그대로 통과시킨다 (재사용 — 신규 검증 없음).
   - issue 분기 (dp :880-902 대응): `workspace/issues/{project}/issue.md` 부재 → 에러 "workspace/issues/{project}/issue.md 없음 — `/pilot:issue {project}` 로 이슈 폴더를 생성한 뒤 재시도." (**`.agent-state.yml`·`projects/` 문자열이 에러에 포함되면 회귀**). 존재 시 `analyzed=False`·`tdd=False` 고정, `mode` 는 초기값 `None` 유지 (`.agent-state.yml` 안 읽음 — state 파싱·schema 검사·plugin_version 비교·mode 파싱은 전부 else(project) 분기로 이동), hint `"[work_mode] issue — 이슈 수정 모드: 최소 변경·롤백 가능. issue.md 가 단건 명세 (planner=원인, generator=조치 기입)"` 추가, `result["domain"] = determine_domain(issue_md)`.
   - `determine_domain`: 정규식을 `r"^\s*-?\s*\*?\*?(?:domain|도메인)\*?\*?\s*:\s*(\S+)"` 로 확장 + docstring "project.md 제한사항 또는 issue.md 상단에서 추출" (dp :395-412 대응). domain traversal 은 pilot 현행 `has_path_traversal` + WARN 힌트 + 무시 유지 (**dp `has_domain_traversal` 미이식** — spec 예외 케이스).
   - `.focus.md`: `focus_base = "issues" if work_mode == "issue" else "projects"` → `workspace / focus_base / project / ".focus.md"`.
   - `build_load_plan(..., work_mode: str = "project")` kwarg 신설 + main 호출부 전달:
     - step 2 재구성: issue 면 `spec_md_abs = workspace/"issues"/project/"issue.md"` 를 `workspace/issues/{project}/issue.md` 로 add (부재 힌트 없음 — main 이 선검증). project 면 기존 project.md 로직 그대로 (`spec_md_abs` 변수로 통일).
     - step 3 (prompts): `if work_mode != "issue":` 로 감싼다 — issue 는 **전체 skip, 부재 힌트도 미출력** (이슈엔 프로젝트별 prompts/ 트윈이 없다).
     - step 8: `config.update(parse_lang_override(spec_md_abs))` — step 2 의 spec_md_abs 재사용 (project_md_abs 재계산 제거). issue.md 는 통상 `## 제한사항` 이 없어 빈 dict (graceful — parse_lang_override 기존 거동).
     - step 0(SSOT)·1(MANIFEST/config)·4(도메인 진입 파일)·5(boundaries)·6(conventions)·7(모드 분기) **무변경** — MANIFEST 도메인 진입 파일·boundaries 로드는 양 모드 동일 (pilot 방식 유지).
   - `build_instructions` 5번째 지시문을 "analyzed / tdd / mode / domain / work_mode 값을 이후 분기에 사용" 으로 갱신 (지시문 5개 유지).
   - 모듈 docstring: 출력 JSON 스키마에 `"work_mode": "project" | "issue"` + issue 모드 계약 주석 (stateless: analyzed=false·tdd=false·mode=null 고정, domain 은 issue.md `도메인:`/`domain:` 라인, project.md·prompts/ 미로드. 계약 상세: `docs/how-to/issue-cycle.md`). `--project` argparse help 를 "프로젝트명 (생략 시 STATE.md 진행중. 명시 시 STATE 우회 project 모드 강제)" 로 갱신.
   - **금지**: `parse_lang_tools`·`parse_lang_override`·`LANG_KEYS` 수정 금지 (전달사항 :174 별건). dp 의 `project_phase`/`resolve_project_phase`·`list_supplementary_docs`·`read_known_domains`·persona 주입·`boundary_token` 은 흔적도 이식 금지 (주의사항 § 이식 제외 매핑).

2. **`pilot/tests/tools/test_orchestrate_load.py` 확장** — 스텝 1 과 동일 커밋로 고정 (dp +132줄 대응, TEAM 제거 적응).
   - `ParseStateMdActive` 개편 (기존 2건 갱신): `test_extracts_active_mode_name_pairs` (`| project | ProjA | 진행중 |`·`| issue | hotfix-1 | 진행중 |` → 튜플 목록) · `test_legacy_numeric_mode_column_passthrough` (`| 1 | ProjA | 진행중 |` → `("1", "ProjA")` — 소비부 project 폴백 전제) · `test_no_state_md_returns_empty` 유지.
   - `MainIssueMode` 신설 — scaffold: `workspace/STATE.md` (`| 모드 | 이름 | 상태 |` 헤더 + `| issue | hotfix-1 | 진행중 |`), `workspace/issues/hotfix-1/issue.md` (`# 제목\n\n도메인: orders\n\n## 현상\n...`), `workspace/context/MANIFEST.md` (`## 도메인 분류` 표에 `| orders | orders.md | ... |`), `workspace/context/orders.md`:
     - `test_issue_mode_contract_fields_and_files` — `work_mode=="issue"`·`project=="hotfix-1"`·`analyzed is False`·`tdd is False`·`mode is None`·`domain=="orders"`·files 에 `workspace/issues/hotfix-1/issue.md` + `workspace/context/orders.md` 포함·`project.md`/`prompts/` 문자열이 files·hints 에 없음·`[work_mode] issue` 힌트 존재. (dp 의 `project_phase`·supplementary 단언은 미이식 필드라 제외)
     - `test_issue_mode_all_phases_exit_zero` — 4 phase 루프 실행, 전부 exit 0 + `work_mode=="issue"` (spec smoke 게이트의 자동화).
     - `test_issue_focus_read_from_issues_dir` — `issues/hotfix-1/.focus.md` 본문이 `focus` 로 반환.
     - `test_missing_issue_md_reports_issue_context_error` — `| issue | ghost |` → exit 1, 에러에 `issues/ghost/issue.md 없음` 포함 + **`.agent-state` 와 `projects/` 미포함** (오도성 처방 부재 검증).
     - `test_bare_issue_row_unsupported` — `| issue | - |` → exit 1 + "사이클 비지원".
     - `test_explicit_project_flag_forces_project_mode` — issue 활성 상태에서 `--project P` → project 모드 진입 (에러에 `.agent-state.yml` 포함 = project 분기 진입 증거).
   - `DetermineDomain` 에 `test_korean_domain_label` 추가 (`도메인: orders` 라인 파싱).
   - `BuildInstructions` 는 무변경으로 통과 확인 (지시문 5개·ins[0..2] 단언 유지됨).

3. **`pilot/tools/doctor/integrity.py` + `pilot/tests/tools/test_doctor_issue_mode.py` (신규)** — 활성 판정 오진 제거 (dp `integrity.py:1964-2060` 대응, team 인자 제거).
   - `_active_rows(workspace: Path) -> list[tuple[str, str]]` 헬퍼 신설 (`parse_state_md_all_rows` 필터).
   - `determine_active_project(workspace)` 재작성: 단일 활성 행의 mode 가 `issue` 면 None (docstring: 이슈명을 프로젝트로 오인해 `/pilot:project {이슈명}` 처방이 나가는 오진 차단 — 따르면 이슈명으로 프로젝트가 생성되고 STATE 가 뒤집힘. legacy 첫 칸 순번 숫자는 project 폴백). `parse_state_md` import 는 :343 표시용 소비가 남으므로 유지.
   - `determine_active_issue(workspace)` 신설 (단일 활성 행이 issue 일 때 이슈명 — 스킵 안내용).
   - `run_integrity_check`: `if not project:` 분기에서 `determine_active_issue` 조회 → 있으면 `활성 issue ({이슈명}) — 프로젝트 체크 건너뜀 (이슈는 issues/ 폴더 기반. 프로젝트 검사는 --project 로 지정)` 안내 (기존 "활성 프로젝트 없음" 안내는 else 로).
   - `integrity.py:377` 부근 STATE 이력 WARN hint 의 "이력은 git log 로 추적" → "이력 SSOT 는 projects/·issues/ 로컬 폴더" 로 1줄 정정 (근거: 주의사항 § doctor hint 1줄 정정).
   - `_fix_state_md_prune_history` **무변경** (D6).
   - 테스트 신규 `test_doctor_issue_mode.py` (dp 110줄 대응 — team scaffolding 제거, 기존 `test_doctor_*.py` 의 importlib 패턴 답습): `DetermineActiveProjectModeAware` (issue 행 → None / project 행 → 이름 / legacy 숫자 → 이름 폴백) · `DetermineActiveIssue` (issue 행 → 이름 / project 행 → None) · `IntegrityCheckSkipsProjectOnActiveIssue` (issue 활성 workspace 에서 run_integrity_check stdout 캡처 — "활성 issue" 안내 존재 + 프로젝트 부재 ERROR 없음) · `PruneHistoryKeepsIssueRow` (issue 진행중 + 이력 행 STATE 에 fixer 실행 → issue 행 보존·이력만 제거 — spec (7) `--fix` 확인 요구).

4. **`pilot/hooks/protect-managed.sh` + `pilot/tests/tools/test_protect_managed.py`** — issues/ 보호 확장 (dp 훅 :98-126 대응, `{TEAM}` 세그먼트 제거).
   - 헤더 주석에 issues/ 규칙 단락 추가 (issue.md 의 사용자 작성 현상·누적 기록 보호 취지 + Edit·신규·`.focus.*` 통과).
   - projects/ 상위 차단 블록 **직후**에 대칭 블록 2개:
     - `^(workspace/issues)/?$` — 상위 폴더 destructive 차단 (에러: "issues/ 상위 폴더 삭제·이동 금지 — 모든 이슈의 누적 기록이 소실됩니다." + PILOT_PROTECT_BYPASS 안내).
     - `^(workspace/issues/[^/]+)(/|$)` — 기존 파일·폴더면 차단 (에러: "기존 이슈 파일·폴더 덮어쓰기·삭제·이동 금지 (issue.md 의 사용자 작성 현상·기록 손실 위험). 대안: 부분 갱신 (원인·조치·재발 방지 기입) → Edit 도구 / 의도적 reset → PILOT_PROTECT_BYPASS=1"), `! -e` 신규 생성은 통과. **Edit 분기 코드는 넣지 않는다** — pilot 훅은 Write·Bash 만 처리하므로 Edit 통과가 구조적 보장 (블록 주석에 이 사실 1줄). `.focus.md`·`.focus.history/` 는 기존 공통 예외(:39-40)가 경로 무관으로 선처리 — 무변경.
   - 테스트 `ProtectManagedIssues` 클래스 신설 (dp +50줄 대응): `test_write_existing_issue_md_blocked` (exit 2 + "이슈") · `test_write_new_derived_artifact_passes` (`issues/{slug}/issue.plan.md` 신규 Write → 0) · `test_edit_existing_issue_md_passes` (tool_name=Edit → 0) · `test_rm_issue_dir_blocked` (기존 이슈 폴더 rm -rf → 2) · `test_issues_parent_rm_blocked` (`rm -rf workspace/issues` → 2 + "상위") · `test_focus_in_issues_passes` (`issues/{slug}/.focus.md` Write → 0).

5. **wrapper 4종 이슈 블록** — 전부 **자기완결 인라인** (dp 원문의 "qa 결함 수정 모드와 원형 동일"·"qa 블록과 동일"·"qa/SKILL.md 명명 규약"·"verify-report-lint"·"instincts" 참조는 계약 전문으로 대체. 완성본에 `qa`·`phase == qa` 참조가 남으면 안 된다). 4종 공통으로 step 1 직후에 다음 단락 삽입: "**[필수] work_mode 확인** — step 1 JSON 의 `work_mode` 가 `issue` 면 {블록 지시} (issue 는 standard 고정 — stateless 라 tdd/characterize 와 동시 활성 없음). `project`(또는 필드 부재 — 구버전 출력)면 평소대로 진행."
   - **`pilot/agents/pilot-planner.md`**:
     - step 6(계획 저장)에 1줄: "work_mode=issue 면 이슈 수정 모드 블록의 'plan 저장 경로 (issue)' 가 우선한다 (features/ 부재와 무관하게 저장)."
     - 본문 말미(`## 플래닝 프로세스` 앞)에 `## 이슈 수정 모드 (work_mode == issue)` H2 신설, 항목:
       - ① 목적 1문장 — 활성 issue `workspace/issues/{이슈명}/` 의 운영 결함 1건 해결 (최소 변경·회귀영향 중심) ② **명세는 issue.md** — `## 현상`·`## 의심 영역` 이 요구사항, features/·project.md·prompts/ 는 존재하지 않음 ③ **최소 변경·롤백 가능** — 결함 지점만 좁게, 인접 개선·리팩터·신규 추상화 제안 금지 (issues/GUIDE.md 원칙) ④ **`## 원인` Edit 기입**.
       - ⑤ **영향 범위 후보 필수** — plan 본문에 절 신설, 동일 호출 경로 공유 후보 나열 (grep/scan 인용), 0건이면 검색 범위·키워드 기록 — evaluator 가 반려 게이트로 사용 ⑥ **결함 지점 1줄 필수** — `결함 함수: {file_path}#{symbol}` (데이터 정합 이슈면 `조치 대상: {테이블·데이터 범위}`) — generator 변경 범위 게이트 ⑦ **회귀 재현 테스트 스텝 필수** — 실행 명령 포함 (D2; 테스트 코드 작성은 Generator 몫 — step 4 공통 원칙 불변).
       - ⑧ **plan 저장 경로 (issue)** — `issues/{이슈명}/issue.plan.md`, 재작업·대형 개정은 `issue.plan.r{N}.md` (규약 SSOT: issues/GUIDE.md § 이슈 폴더 구조) + plan-validate 동일 경로 `--mode standard` ⑨ **비적용·치환** — 절차 2(전달사항 — project.md 없음) 건너뜀 · 절차 7 Slack 메시지 `계획 확인 필요: {이슈명}` 치환 (notifier 자동 no-op, 호출 유지) · 절차 9 재호출 분기의 critic 파일은 `issues/{이슈명}/issue.plan.critic[.r{N}].md`.
   - **`pilot/agents/pilot-planner-critic.md`** (dp 대칭 — 별도 H2 없이 절차 분기): work_mode 확인 단락 ("issue 면 대상은 활성 issue — 후보 탐색·입력·출력이 `issues/{이슈명}/` 기준. 챌린지 기준·산출 형식은 동일") + 절차 2 bash 블록에 `# work_mode=issue 면 활성 issue 의 plan 후보:\nls -t workspace/issues/{이슈명}/issue.plan*.md 2>/dev/null | head -3` 추가 (D5 — dp 원문 그대로) + 절차 3 에 "work_mode=issue 면 features/ 대신 `issues/{이슈명}/issue.md` (현상·의심 영역) + `issues/{이슈명}/issue.plan[.r{N}].md` 가 입력" + 절차 5 에 "work_mode=issue 면 출력은 `issues/{이슈명}/issue.plan.critic[.r{N}].md` (r 은 대상 plan 과 동일)".
   - **`pilot/agents/pilot-generator.md`**: work_mode 확인 + 이슈 블록 (step 1 아래 인라인) — ① **변경 범위 게이트**: plan 의 `결함 함수: {file_path}#{symbol}` (또는 `조치 대상: ...`) 안에서만 수정, 범위 밖 변경 필요 발견 시 구현 중단 + 보고 (`@pilot-planner` 재확인 안내) 후 종료 ② **plan 로드 경로**: step 2 의 features/ 경로 대신 `issues/{이슈명}/issue.plan[.r{N}].md` (r 최대값), plan-validate 도 동일 경로 + `--mode standard` ③ **issue.md `## 조치` Edit 기입**: 변경 파일 목록 + 핵심 diff 요약 (데이터 조치면 실행 쿼리·대상 범위) ④ **회귀 재현 테스트**: plan 스텝대로 작성 (evaluator 가 직접 실행해 test_run 에 기록).
   - **`pilot/agents/pilot-evaluator.md`**: work_mode 확인 + 이슈 블록:
     - ① **회귀영향 평가 필수** (D4): plan "영향 범위 후보" 각 항목을 3분류로 판정 + 사유 1줄 — (a) 영향 있음+회귀 우려 → 추가 검증 필요, issues_to_fix escalate / (b) 영향 있음+회귀 우려 없음 (근거 명시) / (c) 영향 없음 (근거 명시). 반려 기준: 절 부재, 또는 0건인데 검색 범위·키워드 기록 없음 → `NOT_READY` + issues_to_fix 에 "planner 재호출 필요 — 영향 범위 후보 누락" (직접 planner 호출 금지 — 오케스트레이션이 라우팅). 평가 결과는 issue.eval 에 "회귀영향 평가" 섹션으로 기록.
     - ② **회귀 재현 테스트 직접 실행 (mode 무관)**: plan 스텝 테스트를 `{test_command}` 로 직접 실행, REPORT `test_run: pass|fail` — **skip 금지** (step 2 표준 모드의 "미설정 시 skip" 을 오버라이드. `config.test_command` 미설정이어도 plan 스텝에 기재된 실행 방법으로 실행 — D2). 실행 실패 → `test_run: fail` + issues_to_fix.
     - ③ **완료 신호 = issue.md 기입 확인**: `## 원인`(planner)·`## 조치`(generator) — **`## 조치` 미기입이면 READY 금지** (issues_to_fix escalate). `## 재발 방지` 미기입은 반려 사유 아님 — chat 보고에 "재발 방지 기록 권장" 1줄.
     - ④ **eval 저장 경로 (issue)**: REPORT 를 `issues/{이슈명}/issue.eval.md` 에 저장, 대응 plan 이 `issue.plan.r{N}.md` 면 `issue.eval.r{N}.md` (r 동일 — 규약 SSOT: issues/GUIDE.md) ⑤ **REPORT 필드 매핑 (issue)**: `feature:` → `{이슈명}` · `mode:` → `issue` (D3 — work_mode 가 SSOT).
     - ⑥ **비적용 스텝**: step 4(prompts/evaluator.md 체크박스 — 이슈엔 prompts/ 없음)·step 5(project.md 목표 `[x]`)·step 6(전달사항) 건너뜀 — **유령 파일·폴더 생성 금지**. step 7 의 "REPORT vs 체크박스" 동기화 검증은 "REPORT ↔ issue.md `## 조치` 기입" 대조로 대체. step 8 Slack 은 `--feature-id {이슈명}`.
     - step 7 추가 2건: REPORT 템플릿 `- mode:` 행 enum 에 `| issue` 추가 + `test_run` 행 주석에 "(work_mode=issue 는 skip 금지)" · 자기 점검 목록에 "work_mode=issue 면 `test_run` 은 `pass|fail` 만 허용 (skip 금지)" 1줄 (spec (2) 명시).

6. **공통 계약 문서 3건 + commit SKILL** — wrapper 블록(스텝 5)과 스킬 경로(스텝 7·8)의 접점.
   - `pilot/skills/context/shared/wrapper-protocol.md` § 4 에 1줄: "`work_mode` 필드 (`project`|`issue`, 부재 시 project): `issue` 면 각 wrapper 본문의 '이슈 수정 모드' 블록·경로 분기를 활성화한다." (개별 wrapper 블록과의 이중화는 § 잔류 최소 셋 원칙 범위 내 — 선언 1줄만).
   - `pilot/skills/context/shared/preamble.md`:
     - P1 에 issue 판정 항목 신설 (dp P2 대응): "**진행중 행의 mode 열이 `issue` 면** (`| issue | {이슈명} | 진행중 |`): messages.md 의 `issue_active_not_project` 출력 후 종료 — 이슈명을 `{PROJECT}` 로 오인해 `projects/{이슈명}/` 유령 경로를 만들거나 부재 state 에 기록하는 것을 막는다. **예외:** `focus` 는 종료하지 않고 issues/ 경로로 분기 (focus/SKILL.md § 경로 계약), `commit` 은 종료하지 않고 진행 (이슈 수정 커밋은 필수 경로 — D1), `pilot-doctor` 는 P 절차 밖 (doctor.py 자체 인식)." (dp 원문의 "qa/SKILL.md 와 동일 원리" 괄호는 제거 — qa 미보유.)
     - P2: 갱신 규칙에 "issue 모드의 기록 값은 issue SKILL 3단계가 확정한 **slug** 다 — 표는 1행 규약이라 개행·`|` 가 섞이면 행 파서가 깨진다" 1줄 + "**원칙 — 이력은 git log 로.**" 단락을 "**원칙 — 이력은 STATE.md 에 쌓지 않는다.** `보류`·`완료` 행을 누적하지 않는다. 과거 작업 이력의 SSOT 는 `workspace/projects/*/`·`issues/*/` **로컬 폴더** 자체다 (STATE.md·projects/ 는 통상 gitignore 라 `git log` 로는 회수되지 않는다 — 저장소가 이들을 추적하는 예외 구성에서만 git log 보조 가능)" 로 정정 — dp HEAD 일반형 그대로 (C3: 배포 문서라 "이 저장소"·내부 감사 ID "감사 F22" 유입 금지 — 저장소 특정 근거는 plan·spec 에만 남긴다).
     - P3 에 issue 분기 1항: "**issue 모드**: 도메인 소스는 `.agent-state.yml` 이 아니라 **issue.md 의 `도메인:` 라인**이다 (state 파일 미신설 — 기록처는 이슈 자신의 기록물). 라인이 있으면 그 값으로 도메인 컨텍스트를 로드, 없으면 issue SKILL 5단계의 1회 질의가 확정 후 기입한다. orchestrate-load 도 같은 라인을 파싱하므로 wrapper 사이클과 소스가 일치한다." **적용표는 무변경** (issue 행 P-1·P0·P2·P3 현행 유지, commit 행 P1 유지 — D1).
   - `pilot/skills/context/shared/messages.md` 에 `issue_active_not_project` 신설 (전제조건 메시지 절): "지금 활성 작업은 issue ({이슈명}) 입니다. 본 스킬은 project 전용이라 실행하지 않습니다.\n- 이슈 작업을 계속하려면: `@pilot-planner` (사이클) 또는 직접 수정\n- project 로 전환하려면: `/pilot:project {프로젝트명}`".
   - `pilot/skills/commit/SKILL.md` 사전 확인에 1줄: "활성 행이 `| issue | {이슈명} |` 이어도 종료하지 않고 진행한다 (P1 issue 판정의 예외 — 이슈 수정 커밋은 필수 경로. preamble P1 참조)."

7. **`pilot/skills/focus/SKILL.md` — issues/ 분기** (dp focus SKILL :26-55 대응).
   - 사전 확인에 2항 추가: 활성 행 `| project | {PROJECT} |` → project 대상 / `| issue | {이슈명} |` → **P1 issue 종료 규칙 예외** — 이슈를 대상으로 진행. `| issue | - |` (bare) 는 기록처가 없으므로 "bare issue 모드에는 focus 를 기록할 수 없습니다. `/pilot:issue {이슈명}` 으로 재진입하세요." 출력 후 종료.
   - `## 경로 계약` 을 mode 분기로 재작성: project → `workspace/projects/{PROJECT}/.focus.md`·`.focus.history/` / issue → `workspace/issues/{이슈명}/.focus.md`·`.focus.history/`. "**orchestrate-load 가 같은 기준 (work_mode) 으로 읽으므로 반드시 일치시켜야 한다** (불일치 시 래퍼가 지시를 못 본다)" 문구 포함. 기록·제거 모드의 결과 출력 경로도 활성 폴더 기준으로 1줄 명시.

8. **`pilot/skills/issue/SKILL.md` + `pilot/skills/context/lifecycle/issues/GUIDE.md` — 재정의 + slug 규약** (dp HEAD 기준, **5-bis 사전 인터뷰·인터뷰 대필 blockquote·oq-gate 약속 미이식**).
   - SKILL 재정의 (**100줄 이하 — 인터뷰 미이식으로 dp 69줄보다 짧게, 목표 ~55줄**): frontmatter description 을 사이클 지원으로 재작성 (schema.py description 바이트 상한 준수) · "경량 모드" blockquote 삭제 · 정의 3항은 spec §(6) 확정 본문 그대로 (① 누적 컨텍스트 기반 ② project 유사 구조 단건 처리 — 명명은 GUIDE § 이슈 폴더 구조 ③ 기본 사이클 유지 — 조사·회신형은 직접 처리 가능). dp 의 "> QA 결함 처리는 …" blockquote 는 **미이식**.
   - 수행 절차 6단계는 **spec §(6) "수행 절차" ①~⑥ 이 확정 본문** (이미 pilot 번호 체계 P2=STATE·P3=도메인으로 적응돼 있음) — 그대로 SKILL 에 구현한다. plan 확정 보충 4건만 추가: (i) 2단계 검색 명령은 `ls workspace/issues/ 2>/dev/null` + `grep -H "^# " workspace/issues/*/issue.md 2>/dev/null` 원문 고정 (ii) 4단계 STATE 기록 값의 "개행·`|` 금지" 사유는 preamble P2 참조로 처리 (iii) 6단계 코드 수정형 안내 문구에 "plan 은 `issues/{이슈명}/issue.plan.md`, critic → generator → evaluator (회귀 재현 테스트 실행 포함)" 경로 명시 (iv) **bare 진입 (C2 — dp HEAD 절차 1 준거)**: 고지 후 **GUIDE 로드 + 2·3단계 건너뜀** (검색·slug 불가) → 4단계 (`| issue | - | 진행중 |`) 부터, 5단계 질의 없이 MANIFEST 까지만, **6단계 안내에서 사이클 항목 제외** (orchestrate-load 의 bare 에러와 모순 금지).
   - GUIDE 재정의 (dp HEAD 대응 + 이름 매핑):
     - 개요 — projects/ 산출물 (project.md·features/·prompts/) 미참조, `workspace/context/` 도메인 지식·과거 이슈 이력·메모리는 진단 기반. 진입 모드별 동작은 issue SKILL 이 SSOT (절차 복제 금지). 처리 원칙 5항 유지.
     - 진단 절차 — 6번을 경로 분기로 재작성 (코드 결함 → `@pilot-planner` 사이클, plan: `issues/{이슈명}/issue.plan.md`, 검증: evaluator 회귀 테스트 실행 / 조사·경미 → 직접 수정) + 7·8번 (검증 — 사이클 시 evaluator REPORT / 기록 — planner=원인·generator=조치). 3~5번의 scope/enums/rules 표현은 "도메인 컨텍스트 (MANIFEST 가 안내하는 진입 파일·규칙 문서)" 로 일반화.
     - **이슈 폴더 구조 4파일** (`issue.md`·`issue.plan[.r{N}].md`·`issue.plan.critic[.r{N}].md`·`issue.eval[.r{N}].md`) + **`.r{N}` 규약 자체 정의** ("항상 마지막 `.md` 직전, 재작업·대형 개정 시 기존 r 최대값 + 1" — "qa 규약 준용" 문구 금지).
     - **§ 폴더명 (slug) 규약** — 식별자·표시명 분리 원칙 + 규칙 표 3행 (문자 집합 `[a-z0-9-]` ≤40자 / 용어 매핑 — 임의 번역 금지, `workspace/context/` 의 코드 표기 우선 / 재도출 — 폴더 기존 시 금지) + 입력→폴더→H1 예시 블록 (dp 의 `rules/retail.md`·`not_bought` 예시는 "도메인 문서가 코드 표기를 명시한 경우" 일반 예시로 각색) + 영문 강제 이유 문단 (장기 누적·셸 경로·macOS NFD·표기 흔들림 → 유사 검색 무력화).
     - **섹션별 역할 표** — 제목 H1 = AI 원문 요약 / 도메인 = AI (사용자 확정 후) / 현상·의심 영역 = 사용자 / 원인 = AI (사이클 시 `@pilot-planner`) / 조치 = AI (사이클 시 `@pilot-generator`, evaluator 가 기입 여부를 READY 게이트로 확인) / 재발 방지 = AI 선택 (미기입은 반려 사유 아님).
     - **Open Questions 항** — "(선택) 미해결 결정 항목 `- [ ]`, 형식은 feature 명세와 동일한 4 카테고리 H3 권장" **까지만** — "plan-validate 기계 검증" 약속 금지 (이식 제외 ⑥).
     - **템플릿 갱신** — H1 주석 "{제목 — 사용자 입력 원문의 1줄 요약. 폴더명 slug 와 다르다}" + `도메인: {식별자 — 미정이면 스킬 진입 시 질의 후 기입}` 라인 + 현상 확장 축 (원문 전문·증상·에러·재현 경로·`기대 동작:`·`영향 범위:` — 미확인 축 `(미확인)`). dp GUIDE :85 인터뷰 대필 blockquote 는 **미이식**.

9. **문서 신설·연결** (dp docs 대응 + 이름 매핑).
   - `pilot/docs/how-to/issue-cycle.md` 신설 (~65줄, dp HEAD 각색):
     - 한 줄 요약 (누적 컨텍스트 위 운영 문제 1건 진단·수정, 코드 수정 시 project 와 동일 사이클) · 언제 쓰나 (dp 의 qa 문단은 "활성 project 의 feature 작업은 `/pilot:project`" 로 대체) · 전제 (`/pilot:init` · `/pilot:learn` 누적일수록 진단 품질 향상).
     - 절차 1 진입 — 여러 줄 입력 권장 (명세의 재료), 유사 이슈 검색 → slug 도출 → STATE `| issue | {slug} | 진행중 |`. **인터뷰 문단 대신** "신규 이슈면 `도메인:` 확정 질의 1회". slug 코드 표기 우선 문단은 일반화 예시로. bare 안내 1줄.
     - 절차 2 현상 확인·보강 (직접 편집 — 기대 동작·영향 범위 축, `(미확인)` 표기) · 절차 3 처리 경로 (조사·경미형 / 코드 수정형 `@pilot-planner` — work_mode 인식 설명 + 단계·산출물·특칙 4행 표, evaluator 행은 "REPORT 는 `mode: issue`") · 절차 4 마무리 (재발 방지 권장 · `/pilot:commit`·`/pilot:pr` — **commit 은 issue 모드에서도 동작** 1줄 · `/pilot:project {이름}` 전환).
     - 주의 4항 — project 전용 스킬은 issue 행에서 종료 (`analyze`·`confl`·`tdd`·`create-feature`·`characterize`·`autopilot`·`pr`·`slack`, preamble P1 판정; `focus`·`commit` 예외) / 기존 이슈 파일은 훅 보호 (Write 차단·Edit 허용) / tdd·characterize 미지원 (standard 고정) / Slack 자동 no-op.
   - `pilot/docs/how-to/index.md` — `## 운영` grid 에 카드 1건: `:material-fire-extinguisher:`(류) __[운영 이슈 단건 처리](issue-cycle.md)__ — "누적 컨텍스트 기반으로 운영 이슈 1건을 진단·수정합니다. 코드 수정 시 project 와 동일한 4-에이전트 사이클을 이슈 단위로 사용합니다."
   - `pilot/mkdocs.yml` nav — `How-to > 운영` 그룹에 `운영 이슈 단건 처리: how-to/issue-cycle.md` 행 추가 (Doctor 행 앞).

10. **버전 표기 + 재생성 + 전수 게이트** (마지막 — 모든 변경 반영 후).
    - `pilot/.claude-plugin/plugin.json` `0.11.0` → `0.13.0` · `pilot/mkdocs.yml:122` `extra.version: "0.13.0"` · `pilot/docs/index.md:11` highlights 를 v0.13.0 (issue 단건 사이클 + slug 자동 명명) 로 갱신. `grep -rn "0\.11\.0" pilot/ --include="*.json" --include="*.md" --include="*.yml"` (docs-site·reference 제외) 로 표기 지점 전수 재확인.
    - `python3.12 pilot/tools/docs_build.py` 재생성 (수정된 agents 4종·issue/focus/commit SKILL·orchestrate-load docstring 의 reference 페이지 반영) → `--check` exit 0.
    - 게이트 전수 실행 (아래 § 게이트).

### 주의사항

- **이식 제외 7항 — dp 원문 소재 매핑 (스며듦 방지 체크리스트)**: ① qa phase — dp orchestrate-load `project_phase`·`resolve_project_phase`·`VALID_PROJECT_PHASES`, wrapper 의 "결함 수정 모드 (phase == qa)" 블록·참조, 훅의 `read_project_phase`·features/ qa 차단, REPORT `phase:` 필드 → **결과 JSON 미신설 + 전부 인라인 대체** ② verify-report-lint — dp evaluator ":151 lint 강제" 문구 → 모델 계약 (D2) ③ supplementary docs — dp orchestrate-load `list_supplementary_docs`·step 2-1·파생 제외 로직·해당 테스트 → 통째 미이식 ④ 단일 도메인 자동 채택 — dp `read_known_domains` 블록 (:978-993) → 미이식 (별도 백로그) ⑤ 5-bis 사전 인터뷰 — dp issue SKILL 절차 5 의 흡수 문장·5-bis 전체·GUIDE :85 blockquote·issue-cycle.md 인터뷰 문단 → 미이식, 도메인 확정은 0.25.0 원형 "자유 질의 1회" ⑥ oq-gate — dp GUIDE :96 의 "plan-validate 기계 검증" 문장·generator 의 [Open Questions 게이트] → GUIDE 는 "4 카테고리 H3 형식 권장" 까지만 ⑦ persona 주입 — dp `read_agent_persona`·`identity_yml_path`·`DP_DISABLE_PERSONA` → 미이식 (pilot 은 step 0 files_to_read 로 identity.yml 로드).
- **자기완결 인라인 치환표** (완성본에 `qa`·`phase == qa`·`instincts` 참조 잔존 금지): "결함 수정 모드와 원형이 같고" → 목적 1문장 · "`.r{N}` 규약은 qa/SKILL.md 와 동일" → GUIDE 자체 정의 · "[모드 가드] 해제" → pilot 에 모드 가드 부재라 문구 불요 (사전 실측) · "qa 블록과 동일한 3 분류·반려 기준" → 전문 인라인 (D4) · "verify-report-lint.py 도 동일 강제" → 자기 점검 목록 (D2) · "instincts" 인용 → guardrails § 사용자 게이트 생략 금지가 대응.
- **사내 식별자 금지**: 신규·수정 본문에 `dp-skills`·`deali`·`{TEAM}`·`workspace/{TEAM}`·`ag-`·`qa/`·`verify-report-lint`·`discover`·`run-cycle`·`migrate-state` 유입 금지. 기존 2건 (`auto_pilot.py:82`·`pilot-evaluator.md:54` 자기 서술) 은 sweep 게이트 "자기 서술 제외" 대상 — evaluator 판단, 본 작업이 늘리지 않는다.
- **분량 규율 (#19 게이트)**: issue SKILL ≤ 100줄 (목표 ~55줄 — dp 69줄에서 인터뷰 항 제거분만큼 짧아야 정상). wrapper 4종은 **계약 보존 우선** — 블록·분기 추가만 허용, 기존 계약 문장 삭제·재배열 금지.
- **게이트 실행 인터프리터**: 게이트는 **`/opt/homebrew/bin/python3.12`** (baseline 309 OK 실측) 로 실행. 기본 `python3`(3.14) 은 PyYAML 부재 수집 에러 (환경 이슈)·`/usr/bin/python3`(3.9) 은 구문 비호환 — 사용 금지.
- **hints 순서 계약**: issue 모드에서 `[work_mode] issue` 힌트는 main 이 추가 (build_load_plan 힌트보다 앞). "비 TDD 프로젝트" 힌트는 issue 모드에서도 출력됨 (dp 동일 거동 — 수정하지 않는다).
- **STATE 표 하위호환**: legacy 헤더 `| 순번 | 이름 | 상태 |` 는 `parse_state_md_all_rows` 가 첫 칸 "순번" 을 제외하지 않지만 상태 열 `상태 ≠ 진행중` 이라 활성 필터에서 자연 탈락 — 별도 처리 불요 (기존 워크스페이스 무중단).
- **에이전트 간 전달사항 처리 (사용자 위임 결정)**: 관련 3건 반영 — ① **open-questions.md ↔ interview.md 짝 패턴**: GUIDE 의 Open Questions 항은 open-questions.md 의 4 카테고리 H3·`- [ ]` 행 형식을 그대로 "권장" 으로만 채택 (신규 행 형식·카테고리 발명 금지) → interview.md 행 파싱 규칙·scope-sync.md 5-2 규칙 2 등 **파싱 3곳 무변경** ② **docs/reference git 미추적**: evaluator 는 스텝 10 의 docs 재생성을 커밋 diff 가 아니라 **상태 기반 증거** (`docs_build.py --check` exit 0 + 생성 페이지 목록 ↔ 소스 실재 목록 일치) 로 판정한다 ③ **orchestrate-load placeholder leak (:174)**: **별건 유지** — 본 작업은 `parse_lang_tools`·`parse_lang_override` 를 수정하지 않는다 (diff 에 포함 금지). **무관 전달사항 23건 이월 (사용자 위임 결정)** — 체크박스 불변.
- **doctor hint 1줄 정정의 근거**: `integrity.py:377` "이력은 git log 로 추적" 은 preamble P2 동일 계열 실상 불일치 (STATE.md 통상 gitignore — git log 회수 불가) — spec (3) P2 정정 파생, 같은 커밋 1줄 동기화 (spec 열거 외 유일한 추가 변경).
- **REPORT 계약 확장 주의**: `mode:` enum 에 `issue` 추가는 project 모드 출력 불변 (issue 모드 한정 표기). auto_pilot.py 의 REPORT 파서가 mode 값을 enum 검증하는지 generator 가 구현 전 확인 — 검증한다면 `issue` 허용 1줄 추가 (autopilot 은 issue 행에서 P1 종료라 실행 경로는 없지만 파서 어휘는 일치시킨다).
- **generator plan 부재 케이스는 dp 동일 공백 — 임의 개선 금지 (C5)**: planner 없이 직접 호출된 issue 세션은 `issue.plan*.md` 부재로 step 2 "없으면 skip" 적용 (변경 범위 게이트 기준 부재) — dp HEAD `ag-generator.md` step 2 동일 공백 (실측). 가드 신설·step 2 문구 수정 금지 (dp 패리티).

### 교차 의존

- feature 후속 (orchestrate-load placeholder leak, 전달사항 :174) — 본 작업이 `build_load_plan` 시그니처 (`work_mode` kwarg)·step 8 `spec_md_abs` 구조를 바꾸나 `parse_lang_tools` 는 불변 — 충돌 없음.
- `/pilot:autopilot` — issue 행에서 P1 판정으로 종료 (project 전용 유지). 본 작업은 autopilot SKILL 을 수정하지 않는다 — REPORT 파서 어휘만 확인 (주의사항 참조).
- `#22 context 드리프트 재학습` (미완 목표) — 본 작업으로 `workspace/context/pilot/index.md`·`spec.md` 의 issue 서술 (경량 모드) 이 재차 stale — 해소는 #22 `/pilot:learn` 재실행 담당 (workspace/context/ 직접 Edit 금지 — drift-protocol § A).

### 게이트 (구현 완료 판정 — spec § 기대 결과)

1. `/opt/homebrew/bin/python3.12 -m unittest discover -s pilot/tests/tools` 전체 통과 (baseline **309** + 신규 issue 케이스, 기존 무손 — C1 정정).
2. smoke (자동화): `MainIssueMode.test_issue_mode_all_phases_exit_zero` — 4 phase 모두 `work_mode: "issue"`·`domain` 파싱·prompts 미로드·exit 0. bare → exit 1 + 사이클 비지원.
3. pilot-doctor: 활성 issue workspace 에서 프로젝트 오진 0 + 스킵 안내 1줄 (`IntegrityCheckSkipsProjectOnActiveIssue`) · 활성 project workspace 기존 출력 무변화 (기존 doctor 테스트 무손으로 판정).
4. 사내 식별자 sweep: `grep -rn 'dp-skills\|deali\|workspace/{TEAM}\|ag-planner\|verify-report-lint' pilot/ --include="*.md" --include="*.py" --include="*.sh"` → 신규 유입 0건 (기존 자기 서술 2건 초과분 없음 — 제외 판단은 evaluator).
5. **순서 필수 (C1)**: 스텝 10 의 `docs_build.py` 생성 실행 **후** `--check` exit 0 + mkdocs nav 정합 (issue-cycle.md 포함) — 생성 전 exit 1 이 정상 (미추적 reference 부재, 사전 실측). **docs/reference 는 git 미추적 — 상태 기반 증거로 판정** (전달사항 ②).
6. 버전 표기 동기: plugin.json `0.13.0` + `grep "0\.11\.0"` 잔존 0 (표기 3곳 전수).
