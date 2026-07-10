---
name: commit
description: >-
  사용자가 "커밋해줘", "변경 묶어서 커밋" 등 git 커밋 작성을 요청할 때
  사용한다. 변경 파일을 확인하고 `skills/context/shared/commit.md`
  규칙(scope 표기, 한국어 본문, 50자 이내 요약)에 맞춰 메시지를 작성해
  커밋한다. unstaged 파일이 있으면 포함 여부를 사용자에게 확인한다.
---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

커밋 규칙 로드:

- `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/commit.md` 가 존재하면 Read 한다.
- 존재하지 않으면 fallback 규칙을 사용한다:
  - scope 없이 한국어 제목 + 50자 이내 + 필요 시 본문.

## 수행

commit.md 의 **커밋 전 흐름**과 **커밋 메시지 규칙**을 그대로 따른다 — unstaged 파일이 있으면 포함 여부를 사용자에게 질의한 뒤, 규칙에 맞춘 메시지 초안을 사용자에게 확인받고 커밋한다. (fallback 시에도 unstaged 질의와 사용자 확인은 동일하게 수행.)
