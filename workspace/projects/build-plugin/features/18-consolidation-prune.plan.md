# 구현 계획: #18 정비 prune — 미사용·드리프트 정리

> 모드: standard (tdd: false, mode: null) · 작성: 2026-07-24 planner
> 근거 SSOT: `docs/audits/2026-07-24-pilot-consolidation-audit.md` § 3·§ 4 / `2026-07-24-audit-1-reference-graph.md` § B·C·D / `2026-07-24-audit-2-duplication.md` § B
> 원칙: 동작 변경 없는 삭제·문구 정정만. 정본 판단은 감사 축 2 § B 판정 그대로 (재조사 안 함).
> **승인 기록 (2026-07-24)**: 사용자 확인 1~4 전부 권고안대로 승인. feature spec 정정 (INDEX.md 혼동 :13 · verify-reports 위치 오기 :29) 반영 완료. 전달사항 8건 소비 `[x]` 처리, 나머지 ~28건은 #19/#20 이월.
> **critic 합의 반영 (2026-07-24, `.plan.critic.md` C1~C7 전건 accepted)**: C1 사용자 재결정 — `_input/` 삭제 취소·**보존** (배포 튜토리얼 `pilot/docs/tutorial/getting-started.md:16` 이 소비자). C2 잔존 참조 게이트를 `git grep` 경로 앵커로 재설계. C3 사용자 재결정 — B-9 INFO 문구 중립화 전면 통일 (3곳). C4 docs_build CI 논거 정정. C5 빈 카테고리 가드. C6 인용 정정 (:46·15파일). C7 generator 행 1셀 추가.

### 변경 파일

