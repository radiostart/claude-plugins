# #16 Doctor — onboarding-health 점검 — Implementation Plan

> source: features/16-doctor-onboarding-health.md · 직전 plan 협상 (옵션 C — plan 만 저장)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (Q1~Q9)

사용자가 모든 권고를 채택 (a 옵션 9건).

| Q | 결정 | 근거 |
| --- | --- | --- |
| Q1 OH 섹션 위치 | 기존 "구조 정합성" 섹션 아래 H4 + 구분선. `── Onboarding Health ─────────────────` 형식 (spec line 33 그대로). | a 채택 |
| Q2 WARN 색상·prefix | yellow `WARN` prefix + `OH-N` label. `Result.WARN` 재사용 (인수인계 line 87 `Result.INFO` 동일 패턴). | a 채택 |
| Q3 OH-5 조건 | 프로젝트 인자 지정 시만. workspace 단독 호출 시 OH-5 = `N/A` 표시 (spec line 19, 38, 50 그대로). | a 채택 |
| Q4 WARN 5건 안내 | 상단 1 줄 `신규 워크스페이스 감지 — getting-started.md 권장` + features/14 가이드 링크 (spec line 45 그대로). | a 채택 |
| Q5 SKILL.md drift 정정 | `pilot/skills/doctor/SKILL.md:77·99` 의 `tdd` 2-way wording → 3-way 로 정정 (인수인계 line 132 #15 후속). 본 plan 변경 파일 목록에 포함. | a 채택 |
| Q6 회귀 fixture | `pilot/tests/fixtures/v0.1.0-baseline/doctor-onboarding/expected/` 에 `pass-only/` + `warn-mixed/` 2 케이스 신설. `diff.sh EXPECTED_SUBDIRS` 에 2 행 추가. | a 채택 |
| Q7 `--no-onboarding-health` | v0.3.0 미포함. v0.4.0 검토. | a 채택 |
| Q8 `--fix` 미지원 | `--fix` 호출 시 OH 섹션만 skip + INFO 1 줄 (spec line 37 그대로). | a 채택 |
| Q9 version bump | 본 PR patch bump 안 함. v0.3.0 합본 PR 끝 일괄. | a 채택 |

## 인수인계 항목 소비 매핑 (project.md 미처리 항목)

| line | 항목 | 본 plan 활용 |
| --- | --- | --- |
| 87 | `Result.INFO` 레벨 (#04) | OH 처방 줄 INFO 활용 (WARN 과 색상 구분). step 1·4. |
| 88 | `_parse_md_tables_in_section` 헬퍼 (#04) | OH-1 (3 섹션 표 행 수) · OH-4 (도메인 분류 표 행 수) lookup 재사용. step 2. |
| 110 | sub-string 매칭 패턴 (#10 `(learn 미완료)`) | OH-1 의 `## learn 언어 패턴`·`## scope 카테고리`·`## Ignore` 헤더 매칭 동일 패턴. step 2. |
| 115 | features 디렉터리 순회 패턴 (#11 `check_features_open_questions`) | OH-5 동일 features 디렉터리 순회. step 2 (`_check_oh5_features_entry`). |
| 129 | `check_project(workspace: Path, project: str)` 시그니처 (#15) | OH-5 는 `check_project` 안에서 호출. OH-1~4 는 `check_workspace` 안. step 3. |
| 132 | #15 SKILL.md 미수정 (#16 일괄) | Q5 로 정확 소비. evaluator wrapper step 2 가 본 plan 의 SKILL.md edit 후 `[x]` 처리. |

## 범위

### 포함

- OH-1 ~ OH-5 5 룰 신설 (개별 `_check_oh{N}_*` 함수 + dispatcher `check_onboarding_health`)
- WARN 출력 분리 (yellow + `OH-N` prefix + 처방 1~2 줄)
- SKILL.md drift 정정 (Q5 — line 77·99 의 `tdd` 2-way wording → 3-way)
- 회귀 fixture 2 케이스 (Q6 — `pass-only/` + `warn-mixed/`)
- `--fix` skip 처리 (Q8 — OH 섹션만 skip + INFO 1 줄)
- WARN 5건 동시 시 onboarding 가이드 링크 1 줄 (Q4)

### 제외 (v0.4.0 이월 또는 본 plan 의도 외)

- `--no-onboarding-health` 플래그 (Q7)
- `--fix` 의 OH auto-resolve (사용자 의도 필요 — spec line 37·43)
- STATE.md 자동 감지 OH-5 (Q3 — workspace 단독 시 N/A)
- 다른 doctor 룰 신규 추가 (구조 정합성 검사는 그대로)

## 변경 파일

### 신설

- [x] `pilot/tests/fixtures/v0.1.0-baseline/doctor-onboarding/expected/pass-only/` — PASS-only 5건 fixture (config 채움 + scope/ 채움 + STATE.md 진행중 1건 + MANIFEST 도메인 1행 + features 1건)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/doctor-onboarding/expected/warn-mixed/` — WARN 5건 동시 fixture (config 빈 표 + scope/ 빈 + STATE.md 진행중 0 + MANIFEST 도메인 0행 + features 0건)

### 수정

- [x] `pilot/tools/doctor/integrity.py` — `check_onboarding_health(workspace: Path, project: str | None) -> list[Result]` dispatcher + OH-1~5 5 함수 신설
- [x] `pilot/tools/doctor/_common.py` — WARN yellow + `OH-N` prefix 포맷터 보강 (이미 `Result.WARN` 존재 시 라벨만 신설)
- [x] `pilot/tools/doctor.py` (CLI entry) — onboarding-health 섹션 호출 위치 (기존 "구조 정합성" 출력 직후) + `--fix` 분기 skip + INFO 1 줄
- [x] `pilot/skills/doctor/SKILL.md` — (a) "Onboarding Health" 1 단락 추가 (b) line 77·99 의 `tdd` 2-way → 3-way drift 정정 (Q5)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` — `EXPECTED_SUBDIRS` 에 `doctor-onboarding/expected/pass-only`·`doctor-onboarding/expected/warn-mixed` 2 행 추가

## OH-1 ~ OH-5 판정 알고리즘 (Generator 가 직접 구현)

> 모든 OH 룰은 **WARN 만 발화** (exit code 영향 없음). 부재·검출 실패 시 abort 없이 진행. 출력은 항상 5 행 (OH-5 는 workspace 단독 시 `N/A`).

### OH-1 · config.md 핵심 섹션 채워짐

- 대상: `workspace/context/config.md`
- 헬퍼: `_parse_md_tables_in_section(text, section_header)` (인수인계 line 88 · integrity.py:785 기존 헬퍼 재사용 — 코드블록 펜스 추적 보강은 #10 PR-1 에서 완료, integrity.py:807·811-820)
- 3 섹션 표 본문 행 수 ≥ 1 검증:
  - `## learn 언어 패턴` (sub-string 매칭 허용 — 인수인계 line 110 패턴 답습)
  - `## scope 카테고리`
  - `## Ignore`
- 표 0 행 발견 → WARN + 처방 1 줄: `[OH-1 WARN] config.md '{섹션명}' 미채움 — /pilot:init --rewizard (v2 옵션) 또는 수동 편집` (현재는 `--rewizard` v2 미구현 → "수동 편집 안내" 로 폴백)
- 3 섹션 모두 채움 → PASS

### OH-2 · scope/ 디렉터리 채워짐

- 대상: `workspace/context/scope/`
- 검증:
  - 디렉터리 존재 확인 (`Path.is_dir()`)
  - 하위 `*.md` 파일 ≥ 1 (`list(scope_dir.glob("*.md"))` 길이)
- 부재 또는 0 건 → WARN + 처방: `[OH-2 WARN] scope/ 미채움 — /pilot:learn <진입파일> 호출 권장 (analyze 가 scope 파일 생성)` (#13 wizard 자동 채움 안내는 본 PR 미포함 — features/07 후속)

### OH-3 · 첫 project 등록

- 대상: `workspace/STATE.md`
- 검증: 표 본문에 `진행중` 또는 `대기` 상태 행 수 ≥ 1
  - STATE.md 표 파싱: 정확 헤더 (`| 프로젝트 | 상태 | 마지막 활동 |`) 매칭 + 상태 컬럼 값이 `진행중` 또는 `대기` 인 행 카운트
- 0 → WARN + 처방: `[OH-3 WARN] 등록 프로젝트 없음 — /pilot:project {이름} 호출 권장`
- STATE.md 자체 부재 시 → 구조 정합성 ERROR 가 사전 차단 (OH-3 진입 안 함, 예외 케이스 spec line 49)

### OH-4 · MANIFEST 진입파일 존재

- 대상: `workspace/context/MANIFEST.md`
- 헬퍼: `_parse_md_tables_in_section` 동일 (OH-1 과 공유)
- 검증: `## 도메인 분류` 표 본문 행 수 ≥ 1
  - 표 헤더 정확 매칭: `| 도메인 | 진입 파일 | 설명 |`
  - 본문 행이 placeholder (`|  |  |  |`) 이면 0 으로 카운트
- 0 → WARN + 처방: `[OH-4 WARN] MANIFEST 도메인 미등록 — /pilot:learn <진입파일> 호출 권장`

### OH-5 · features/ 진입 가능 상태 (프로젝트 인자 시만)

- 대상: `workspace/projects/{project}/features/`
- 조건: `project` 인자 지정 시만 실행. `project is None` → 출력 `N/A` 표시 + INFO 1 줄 (`프로젝트 지정 시 features/ 진입 가능성 검사`)
- 검증: 디렉터리 존재 + `*.md` 파일 (`.plan.md` 포함, hidden `.` 제외) ≥ 1
  - 인수인계 line 115 의 features 순회 패턴 (`#11` `check_features_open_questions` 의 `Path.glob`) 답습
- 0 → WARN + 처방: `[OH-5 WARN] features/ 비어있음 — @pilot-planner 또는 /pilot:create-feature 호출 권장`

## 출력 형식 (spec line 32-39 그대로 인용)

```
── Onboarding Health ─────────────────
OH-1  config 핵심 섹션:        {PASS|WARN}
OH-2  scope/ 채움:              {PASS|WARN}
OH-3  첫 project 등록:          {PASS|WARN}
OH-4  MANIFEST 진입파일:        {PASS|WARN}
OH-5  features/ 진입 가능:      {PASS|WARN|N/A}   ← 프로젝트 인자 시만

{WARN 항목이 있으면 처방 1~2 줄씩 추가 출력}
```

WARN 5건 동시 시 (spec line 45):

```
── Onboarding Health ─────────────────
신규 워크스페이스 감지 — getting-started.md 권장 (pilot/docs/getting-started.md)
OH-1  ...
...
```

`--fix` 호출 시 (spec line 37, Q8):

```
── Onboarding Health ─────────────────
[INFO] --fix 모드 — onboarding-health 섹션 skip (사용자 의도 필요)
```

## SKILL.md Q5 정정 patch (정확 wording)

### before (현재)

- line 77: `- \`tdd\` 필드 ↔ \`project.md\` 의 \`**TDD 모드**\` 문자열 일치`
- line 99: `  [PASS] MyProject tdd: tdd=false, 일치`

### after (3-way 정정)

- line 77: `- \`tdd\` 필드 ↔ \`project.md\` 의 \`**TDD 모드**\` 문자열 ↔ \`prompts/{flow,planner,generator,evaluator}.md\` 의 백업 마커 3-way 일치 (인수인계 line 130 패턴)`
- line 99: `  [PASS] MyProject tdd: state=false ↔ project=false ↔ prompts 마커 부재, 3-way 일치`

> 정확 line 번호는 step 5 진입 시 grep 으로 재확인 (다른 변경으로 line 이동 가능성). 텍스트 자체는 unique 하므로 Edit replace 안전.

## 단계별 구현 순서

1. **`_common.py` 포맷터 보강** — `Result.WARN` 이 yellow 출력 + `OH-N` prefix 라벨 지원. `Result.INFO` (인수인계 line 87) 와 색상 구분. 기존 함수 시그니처 보존.
   > 검증 결과 `_common.py` 의 `Result.WARN` 이 이미 yellow 색상 적용 — 별도 보강 불요. OH-N prefix 는 `r.label` 필드에 직접 포함하는 방식으로 구현 완료.
2. **`integrity.py` 의 OH-1~5 5 함수 신설** — `_check_oh1_config_sections(workspace) -> list[Result]` ~ `_check_oh5_features_entry(workspace, project) -> list[Result]` 5 함수. 헬퍼 재사용 (line 88 `_parse_md_tables_in_section`).
3. **`check_onboarding_health(workspace, project=None) -> list[Result]` dispatcher 신설** — OH-1~4 항상 호출, OH-5 는 `project is not None` 시만 호출 (workspace 단독 시 `N/A` Result 1 줄). `check_workspace` 호출자에서 OH-1~4, `check_project` 호출자에서 OH-5 추가 호출 (시그니처 인수인계 line 129).
4. **CLI entry (`doctor.py`) 호출 위치 결정** — 기존 "구조 정합성" 출력 직후 (Q1, spec line 32-39). `--fix` 분기 시 OH 섹션 skip + INFO 1 줄 (Q8). WARN 5건 동시 발생 시 상단에 onboarding 가이드 링크 1 줄 (Q4 — `pilot/docs/getting-started.md` 상대 경로 인용).
5. **SKILL.md drift 정정 (Q5)** — line 77·99 의 wording 위 patch 그대로 적용. step 5 진입 시 `grep -n 'TDD 모드' pilot/skills/doctor/SKILL.md` 와 `grep -n 'tdd=false, 일치'` 로 정확 line 재확인 후 Edit.
6. **SKILL.md 본문 "Onboarding Health" 안내 1 단락 추가** — "동작" 섹션 또는 "검사 범위" 직후 (line 81 의 `스키마 상세:` 뒤). 내용: (a) 출력 형식 (b) `--fix` skip (c) 신규 워크스페이스 시 가이드 링크 (d) WARN 은 exit 영향 없음 (e) OH-5 = `N/A` 의미.
7. **fixture 캡처 — `pass-only/`** — `workspace/context/config.md` (3 섹션 각 1+ 행 채움) + `workspace/context/scope/sample.md` (1 파일) + `workspace/STATE.md` (진행중 1건) + `workspace/context/MANIFEST.md` (도메인 분류 1행) + `workspace/projects/sample-project/features/01-foo.md` (1건) + `expected/pass-only/doctor-output.txt` (PASS 5건 + 처방 0줄). 기존 fixture `pass-valid` 패턴 답습.
8. **fixture 캡처 — `warn-mixed/`** — 위 5 항목 모두 비움 (config 표 빈 헤더만 + scope/ 빈 + STATE.md 진행중 0 + MANIFEST 도메인 0행 + features 0건). `expected/warn-mixed/doctor-output.txt` (WARN 5건 + 처방 5줄 + 상단 가이드 안내 1 줄).
9. **`diff.sh` `EXPECTED_SUBDIRS` 확장** — 2 행 추가:
   ```bash
   EXPECTED_SUBDIRS=(
     # ... 기존 ...
     "doctor-onboarding/expected/pass-only"
     "doctor-onboarding/expected/warn-mixed"
   )
   ```
10. **회귀 검증** — `pilot/tests/fixtures/v0.1.0-baseline/diff.sh --actual {regen}` 실행 exit 0 확인. 두 fixture 양쪽 출력 매칭.

## 검증 방법

- OH-1~5 5 룰 모두 단위 동작 확인 (PASS / WARN 양쪽 fixture)
- `--fix` 호출 시 OH 섹션 skip + INFO 1 줄 출력 확인 (Q8)
- WARN 5건 동시 발생 시 onboarding 가이드 링크 1 줄 출력 확인 (Q4)
- 기존 구조 정합성 출력은 그대로 보존 (출력 길이 +5~20 라인 범위)
- fixture `diff.sh` exit 0 (doctor-onboarding/expected 2 케이스 양쪽)
- SKILL.md line 77·99 3-way wording 적용 (drift 0 — Q5 검증)
- `Result.WARN` 출력이 exit code 영향 없음 (기존 `summarize()` PASS/WARN/ERROR 카운트 정책 보존, WARN 은 exit 0)

## 주의사항

- **`Result.WARN` exit code 영향 없음** — 기존 `summarize()` 의 카운트 정책 보존 (WARN 은 exit 0, ERROR 만 exit 1). 본 PR 이 정책 변경 안 함.
- **OH-5 의 `N/A` 표시** — workspace 단독 호출 시 출력 (Q3). 색상은 기존 doctor `Result.INFO` 와 동일.
- **WARN 5건 시 안내 링크** — features/14 의 `pilot/docs/getting-started.md` 상대 경로 인용. 절대 경로 또는 사용자 workspace 경로 사용 금지 (#14 spec line 25 정책).
- **SKILL.md line 77·99 정확 위치는 step 5 진입 시 grep 으로 재확인** — 다른 변경 (#15 머지 후) 으로 line 이동 가능성. 텍스트 unique 이므로 Edit replace 안전.
- **`_parse_md_tables_in_section` 헬퍼 코드블록 펜스 추적은 #10 PR-1 에서 완료** (integrity.py:807·811-820, 인수인계 line 109). OH-1·OH-4 가 그대로 재사용 — 별도 보강 불요.
- **체크박스 갱신 권한** — 본 plan 의 generator 가 `project.md` 의 `## 목표` 체크박스를 self-mark 하지 않는다 (#03 인수인계 line 99 위반 회피). evaluator wrapper step 5 가 단독 권한자.
- **fixture STATE.md 표 헤더** — 현재 build-plugin workspace 의 STATE.md 헤더 형식과 정합 확인. 표 헤더 자체가 v0.2.x → v0.3.0 사이에 변경된 적 없는지 step 7 진입 시 1 회 확인 필요.
- **OH-3 `대기` 상태 처리** — spec line 23 은 `진행중 또는 대기` 둘 다 카운트. STATE.md 의 상태 컬럼 값이 정확 한국어 `진행중` / `대기` 인지 또는 `in-progress` / `waiting` 영어인지는 step 7 fixture 확인 시 정합 검증.

## 교차 의존

- **features/00 (회귀 픽스처)** — fixture 입력 트리 `_input/python-sample/` 와는 별도. `doctor-onboarding/expected/` 는 doctor 직접 호출 fixture 라 `_input/` 의존 없음.
- **features/13 (init wizard)** — OH-1 처방 `/pilot:init --rewizard` 는 v2 옵션 미구현. 현재는 "수동 편집 안내" 로 폴백. #13 후속 PR 에서 `--rewizard` 도입 시 처방 wording 갱신.
- **features/14 (onboarding guide)** — WARN 5건 시 안내 링크 대상 (`pilot/docs/getting-started.md`). #14 머지 완료 상태라 본 PR 에서 링크 인용 안전.
- **features/15 (tdd toggle)** — Q5 의 SKILL.md drift 정정이 #15 후속 처리 (인수인계 line 132). #15 머지 후 본 PR 이 정정 — 순서 정합.
- **인수인계 line 87·88·110·115·129·132** — 본 plan step 1~5 에서 6 건 모두 소비. evaluator wrapper step 2 가 `project.md` 의 6 행 `[x]` 처리.
