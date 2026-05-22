# Quick Start

설치된 pilot 으로 *첫 plan* 까지 가는 가장 짧은 경로입니다. 3 명령으로 끝납니다.

!!! info "전제"
    - Claude Code 가 설치되어 있고 `pilot@radiostart-plugins` 가 등록돼 있다.
    - 작업할 코드 저장소에서 Claude Code 를 띄운 상태이다.

## 1. 워크스페이스 초기화

```bash
/pilot:init
```

대화형 wizard 가 실행되어 `workspace/` 디렉토리를 만듭니다.

```
workspace/
├── STATE.md                       # "활성 프로젝트" 표 (현재 비어있음)
└── context/
    ├── MANIFEST.md                # 도메인 진입 파일 색인
    ├── config.md                  # 언어·도구 기본값
    └── shared/                    # identity·instincts·guardrails SSOT
```

wizard 는 언어(Ruby/Python/TypeScript 등)를 묻고 그 답을 `config.md` 에 기록합니다. 한 번만 실행하면 됩니다.

## 2. 첫 프로젝트 생성

```bash
/pilot:project MyFirstFeature
```

`workspace/projects/MyFirstFeature/` 가 만들어지고 `STATE.md` 가 갱신되어 이 프로젝트가 *활성* 상태가 됩니다.

이 단계에서 wizard 가 묻는 것:

- **도메인** — 이 프로젝트가 만지는 코드의 도메인 (예: `coupon_service`, `auth`, `billing`).
- **TDD 모드** 여부 — Red→Green→Refactor 강제 여부 (기본: `false`).

답한 결과는 `.agent-state.yml` 에 기록됩니다:

```yaml
schema: v1.2
analyzed: false
tdd: false
domain: my-domain
plugin_version: "0.5.0"
```

## 3. 첫 feature 추가 + plan 작성

feature 명세를 한 줄로 추가합니다:

```bash
/pilot:create-feature "사용자 프로필 이메일 필드 추가"
```

`features/01-user-profile-email-field.md` 가 prompt-origin 템플릿으로 생성되고, `project.md` 와 `prompts/planner.md` 가 자동 동기화됩니다.

이제 planner 를 호출합니다 — `@` 로 subagent 명시 호출:

```
@pilot-planner
```

planner 가 `workspace/` 컨텍스트를 로드하고, feature 명세를 읽어 *구현 계획* 을 작성합니다:

```
features/01-user-profile-email-field.plan.md
```

확인 후 다음 중 하나를 호출합니다:

- `@pilot-planner-critic` — 권장. plan 을 챌린지해 `.plan.critic.md` 에 기록.
- `@pilot-generator` — critic 을 건너뛰고 바로 구현 (trivial 변경에서만).

## 다음 단계

- :material-tools: How-to:
    - [Critic 활용 — planner 결과를 반론 검증](../how-to/index.md)
    - [TDD 모드 활성화](../how-to/index.md)
- :material-book-open-variant: Reference:
    - [에이전트 — pilot-planner / -critic / -generator / -evaluator](../reference/index.md)
    - [스킬 — `/pilot:*` 13 종](../reference/index.md)

!!! tip "막혔다면"
    `/pilot:doctor` 가 `workspace/` 무결성과 schema 버전을 점검하고 마이그레이션 안내를 띄웁니다.