- [x] `pilot/tests/fixtures/handoff-quality/` — 전체 삭제 (bad/05·06, good/03·04 계 4파일. 소비 도구는 2026-07-10 감사에서 이미 삭제, 저장소 참조 0건 확인)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` — 삭제 (수동 회귀 하네스 진입점)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/{learn,project,analyze,wizard,tdd-on,tdd-off,doctor-onboarding}/` — 삭제 (계 37파일. `diff.sh` 의 `EXPECTED_SUBDIRS` 로만 소비 — 자동 테스트 참조 0건 확인)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/README.md` — 재작성 (170줄 → 보존 픽스처 5종 + `_input/` 용도 설명만. 수동 회귀 절차·diff.sh 사용법 전부 제거 — 죽은 참조 방지) **(승인됨 2026-07-24)**. `_input/` (15파일) 은 critic C1 재결정으로 **보존** — "배포 튜토리얼 (`pilot/docs/tutorial/getting-started.md`) 의 더미 저장소용" 설명을 README 에 명시. 이관·튜토리얼 재작성은 하지 않음 (#18 무동작변경 원칙)
- [x] `pilot/examples/code-review/README.md` — 삭제 (외부 참조 0건 — `{lang}.md` 패턴 참조만 존재)
- [x] `pilot/skills/context/lifecycle/INDEX.md` — 삭제 (사람용 라우터, 런타임 로더·외부 링크 0건)
- [x] `pilot/skills/context/lifecycle/setup/README.md` — 삭제 (inbound 링크는 삭제되는 lifecycle/INDEX.md 뿐)
- [x] `pilot/skills/context/lifecycle/issues/example/issue.md` — 삭제 (inbound 링크는 삭제되는 lifecycle/INDEX.md 뿐. `/pilot:issue` 는 issues/GUIDE.md 인라인 템플릿 사용)
- [x] `pilot/skills/context/INDEX.md` — 드리프트 정정 4곳: B-1 (:53) · B-2 (:109·:117) · B-6 (:137) · A-12 (:58-68 트리) **(승인됨 2026-07-24 — spec :13 의 파일 혼동 문구도 정정 완료)**
- [x] `pilot/skills/analyze/SKILL.md` — B-2 (:202) · B-9 (:167) 문구 정정
- [x] `pilot/skills/context/shared/open-questions.md` — B-9 정본 문구 중립화 (:54, critic C3 사용자 재결정)
- [x] `pilot/skills/analyze/references/scope-sync.md` — B-9 동일 INFO 문구 통일 (:107, critic C3 — SKILL.md:167 의 위임처라 누락 시 새 모순 발생)
- [x] `pilot/skills/pr/SKILL.md` — B-4 (:49) 자기순환 오문 정정
- [x] `pilot/skills/context/lifecycle/projects/GUIDE.md` — B-3 (:173) · B-5 (:208) 정정
- [x] `pilot/skills/context/lifecycle/projects/prompts-scaffold-notes.md` — B-5 (:56) 정정
- [x] `pilot/skills/code-review-init/SKILL.md` — B-7 (:31) messages.md 키 참조로 정정
- [x] `pilot/skills/tdd/SKILL.md` — B-8 (:13) characterize 정본 포인터 정정
- [x] `pilot/skills/doctor/SKILL.md` — :46 의 존재하지 않는 `.github/workflows/validate.yml` stale 언급 정정 **(승인됨 2026-07-24, 라인 critic C6 정정)**
- [x] `pilot/tools/docs_build.py` — stale 출력 정리 로직 추가 (감사 축 1 § D-2)
- [x] `pilot/tests/tools/test_docs_build.py` — stale 정리 테스트 케이스 추가

### 구현 순서

1. **삭제 + 잔존 참조 정리** — #19 재작성 전에 죽은 참조를 먼저 확정하는 것이 본 feature 의 존재 이유 (사이클 1/3).
   - `git rm -r` 로 삭제: `handoff-quality/` 전체, `v0.1.0-baseline/{diff.sh,learn,project,analyze,wizard,tdd-on,tdd-off,doctor-onboarding}`, `examples/code-review/README.md`, `lifecycle/{INDEX.md,setup/README.md,issues/example/issue.md}`.
   - **보존 (오삭제 금지)**: `v0.1.0-baseline/{config,external-domain,migration,open-questions,transaction-contracts}` — 각각 `test_doctor_integrity.py`·`test_doctor_external_domain.py`+`test_doctor_cross_domain.py`·`test_doctor_migration.py`·`test_doctor_open_questions.py`·`test_doctor_cross_domain_transaction.py` 가 소비 (경로 인용 실측 완료). **`v0.1.0-baseline/_input/` (15파일) 보존** — 배포 튜토리얼 `pilot/docs/tutorial/getting-started.md:16` 이 더미 저장소로 복사 (critic C1, 사용자 재결정 2026-07-24). sibling `tests/fixtures/{verify-reports,docs_build,regen-verify}` 도 무관 — 건드리지 않음.
   - `v0.1.0-baseline/README.md` 재작성: 보존 픽스처 5종의 용도 + 소비 테스트 매핑 표 + `_input/` 의 "배포 튜토리얼 (docs/tutorial/getting-started.md) 더미 저장소용 보존" 설명만 남긴다. diff.sh·재실행 절차·expected 트리 서술 전부 제거.
   - 삭제 후 잔존 참조 0 확인 (critic C2 재설계 — `git grep` 은 untracked·gitignored 산출물 자동 제외, `docs/audits/` 는 pathspec `pilot/` 밖):

     ```bash
     git grep -nE "fixtures/handoff-quality|v0\.1\.0-baseline/(diff\.sh|learn/|project/|analyze/|wizard|tdd-on|tdd-off|doctor-onboarding)|lifecycle/INDEX\.md|lifecycle/setup/README|issues/example/issue\.md|examples/code-review/README" -- pilot/
     ```

     기대결과: 매칭 0 (exit 1). `_input` 은 보존 확정이라 패턴에서 제외 — hooks 의 `tool_input`·테스트 메서드명 오탐 문제도 함께 소멸.

2. **드리프트 정정 B-1~B-9** — 각 항목 정본은 감사 축 2 § B 판정. 문구만 바꾸고 구조·단계 번호·기계 계약은 불변.
   - **B-1** `context/INDEX.md:53`: "기존 `진행중` 행을 모두 `보류`로 변경 후 새 행을 추가한다" → preamble P2 현행으로: "테이블 본문 전체를 삭제 후 새 행 1개만 추가한다 (`보류`·`완료` 행 누적 금지 — 이력은 git log)". 정본: `shared/preamble.md:47-49`.
   - **B-2** `context/INDEX.md:109`: "@pilot-planner 가 Red 단계에서 feature.md 를 직접 읽어 실패 테스트를 작성한다" → "@pilot-planner 는 스텝별 Red 계약만 남기고, 실패 테스트 작성 (Red) 은 @pilot-generator 가 수행한다". `:117` planner 행 TDD 컬럼: "+ 스텝 분할 + 실패 테스트 작성 (Red)" → "+ 스텝 분할 + Red 계약 작성 (실패 테스트는 Generator)". `:119` generator 행 TDD 컬럼 (critic C7a): "+ 실패 테스트 통과 최소 구현 + Refactor (Green)" → "+ Red 실패 테스트 작성 → Green 최소 구현 → Refactor" — 인접 행 반쪽 stale 방지. `analyze/SKILL.md:202`: 동일 취지로 "TDD 모드에서는 @pilot-generator 가 `.plan.md` 의 Red 계약을 따라 실패 테스트를 작성한다 (Planner 는 Red 계약만 — 상세: rgr.md)". 정본: `modes/rgr.md:30-34,46`.
   - **B-3** `projects/GUIDE.md:173`: 구템플릿 섹션명 (`## 개요`·`## 조건 / 트리거 / 기대결과`·`## 변경 대상`·`## 엣지 케이스`) → 현행: "`## 요구사항` (조건/트리거/기대결과), `## 상태 전환`, `## 비즈니스 규칙`, `## 예외 케이스`, `## Open Questions` (4 카테고리)". 정본: `create-feature/SKILL.md:75-96`.
   - **B-4** `pr/SKILL.md:49`: "config.md 에 정의되어 있으면 그 값, 없으면 config.md" 자기순환 → "`.agent-state.yml` 의 `pr_base_branch` → `workspace/context/config.md` 의 `pr_default_base` → 하드 fallback `develop`". 정본: `lifecycle/state-schema.md:100-104` + pr frontmatter "state·config 순".
   - **B-5** `projects/GUIDE.md:208` 및 `prompts-scaffold-notes.md:56`: "`.claude/agents/pilot-planner.md`" → "`${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md`". 정정 후 `grep -rn "\.claude/agents" pilot/skills/` 0건 확인.
   - **B-6** `context/INDEX.md:137`: STATE.md 부재 시 "빈 테이블로 생성 후 계속 진행" → "messages.md 의 `workspace_missing` 안내 출력 후 종료" (스킬 8곳 실동작과 일치). preamble P1 정의부 보강은 #19 몫 — 여기선 INDEX 행만 정정.
   - **B-7** `code-review-init/SKILL.md:31`: 자체 문구 "워크스페이스 미초기화. `/pilot:init` 먼저 실행하세요." → messages.md `workspace_missing` 키 참조 (문구: "workspace/ 가 없습니다. 먼저 `/pilot:init` 으로 초기화하세요." — `shared/messages.md:18-22`). preamble 적용표 행 추가는 #19 몫.
   - **B-8** `tdd/SKILL.md:13`: "우선순위 규칙: [characterize/SKILL.md](../characterize/SKILL.md) 참조" → 정본 직결: "[`modes/characterize.md`](../context/modes/characterize.md) 참조" (characterize.md:10 이 정본).
   - **B-9** (critic C3, 사용자 재결정 — 정본 문구 중립화 후 전면 통일): 통일 문안은 **`[INFO] {외부 도메인} 의존성 감지 — 먼저 \`/pilot:learn {추천 경로}\` 권장`** — 주어 ("이 feature 는" / "features/ 의 일부") 를 제거해 단건 (create-feature) / 배치 (analyze 5-2) 양쪽 맥락에 중립. 적용 3곳: ① `shared/open-questions.md:54` (정본 자체를 이 문안으로 교체) ② `analyze/SKILL.md:167` ③ `analyze/references/scope-sync.md:107` (SKILL.md:167 의 위임처 — 누락 시 새 모순 발생). analyze 고유 "재분석 권장" 뉘앙스는 INFO literal 밖 주변 산문 (scope-sync 5-2 본문) 이 담당 — literal 3곳은 완전 동일 유지. 이 문구는 기계 파싱 대상 아님 (doctor·테스트 grep 무관 — 실측 확인).
   - **A-12** `context/INDEX.md:58-68` 프로젝트 폴더 트리를 정본 `projects/GUIDE.md:13-25` 와 정렬 (`.plan.md` 행 누락 보충). 3벌 중 setup/README.md 사본은 삭제로 해소, 완전 통합은 #19 몫.
   - **doctor stale** `doctor/SKILL.md:46` (라인 critic C6 정정): "CI 자동 실행 (`.github/workflows/validate.yml`)" → validate.yml 미존재 (`.github/workflows/` 에 docs.yml·tests.yml 뿐). 정정안: "CI 연동은 #20 에서 `validate.yml` 신설 예정 — 현재 수동 실행" 취지 1줄 (승인됨 2026-07-24).

