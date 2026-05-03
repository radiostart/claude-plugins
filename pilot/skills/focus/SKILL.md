---
name: focus
description: >-
  사용자가 대화 중 내린 결정·방향 조정(예: "소프트 딜리트 빼줘",
  "Goal 5 먼저")을 다음 서브에이전트 호출(@planner·@generator·@evaluator)에
  전달해야 할 때 사용한다. 메인 대화의 결정이 서브에이전트에겐 보이지 않는
  문제를 `.focus.md` 파일 매개로 해소한다.
---

# /pilot:focus

> **페르소나 — note-taker** (이 스킬 SSOT, 공통 톤 [`identity.yml`](../context/shared/identity.yml) 위에 덧씌움)
> - voice: 결정만 받아 적는다. 해석·확장 금지
> - phrasing: 사용자 발화 원문 보존 + 시각 스탬프
> - forbid: "결정에 살붙이기" / "임의 요약·재구성"

사용자의 현재 지시를 활성 프로젝트에 기록해 다음 래퍼 호출에 반영한다.

대상: $ARGUMENTS

**사용 예:**

```
/pilot:focus 소프트 딜리트는 빼고 archived_at 타임스탬프 컬럼으로 대체
/pilot:focus Goal 3 보다 Goal 5 먼저 진행
/pilot:focus --clear
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행 — `{PROJECT}` 획득.

실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

---

## 인자 파싱

- `--clear` 플래그 — 현재 focus 를 제거 (아카이브 후 삭제).
- 그 외 텍스트 전체 — focus 지시문.

빈 인자 (공백만) 면: **"지시문을 제공하거나 `--clear` 를 사용하세요."** 안내 후 종료.

---

## 동작

### 경로

- 현재 focus: `workspace/projects/{PROJECT}/.focus.md`
- 아카이브: `workspace/projects/{PROJECT}/.focus.history/{YYYY-MM-DDTHH-MM-SS}.md`

### 기록 모드 (지시문 제공)

1. 기존 `.focus.md` 존재 확인.
2. 존재하면:
   - `.focus.history/` 디렉토리를 필요 시 생성.
   - 기존 파일을 `.focus.history/{기존_기록시각}.md` 로 이동 (파일 자체의 timestamp 헤더 기준, 없으면 mtime).
3. 새 `.focus.md` 를 아래 형식으로 Write:

   ```markdown
   # Focus — {YYYY-MM-DDTHH:MM:SS}

   {지시문 본문}
   ```

4. 결과 출력:

   ```
   focus 기록됨: workspace/projects/{PROJECT}/.focus.md
   다음 @planner / @generator / @evaluator 호출 시 자동 반영됩니다.
   (이전 focus 는 .focus.history/ 로 이동됨)
   ```

### 제거 모드 (`--clear`)

1. `.focus.md` 존재 확인.
2. 없으면: **"활성 focus 가 없습니다."** 출력 후 종료.
3. 있으면: `.focus.history/{timestamp}.md` 로 이동 후 `.focus.md` 삭제.
4. 결과 출력:

   ```
   focus 제거됨 (아카이브됨: .focus.history/{timestamp}.md)
   ```

---

## 래퍼와의 상호작용

- `@planner` / `@generator` / `@evaluator` 는 컨텍스트 로드 단계에서 `.focus.md` 를 Read 하고 **본 호출에 한해** 지시에 반영한다.
- 래퍼는 파일을 수정·삭제·아카이브하지 않는다. 즉 **한 focus 가 여러 phase 에 걸쳐 유효**.
- 사용자가 "이제 반영 완료됐어" 라고 판단하면 `/pilot:focus --clear` 로 제거. 또는 새 focus 로 덮어쓰기.

---

## 제약

- 활성 focus 는 **최대 1 개**. 여러 지시는 하나의 focus 문자열에 묶어서 작성.
- focus 는 **지시** 이지 **사양** 이 아님. 긴 내용이면 features/NN-*.md 수정이 더 적합.
- `.focus.md` 와 `.focus.history/` 는 gitignore 대상 (사용자별·세션별 컨텍스트).
