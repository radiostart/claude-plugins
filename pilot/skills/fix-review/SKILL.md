---
name: fix-review
description: >-
  CODE REVIEW REPORT 의 finding 별 처리 경로를 추천한다 — `trivial` (직접 Edit) /
  `one-shot` (`@pilot-generator`) / `full-cycle` (`@pilot-planner`) / `new-feature`
  (`/pilot:create-feature`) / `dismiss` (룰 보강·acknowledgement). 자동 실행은 안 함 —
  사용자가 표를 보고 명시 호출. `/pilot:review` 출력 다음 단계.
---

# /pilot:fix-review

`@pilot-code-review` 의 CODE REVIEW REPORT 를 읽어 finding 별로 어디서부터 시작할지 추천한다.
실제 수정·`@pilot-*` 호출·feature 생성은 사용자가 결정·실행한다 (자동 invoke 없음).

대상: $ARGUMENTS

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1** 수행 (다단계 — TodoWrite 선로딩).
프로젝트 컨텍스트 독립.

## 인자 파싱

- (없음) → 직전 turn 의 CODE REVIEW REPORT 본문 추출
- `--from <path>` → 파일에서 REPORT Read
- (REPORT 부재) → "REPORT 없음. `/pilot:review` 먼저 실행하세요" 안내 후 종료

## 분류 축

각 finding 을 5 경로 중 하나로 추천:

| 경로 | 조건 | 다음 액션 |
| --- | --- | --- |
| **trivial** | 단일 파일·기계적 수정 (네이밍·import·매직넘버·잔존 디버그 제거) | 사용자가 직접 Edit (사이클 없이 묶어 1 commit) |
| **one-shot** | 단일 함수·로직 변경 (예: 반복 쿼리 개선·rescue 수정·null 가드) | `@pilot-generator` 1 회 호출 (선택 finding 묶어서 전달) |
| **full-cycle** | 다중 파일·시그니처 변경·트랜잭션 구조·영향 분석 필요 | `@pilot-planner → @pilot-generator → @pilot-evaluator` 정식 사이클 |
| **new-feature** | 본 변경 의도와 분리되어야 할 별도 기능 (helper 추출·큰 리팩터·횡단 관심사) | `/pilot:create-feature "{지시문}"` 로 별도 feature |
| **dismiss** | 의도된 결정·trade-off·룰 보강 사항 (drift 류) | 사유 기록 또는 `workspace/context/review/{lang}.md` 보강 권장 |

### 분류 신호 (severity 와 직결 안 됨)

- 변경 파일 수 (1 → trivial/one-shot, 다중 → full-cycle 후보)
- 시그니처·인터페이스 변경 여부 (있으면 full-cycle 가산)
- 호출자 영향 범위
- 사용자 가시 여부 (UI/API/docs/i18n)
- finding 의 개선안이 명시한 액션 단순도
- reviewer 의 재진입 라우팅 (`feature`/`planner`/`generator`/`local`) — full-cycle/one-shot 판단의 1차 참고
- 본 변경 의도와의 결합도 (의도와 떨어진 큰 작업 → new-feature)

**분류 모호하면 보수적으로 한 단계 더 위 (trivial→one-shot, one-shot→full-cycle).**

## 출력

```
## FIX RECOMMENDATIONS
- source: {REPORT base — 브랜치/경로/turn 식별}
- total: {N} findings → trivial {a} · one-shot {b} · full-cycle {c} · new-feature {d} · dismiss {e}

| # | sev | path:line | 경로 | 이유 |
|---|-----|-----------|------|------|
| 1 | blocking | services/foo.rb:42 | full-cycle | 시그니처 변경 + 호출자 5곳 영향 (reviewer 라우팅 planner) |
| 2 | suggestion | services/bar.rb:15 | one-shot | 단일 함수 반복 쿼리 — 일괄 조회 도입 |
| 3 | nit | views/baz.erb:5 | trivial | 매직 넘버 1줄 추출 |
| ... | ... | ... | ... | ... |

## 다음 액션 (사용자 선택)

- **trivial 묶음 ({a}건):** 직접 Edit 후 `/pilot:commit`. 추천 commit scope: `{scope}`
- **one-shot 묶음 ({b}건):** `@pilot-generator` 호출. 컨텍스트 한 줄: "{finding 요약 모음}"
- **full-cycle ({c}건):** finding 별로 `@pilot-planner` 시작. 첫 후보: #{N} {path:line}
- **new-feature ({d}건):** `/pilot:create-feature "{권장 지시문}"` (예: "{예시}")
- **dismiss ({e}건):** {룰 보강 권장 항목 / acknowledgement 사유}
```

## 제약

- **자동 실행 안 함.** 분류·추천만. Edit / `@-mention` 호출 / 스킬 invoke 모두 사용자 책임.
- 분류는 finding 본문 + 본문 명시된 개선안만으로 판단. 코드 직접 Read 안 함 (reviewer 가 이미 읽은 결과를 신뢰).
- 단일 finding 을 여러 경로에 동시 분류 안 함. 모호하면 보수적 채택 + "이유" 컬럼에 명시.
- 요구사항 충족·게이트 판정 영역 finding 은 `@pilot-code-review` 책임 밖이지만, 만약 REPORT 에 들어왔다면 `dismiss` + "evaluator 책임 영역 — `@pilot-evaluator` 사이클로 처리" 사유.

## 참조

- [`agents/pilot-code-review.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-code-review.md) — REPORT 생산자
- [`skills/create-feature/SKILL.md`](../create-feature/SKILL.md) — new-feature 경로의 다음 단계
- [`skills/commit/SKILL.md`](../commit/SKILL.md) — trivial 묶음 후 다음 단계
