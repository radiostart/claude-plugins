# Drift Protocol

작업 중 `workspace/` 의 도메인 지식 (`context/`) 또는 프로젝트 산출물 (`project.md`·`prompts/*.md`·`features/`) 이 *실제 코드와 어긋난다* 는 사실을 발견했을 때의 대응 규약입니다.

근거는 [`skills/context/lifecycle/drift-protocol.md`](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md) (SSOT). 본 페이지는 그 SSOT 의 *이유* 와 *적용 시점* 을 다룹니다.

## 두 가지 drift 카테고리

### § A — 도메인 지식 drift (`context/`)

`workspace/context/{domain}.md` 가 *실제 코드* 와 다름.

예:
- 도메인 파일에 "쿠폰 만료는 `end_date` 만 확인" 으로 적혀 있지만 실제 코드는 `valid_until` 컬럼을 사용.
- MANIFEST 의 진입 파일 경로가 리팩터 후 옮겨졌는데 갱신 안 됨.

### § B — 프로젝트 산출물 drift (`projects/{P}/`)

`project.md`·`features/NN-*.md`·`prompts/*.md` 가 *현재 상태* 와 다름.

예:
- `prompts/planner.md` 의 *기능별 사전 확인 사항* 이 옛 feature 번호 매김으로 남아 있음.
- `features/01-*.md` 가 이미 구현됐는데 상태가 그대로.

## 누가 어떻게 발견하나

| 에이전트 | 발견 범위 |
|---|---|
| **Planner** | § A (계획 수립 중 도메인 지식과 코드 비교) + § B (project.md·prompts/) |
| **Generator** | § A (구현 중 도메인 지식 의존 시) + § B (prompts/generator.md 와 실제 패턴 비교) |
| **Evaluator** | § A·§ B 모두 — 검증 단계에서 가장 잘 보인다 |

## 대응 규약 (요약)

1. **단건 발견** — 작업을 계속하되 *해당 라인을 사용자에게 보고* + `project.md` 의 *드리프트 메모* 섹션에 기록.
2. **누적 임계 (3 건 이상)** — 작업 중단. 사용자에게 *우선 drift 정리* 를 요청. 그러지 않으면 잘못된 가정 위에 쌓인 작업이 계속 늘어남.
3. **자체 판단으로 침묵 수정 금지** — drift 가 사용자의 의도된 변경일 수도 있다 (예: 도메인 모델 진화). 항상 사용자 확인.

## 왜 *지우는* 게 아니라 *기록* 인가

drift 가 자동 수정되면:
- 사용자가 *언제 무엇이 바뀌었는지* 모름.
- 의도된 변경 (예: `valid_until` 로 컬럼명 진화) 이 *우연한 동기화* 로 처리됨.
- evaluator 의 *증거 기반 판정* 이 약해짐.

명시 기록 + 사용자 결정이 더 보수적이지만 *되돌릴 수 있는* 흐름입니다.

## 누가 결국 수정하나

발견 에이전트가 아니라 **사용자가 결정한 후 적절한 도구가 수정** 합니다:

- 도메인 지식 (`context/`) 수정 → `/pilot:learn` 으로 *재추출* 또는 사용자 수동 편집.
- 프로젝트 산출물 (`project.md`·`prompts/`) → `/pilot:analyze --regen-agents` 또는 `/pilot:doctor --fix`.

수정 후 다시 사이클 진입 — drift 가 정리된 컨텍스트 위에서 계획 새로 작성.

## 도구의 지원

- **`orchestrate-load.py`** — `plugin_version` 비교 시 schema 진화를 감지하면 hints 에 WARN 추가.
- **`/pilot:doctor`** — `analyzed` · `tdd` 플래그와 실제 파일 상태의 불일치 정기 점검.
- **`docs_build.py --check`** — 사이트의 reference/ 가 SSOT 와 어긋났는지 (별 차원의 drift, 사이트 빌드 보조).

## 다음

- [SSOT 와 derived](ssot-and-derivation.md) — drift 가 발생하는 *경계 라인*.
- How-to: [Doctor 진단·마이그레이션](../how-to/doctor-migration.md) — 정기 검사 흐름.
- Reference: [drift-protocol.md SSOT](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md).
