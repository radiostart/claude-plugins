# #26 issue 단건 사이클 + 폴더 slug 자동 명명 (dp-skills 0.25.0/0.30.0 포팅)

> source: prompt
> created: 2026-07-31T00:00:00Z
> user_prompt: "dp-skills 0.25.0 'issue 단건 사이클' + 0.30.0 'issue 폴더 slug 자동 명명' 을 pilot 에 포팅한다. 현재 pilot issue SKILL 은 경량 모드 (사이클·slug 없음). 주의: pilot 은 TEAM 레이어 없음 (workspace/ 직접), verify-report-lint 없음 (#20 삭제 — evaluator 게이트는 모델 계약), dp 의 qa phase 개념 없음. 이름 매핑: /dp-skills:* → /pilot:*, ag-* → pilot-*"

## 포팅 원본 (SSOT)

- 원본 저장소: `/Users/jay-p/Projects/deali-skills-plugin` (플러그인 본체 `dp-skills/`), HEAD = `7dc24fb` (0.30.2) — **파일의 HEAD 상태를 기준**으로 이식하되 아래 "이식 제외" 를 적용한다.
- 범위 특정 커밋: `cf54939` (0.25.0 issue 단건 사이클 — 변경 파일 33개) · `c1febc6` (0.30.0 slug 자동 명명 — 변경 파일 7개). `git show {커밋} --stat` 으로 대상 파일을, HEAD 파일로 최종 내용을 확인한다.
- 본 워크스페이스 기준점: pilot v0.11.0 (`bac0375` — dp-skills 0.30.2 하니스 정합 기포팅). 즉 **이 두 기능 외의 delta 는 이미 반영돼 있다** — issue 관련 hunk 만 이식한다.

## 요구사항

