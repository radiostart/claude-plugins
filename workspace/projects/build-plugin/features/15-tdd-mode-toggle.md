# #15 TDD 모드 사후 토글 (`/pilot:tdd on|off`)

> source: design-pilot-review-2026-05-20.md (Tier 2 — 운영 UX 갭)

## 요구사항

- **조건**: 현재 [`/pilot:tdd`](../../../../pilot/skills/tdd/SKILL.md) 는 단방향 활성화만 지원 (project.md `## 제한사항` 에 TDD 문구 주입 + prompts/*.md 갱신). off 전환 시 사용자가 ① `.agent-state.yml` 의 `tdd:` 플래그 수동 편집, ② project.md TDD 문구 수동 제거, ③ prompts/*.md TDD 영역 수동 복원을 각자 해야 함 → 실수 유발 + UX 단절. 현재 `tdd on` 은 tdd-activation §5 가 `.agent-state.yml` `tdd: true` 를 갱신함. 그러나 `tdd off` 분기 자체가 부재하여 비활성화 시 state.yml 가 stale 상태로 남는다.
- **트리거**: `/pilot:tdd on` `/pilot:tdd off` `/pilot:tdd` (인자 없으면 현재 상태 보고).
- **기대결과**: 단일 명령으로 ① `.agent-state.yml tdd:` 토글, ② project.md `## 제한사항` + `## 에이전트 호출 흐름` 의 TDD 문구 주입/제거, ③ prompts/{planner,generator,evaluator}.md 의 TDD 섹션 주입/제거 — 세 산출물이 일관된 상태로 동기화.

## 비즈니스 규칙

- **명령 형식**:
  - `/pilot:tdd on` — 활성화 (현재 동작과 동등 + state.yml 갱신).
  - `/pilot:tdd off` — 비활성화 (전체 복원).
  - `/pilot:tdd` (인자 없음) — 현재 상태 보고: `.agent-state.yml tdd:` 값 + project.md TDD 문구 존재 여부 + prompts 의 TDD 섹션 존재 여부. 셋이 일치하지 않으면 WARN 출력 후 `--fix` 안내.
  - `/pilot:tdd --fix` — 3 산출물 정합성 강제 동기화 (state.yml 값을 진실로 간주).
- **on 동작 (활성화)**:
  - `.agent-state.yml tdd: true` 로 설정 (false 또는 미존재면 추가).
  - project.md `## 제한사항` 에 [tdd-activation.md](../../../../pilot/skills/context/modes/tdd-activation.md) §1-1 문구 주입 (이미 있으면 skip — idempotent).
  - project.md `## 에이전트 호출 흐름` 을 TDD 버전 (Red-Green-Refactor) 으로 교체. 기존 비TDD 버전을 백업 코멘트 (`<!-- pilot-tdd-original-flow ... -->`) 로 보존.
  - prompts/{planner,generator,evaluator}.md 의 TDD 영역 갱신 ([tdd-activation.md](../../../../pilot/skills/context/modes/tdd-activation.md) §2~4 literal).
- **off 동작 (비활성화)**:
  - `.agent-state.yml tdd: false` 로 설정.
  - project.md `## 제한사항` 에서 TDD 문구 1단락 제거 (literal 매칭 — 사용자 추가 문구는 보존).
  - project.md `## 에이전트 호출 흐름` 의 TDD 버전을 원본 표준 흐름으로 복원. 백업 코멘트 (`<!-- pilot-tdd-original-flow ... -->`) 가 있으면 그 내용으로 복원, 없으면 [project.md.template](../../../../pilot/skills/context/lifecycle/setup/templates/project.md.template) (또는 동등 위치) 의 표준 섹션으로 복원.
  - prompts/{planner,generator,evaluator}.md 의 TDD 섹션 제거 (literal 매칭).
- **idempotency**:
  - `on` 두 번 호출 → 두 번째는 no-op (모든 항목 이미 적용됨).
  - `off` 두 번 호출 → 두 번째는 no-op.
  - 부분 적용 상태 (state.yml=true 이지만 project.md TDD 문구 없음) 에서 `on` → 누락 항목만 보완 (현재 [tdd/SKILL.md](../../../../pilot/skills/tdd/SKILL.md) 2단계의 "이미 적용된 항목은 건너뛴다" 와 일관).
- **상태 보고 출력 (인자 없음)**:
  ```
  TDD 모드 상태: {ON|OFF|INCONSISTENT}

  - .agent-state.yml tdd:      {true|false|missing}
  - project.md TDD 제한사항:    {present|absent}
  - prompts TDD 섹션:           {3/3|N/3 (...)}

  {INCONSISTENT 시: WARN — /pilot:tdd --fix 로 동기화하세요}
  ```
- **doctor 연계**: `/pilot:doctor` 의 정합성 점검에 "tdd 3-way 일치" 룰 추가 (state.yml + project.md + prompts). 불일치 시 WARN, `--fix` 시 `/pilot:tdd --fix` 호출.
- **TDD off 후 작성된 plan/구현 보존**: 본 토글은 **메타 모드** 만 전환. features/NN-{slug}.md `.plan.md` 등 작성된 산출물은 손대지 않음. 사용자 책임으로 모드 전환 후 신규 plan 부터 새 모드 적용.

## 예외 케이스

- **신규 프로젝트가 `--tdd` 로 생성됨 (`/pilot:project NAME --tdd`)**: state.yml `tdd: true` 가 생성 시점에 이미 설정. `/pilot:tdd on` 호출 시 no-op + INFO 1줄.
- **`tdd-activation.md` 의 literal 문구가 v0.2 → v0.3 사이 변경됨**: 기존 프로젝트의 project.md TDD 단락이 구버전 문구일 수 있음. `off` 시 literal 매칭 실패 → WARN 출력 + 사용자에게 수동 제거 안내. v2 에서 fuzzy 매칭 도입 고려.
- **`<!-- pilot-tdd-original-flow ... -->` 백업 코멘트 누락**: 구버전 (본 feature 도입 전) 에 `on` 한 프로젝트는 백업이 없음. `off` 시 template 의 표준 섹션으로 복원 + INFO 1줄 ("원본 백업 없음 — template 표준 흐름으로 복원").
- **사용자가 prompts/*.md 의 TDD 섹션을 수동 수정**: literal 매칭 영역 외 사용자 수정은 보존. literal 매칭된 영역만 교체/제거.
- **state.yml schema 변경**: 현재 v1.2. `tdd:` 필드는 v1.0 부터 존재. schema 변동 시 features/04 의 doctor 검증이 사전 차단.

## 관련 파일 범위

- **변경**: `pilot/skills/tdd/SKILL.md`
  - "수행 절차" 를 on/off 두 분기로 재구성.
  - `--fix` 옵션 동작 명문화.
  - 인자 없는 호출 시 상태 보고 포맷 명시.
- **변경**: `pilot/skills/context/modes/tdd-activation.md`
  - off 시 복원 절차 (literal 매칭 + 백업 코멘트 활용) 1 단락 추가.
  - on 시 백업 코멘트 (`<!-- pilot-tdd-original-flow ... -->`) 주입 절차 1 단락 추가.
- **변경**: `pilot/skills/doctor/SKILL.md` + `pilot/tools/doctor.py`
  - "tdd 3-way 일치" 룰 1 항 추가. INCONSISTENT 시 WARN. `--fix` 시 `/pilot:tdd --fix` 위임.
- **변경**: `pilot/skills/project/SKILL.md`
  - 이미 `pilot/skills/project/SKILL.md:116-118` 가 tdd-activation 위임 → state.yml `tdd: true` 갱신 정상. patch 불필요 (Q6 트레이스 결과).
- **회귀 픽스처**: features/00 의 분기 케이스 추가 — `tdd-on/expected/`, `tdd-off/expected/` (TDD 토글 후 산출물 일관성 검증).
- **사용자 영향**: 기존 `--tdd` 로 생성된 프로젝트는 백업 코멘트 부재 → `off` 시 INFO 안내. 신규 프로젝트는 영향 없음. `tdd` 명령은 그대로 backward-compatible (현재 단방향 활성화는 `on` 인자 추가 형태로 흡수).
