---
name: review
description: >-
  프로젝트 진행 중 작성된 코드를 PR 이전에 품질 관점에서 리뷰한다.
  변경분(git diff)을 대상으로 pilot-code-review 에이전트를 호출하며,
  결함마다 severity 와 재진입 라우팅(feature/planner/generator)을 제시한다.
  evaluator 의 요구사항·게이트 판정과는 별개 축이다.
---

# /pilot:review

PR 생성 이전, 사이클 내부에서 작성된 코드를 품질 관점으로 리뷰한다.

대상: $ARGUMENTS

---

## 동작

1. **target 결정**
   - 인자 없음 → 변경분 전체 (uncommitted + 현재 브랜치 커밋)
   - 경로 인자 (예: `app/services/`) → 해당 경로로 한정
   - 커밋 범위 인자 (예: `HEAD~3..HEAD`) → 해당 범위
2. 결정한 target 을 전달하며 `@pilot-code-review` 를 호출한다.

에이전트가 변경분을 수집해 언어별 규칙 + baseline 루브릭으로 리뷰하고 `CODE REVIEW REPORT` 를 출력한다. 코드는 수정하지 않으며, 결함마다 재진입 라우팅(feature/planner/generator/trivial/new-feature/dismiss)을 제시해 사용자가 선택한다. REPORT 의 routing 요약이 trivial 일괄 커밋·one-shot 묶음·full-cycle 후보까지 직접 안내한다. 상세 절차: [`pilot-code-review.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-code-review.md).

---

## 언어별 규칙

언어별 리뷰 규칙은 `workspace/context/review/{lang}.md` 에 둔다. 파일이 있는 언어는 그 규칙 + plugin baseline 이, 없는 언어는 baseline 만 적용된다. 작성 템플릿: [`review-rules-template.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-rules-template.md).

---

## 역할 경계

- `/pilot:review` (이 스킬) — 팀 규칙 파일(`workspace/context/review/{lang}.md`) 적용·사이클 재진입 라우팅이 필요한 리뷰. 대화창에 리포트 + 재진입 라우팅 출력.
- 내장 `/code-review` — 범용 정확성 리뷰 패스 (로컬 변경분·GitHub PR 모두 대상). 팀 규칙·라우팅이 필요 없으면 이쪽.
- `@pilot-evaluator` — 요구사항 충족·게이트 통과 **판정**. 사이클의 일부.
- 내장 `/security-review` — 심층 보안 패스. 보안이 중요한 변경에 별도 권장.