3. **docs_build stale 정리 + 게이트 검증**
   - `docs_build.py`: 쓰기 경로 (`main()` 의 `write_files` 직후) 에 정리 함수 추가 — `docs/reference/{agents,skills,tools}/*.md` 중 이번 build 산출 집합에 없는 파일 삭제 + 삭제 건수 stderr 1줄. `reference/index.md` (커밋본)·`identity.md` 는 대상 밖 (3개 하위 디렉터리만 스캔). **빈 카테고리 가드 (critic C5)**: 해당 카테고리 build 산출 ≥ 1건일 때만 그 디렉터리를 정리 — `--root` 가 부분 트리 (fixture root 등) 일 때 기존 산출물 일괄 오삭제 방지. `--check` 경로는 불변.
   - **CI 안전 논거 (critic C4 정정)**: CI (`.github/workflows/docs.yml:50`) 는 write 경로를 실행하므로 정리 로직이 CI 실행 경로에 포함된다 — 무해한 실제 이유는 "CI 는 clean checkout 이라 stale 0건 → 정리 로직 no-op". `--check` 는 어느 워크플로에도 미등장.
   - `test_docs_build.py`: 기존 unittest 패턴 답습 — 4케이스: ① temp root 에 stale `.md` 심은 뒤 build+write 실행 → 제거 확인 ② 정상 산출물 비제거 확인 ③ 카테고리 `index.md` (build 산출 집합 포함) 비제거 확인 (critic C4) ④ 빈 카테고리 디렉터리 비정리 확인 (critic C5).
   - 게이트 실행 (spec 비즈니스 규칙 — 사이클 공통): ① `python3 -m pytest pilot/tests` 전체 통과 (fixture 삭제 feature 라 전체 실행이 spec 명시 게이트 — guardrails test_run 의 "관련 경로만" 예외) ② `python3 pilot/tools/doctor.py workspace` 클린 ③ `python3 pilot/tools/docs_build.py` 정상 + 로컬 stale `docs/reference/skills/fix-review.md` 제거 확인 (D-2 수용 증거) ④ `test_doc_links.py` 통과 = 깨진 링크 0.

