# TDD 활성화 절차 (SSOT)

이 문서는 `/pilot:project --tdd` 와 `/pilot:tdd` 양쪽에서 참조되는 공통 절차다.
대상 프로젝트는 호출자가 결정한다. 이 문서에서는 `{PROJECT}` 로 표기한다.

모든 단계는 **idempotent** 하다. "이미 존재함" 판별 기준은 각 단계의 **Detect literal** 로 명시한다. 해당 literal 이 파일에 이미 있으면 그 단계를 생략한다.

대상 파일:

- `workspace/projects/{PROJECT}/project.md`
- `workspace/projects/{PROJECT}/prompts/planner.md`
- `workspace/projects/{PROJECT}/prompts/generator.md`
- `workspace/projects/{PROJECT}/prompts/evaluator.md`

---

## 1. `project.md` 수정

### 1-1. `## 제한사항` 에 TDD 문구 추가 (중복 방지)

**Detect literal:** `- **TDD 모드**:` (제한사항 섹션 내 문자열 포함 여부로 판단)

이미 있으면 생략한다. 없으면 아래 항목을 추가한다:

```markdown
- **TDD 모드**: 테스트 없이 프로덕션 코드를 작성하지 않는다. Planner 는 Red 계약 (스텝 분할 + 테스트 경로·검증 행동·기대 실패 유형) 만 남기고, Generator 가 **Red 작성·실패 확인 → Green → Refactor** 를 한 컨텍스트에서 순환한다. Evaluator 는 `.plan.md` 의 Red 증거 교차 검증 + **변경 관련 테스트만** 실행한다.
```

### 1-1b. `## 에이전트 호출 흐름` 기존 본문을 백업 마커로 감싸기

**on 활성화 직전에 수행한다.** 1-2 교체 전 단계.

1. `## 에이전트 호출 흐름` H2 직후부터 다음 H2 (`^## ` 로 시작하는 줄) 직전까지 본문을 잘라낸다.
   - H2 시작 매칭: `^## 에이전트 호출 흐름\s*$` (정확 일치, 양 끝 공백 허용)
   - H2 끝 매칭: 다음 `^## ` 로 시작하는 줄 직전까지 (또는 파일 끝)
2. 잘라낸 본문이 **이미 마커로 감싸여 있으면** (마커 매칭: `<!-- pilot-tdd-original-flow:start -->[\s\S]*?<!-- pilot-tdd-original-flow:end -->`, non-greedy) → 이 단계 skip (idempotent).
3. **표준 흐름 literal 확인** (`### 1. Planner — 구현 계획 수립` 포함 여부):
   - 포함 → 잘라낸 본문을 아래 마커 쌍으로 감싸서 H2 직후에 삽입:
     ```
     <!-- pilot-tdd-original-flow:start -->
     {원본 본문}
     <!-- pilot-tdd-original-flow:end -->
     ```
   - 미포함 (사용자가 본문 수정) → **WARN 1줄** 출력 후 마커 주입 skip:
     ```
     [WARN] '## 에이전트 호출 흐름' H2 본문이 표준 형식과 다름 — 백업 마커 주입 skip. /pilot:tdd off 시 template fallback 으로 복원됨.
     ```

### 1-2. `## 에이전트 호출 흐름` 을 TDD 버전으로 교체

**Detect literal:** `### 1. Planner — Red 계약 작성` (`## 에이전트 호출 흐름` 섹션 내 포함 여부로 판단)

이미 있으면 생략한다. 없으면 기존 `## 에이전트 호출 흐름` 섹션 본문 (백업 마커 주입 후) 을 아래 구조로 교체한다.

```markdown
## 에이전트 호출 흐름

**순서를 반드시 준수한다. 이전 단계 완료 전 다음 단계로 진행하지 않는다.**

### 1. Planner — Red 계약 작성 (테스트 코드 X)

- **진입 조건:** 새 기능 구현 시작 시 항상 실행
- **로드:** `prompts/planner.md` + [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md)
- **산출물:** `.plan.md` 에 스텝별 3 축 기록 — (a) 테스트 대상 경로 · (b) 검증할 행동 · (c) 기대 실패 유형
- **완료 기준:** 스텝 목록과 Red 계약 3 축 확정 → Generator 진행
- **금지:** 테스트 코드 작성 — Generator 담당

### 2. Generator — Red + Green + Refactor 순환

- **진입 조건:** Planner 의 Red 계약 확정 후
- **로드:** `prompts/generator.md` + [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) + [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) + workspace `conventions_doc` (`orchestrate-load` 자동 주입)
- **동작:** 스텝마다 Red → Green → Refactor 를 한 컨텍스트에서 순환. 각 스텝의 `.plan.md` 에 `[Red] 실패 유형·메시지` / `[Green] 통과 시각` / `[Refactor] 수정 내역` 을 Edit 로 기록.
- **완료 기준:** 모든 스텝 [Red]+[Green] 증거 기록 + 직전 `{test_command}` 전체 PASS + `{source_root}` 1 개 이상 수정 → Evaluator 진행

### 3. Evaluator — Red 증거 교차 검증 + 변경 관련 테스트 실행

- **진입 조건:** Generator 완료 후
- **로드:** `prompts/evaluator.md`
- **동작:** `{test_command} {변경 관련 경로}` 실행 + `.plan.md` 스텝별 [Red]+[Green] 증거 교차 검증. 증거 누락·"인프라 오류" 기록 스텝 발견 시 Generator 에 반려.
- **완료 기준:** 변경 관련 테스트 통과 + Red 증거 교차 검증 통과 + 요구사항 체크리스트 확인 → 목표의 해당 항목 완료 처리 + VERIFICATION REPORT `status: READY` 출력
- **금지:** 인자 없는 `{test_command}` (전체 스위트) 실행 금지 — 반드시 변경된 테스트 경로를 나열
```

