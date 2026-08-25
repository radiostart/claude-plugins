---
name: qa
description: >-
  사용자가 `/pilot:qa {KEY}` 를 명시적으로 호출했을 때만 사용한다 — 대화에 Jira 티켓 링크·이슈 키가
  보이는 것만으로는 발동하지 않는다 (링크 공유·메모는 처리 요청이 아니다). Jira QA 결함 처리 모드 진입 — 활성
  project 의 qa/ 에서 결함 1건의 분석·수정 사이클을 시작한다 (이슈 키 인자 필수, `off` 로 development
  복귀). 다건 추적·잔여 현황·재오픈은 Jira UI 가 SSOT — 본 스킬은 보드뷰·다건 조회를 하지 않는다.
---

QA phase 결함 처리 모드를 활성화한다.

대상 Jira 키: $ARGUMENTS

**전제:**

- 활성 project 가 있어야 한다 (`/pilot:project {PROJECT}` 로 먼저 진입).
- phase 자동 전환은 수행 절차 3 참조 — 수동 전환이 필요할 때만 `/pilot:project {PROJECT} --qa`.
- 단발 운영 이슈는 `/pilot:issue` 를 사용한다 — project 컨텍스트가 끊겨도
  되는 핫픽스·장애 분석용. QA 결함은 project 컨텍스트가 필수이므로 본 스킬.

---

## 사전 확인 (fail-fast 순서)

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 을 수행하되,
아래 순서를 따른다 — **진입 게이트를 통과한 뒤에만 비용이 드는 P-1·P0 을
수행한다**:

1. 수행 절차 **1 (인자 검증)** — Read 없이 즉시 판정. `off` 면 1-A 로 분기.
2. 수행 절차 **2 (활성 project 확인)** — STATE.md 1회 Read 게이트.
3. 게이트 통과 후에만:
   - **P-1**: 진행 보드 선로딩 (다단계 스킬).
   - **P0**: 컨텍스트의 `MEMORY.md` 인덱스에서 인자의 Jira 키·주변 키워드와
     관련된 메모를 가려 본문을 Read 하여 과거 동일·유사 결함 처리 이력을
     컨텍스트에 반영.

게이트에서 종료가 확정된 호출(인자 없음·형식 오류·활성 project 없음)에는
P-1·P0 을 수행하지 않는다 — 곧 종료할 호출에 todo 보드·메모 Read 비용을
쓰지 않는다.

---

## 수행 절차

아래 순서대로 진행한다. 중간 단계에서 "다음 작업" 안내를 출력하지 않고 모든
단계를 마친 뒤 결과 출력에서 한 번만 안내한다.

### 1. 인자 검증 (필수)

- `$ARGUMENTS` 가 `off` (대소문자 무시) 이면 → **off 모드** (아래 "### 1-A. off 모드" 로 진행, 이후 단계 건너뜀).
- `$ARGUMENTS` 가 비어있으면 다음 메시지 출력 후 종료:

  ```
  Jira 이슈 키가 필요합니다. 예: /pilot:qa SHOP-1234
  ```

- `$ARGUMENTS` 가 `^[A-Z]+-\d+$` 형식을 만족하지 않으면 다음 메시지 출력 후
  종료 (`$ARGUMENTS` 는 실제 입력값으로 치환):

  ```
  Jira 키 형식 오류: '$ARGUMENTS'. 예: QAPRJ-1234
  ```

검증 통과 시 입력값을 `{KEY}` 로 사용한다.

### 1-A. off 모드 (phase 탈출)

`$ARGUMENTS == off` 일 때만 수행하며, 완료 후 즉시 종료한다 (KEY 검증·결함
처리·이후 모든 단계 건너뜀).

1. 수행 절차 **2 (활성 project 확인)** 수행.
2. 활성 project 의 `.agent-state.yml` 의 `phase` 확인:
   - `phase != qa` (development 또는 부재) → `"이미 development phase 입니다."` 출력 후 종료 (변경 없음).
   - `phase == qa` → 다음으로.
3. [phase-transition.md](../context/lifecycle/phase-transition.md) 의 `to-development` 절차 수행.
4. 다음 한 줄 출력 후 종료:

   ```
   qa → development phase 복귀. features/ 수정 가능.
   ```

off 모드는 결함 처리·Jira 조회를 하지 않는다.

### 2. 활성 project 확인

`workspace/STATE.md` 를 Read 한다.

- **파일이 없으면** (Read 실패) 아래 메시지를 출력하고 **즉시 종료**한다 —
  Glob·find·ls 등 추가 탐색을 하지 않는다 (미셋업은 정상 상태이지 진단 대상이
  아니다).
- 파일이 있으면 본문 표에 `| project | X | ... |` 행이 있는지 확인한다. 없으면
  같은 메시지를 출력하고 종료한다.

```
활성 project 가 없습니다. /pilot:project {PROJECT} 먼저 호출하세요.
```

행이 있으면 두 번째 컬럼 값을 `{PROJECT}` 로 사용한다.

