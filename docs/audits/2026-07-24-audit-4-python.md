# 감사 축 4 — Python 도구 (원본 결과)

대상: `pilot/tools/` (16 파일, 7,109줄 — 테스트 제외). 모든 스크립트의 호출처를 파일명 전체·베이스네임·하이픈/언더스코어 변형으로 grep 검증. **완전 미사용 스크립트는 없다** — 단, verify-report-lint.py 의 검증 로직(validate)과 doctor 내부 다수 검사는 런타임 소비자가 사실상 모델뿐이라 이관 대상이다.

## A. 분류표

| 스크립트 | 줄수 | 호출처 | 분류 | 근거 | 예상 절감 | 위험도 |
|---|---|---|---|---|---|---|
| `doctor/integrity.py` | 2,160 | tools/doctor.py:159 ← skills/doctor:30, learn:164, project:149, tdd-activation:235 | **슬림화** (내부 ~50% 이관·삭제) | 상태 파일 검사·auto-fix 는 멱등 필수. 그러나 md 표 스키마 lint 5종 + 시효 만료 마이그레이션이 절반 이상 | **~1,100** | 중 (§B) |
| `confluence.py` | 865 | confl:53,86,111,152 · project:124 · analyze:73 | **유지** | 외부 API + 인증 + HTML→MD 결정적 변환 | 0 | — |
| `orchestrate-load.py` | 762 | 4 wrapper 에이전트 :18/:26 | **유지** (경미 슬림) | 컨텍스트 로드 SSOT. `parse_state_yml`·semver 가 _common.py 와 중복 (~50줄) | ~50 | 하 |
| `docs_build.py` | 420 | .github/workflows/docs.yml:50 · mkdocs.yml:43 | **유지** | CI 문서 빌드 — 결정적 산출물 필수 | 0 | — |
| `doctor/schema.py` | 410 | doctor.py:145 (`--schema`) ← skills/doctor:46 | **이관 후 삭제 (조건부)** | 플러그인 구조 lint. SKILL 이 주장하는 CI(`validate.yml`)는 **존재하지 않음 (stale)** — 실호출은 수동뿐. 대안: CI 재배선 후 유지 | 410 (+배선 ~20) | 중 (릴리즈 게이트 약화) |
| `verify-report-lint.py` | 372 | auto_pilot.py:85-107 (**파서 2함수만** 재사용) · 테스트 | **슬림화** (validate 이관) | 런타임에서 lint CLI 를 부르는 skill/agent/hook 없음. validate()+렌더+CLI (~250줄)는 테스트 전용 | ~250 | 하 |
| `doctor/_common.py` | 313 | doctor 패키지 전체 | **유지** | Result·파서·auto-fix 러너 공용부 | 0 | — |
| `plan-validate.py` | 282 | pilot-planner:49 · pilot-generator:33 · autopilot:81 | **유지** | 형식 lint 이나 autopilot 전이기계가 exit code 를 stop 신호로 소비 + generator 읽기 게이트(자기 인증 방지) | 0 | — |
| `init_detect.py` | 279 | skills/init:63 (함수 import) | **이관 후 삭제** | 확장자 빈도→언어, depth≤2 폴더→scope 제안값. 모델이 Glob/ls 로 동일 판단 가능, 실패해도 사용자 확인 단계가 흡수 | 279 | 하 |
| `slack-notify.py` | 271 | slack-notify.sh:28 · pr:99 · slack:93 · evaluator:69 · planner:57 | **유지** | 외부 webhook + secret 차단 + 훅 stdin 파싱 | 0 | — |
| `regen-verify.py` | 250 | analyze/references/regen-mode.md:47 | **유지** | *모델 실수를 잡는* diff 검증 — 이관 시 자기 인증 문제 | 0 | — |
| `auto_pilot.py` | 193 | autopilot:89,101,125 | **유지** | 자율 모드 전이 결정 — 결정성이 존재 이유 | 0 | — |
| `doctor/diagnose.py` | 181 | doctor.py:152 (`--diagnose`) ← skills/doctor:45 | **이관 후 삭제** | 휴리스틱 패턴 매칭 — 모델이 더 잘하는 판단 유형. 전용 테스트 없음 | 181 (+배선 ~15) | 하 |
| `memory-hint.py` | 176 | preamble.md:21 (P0) ← 5개 스킬 | **이관 후 삭제** | 키워드 점수 메모 선별 — 모델이 MEMORY 색인 직접 선별 가능. integrity.py:453 안내 문구 동기화 필요 | 176 | 하~중 (preamble 동시 수정) |
| `doctor.py` | 163 | skills/doctor:30 외 다수 | **슬림화** | dispatcher 필수. :36-112 backward-compat re-export 는 테스트 편의 전용 | ~60 | 하 |
| `doctor/__init__.py` | 12 | 패키지 필수 | **유지** | — | 0 | — |

