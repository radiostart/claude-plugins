# 대상 plan 확정 (조사·집계 SSOT)

호출자가 대상 feature 를 명시하지 않았을 때 **어떤 plan 파일을 후보로 세는지**를
정의한다. `@pilot-generator` · `@pilot-planner-critic` · `@pilot-evaluator` 세
wrapper 가 본 문서를 단일 기준으로 공유한다 — 셋이 서로 다른 집계 규칙을 쓰면
같은 상태에서 어떤 wrapper 는 "후보 1 개", 다른 wrapper 는 "후보 3 개" 로 갈린다.

> **경계** — 본 문서는 **후보 조사·집계**만 다룬다. 후보 수가 정해진 뒤의
> **행동**(0 개일 때 무엇을 하는가 등)은 역할마다 다르므로 각 wrapper 본문에
> 남긴다. 아래 § 후보 수별 행동 참조.
>
> `.r{N}` **명명 규약** 자체의 SSOT 는 issue 산출물은 issues/GUIDE.md
> § 이슈 폴더 구조, qa 산출물은 qa/SKILL.md § qa/ 산출물 명명 규약이다.
> 본 문서는 그 규약으로 만들어진 파일을 **세는 법**만 정한다.

## 1. 조사 방법 — Glob 도구 (모드별 택일)

| 상황 | Glob 패턴 |
| --- | --- |
| 기본 (development) | `workspace/projects/{PROJECT}/features/*.plan.md` |
| `project_phase == qa` | `workspace/projects/{PROJECT}/qa/*.plan.md` · `…/qa/*.plan.r*.md` |
| `work_mode == issue` | `workspace/issues/{이슈명}/issue.plan.md` · `…/issue.plan.r*.md` |

`work_mode == issue` 의 경로는 `workspace/issues/` 직하다 — `projects/{PROJECT}/`
를 앞에 붙이지 않는다.

**셸 글롭 (`ls -t a/*.md b/*.md`) 을 쓰지 않는다.** zsh 는 패턴 하나라도 안 맞으면
(`nomatch`) 명령 전체가 실행되지 않아 매칭되던 쪽 결과까지 사라지고, `2>/dev/null`
로도 잠기지 않는다. `qa/` 부재는 development 의 **정상 상태**이므로 이 함정은
예외가 아니라 기본 경로다 — "후보 0 건" 이 실제 부재인지 셸 실패인지 구분할 수
없게 된다.

## 2. 집계 규칙

- **`.plan.critic.md` · `.plan.critic.r{N}.md` 는 후보가 아니다** — critic
  산출물이다. 포함하면 critic 직후 호출되는 wrapper 에서 상시 복수가 된다
  (issue 모드의 `issue.plan*.md` 같은 광역 글롭이 이를 삼킨다 — 위 표의 패턴만 쓴다).
- **대응 `.eval.md` 의 `status` 가 `READY` 인 plan 은 후보가 아니다** (처리 완료).
  plan 산출물은 삭제되지 않고 누적되므로, 이 필터가 없으면 두 번째 feature 이후
  후보가 **상시 복수**가 되어 확정 절차가 매번 발동한다.
  - eval 짝: project 모드 `features/NN-{slug}.eval.md` · qa phase
    `qa/{KEY}.eval[.r{N}].md` · issue 모드 `issue.eval[.r{N}].md`
    (r 은 plan 과 동일).
  - `READY` 판정은 `status:` **값 전체 일치**로 한다 — `NOT_READY` 가 `READY` 를
    부분 문자열로 포함하므로 substring 매칭은 오판한다.
  - `NOT_READY` 는 재작업 (generator) · 재계획 (critic) · 재평가 (evaluator)
    대상이므로 **후보로 남긴다**.
- **(qa·issue) 같은 대상의 `.r{N}` 이 여러 개면 r 최대값 1 개로 센다.**
  `.eval.md` 짝은 같은 r 을 본다. project 모드 (development) 의 plan·eval 은
  `.r{N}` 없는 단일 파일이다 (재평가 시 전체 재생성 — pilot-evaluator step 7).

`READY` 인 feature 를 다시 다뤄야 하면 **호출 프롬프트로 대상을 명시**한다
(프롬프트가 후보 조사에 우선한다).

## 후보 수별 행동은 여기서 정하지 않는다

본 문서는 **후보를 세는 데까지**만 관여한다. 센 뒤의 행동(1 개면 무엇을 명시하고,
0 개면 종료인지 진행인지)은 역할마다 달라 각 wrapper 본문이 SSOT 다.

| wrapper | 해당 절 |
| --- | --- |
| `@pilot-generator` | step 2 `[대상 plan 확정]` |
| `@pilot-planner-critic` | step 2 `[대상 plan 확정]` |
| `@pilot-evaluator` | step 1 `[필수] 대상 feature 확정` |

> 여기에 행동 규칙을 옮겨 적지 않는다 — wrapper 본문과 이중화되어 편집 지점이
> 3 벌에서 4 벌로 늘어난다 (본 문서를 만든 목적과 정반대). wrapper 는 본 문서
> 없이도 **자기 역할의 행동을 단독으로 읽을 수 있어야** 한다.

## 변경 시 동기화 대상

본 문서의 조사·집계 규칙을 고치면 아래에 인라인 재서술이 남아 있지 않은지 함께
확인한다:

- `agents/pilot-generator.md` — step 2 `[대상 plan 확정]`
- `agents/pilot-planner-critic.md` — step 2 `[대상 plan 확정]`
- `agents/pilot-evaluator.md` — step 1 `[필수] 대상 feature 확정`
- `skills/autopilot/SKILL.md` — 메인 루프의 대상 명시 규칙 (본 문서의 조사 절차를
  우회하는 명시 경로라, 규칙 변경의 영향을 함께 받는다)

세 wrapper 가 같은 규칙을 각자 인라인으로 들고 있으면 규칙 개정 때마다 3 벌
동기 편집이 필요하다 — 그 비용이 본 SSOT 분리의 근거다.