> (P1 정식 절차 미사용 — qa 는 `mode=project` 행에만 진입 가능하므로 STATE.md
> 표를 직접 검사한다. issue 모드와 직교.)

### 3. phase 확인 및 자동 전환

`workspace/projects/{PROJECT}/.agent-state.yml` 를 Read 하여 `phase`
필드 값을 확인한다. `state-schema.md` 규칙에 따라 `phase` 필드 부재는
`development` 로 간주한다 (v1.2 이하 → v1.3 마이그레이션은 단순 필드
추가이므로 의미 변화 없음).

- `phase: qa` → 다음 단계로 진행.
- `phase: development` **또는 `phase` 필드 부재** → 자동으로 qa phase 로 전환
  후 진행:

  1. [phase-transition.md](../context/lifecycle/phase-transition.md) 의 `to-qa`
     절차를 수행한다 (`.agent-state.yml` 의 `phase: qa`·`qa_started_at` 갱신).
     STATE.md status 는 건드리지 않는다 — `진행중` 유지.

  2. 다음 한 줄을 출력한다:

     ```
     development → qa phase 자동 전환됨.
     ```

  3. `phase` 필드 부재인 경우에만 추가로 advisory 한 줄 출력 (종료 아님):

     ```
     (선택) schema 업그레이드는 'python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --fix' — 동작에는 필수 아님
     ```

  4. 다음 단계로 진행.

### 4. qa/{KEY}.md 존재 여부 분기

`workspace/projects/{PROJECT}/qa/{KEY}.md` 존재 여부를 확인한다.

- **존재함** (= 같은 티켓 재작업) → `qa/{KEY}.md` 를 Read 만 수행하고 6 단계로 진행. `qa/{KEY}.md` 재생성·Jira 재fetch 금지 (기존 내용 보존). **단, 6 단계 작업 브랜치 생성의 git Bash 는 허용한다** — 재작업도 새 작업 브랜치가 필요하다. 재작업 회차 N 은 `qa/{KEY}.plan*.md` 의 기존 r 최대값 + 1 로 정하고 (초회 산출물만 있으면 N=1), 이후 사이클 산출물은 아래 "qa/ 산출물 명명 규약"의 `.r{N}` 명명을 따른다.
- **존재하지 않음** → 5 단계 (신규 생성 절차) 로 진행.

### 4-1. qa/ 산출물 명명 규약

사이클 산출물의 파일명은 아래 표가 SSOT 다. 에이전트(@pilot-planner·@pilot-planner-critic·@pilot-evaluator)의 qa 분기가 이 규약을 따르고, `/pilot:pilot-doctor` 가 위반을 WARN 으로 감지한다.

| 산출물 | 초회 | 재작업·대형 개정 N회차 |
| --- | --- | --- |
| 티켓 본문 | `qa/{KEY}.md` | (재생성 금지) |
| plan | `qa/{KEY}.plan.md` | `qa/{KEY}.plan.r{N}.md` |
| plan critic | `qa/{KEY}.plan.critic.md` | `qa/{KEY}.plan.critic.r{N}.md` |
| eval | `qa/{KEY}.eval.md` | `qa/{KEY}.eval.r{N}.md` |

- `.r{N}` 은 **항상 마지막 `.md` 바로 앞**. (`{KEY}.plan.r1.critic.md` 같은 중간 삽입 금지)
- critic 파일명 = 대응 plan 파일명에서 `.plan` → `.plan.critic` 치환 (r 꼬리표 유지).
- eval 의 r = 대응 plan 의 r.
- 기존 비규약 파일은 자동 rename 하지 않는다 — doctor WARN 의 기대 이름으로 수동 정리.
- **사이클 내 대형 개정도 새 회차로 분리** — 같은 티켓에서 plan 의 전제가 바뀌는 개정(결함 함수 목록 변경·1차 수정 머지 후 추가 수정·작업 브랜치 변경)은 기존 plan 에 `추가 수정` 류 섹션을 덧붙이지 않고 `qa/{KEY}.plan.r{N}.md` 새 파일로 시작한다. critic·eval 도 같은 r 을 따른다. critic 챌린지 반영으로 같은 계획 내부를 다시 쓰는 것은 대형 개정이 아니다 (같은 plan 파일 제자리 수정 — pilot-planner 재호출 분기). (한 plan 파일에 추가 수정이 누적되면 파일이 무한 비대해져 매 로드마다 토큰을 낭비한다.)

### 5. 신규 생성 절차

#### 5-1. workspace KEY 중복 검사

같은 `{KEY}` 파일이 다른 project 에 이미 있는지 검사한다 — 같은 결함이 두
project 에 분산되면 추적이 어렵다.

Glob 또는 Bash 로 확인:

```bash
find workspace/projects/ -path "*/qa/{KEY}.md" -not -path "*/{PROJECT}/qa/*"
```

매칭이 있으면 다음 WARN 출력 후 사용자 확인:

```
같은 KEY '{KEY}' 가 다른 project '{OTHER_PROJECT}' 에 이미 존재: {경로}.
같은 결함이 두 project 에 분산되면 추적이 어려워집니다.
계속 진행할까요? [y/N]:
```

