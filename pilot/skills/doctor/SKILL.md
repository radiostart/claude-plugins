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

워크스페이스·프로젝트 정합성을 검사한다. 검사 범위·판정 기준·출력 형식·처방은 스크립트가 출력에 전부 포함한다 — 로직 SSOT 는 `tools/doctor.py` (진단 모드는 `tools/doctor/diagnose.py`).

대상: $ARGUMENTS (생략 시 STATE.md 의 `진행중` 프로젝트)

## 동작

아래 Bash 명령을 실행해 결과를 사용자에게 그대로 출력한다 (인자로 프로젝트명 전달 시 `--project {PROJECT}` 덧붙임):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

exit code: `0` — ERROR 없음 (PASS / WARN 만) · `1` — ERROR 1 건 이상.

## 플래그

- `--fix` — auto-fixable 항목 자동 수정 (`.gitignore` secret 패턴 주입·STATE.md 이력 정리·schema 업그레이드 등).
- `--diagnose` — 실패 진단 모드. 정합성 검사와 독립적으로 런타임 실패 패턴 (`loop`·`red-miss`·`repeat-not-ready`·`scope-violation`·`none`) 을 진단한다. exit code: `0` (pattern=none) · `1` (감지). 호출 시점: evaluator `NOT_READY` 2회 / 동일 도구 반복 의심 / 완료 선언인데 체크리스트·REPORT 비어있을 때.
- `--schema` — 플러그인 구조 전용 검사 (workspace 와 무관, `workspace` 인자 없이 실행). CI 연동은 #20 에서 `validate.yml` 신설 예정 — 현재는 수동 실행. 스키마 규칙: [`PLUGIN_SCHEMA_NOTES.md`](../../.claude-plugin/PLUGIN_SCHEMA_NOTES.md).

## 임베디드 호출 시 출력 규칙 (정본)

다른 스킬·절차가 자체 흐름 마지막 단계로 `doctor.py workspace` 를 실행할 때(예: `project`·`create-feature`·`analyze` 6-5·`tdd-activation` §6) 따르는 공통 규칙: ERROR 또는 WARN 이 있으면 **원문을 사용자에게 그대로 출력**한다(요약하면 어떤 파일·필드가 문제인지 직접 확인할 수 없다) · 모두 PASS 면 `doctor: all checks passed` 한 줄만 표시 · 비차단(읽기 전용 점검이므로 호출부 절차를 중단시키지 않는다). 호출부는 이 규칙을 재서술하지 않고 본 절 참조만 남긴다.

## Onboarding Health (모델 점검)

`doctor.py` 출력 자체에는 온보딩 점검 섹션이 없다 (v0.9.0+ 구조 정합성 검사로 축소 — 근거: `docs/audits/2026-07-24-audit-4-python.md` § B). `/pilot:doctor` **스킬 경유 호출**에서만 아래 조건으로 모델이 직접 점검·안내한다. **임베디드 호출**(`project`·`create-feature`·`analyze` 6-5·`tdd-activation` §6)에서는 이 nudge 가 발화하지 않는다 — 의도된 다운그레이드이며, 신규 사용자 온보딩 funnel 은 [`docs/tutorial/getting-started.md`](../../docs/tutorial/getting-started.md) 가 커버한다.

- **발동 조건**: `context/MANIFEST.md` 의 `## 도메인 분류` 표 행 0건 **또는** `STATE.md` 등록 프로젝트(진행중/대기) 0건.
- **점검 5항목**: (1) `config.md` 의 `## learn 언어 패턴`·`## scope 카테고리`·`## Ignore` 3섹션 채움 여부 (2) `context/scope/` 에 `*.md` 존재 여부 (3) `STATE.md` 진행중/대기 프로젝트 ≥1 여부 (4) `MANIFEST.md` `## 도메인 분류` 표 행 ≥1 여부 (5) 활성 프로젝트 `features/` 에 `*.md` ≥1 여부.
- **처방 3종**: 미채움 항목에 따라 `/pilot:learn {진입파일}`(도메인 학습) · `/pilot:project {이름}`(프로젝트 등록) · `/pilot:create-feature`(feature 작성) 를 안내.

## 제약

- 스크립트는 순수 파이썬 stdlib 만 사용 (외부 의존 없음)
- 검사는 **비파괴** — 읽기만 함, 파일 수정 안 함 (`--fix` 제외)
- 실패 시 fix 제안은 출력하되 자동 적용 안 함. 사용자가 해당 스킬을 재실행.
