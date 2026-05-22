# Drift Protocol

작업 수행 중 `workspace/` 내의 도메인 지식(`context/`)이나 project 산출물(`project.md`, `prompts/*.md`, `features/`)이 *실제 구현 코드와 일치하지 않을 때* 적용하는 대응 규약입니다.

원천 규정은 [`skills/context/lifecycle/drift-protocol.md`](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md) (SSOT) 파일에 명시되어 있으며, 이 페이지에서는 해당 규칙의 도입 배경과 구체적인 적용 시점을 다룹니다.

## 두 가지 Drift 카테고리

### § A — 도메인 지식 Drift (`context/`)

`workspace/context/{domain}.md`에 정의된 정보가 실제 code와 일치하지 않는 경우

예시:
- 도메인 파일에는 '쿠폰 만료는 `end_date`만 확인'으로 기술되어 있으나, 실제 code는 `valid_until` column을 사용 중인 경우
- `MANIFEST.md` 내 진입 파일(entry file)의 경로가 refactoring으로 변경되었으나 갱신되지 않은 경우

### § B — 프로젝트 산출물 Drift (`projects/{P}/`)

`project.md`, `features/NN-*.md`, `prompts/*.md` 파일의 내용이 현재 개발 진행 상황과 일치하지 않는 경우

예시:
- `prompts/planner.md`에 기재된 기능별 사전 확인 사항(pre-check)이 이전 feature 번호를 가리키고 있는 경우
- `features/01-*.md` 기능이 이미 구현되었으나 상태가 미개발로 남아 있는 경우

## 발견과 보고 주체

| 에이전트 | 감지 범위 |
|---|---|
| **Planner** | § A (계획 수립 과정에서 도메인 지식과 code 비교) + § B (`project.md`, `prompts/` 점검) |
| **Generator** | § A (구현 중 도메인 지식 의존 시 검증) + § B (`prompts/generator.md`와 실제 구현 패턴 비교) |
| **Evaluator** | § A와 § B 모두 감지 가능 (검증 단계에서 불일치 현상이 가장 명확히 드러남) |

## 대응 규약 (요약)

1. **단건 발견** — 작업을 계속 진행하되 불일치하는 부분을 사용자에게 보고하고, `project.md`의 drift 메모 섹션에 기록합니다.
2. **누적 임계치 도달 (3건 이상)** — 진행 중인 작업을 중단하고 사용자에게 우선 drift 정리를 요청합니다. 그렇지 않으면 잘못된 가정을 바탕으로 작성된 코드가 누적되는 문제가 발생합니다.
3. **자체 판단에 따른 임의 수정 금지** — drift 현상이 사용자의 의도적인 변경(예: 도메인 모델 고도화)일 수도 있으므로, 반드시 사용자의 명시적 동의와 확인 과정을 거쳐야 합니다.

## 자동 수정이 아닌 기록을 지향하는 이유

drift가 임의로 자동 수정되면 다음과 같은 한계가 발생합니다:
- 사용자가 작업 과정에서 어떤 정보가 변경되었는지 직관적으로 인지하지 못합니다.
- 사용자의 의도된 변경(예: `valid_until`로의 column명 리팩토링)이 단순 동기화 작업으로 누락될 수 있습니다.
- evaluator가 명확한 증거에 기반해 구현 내용을 판정하기 어려워집니다.

따라서 명시적 기록과 사용자 결정을 바탕으로 안전하고 되돌릴 수 있는(reversible) 흐름을 유지합니다.

## 최종 수정 권한

발견한 agent가 임의로 변경하지 않으며, **사용자의 결정에 따라 적절한 tool을 사용하여 수정**합니다.

- 도메인 지식(`context/`) 수정: `/pilot:learn`으로 재추출하거나 사용자가 직접 수동 편집
- 프로젝트 산출물(`project.md`, `prompts/`) 수정: `/pilot:analyze --regen-agents` 또는 `/pilot:doctor --fix` 실행

수정 완료 후 cycle을 재시작하여 drift가 해결된 깨끗한 context 위에서 계획을 다시 수립합니다.

## 도구의 지원

- **`orchestrate-load.py`** — `plugin_version` 비교 시 schema 변경을 감지하면 hints에 경고(WARN)를 주입합니다.
- **`/pilot:doctor`** — `analyzed` 및 `tdd` flag 상태와 실제 파일 구조 간의 불일치를 정기적으로 점검합니다.
- **`docs_build.py --check`** — 문서 사이트의 `reference/`가 SSOT와 어긋났는지 검증합니다 (문서 사이트 빌드를 위한 보조 검사).

## 다음 단계

- [SSOT와 Derived](ssot-and-derivation.md): drift가 발생하는 경계 구분
- How-to: [Doctor 진단·마이그레이션](../how-to/doctor-migration.md) — 정기 점검 flow
- Reference: [drift-protocol.md SSOT](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md)
