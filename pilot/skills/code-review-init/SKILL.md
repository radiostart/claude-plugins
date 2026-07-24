---
name: code-review-init
description: >-
  워크스페이스에 언어별 코드 리뷰 룰 파일 (`workspace/context/review/{lang}.md`) 을
  셋업한다. `@pilot-code-review` 가 변경 언어의 룰 파일 부재를 인지하면 본 스킬로
  1 회성 생성. 3 가지 시작 전략 (예시 복사 / 빈 템플릿 / AI 생성) 중 사용자가 선택.
  생성 후 사용자가 본문 편집해 팀 컨벤션 반영.
---

# /pilot:code-review-init

워크스페이스의 언어별 코드 리뷰 룰 파일 `workspace/context/review/{lang}.md` 를 셋업한다.

대상 언어: $ARGUMENTS

## 사전 확인

1. `$ARGUMENTS` 첫 토큰을 `{lang}` 슬러그로 사용 (`python`/`typescript`/`ruby`/`java`/`go` 등). 비어있으면 `git ls-files | awk -F. '{print $NF}' | sort | uniq -c | sort -rn | head -5` 로 dominant 확장자를 감지해 슬러그 추론(`.py→python`·`.ts/.tsx→typescript`·`.rb→ruby` 등, 매칭 없으면 사용자 질의) 후 "**{추정 lang} 로 진행할까요?**" 확인.
2. `workspace/context/` 없으면 [`messages.md`](../context/shared/messages.md) 의 `workspace_missing` 안내 후 종료.
3. 대상 경로 `workspace/context/review/{lang}.md` (폴더 없으면 생성). **이미 존재하면 사용자 확인 없이 덮어쓰지 않는다** — "덮어쓰기 / 백업 후 새로 생성(`{경로}.bak.{timestamp}`) / 취소" 질의.

## 동작 — 시작 전략 3 종 (택 1 질의)

### 전략 A — 사전 작성된 예시 복사

`${CLAUDE_PLUGIN_ROOT}/examples/code-review/{lang}.md` 존재 시만 제시(부재 시 비활성, B/C 만). 헤더 안내 블록 제거 후 사용 프레임워크 확인(ruby→Rails·php→Laravel/Symfony·kotlin→Android/서버사이드·java→Spring·js/ts→React 등) → 미사용 프레임워크 섹션 제거 → Write.

### 전략 B — 빈 형식 템플릿 복사

`${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-rules-template.md` Read → 안내부 제거 → `{언어}` placeholder 를 사람이 읽는 이름으로 치환(lint 예시도 해당 언어로 또는 삭제) → Write → "본문의 관용구·결함 섹션을 직접 채우세요" 안내.

### 전략 C — AI 생성 (코드베이스 기반)

`git ls-files | grep -E '\.({lang 확장자})$' | head -50` 로 상위 파일 Read 해 컨벤션(logger·테스트 프레임워크·DI·ORM) 파악 → `review-rules-template.md` 형식에 발견 패턴 반영 → **미리보기 제시 후 "이대로 저장/수정 후 저장/취소" 질의** — **자동 저장 금지**, LLM 추측 기반 draft 임을 명시.

## 결과 출력

생성 경로·전략·룰 섹션 수·유지된 프레임워크 섹션 + 다음 단계(본문 검토·편집 → `/pilot:review` 실행 시 자동 로드) 안내.

## Do-NOT

- 기존 파일을 사용자 확인 없이 덮어쓰지 않는다.
- 전략 C 결과를 자동 저장하지 않는다(반드시 미리보기 → 승인).
- 생성된 룰의 정확성을 보증하지 않는다 — 사용자 책임(draft 도우미).
- `workspace/` 외부 경로에 Write 금지.

## 호출 시점

- `/pilot:review` 결과에서 `{lang}.md` 부재로 baseline 만 적용됐음을 인지 → 사용자가 명시 호출
- 새 언어 도입 시 선제적 호출 · `/pilot:init` 후 주력 언어 셋업
