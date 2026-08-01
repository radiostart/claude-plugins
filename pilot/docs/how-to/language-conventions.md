# 언어 컨벤션 설정

!!! info "한 줄 요약"
    플러그인은 기본적으로 *언어 중립적*인 코드 정책만 내장하고 있습니다. 프로젝트의 언어 및 프레임워크 고유 컨벤션과 검증 케이스는 워크스페이스가 `conventions_doc` 및 `conventions_evals` 파일을 통해 공급하며, `config.md` 에서 해당 경로를 선언하여 활성화합니다.

## 컨벤션 공급의 필요성

플러그인이 기본 제공하는 것은 **언어에 무관한 공통 원칙**뿐입니다:

- `coding.md`: 코드 생성 메타 정책 (수정 최소화, 시그니처 보존, 우선순위 사다리 등)
- `evals/coding.json`: 공통 검증 케이스 (현재 `existing-code-modification` 1건)

Ruby/Rails의 관례적 매크로, Kotlin의 코루틴 설계 규약, 레이어 패턴의 역할 책무와 같이 *특정 언어나 프레임워크에 특화된 고유 관행*은 플러그인이 미리 가정하지 않고 워크스페이스 정의에 위임합니다. 정의가 누락될 경우 generator 는 기존 코드의 패턴을 단순히 답습하여 추론을 실행하게 됩니다.

## 전제 조건

- `/pilot:pilot-init` 을 실행하여 `workspace/context/config.md` 파일이 존재해야 합니다 ([워크스페이스 설정](workspace-config.md) 참고).

## 작업 절차

### 1. 관행 문서 작성 (`conventions_doc`)

언어 및 프레임워크의 코딩 컨벤션을 텍스트 형식으로 작성합니다 (예: `workspace/context/conventions.md`):

- **레이어 역할 책무**: 컨트롤러, 서비스, 모델 레이어의 명확한 역할 정의
- **명명 규칙/매크로/관용구**
- **테스트 프레임워크 문법 및 Mock 패턴**
- **금지해야 할 안티패턴**

### 2. 검증 케이스 정의 (`conventions_evals`)

코드가 완성된 후 generator 가 자가 진단 체크리스트로 활용할 검증 케이스를 JSON 형식으로 기술합니다 (generator 의 자가 진단과 별개로 evaluator 도 같은 케이스로 독립 검증합니다):

```json
{
  "cases": [
    {
      "id": "service-layer-guard",
      "description": "서비스 레이어 수정 시",
      "criteria": [
        "컨트롤러 로직을 서비스로 끌어내렸는가",
        "트랜잭션 경계가 서비스 메서드 단위인가"
      ]
    }
  ]
}
```

이 케이스들은 플러그인의 공통 케이스 뒤에 **append** 되며, 동일한 `id` 를 선언할 경우 프로젝트의 정의로 **override** 됩니다.

### 3. config.md 에 파일 경로 연동

`workspace/context/config.md` 의 `## 언어·도구 기본값` 표에 두 설정 경로를 명시합니다:

| 키 | 값 |
|---|---|
| `conventions_doc` | `context/conventions.md` |
| `conventions_evals` | `context/evals/conventions.json` |

경로가 정상적으로 선언되면 `@pilot-generator` 와 `@pilot-evaluator` 가 컨텍스트를 로드할 때 두 파일을 찾아 자동으로 분석합니다. **선언한 경로에 실제 파일이 존재하지 않으면 에러가 발생하므로**, 반드시 지정한 경로에 파일을 생성해 두어야 합니다.

## 우선순위

코드 구현 방향에 판단 충돌이 발생할 경우, generator 는 다음 우선순위에 따라 가중치를 둡니다:

1. 프로젝트 내 `prompts/generator.md` 에 기재된 명시적 규칙
2. `context/rules/{domain}.md` 에 작성된 비즈니스 규칙
3. `conventions_doc` 으로 주입된 언어/프레임워크 관행
4. 기존 제품 코드의 구현 패턴 (참조용으로만 활용하며 비표준 패턴은 답습하지 않음)

## 다음 단계

- :material-file-cog: How-to: [워크스페이스 설정](workspace-config.md) — `conventions_doc` 및 `conventions_evals` 키 설정 방법.
- :material-gavel: How-to: [도메인 규칙 작성](authoring-domain-rules.md) — 비즈니스 도메인 관점의 정책 수립 방법.
- :material-book-open-variant: Reference: [`/pilot:pilot-doctor`](../reference/skills/pilot-doctor.md)
