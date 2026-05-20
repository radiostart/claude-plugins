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

> **페르소나 — diagnostician** (이 스킬 SSOT, 공통 톤 [`identity.yml`](../context/shared/identity.yml) 위에 덧씌움)
> - voice: 증상 → 근거 → 처방. 확신 없으면 가설로 표시
> - phrasing: "FAIL: <증상> · 근거: <파일:라인> · 처방: <명령>"
> - forbid: "근거 없는 단정 처방" / "증상 없이 처방만 출력"

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

`--fix` 의 v0.1.0 → v0.2.0 마이그레이션 동작 (`## learn 언어 패턴` default 표 자동 주입 여부 질의) 상세: [`references/migration.md`](references/migration.md).

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
- `tdd` 필드 ↔ `project.md` 의 `**TDD 모드**` 문자열 ↔ `prompts/{flow,planner,generator,evaluator}.md` 의 백업 마커 3-way 일치 (인수인계 line 130 패턴)
- `pr_base_branch` (있을 경우) ↔ `git ls-remote origin <X>` 존재 일치 (stale 시 WARN)

스키마 상세: [state-schema.md](../context/lifecycle/state-schema.md)

---

## Onboarding Health

기존 구조 정합성 검사 직후 신규 사용자 관점 5개 항목을 WARN 수준으로 추가 진단한다.

```
── Onboarding Health ─────────────────
OH-1  config 핵심 섹션:        PASS|WARN
OH-2  scope/ 채움:              PASS|WARN
OH-3  첫 project 등록:          PASS|WARN
OH-4  MANIFEST 진입파일:        PASS|WARN
OH-5  features/ 진입 가능:      PASS|WARN|N/A
```

- **OH-1**: `config.md` 의 `## learn 언어 패턴` / `## scope 카테고리` / `## Ignore` 3 섹션 표 본문 행 수 ≥ 1.
- **OH-2**: `workspace/context/scope/` 에 `*.md` 파일 ≥ 1.
- **OH-3**: `STATE.md` 에 `진행중` 또는 `대기` 프로젝트 ≥ 1.
- **OH-4**: `MANIFEST.md` 의 `## 도메인 분류` 표 본문 행 ≥ 1.
- **OH-5**: `projects/{project}/features/` 에 `*.md` ≥ 1. 프로젝트 인자 미지정 시 `N/A`.

**WARN 수준 정책**: exit code 영향 없음 (구조 정합성 ERROR 만 exit 1). 항목마다 처방 1줄 동반.

**`--fix` 미지원**: onboarding-health 는 사용자의 실제 작업 의도가 필요. `--fix` 호출 시 OH 섹션은 skip + INFO 1줄.

**WARN 5건 동시**: "신규 워크스페이스 감지 — getting-started.md 권장" 안내 1줄 추가 (`pilot/docs/getting-started.md`).

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
  [PASS] MyProject tdd: state=false ↔ project=false ↔ prompts 마커 부재, 3-way 일치

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

정합성 검사와 독립. 런타임 실패 패턴 (`loop`·`red-miss`·`repeat-not-ready`·`scope-violation`·`none`) 을 4-phase (capture → diagnose → reduce → report) 로 진단한다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --diagnose [--project MyProject]
```

- exit code: `0` (pattern=none) · `1` (감지).
- 복수 패턴 동시 감지 시 우선순위: `red-miss > repeat-not-ready > scope-violation > loop` (이 때 `confidence: medium`).
- 호출 시점: evaluator `NOT_READY` 2회 / 동일 도구 반복 의심 / 완료 선언인데 체크리스트·REPORT 비어있을 때.

검출 패턴·판정 근거·출력 형식 상세: [`references/diagnose.md`](references/diagnose.md).

---

## 스키마 검사 모드 (`--schema`)

플러그인 구조 전용 검사 (workspace 와 무관). `plugin.json` 필수·금지 키, `hooks/hooks.json` matcher, `skills/*/SKILL.md` · `agents/*.md` frontmatter, `version` ↔ git tag 일치를 검증한다. CI 자동 실행 (`.github/workflows/validate.yml`). 상세: [`references/schema.md`](references/schema.md).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --schema
```

---

## 제약

- 스크립트는 순수 파이썬 stdlib 만 사용 (외부 의존 없음)
- 검사는 **비파괴** — 읽기만 함, 파일 수정 안 함
- 실패 시 fix 제안은 출력하되 자동 적용 안 함. 사용자가 해당 스킬을 재실행.
