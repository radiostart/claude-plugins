# 도메인 규칙(rules) 작성

!!! info "한 줄 요약"
    `/pilot:learn` 은 코드의 *구조* 만 추출한다. 비즈니스 *규칙* 은 사용자가 직접 정리하고, `MANIFEST.md` 가 그것을 에이전트에 연결한다. 규칙 문서의 위치·구조는 자유 — MANIFEST 가 가리키기만 하면 된다.

## 역할 분리 — learn 이 하는 일, 사용자가 하는 일

| 구분 | `/pilot:learn` (자동) | 사용자 (직접) |
|---|---|---|
| 다루는 것 | 코드의 *구조적 사실* — 파일·시그니처·라우트·상태값 | *비즈니스 규칙* — 정책·제약, "왜·언제" |
| 근거 | 코드에 문자 그대로 있는 것 (`file:line` 인용) | 사람의 판단 — 코드에 없음 |
| 산출 | `context/{domain}.md` (또는 `{domain}/` 폴더) | 규칙 문서 + `MANIFEST.md` 연결 |

`learn` 의 원칙은 *추측 금지* 다. 검증 패턴·상태 enum 같은 *구조* 는 잡지만, "환불은 결제 후 7 일 이내만" 같은 *정책의 의도* 는 코드만 봐서는 알 수 없다 — 그래서 규칙은 사용자 몫이다.

## 핵심은 MANIFEST.md

플러그인이 강제하는 계약은 `workspace/context/MANIFEST.md` **하나뿐** 이다. 에이전트는 MANIFEST 의 `## 도메인 분류` 표에 선언된 도메인 → 진입 파일을 보고 자동 로드한다.

!!! tip "그래서 — 구조는 자유다"
    비즈니스 규칙을 *어떤 파일·어떤 구조로 두든 상관없다.* MANIFEST 가 그 진입점을 가리키기만 하면 에이전트가 읽는다. 잘 해야 하는 건 **MANIFEST.md 를 정확히 쓰는 것** 이다.

## 전제

- `/pilot:learn` 으로 도메인 구조가 부트스트랩돼 있다.

## 절차

### 1. 규칙을 어디에 둘지 정한다 (구조 자유)

정해진 정답은 없다. 도메인 성격에 맞게 고른다 — 예:

- 작은 도메인 → `context/{domain}.md` 안에 `## 규칙` 섹션 하나.
- 규칙이 많은 도메인 → 별도 파일로 (`scope` = 구조 / `rules` = 규칙 두 축 분리).
- sub-domain 구조 → `context/{domain}/policies.md` 처럼 도메인 폴더 안에.

### 2. 규칙을 선언적으로 적는다

코드 스니펫이 아니라 **정책 표현** 으로 쓴다. 구체 문자열(메모 포맷·상태값 의미)은 *한 곳* 에만 둔다.

!!! example "예시 — `context/rules/orders.md` (한 가지 형태일 뿐)"
    ```markdown
    # orders 도메인 규칙

    ## 환불 정책
    - 환불은 결제 완료 후 7 일 이내만 허용. 이후는 고객센터 수동 처리.

    ## 주문 메모 포맷
    - 형식: `[{액션}({필드})]` — 예: `[refund(amount)]`

    ## 상태 전환 규칙
    - `pending → paid → shipped → delivered`. `cancelled` 는 `shipped` 이전만.
    ```

    이건 *하나의 예시* 다 — 같은 내용을 `{domain}.md` 안 섹션으로 둬도, 다른 분류로 쪼개도 된다. 형태가 아니라 *MANIFEST 가 찾을 수 있는가* 가 중요하다.

### 3. MANIFEST.md 가 가리키게 한다

`workspace/context/MANIFEST.md` 의 `## 도메인 분류` 에 규칙 문서를 도메인 진입 경로의 일부로 등록한다. 그래야 `orchestrate-load.py` 가 활성 프로젝트의 도메인을 매칭해 에이전트에게 자동 Read 시킨다. **등록 안 된 파일은 존재해도 로드되지 않는다.**

### 4. agent 파일은 *참조만*

`prompts/*.md` 에 규칙 내용을 복사하지 않는다. "주문 메모는 규칙 문서의 '메모 포맷' 을 따른다" 한 줄로 참조한다 — 같은 규칙을 `generator.md`·`evaluator.md` 양쪽에 박으면 한쪽만 고쳐져 drift 가 난다.

## 흔한 실수

| 실수 | 올바른 방식 |
|---|---|
| 규칙에 코드 블록을 붙여넣음 | 정책을 산문·표로. 구현은 코드에. |
| 규칙을 agent 파일에 직접 박음 | 규칙 문서 한 곳 + 참조 |
| 규칙 문서를 만들고 MANIFEST 에 등록 안 함 | 등록해야 에이전트가 로드 |
| 구조 사실(파일 경로·모델)을 규칙에 섞음 | 그건 `learn` 산출물(구조) 쪽 |

## 다음 단계

- :material-magnify-scan: How-to: [외부 도메인 부트스트랩](cross-domain-learn.md) — `learn` 으로 구조를 먼저 만든다.
- :material-lightbulb-on: Explanation: [Workspace 레이아웃](../explanation/workspace-layout.md) — `context/` 가 어떻게 구성되는지.
- :material-book-open-variant: Reference: [`/pilot:learn`](../reference/skills/learn.md) · [도메인 분류 — MANIFEST.md](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/INDEX.md)
