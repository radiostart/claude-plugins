# Evaluator — build-plugin

구현 완료 후 요구사항 충족 여부와 일관성을 검토한다.

**역할:** **완성도 심사** — Generator 의 자체 sanity check 와 별개로, features 요구사항·비즈니스 규칙·예외 케이스 충족 여부를 최종 판정. 체크리스트 `[x]` 가 이 판정의 기록.

> **⚠️ 이 파일은 `@pilot-evaluator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-evaluator.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-evaluator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-evaluator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

---

<!-- [analyze-managed] -->
## 기능 완성도

- [x] #00 `pilot/tests/fixtures/v0.1.0-baseline/` 디렉터리 + 1 언어 `_input/` + `learn/project/analyze/expected/` + `config/{pass-empty,pass-valid,error-*}` + `diff.sh`. v0.1.0 캡처 시 diff 0. (0a + 0b 캡처 완료. `_input/python-sample/` 11 파일 + `learn/expected/` + `project/expected/projects/python-sample-demo/` + `analyze/expected/projects/python-sample-demo/` 일관. `python-sample` (도메인명) ↔ `python-sample-demo` (프로젝트명) 구분 적용. 회귀 자동 검증 자체 (`diff.sh --actual {regen}` 1 회 실행) 는 별도 항목 line 50·63 으로 분리 — runtime lookup 구현 후 1 회 수행)
- [x] #01 learn Phase 2 가 config.md `## learn 언어 패턴` 의 두 표를 lookup (long-form). D10 default 폐지 — SKILL.md 본문에 default 표 0. config 비면 폴더 인접성 fallback. 사용자 override 시 즉시 반영. backward-compat 은 #05 마이그레이션으로 위임.
- [x] #02 analyze 5-2 가 config.md `## scope 카테고리` 매핑을 lookup. config 비면 default (Routes/Models/Services) 사용. `/pilot:create-feature` 도 동일 lookup 자동 적용 (5-2 인용 호출).
- [x] #03 `/pilot:project` 가 신규 폴더 생성 시 1 회 H3 동적 생성. 재실행 시 기존 H3 보존. config 비면 default H3 (Models/Endpoints/Services) 생성 (기존 거동).
- [x] #04 doctor 가 신규 config 섹션 존재 시 스키마 검증 (컬럼 수·헤더 화이트리스트·`## ` prefix). D10 행 수 0 허용 (빈 표 → INFO 1 줄). 부재 시 INFO 1 줄, WARN 아님.
- [x] #05 doctor `--fix` 가 v0.1.0→v0.2.0 업그레이드 감지 시 사용자 확인 (a/b/c) 후 v0.1.0 default 표 자동 주입 또는 거부 기록. interactive 환경 only — non-interactive 자동 미루기.

---

<!-- [analyze-managed] -->
## 프로젝트 고유 항목

