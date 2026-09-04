# phase 전환 절차 (SSOT)

development ⇄ qa phase 전환의 단일 정의. `project`·`qa` 스킬이 본 파일을
참조한다 — 절차를 복붙하지 말 것 (drift 방지).

전환은 프로젝트의 `.agent-state.yml` **한 곳만** 갱신한다. phase 의 SSOT 는
`.agent-state.yml` 의 `phase` 필드이며, `STATE.md` 의 status 칸은 phase 를
비추지 않는다 — qa phase 에서도 `진행중` 을 유지한다 (status 는 project
생명주기 표시 전용).

## 공통 Edit 규칙

- `.agent-state.yml` 은 **Edit 도구만** 사용한다 (Write 금지 — 파일 전체
  덮어쓰기로 다른 필드 유실 위험).
- `phase:` 줄이 부재하면 (구버전 schema 케이스) `domain:` 줄 또는 `tdd:`
  줄 다음에 한 줄을 Edit 으로 삽입한다. `schema:` 줄은 손대지 않는다 (schema
  업그레이드는 `doctor --fix` 소관).
- `STATE.md` 는 **건드리지 않는다.** phase 전환은 status 칸을 바꾸지 않으며,
  활성 project 행은 [preamble.md](../shared/preamble.md) **P2** 규칙대로
  `진행중` 을 유지한다 (status 거울 폐지 — phase 는 `.agent-state.yml` 단독
  SSOT. 거울을 두면 두 파일 동기화 누락 시 drift 가 생기고, `진행중` 리터럴로
  활성 project 를 찾는 P1 이 깨진다).

> phase 카운트·결함 잔여 등 동적 정보는 STATE.md 에 기록하지 않는다 — 다건
> 추적의 SSOT 는 Jira UI 다 (잔여·우선순위·재오픈 현황). 로컬 보드뷰·카운트를
> 만들지 않는다 (SSOT 이중화 회피).

## to-qa (development → qa)

1. `.agent-state.yml`: `phase:` 줄을 `phase: qa` 로 교체 (부재 시 삽입).
2. `.agent-state.yml`: `qa_started_at:` 행을 현재 UTC ISO 8601
   (`date -u +%Y-%m-%dT%H:%M:%SZ`) 값으로 교체. 행이 없으면 `phase:` 줄 다음에
   `qa_started_at: "{timestamp}"` 한 줄을 삽입한다.
3. **idempotent**: 이미 `phase: qa` 면 phase 는 무변화, `qa_started_at` 만
   갱신한다 (마지막 진입 시점 기록 의도).

## to-development (qa → development)

1. `.agent-state.yml`: `phase:` 줄을 `phase: development` 로 교체 (부재 시
   `domain:` 또는 `tdd:` 줄 다음에 삽입).
2. `qa_started_at:` 은 **삭제하지 않고 보존**한다 (감사 이력 — 마지막 qa 진입
   시점). `qa/` 폴더도 **보존**한다.
3. **idempotent**: 이미 `phase: development` (또는 부재) 면 무변화, 다른 필드
   불변.
