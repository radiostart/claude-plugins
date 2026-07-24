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

워크스페이스·프로젝트 정합성을 검사한다. 검사 범위·판정 기준·출력 형식·처방은
스크립트가 출력에 전부 포함한다 — 로직 SSOT 는 `tools/doctor.py` (진단 모드는 `tools/doctor/diagnose.py`).

대상: $ARGUMENTS (생략 시 STATE.md 의 `진행중` 프로젝트)

---

## 동작

아래 Bash 명령을 실행해 결과를 사용자에게 그대로 출력한다 (인자로 프로젝트명 전달 시 `--project {PROJECT}` 덧붙임):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

exit code: `0` — ERROR 없음 (PASS / WARN 만) · `1` — ERROR 1 건 이상.

---

## 플래그

- `--fix` — auto-fixable 항목 자동 수정. v0.1.0 → v0.2.0 마이그레이션 동작 (`## learn 언어 패턴` default 표 자동 주입 여부 질의) 상세: [`references/migration.md`](references/migration.md).
- `--diagnose` — 실패 진단 모드. 정합성 검사와 독립적으로 런타임 실패 패턴 (`loop`·`red-miss`·`repeat-not-ready`·`scope-violation`·`none`) 을 진단한다. exit code: `0` (pattern=none) · `1` (감지). 호출 시점: evaluator `NOT_READY` 2회 / 동일 도구 반복 의심 / 완료 선언인데 체크리스트·REPORT 비어있을 때.
- `--schema` — 플러그인 구조 전용 검사 (workspace 와 무관, `workspace` 인자 없이 실행). CI 연동은 #20 에서 `validate.yml` 신설 예정 — 현재는 수동 실행. 스키마 규칙: [`PLUGIN_SCHEMA_NOTES.md`](../../.claude-plugin/PLUGIN_SCHEMA_NOTES.md).

---

## 임베디드 호출 시 출력 규칙 (정본)

다른 스킬·절차가 자체 흐름 마지막 단계로 `doctor.py workspace` 를 실행할 때(예: `project`·`create-feature`·`analyze` 6-5·`tdd-activation` §6) 따르는 공통 규칙:

- ERROR 또는 WARN 이 있으면 **원문을 사용자에게 그대로 출력**한다 (요약하면 어떤 파일·필드가 문제인지 직접 확인할 수 없다).
- 모두 PASS 면 `doctor: all checks passed` 한 줄만 표시한다.
- 비차단 — 호출부 절차 자체를 중단시키지 않는다 (읽기 전용 점검이므로).

호출부는 이 규칙을 재서술하지 않고 본 절 참조만 남긴다.

---

## 제약

- 스크립트는 순수 파이썬 stdlib 만 사용 (외부 의존 없음)
- 검사는 **비파괴** — 읽기만 함, 파일 수정 안 함 (`--fix` 제외)
- 실패 시 fix 제안은 출력하되 자동 적용 안 함. 사용자가 해당 스킬을 재실행.