비-Python: `pilot-update.sh`(66줄)·`release.sh`(112줄)는 범위 외이나 doctor 호출 없음 확인.

## B. integrity.py 상세 (2,160줄)

### 내부 구조

| 섹션 | 줄 범위 | 규모 | 성격 |
|---|---|---|---|
| credential drift (.env↔env SHA) | 41-74 | 34 | 보안 — **보존** |
| Slack secret (.gitignore 강제주입·tracked 검사) | 81-181 | 100 | 보안, 즉시 수정 부작용 — **보존** |
| auto-fix 팩토리 3종 (STATE 이력·schema v1→v1.2·legacy 섹션) | 187-313 | 127 | 상태 마이그레이션 — **보존** |
| `check_workspace` + auto-memory 안내 | 320-457 | 138 | 구조 존재 검사 — **보존** |
| `check_project` (schema·analyzed·tdd 3-way·domain·pr_base remote·plugin_version drift·mtime drift·중복 H2) | 460-815 | 356 | 상태↔실파일 정합성 — **보존** (verbose Result 로 다소 비대) |
| md 표 파서 `_parse_md_tables_in_section` | 822-873 | 52 | 공용 헬퍼 |
| `check_conventions_paths` | 876-935 | 60 | 파일 존재 검사 — **보존** |
| `check_workspace_config_sections` (learn/scope 표 헤더 lint) | 938-1171 | 234 | **이관 후보** |
| `check_workspace_external_domain_section` | 1174-1314 | 141 | **이관 후보** |
| `check_features_open_questions` (INFO 전용) | 1317-1372 | 56 | **이관 후보** |
| tx 화이트리스트 + `check_domain_transaction_contracts` | 1379-1589 | 211 | **이관 후보** |
| `migrate_v0_1_to_v0_2` + default 표 주입 + interactive 프롬프트 | 1600-1845 | 246 | **삭제 후보 (시효 만료)** |
| Onboarding Health OH-1~5 | 1848-2068 | 221 | **이관/축소 후보** |
| 진입점 `run_integrity_check` | 2071-2160 | 90 | **보존** |

### 비대 원인

1. **md 표 스키마 lint 가 ~640줄 (30%)** — 기계 파서가 실소비하는 표는 `## 도메인 분류`(orchestrate-load.py:278)·`## 외부 도메인 reference`(:320)뿐이며 그 파서들은 graceful degrade. 나머지 lint 의 소비자는 **모델 자신** — 모델은 헤더가 약간 달라도 표를 읽는다.
2. **시효 만료 마이그레이션 246줄** — 플러그인 v0.9.0 현재 v0.1→v0.2 마이그레이션은 실사용 종료.
3. **Onboarding Health 221줄** — 기존 검사와 사실상 중복 (OH-3↔STATE, OH-4↔MANIFEST), WARN/INFO 전용.
4. **verbose Result 생성** — 검사 1건당 8~15줄의 메시지 조립.

### 보존 필수

`check_workspace`·`check_project`(schema, analyzed↔features, tdd 3-way, mtime drift, semver 비교, `git ls-remote`), auto-fix 3종, credential/Slack secret 검사, `_parse_md_tables_in_section`(도메인 분류 표 검증이 남는 한), `run_integrity_check`. 파일시스템·git·시각 비교라 모델 대체 시 조용한 회귀 발생.

### 축소 시나리오

