# python-sample-demo

> **Orchestrator** — 프로젝트 전체 흐름을 조율한다.
> 구체적 구현 지식은 `prompts/` 의 에이전트 컨텍스트 파일을 참조한다.
>
> **이 파일은 스캐폴딩 템플릿이다.** `/pilot:project` 가 신규 프로젝트 생성 시 그대로 복사한다.
> `{프로젝트명}` 토큰만 실제 프로젝트명으로 치환하고, 본문의 `{…}` 플레이스홀더는 사용자 또는 `/pilot:analyze` 가 채운다.

## 개요

{프로젝트 목적과 배경을 1~2문장으로}

## 제한사항

- {구현 제약 사항 — 예: 특정 DB 단일 조회, 외부 API 호출 금지, 상태값 전환 규칙 등}
- **TDD 모드**: 테스트 없이 프로덕션 코드를 작성하지 않는다. Planner 는 Red 계약 (스텝 분할 + 테스트 경로·검증 행동·기대 실패 유형) 만 남기고, Generator 가 **Red 작성·실패 확인 → Green → Refactor** 를 한 컨텍스트에서 순환한다. Evaluator 는 `.plan.md` 의 Red 증거 교차 검증 + **변경 관련 테스트만** 실행한다.

## 목표

- [ ] {완료 조건 1} -> [상세](features/NN-{slug}.md)
- [ ] {완료 조건 2} -> [상세](features/NN-{slug}.md)

> `/pilot:analyze` 실행 시 features/ 파일과 동기화되어 이 목록이 자동 갱신된다.

## 에이전트 호출 흐름

<!-- pilot-tdd-original-flow:start -->

**순서를 반드시 준수한다. 이전 단계 완료 전 다음 단계로 진행하지 않는다.**

### 1. Planner — 구현 계획 수립

- **진입 조건:** 새 기능 구현 시작 시 항상 실행
- **로드:** `prompts/planner.md`
- **완료 기준:** 구현 단계별 계획이 명시적으로 확정됨 → Generator 진행

### 2. Generator — 코드 구현

- **진입 조건:** Planner 계획 확정 후
- **로드:** `prompts/generator.md` + [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md)
- **완료 기준:** 구현 완료 후 [`evals/coding.json`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/evals/coding.json) 해당 케이스 체크 통과 → Evaluator 진행

### 3. Evaluator — 검토

- **진입 조건:** Generator eval 체크 통과 후
- **로드:** `prompts/evaluator.md`
- **완료 기준:** 체크리스트 전 항목 확인 → 목표의 해당 항목 `[x]` 처리

> **TDD 모드** 활성화 시 (`/pilot:project {PROJECT} --tdd` 또는 `/pilot:tdd`) 이 섹션이 Red-Green-Refactor 흐름으로 자동 교체된다. 상세: [tdd-activation.md](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/tdd-activation.md).

<!-- pilot-tdd-original-flow:end -->

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

## 관련 파일

> H3 + 표는 `/pilot:project` 가 신규 폴더 생성 시 1 회 가공한다 (`workspace/context/config.md` 의 `## scope 카테고리` 의 `project.md 대상 H3` 컬럼 따라 H3 + 빈 표 생성). 표 본문은 `/pilot:analyze` 5-2 또는 `/pilot:create-feature` 가 매번 갱신한다. 사용자 수동 추가 H3 는 양쪽 모두 보존, 삭제는 복구하지 않는다.

### Endpoints

| 엔드포인트 | Method | 목적 |
| ---------- | ------ | ---- |

### Models

| Class | DB | 목적 |
| ----- | -- | ---- |

### Services

| Class | 파일 | 목적 |
| ----- | ---- | ---- |

## 에이전트 간 전달사항
