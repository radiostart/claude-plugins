---
name: doctor
description: >-
  pilot 워크스페이스·프로젝트의 정합성을 검사한다. 상태 이상·드리프트·
  부분 설정이 의심될 때, 또는 정기 점검·진단을 원할 때 사용한다.
  STATE.md·MANIFEST.md·config.md 존재 여부, `.agent-state.yml` 스키마,
  `analyzed`·`tdd` 플래그가 실제 파일 상태와 일치하는지 검사해 STATE
  corrupt 같은 조용한 문제를 조기 감지한다.
---

# /pilot:doctor

워크스페이스·프로젝트 정합성을 검사한다.

대상: $ARGUMENTS (생략 시 STATE.md 의 `진행중` 프로젝트)

---

## 동작

아래 Bash 명령을 실행해 결과를 사용자에게 그대로 출력한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

인자로 프로젝트명이 전달되면 `--project` 플래그로 전달:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --project {PROJECT}
```

스크립트가 정합성을 검사하고 ANSI 컬러 포함 결과를 stdout 으로 출력한다. exit code:

- `0` — ERROR 없음 (PASS / WARN 만)
- `1` — ERROR 1 건 이상

`--fix` 플래그를 추가하면 auto-fixable 항목을 자동 수정한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --fix
```

**`--fix` 마이그레이션 동작 (v0.1.0 → v0.2.0)**

pilot v0.2.0 부터 `## learn 언어 패턴` 의 default 표가 SKILL.md 에서 제거됐다. `--fix` 실행 시 다음 조건을 자동 감지해 사용자에게 마이그레이션을 제안한다:

- **감지 조건**: `.agent-state.yml.plugin_version` 이 `0.1.x` 또는 부재 + 현재 plugin 이 `0.2.0+` + `workspace/context/config.md` 의 `## learn 언어 패턴` 두 표 모두 빈 행.
- **동작**: interactive 환경에서 `a) 주입 / b) 거부 / c) 미루기` 선택. non-interactive 환경에서는 자동 미루기 (hang 방지).
- **결과**:
  - `a) 주입`: v0.1.0 default 5 언어 표를 `config.md` 에 자동 주입 + `.agent-state.yml.migration_v0_2_0: accepted` + `plugin_version: 0.2.0`.
  - `b) 거부`: config 빈 채로 유지 + `migration_v0_2_0: declined` + `plugin_version: 0.2.0`.
  - `c) 미루기`: 변경 없음, 다음 `--fix` 호출 시 다시 묻기.
- **부분 정의 사용자**: `## learn 언어 패턴` 에 이미 행이 있으면 마이그레이션 skip + INFO.
- **신규 사용자** (`plugin_version: 0.2.0` 부터): 마이그레이션 skip.

---

## 검사 범위

### Workspace

- `workspace/` 존재
- `workspace/STATE.md` 존재 + `진행중` 행 정확히 1 개 (0 = WARN, 2+ = ERROR)
- `workspace/context/MANIFEST.md` 존재
- `workspace/context/config.md` 존재 (없으면 WARN)

### Project

- `.agent-state.yml` 존재 + `schema: v1.2` (v1·v1.1 은 업그레이드 권장 WARN)
- `analyzed` 필드 ↔ `features/*.md` (`.plan.md` 제외) 실제 존재 일치
- `tdd` 필드 ↔ `project.md` 의 `**TDD 모드**` 문자열 일치
- `pr_base_branch` (있을 경우) ↔ `git ls-remote origin <X>` 존재 일치 (stale 시 WARN)

스키마 상세: [state-schema.md](../context/lifecycle/state-schema.md)

---

## 출력 예시

```
pilot doctor  workspace: /path/to/workspace

Workspace:
  [PASS] workspace/: 존재
  [PASS] STATE.md: 진행중: MyProject
  [PASS] context/MANIFEST.md: 존재
  [PASS] context/config.md: 존재

Project (MyProject):
  [PASS] MyProject/.agent-state.yml: schema v1.2
  [WARN] MyProject analyzed: state.yml analyzed=false 이지만 features/ 에 3 개 존재
         → /pilot:analyze 재실행으로 state.yml 동기화
  [PASS] MyProject tdd: tdd=false, 일치

요약: 5 PASS · 1 WARN · 0 ERROR
```

---

## 언제 실행하나

- 프로젝트 활성화 직후 상태 확인 (`/pilot:project {이름}` 후)
- `analyze` · `tdd` 실행 직후 state 갱신 확인
- drift 의심 시 수동 점검
- 신규 팀 합류 시 workspace 구조 검증

향후 hook 연동 (post-project / post-analyze / post-tdd) 으로 자동 실행 예정.

---

## 실패 진단 모드 (`--diagnose`)

기존 정합성 검사와 독립. 런타임 실패 패턴을 4-phase (capture → diagnose → reduce → report) 로 진단한다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --diagnose
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --diagnose --project MyProject
```

검출 패턴:

| 패턴 | 의미 | 판정 근거 |
|---|---|---|
| `loop` | 에이전트 루프 의심 | `.plan.md` 에 동일 설명 3회+ 반복 |
| `red-miss` | TDD Red 증거 누락 | `tdd: true` 인데 스텝 대비 `[Red]` 마크 부족 |
| `repeat-not-ready` | 동일 feature 2회+ 반려 | `.plan.md` / `project.md` 에 `NOT_READY` · `반려` 누적 |
| `scope-violation` | `.focus.md` scope 외 편집 | git diff 파일과 scope 불일치 |
| `none` | 정상 | 감지된 패턴 없음 |

출력:

```
## DIAGNOSIS
- project: MyProject
- pattern: red-miss | repeat-not-ready | loop | scope-violation | none
- evidence: {근거 요약}
- recommended_action: {권장 액션}
- confidence: high | medium
```

exit code: `0` (pattern=none) · `1` (패턴 감지). 복수 패턴 동시 감지 시 우선순위는 `red-miss > repeat-not-ready > scope-violation > loop` 이며 이 때 `confidence: medium`.

언제 호출:

- evaluator 가 같은 feature 에 `status: NOT_READY` 를 2회 출력했을 때
- 에이전트가 동일 도구·명령을 반복하는 것으로 의심될 때
- 체크리스트·REPORT 기록이 비어있는데 완료 선언된 경우 (Red 증거 누락 의심)

---

## 스키마 검사 모드 (`--schema`)

플러그인 구조 전용 검사. workspace 와 무관.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --schema
```

검사 범위: [`.claude-plugin/PLUGIN_SCHEMA_NOTES.md`](../../.claude-plugin/PLUGIN_SCHEMA_NOTES.md) 기준.

- `plugin.json` 필수·금지 키
- `hooks/hooks.json` matcher 허용값
- `skills/*/SKILL.md` · `agents/*.md` frontmatter
- `version` ↔ git tag 일치 (불일치는 WARN)

CI 에서 자동 실행 — `.github/workflows/validate.yml`.

---

## 제약

- 스크립트는 순수 파이썬 stdlib 만 사용 (외부 의존 없음)
- 검사는 **비파괴** — 읽기만 함, 파일 수정 안 함
- 실패 시 fix 제안은 출력하되 자동 적용 안 함. 사용자가 해당 스킬을 재실행.