- **조건**: pilot v0.11.0 (doctor → pilot-doctor 리네임·effort 프런트매터·protect-managed projects 상위 차단 반영 상태).
- **트리거**: 현행 `/pilot:issue` 는 경량 모드 — 사이클 (`@pilot-*`) 이 STATE 의 issue 행을 인식하지 못해 이슈명을 프로젝트로 오인 (`.agent-state.yml 누락` 오도성 에러·`projects/{이슈명}/` 유령 경로·doctor 오진). 이슈 폴더명 규약도 없어 한글 자유 문자열 폴더가 유사 이슈 검색을 무력화한다.
- **기대결과** — 8개 영역:

  **(1) `pilot/tools/orchestrate-load.py` — STATE.md mode 열 인식 (work_mode 계약)**
  - `parse_state_md_active` 가 `(mode, 이름)` 튜플 목록을 반환. 행 파싱 SSOT 는 `doctor/_common.parse_state_md_all_rows` (pilot `_common.py:116` 에 이미 존재 — 재사용, 인라인 파서 제거).
  - 결과 JSON 에 `work_mode: "project" | "issue"` 필드 신설. mode 열이 `issue` 외 값 (`project`·legacy 순번 숫자·기타) 이면 project 폴백 (하위호환).
  - `--project` 명시 시 STATE 우회 project 모드 강제 (corrupt-state 탈출구 — argparse help 갱신).
  - issue 모드 분기: `| issue | - |` (bare) → "이슈명 없는 issue 모드는 사이클 비지원 — `/pilot:issue {이슈명}` 으로 생성 후 재시도" 에러. `workspace/issues/{이슈명}/issue.md` 부재 → **issue 맥락 에러** (`/pilot:issue {이슈명}` 처방 — 종전 `.agent-state.yml 누락` 오도성 처방이 나가지 않아야 함). 존재 시 stateless 고정: `analyzed=false`·`tdd=false`·`mode=null` (`.agent-state.yml` 안 읽음), `[work_mode] issue — 이슈 수정 모드: 최소 변경·롤백 가능. issue.md 가 단건 명세 (planner=원인, generator=조치 기입)` 힌트.
  - `determine_domain` 정규식을 `(?:domain|도메인)` 으로 확장 — issue.md 상단 `도메인: {값}` 라인 파싱 (project.md 의 기존 `domain:` 도 계속 매칭).
  - `build_load_plan(work_mode=...)`: 작업 명세 = issue 모드에서 `workspace/issues/{이슈명}/issue.md` (project.md 부재 힌트 억제 — project 전제 힌트 미출력). `prompts/{phase}.md` 로드는 issue 모드에서 **전체 skip** (부재 힌트도 미출력 — 이슈엔 프로젝트별 prompts/ 트윈이 없다). 언어·도구 override (step 8) 소스 = 작업 명세 문서 (issue.md 는 통상 제한사항 없음 — 빈 dict graceful). MANIFEST 도메인 진입 파일·boundaries 로드는 양 모드 동일 (pilot 방식 유지).
  - `.focus.md` 경로: work_mode 에 따라 `workspace/{issues|projects}/{이름}/.focus.md` 분기.
  - 모듈 docstring 의 출력 JSON 스키마·issue 모드 계약 주석 갱신. `instructions` 필드 (pilot 고유) 는 양 모드 동일 유지.

  **(2) `pilot/agents/pilot-{planner,planner-critic,generator,evaluator}.md` — 이슈 수정 모드 블록**
  - 4종 모두 step 1 (orchestrate-load) 직후 "[필수] work_mode 확인" 추가 — `issue` 면 이슈 수정 모드 활성 (issue 는 standard 고정 — tdd/characterize 와 동시 활성 없음), `project`/필드 부재 (구버전 출력) 면 평소대로.
  - **자기완결 인라인 필수**: dp 원문의 이슈 블록은 qa 결함 수정 모드를 "원형" 으로 참조·승계하는데 pilot 엔 qa 가 없다 — 참조 대신 계약 전문을 블록 안에 기술한다.
  - planner: 명세 = `issues/{이슈명}/issue.md` 의 `## 현상`·`## 의심 영역` (features/·project.md·prompts/ 는 존재하지 않음) · 최소 변경·롤백 가능 (인접 개선·리팩터·신규 추상화 제안 금지) · `## 원인` Edit 기입 · **회귀영향 (영향 범위) 후보 필수** (0건이면 검색 범위·키워드 기록) · **회귀 재현 테스트 스텝 필수 작성** · 결함 지점 1줄 (`결함 함수: {file_path}#{symbol}`, 데이터 정합 이슈면 `조치 대상: {테이블·데이터 범위}`) · plan 저장 = `issues/{이슈명}/issue.plan[.r{N}].md` + plan-validate `--mode standard` · 절차 2 (에이전트 간 전달사항 — project.md 없음) 비적용 · Slack 메시지 `계획 확인 필요: {이슈명}` 치환 (notifier 자동 no-op, 호출 유지).
  - planner-critic: 후보 탐색 `ls -t workspace/issues/{이슈명}/issue.plan*.md` · 입력 = issue.md (현상·의심 영역) + issue.plan[.r{N}].md · 챌린지 저장 = `issues/{이슈명}/issue.plan.critic[.r{N}].md` · 챌린지 기준·산출 형식은 project 와 동일.
  - generator: plan 로드 = `issues/{이슈명}/issue.plan[.r{N}].md` (r 최대값) · **변경 범위 게이트** — plan 의 결함 지점 1줄 범위 안에서만 수정, 범위 밖 변경 필요 발견 시 구현 중단 + 보고 (`@pilot-planner` 재확인 안내) 후 종료 · `## 조치` Edit 기입 (변경 파일 목록 + 핵심 diff 요약, 데이터 조치면 실행 쿼리·대상 범위) · plan-validate 동일 경로 `--mode standard`.
  - evaluator: **회귀 재현 테스트 직접 실행** — plan 의 해당 스텝 테스트를 `{test_command}` 로 실행하고 REPORT `test_run: pass|fail` 기록, **skip 금지** (pilot 은 lint 도구가 없으므로 모델 계약으로 명문화 — pilot-evaluator 의 REPORT 자기 점검 목록에 반영) · 완료 신호 = issue.md `## 원인`·`## 조치` 기입 확인, **`## 조치` 미기입이면 READY 금지** (issues_to_fix escalate) · `## 재발 방지` 미기입은 반려 사유 아님 (권장 1줄) · REPORT 저장 = `issues/{이슈명}/issue.eval[.r{N}].md` (r 은 plan 과 동일) · REPORT 필드 매핑 — feature → `{이슈명}`, 모드 표기는 `issue` (pilot REPORT 형식에 맞게 설계) · 비적용 스텝 — project.md 목표 `[x]`·전달사항 작성·prompts 체크박스 갱신 (유령 파일·폴더 생성 금지), 동기화 검증은 "REPORT ↔ issue.md `## 조치` 기입" 대조로 대체, Slack 은 `--feature-id {이슈명}`.

  **(3) `pilot/skills/context/shared/preamble.md` — P 절차 issue 행 판정**
  - P1 (활성 프로젝트 확인) 에 issue 행 판정 신설: 진행중 행 mode 가 `issue` 면 messages.md 의 `issue_active_not_project` 출력 후 종료 — 이슈명을 `{PROJECT}` 로 오인해 `projects/{이슈명}/` 유령 경로를 만드는 것을 차단. **예외**: `focus` 는 종료하지 않고 issues/ 로 분기 (focus SKILL § 경로), `commit` 은 종료하지 않고 진행 (아래 비즈니스 규칙), `pilot-doctor` 는 P 절차 밖 (doctor.py 자체 인식).
  - P2 (STATE.md 갱신): 기록 값 = slug (개행·`|` 가 섞이면 행 파서가 깨진다) 명시. "이력은 git log 로" 원칙 문구를 실상에 맞게 정정 — `workspace/STATE.md` 는 이 저장소에서 gitignore (감사 F22) 라 git log 로 회수되지 않는다. 이력 SSOT = `projects/*/`·`issues/*/` 폴더.
  - P3 (도메인 컨텍스트 로드): issue 분기 — 도메인 소스는 `.agent-state.yml` 이 아니라 **issue.md 의 `도메인:` 라인** (state 파일 미신설 — 기록처는 이슈 자신의 기록물). orchestrate-load 도 같은 라인을 파싱하므로 wrapper 사이클과 소스 일치.

  **(4) `pilot/hooks/protect-managed.sh` — issues/ 보호 확장**
  - `workspace/issues` 상위 폴더 자체: destructive 대상이면 차단 (모든 이슈 기록 소실 경로 — v0.11.0 의 projects 상위 차단 블록과 대칭 구현).
  - `workspace/issues/{이슈명}(/|$)`: 기존 파일·폴더 Write·destructive 차단, 신규 생성·Edit·`.focus.md`·`.focus.history/`(기존 경로 무관 예외) 통과 — issue.md 의 사용자 작성 현상·누적 기록이 재진입 Write 로 소실되는 것을 차단. 헤더 주석·에러 메시지도 issues 규칙 반영.

  **(5) `pilot/skills/focus/SKILL.md` — issues/ 분기**
  - 사전 확인: 활성 행이 `| issue | {이슈명} |` 이면 P1 의 issue 종료 규칙 **예외** — 이슈를 대상으로 진행. `| issue | - |` (bare) 는 기록처가 없으므로 "bare issue 모드에는 focus 를 기록할 수 없습니다. `/pilot:issue {이슈명}` 으로 재진입하세요." 후 종료.
  - 경로 계약: issue 활성 시 `workspace/issues/{이슈명}/.focus.md` · 아카이브 `workspace/issues/{이슈명}/.focus.history/{timestamp}.md`. "orchestrate-load 가 같은 기준 (work_mode) 으로 읽으므로 반드시 일치시켜야 한다" 문구 포함. 결과 출력 경로도 분기.

  **(6) `pilot/skills/issue/SKILL.md` + `pilot/skills/context/lifecycle/issues/GUIDE.md` — 재정의 + slug 규약**
  - SKILL 재정의: "경량 모드" blockquote 삭제. 정의 3항 — ① 누적 컨텍스트 기반 (projects/ 산출물 독립, `workspace/context/` 도메인 지식·과거 `issues/` 이력·메모리 P0 는 진단 기반) ② project 유사 구조의 단건 처리 (issue.md 1건 명세 + 사이클 파생 산출물) ③ 기본 사이클 유지 (코드 수정 이슈는 `@pilot-planner → @pilot-planner-critic → @pilot-generator → @pilot-evaluator`, 조사·회신형은 사이클 없이 직접 처리 가능). frontmatter description 도 사이클 지원으로 재작성.
  - 수행 절차 (6단계): ① bare 진입 1줄 고지 (기록·사이클 비지원) ② **유사 이슈 검색** — `ls workspace/issues/` + `grep -H "^# " workspace/issues/*/issue.md` 로 폴더명·H1 제목 **병행** 매칭, 유사 발견 시 "재개 / 새 이슈" 질의 (`{slug} — {제목}` 목록), H1 없는 기존 이슈는 폴더명 매칭만 (소급 기입 금지) ③ **slug 결정 + 폴더 생성/로드** — 폴더명 = 원문에서 도출한 영문 kebab slug (`[a-z0-9-]` 만 40자 이내), 팀 용어는 임의 번역 금지 — `workspace/context/` 도메인 문서 (rules·enums 류) 에 코드 표기가 있으면 그것을 채택 (폴더명으로 소스 grep 가능하게), 축이 둘 이상이거나 매핑 모호하면 후보 2~3개 제시 후 확정·명확하면 1줄 고지 후 진행, 신규면 GUIDE 템플릿으로 생성 (H1 = 원문 1줄 요약 — 개행·`|` 제거, `## 현상` = 원문 전문, `도메인:` 라인), 기존이면 issue.md 만 Read + 파생 산출물 (`issue.plan*.md`·`issue.eval*.md`) 진행 상태 요약, **slug 재도출 금지** ④ P2 — STATE 본문 `| issue | {slug} | 진행중 |` 1행 교체 (bare 는 `| issue | - | 진행중 |`) ⑤ 도메인 확정 + P3 — `도메인:` 라인 부재 시 **1회 질의** (`## 의심 영역` 과 `workspace/context/` 대조 후보 제시 → 확정 후 issue.md 상단 `도메인: {값}` Edit 기입), 판단 어려우면 미정 진행 (MANIFEST 까지 — wrapper 진입 시 재질의), bare 는 질의 없이 MANIFEST 까지 ⑥ 결과 출력 — 산출물 상태 분기 (명시적 if/elif/else): eval 최신 READY → "`## 재발 방지` 기록 확인" 안내 / elif plan 존재 → 재개 안내 (챌린지 전 `@pilot-planner-critic`, 승인 후 `@pilot-generator` — 승인 흔적은 산출물에 없으므로 사용자 재확인) / else 경로 분기 (코드 수정형 → `@pilot-planner` 사이클 · 조사·경미형 → 직접 처리 후 `## 원인`·`## 조치` 기록).
  - GUIDE 재정의: 개요 (누적 컨텍스트 문구) · 진단 절차 6번 경로 분기 (사이클 ↔ 직접) · 폴더 구조 4파일 (`issue.md`·`issue.plan[.r{N}].md`·`issue.plan.critic[.r{N}].md`·`issue.eval[.r{N}].md`) + **`.r{N}` 규약 자체 정의** ("항상 마지막 `.md` 직전, 재작업·대형 개정 시 기존 r 최대값 + 1" — dp 의 "qa 규약 준용" 참조를 쓰지 않고 본문에 직접 기술) · **§ 폴더명 (slug) 규약** — 식별자·표시명 분리 원칙, 규칙 표 (문자 집합 / 용어 매핑 / 재도출), 입력→폴더→H1 예시 블록, 영문 강제 이유 (장기 누적·셸 경로·NFD·표기 흔들림 → 유사 검색 무력화) · 섹션별 역할 표 (제목 H1 = AI 원문 요약 / 도메인 / 현상 = 사용자 / 의심 영역 / 원인 = 사이클 시 `@pilot-planner` / 조치 = `@pilot-generator` / 재발 방지 선택) · 템플릿 갱신 (H1 주석 "폴더명 slug 와 다르다" + `도메인:` 라인 + 현상 확장 축: 기대 동작·영향 범위 — 미확인 축 `(미확인)` 표기).
  - `pilot/skills/context/shared/messages.md`: `issue_active_not_project` 메시지 신설 (dp 대응 — pilot 어휘: `@pilot-planner` (사이클) 또는 직접 수정 / 프로젝트 전환 `/pilot:project {이름}`).

  **(7) `pilot/tools/doctor/integrity.py` — 활성 판정 오진 제거** (dp `integrity.py:1977-2041` 대응)
  - 활성 프로젝트 해석이 issue 행을 프로젝트로 오인하지 않도록: mode == `issue` 행은 프로젝트 판정에서 제외 + `determine_active_issue` 신설 + 활성 issue 면 "활성 issue ({이슈명}) — 프로젝트 체크 건너뜀 (이슈는 issues/ 폴더 기반. 프로젝트 검사는 --project 로 지정)" 안내 후 프로젝트 검사 skip. `parse_state_md` (mode-blind 이름 반환) 소비처 전수 점검 — 이슈명이 프로젝트 경로로 새는 경로 제거. STATE 관련 `--fix` (`_fix_state_md_prune_history`) 가 issue 행을 훼손하지 않는지 확인.

  **(8) 테스트·문서·버전**
  - `pilot/tests/tools/test_orchestrate_load.py` 확장: work_mode 판정 (issue/project/legacy 폴백) · bare issue 에러 · issue.md 부재 에러 (오도성 처방 부재 검증) · `도메인:` 라인 파싱 · prompts skip · focus 경로 분기 · `--project` 우회 (dp 동일 커밋의 +132줄 대응 — TEAM 제거 적응).
  - `pilot/tests/tools/test_protect_managed.py` 확장: issues/ 기존 파일 차단 · 신규 통과 · 상위 폴더 차단 (dp `test_protect_managed_hook.py` +50줄 대응).
  - `pilot/tests/tools/test_doctor_issue_mode.py` 신규 (dp 110줄 대응 — 활성 issue 시 프로젝트 오진 0).
  - `pilot/docs/how-to/issue-cycle.md` 신설 + `docs/how-to/index.md` 행 + `mkdocs.yml` nav (dp 대응, 이름 매핑 적용). `docs/index.md` 의 issue 서술이 있으면 slug·사이클 반영.
  - `pilot/.claude-plugin/plugin.json` 0.11.0 → **0.13.0** + 버전 표기 동기 지점 grep 으로 전수 확인 (v0.11.0 커밋이 "버전 표기 3곳" 동기화한 전례).