- [x] #01 다중 확장자·확장자 없음 케이스 v1 외 (`Makefile`·shebang) — fallback 폴더 인접성 적용 확인
- [x] #01 config 표 컬럼 수 불일치 시 doctor ERROR
- [x] #01 lookup 우선순위: config 행 → 폴더 인접성 fallback (D10 default 폐지로 SKILL.md default 부재). 동일 (언어, 역할) 키는 config 만 있음
- [x] #01 D10 적용 — SKILL.md (learn) Phase 2 본문에서 default 표 2 개 모두 제거. config.md 두 표 헤더만. fixture pass-valid 두 표 헤더만. 세 곳 동기화
- [x] #02 MANIFEST 진입 파일에 scope 헤더 없음 → 5-2 가 해당 표만 skip + INFO 1 줄. `analyzed:true` 정상 게이트
- [x] #02 scope 파일 자체 부재 → 동일 skip (기존 5-2 거동과 일관)
- [x] #02 config 빈 표 → SKILL.md default 사용 (= 부재와 동일 처리)
- [x] #03 H3 SSOT 분리 검증: H3 헤더 = `/pilot:project` 1 회 생성, 표 본문 = `/pilot:analyze` 또는 create-feature 매번 갱신
- [x] #03 사용자 수동 추가 H3 (config 외) = 양쪽 모두 보존
- [x] #03 사용자가 H3 삭제 → 재실행 시 복구 안 함 (사용자 의도)
- [x] #03 example/project.md `## 관련 파일` H2 부재 → H2 + H3 모두 새로 생성
- [x] #04 부적절 헤더 문자 (슬래시·콜론·#·|) 포함 시 ERROR + 행 위치·차단 문자 안내
- [x] #04 scope 헤더 컬럼 `## ` prefix 위반 시 ERROR
- [x] #04 행 수 0 허용 (D10) — 빈 표 → INFO 1 줄 ("폴더 인접성 fallback 동작"), ERROR 아님
- [x] #05 감지 조건: `.agent-state.yml.plugin_version` 0.1.x 또는 부재 + 현재 plugin v0.2.0+ + `## learn 언어 패턴` 두 표 모두 빈 행
- [x] #05 opt-in (a) → v0.1.0 default 5 언어 + 6 역할 표 자동 주입 + `migration_v0_2_0: accepted` + `plugin_version: 0.2.0`
- [x] #05 opt-out (b) → config 빈 채로 + `migration_v0_2_0: declined` + `plugin_version: 0.2.0`
- [x] #05 postpone (c) → 변경 없음, 다음 `--fix` 호출 시 다시 묻기
- [x] #05 non-interactive 환경 (stdin.isatty()=False) → 자동 미루기 + INFO 1 줄, hang 방지
- [x] #05 부분 정의 사용자 (어느 한 표 행 > 0) → skip + INFO ("부분 정의됨 — 사용자 직접 갱신 권장")
- [x] #05 신규 사용자 (`plugin_version: 0.2.0` 부터) → skip
- [x] #05 `--fix` 미호출 (기본 doctor) 시 마이그레이션 prompt 발생 안 함 (`run_auto_fixes` 가 `--fix` 모드에서만 호출)
- [ ] backward-compat 0 brittle: 회귀 골든 픽스처 `pilot/tests/fixtures/v0.1.0-baseline/` 로 config 비어있을 때 v0.1.0 = v1 동일 출력 검증 (0a + 0b 캡처 완료. 실제 회귀 실행 = `bash diff.sh --actual {regen}` 미실행. 디렉터리 명 정합 후 1 회 수행 필요)
- [x] #09 `/pilot:learn` Phase 2 외부 도메인 reference 추출 절차 명시 (내부 vs 외부 namespace 분류, ignore 패턴 12 항목 default, A2 runtime fallback). `/pilot:create-feature` 3-bis · `/pilot:analyze` 5-2 의 cross-domain detect (MANIFEST 외부 도메인 lookup → INFO 1 줄)
- [x] #10 MANIFEST.md `## 외부 도메인 reference (learn 미완료)` 섹션 자동 작성 (3 컬럼 표). 추정 도메인 알고리즘 1 순위 (`Module::Class` namespace 첫 segment 소문자화). 추천 경로 (`app/{models,services,controllers}/{도메인}/`). idempotency (현재 learn 시 자기 행 제거 + 도메인 분류 표 등록 시 INFO). doctor `check_workspace_external_domain_section` schema 검증 (3 컬럼 + 헤더 정확 일치 + stale row INFO). MANIFEST.md.template placeholder 주석 추가
- [x] #11 `/pilot:create-feature` 가 features/NN-*.md 작성 시 `## Open Questions` 4 카테고리 (a/b/c/d) 강제 + 빈 카테고리 `- (없음)` 표시. 3-bis cross-domain detect 결과를 (b)/(c) 로 자동 분류. `/pilot:analyze` 5-2 가 기존 Open Questions 섹션 보존 + 갱신. doctor `check_features_open_questions` schema 검증 (섹션 부재 INFO, H3 누락 INFO, ERROR 없음 — backward-compat). 4 픽스처 (pass-empty/pass-valid/info-missing-section/info-missing-h3) + 4 unit 테스트 PASS
- [x] #12 `/pilot:learn` Phase 3 transaction nesting Grep 패턴 추가 (`\.transaction\s*do\s*$|ActiveRecord::Base\.transaction|\w+Record\w*\.transaction` ±20 줄 Read). Phase 3 추출 항목에 cross-domain transaction nesting (외부 namespace 만, 본 도메인 nesting 제외 = Open Q d-4) + 변경 type 매핑 (`update→write`/`destroy→destroy`/`find→read`/`create→create`). Phase 4 step 2 신규 — `### Cross-domain Transaction Contracts` sub-section (4 컬럼 표) 자동 작성. inline vs 분리 룰 (5 행 임계 = Open Q d-3). `(auto)` 마커 + idempotency. A2 runtime fallback (detect 실패 시 placeholder 행, abort 안 함). doctor `check_domain_transaction_contracts` schema 검증 (4 컬럼 + 헤더 정확 + 변경 type 화이트리스트). 7 픽스처 + 7 unit 테스트 PASS. backward-compat — 섹션 부재 시 INFO 만
- [x] #13 `/pilot:init` 1.5 단계 wizard 신설 (`config.md created` 조건 + `--no-wizard` 자연어 분기). `pilot/tools/init_detect.py` (Python 표준 라이브러리만, 의존성 0) — `detect_languages` (상위 3 확장자 → features/01 5 default 언어 매핑) · `detect_scope_candidates` (depth ≤ 2 폴더 빈도 ≥ 1, Q1 적용) · `IGNORE_BASELINE` 10 패턴. SKILL.md 본문 3 군데 갱신 (`### 2. wizard 적용`, `## 결과 출력` 3 줄, `## 참고` `--no-wizard` 단락). 회귀 fixture `wizard/expected/config.md` 캡처 + `diff.sh EXPECTED_SUBDIRS` 4 번째 항목 추가. 단위 테스트 8/8 PASS. spec line 24 Q1 patch (≥ 2 → ≥ 1) 적용
- [x] #14 `pilot/docs/getting-started.md` 신설 (324 줄, 250~350 범위) + `pilot/README.md` line 9 callout 1 줄 추가. 5 step (init→learn→project→create-feature→planner) + 사전 준비 + troubleshooting 5건 (case 2 = `wizard 잘못 매핑 정정 경로`, Q7 교체) + timing 측정 가이드. 더미 저장소 `${CLAUDE_PLUGIN_ROOT}/tests/fixtures/v0.1.0-baseline/_input/python-sample` 을 `/tmp/pilot-tutorial/` 로 복사 후 진행. 모든 출력 캡처는 핵심 3~5 줄 + `... (생략)` 처리 (Q3). 한국어 본문 (Q5). Q1~Q7 모두 반영. plan-validate exit 0. SKILL.md 명령 형식 정합 (`/pilot:init`·`/pilot:learn <path>`·`/pilot:project {name}`·`/pilot:create-feature {prompt}`·`@pilot-planner`). 인수인계 line 122·123·124 (#13 후속) 모두 가이드 본문에 반영
- [x] #15 `/pilot:tdd` 4 분기 (on/off/--fix/상태 보고) 재구성. `pilot/skills/tdd/SKILL.md` 본문 4 절 + 각 사용자 출력 형식 명시. `pilot/skills/context/modes/tdd-activation.md` §1-1b (백업 마커 주입) + `## 비활성화 절차` off-1~off-7 + literal 매칭 정확 문자열 (§1-1b·off-2·off-3) 추가. `pilot/tools/doctor/integrity.py:549-573` 의 `check_project` `tdd 정합성` 블록 2-way → 3-way 확장 (state ↔ project.md ↔ prompts/*.md 백업 마커 기준). 함수 시그니처 `check_project(workspace, project)` 보존, 호출자 영향 0. 회귀 fixture `tdd-on/expected/` + `tdd-off/expected/` 신설 (5 파일씩 — state.yml + project.md + prompts/{planner,generator,evaluator}.md). diff.sh `EXPECTED_SUBDIRS` 에 2 행 추가, 6 서브디렉터리 [OK]. spec drift T1 (line 7) + T2 (line 64-65) Q9 patch 적용. `pilot/docs/getting-started.md` line 200·202 broken link 정정 Q10 (인수인계 line 126 소비). `pilot/skills/project/SKILL.md` patch 없음 (Q6). plugin.json version bump 없음 (Q8). `.plan.md` 손대지 않음 (Q5)
- [x] #16 Doctor onboarding-health (OH-1~5 5룰) — 구조: OH-1 (config 3섹션 행 수 ≥ 1) · OH-2 (scope/ *.md ≥ 1) · OH-3 (STATE.md 진행중/대기 ≥ 1) · OH-4 (MANIFEST 도메인 분류 행 ≥ 1) · OH-5 (features/ *.md ≥ 1, project 인자 시만). `check_onboarding_health(workspace, project=None)` dispatcher + 5 `_check_ohN_*` 함수 (integrity.py). doctor.py re-export 추가. SKILL.md 본문 1 단락 + Q5 drift 정정 (line 77·99 → 3-way wording, line 77 본문 + line 126 [PASS] 예시). fixture 2 케이스 (`doctor-onboarding/expected/pass-only/` + `warn-mixed/`). diff.sh `EXPECTED_SUBDIRS` 2 행 추가. `--fix` skip + INFO 1줄. early return 분기 (integrity.py:2025-2043) 에 OH-1~4 호출 + OH-5 N/A + WARN ≥ 4 시 안내 1줄 + `--fix` skip 추가. warn-mixed expected output 재캡처 (Project 섹션 0 · OH 섹션 8 줄). config.md `## scope 카테고리` 표 3 컬럼 정정. plan line 161 정합 주석. 실 doctor 호출 3건 (pass-only --project · warn-mixed · --fix) 모두 expected 와 byte-clean MATCH
- [x] #06 learn SKILL.md Phase 1 자동 도출 규칙 list (line 82-84) 에 3 sub-bullet 추가 — 일반 진입점 부모 폴더명 fallback (부모→2단계 상위→사용자 질의, A2 패턴 abort 없음) + 도메인명 sanitize (영숫자·하이픈 외 제거 + 소문자화) + 절대경로 정규화 (정규화 실패 시 사용자 질의). Phase 5 step 2 (line 304-306) `## 도메인 분류` 형태 detect 표 직후 blockquote 2 단락 추가 — H2 헤더 정확 매칭 강제 (정규식 `^##\s+도메인\s*분류\s*$` 인용 + 본문 prose 동일 string 등장 무시) + 코드블록 펜스 (` ``` `) 안 줄 무시 (`_parse_md_tables_in_section` 코드블록 추적 보강 정합 — integrity.py:807·811-820). 변경 파일 1개·7 라인 추가만. 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화). getting-started.md drift 점검 결과 영향 0 (Phase 1·5 출력 코드블록에 본 wording 미등장)
- [x] #07 analyze SKILL.md 5-1 ↔ 5-2 사이에 신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성` 삽입 (analyze SKILL.md:208-240, 34 라인 추가). 트리거 조건 (scope 부재 + MANIFEST H2 헤더 존재) + 본문 구성 (H2/표 헤더 = config `scope 헤더`/`표 헤더` 컬럼 그대로) + 본문 추출 우선순위 3단 (inventory.md → index.md → 빈 표 + INFO) + idempotency (기존 파일 보존 + 사용자 수동 행 보존) + A2 runtime fallback (abort 없이 빈 표 + INFO + 5-2 진행) + 예외 4건 (MANIFEST 부재 / config 빈 표 → features/02 default / inventory.md 부재 → 2·3순위 / scope 헤더 prefix 위반 → doctor 사전 차단). wizard 인용 주입 SSOT blockquote (analyze SKILL.md:226) 로 인수인계 line 123 (#13 후속) 직접 소비. 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화)
- [x] #08 project SKILL.md line 63 직후 nested blockquote 1 단락 추가 (project SKILL.md:65-80, 18 라인). 5 요소 모두 반영 — H1 정확 매칭 정규식 (`^#\s+.*\{프로젝트명\}.*$` 단순화 채택, Q3) · 보존 대상 3 (가이드 주석 self-reference · 코드블록 · 표 본문 셀) · 사용자 프로젝트명 sanitize (`[a-zA-Z0-9가-힣\-_]` 외 차단 + 사용자 질의 prompt) · A2 runtime fallback (H1 토큰 부재 → 치환 skip + INFO 1 줄 + abort 안 함, 인수인계 line 31 #04 소비) · 대상 파일 4 종 (`project.md` 1 + `prompts/{planner,generator,evaluator}.md` 3). example template 본문 변경 없음 (backtick wrap 이미 완료, 인수인계 line 101 #03 소비). 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화). list item 안 nested blockquote 들여쓰기 정합 (2 spaces) — H3 동적 채움 blockquote (line 88~) 와 같은 list item 안 공존

