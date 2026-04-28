---
name: ai-review
description: >-
  PR의 AI 리뷰 코멘트(devops-deali 작성)에서 필수 수정사항만 추출해 새
  fix 브랜치에서 적용하고, 원본 PR의 base branch로 후속 PR을 자동 생성한다.
  권장 사항이나 "런타임 오류 없음"으로 판정된 항목은 제외한다.
---

PR의 AI 리뷰 결과를 분석하고, 필수 수정사항을 새 브랜치에서 수정한 뒤 PR을 생성한다.

대상 PR: $ARGUMENTS

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1** 수행 (TodoWrite 선로딩 — 다단계 작업).
프로젝트 컨텍스트와 독립이므로 P0/P1/P2 는 미적용.

## 수행할 작업

### 1. PR 정보 파싱

- `$ARGUMENTS` 에서 PR 번호를 추출한다. URL 형식(`https://github.com/.../pull/123`) 또는 숫자(`123`) 모두 허용한다.
- `$ARGUMENTS` 가 비어있으면 [messages.md](../context/shared/messages.md) 의 `pr_number_required` 출력 후 종료.
- `gh api repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}` 로 PR 의 base branch 를 확인한다.

### 2. 최신 AI 리뷰 코멘트 조회

- `gh api repos/{OWNER}/{REPO}/issues/{PR_NUMBER}/comments` 로 코멘트 목록을 조회한다.
- `devops-deali` 가 작성한 가장 마지막 코멘트를 찾는다.
- 해당 코멘트에서 **`## 1. 필수 수정사항` → `### 1.1 런타임 오류 검사`** 섹션의 내용만 추출한다.
  - `## 2.` 이후 내용(권장 사항)은 수정 대상에서 제외한다.
  - "런타임 오류 없음", "실질적 런타임 오류 위험은 낮습니다" 등 실제 수정이 불필요한 항목도 제외한다.

### 3. 수정할 항목이 없는 경우

- 필수 수정사항이 없으면 [messages.md](../context/shared/messages.md) 의 `ai_review_no_fixes` 출력 후 종료한다.

### 4. fix 브랜치 생성

- 현재 브랜치를 base로 삼아 새 브랜치를 생성한다.
- 브랜치 이름 규칙: `fix/{PR_NUMBER}-ai-review`
  - 이미 존재하면 `fix/{PR_NUMBER}-ai-review-2`, `-3`, ... 순으로 자동 증가한다.
  - `git branch -a | grep "fix/{PR_NUMBER}-ai-review"` 로 기존 브랜치 목록을 확인해 다음 번호를 결정한다.
- `git checkout -b fix/{PR_NUMBER}-ai-review-{N}` 으로 브랜치 생성 후 해당 브랜치에서 작업한다.

### 5. 필수 수정사항 적용

- 추출한 각 수정 항목에 대해 대상 파일을 Read로 읽고, 정확한 코드 위치를 확인한 뒤 Edit로 수정한다.
- 수정 시 AI 리뷰의 "수정 후" 코드를 기준으로 적용한다.
- 수정 후 IDE 진단(PostToolUse hook)에서 **Error** 레벨 문제가 있으면 즉시 수정한다. `Information` 레벨은 무시한다.

### 6. 커밋

- `git add {수정된 파일들}` 로 변경 파일을 스테이징한다.
- 커밋 메시지 형식:

  ```
  fix: AI 리뷰 수정 - {수정 항목 요약}
  ```

  - 수정 항목이 여러 개면 가장 대표적인 항목 위주로 요약한다.

### 7. 원격 push 및 PR 생성

- `git push origin {브랜치명}` 으로 push한다.
- `gh pr create` 로 PR을 생성한다.
  - `--base`: PR `{PR_NUMBER}`의 base branch (1단계에서 조회한 값)
  - `--head`: 방금 생성한 fix 브랜치
  - `--title`: `fix: AI 리뷰 수정 ({N}차) - {수정 항목 요약}`
  - `--body`: 수정 항목 목록 + `관련 PR: #{PR_NUMBER}` 포함

### 8. 완료 안내

- 생성된 PR URL을 사용자에게 안내한다.
- 수정하지 않은 항목(권장 사항, 위험 낮음 판단 항목)이 있으면 해당 목록도 함께 안내한다.
