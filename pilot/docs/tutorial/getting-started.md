# Pilot 시작하기 — Deep Walkthrough

이 가이드는 더미 저장소 `_input/python-sample/` 를 따라 *init → learn → project → create-feature → planner → critic* 의 한 사이클을 직접 돈다. 끝에 선택 Step 으로 **Characterize 모드** 도 짚는다.

!!! tip "더 짧은 경로"
    "이게 뭔지 모양만 보고 싶다" 면 [Quick Start](quick-start.md) 가 적합하다 — 3 명령으로 첫 plan 까지. 본 가이드는 *실제 프로젝트에 도입하려는* 사용자 대상.

---

## 사전 준비

이 가이드는 더미 저장소를 복사해 따라간다 — 플러그인 캐시의 샘플을 작업 디렉터리로 옮긴다:

```bash
# ${CLAUDE_PLUGIN_ROOT} = 플러그인 캐시 경로 (echo $CLAUDE_PLUGIN_ROOT 로 확인)
cp -r "${CLAUDE_PLUGIN_ROOT}/tests/fixtures/v0.1.0-baseline/_input/python-sample" \
       /tmp/pilot-tutorial

cd /tmp/pilot-tutorial
```

이후 모든 명령은 `/tmp/pilot-tutorial/` 기준이다.

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

wizard 가 `config.md` 의 `## learn 언어 패턴` 표에 Python 의존성 추출 패턴을,
`## scope 카테고리` 표에 `models/`·`services/` 매핑을 자동 주입한다.
패턴 텍스트는 features/01 default 표의 해당 언어 행 전체를 인용 주입한 것이다.