---

## 2. `prompts/planner.md` — TDD Red 계약 단계 추가

**Detect literal:** `## TDD — Red 계약`

파일 **말미에** 아래 섹션을 추가한다. literal 이 이미 있으면 생략한다.

```markdown
---

## TDD — Red 계약

이 프로젝트는 TDD 모드다. Planner 는 Red 계약만 남긴다 — **테스트 코드는 작성하지 않는다**. 스텝별 3 축 (테스트 경로 · 검증할 행동 · 기대 실패 유형) 을 `.plan.md` 에 기록한다. 상세: [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Planner — Red Contract` 절 (래퍼가 자동 로드).
```

---

## 3. `prompts/generator.md` — TDD 모드 안내 추가

**Detect literal:** `> **TDD 모드**: Red 작성`

파일 **최상단(첫 줄 앞)** 에 아래 안내를 추가한다. literal 이 이미 있으면 생략한다.

```markdown
> **TDD 모드**: Red 작성·실패 확인 → Green (최소 구현) → Refactor 를 한 컨텍스트에서 순환한다.
> Planner 가 남긴 `.plan.md` 의 Red 계약을 따라 spec 을 직접 작성·실행한다. 각 스텝의 `[Red][Green][Refactor]` 증거를 `.plan.md` 에 Edit 로 기록 (텍스트 보고만 금지). 상세 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Generator — Red + Green + Refactor` 절을 따른다 (래퍼가 자동 로드).
```

---

## 4. `prompts/evaluator.md` — TDD 테스트 실행 섹션 추가

**Detect literal:** `## TDD 테스트 실행`

파일 **최상단(첫 줄 앞)** 에 아래 섹션을 추가한다. literal 이 이미 있으면 생략한다.

```markdown
## TDD 테스트 실행

이 프로젝트는 TDD 모드다. (1) 변경 관련 테스트 실행 + (2) `.plan.md` 스텝별 `[Red]+[Green]` 증거 교차 검증. 증거 누락·"인프라 오류" 기록 스텝 발견 시 Generator 에 반려. 상세 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Evaluator — 실행 및 검증` 절을 따른다. 실행 대상 테스트 경로는 이번 feature 의 `plan.md` 에서 확인한다 (인자 없는 전체 스위트 실행 금지). 실제 명령 문자열은 `workspace/context/config.md` 의 `{test_command}` 값.

---
```

---

## 비활성화 절차 (/pilot:tdd off)

이 섹션은 `/pilot:tdd off` 분기가 위임한다. 단계는 **idempotent** 하다.

### off-1. `.agent-state.yml` — `tdd: false` 갱신

`workspace/projects/{PROJECT}/.agent-state.yml` 을 Read 후 `tdd: true` 를 `tdd: false` 로 Edit.
이미 `tdd: false` 이면 skip.

### off-2. `project.md` 의 `## 에이전트 호출 흐름` 복원

1. `## 에이전트 호출 흐름` H2 본문에서 `<!-- pilot-tdd-original-flow:start -->` ... `<!-- pilot-tdd-original-flow:end -->` 마커를 검색한다.
   - **마커 발견** → 마커 안의 원본 본문을 꺼내, 마커 쌍 + TDD 분기 본문 전체를 원본 본문으로 교체 (마커 제거). 인라인 백업 우선 (Q2 b 채택).
   - **마커 부재** → `pilot/skills/context/lifecycle/setup/templates/project.md.template` 의 `## 에이전트 호출 흐름` 섹션 본문으로 교체 + INFO 1줄 출력:
     ```
     [INFO] 백업 마커 부재 (구버전 프로젝트) — template 표준 흐름으로 복원. 사용자가 표준 흐름을 수정한 적이 있다면 수동 검토 권장.
     ```

