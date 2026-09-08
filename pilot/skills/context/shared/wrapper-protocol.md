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
- 없으면 반환 JSON 을 처리한다: `files_to_read` 순서대로 Read · `focus` 반영 결과를 간단 보고 · `hints` 를 세션 컨텍스트로 주입 · `tdd`/`mode`/`domain`/`project_phase`/`work_mode` 값을 이후 분기에 사용 (`analyzed` 는 분기 필드가 아니라 보고용 — 실소비처는 doctor·switch 조회뿐이며, 도메인 지식 로드는 `domain` 유무로만 갈린다). 상세 계약: [state-schema.md](../lifecycle/state-schema.md).
- `work_mode` 필드 (`project`|`issue`, 부재 시 project): `issue` 면 각 wrapper 본문의 "이슈 수정 모드" 블록·경로 분기를 활성화한다.

## 5. domain null 예외

`domain: null` 이면 사용자에게 도메인을 질의하고 확정한 뒤, 해당 `scope/{domain}.md`·`rules/{domain}.md` 를 수동 Read 한다.

## 6. 본문 부분 로드 (권장 — 필수 step 아님)

진입 파일 로드 후 특정 주제(feature 키워드·클래스명·소스 경로)의 상세가 필요하면 본문 파일 전체 Read·무차별 Grep 대신 **탐색 → 선별 → 주입** 3단계로 섹션을 좁힌다. 도구는 후보를 좁히고 최종 선택은 에이전트가 한다:

1. **탐색** — `python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<feature 키워드>" --scope {domain} --format manifest --limit 8` → 후보당 1줄 (`[#n] score [type] | file :: heading | L{start}-{end} | {age}d | matched | snippet`). `+필수어` 사전필터 · `--include features/ docs/` 부속 문서 · 소스 경로 질의(`app/services/x.rb`)는 그 파일을 다루는 섹션의 역방향 조회.
2. **선별** — 후보를 feature 명세·plan 의 현재 단계와 대조해 **지금 결정에 필요한 1~3개**만 고른다.
   - `[rules]`·`[boundary]` 후보는 필수어가 맞으면 버리지 않는다 (규칙 누락 → 평가 단계 반려).
   - 관련 후보가 0 이면 질의를 넓혀(동의어·영문명·`+필수어` 제거) 1회 재검색, 그래도 0 이면 진입 파일 목차로 회귀.
   - 고른 섹션과 사유를 1줄 보고한다 (dogfooding 측정 근거).
3. **주입** — `python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py 'select:{file}#{heading},{file}#{heading}' --inject` 1회로 본문을 받는다. 인자는 **작은따옴표**로 감싼다 — 큰따옴표 안의 백틱·`$` 는 쉘이 치환해 헤딩이 비고 파일 전체가 주입된다(도구가 INFO 로 알리지만 그 전에 막는다). `file` 은 manifest 에 표시된 경로 그대로(`--include` 부속 문서 포함), `heading` 은 manifest 줄의 헤딩(백틱 제거본) 일부 — 부분 문자열 매칭. `<context-snippet file heading lines>` 블록, 렌더 총량 12,000B·섹션당 400줄 상한. 잘린 섹션은 블록 뒤 `[잘림 — 나머지: Read …]` 힌트로 이어 읽는다. 상태값(`enums` 등) 확인도 같은 절차.

0건이면 도구가 `--scope`·`+필수어` 제거 등 상태 안내를 낸다 — 실패가 아니다. 도구 부재 시 진입 파일 목차 → 라인 범위 수동 2단계로 대체.

## 7. 공통 참조

- 탐색 제약: [scope-exploration.md](../domain/scope-exploration.md)
- drift 대응: [drift-protocol.md](../lifecycle/drift-protocol.md) § A. 누적 임계(3 건 이상) 처리는 각 wrapper 본문의 "drift-protocol § 누적 임계 처리 — {Phase} 행 참조" 로 위임.

## 잔류 최소 셋 (각 wrapper 본문 필수 4 항)

이관 후에도 `agents/{phase}.md` 본문에는 아래 4 항목이 **그대로 잔류**해야 한다. 이관된 계약(JSON 처리 상세·domain null 예외·부분 로드 규칙)은 서브에이전트가 본 문서를 Read 해야만 도달한다 — "Read 하라"는 지시 자체가 없으면 성공 경로에서 유실되므로 ④가 특히 필수다.

1. **[불변] 선언** — § 3 요지 1 문장.
2. **orchestrate-load bash 블록** — 실제 실행 명령.
3. **error 종료 1줄** — `error` 필드 처리.
4. **본 문서 Read 지시 1줄** — "이 문서(`wrapper-protocol.md`)를 Read 하고 그 계약을 따른다."
