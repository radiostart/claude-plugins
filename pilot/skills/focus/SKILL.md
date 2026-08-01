---
name: focus
description: >-
  사용자가 대화 중 내린 결정·방향 조정(예: "소프트 딜리트 빼줘",
  "Goal 5 먼저")을 다음 서브에이전트 호출(@pilot-planner·@pilot-planner-critic·@pilot-generator·@pilot-evaluator)에
  전달해야 할 때 사용한다. 메인 대화의 결정이 서브에이전트에겐 보이지 않는
  문제를 `.focus.md` 파일 매개로 해소한다.
---

# /pilot:focus

> **페르소나 — note-taker** (이 스킬 SSOT, 공통 톤 [`identity.yml`](../context/shared/identity.yml) 위에 덧씌움)
> - voice: 결정만 받아 적는다. 해석·확장 금지
> - phrasing: 사용자 발화 원문 보존 + 시각 스탬프
> - forbid: "결정에 살붙이기" / "임의 요약·재구성"

사용자의 현재 지시를 활성 프로젝트에 기록해 다음 래퍼 호출에 반영한다.

대상: $ARGUMENTS (`--clear` 로 제거)

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료. `--clear` 도 지시문도 없는 빈 인자면 안내 후 종료.

- 활성 행이 `| project | {PROJECT} |` → project 를 대상으로 진행.
- 활성 행이 `| issue | {이슈명} |` → **P1 issue 종료 규칙 예외** — 종료하지 않고 이슈를 대상으로 진행한다 (아래 § 경로 계약 의 issues/ 분기). 단 `| issue | - |` (이슈명 없는 bare) 는 기록처가 없으므로 "bare issue 모드에는 focus 를 기록할 수 없습니다. `/pilot:issue {이슈명}` 으로 재진입하세요." 출력 후 종료.

## 경로 계약

활성 STATE.md 행의 mode 에 따라 기록 폴더가 갈린다 — **orchestrate-load 가 같은 기준 (work_mode) 으로 읽으므로 반드시 일치시켜야 한다** (project 활성인데 issues/ 에 쓰거나 그 반대면 래퍼가 지시를 못 본다):

- **project 활성**: `workspace/projects/{PROJECT}/.focus.md` · 아카이브 `workspace/projects/{PROJECT}/.focus.history/{ISO timestamp}.md` (삭제가 아닌 **이동**)
- **issue 활성**: `workspace/issues/{이슈명}/.focus.md` · 아카이브 `workspace/issues/{이슈명}/.focus.history/{ISO timestamp}.md`

아래 동작의 `.focus.md`·`.focus.history/` 와 결과 출력의 `{경로}` 는 모두 위에서 결정된 활성 폴더 기준이다.

## 동작

### 기록 모드 (지시문 제공)

기존 `.focus.md` 있으면 `.focus.history/{기존 기록시각}.md` 로 이동(파일 timestamp 헤더 기준, 없으면 mtime) — **활성 focus 는 항상 최대 1개**. 새 `.focus.md` 를 아래 형식으로 Write:

```markdown
# Focus — {YYYY-MM-DDTHH:MM:SS}

{지시문 본문}
```

결과: "focus 기록됨: {경로}. 다음 @pilot-planner/@pilot-planner-critic/@pilot-generator/@pilot-evaluator 호출 시 자동 반영됩니다 (이전 focus 는 history 로 이동됨)."

### 제거 모드 (`--clear`)

`.focus.md` 없으면 "활성 focus 가 없습니다" 후 종료. 있으면 `.focus.history/{timestamp}.md` 로 이동 후 삭제 → "focus 제거됨 (아카이브됨: {경로})" 출력.

## 래퍼와의 상호작용

4 에이전트는 컨텍스트 로드 단계에서 `.focus.md` 를 Read 하고 **본 호출에 한해** 반영한다. **래퍼는 Read 만** — 수정·삭제·아카이브하지 않으므로 한 focus 가 여러 phase 에 걸쳐 유효하다. 해제는 사용자의 `/pilot:focus --clear` 또는 새 focus 로 덮어쓰기.

## 제약

- 활성 focus 는 **최대 1개** — 여러 지시는 하나의 focus 문자열에 묶어 작성.
- focus 는 **지시**이지 **사양**이 아니다. 긴 내용은 `features/NN-*.md` 수정이 더 적합.
- `.focus.md`·`.focus.history/` 는 gitignore 대상 (사용자별·세션별 컨텍스트).