---

## 일관성

- [x] 언어 컨벤션 준수 ([`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) 참조)
- [x] 기존 코드 패턴과 조화 (불필요한 리팩토링 없음)

---

## 테스트

- [ ] 회귀 픽스처 자동 검증 (`pilot/tests/fixtures/v0.1.0-baseline/`) — config 비어있을 때 v1 출력 = v0.1.0 출력 (0b `_input/`+`expected/` 캡처 완료. 실제 `diff.sh --actual {regen}` 실행 미수행 — 디렉터리 명 정합 후 1 회 수행 필요)
- [ ] config 신규 섹션 정의 시 override 거동 (사용자 행이 default 위에 우선 적용) 검증 (#01·#02·#03 의 runtime lookup 미구현)
- [x] `pilot/tests/tools/test_doctor_integrity.py` (#04) — 7/7 PASS (test_pass_empty_table 신규 포함)
- [x] `pilot/tests/tools/test_doctor_migration.py` (#05) — 7/7 PASS (opt-in/out/postpone, 신규/부분/non-interactive/v010 detect)
- [x] `pilot/tests/tools/test_doctor_external_domain.py` (#10) — 5/5 PASS (pass-empty/pass-valid/error-column-mismatch/error-header-mismatch/info-stale-row)
- [x] `pilot/tests/tools/test_doctor_cross_domain.py` (#09) — 2/2 PASS (info-stale-row-bidirectional / no-error-on-valid-manifest)
- [x] `pilot/tests/tools/test_doctor_open_questions.py` (#11) — 4/4 PASS (pass-empty/pass-valid/info-missing-section/info-missing-h3)
- [x] `pilot/tests/tools/test_doctor_cross_domain_transaction.py` (#12) — 7/7 PASS (pass-no-subsection/pass-inline/pass-separated/pass-empty/error-column-mismatch/error-header-mismatch/error-bad-type)
- [x] 해피패스 커버 (pass-empty + pass-valid + 빈 표)
- [x] 에러 케이스 처리 (#04 doctor 검증 ERROR 케이스)
- [x] 기존 테스트 영향 없음 (doctor --schema 5 PASS·1 WARN·0 ERROR 유지, doctor workspace 9 PASS·1 WARN·0 ERROR)

> **비 TDD 프로젝트**는 자동 테스트 실행 단계가 없다. "읽기만 하고 끝" 을 피하려면 아래 수동 확인 중 적합한 것을 선택:
>
> - dev server / console 에서 기능 직접 실행 (UI / API 응답 육안 확인)
> - 대표 시나리오를 수기 테스트 케이스로 `## 테스트` 에 체크 항목으로 추가
> - 변경 주변 기존 테스트가 있으면 `{test_command} {경로}` 로 회귀 확인

---

## 전달사항 작성 가이드

래퍼가 검토 완료 후 요구하는 `## 에이전트 간 전달사항` (project.md) 기록 기준.

**전달할 것:**

- 신규 메서드·서비스·상수 추가 — 다음 feature 에서 재사용 가능성
- 모델 스키마·상태값 변경 — 후속 feature 의 가정 조건이 바뀜
- 제약·엣지 케이스 발견 — 다음 계획에 선행 반영 필요
- 공통 패턴 정립 (예: 특정 factory 콜백 우회 기법) — 다른 spec 재사용

**전달하지 않을 것:**

- 구현 디테일 (코드에 이미 있음 — 읽으면 됨)
- 완료된 체크리스트 항목 (이 파일에 `[x]` 로 반영됨)
- 일반적 언어·프레임워크 관행 (팀 `conventions_doc` 에 이미 있음)

**형식:**

```markdown
- [ ] {내용 1줄 + 후속 feature 에서의 반영 방향} (from #{완료 feature 번호})
```

**예:**

- [ ] `OrderService.reset_for_test` 추가됨 → #12 시점에 제거 판단 필요 (from #11)
- [ ] `order_status` 에 `pending` 값 추가 → #13 관리자 화면에서 필터 추가 필요 (from #11)

전달할 사항이 없으면 `## 에이전트 간 전달사항` 섹션을 건드리지 않는다 (빈 항목 추가 금지).
