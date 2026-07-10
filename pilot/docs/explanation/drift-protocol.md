# Drift Protocol

작업 수행 중 `workspace/` 하위 문서 — 도메인 지식(`context/`)과 project 산출물(`project.md`, `prompts/*.md`) — 가 *실제 구현 코드와 일치하지 않을 때* 적용하는 대응 규약입니다.

규칙 정본: [`skills/context/lifecycle/drift-protocol.md`](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md) (SSOT — 에이전트별 트리거 매트릭스·누적 임계 처리 포함). 이 페이지는 규칙의 도입 배경과 두 카테고리의 간단한 예시만 다룹니다.

## 두 가지 Drift 카테고리 (예시)

### § A — 도메인 지식 Drift (`context/`)

`workspace/context/{domain}.md`에 정의된 정보가 실제 code와 일치하지 않는 경우

예시:
- 도메인 파일에는 '쿠폰 만료는 `end_date`만 확인'으로 기술되어 있으나, 실제 code는 `valid_until` column을 사용 중인 경우
- `MANIFEST.md` 내 진입 파일(entry file)의 경로가 refactoring으로 변경되었으나 갱신되지 않은 경우

### § B — 프로젝트 산출물 Drift (`projects/{P}/`)

`project.md`, `prompts/*.md` 파일의 내용(클래스명·상태값·경로 등)이 실제 코드·진행 상황과 일치하지 않는 경우

예시:
- `prompts/planner.md`에 기재된 기능별 사전 확인 사항(pre-check)이 이전 feature 번호를 가리키고 있는 경우
- `project.md`의 관련 파일 표에 기재된 클래스명·경로가 리팩토링 이후의 실제 코드와 다른 경우

카테고리별 적용 대상, 에이전트별 감지 범위(트리거 매트릭스), 누적 임계 도달 시 처리 방식은 모두 SSOT 문서가 정의합니다.

## 자동 수정이 아닌 기록을 지향하는 이유

drift가 임의로 자동 수정되면 다음과 같은 한계가 발생합니다:
- 사용자가 작업 과정에서 어떤 정보가 변경되었는지 직관적으로 인지하지 못합니다.
- 사용자의 의도된 변경(예: `valid_until`로의 column명 리팩토링)이 단순 동기화 작업으로 누락될 수 있습니다.
- evaluator가 명확한 증거에 기반해 구현 내용을 판정하기 어려워집니다.

따라서 명시적 기록과 사용자 결정을 바탕으로 안전하고 되돌릴 수 있는(reversible) 흐름을 유지합니다.

## 다음 단계

- [SSOT와 Derived](ssot-and-derivation.md): drift가 발생하는 경계 구분
- How-to: [Doctor 진단·마이그레이션](../how-to/doctor-migration.md) — 정기 점검 flow
- Reference: [drift-protocol.md SSOT](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/drift-protocol.md) — 트리거 매트릭스·누적 임계 포함