- 삭제: 마이그레이션 246줄 → **-246**
- 이관: config sections 234 + external domain 141 + open questions 56 + tx contracts 211 → **-642**
- 축소: Onboarding Health 221 → doctor SKILL 지시문 1문단 → **-221**
- 합계 약 **-1,100줄** (2,160 → ~1,060)

## C. 이관 항목 상세 (검증 → 대체 지시문 초안)

1. **`check_workspace_config_sections`** → init·learn SKILL 에: "config.md 표 생성·수정 시 헤더 리터럴 정확 유지: `| 언어 | 의존성 추출 패턴 |` · `| 역할 | 식별 패턴 |` · `| scope 헤더 | project.md 대상 H3 | 표 헤더 |`. scope 헤더 값은 `## ` 시작, H3 값은 영숫자·공백·하이픈만. 저장 직후 재확인."
2. **`check_workspace_external_domain_section`** → learn SKILL 에: "`## 외부 도메인 reference` 표는 3컬럼 헤더 유지, 도메인 learn 완료 시 해당 행 제거 (멱등). `## 도메인 분류` 에 있는 도메인을 여기 남기지 않는다." (orchestrate-load 파서 graceful 이므로 안전)
3. **`check_features_open_questions`** (INFO 전용) → "features 파일에는 `## Open Questions` 와 (a)~(d) 4개 H3 를 항상 포함한다" 한 줄로 고정.
4. **`check_domain_transaction_contracts`** → learn SKILL 에: "`### Cross-domain Transaction Contracts` 표는 4컬럼, 변경 type 은 read/write/destroy/create 의 `·` 조합만."
5. **verify-report-lint `validate()`** → evaluator REPORT 계약에 자기 점검 1줄 추가. 파서 2함수(~120줄)는 auto_pilot.py 로 흡수.
6. **`diagnose.py`** → doctor SKILL `--diagnose` 항목을 지시문 진단(loop/red-miss/repeat-not-ready/scope-violation + `## DIAGNOSIS` 블록)으로 교체.
7. **`memory-hint.py`** → preamble P0 을 "MEMORY.md 색인에서 직접 선별 Read" 로 교체. integrity.py:453 동기화.
8. **`init_detect.py`** → init SKILL step 1 을 Glob 기반 직접 판단 지시로 교체.
9. **`doctor/schema.py`** (조건부) → 릴리즈 절차 지시문 대체 — 단, **권장 대안은 stale 된 `validate.yml` 참조를 실제 CI 로 복원하고 유지**.

## D. 합계

**스크립트 절감 (tools/ 7,109줄 기준):**

| 분류 | 대상 | 절감 |
|---|---|---|
| 미사용 삭제 | 없음 | 0 |
| 시효 만료 삭제 | integrity.py 마이그레이션 | ~246 |
| 모델 이관 후 삭제 | diagnose(181) · memory-hint(176) · init_detect(279) · schema(410, 조건부) | 636~1,046 |
| 슬림화 | integrity lint·OH(~860) · verify-report-lint(~250) · doctor.py(~60) · orchestrate-load(~50) | ~1,220 |
| **합계** | | **~2,100 (schema 유지) ~ 2,500 (전부)** — 전체의 30~35% |

**테스트 절감 (tests/tools/ 4,767줄 기준):** test_doctor_migration(278) · test_doctor_integrity(136) · test_doctor_external_domain+cross_domain(232) · test_doctor_open_questions(107) · test_doctor_cross_domain_transaction(154) · test_verify_report_lint 부분(~140) · test_init_detect(192) · test_memory_hint(137) = **~1,376줄 (약 29%)** + fixtures (`v0.1.0-baseline/` 대부분, `verify-reports/` 일부).

**총 예상 절감: 약 3,500~3,900줄** (스크립트 ~2,100-2,500 + 테스트 ~1,380).

**주의 (오탐 방지):** 이관 대상 4개 스크립트는 모두 **살아있는 호출처가 있다** — 삭제는 호출 측 문서(preamble.md, init/doctor SKILL.md, integrity.py:453) 수정과 동일 커밋에서 수행할 것. plan-validate.py·regen-verify.py·auto_pilot.py 는 형식 검사처럼 보여도 각각 autopilot hard-stop 신호·모델 자기 인증 방지·전이 결정성이라는 구조적 역할이 있어 이관 부적합.
