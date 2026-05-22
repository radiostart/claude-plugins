# Pilot 시작하기 — Deep Walkthrough

이 가이드는 샘플 저장소인 `_input/python-sample/`를 사용하여 `init` → `learn` → `project` → `create-feature` → `planner` → `critic`으로 이어지는 Cycle을 직접 진행합니다. 마지막에는 선택 단계로 **Characterize 모드**도 함께 살펴봅니다.

!!! tip "더 빠른 시작을 원하는 경우"
    Pilot이 어떤 도구인지 빠르게 확인하고 싶다면 [Quick Start](quick-start.md)를 권장합니다. 단 3개의 명령어로 첫 Plan까지 작성할 수 있습니다. 본 가이드는 실제 project에 Pilot을 도입하려는 사용자를 대상으로 합니다.

---

## 사전 준비

본 가이드는 샘플 저장소를 복제하여 진행합니다. 플러그인 캐시에 있는 샘플을 작업 디렉터리로 복사합니다.

```bash
# ${CLAUDE_PLUGIN_ROOT}는 플러그인 캐시 경로입니다. (echo $CLAUDE_PLUGIN_ROOT로 확인 가능)
cp -r "${CLAUDE_PLUGIN_ROOT}/tests/fixtures/v0.1.0-baseline/_input/python-sample" \
       /tmp/pilot-tutorial

cd /tmp/pilot-tutorial
```

이후 모든 명령어는 `/tmp/pilot-tutorial/` 디렉터리를 기준으로 실행합니다.

---

## Step 1: 워크스페이스 초기화 (`/pilot:init`)

```
/pilot:init
```

**기대 출력:**

```
워크스페이스 초기화 완료
Workspace: /tmp/pilot-tutorial/workspace

파일 상태:
  workspace/STATE.md                    created
  workspace/context/MANIFEST.md         created
  workspace/context/config.md           created

wizard 결과:
  언어 감지: 1개 자동 주입 (Python)
  scope 후보: 2개 매핑 (models, services)
  Ignore baseline: 10개 추가
... (생략)
```

wizard가 `config.md` 파일의 `## learn 언어 패턴` 표에 Python 의존성 추출 패턴을 주입하고, `## scope 카테고리` 표에는 `models/`와 `services/` 매핑을 자동으로 입력합니다.
주입되는 패턴 텍스트는 `features/01 default` 표의 해당 언어 행 전체를 인용한 것입니다.

