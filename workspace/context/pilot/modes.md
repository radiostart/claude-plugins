# pilot — Modes skills

활성 프로젝트의 실행 모드를 전환한다. 2 개 스킬: `tdd` `characterize`. 둘 다 `.agent-state.yml` 의 모드 플래그를 토글하고 prompts/* 의 거동을 바꾼다.

> 두 모드 동시 활성 시 — `tdd: true` + `mode: characterize` 면 **characterize 가 우선** (Red 계약 대신 Characterization Contract) (`pilot/skills/characterize/SKILL.md:54`).

---

## `/pilot:tdd`

이미 구현된 코드가 있는 기존 프로젝트에 TDD 모드를 사후 적용 (`pilot/skills/tdd/SKILL.md:10`).

> 신규 프로젝트를 TDD 로 시작할 때는 `/pilot:project {PROJECT} --tdd` 사용 (`pilot/skills/tdd/SKILL.md:12-13`).

- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/tdd/SKILL.md:16-18`).
- **수행 절차** (`pilot/skills/tdd/SKILL.md:21-29`):
  1. `workspace/projects/{PROJECT}/project.md` 의 `## 제한사항` 에 **TDD 모드** 문구 (`tdd-activation.md` §1-1 literal) 존재 확인.
     - 이미 있으면 → `messages.md:tdd_already_active` 출력 후 누락 항목만 보완.
     - 없으면 → 2 단계 수행.
  2. `tdd-activation.md` 절차에 따라 `project.md`, `prompts/{planner,generator,evaluator}.md` 갱신. **각 단계 idempotent** — 이미 적용된 항목은 자동 skip.
  3. 결과 요약 + "TDD 모드 활성화 완료. `@planner` 를 호출해 기능을 스텝 단위로 분할하고 실패 테스트를 작성하세요." 안내.
- **수정 대상 파일**: `project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md`.
- **참조 문서**: `skills/rgr.md` (TDD Red-Green-Refactor 절차) (`pilot/skills/tdd/SKILL.md:28`).

---

## `/pilot:characterize`

레거시 코드의 현재 동작을 spec 으로 포착하는 characterization 모드 전환 (`pilot/skills/characterize/SKILL.md:10`).

- **인자** (`pilot/skills/characterize/SKILL.md:14`): `(빈 문자열)` 또는 `on` → ON, `off` → OFF.
- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/characterize/SKILL.md:18-22`).
- **동작** (`pilot/skills/characterize/SKILL.md:34-49`):
  1. `workspace/projects/{PROJECT}/.agent-state.yml` Read.
  2. 파일 없거나 schema < `v1.1` → "프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도" 출력 후 종료.
  3. 모드 전환:
     - **on**: `mode: characterize` 라인 추가 (기존 `mode:` 키 있으면 값 교체).
     - **off**: `mode:` 라인 제거 또는 `mode: null`.
  4. 결과 안내 — `mode: {characterize|null}`, `tdd: {true|false}` 표시 + 참조 `${CLAUDE_PLUGIN_ROOT}/skills/context/modes/characterize.md`.
- **주의** (`pilot/skills/characterize/SKILL.md:52-56`):
  - `tdd: true` + `mode: characterize` 동시 → characterize 우선 (Red 계약 대신 Characterization Contract).
  - **Characterization 사이클 중 `{source_root}` 수정은 Evaluator 가 반려**. 리팩터하려면 먼저 `/pilot:characterize off` 로 복귀.
  - 정본 절차는 `pilot/skills/context/modes/characterize.md`. 본 스킬은 **상태 전환 명령** 일 뿐 절차 정의가 아님.