- 사용자가 `y`/`yes` 응답 시 다음 단계로 진행.
- 그 외 응답 또는 non-interactive (no TTY) 면 **fail-safe 로 거절** 하고
  종료.

#### 5-2. Jira fetch

다음 Bash 명령을 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/jira.py fetch {KEY}
```

- 성공 (exit 0) → stdout 으로 받은 markdown 본문을 5-3 prefill 에 사용.
- 실패 (exit 1) → stderr 의 에러 메시지를 사용자에게 그대로 안내하고 종료.
  **빈 파일을 생성하지 않는다.** 환경변수 미설정·네트워크·인증·404 등
  원인별 안내는 jira.py 가 출력한다.

stdout 의 섹션 구성: [`references/jira-prefill.md`](references/jira-prefill.md).

#### 5-3. 템플릿 prefill

`${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/example/qa/JIRA-KEY.md.example`
의 구조를 따라 `workspace/projects/{PROJECT}/qa/{KEY}.md` 를 신규 생성
한다. fetch 결과 주입 규칙 (토큰 매핑·폐기 항목·placeholder 유지):
[`references/jira-prefill.md`](references/jira-prefill.md).

> 회신 섹션은 만들지 않는다. 회신 SSOT 는 Jira (`tools/jira.py comment`).

폴더가 없으면 `qa/` 폴더를 lazy 생성한다.

### 6. 작업 브랜치 생성

신규 생성·기존 Read 두 경로 모두 공통으로 수행한다. @pilot-planner 핸드오프
(7 단계) 전에 결함 수정용 작업 브랜치를 만든다 (질의 없음 — 6-2 가 생성·보고).

#### 6-1. 브랜치명 결정 (재작업 중복 방지)

base 는 `fix/{KEY}`. 같은 티켓이 이전에 해결된 뒤 다시 수정이 진행되는
경우(재작업)를 대비해, 기존 동일 base 브랜치(local + remote)를 조사하여 suffix
최댓값 + 1 의 `fix/{KEY}-{N+1}` 로 충돌을 피한다 — 조사 명령·suffix 결정 예시:
[`references/branch-naming.md`](references/branch-naming.md).

#### 6-2. 생성 + 보고 (질의 없음)

결정된 브랜치명으로 `git checkout -b {branch}` 를 **질의 없이 실행**하고 1줄
보고한다. 분기점 (현재 HEAD 의 브랜치명·short SHA) 을 반드시 포함한다 —
잘못된 base 에서 분기했음을 사용자가 즉시 인지하고 개입할 수 있도록 (둘째
줄은 재작업 충돌 감지 시에만):

```
작업 브랜치 생성: '{branch}' (분기점: {현재 브랜치}@{short SHA})
(재작업 — 기존 'fix/{KEY}' 충돌 회피)
```

- 생성 실패 (이미 존재 등) 시 에러를 그대로 안내하고 브랜치 미생성 상태로
  7 단계 진행.
- 다른 브랜치 전략이 필요하면 사용자가 사전에 말하면 반영한다 — 브랜치는
  완전 가역 (삭제 후 재분기 가능) 이라 사후 교정 비용이 낮다. 질의 없는
  생성이 기본 동선 — 스킬 호출 자체가 결함 수정 의도이며 브랜치 생성은 그
  기본 동선이다.

브랜치는 현재 HEAD 에서 분기한다. 특정 base(main/develop 등)에서 시작해야 하면
사용자가 먼저 해당 브랜치로 이동한 뒤 본 스킬을 호출한다.

### 7. 다음 단계 안내

신규 생성·기존 Read 모두 동일하게 다음 한 줄을 출력한다 (6 단계에서 브랜치를
만들었으면 그 이름을 앞에 덧붙인다):

```
qa/{KEY}.md 준비됨. @pilot-planner 호출로 분석·수정 시작하세요. 회신은
'python3 ${CLAUDE_PLUGIN_ROOT}/tools/jira.py comment {KEY} "..."' 로.
```

기존 파일을 Read 한 경우에는 핵심 섹션 (현상·연관 feature·원인·조치) 의
현재 상태를 한 줄 요약으로 덧붙인다.

---

## 명시 비분기 (out of scope)

- **보드뷰·다건 조회 절대 안 함.** 잔여 결함·우선순위·재오픈 현황은 Jira UI
  가 SSOT — 로컬 보드뷰·INDEX·진행 카운트를 만들지 않는다 (SSOT 이중화 회피).
- **인자 필수.** 인자 없는 호출은 1 단계에서 즉시 종료.
- **features/ 수정 금지.** QA phase 는 features/ 를 읽기 전용으로 본다 —
  features 본문 수정이 필요하면 `/pilot:qa off` 또는
  `/pilot:project {PROJECT} --qa off` 로 development 로 복귀한 뒤 별도
  사이클 진행.
- **회신 로컬 기록 없음.** `qa/{KEY}.md` 에는 회신 섹션을 두지 않는다.
  회신 이력은 Jira 코멘트가 SSOT.