!!! note
    wizard가 자동으로 정보를 입력합니다. 폴더 매핑이 잘못된 경우에는 [Troubleshooting (2)](#2-wizard-잘못-매핑-정정-경로)을 참고하여 수정하시기 바랍니다.

---

## Step 2: 도메인 학습 (`/pilot:learn`)

```
/pilot:learn main.py
```

**기대 출력:**

```
Phase 1 — 도메인 도출: python-sample
Phase 2 — Inventory
  발견 파일 5개 (services 2 · models 2 · routes 1 · 기타 0)
  진입점: main.py  추적 깊이: 2  도메인: python-sample

위 범위로 진행할까요?
  a) 그대로 진행   b) 좁히기 ...   c) 도메인명 변경   d) 중단
... (생략)
```

`a`를 선택하면 Phase 3부터 5까지 자동으로 진행됩니다. **생성되는 산출물:**

```
workspace/context/python-sample/
├── index.md      # 도메인 요약 및 file:line 인용 표
└── inventory.md  # 역할별 파일 분류 및 public interface 목록
```

---

## Step 3: 프로젝트 생성 (`/pilot:project`)

```
/pilot:project python-sample-demo
```

**기대 출력:**

```
프로젝트 활성화: python-sample-demo

생성된 파일:
  workspace/projects/python-sample-demo/project.md
  workspace/projects/python-sample-demo/prompts/planner.md
  workspace/projects/python-sample-demo/prompts/generator.md
  workspace/projects/python-sample-demo/prompts/evaluator.md

STATE.md: | project | python-sample-demo | 진행중 |
doctor: all checks passed
```

**생성된 디렉터리 구조:**

```
workspace/projects/python-sample-demo/
├── project.md
├── .agent-state.yml
└── prompts/
    ├── planner.md
    ├── generator.md
    └── evaluator.md
```

---

## Step 4: 첫 feature spec 작성 (`/pilot:create-feature`)

Planner를 호출하기 전에 feature spec 파일이 작성되어 있어야 합니다.

```
/pilot:create-feature "user 모델에 email 필드 추가"
```

**기대 출력:**

```
features/01-user-email-field.md 생성 완료

Open Questions (자동 생성):
  (a) 같은 도메인 추가 read — models/user.py
  (b) cross-domain 산출물 부재 — (없음)
  (c) 외부 spec 부재 — (없음)
  (d) 비즈니스 결정 — email 중복 허용 여부
```

**생성 파일:** `workspace/projects/python-sample-demo/features/01-user-email-field.md`

`features/11` 양식에 정의된 Open Questions 4개 카테고리 템플릿이 자동으로 주입됩니다. 답변하기 모호한 항목은 `(없음)`으로 유지한 채 Planner에게 분석과 설계를 위임할 수 있습니다.

---

## Step 5: 첫 plan 작성 (`@pilot-planner`)

```
@pilot-planner — features/01-user-email-field.md 기준으로 plan 작성해줘
```

**기대 출력:**

```
features/01-user-email-field.plan.md 저장 완료

plan-validate: exit 0 (valid)

변경 파일:
  models/user.py          — email 필드 추가
  services/user_service.py — validate_email 로직 추가
```

Plan 파일(`features/01-user-email-field.plan.md`)이 생성되면 1차 목표가 달성된 것입니다. 다음 단계로 설계의 결함을 찾기 위한 **Adversarial 검증**을 수행합니다.

---

## Step 6: plan 검증 (`@pilot-planner-critic`)

```
@pilot-planner-critic
```

Planner와 동일한 context를 기반으로 하되, 정반대의 관점에서 검증을 수행합니다. Planner가 **설계**를 담당한다면, Critic은 **반론과 잠재적 결함 도출**을 담당합니다. `premise`, `scope`, `edge-case`, `alternative`, `risk` 등 5가지 카테고리로 검증을 수행한 후,

```
features/01-user-email-field.plan.critic.md
```

파일에 그 결과를 기록합니다. 발견된 이슈들은 `severity` 수준에 따라 `blocking`, `suggestion`, `nit` 개수로 분류되어 보고됩니다.

**Critic의 책임 경계:** Critic은 Plan이나 코드를 **직접 수정하지 않습니다**. 사용자는 제기된 이슈를 검토하여 반영 여부를 결정하고, `@pilot-planner`를 다시 호출하여 조율 및 합의 과정을 거치게 됩니다. 자세한 사항은 [Critic 활용 How-to](../how-to/critic-review.md) 가이드를 참고하시기 바랍니다.

단순하고 명확한 변경 사항인 경우 Critic 검증 단계를 생략하고 바로 `@pilot-generator`로 진행할 수 있습니다. 단, **단계의 생략은 항상 사용자가 최종 결정**합니다.

---

## Step 7 (선택): Characterize 모드 — 레거시 코드 안전망

앞서 설명한 Step 4~6은 별도의 모드를 활성화하지 않은 **표준** Cycle이었습니다. 이번 단계에서는 실무에서 유용하게 사용되는 **Characterize 모드**를 알아봅니다.
Characterize 모드는 **테스트 코드가 없는 기존 레거시 코드**를 리팩터링하기 전에, 현재 동작 방식을 그대로 테스트 코드로 고정하여 안전망을 마련해 주는 기능입니다.

!!! warning "수행 순서에 대한 주의사항"
    Characterize는 하나의 **모드**이므로, `@pilot-planner`를 호출하기 **전**에 먼저 활성화해야 합니다. 대상이 레거시 코드였다면, 본 가이드의 **Step 5(첫 Plan 작성) 단계**에서 Characterize 모드를 켰어야 합니다. 아래에서는 이를 별도의 feature로 구성하여 **모드 활성화 → create-feature → planner 호출** 순서로 실습을 진행합니다. 신규 기능 개발만 필요한 경우에는 이 단계를 건너뛰셔도 됩니다.

### 모드 활성화

```
/pilot:characterize
```

**기대 출력:**

```
characterize 모드 ON.

- mode: characterize
- tdd: false

이후 @pilot-planner / @pilot-generator / @pilot-evaluator 호출 시 characterize.md 절차가 적용됩니다.
```

`.agent-state.yml` 파일에 `mode: characterize` 설정이 기록됩니다. 이후 동일한 Agent들을 호출하더라도 산출물의 형태가 달라집니다.

### 동작 포착용 feature 생성 및 Planner 실행

```
/pilot:create-feature "main.py 의 현재 출력 동작 포착"
@pilot-planner
```

Step 5와 달리, Planner는 자유로운 형식의 Plan 대신 **Characterization Contract**(입력 값 / 현재 출력=빈칸 / 관찰된 Side Effect) 양식을 생성합니다. '현재 출력' 결과 값은 Planner가 예측하여 작성하지 않고 비워두며, 다음 단계인 `@pilot-generator`가 실제 코드를 실행하여 값을 채우게 됩니다.

이후 `@pilot-generator`(소스 코드 수정 없이 테스트 코드만 작성) → `@pilot-evaluator`(코드 수정 없이 작성된 테스트 검증) 과정을 완료하면, `main.py` 파일의 현재 동작이 테스트 코드로 안전하게 고정됩니다.

### 모드 비활성화

```
/pilot:characterize off
```

테스트 안전망이 확보되면 Characterize 모드를 해제하고, 표준(또는 TDD) Cycle로 전환하여 본격적인 리팩터링을 진행할 수 있습니다.

!!! note
    적용 시점 판단과 전체 작업 흐름에 대한 상세 정보는 [Characterize 모드 How-to](../how-to/characterize-mode.md) 가이드를 참고하시기 바랍니다.

---

## 다음 단계

본 Cycle을 완성도 있게 마무리하려면 다음과 같이 진행합니다.

```
@pilot-planner          # 조율 및 합의 표를 채우며 Plan 수정 (Critic 피드백 반영)
@pilot-generator        # Plan 기반 소스 코드 구현 및 테스트 작성
@pilot-evaluator        # 구현된 코드의 완성도 검증 및 체크리스트 점검
```

**함께 확인하면 좋은 가이드:**

- **How-to:** [TDD 모드 활성화](../how-to/tdd-mode.md) · [Critic 활용](../how-to/critic-review.md) · [Doctor 진단 및 마이그레이션](../how-to/doctor-migration.md)
- **Reference:** [에이전트](../reference/agents/index.md) · [스킬](../reference/skills/index.md) · [도구](../reference/tools/index.md)
- **Explanation:** [에이전트 흐름](../explanation/agent-flow.md) · [모드](../explanation/modes.md)

!!! note "cross-domain 시나리오"
    `secondary-domain/` 서브 디렉터리를 포함하는 샘플 저장소를 활용하여 진행 중인 경우, 본 가이드를 완수한 뒤 [외부 도메인 연동](../how-to/cross-domain-learn.md) 단계로 진행해 주시기 바랍니다.

---

## Troubleshooting

### 1. config.md fallback 동작

**증상:** wizard를 건너뛰거나(skip) 비어 있는 workspace에서 `/pilot:learn`을 호출할 때 언어 패턴이 감지되지 않는 현상 (`## learn 언어 패턴` 표가 비어 있음).

**해결 방법:**

```bash
cat workspace/context/config.md   # 설정 파일 내용 확인
```

`/pilot:doctor` 명령어로 `OH-1` 진단 항목을 확인한 뒤, config 표가 비어 있는 경우 `/pilot:init` 명령어를 다시 실행합니다. (이미 `exists` 상태인 `config.md` 파일이 존재하면 wizard가 실행되지 않고 skip될 수 있으므로, 기존 파일을 삭제한 뒤 재시행해야 합니다.)

---

### 2. wizard 잘못 매핑 정정 경로 { #2-wizard-잘못-매핑-정정-경로 }

**증상:** wizard 실행 결과 "scope 후보: M개 매핑 ({폴더목록})" 항목에 `controllers/`와 같이 도메인 분류와 무관한 폴더가 포함되는 현상. 이는 wizard가 파일 빈도가 1 이상인 폴더를 자동으로 매핑하는 탐색 규칙을 가지고 있기 때문입니다. (샘플 저장소에서는 발생하지 않으나, 실제 서비스 저장소에서 나타날 수 있습니다.)

**해결 방법:**

`workspace/context/config.md` 파일을 수동으로 편집합니다.

1. `## scope 카테고리` 표에서 오인식된 행 (예: `| ## Controllers | ... |`)을 제거합니다.
2. `## Ignore` 표에 제외할 경로 패턴(예: `controllers/`)을 추가합니다.

```
/pilot:doctor    # schema 검증 수행 — 오류가 없으면 PASS
```

---

### 3. learn H2 매칭 실패

**증상:** `/pilot:learn` Phase 5 단계에서 `MANIFEST.md` 파일 내의 `## 도메인 분류` 헤더나 표를 인식하지 못하여 도메인이 정상적으로 등록되지 않는 현상.

**해결 방법:**

```bash
grep "^##" workspace/context/MANIFEST.md   # 헤더 형식 확인
```

`## 도메인 분류` 섹션이 누락되었거나 오탈자가 있는 경우:

```
/pilot:doctor    # 헤더 정합성 검사 — 오류 보고 확인
```

doctor 진단 도구가 헤더 불일치를 보고하면, `MANIFEST.md` 파일을 직접 열어 `## 도메인 분류` 헤더 명칭을 올바르게 수정합니다. 이때 `workspace/context/config.md` 파일의 `## learn 언어 패턴` 섹션 정합성도 같이 검증하는 것을 권장합니다.

---

### 4. STATE.md 누락

**증상:** `@pilot-planner` 호출 시 "활성 프로젝트 없음" 또는 ".agent-state.yml 누락" 오류 메시지가 발생하는 현상.

**해결 방법:**

```
/pilot:project python-sample-demo
```

`/pilot:project` 명령어는 멱등성(idempotent)이 보장되어 여러 번 수행해도 안전합니다. 명령어 실행 후 파일 존재 여부를 확인합니다.

```bash
ls workspace/projects/python-sample-demo/.agent-state.yml
```

해당 파일이 정상적으로 생성된 것이 확인되면, `@pilot-planner`를 다시 호출합니다.

---

### 5. generator orchestrate-load 누락

**증상:** `@pilot-generator`가 context 로딩 단계를 건너뛰거나 "wrapper protocol 위반" 오류를 발생시키는 현상.

**해결 방법:**

generator wrapper의 첫 번째 단계(step 1)에서 `orchestrate-load.py`가 선행 실행되어야 합니다.

```bash
# 플러그인을 최신 버전으로 업데이트한 후 세션을 재시작합니다.
pilot-update    # 또는: /plugin update pilot@claude-plugins
```

동시에 `workspace/projects/{PROJECT}/project.md` 파일의 `## 에이전트 간 전달사항` 섹션에 orchestrate-load 설정이 누락되지 않았는지 함께 확인합니다.
