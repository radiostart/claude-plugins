# 도메인 규칙 작성

!!! info "한 줄 요약"
    `/pilot:learn` 은 코드의 *구조* 를 추출하지만, 비즈니스 *규칙* 은 사용자가 직접 정의하고 `MANIFEST.md`를 통해 에이전트에 연결해야 합니다. 규칙 문서의 위치와 구조는 자유롭게 정의할 수 있으며, `MANIFEST.md`가 이를 가리키기만 하면 에이전트가 로드합니다.

## 역할 분리 — learn의 역할과 사용자의 역할

| 구분 | `/pilot:learn` (자동) | 사용자 (수동) |
|---|---|---|
| 다루는 영역 | 코드의 *구조적 사실* (파일, 시그니처, 라우트, 상태값 등) | *비즈니스 규칙* (정책, 제약사항, 의도 등) |
| 근거 | 코드 상에 명시된 사실 (`file:line` 인용) | 사람의 의사결정 (코드에 직접 드러나지 않음) |
| 산출물 | `context/{domain}.md` (또는 `{domain}/` 폴더) | 규칙 문서 및 `MANIFEST.md` 연결 |

`learn` 의 원칙은 *추측 배제* 입니다. 검증 패턴이나 상태 enum 같은 *구조* 는 식별할 수 있지만, "환불은 결제 후 7일 이내에만 허용" 과 같은 *정책적 의도* 는 코드만으로 파악하기 어렵기 때문에 사용자가 직접 정의해야 합니다.

## 핵심은 MANIFEST.md

플러그인이 강제하는 유일한 계약은 `workspace/context/MANIFEST.md` 입니다. 에이전트는 `MANIFEST.md` 의 `## 도메인 분류` 표에 선언된 domain 및 진입(entry) 파일을 파악하여 자동으로 필요한 규칙을 로드합니다.

!!! tip "구조의 자유도"
    비즈니스 규칙을 어떤 파일명이나 폴더 구조로 관리하든 무방합니다. `MANIFEST.md` 가 해당 진입점을 정확히 가리키고 있기만 하면 에이전트가 정상적으로 읽어 들입니다. 핵심은 `MANIFEST.md` 를 올바르게 갱신하는 것입니다.

## 전제 조건

- `/pilot:learn` 을 통해 도메인의 구조적 정보가 이미 추출되어 있어야 합니다.

## 작업 절차

### 1. 규칙 문서 구조 결정

도메인의 성격과 규모에 맞춰 적절한 구조를 선택합니다:

- **소규모 도메인**: `context/{domain}.md` 파일 내에 `## 규칙` 섹션을 직접 추가합니다.
- **규칙이 많은 도메인**: 별도 파일로 분리하여 관리합니다 (예: `scope` 구조 문서와 `rules` 규칙 문서를 구분).
- **하위 도메인(subdomain) 구조**: `context/{domain}/policies.md` 처럼 도메인 폴더 내에 배치합니다.

### 2. 규칙 명세 작성

코드 스니펫을 작성하는 것이 아니라 **비즈니스 정책**을 선언적으로 기술합니다. 구체적인 문자열 포맷이나 상태값의 정의는 한 곳에만 모아서 작성합니다.

!!! example "예시 — `context/rules/orders.md` (예시 구조 중 하나)"
    ```markdown
    # orders 도메인 규칙

    ## 환불 정책
    - 환불은 결제 완료 후 7일 이내에만 가능합니다. 7일이 지난 경우에는 고객센터를 통해 수동으로 처리해야 합니다.

    ## 주문 메모 포맷
    - 형식: `[{액션}({필드})]` — 예: `[refund(amount)]`

    ## 상태 전환 규칙
    - `pending → paid → shipped → delivered` 순서로 전환됩니다. `cancelled` 상태는 `shipped` 이전에만 전이할 수 있습니다.
    ```

    상기 내용은 하나의 예시일 뿐이며, 동일한 내용을 `{domain}.md` 내의 섹션으로 두거나 다른 분류로 나누어도 무방합니다. 중요한 것은 `MANIFEST.md` 가 이를 식별할 수 있는지 여부입니다.

### 3. MANIFEST.md 연동

`workspace/context/MANIFEST.md` 의 `## 도메인 분류` 섹션에 작성한 규칙 문서 경로를 등록합니다. 이를 통해 `orchestrate-load.py` 가 활성화된 project의 도메인을 판별하고 에이전트가 문서를 읽도록 자동으로 로드합니다. **MANIFEST.md에 등록되지 않은 파일은 프로젝트 내에 존재해도 에이전트에 로드되지 않습니다.**

### 4. agent 프롬프트에서의 참조

`prompts/*.md` 파일에 규칙을 직접 복사해 넣지 마십시오. 대신 "주문 메모 작성 시에는 규칙 문서의 '주문 메모 포맷' 정책을 따릅니다" 와 같이 참조 경로만 지정합니다. 동일한 규칙을 여러 프롬프트에 중복해서 하드코딩하면 drift가 발생하기 쉽습니다.

## 흔한 실수

| 잘못된 방식 | 올바른 방식 |
|---|---|
| 규칙 문서 내에 코드 블록을 다량 포함시킴 | 정책과 규칙은 텍스트 및 표로 설명하고, 상세 구현은 코드로 위임합니다. |
| 규칙을 agent 프롬프트 파일에 직접 하드코딩함 | 공통 규칙 문서에 정리한 뒤 프롬프트에서는 참조만 합니다. |
| 규칙 문서를 새로 생성한 뒤 MANIFEST.md에 누락함 | 반드시 `MANIFEST.md` 에 등록해야 에이전트가 인식합니다. |
| 파일 경로 등 구조적 사실을 규칙 문서에 혼재시킴 | 구조에 관한 팩트는 `learn` 이 추출한 영역에 두고, 규칙에는 정책만 담습니다. |

## 다음 단계

- :material-magnify-scan: How-to: [외부 도메인 연동](cross-domain-learn.md) — `learn` 을 통해 구조적 기반을 먼저 마련합니다.
- :material-lightbulb-on: Explanation: [Workspace 레이아웃](../explanation/workspace-layout.md) — `context/` 디렉터리가 어떻게 구성되고 관리되는지 파악합니다.
- :material-book-open-variant: Reference: [`/pilot:learn`](../reference/skills/learn.md) · [도메인 분류 — MANIFEST.md](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/INDEX.md)
