# Quick Start

설치된 Pilot을 사용하여 첫 Plan을 작성하기까지의 가장 빠른 경로입니다. 단 3개의 명령어만으로 완료됩니다.

!!! info "전제 조건"
    - Claude Code가 설치되어 있고, `pilot@radiostart-plugins`가 등록되어 있어야 합니다.
    - 대상 소스 코드 저장소에서 Claude Code를 실행한 상태여야 합니다.

---

## 1. workspace 초기화

```bash
/pilot:init
```

대화형 wizard가 실행되어 `workspace/` 디렉터리를 생성합니다.

```
workspace/
├── STATE.md                       # 활성 project 목록 (초기에는 비어 있음)
└── context/
    ├── MANIFEST.md                # 도메인 진입 파일 색인 (인덱스)
    └── config.md                  # 언어 및 도구 기본 설정
```

wizard가 사용 언어(Ruby, Python, TypeScript 등)를 자동 감지하여 그 결과를 `config.md`에 기록합니다. 최초 한 번만 실행하면 됩니다.

---

## 2. 첫 project 생성

```bash
/pilot:project MyFirstFeature
```

`workspace/projects/MyFirstFeature/` 디렉터리가 생성되고, `STATE.md` 파일이 갱신되면서 해당 project가 **활성(Active)** 상태가 됩니다.

프로젝트 상태는 `.agent-state.yml` 파일에 기록됩니다.

- **도메인(domain):** 이 단계에서는 묻지 않습니다. 초기값은 `null`이며, `/pilot:analyze` 진입 시 사용자 확인을 거쳐 확정됩니다.
- **TDD 모드:** `/pilot:project MyFirstFeature --tdd` 플래그로 활성화합니다 (기본값: `false`).

```yaml
schema: v1.2
analyzed: false
tdd: false
domain: null
plugin_version: "{현재 플러그인 버전}"
```

---

## 3. 첫 feature 추가 및 Plan 작성

새로운 feature 명세를 한 줄 명령어로 추가합니다.

```bash
/pilot:create-feature "사용자 프로필 이메일 필드 추가"
```

`features/01-user-profile-email-field.md` 파일이 템플릿 형태로 생성되며, `project.md` 및 `prompts/planner.md`가 자동으로 동기화됩니다.

이제 Planner를 호출합니다. Claude Code의 `@` 기능을 활용하여 지정된 Agent를 명시적으로 호출합니다.

```
@pilot-planner
```

Planner가 workspace context를 로딩하고, feature 명세를 분석하여 **구현 계획(Plan)**을 수립합니다.

```
features/01-user-profile-email-field.plan.md
```

생성된 Plan을 검토한 후, 목적에 맞게 다음 중 하나의 Agent를 호출합니다.

- `@pilot-planner-critic` (권장): 설계의 허점을 역으로 검증하여 `.plan.critic.md` 파일에 기록합니다.
- `@pilot-generator`: Critic 검증 단계를 생략하고 즉시 코드를 구현합니다. (매우 단순하고 명확한 변경 사항인 경우에만 권장)

---

## 다음 단계

- :material-tools: **How-to:**
    - [Critic 활용 (Planner 설계 교차 검증)](../how-to/critic-review.md)
    - [TDD 모드 활성화](../how-to/tdd-mode.md)
- :material-book-open-variant: **Reference:**
    - [에이전트 (pilot-planner / -critic / -generator / -evaluator)](../reference/index.md)
    - [스킬 (`/pilot:*`)](../reference/index.md)

!!! tip "문제 해결"
    진행 과정 중 오류가 발생하거나 막히는 경우, `/pilot:doctor` 명령어를 실행하십시오. workspace의 무결성과 schema 버전을 확인하여 문제 진단 및 마이그레이션 안내를 제공합니다.