> wizard 가 자동 채움 — 잘못 매핑된 폴더가 있으면 [Troubleshooting (2)](#2-wizard-잘못-매핑-정정-경로) 참조.

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

`a` 선택 → Phase 3~5 자동 진행. **산출 파일:**

```
workspace/context/python-sample/
├── index.md      # 도메인 요약 + file:line 인용 표
└── inventory.md  # 역할별 파일 분류 + public interface 목록
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

**생성 폴더 트리:**

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

planner 호출 전 feature spec 파일이 필요하다.

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

산출 파일: `workspace/projects/python-sample-demo/features/01-user-email-field.md`

features/11 의 Open Questions 4 카테고리 템플릿이 자동 주입된다. 답하기 어려운
항목은 `(없음)` 으로 두고 planner 에게 위임해도 된다.

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

plan 파일 (`features/01-user-email-field.plan.md`) 이 생성되면 1차 목표 달성. 다음 step 으로 *adversarial 검증* 을 한 번 돌려 본다.

---

## Step 6: plan 검증 (`@pilot-planner-critic`)

```
@pilot-planner-critic
```

planner 와 같은 컨텍스트 위에서 정반대 관점으로 동작한다 — planner 가 *설계* 라면 critic 은 *반론·결함 찾기*. 5 카테고리 — `premise` · `scope` · `edge-case` · `alternative` · `risk` — 로 챌린지를 만들고:

```
features/01-user-email-field.plan.critic.md
```

에 결과를 기록한다. `severity` 별 `blocking` · `suggestion` · `nit` 개수가 보고된다.

**critic 의 책임 경계** — plan/코드를 *직접 수정하지 않는다*. 챌린지 검토 후 사용자가 어떤 항목을 채택할지 결정하고 `@pilot-planner` 재호출이 합의 표를 채운다. 자세히는 [Critic 활용 How-to](../how-to/critic-review.md) 참조.

trivial 한 변경에서는 critic 을 건너뛰고 바로 `@pilot-generator` 로 가도 된다 — 다만 *생략은 항상 사용자 결정*.

---

## Step 7 (선택): Characterize 모드 — 레거시 코드 안전망

여기까지가 표준 사이클이다. 실무에서 자주 쓰는 모드를 하나 더 짚는다 — **Characterize 모드** 는 *테스트 없는 기존 코드* 를 리팩터하기 전에, 그 코드의 *현재 동작* 을 테스트로 고정해 안전망을 만든다.

!!! note "건너뛰어도 되는 Step"
    신규 기능을 만드는 중이라면 이 Step 은 지나쳐도 된다. 테스트 없는 레거시 코드를 손볼 일이 생기면 그때 돌아오면 된다.

### 모드 켜기

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

`.agent-state.yml` 에 `mode: characterize` 가 기록된다. 이후 **같은 에이전트들** 을 그대로 호출하지만 산출물이 달라진다.

### 포착용 feature 추가 후 planner 실행

```
/pilot:create-feature "main.py 의 현재 출력 동작 포착"
@pilot-planner
```

Step 5 와 비교하면 — 같은 planner 인데 자유 형식 plan 이 아니라 **Characterization Contract** (입력 / 현재 출력=빈칸 / 관찰된 사이드 이펙트) 형식으로 나온다. "현재 출력" 은 planner 가 예측하지 않고 비워 두며, 다음 단계의 `@pilot-generator` 가 코드를 실제로 실행해 채운다.

이후 `@pilot-generator` (소스 미수정 + 테스트 작성) → `@pilot-evaluator` (소스 미수정·테스트 검증) 로 사이클을 마치면 `main.py` 의 현재 동작이 테스트로 고정된다.

### 모드 끄기

```
/pilot:characterize off
```

안전망이 확보되면 모드를 해제하고 표준(또는 TDD) 사이클로 돌아가 본격 리팩터를 진행한다.

> 시작 시점 판단·전체 절차는 [Characterize 모드 How-to](../how-to/characterize-mode.md) 에 자세히 있다.

---

## 다음 단계

본 사이클을 끝까지 돌리려면:

```
@pilot-planner          # 합의 표 채우면서 plan 수정 (critic 결과 반영)
@pilot-generator        # plan 기반 코드 구현
@pilot-evaluator        # 구현 완성도 검토 + 체크리스트
```

**자주 함께 쓰는 작업:**

- How-to: [TDD 모드 활성화](../how-to/tdd-mode.md) · [Critic 활용](../how-to/critic-review.md) · [Doctor 진단·마이그레이션](../how-to/doctor-migration.md)
- Reference: [에이전트](../reference/agents/index.md) · [스킬](../reference/skills/index.md) · [도구](../reference/tools/index.md)
- Explanation: [에이전트 흐름](../explanation/agent-flow.md) · [모드](../explanation/modes.md)

!!! note "cross-domain 시나리오"
    `secondary-domain/` 서브트리를 포함한 더미 저장소를 사용한 경우 — 본 가이드 완료 후 [외부 도메인 부트스트랩](../how-to/cross-domain-learn.md) 으로 진입.

---

## Troubleshooting

### 1. config.md fallback 동작

**증상:** wizard 를 skip 하거나 빈 workspace 에서 `/pilot:learn` 호출 시
언어 패턴이 인식되지 않는다 (`## learn 언어 패턴` 표가 비어있음).

**해결:**

```bash
cat workspace/context/config.md   # 표 내용 확인
```

`/pilot:doctor` 로 `OH-1` 항목 확인 후, config 표가 비어있으면 `/pilot:init` 재실행
(이미 `exists` 인 config.md 가 있으면 wizard skip — 파일을 삭제 후 재실행).

---

### 2. wizard 잘못 매핑 정정 경로 { #2-wizard-잘못-매핑-정정-경로 }

**증상:** 결과의 "scope 후보: M개 매핑 ({폴더목록})" 에서 `controllers/` 같이
도메인과 무관한 폴더가 잡혔다. 이는 wizard 가 빈도 ≥ 1 인 폴더를 자동 매핑하는
특성 때문이다 — 더미 저장소에서는 발생하지 않으나 자체 저장소에서 나타날 수 있다.

**해결:**

`workspace/context/config.md` 를 직접 편집:

1. `## scope 카테고리` 표에서 잘못된 행 (`| ## Controllers | ... |`) 삭제.
2. `## Ignore` 표에 해당 경로 패턴 추가 (예: `controllers/`).

```
/pilot:doctor    # schema 검증 — 오류 없으면 PASS
```

---

### 3. learn H2 매칭 실패

**증상:** `/pilot:learn` Phase 5 에서 `MANIFEST.md` 의 `## 도메인 분류` 표를
찾지 못하거나 도메인이 등록되지 않는다.

**해결:**

```bash
grep "^##" workspace/context/MANIFEST.md   # 헤더 확인
```

`## 도메인 분류` 가 없거나 오탈자이면:

```
/pilot:doctor    # 헤더 불일치 → ERROR 보고
```

doctor 가 헤더 불일치를 보고하면 MANIFEST.md 를 직접 편집해 `## 도메인 분류`
헤더를 정확히 맞춘다. `workspace/context/config.md` 의 `## learn 언어 패턴` 표도
함께 확인한다.

---

### 4. STATE.md 누락

**증상:** `@pilot-planner` 호출 시 "활성 프로젝트 없음" 또는
`.agent-state.yml 누락` 오류.

**해결:**

```
/pilot:project python-sample-demo
```

`/pilot:project` 는 idempotent (`exists` 분기로 안전). 실행 후 확인:

```bash
ls workspace/projects/python-sample-demo/.agent-state.yml
```

파일이 있으면 `@pilot-planner` 재호출.

---

### 5. generator orchestrate-load 누락

**증상:** `@pilot-generator` 가 컨텍스트 로드 단계를 skip 하거나
"wrapper protocol 위반" 오류가 발생한다.

**해결:**

generator wrapper 의 step 1 이 `orchestrate-load.py` 를 반드시 먼저 실행해야 한다.

```bash
# 플러그인 최신화 후 세션 재시작
pilot-update    # 또는: /plugin update pilot@claude-plugins
```

`workspace/projects/{PROJECT}/project.md` 의 `## 에이전트 간 전달사항` 섹션에서
orchestrate-load 관련 항목도 확인한다.