### 주의사항

- **feature spec 드리프트 2건 — 승인 획득 후 정정 완료 (2026-07-24, drift-protocol § B)**:
  1. spec :13 "INDEX.md 삭제로 자동 해소" 파일 혼동 — 삭제 승인 파일은 `lifecycle/INDEX.md` (59줄) 이고 B-1·B-2·B-6·A-12 는 별개 파일 `skills/context/INDEX.md` (148줄, preamble P3 런타임 참조 — 삭제 불가). spec 문구를 "문구 정정으로 처리" 로 정정 완료, 본 계획 스텝 2 가 실행.
  2. spec :29 `verify-reports` 위치 오기 (실제는 sibling `tests/fixtures/verify-reports/`) — 정정 완료.
- 보존 픽스처 오삭제 = pytest 즉시 파손. 스텝 1 의 보존 목록·테스트 매핑을 삭제 전 재확인 (spec 예외 케이스 명시 사항).
- **`_input/` 보존 확정 (critic C1, 사용자 재결정 2026-07-24)**: 배포 튜토리얼 `pilot/docs/tutorial/getting-started.md:16` 이 `_input/python-sample` 을 복사해 walkthrough 진행 — 삭제 시 배포 문서 파손. 이관·튜토리얼 재작성은 하지 않는다 (#18 무동작변경 원칙). 초기 "유일 소비자 diff.sh" 판단은 오탐 (md 링크 검사·mkdocs strict 가 코드블록 안 셸 경로를 못 잡는 사각지대).
- `migration/` 픽스처는 #20 (마이그레이션 코드 삭제) 전까지 보존 (spec 예외 케이스).
- 문자열 기계 계약 (messages.md 키·CLI 시그니처·analyze 단계 번호 앵커·Detect literal) 불변 — 본 feature 는 문구 정정만. A-6 (tdd Detect literal 하드코드) 은 중복 통합이라 #19 몫, #18 에서 건드리지 않는다.
- `docs/audits/` 하위 문서는 감사 기록 원본 — 삭제 파일 언급이 있어도 수정하지 않는다.
- 커밋 분리 권장: (1) 삭제 + README 재작성, (2) 드리프트 정정 B-1~B-9, (3) docs_build 정리 로직 — 리뷰·revert 단위 확보.
- generator 는 `project.md` `## 목표` 체크박스 수정 금지 (evaluator 단독 권한 — #03 인수인계).

### 교차 의존

- feature #19 (정비 rewrite) — #18 이 확정한 삭제·정정 위에서 재작성 수행. #18 에서 의도적으로 이월한 것: A-1~A-16 중복 통합 전체, B-6 부수 (preamble P1 `workspace_missing` 케이스 보강), B-7 부수 (preamble 적용표 `code-review-init`·`review` 행 추가), A-12 완전 통합, A-6 Detect literal 참조화. `context/INDEX.md` 는 #19 재작성 대상이므로 #18 정정은 최소 문구만.
- feature #20 (정비 slim) — `v0.1.0-baseline/migration/` 픽스처 삭제 시점 = #20. `doctor/SKILL.md` 의 validate.yml 문구는 #20 의 `validate.yml` 신설 시 재갱신 (동일 커밋 권장). `_input/` 은 튜토리얼 더미 저장소용 보존 확정 (critic C1) — #19/#20 에서 삭제 후보로 재상정하려면 튜토리얼 이관이 선행 조건.
