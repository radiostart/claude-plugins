---
name: init
description: >-
  새 워크스페이스 셋업 — `workspace/` 구조를 초기화한다.
  `workspace/STATE.md` 와 `workspace/context/` 하위의 `MANIFEST.md`·`config.md`
  스켈레톤을 일괄 생성한다. 처음 pilot 을 도입·셋업할 때 사용한다.
---

# /pilot:init

워크스페이스 구조를 일괄 생성한다.

## 사전 확인

workspace 경로 = CWD 기준 `./workspace/`. 폴더 없으면 생성(`mkdir -p workspace/context`).

## 동작

### 1. 스켈레톤 생성

`${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/` 의 각 템플릿을 **대상 존재 시 skip(exists), 없으면 생성(created)** 원칙으로 적용한다(idempotent):

| 템플릿 | 대상 경로 |
| ------ | --------- |
| `templates/STATE.md.template` | `workspace/STATE.md` |
| `templates/MANIFEST.md.template` | `workspace/context/MANIFEST.md` |
| `templates/config.md.template` | `workspace/context/config.md` |

`MANIFEST.md.template` 의 `## 외부 도메인 reference` 는 placeholder 주석만 — 실제 작성은 `/pilot:learn` 이 cross-domain reference 를 처음 발견할 때 수행한다.

> **`rules/`·`scope/`·`enums/` 등 카테고리 폴더는 생성하지 않는다.** 사용자가 MANIFEST.md 를 채우며 구조를 결정하고, 실제 도메인 파일 추가 시점에 필요한 폴더를 만든다.

### 2. wizard 적용 (created 인 경우만)

`config.md` 가 `created` 일 때만 진입(`exists` 면 skip). `--no-wizard` 토큰이 있으면 skip. **어느 단계가 실패해도 abort 금지 — 나머지는 계속 진행** ([guardrails.md](../context/shared/guardrails.md) § A2).

> **표 헤더 고정 스키마 (doctor strict 검증 — 한 글자 오차도 ERROR)**: `## learn 언어 패턴` 표1(의존성 추적) `| 언어 | 의존성 추출 패턴 |` · 표2(역할 분류) `| 역할 | 식별 패턴 |` · `## scope 카테고리` `| scope 헤더 | project.md 대상 H3 | 표 헤더 |`(scope 헤더 값은 `## ` 로 시작) · `## Ignore` `| 패턴 | 사유 |`. 문자열 원문 그대로 보존 필수.

1. **언어 감지** — `${CLAUDE_PLUGIN_ROOT}/tools/init_detect.py` 의 `detect_languages(cwd_path)`(`pathlib.Path`)를 호출해 `## learn 언어 패턴` 두 표에 주입(언어별 default 패턴 — ruby/typescript/python/kotlin/go). 기존 행 있으면 dedupe 병합(사용자 수동 추가 보존). 감지 0건 → 헤더만 남기고 빈 행 + INFO.
2. **scope 후보 감지** — `detect_scope_candidates(cwd_path)` 호출해 `## scope 카테고리` 표(scope 헤더/project.md 대상 H3/표 헤더 3컬럼 강제)에 주입. 같은 H3 가 여러 폴더에서 매핑되면 1행만 dedupe. 후보 0건 → default 3행(Routes/Models/Services, 출처: [scope-sync.md](../analyze/references/scope-sync.md) 5-2 canonical) + INFO.
3. **Ignore baseline 주입** — `IGNORE_BASELINE` 10패턴을 `## Ignore` 표에 주입(기존 행 dedupe 병합).

## 결과 출력

파일 상태(created/exists) 3종 + wizard 결과(언어 감지 N개·scope 후보 M개·Ignore baseline P개, skip 시 사유) + 다음 단계(`/pilot:project {프로젝트명}`) + 점진적으로 채울 항목(MANIFEST/config/rules·scope) 안내.

## 참고

- 워크스페이스를 **처음 만들 때만** 사용 — 프로젝트 추가는 `/pilot:project`.
- 생성 파일은 사용자가 직접 채워야 하는 스켈레톤 — 모두 비워둬도 동작한다.
- `--no-wizard` 시 v0.2.x 이전과 동일하게 빈 스켈레톤만 생성.
