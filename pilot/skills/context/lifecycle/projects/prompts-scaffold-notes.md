# prompts/*.md 스캐폴딩 공통 노트

`workspace/projects/{PROJECT}/prompts/` 하위 `planner.md`·`generator.md`·`evaluator.md` 공통 가이드. 각 파일 상단에서 본 문서를 한 줄 링크로 참조한다.

## 주의 — 이 파일들은 subagent 정의가 아니다

`workspace/projects/{PROJECT}/prompts/*.md` 와 플러그인 `${CLAUDE_PLUGIN_ROOT}/agents/*.md` 는 **이름은 같지만 성격이 다르다**:

| 위치 | 정체 | `@pilot-planner` 호출 시 | 편집 효과 |
|---|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/agents/{phase}.md` | **Claude Code subagent 정의** (frontmatter `name:`, `tools:`) | ✅ 실제 실행되는 wrapper | 플러그인 업데이트로만 변경 |
| `workspace/projects/{PROJECT}/prompts/{phase}.md` | **프로젝트 컨텍스트 문서** (마크다운) | wrapper 가 Read 로 내용만 참고 | 다음 `@{phase}` 호출에 반영 |

즉 프로젝트 쪽 파일은 Claude Code subagent 레지스트리에 등록되지 않으며, 단독으로는 아무것도 실행하지 않는다. wrapper 가 진입 시 `tools/orchestrate-load.py` 결과를 따라 Read 툴로 불러들이는 **입력 자료**일 뿐.

**혼선 방지 규칙:**

- 파일 **편집** 은 가능하지만 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 에서 덮어쓰인다. 커스텀은 그 외 섹션에 둘 것.
- wrapper 의 **동작 자체를 바꾸려면** 플러그인을 수정해야 한다 (프로젝트 파일로는 불가).
- tool 권한·model 도 플러그인 쪽 frontmatter 에서만 선언된다.

---

## 파일의 역할

- **스캐폴딩 템플릿** — `/pilot:project` 가 `example/` 에서 복사한 초기본.
- 섹션명·순서는 `/pilot:analyze` 주입 대상과 동기화되어 있다. **임의 변경 금지**.

## analyze-managed 섹션

`<!-- [analyze-managed] -->` 주석이 달린 섹션은 `/pilot:analyze` 가 관리한다.

- 다음 analyze 실행 시 **덮어쓰기 대상** — 수동 편집 내용은 유실된다.
- 커스텀 내용은 주석이 없는 **별도 섹션** 에 작성한다 (예: `## 주의사항`, `## 구현 패턴`).

## wrapper 분기 판정

래퍼 (`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator`) 의 pre/post-analyze 분기는 `.agent-state.yml` 의 `analyzed` 필드로 판정.

- 스키마 상세: [state-schema.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/state-schema.md)

## TDD 모드

`/pilot:tdd` 활성화 시 각 파일에 Red/Green/Refactor 섹션이 자동 주입된다.

- 상세: [tdd-activation.md](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/tdd-activation.md)

## 각 파일 고유 책임

| 파일 | 로드 주체 | 핵심 섹션 |
| ---- | --------- | --------- |
| `planner.md` | `@pilot-planner` 래퍼 | `## 기능별 사전 확인 사항` (analyze-managed) |
| `generator.md` | `@pilot-generator` 래퍼 | `## 컨텍스트 로드`, `## 핵심 서비스/모델` (둘 다 analyze-managed) |
| `evaluator.md` | `@pilot-evaluator` 래퍼 | `## 기능 완성도`, `## 프로젝트 고유 항목` (analyze-managed) |

플래닝 공통 가이드는 래퍼 `.claude/agents/pilot-planner.md` 의 `## 플래닝 프로세스 (공통 가이드)` 섹션. 프로젝트 planner.md 에 복사 금지.
