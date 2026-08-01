# 운영 이슈 단건 처리 (issue 사이클)

!!! info "한 줄 요약"
    누적된 컨텍스트 (도메인 지식·과거 이슈 이력) 위에서 운영 문제 1건을 진단·수정합니다. 코드 수정이 필요하면 project 와 동일한 planner→critic→generator→evaluator 사이클을 이슈 단위로 사용합니다.

## 언제 쓰나

- **project 컨텍스트와 무관한** 운영 장애·버그·핫픽스·데이터 정합 이슈 1건을 처리할 때
- 과거 유사 이슈의 원인·조치 기록을 출발점으로 삼고 싶을 때

활성 project 의 feature 작업은 [`/pilot:project`](../tutorial/getting-started.md) 를 사용합니다 — issue 는 project 독립 단건 전용입니다.

## 전제

- workspace 가 초기화되어 있을 것 (`/pilot:pilot-init`).
- 도메인 컨텍스트 (`workspace/context/`) 가 채워져 있을수록 진단 품질이 올라갑니다 ([`/pilot:learn`](../reference/skills/learn.md) 누적).

## 절차

### 1. 이슈 모드 진입

```text
/pilot:issue 미출고 주문 일괄 취소가 실패하는 문제
환불 대기 건이 섞이면 취소가 안 됨
```

**아는 대로 길게, 여러 줄로 써도 됩니다** — 입력은 폴더명이 아니라 명세의 재료입니다. 첫 줄(또는 핵심 요약)이 H1 제목, 전문이 `## 현상` 으로 들어갑니다.

내부 동작:

- `workspace/issues/` 에서 **유사 이슈를 먼저 검색**해 재개/신규를 확인합니다 — 폴더명(영문 slug)과 각 `issue.md` 의 H1 제목(한글)을 함께 훑으므로 한글 키워드로도 과거 이슈가 걸립니다.
- 신규면 입력에서 **영문 kebab slug** 를 뽑아 `issues/{slug}/issue.md` 를 템플릿으로 생성하고, STATE.md 를 `| issue | {slug} | 진행중 |` 로 교체합니다. 입력 원문은 버려지지 않습니다.
- 신규 이슈면 `도메인:` 라인 확정을 위한 **질의 1회**가 이어집니다 — 확정 값은 issue.md 상단에 기입되고 해당 도메인 컨텍스트가 로드됩니다 (상태 파일 없음 — 기록처는 issue.md 자신).

slug 는 팀 용어의 **코드 표기를 우선** 채택합니다 — 도메인 문서가 "미출고" 의 코드 표기를 `unshipped` 로 명시했다면 `unshipped-bulk-cancel-fail` 이 됩니다. 폴더명으로 소스를 grep 할 수 있게 하려는 것입니다. 입력에 축이 여러 개 섞여 용어 매핑이 갈리면 후보 2~3개를 제시하고 확인을 받습니다.

인자 없이 `/pilot:issue` (bare) 로 진입하면 폴더·기록이 남지 않고 사이클도 비지원입니다 — 짧은 조사 전용.

### 2. 현상 확인·보강

`issue.md` 의 `## 현상` (증상·에러·재현 경로·기대 동작·영향 범위) 을 직접 편집해 보강합니다 — 모르는 축은 `(미확인)` 으로 남깁니다. 선택적으로 `## 의심 영역` 을 채우면 AI 탐색 범위와 도메인 후보 제시가 좁아집니다.

### 3. 처리 경로 선택

- **조사·경미형** (원인 파악·회신·1줄 수정): 진단 절차대로 직접 처리하고 issue.md 의 `## 원인`·`## 조치` 를 기록합니다.
- **코드 수정형**: 사이클을 시작합니다:

```text
@pilot-planner
```

orchestrate-load 가 STATE.md 의 issue 행을 인식해 (`work_mode: issue`) `issues/{이슈명}/` 기반으로 로드하며, 이후 흐름은 project 와 동일합니다:

| 단계 | 산출물 | 이슈 모드 특칙 |
| --- | --- | --- |
| `@pilot-planner` | `issue.plan[.r{N}].md` | 최소 변경·롤백 가능, `## 원인` 기입, 영향 범위 후보·결함 함수 1줄·회귀 재현 테스트 스텝 필수 |
| `@pilot-planner-critic` | `issue.plan.critic[.r{N}].md` | 챌린지 기준 동일 |
| `@pilot-generator` | 코드 수정 | 결함 함수 (또는 조치 대상) 범위 내에서만 수정, `## 조치` 기입 |
| `@pilot-evaluator` | `issue.eval[.r{N}].md` | 회귀영향 평가 + 회귀 테스트 **직접 실행** (`test_run` skip 금지), `## 조치` 기입이 READY 게이트, REPORT 는 `mode: issue` |

plan 승인·critic blocking·NOT_READY 의 휴먼 게이트는 project 사이클과 동일하게 유지됩니다.

### 4. 마무리

- evaluator READY 후 `## 재발 방지` 를 기록해 두면 다음 유사 이슈 진단의 출발점이 됩니다.
- 커밋·PR 은 평소처럼 [`/pilot:commit`](../reference/skills/commit.md)·[`/pilot:pr`](../reference/skills/pr.md) 를 사용합니다 — **commit 은 issue 모드에서도 동작합니다** (P1 issue 판정 예외).
- 다른 작업으로 전환: `/pilot:project {프로젝트명}` (이슈 폴더·기록은 그대로 남습니다).

## 주의

- **issue 활성 중 project 전용 스킬은 실행되지 않습니다** — `analyze`·`confl`·`tdd`·`create-feature`·`characterize`·`autopilot`·`pr`·`slack` 은 issue 행을 감지하면 명확히 종료합니다 (preamble P1 판정). `focus`·`commit` 은 예외로 계속 동작합니다.
- 기존 이슈 파일은 hook 이 보호합니다 — 재진입 시 Write 덮어쓰기가 차단되고 Edit (원인·조치 기입) 만 허용됩니다.
- tdd/characterize 모드는 issue 사이클에서 지원하지 않습니다 (standard 고정).
- Slack 알림은 이슈 모드 미지원입니다 (자동 no-op).
