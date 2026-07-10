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
- 이벤트 허용값: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `SessionStart`, `SessionEnd`, `Notification`, `PermissionRequest`
- matcher (툴 이름 정규식, `|` 구분) 는 이벤트와 별개 개념 — `PreToolUse`/`PostToolUse` 에서 사용
- 각 훅 `timeout` 권장 (기본 5)
- 현재 실제 사용 중: `PreToolUse`(`Bash`, `Edit|Write`), `PostToolUse`(`Edit|Write`), `PermissionRequest`, `Notification`

## skills/ 하위 비스킬 디렉터리 관행

- `skills/` 하위에서 `SKILL.md` 가 없는 디렉터리는 스킬로 등록되지 않는다.
- `skills/context/` 는 이 성질을 이용한 **자료 컨테이너** (스킬·에이전트가 참조하는 SSOT 모음) — 의도된 배치이며, 검증기/SDK 변경 시 이 성질이 유지되는지가 회귀 판단 기준이다.

## tools/ 파일 명명 규칙

- 신규 도구는 `snake_case.py` (파이썬 import 가능 — 테스트 편의).
- 기존 kebab-case 도구(orchestrate-load.py 등)는 **동결** — 에이전트·스킬·docs 의 경로 참조가 광범위해 리네임 비용이 이득보다 크다. 이원화를 더 늘리지 않는 것이 목표.

## SKILL.md frontmatter

- 필수: `name`, `description`
- `description` 은 1024 bytes 이하

## 에이전트 frontmatter (agents/*.md)

- 필수: `name`, `description`, `tools`
- 선택: `model` (미지정 시 기본)

## schema 버전 태그

이 문서는 상단 `<!-- schema-version: 2026.Q2 -->` 주석으로 버전 명시. SDK 변경 시 갱신.
