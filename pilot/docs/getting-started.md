# Pilot 시작하기 — 5분 완주

이 가이드는 더미 저장소 `_input/python-sample/` 를 따라 5분 안에 첫 plan 산출
(`features/01-{slug}.plan.md`) 까지 진행한다.

> **시작 전:** 사전 준비 완료 시점부터 Step 5 완료까지 stopwatch 측정을 권장한다.
> 5분 초과 시 어느 step 에서 막혔는지 `features/05-dogfooding.md` 로 피드백을 전달해 준다.
> 실측 책임은 별도 dogfooding feature 가 담당 — 본 가이드는 경로만 안내한다.

---

## 사전 준비

### gstack 설치 확인

pilot 은 gstack 이 설치된 환경에서만 동작한다 (CLAUDE.md `gstack (REQUIRED)` 룰).

```bash
test -d ~/.claude/skills/gstack/bin && echo "OK" || echo "MISSING"
```

`MISSING` 이면 아래 절차로 설치 후 Claude Code 재시작:

```bash
git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup --team
```

### 더미 저장소 복사

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

**이것이 이 가이드의 최종 목표다.** plan 파일
(`features/01-user-email-field.plan.md`) 이 생성되면 5분 완주에 성공한 것이다.

---

## 다음 단계

plan 이 준비됐으면 아래 순서로 구현·검토를 진행한다:

```
@pilot-generator   # plan 기반 코드 구현
@pilot-evaluator   # 구현 완성도 검토 + 체크리스트
```

**관련 features (현재 작업 중):**

- [TDD 모드 토글](../skills/tdd/SKILL.md)
  — 구현 완료 후 TDD 사이클로 전환하는 방법.
- [Doctor 진단](../skills/doctor/SKILL.md)
  — `/pilot:doctor` 로 워크스페이스 정합성을 자동 점검하는 방법.
- [SKILL 인덱스](../skills/context/INDEX.md) — 전체 스킬 목록.

> **cross-domain 시나리오**를 시도하는 경우 (`secondary-domain/` 서브트리 포함)
> — 단일 도메인 5분 완주 이후에 features/09 cross-domain 처리 가이드를 참조한다.

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

### 2. wizard 잘못 매핑 정정 경로

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

---

## timing 측정 가이드

사전 준비 완료 후 **Step 1 부터 Step 5 까지** stopwatch 로 측정을 권장한다. 목표: 5분 이내.

| Step | 작업 | 예상 소요 |
|------|------|-----------|
| 1 | `/pilot:init` | 30초~1분 |
| 2 | `/pilot:learn` (Phase 2 확인 포함) | 1~2분 |
| 3 | `/pilot:project` | 20초 |
| 4 | `/pilot:create-feature` | 30초 |
| 5 | `@pilot-planner` | 1~2분 |

5분 초과 시 어느 step 에서 막혔는지 `features/05-dogfooding.md` 로 피드백을 전달해 준다.
실측 자동화 인프라는 미구현 — 사용자의 직접 측정이 가이드 개선의 가장 빠른 경로다.