### off-3. `project.md` 의 `## 제한사항` 에서 TDD 문구 제거

**Detect literal:** `- **TDD 모드**:` (제한사항 섹션 내)

literal 이 있으면 해당 bullet 1개 단락 (다음 bullet 직전까지) 을 제거한다. 없으면 skip.
literal 매칭 실패 시 (구버전 문구) → **WARN 1줄** + 사용자에게 수동 제거 안내:
```
[WARN] `## 제한사항` 내 TDD 문구 literal 매칭 실패 — 수동 제거 필요.
```

### off-4. `prompts/planner.md` — TDD Red 계약 단계 제거

**Detect literal:** `## TDD — Red 계약`

literal 이 있으면:
1. `<!-- pilot-tdd-original-planner:start -->` ... `<!-- pilot-tdd-original-planner:end -->` 마커 검색.
   - 마커 발견 → 마커 안 원본 본문 복원 + 마커·TDD 섹션 제거.
   - 마커 부재 → `## TDD — Red 계약` 섹션 (다음 `---` 구분선 또는 파일 끝까지) 을 포함한 앞 `---` 줄까지 제거.

없으면 skip.

### off-5. `prompts/generator.md` — TDD 모드 안내 제거

**Detect literal:** `> **TDD 모드**: Red 작성`

literal 이 있으면:
1. `<!-- pilot-tdd-original-generator:start -->` ... `<!-- pilot-tdd-original-generator:end -->` 마커 검색.
   - 마커 발견 → 마커 안 원본 본문 복원 + 마커·TDD 안내 제거.
   - 마커 부재 → `> **TDD 모드**: Red 작성` 으로 시작하는 blockquote 블록 (연속된 `>` 줄) 을 제거.

없으면 skip.

### off-6. `prompts/evaluator.md` — TDD 테스트 실행 섹션 제거

**Detect literal:** `## TDD 테스트 실행`

literal 이 있으면:
1. `<!-- pilot-tdd-original-evaluator:start -->` ... `<!-- pilot-tdd-original-evaluator:end -->` 마커 검색.
   - 마커 발견 → 마커 안 원본 본문 복원 + 마커·TDD 섹션 제거.
   - 마커 부재 → `## TDD 테스트 실행` 섹션 (다음 `---` 구분선까지, `---` 포함) 제거.

없으면 skip.

### off-7. 완료 보고

수정된 파일 목록 + state.yml `tdd: false` 확인:

```
✓ TDD 모드 비활성화
  - .agent-state.yml: tdd: false
  - project.md `## 에이전트 호출 흐름`: 표준 흐름 복원 (백업 마커에서)
  - prompts/{planner,generator,evaluator}.md: 표준 분기 복원
```

---

### literal 매칭 정확 문자열 (§1-1b · off-2 · off-3)

generator 가 본문 그대로 사용. 매칭 실패 시 WARN + skip (abort 금지 — A2 runtime fallback).

- H2 시작 매칭: `^## 에이전트 호출 흐름\s*$` (정확 일치, 양 끝 공백 허용)
- H2 끝 매칭: 다음 `^## ` 로 시작하는 줄 직전까지 (또는 파일 끝)
- 마커 매칭: `<!-- pilot-tdd-original-flow:start -->[\s\S]*?<!-- pilot-tdd-original-flow:end -->` (non-greedy, 첫 `:end -->` 까지)
- prompts 마커 명명 패턴: `<!-- pilot-tdd-original-{planner|generator|evaluator}:start -->` ... `:end -->` (각 파일별 고유, 혼용 금지)

---

## 5. `.agent-state.yml` — `tdd: true` 갱신

**Detect literal:** `tdd: true`

`workspace/projects/{PROJECT}/.agent-state.yml` 을 Read 후:

- `schema` 가 지원 버전(`v1.1`, `v1.2`) 이 아니거나 파일 없음 → 에러 출력: **"프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도하세요."**
- `tdd: true` 이미 있으면 생략.
- 없으면 `tdd: false` 를 `tdd: true` 로 Edit.

이 단계를 통과해야 wrapper (`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator`) 가 TDD 분기로 동작한다. 스키마 상세: [state-schema.md](../lifecycle/state-schema.md).

---

## 6. 무결성 검증 (자동)

TDD 활성화 완료 후 아래를 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

- ERROR / WARN 있으면 **원문 그대로** 출력.
- 모두 PASS 면 `doctor: all checks passed`.

---

## 완료 후 요약 출력

호출자는 아래 항목을 요약해 사용자에게 안내한다.

- 수정된 파일: `project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md`, `.agent-state.yml`
- 참조 문서: `skills/context/modes/rgr.md`, `skills/context/lifecycle/state-schema.md`
