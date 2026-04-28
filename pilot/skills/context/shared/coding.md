# 코드 생성 정책 (언어 중립 메타)

이 문서는 **언어·프레임워크 불문 공통 원칙**만 담는다. Ruby/Rails·Kotlin·Java 등 언어별 구체 관행 (네이밍·매크로·테스트 문법·레이어 규칙) 은 **프로젝트가 제공하는 `conventions_doc`** 을 우선 따른다.

> `conventions_doc` 경로는 `workspace/context/config.md` 의 `## 언어·도구 기본값` 표에 선언. 래퍼 (`orchestrate-load.py`) 가 generator phase 에서 자동 로드한다.

## 우선순위 사다리

구현 판단 충돌 시 아래 순서로 해결한다.

1. **프로젝트 구현 지침** — `projects/{PROJECT}/agents/generator.md` 의 명시 규칙 (필수 콜백·특정 서비스 호출 패턴 등)
2. **팀 도메인 규칙** — `context/rules/{domain}.md` 의 비즈니스 규칙
3. **언어·프레임워크 관행** — `conventions_doc` 가 가리키는 문서 (레이어 책임·매크로·네이밍)
4. **기존 코드 패턴** — 참조만. 비표준 패턴은 답습하지 않는다

## 기존 코드 수정 원칙 (언어 공통)

- 기능 구현에 **필수적인 경우에만** 수정한다
- 수정 시 기존 동작을 보존한다 (시그니처·반환값)
- 수정 범위를 최소화한다 — 관련 없는 리팩토링 금지

## 독립 파일 배치 작업

독립 파일 N 개를 생성·수정할 때 (예: 일괄 파일 생성, 테스트 파일 다수 추가) **동일 assistant turn 에서 여러 tool_use 블록** 을 보내 harness 가 병렬 실행하게 한다. Write·Edit 모두 적용.

- 파일끼리 **의존 관계가 없을 때만** 병렬. 앞 파일의 내용을 뒤 파일이 참조하면 순차.
- 실무상 **3~5 개 단위** 묶음이 적정. 10+ 개 동시는 컨텍스트 혼잡 → 배치 분할.
- 각 파일 내용을 별도로 생각해야 하므로 "토큰 비용" 은 여전히 파일당 발생. 이 최적화는 **turn round-trip 절감** 목적.

## 검증

**코드 작성·수정이 완료되면 규모에 관계없이 항상 실행한다.**

체크리스트는 두 출처의 케이스를 합쳐 로드한다:

1. **플러그인 공통 evals** — [`evals/coding.json`](evals/coding.json) — 언어 불문 공통 케이스 (현재: `existing-code-modification`)
2. **프로젝트 언어별 evals** — `workspace/context/config.md` 의 `conventions_evals` 가 가리키는 파일 — 언어·프레임워크별 고유 케이스 (팀 컨벤션에 맞춘 레이어 가드 등)

**Merge 규칙:** 프로젝트 evals 가 공통 evals 에 `append`. 동일 `id` 는 프로젝트가 `override`. 작업 유형에 해당하는 케이스의 `criteria` 를 체크리스트로 확인. 미충족 항목은 수정 후 재확인한다.

`conventions_evals` 미선언이면 플러그인 공통 케이스만 적용 — 언어별 가드는 생략되므로 Generator 가 관행 문서 (`conventions_doc`) 를 스스로 숙지해야 한다.
