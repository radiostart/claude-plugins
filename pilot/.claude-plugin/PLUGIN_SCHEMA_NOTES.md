<!-- schema-version: 2026.Q2 -->

# pilot Plugin Schema Notes

## 목적

플러그인 검증기의 암묵적 제약 문서화. 구조 변경 시 회귀 차단 기준.

## plugin.json 규칙

- 권장 필드: `name`, `version`, `description`, `author` 만
- **금지 필드:**
  - `hooks` — 훅은 `hooks/hooks.json` 으로만 선언
  - `agents` / `skills` / `commands` — 파일 기반 자동 인식, 명시 금지
- `version` 은 SemVer, patch 는 자유, minor+ 는 수동 CHANGELOG 권장

## hooks/hooks.json 규칙

- 최상위 `hooks` 객체 필수
- matcher 허용값: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `SessionStart`, `SessionEnd`, `Notification`
- 각 훅 `timeout` 권장 (기본 5)
- 현재 실제 사용 중: `PreToolUse` 매처 하위 `Bash`, `Edit|Write` (정규식 매처 허용 — 툴 이름을 `|` 로 구분)

## SKILL.md frontmatter

- 필수: `name`, `description`
- `description` 은 1024 bytes 이하

## 에이전트 frontmatter (agents/*.md)

- 필수: `name`, `description`, `tools`
- 선택: `model` (미지정 시 기본)

## schema 버전 태그

이 문서는 상단 `<!-- schema-version: 2026.Q2 -->` 주석으로 버전 명시. SDK 변경 시 갱신.
