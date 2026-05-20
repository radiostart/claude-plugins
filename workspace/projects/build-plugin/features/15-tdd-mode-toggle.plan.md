# #15 TDD 모드 사후 토글 — `/pilot:tdd on|off` 양방향 전환

> source: features/15-tdd-mode-toggle.md · 직전 plan 협상 (옵션 C — plan 만 저장, 본 turn 추가 협상 없이 plan 저장까지)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (Q1~Q10 — 사용자 확정)

**Q1 — literal 매칭 (a 채택)**: spec line 64 그대로 literal 매칭 + WARN + 사용자 수동 안내. fuzzy 매칭은 v2 이외.

**Q2 — 백업 코멘트 marker 형식 (b 채택)**: `<!-- pilot-tdd-original-flow:start -->` … `<!-- pilot-tdd-original-flow:end -->` 마커 쌍으로 **기존 표준 흐름 본문을 감싸기** (인라인 백업). 복원 시 코멘트 안의 본문 그대로 사용. template 가 아니라 인라인 백업 — 사용자가 표준 흐름을 수정했다면 그 상태 보존.

**Q3 — doctor 룰 위치 (a 채택)**: `pilot/tools/doctor/integrity.py:549-573` 의 기존 `check_project` `tdd 정합성` 블록을 2-way (state ↔ project.md) → **3-way 확장 (+ prompts/*.md)**. 신규 섹션이 아니라 기존 블록 보강.

**Q4 — `--fix` 우선순위 (a 채택)**: state.yml 값을 진실로 간주. spec line 32 그대로.

**Q5 — 토글이 plan/구현 산출물 손대지 않음 (a 채택)**: 메타 모드만 전환. features/NN-*.md `.plan.md` 손대지 않음. spec line 73 그대로.

**Q6 — project SKILL.md `--tdd` 분기 patch 불필요 (트레이스 결과)**: `pilot/skills/project/SKILL.md:116-118` 가 tdd-activation 전체 위임 → state.yml 갱신 이미 됨. **patch 없음**. spec 본문의 해당 항목은 Q9 에서 함께 정정.

**Q7 — 회귀 fixture 본 plan 포함 (a 채택)**: `pilot/tests/fixtures/v0.1.0-baseline/tdd-on/expected/`, `tdd-off/expected/` 2 디렉터리 신설 + `diff.sh EXPECTED_SUBDIRS` 2 행 추가. features/00·13 패턴과 일관.

**Q8 — version bump milestone 끝 일괄**: v0.3.0 합본 PR. 본 PR 은 patch bump 안 함.

**Q9 — spec 본문 drift patch 동반 (T1·T2 정정)**: `features/15-tdd-mode-toggle.md` 본문의 두 부정확 진술을 함께 patch.
- T1: spec line 7 의 "현재 `tdd on` 도 `.agent-state.yml tdd:` 플래그를 갱신하지 않음 (skill 본문 trace 결과)" → "현재 `tdd on` 은 tdd-activation §5 가 .agent-state.yml `tdd: true` 를 갱신함. 그러나 off 분기 자체가 부재" 형태로 정정.
- T2: spec line 64-65 의 "project SKILL.md `--tdd` 분기에서 state.yml `tdd: true` 명시적 설정 (현재 skill 본문에 누락 가능성 점검)" → 해당 항목 삭제 또는 "이미 tdd-activation 위임으로 갱신됨, patch 불필요" 로 정정.

**Q10 — #14 broken link 정정 동반 (인수인계 line 126 소비)**: `pilot/docs/getting-started.md:200·202` 의 두 broken link 를 플러그인 내부 상대 경로로 교체.
- line 200: `[#15 TDD 토글](../../workspace/projects/build-plugin/features/15-tdd-mode-toggle.md)` → `[TDD 모드 토글](../skills/tdd/SKILL.md)`
- line 202: `[#16 Doctor onboarding-health](../../workspace/projects/build-plugin/features/16-doctor-onboarding-health.md)` → `[Doctor 진단](../skills/doctor/SKILL.md)`
- 인수인계 line 126 `[x]` 처리는 본 feature evaluator 단계에서 wrapper step 2.

## 범위 (포함/제외)

**포함:**
- `pilot/skills/tdd/SKILL.md` 본문 4 분기 재구성 (on / off / --fix / 상태 보고)
- `pilot/skills/context/modes/tdd-activation.md` off 복원 절차 + 백업 마커 주입 절차 추가
- `pilot/tools/doctor/integrity.py:549-573` 의 `check_project` `tdd 정합성` 블록 2-way → 3-way 확장 (state ↔ project.md ↔ prompts/*.md)
- 회귀 fixture 신설: `pilot/tests/fixtures/v0.1.0-baseline/tdd-on/expected/`, `pilot/tests/fixtures/v0.1.0-baseline/tdd-off/expected/`
- `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` 의 `EXPECTED_SUBDIRS` 에 2 행 추가
- spec drift patch: `features/15-tdd-mode-toggle.md` T1·T2 (Q9)
- broken link 정정: `pilot/docs/getting-started.md:200·202` (Q10, 인수인계 line 126 소비)

**제외:**
- fuzzy 매칭 (Q1 — literal only, v2 이외)
- `pilot/skills/project/SKILL.md` `--tdd` 분기 patch (Q6 — 트레이스 결과 이미 tdd-activation 위임 정상)
- features/NN-*.md 또는 .plan.md 산출물 자동 갱신 (Q5 — 메타 모드만 전환)
- template 기반 복원 (Q2 — 인라인 백업 마커 우선, template 는 fallback 만)
- `pilot/.claude-plugin/plugin.json` version bump (Q8 — v0.3.0 합본 PR 끝 일괄)

## 변경 파일

### 신설

- [x] `pilot/tests/fixtures/v0.1.0-baseline/tdd-on/expected/` (디렉터리 + 산출 캡처)
  - `expected/.agent-state.yml` (예: `tdd: true`, `mode: null`, `analyzed: true`)
  - `expected/workspace/projects/{PROJECT}/project.md` (TDD 흐름으로 교체된 본문 + 백업 마커)
  - `expected/workspace/projects/{PROJECT}/prompts/planner.md` (Red 계약 안내 inline)
  - `expected/workspace/projects/{PROJECT}/prompts/generator.md` (Red→Green→Refactor 절차 inline)
  - `expected/workspace/projects/{PROJECT}/prompts/evaluator.md` (tdd_evidence 게이트 inline)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/tdd-off/expected/` (디렉터리 + 산출 캡처)
  - `expected/.agent-state.yml` (예: `tdd: false`)
  - `expected/workspace/projects/{PROJECT}/project.md` (표준 흐름 복원 + 마커 제거)
  - `expected/workspace/projects/{PROJECT}/prompts/{planner,generator,evaluator}.md` (표준 분기)

### 수정

- [x] `pilot/skills/tdd/SKILL.md` (4 분기 재구성 — on/off/--fix/상태 보고)
- [x] `pilot/skills/context/modes/tdd-activation.md` (백업 마커 주입 절차 §X + off 복원 절차 §Y 추가)
- [x] `pilot/tools/doctor/integrity.py` (line 549-573 의 `tdd 정합성` 블록 2-way → 3-way 확장)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` (`EXPECTED_SUBDIRS` 에 `tdd-on/expected` `tdd-off/expected` 2 행 추가)
- [x] `pilot/docs/getting-started.md` (line 200·202 broken link 정정 — Q10)
- [x] `workspace/projects/build-plugin/features/15-tdd-mode-toggle.md` (T1·T2 spec drift patch — Q9)

## 단계별 구현 순서

### Step 1 — `tdd-activation.md` 보강 (백업 마커 + off 복원 절차)

**대상**: `pilot/skills/context/modes/tdd-activation.md`

**1-1. 백업 마커 주입 절차 추가 (`/pilot:tdd on` 또는 `/pilot:project --tdd` 활성화 분기)**

- 현재 §1~6 (활성화 본체) 의 § "project.md 의 ## 에이전트 호출 흐름 H2 본문 교체" 단계 직전에 sub-step 추가:
  - **기존 표준 흐름 본문을 마커로 감싼다**:
    - literal 매칭 패턴 (Q1 a 채택): project.md 의 `## 에이전트 호출 흐름` H2 직후부터 다음 H2 (`## 관련 파일` 또는 `## 에이전트 간 전달사항`) 직전까지의 본문을 잘라낸다.
    - 잘라낸 본문을 `<!-- pilot-tdd-original-flow:start -->\n{원본 본문}\n<!-- pilot-tdd-original-flow:end -->` 로 감싸서 H2 직후에 삽입.
    - 그 직후 TDD 분기 본문을 추가 (기존 §6 의 교체 흐름).
  - **literal 매칭 실패 시 (사용자가 H2 본문을 수정한 경우)**:
    - WARN 1 줄: `[WARN] '## 에이전트 호출 흐름' H2 본문이 표준 형식과 다름 — 백업 마커 주입 skip. /pilot:tdd off 시 template fallback 으로 복원됨.`
    - 마커 주입은 skip 하고 TDD 분기 본문은 H2 본문을 통째로 교체.

**1-2. off 복원 절차 추가 (§ 신규 — `## 비활성화 절차 (off)`)**

- §6 (활성화 종료) 직후 신규 H2 `## 비활성화 절차 (/pilot:tdd off)` 추가:
  1. `.agent-state.yml` 의 `tdd:` 키를 `false` 로 갱신.
  2. project.md 의 `## 에이전트 호출 흐름` H2 본문에서 `<!-- pilot-tdd-original-flow:start -->` ... `<!-- pilot-tdd-original-flow:end -->` 마커를 찾는다.
     - 마커 발견 → 마커 안의 본문을 그대로 사용해 TDD 분기 본문을 복원 (인라인 백업 우선, Q2 b 채택).
     - 마커 부재 → `pilot/skills/context/lifecycle/setup/templates/project.md.template` 의 표준 흐름 본문을 template fallback 으로 사용 + INFO 1 줄: `[INFO] 백업 마커 부재 (구버전 프로젝트) — template 표준 흐름으로 복원. 사용자가 표준 흐름을 수정한 적이 있다면 수동 검토 권장.`
  3. `prompts/{planner,generator,evaluator}.md` 의 TDD 분기 본문을 표준 분기로 교체.
     - 각 prompts 파일도 동일한 마커 쌍 (`<!-- pilot-tdd-original-{planner|generator|evaluator}:start -->` ... `:end -->`) 으로 인라인 백업 → 복원.
  4. 복원 완료 후 사용자에게 결과 보고 (변경된 파일 목록 + state.yml `tdd: false` 확인).

**1-3. literal 매칭 정확 문자열 명시**

- §1-1 의 H2 매칭 regex 패턴을 본문에 명시 (generator 가 그대로 사용):
  - H2 시작 매칭: `^## 에이전트 호출 흐름\s*$` (정확 일치, 양 끝 공백 허용)
  - H2 끝 매칭: 다음 `^## ` 로 시작하는 줄 직전까지 (또는 파일 끝).
  - 마커 매칭: `<!-- pilot-tdd-original-flow:start -->[\s\S]*?<!-- pilot-tdd-original-flow:end -->` (non-greedy, 첫 `:end -->` 까지).

**검증**: `tdd-activation.md` 본문 안에 §1-1·§1-2·§1-3 모두 명시되었는지 확인.

### Step 2 — `pilot/skills/tdd/SKILL.md` 4 분기 재구성

**대상**: `pilot/skills/tdd/SKILL.md`

현재 단방향 활성화 (인자 없는 `/pilot:tdd` 단독) 본문을 4 분기로 재구성. 각 분기의 사용자 출력 형식 포함.

**분기 1: `/pilot:tdd on` (활성화)**

```markdown
## /pilot:tdd on

1. `.agent-state.yml` 의 `tdd:` 값을 읽는다.
   - 이미 `tdd: true` → 사용자에게 `[INFO] TDD 모드 이미 활성화 상태 (state.yml tdd: true)` 보고 후 종료 (idempotent).
2. tdd-activation.md §1~6 (활성화 본체) 위임 — 백업 마커 주입 포함 (§1-1).
3. 완료 후 사용자 출력:
   ```
   ✓ TDD 모드 활성화
     - .agent-state.yml: tdd: true
     - project.md `## 에이전트 호출 흐름`: TDD 분기로 교체 (백업 마커 주입 완료)
     - prompts/{planner,generator,evaluator}.md: TDD 분기 활성
   ```
```

**분기 2: `/pilot:tdd off` (비활성화)**

```markdown
## /pilot:tdd off

1. `.agent-state.yml` 의 `tdd:` 값을 읽는다.
   - 이미 `tdd: false` → 사용자에게 `[INFO] TDD 모드 이미 비활성화 상태 (state.yml tdd: false)` 보고 후 종료 (idempotent).
2. tdd-activation.md 의 `## 비활성화 절차 (/pilot:tdd off)` 위임 — 백업 마커 복원 포함 (§1-2).
3. 완료 후 사용자 출력:
   ```
   ✓ TDD 모드 비활성화
     - .agent-state.yml: tdd: false
     - project.md `## 에이전트 호출 흐름`: 표준 흐름 복원 (백업 마커에서)
     - prompts/{planner,generator,evaluator}.md: 표준 분기 복원
   ```
   - 마커 부재 시 (template fallback) INFO 1 줄 함께 출력 (§1-2 step 2).
```

**분기 3: `/pilot:tdd --fix` (정합성 보정)**

```markdown
## /pilot:tdd --fix

1. `.agent-state.yml` 의 `tdd:` 값을 진실로 간주 (Q4 a 채택, spec line 32).
2. doctor 의 3-way 검증 (Step 3 의 확장된 `tdd 정합성` 블록) 호출.
   - state ↔ project.md ↔ prompts/*.md 셋 중 state 와 다른 부분 detect.
3. state 값이 `true` 이면 활성화 절차 (분기 1) 재실행 (idempotent — 이미 일치하면 no-op).
   state 값이 `false` 이면 비활성화 절차 (분기 2) 재실행.
4. 완료 후 사용자 출력:
   ```
   ✓ TDD 정합성 보정 (state.yml 진실 기준)
     - 보정 전 INCONSISTENT: project.md 만 표준 흐름 / prompts 만 TDD 분기 (예시)
     - 보정 후 CONSISTENT: state=true · project.md=TDD · prompts=TDD
   ```
```

**분기 4: `/pilot:tdd` (인자 없음 — 상태 보고)**

```markdown
## /pilot:tdd (인자 없음)

1. `.agent-state.yml` 의 `tdd:` 값을 읽는다.
2. doctor 의 3-way 검증 호출 — INCONSISTENT 여부 확인.
3. 사용자 출력:
   ```
   TDD 모드 상태
     - .agent-state.yml: tdd: {true|false}
     - project.md `## 에이전트 호출 흐름`: {TDD 분기|표준 흐름|INCONSISTENT}
     - prompts/{planner,generator,evaluator}.md: {TDD 분기|표준 분기|INCONSISTENT}

   {모두 일치 시: ✓ 정합성 OK
    불일치 시: ⚠ INCONSISTENT — `/pilot:tdd --fix` 로 보정 권장}
   ```
```

**검증**: SKILL.md 본문에 4 분기 (on/off/--fix/상태 보고) 모두 명시되었는지 + 각 분기의 출력 형식이 위와 정합한지 확인.

### Step 3 — `pilot/tools/doctor/integrity.py:549-573` 의 `tdd 정합성` 블록 3-way 확장

**대상**: `pilot/tools/doctor/integrity.py`, `check_project` 함수 안의 기존 `tdd 정합성` 블록 (line 549-573)

**3-1. 기존 2-way 블록 (state ↔ project.md) 보강 → 3-way (state ↔ project.md ↔ prompts/*.md)**

- 함수 시그니처 `check_project(project_dir: Path) -> list[Result]` 그대로 유지 (호출자 영향 0, Q3 a 채택).
- 기존 블록의 state.yml `tdd:` 값 읽기 + project.md `## 에이전트 호출 흐름` 본문 TDD 분기 여부 detect 로직 그대로 유지.
- 신규 추가: prompts/`{planner,generator,evaluator}`.md 3 파일 각각의 TDD 분기 활성 여부 detect.
  - detect 방법: 백업 마커 `<!-- pilot-tdd-original-{planner|generator|evaluator}:start -->` 존재 여부 (마커 있음 → TDD 분기 활성 중).
  - 마커 부재 + state.yml `tdd: true` → INCONSISTENT (구버전 프로젝트가 TDD 활성화 안 됐을 가능성).

**3-2. INCONSISTENT 판정 룰**

- state `tdd: true` ↔ project.md TDD 분기 ↔ prompts/*.md 마커 모두 존재 → CONSISTENT (PASS)
- state `tdd: false` ↔ project.md 표준 흐름 ↔ prompts/*.md 마커 모두 부재 → CONSISTENT (PASS)
- 그 외 조합 → INCONSISTENT 판정 + WARN 1 줄:
  ```
  [WARN] TDD 모드 정합성 불일치 — state.yml=tdd:{value} · project.md={TDD|표준} · prompts/*.md={TDD|표준|MIXED}
        처방: `/pilot:tdd --fix` 실행 권장 (state.yml 값을 진실로 보정).
  ```

**3-3. 기존 호출자 영향 검증**

- `run_integrity_check` 의 `check_project` 호출 위치 (integrity.py 안) 그대로. INCONSISTENT 시 Result.WARN 추가만 — Result.ERROR 발화 안 함 (backward-compat — 기존 v0.2.x 사용자가 갑자기 ERROR 발화 안 받도록).

**검증**: integrity.py 의 `tdd 정합성` 블록이 prompts/*.md 3 파일을 모두 lookup + INCONSISTENT 시 WARN 1 줄 발화 + `--fix` 처방 출력. `check_project` 시그니처 변경 0.

### Step 4 — spec drift patch (T1·T2 — Q9)

**대상**: `workspace/projects/build-plugin/features/15-tdd-mode-toggle.md`

**4-1. T1 — line 7 정정**

- 기존: "현재 `tdd on` 도 `.agent-state.yml tdd:` 플래그를 갱신하지 않음 (skill 본문 trace 결과)"
- 정정: "현재 `tdd on` 은 tdd-activation §5 가 .agent-state.yml `tdd: true` 를 갱신함. 그러나 `tdd off` 분기 자체가 부재하여 비활성화 시 state.yml 가 stale 상태로 남는다."

**4-2. T2 — line 64-65 정정**

- 기존: "project SKILL.md `--tdd` 분기에서 state.yml `tdd: true` 명시적 설정 (현재 skill 본문에 누락 가능성 점검)"
- 정정: 해당 항목 삭제. (또는 "이미 `pilot/skills/project/SKILL.md:116-118` 가 tdd-activation 위임 → state.yml `tdd: true` 갱신 정상. patch 불필요." 로 정정. 사용자가 spec drift patch 의 명확성을 우선시하면 삭제 권장 — Q9 사용자 결정 시 둘 다 옵션 제시했고 명확한 선택 없었으므로 generator 는 사용자에게 1 회 확인.)

**검증**: spec 본문에 T1 정정 반영 + T2 항목 삭제 또는 정정. 다른 본문 변경 없음.

### Step 5 — broken link 정정 (Q10 — 인수인계 line 126 소비)

**대상**: `pilot/docs/getting-started.md` line 200·202

**5-1. line 200 교체**

- 기존: `[#15 TDD 토글](../../workspace/projects/build-plugin/features/15-tdd-mode-toggle.md)`
- 신규: `[TDD 모드 토글](../skills/tdd/SKILL.md)`

**5-2. line 202 교체**

- 기존: `[#16 Doctor onboarding-health](../../workspace/projects/build-plugin/features/16-doctor-onboarding-health.md)`
- 신규: `[Doctor 진단](../skills/doctor/SKILL.md)`

**검증**: 두 줄 모두 플러그인 내부 상대 경로 (`../skills/...`) 로 교체 + 링크 텍스트 자연어로 정정. broken link 0 확인.

### Step 6 — 회귀 fixture 캡처 (`tdd-on/expected/`, `tdd-off/expected/`)

**대상**: `pilot/tests/fixtures/v0.1.0-baseline/`

**6-1. `tdd-on/expected/` 캡처 절차**

- 입력: 기존 `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 트리 그대로.
- 절차: 가상 프로젝트에 `/pilot:project python-sample-demo --tdd` (또는 `/pilot:tdd on`) 실행 시뮬레이션.
- 캡처 산출물:
  - `tdd-on/expected/.agent-state.yml` (`tdd: true`, `analyzed: true`, 기존 다른 필드 보존)
  - `tdd-on/expected/workspace/projects/python-sample-demo/project.md` (TDD 분기 + 백업 마커)
  - `tdd-on/expected/workspace/projects/python-sample-demo/prompts/planner.md` (Red 계약 안내 + 마커)
  - `tdd-on/expected/workspace/projects/python-sample-demo/prompts/generator.md` (Red→Green→Refactor 절차 + 마커)
  - `tdd-on/expected/workspace/projects/python-sample-demo/prompts/evaluator.md` (tdd_evidence 게이트 + 마커)

**6-2. `tdd-off/expected/` 캡처 절차**

- 입력: 6-1 결과를 받아 `/pilot:tdd off` 시뮬레이션.
- 캡처 산출물:
  - `tdd-off/expected/.agent-state.yml` (`tdd: false`)
  - `tdd-off/expected/workspace/projects/python-sample-demo/project.md` (표준 흐름 복원, 마커 제거)
  - `tdd-off/expected/workspace/projects/python-sample-demo/prompts/{planner,generator,evaluator}.md` (표준 분기 복원, 마커 제거)

**6-3. 파일 명명 / 디렉터리 구조 규칙**

- 기존 features/00·13 의 expected/ 구조 (`expected/{config,workspace}/...`) 답습.
- README 또는 INDEX 파일 신설 안 함 (features/13 의 `wizard/expected/` 도 README 없음).

**검증**: 두 디렉터리 모두 산출물 4~5 파일씩 갖는다. project.md / prompts 안의 백업 마커 `<!-- pilot-tdd-original-flow:start -->` ... 형식 정확.

### Step 7 — `diff.sh` 의 `EXPECTED_SUBDIRS` 2 행 추가

**대상**: `pilot/tests/fixtures/v0.1.0-baseline/diff.sh`

**7-1. 위치**

- `diff.sh` 의 `EXPECTED_SUBDIRS=(...)` 배열 안 (features/13 의 `wizard/expected` 추가 패턴 답습).

**7-2. 추가 2 행**

```bash
EXPECTED_SUBDIRS=(
  # ... 기존 행들 (config, learn, project, analyze, wizard 등) ...
  "tdd-on/expected"
  "tdd-off/expected"
)
```

**검증**: diff.sh 가 두 디렉터리를 비교 대상에 포함 + `diff.sh` exit 0 (tdd-on/off 양쪽 산출이 expected 와 정확 일치 시). 다른 EXPECTED_SUBDIRS 행 영향 0.

### Step 8 — 회귀 검증 + doctor 3-way 룰 동작 확인

**8-1. 토글 cycle 검증**

- 가상 프로젝트에서 `/pilot:tdd on` → `/pilot:tdd off` → `/pilot:tdd on` 3 회 수행 후 .agent-state.yml + project.md + prompts/*.md 셋 모두 일관 (3-way idempotency).
- 매 cycle 후 `diff.sh` exit 0 확인 (tdd-on/off 양쪽 expected 와 정확 일치).

**8-2. doctor 3-way 룰 동작 확인**

- 인공적으로 INCONSISTENT 상태 (예: state `tdd: true` + project.md 표준 흐름) 생성 → `doctor` 호출 → WARN 1 줄 + `--fix` 처방 출력 확인.
- `/pilot:tdd --fix` 호출 → state 진실 기준으로 보정 → 재 doctor 호출 시 WARN 0 확인.

**8-3. spec drift + broken link 검증**

- spec line 7·64-65 정정 적용 확인 (T1·T2 — Q9).
- `pilot/docs/getting-started.md` line 200·202 broken link 0 확인 (Q10).

## 검증 방법 (요약)

- `pilot/skills/tdd/SKILL.md` 의 4 분기 (on/off/--fix/상태 보고) 본문 + 사용자 출력 형식 명시 (Step 2).
- on/off cycle 후 `.agent-state.yml` + `project.md` + `prompts/*.md` 셋이 일관 (3-way idempotency, Step 8-1).
- doctor 의 tdd 3-way 룰이 INCONSISTENT 시 WARN + `--fix` 처방 출력 (Step 8-2).
- fixture `diff.sh` exit 0 (tdd-on/off 양쪽, Step 7·8-1).
- spec line 7·64-65 정정 적용 (Step 4 — T1·T2 / Q9).
- `pilot/docs/getting-started.md` line 200·202 broken link 0 (Step 5 — Q10).

## 주의사항

- **백업 마커 (Q2 b) 본문 인코딩 시 nested HTML comment 위험**: `-->` 가 본문에 등장하면 마커 종료 오인. 본 마커는 1 회 등장하므로 safe — 단 복원 함수의 regex 가 첫 `<!-- pilot-tdd-original-flow:end -->` 까지 매칭하도록 (non-greedy `[\s\S]*?`).
- **off 시 백업 마커 부재 (구버전 프로젝트)**: template fallback + INFO 1 줄 발화 (spec line 78 와 정합). 사용자가 표준 흐름을 수정한 적이 있다면 수동 검토 권장.
- **doctor 3-way 룰은 기존 2-way 블록의 함수 시그니처 보존** (`check_project(project_dir: Path) -> list[Result]`). 호출자 영향 0 (Q3 a 채택).
- **`pilot/skills/project/SKILL.md` patch 없음** (Q6 — 트레이스 결과 이미 tdd-activation 위임으로 state.yml `tdd: true` 갱신 정상).
- **features/15-tdd-mode-toggle.md spec patch (T1·T2)** 는 v0.3.0 milestone 끝 PR 에서 의미 명확화. 본 plan 작성 시점에 함께 진행 (Q9).
- **prompts/*.md 의 마커 쌍 명명**: 각 prompts 파일별로 `<!-- pilot-tdd-original-{planner|generator|evaluator}:start -->` ... `:end -->` 사용 (project.md 의 `pilot-tdd-original-flow:*` 와 명확히 구분). 한 파일에 여러 마커 쌍 등장 금지.
- **literal 매칭 정확 문자열** (Step 1-3): generator 가 본문 그대로 사용. 매칭 실패 시 WARN + skip (abort 금지 — A2 runtime fallback 패턴 답습).
- **체크박스 갱신 권한 분리** (#03 인수인계 line 99 반영): 본 generator 가 project.md `## 목표` 체크박스를 직접 수정 안 함. evaluator wrapper step 5 가 단독 권한자.
- **version bump 0** (Q8): 본 plan 의 PR 은 `pilot/.claude-plugin/plugin.json` version 변경 없음. v0.3.0 합본 PR 끝에 일괄.

## 교차 의존

- `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 트리 (features/00 산출) — fixture 캡처 입력 (이미 실재, 본 plan 의 step 6 에서 사용).
- 인수인계 line 126 (#14 broken link 정정) — Q10 으로 본 plan step 5 에서 소비. evaluator 단계 wrapper step 2 가 `[x]` 처리.
- T1·T2 spec drift — 본 plan 의 step 4 에서 함께 patch (Q9).
- `pilot/skills/context/lifecycle/setup/templates/project.md.template` (off 시 template fallback) — Q2 인라인 백업 우선이라 fallback 만, 본 plan 에서 template 자체 변경 0.
- `pilot/skills/project/SKILL.md:116-118` — 본 plan patch 안 함 (Q6). 단 향후 `--tdd` 분기 변경 시 본 plan 의 tdd-activation §1-1 마커 주입 절차와 호환 확인 필요.
- `pilot/skills/context/modes/rgr.md` — TDD 모드 활성 시 generator/evaluator 가 참조하는 Red-Green-Refactor 절차. 본 plan 변경 0 (메타 모드 토글만 담당).
