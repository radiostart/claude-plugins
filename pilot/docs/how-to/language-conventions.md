# 언어 컨벤션 공급

!!! info "한 줄 요약"
    플러그인은 *언어 중립* 코드 정책만 내장한다. 프로젝트의 언어·프레임워크 고유 관행과 검증 케이스는 워크스페이스가 `conventions_doc`·`conventions_evals` 로 공급하고, `config.md` 가 그 경로를 선언한다.

## 왜 공급해야 하나

플러그인이 제공하는 것은 **언어 불문 공통 원칙** 뿐이다:

- `coding.md` — 코드 생성 메타 정책 (수정 최소화·시그니처 보존·우선순위 사다리).
- `evals/coding.json` — 공통 검증 케이스 (현재 `existing-code-modification` 1 건).

Ruby/Rails 매크로, Kotlin 코루틴 규약, 레이어 책임 같은 *언어·프레임워크 고유 관행* 은 플러그인이 가정하지 않는다 — 워크스페이스가 채운다. 안 채우면 generator 가 기존 코드 패턴만 보고 추론하게 된다.

## 전제

- `/pilot:init` 으로 `workspace/context/config.md` 가 있다 ([워크스페이스 설정](workspace-config.md)).

## 절차

### 1. 관행 문서 작성 — `conventions_doc`

언어·프레임워크 관행을 산문으로 정리한다 (예: `workspace/context/conventions.md`):

- 레이어 책임 — 컨트롤러/서비스/모델이 각각 무엇을 하나.
- 네이밍·매크로·관용구.
- 테스트 프레임워크 문법·Mock 패턴.
- 피해야 할 안티패턴.

### 2. 검증 케이스 작성 — `conventions_evals`

코드 작성 후 generator 가 체크리스트로 쓰는 케이스를 JSON 으로 정리한다:

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

이 케이스는 플러그인 공통 케이스에 **append** 되며, 같은 `id` 는 프로젝트 것이 **override** 한다.

### 3. config.md 에 경로 선언

`workspace/context/config.md` 의 `## 언어·도구 기본값` 표에 두 경로를 적는다:

| 키 | 값 |
|---|---|
| `conventions_doc` | `context/conventions.md` |
| `conventions_evals` | `context/evals/conventions.json` |

선언하면 `@pilot-generator` 가 컨텍스트 로드 시 두 파일을 자동으로 읽는다. **선언만 하고 실제 파일을 안 만들면 안 된다** — 지정한 경로에 파일이 있어야 한다.

## 우선순위

구현 판단이 충돌하면 generator 는 이 순서로 해결한다:

1. 프로젝트 `prompts/generator.md` 의 명시 규칙
2. `context/rules/{domain}.md` 의 비즈니스 규칙
3. `conventions_doc` 의 언어·프레임워크 관행
4. 기존 코드 패턴 (참조만 — 비표준 패턴은 답습하지 않음)

## 다음 단계

- :material-file-cog: How-to: [워크스페이스 설정 (config.md)](workspace-config.md) — `conventions_doc`·`conventions_evals` 키 선언.
- :material-gavel: How-to: [도메인 규칙 작성](authoring-domain-rules.md) — *비즈니스* 규칙 (관행과는 다른 축).
- :material-book-open-variant: Reference: [`/pilot:doctor`](../reference/skills/doctor.md)
