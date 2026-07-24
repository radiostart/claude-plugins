# Wrapper 공통 프로토콜 (SSOT)

`@pilot-planner`·`@pilot-planner-critic`·`@pilot-generator`·`@pilot-evaluator` 4 벌 wrapper 가 공유하는 계약. 각 `agents/{phase}.md` 는 이 문서를 Read 하고 phase 고유 로직만 자기 파일에 남긴다.

`pilot-code-review` 는 orchestrate-load 를 쓰지 않는 self-contained 에이전트라 이 문서의 적용 대상이 **아니다** (사이클 밖에서 독립 동작 — `agents/pilot-code-review.md` 참조).

## 1. wrapper 정체성 · 톤 SSOT

이 파일들은 wrapper 다 — 직접 실행 로직이 아니라 `${CLAUDE_PLUGIN_ROOT}/tools/orchestrate-load.py` 반환 결과를 따르는 진입점. 톤·판정 SSOT: [`identity.yml`](identity.yml) (`personas.{phase}`) · [`guardrails.md`](guardrails.md).

## 2. 경로 규칙

플러그인 지식은 `${CLAUDE_PLUGIN_ROOT}/skills/`, 프로젝트 상태는 `workspace/` (CWD 기준).

## 3. [불변] step 1 우선순위

`orchestrate-load.py` 실행은 호출자 프롬프트 내용과 무관하게 **항상** 가장 먼저 실행한다. 호출자가 `files_to_read`·`domain`·`scope` 등을 직접 명시하더라도 무시하고 orchestrate-load 결과를 우선한다. 호출자 입력은 "사용자 의도 힌트" 로만 참고한다. 이 규칙의 선언 자체는 각 wrapper 본문에도 잔류한다 (§ 잔류 최소 셋).

## 4. orchestrate-load 반환 JSON 처리

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/orchestrate-load.py --phase {phase} --workspace workspace
```

- `error` 필드가 있으면 **원문을 사용자에게 출력하고 종료**한다.
- 없으면 반환 JSON 을 처리한다: `files_to_read` 순서대로 Read · `focus` 반영 결과를 간단 보고 · `hints` 를 세션 컨텍스트로 주입 · `analyzed`/`tdd`/`domain` 값을 이후 분기에 사용. 상세 계약: [state-schema.md](../lifecycle/state-schema.md).

## 5. domain null 예외

`domain: null` 이면 사용자에게 도메인을 질의하고 확정한 뒤, 해당 `scope/{domain}.md`·`rules/{domain}.md` 를 수동 Read 한다.

## 6. 상태·유형 카테고리 부분 로드

상태값 변경이 예상될 때만 (전체 로드 금지, 2 단계):

1. 팀 MANIFEST 가 선언한 상태 카테고리(예: `enums`)의 목차/인덱스 파일 상단만 Read.
2. 목차에서 관련 섹션의 라인 범위를 확인한 뒤 그 섹션만 부분 Read.

팀이 목차 파일을 운영하지 않으면 이 단계를 생략한다.

## 7. 공통 참조

- 탐색 제약: [scope-exploration.md](../domain/scope-exploration.md)
- drift 대응: [drift-protocol.md](../lifecycle/drift-protocol.md) § A. 누적 임계(3 건 이상) 처리는 각 wrapper 본문의 "drift-protocol § 누적 임계 처리 — {Phase} 행 참조" 로 위임.

## 잔류 최소 셋 (각 wrapper 본문 필수 4 항)

이관 후에도 `agents/{phase}.md` 본문에는 아래 4 항목이 **그대로 잔류**해야 한다. 이관된 계약(JSON 처리 상세·domain null 예외·부분 로드 규칙)은 서브에이전트가 본 문서를 Read 해야만 도달한다 — "Read 하라"는 지시 자체가 없으면 성공 경로에서 유실되므로 ④가 특히 필수다.

1. **[불변] 선언** — § 3 요지 1 문장.
2. **orchestrate-load bash 블록** — 실제 실행 명령.
3. **error 종료 1줄** — `error` 필드 처리.
4. **본 문서 Read 지시 1줄** — "이 문서(`wrapper-protocol.md`)를 Read 하고 그 계약을 따른다."