## 상태 전환

| STATE.md 활성 행 | orchestrate-load work_mode | 로드 기반 | 상태 파일 |
| --- | --- | --- | --- |
| `\| project \| X \| 진행중 \|` | `project` | `projects/X/` (project.md·prompts/) | `.agent-state.yml` 필수 |
| `\| issue \| {slug} \| 진행중 \|` | `issue` | `issues/{slug}/issue.md` 단건 명세 | 없음 (stateless — analyzed/tdd/mode 고정) |
| `\| issue \| - \| 진행중 \|` | — | 에러 (사이클 비지원, bare 는 스킬 경로만) | — |
| legacy (`\| 1 \| X \| 진행중 \|` 등 issue 외 첫 칸) | `project` 폴백 | 기존과 동일 | 기존과 동일 |

## 비즈니스 규칙

- **이름·구조 매핑 (전 파일 공통)**: `/dp-skills:*` → `/pilot:*` · `@ag-*` → `@pilot-*` · `workspace/{TEAM}/` → `workspace/` · 프로젝트 트윈 `agents/{phase}.md` → `prompts/{phase}.md` · `discover` → `learn` · `dp-doctor` → `pilot-doctor` · scope/rules 직접 로드 서술 → pilot 의 MANIFEST 도메인 진입 파일 계약 유지 (`workspace/context/` 하위 구조는 자유 — 플러그인은 MANIFEST 만 안다).
- **이식 제외 (pilot 에 없는 개념 — 흔적도 남기지 말 것)**: ① qa phase (`project_phase`·`resolve_project_phase` — 결과 JSON 에 미신설. REPORT 의 모드 표기는 work_mode 로 직접) ② `verify-report-lint.py` (#20 삭제 — test_run 강제는 evaluator 모델 계약 문구로) ③ supplementary docs 힌트 (`list_supplementary_docs` — pilot 미보유 기능, 파생 산출물 제외 로직 포함 통째 미이식) ④ 단일 도메인 자동 채택 (dp 0.26.0 HOTL — 별도 백로그) ⑤ **issue SKILL 5-bis 사전 인터뷰** (dp 0.27.0 사전 질의형 — pilot #17 OQ 소비형과 같은 날 갈라진 다른 설계, 통째 이식 금지. 도메인 확정은 0.25.0 원형인 "자유 질의 1회" 로) 및 GUIDE 의 인터뷰 대필 blockquote ⑥ oq-gate (dp 0.21.0 — 별도 백로그. GUIDE 의 Open Questions 항은 "선택 섹션 + 4 카테고리 H3 형식 권장" 까지만, "plan-validate 기계 검증" 약속 금지 — pilot plan-validate 에 oq 필드 없음) ⑦ persona 주입·`DP_DISABLE_PERSONA` (pilot 은 identity.yml 로드 방식이 다름 — 현행 유지).
- **자기완결 원칙**: dp 이슈 블록의 "qa 블록과 동일/원형 승계" 류 참조는 모두 전문 인라인. 완성본에 `qa`·`결함 수정 모드 (phase == qa)` 참조가 남으면 안 된다.
- **commit 은 issue 모드에서 계속 동작한다** — dp 원형에서 commit 은 활성 확인 (dp P2) 자체를 수행하지 않아 이슈 작업 중 커밋이 가능하다. pilot 은 commit 이 P1 을 수행하므로 P1 issue 판정의 예외로 명시해 등가를 만든다 (이슈 수정 커밋은 필수 경로). planner 는 commit SKILL 의 `{PROJECT}` 실사용을 확인해 예외 구현 (예외 목록 vs 적용표 조정) 을 확정한다. `pr`·`slack`·`analyze`·`create-feature`·`confl`·`tdd`·`characterize`·`autopilot` 는 dp 대칭대로 issue 행에서 종료 (project 전용).
- **slug 규약 (0.30.0)**: 식별자 (폴더명, `[a-z0-9-]` ≤40자) 와 표시명 (issue.md H1, 한글 원문 요약) 분리. 용어 임의 번역 금지 — workspace/context/ 의 코드 표기 우선. 폴더 기존 시 재도출 금지. 유사 이슈 검색은 폴더명 `ls` + H1 `grep` 병행.
- **분량 규율 (#19 게이트)**: 재작성되는 SKILL.md 는 100줄 이하 유지 (issue SKILL — 인터뷰 미이식으로 dp 69줄보다 짧아야 정상). wrapper 4종은 계약 보존 우선 (블록 추가는 허용, 기존 계약 삭제 금지).
- **사내 식별자 금지**: 완성본에 `dp-skills`·`deali`·`{TEAM}`·`workspace/{TEAM}`·`ag-`·`qa/`·`verify-report-lint`·`discover`·`run-cycle`·`migrate-state` 등 dp 전용 식별자가 남으면 안 된다 (HANDOFF sweep grep 이 게이트).
- **wrapper-protocol.md**: 반환 JSON 처리 규칙 SSOT 에 `work_mode` 필드 존재·의미 1줄 반영 (4 wrapper 공통 계약 — 개별 wrapper 블록과 이중화 허용 범위는 #19 잔류 최소 셋 원칙 준수).
- 에이전트 간 전달사항 중 본 feature 관련 3건 반영: ① `open-questions.md ↔ interview.md 짝 패턴` — issue.md 의 Open Questions 형식이 feature 명세와 동일 4 카테고리 H3 를 쓰도록 정렬 (파싱 규칙 3곳 동기화 유발 변경 금지) ② `docs/reference git 미추적` — evaluator 는 docs 재생성을 상태 기반 증거로 판정 ③ `orchestrate-load placeholder leak (:173)` — **별건 유지**: 본 작업은 `parse_lang_tools` 를 수정하지 않는다 (교차 의존만 계획에 명시).

## 예외 케이스

- STATE 에 `| issue | X | 진행중 |` 인데 `issues/X/issue.md` 부재 → issue 맥락 에러 (`.agent-state.yml`·projects/ 처방 문구가 출력되면 회귀).
- `도메인:` 라인 부재 → orchestrate-load 는 도메인 미판정 힌트로 진행 (에러 아님 — 재질의는 스킬 경로 책임). 라인 값의 경로 탈출 문자는 pilot 현행 `has_path_traversal` 규칙 유지 (WARN + 무시 — dp 의 `/` 허용 `has_domain_traversal` 은 계층 식별자용이라 미이식).
- 이슈명 (slug) 의 traversal 문자 → 기존 project 검사 재사용 (`has_path_traversal`).
- legacy STATE 표 (첫 칸 순번 숫자) → project 폴백으로 기존 워크스페이스 무중단.
- H1 이 없는 기존 이슈 폴더 → 유사 검색은 폴더명 매칭만, H1 소급 기입 금지.
- focus: bare issue (`| issue | - |`) → 기록 불가 안내 후 종료.
- 재진입 (`/pilot:issue {기존슬러그}`) → issue.md Read 만 (GUIDE 미로드·slug 재도출 금지·기존 파일 Write 는 훅이 차단).

## 기대 결과 (게이트)

- `python3 -m unittest discover -s pilot/tests/tools` 전체 통과 (기존 무손 + 신규 issue 케이스).
- smoke: 임시 workspace 에 `| issue | test-slug | 진행중 |` + `issues/test-slug/issue.md` (`도메인: pilot`) 구성 → orchestrate-load 4 phase 모두 `work_mode: "issue"`·`domain: "pilot"`·prompts 미로드·exit 0. `| issue | - |` → exit 1 + 사이클 비지원 메시지.
- pilot-doctor: 활성 issue 상태에서 프로젝트 오진 0 + 스킵 안내 1줄. 활성 project 상태 기존 출력 무변화.
- 사내 식별자 sweep 0건: `grep -rn 'dp-skills\|deali\|workspace/{TEAM}\|ag-planner\|verify-report-lint' pilot/ --include="*.md" --include="*.py" --include="*.sh"` (자기 서술 제외 판단은 evaluator).
- `python3 pilot/tools/docs_build.py --check` exit 0 + mkdocs nav 정합 (신규 how-to 포함).
- 버전 표기 동기: plugin.json `0.13.0` + 표기 지점 전수 (grep `0\.11\.0`).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] 이식 기준 시점 (0.25.0/0.30.0 커밋 vs HEAD 0.30.2) → HEAD 파일 상태 기준 + 이식 제외 목록 적용 (본 명세 § 포팅 원본 — 사용자 지시·메모리 동기화 규칙이 결정 SSOT)
- [x] 인터뷰·oq-gate·supplementary·HOTL 동시 이식 여부 → 전건 제외 (§ 비즈니스 규칙 "이식 제외" — 별도 백로그 유지)
- [x] commit/pr 의 issue 모드 거동 → commit 예외 (계속 동작)·pr 종료 (dp 대칭) — § 비즈니스 규칙 확정, 구현 방식만 planner 위임
- [x] 버전 → 0.13.0 minor bump (dp 는 0.25.0 에서 minor bump — 동일 원칙. 최초 결정은 0.12.0 이었으나 2026-08-01 재번호 — 병렬 포팅 세션의 init/review 리네임 건이 v0.12.0 을 선점: 커밋 58b0c22, stacked PR #18)
