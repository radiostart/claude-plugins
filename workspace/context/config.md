# Workspace Config

워크스페이스 **런타임 설정** — 플러그인 훅·스크립트가 직접 파싱하는 고정 스키마.
도메인 지식은 같은 폴더의 `MANIFEST.md` 에 있다.

> 이 파일은 `/pilot:init` 가 생성한 스켈레톤이다. 사용자가 직접 채워야 한다.
> 표 헤더·키 이름은 **고정 스키마** (플러그인이 정확히 이 형태로 파싱). 값만 채운다.

## Ignore

탐색·분석 시 **참조하지 않는** 파일/폴더. Glob 패턴으로 정의한다.
`hooks/scope-guard.sh` 가 이 섹션을 파싱하여 수정 차단에 사용한다.

| 패턴 | 사유 |
| ---- | ---- |
|      |      |

## 언어·도구 기본값

에이전트 래퍼 (`planner`·`generator`·`evaluator`) 가 `{test_command}`·`{source_root}` 등 플레이스홀더를 해석할 때 참조. Ruby 프로젝트는 fallback 이 있지만 **다른 언어는 이 표가 비어 있으면 동작하지 않는다**.

| 키 | 값 | 용도 |
| --- | --- | --- |
| `language` | `ruby` · `kotlin` · `typescript` 등 | 프로젝트 주 언어 (hint 용) |
| `test_command` | `bundle exec rspec` · `./gradlew test --tests` 등 | 테스트 러너. Evaluator 가 변경 관련 테스트 실행 시 사용 |
| `test_command_fail_fast` | 예: `bundle exec rspec --fail-fast` | Red 단계 빠른 실패용 (선택) |
| `coverage_command` | 예: `bundle exec rspec --format documentation` | 커버리지 리포트 (선택) |
| `lint_command` | 예: `bundle exec rubocop`, `./gradlew ktlintCheck` | 린트 실행 (선택) |
| `source_root` | `app/` · `src/main/` 등 | 소스 루트. characterize 모드의 잠금 대상 · scope-guard 기준 |
| `test_path_convention` | 예: `spec/**/*_spec.rb`, `src/test/kotlin/**/*Test.kt` | 테스트 파일 경로 규약 |
| `test_framework_hints` | 자유 텍스트 | 프레임워크 특이사항 (예: `RSpec 3.x, shared_examples 사용`) |
| `conventions_doc` | 예: `context/conventions.md` | 언어·프레임워크 관행 산문 문서 경로. generator phase 가 자동 로드 |
| `conventions_evals` | 예: `context/evals/conventions.json` | 언어·프레임워크별 검증 케이스 JSON 경로. generator phase 가 자동 로드 |
| `pr_default_base` | 예: `develop` · `main` | `/pilot:pr` 의 base branch default. `.agent-state.yml` 의 `pr_base_branch` 부재 시 사용. 미선언 시 하드 fallback `develop` |

## learn 언어 패턴

`/pilot:learn` 의 Phase 2 (Inventory) 가 진입 파일 확장자에서 언어를 추론한 뒤 본 섹션의 두 표를 lookup. 비어있으면 폴더 인접성 fallback. 사용자가 자기 프로젝트의 패턴을 정의.

### 의존성 추적

| 언어 | 의존성 추출 패턴 |
| ---- | ---------------- |

### 역할 분류

| 역할 | 식별 패턴 |
| --- | --------- |

## scope 카테고리

`/pilot:analyze` 5-2 단계가 `scope/{domain}.md` 의 매칭 H2 표를 추출해 `project.md` 의 `## 관련 파일` H3 표로 기입할 때 사용. config 행이 SKILL.md default 보다 우선. 빈 표 또는 매칭 행 부재 시 SKILL.md default 사용. `/pilot:create-feature` 도 5-2 인용 호출이라 자동 동일 적용.

| scope 헤더 | project.md 대상 H3 | 표 헤더 |
| --- | --- | --- |
| ## Routes | Endpoints | 엔드포인트, Method, 목적 |
| ## Models | Models | Class, DB, 목적 |
| ## Services | Services | Class, 파일, 목적 |

## 설정

플러그인 훅이 runtime 에 읽는 상수.

| 키              | 값                                                  | 용도                                           |
| --------------- | --------------------------------------------------- | ---------------------------------------------- |
| commit_scopes   | `feat,fix,refactor,skills,chore,docs,test,wip`      | `hooks/commit-format.sh` 가 허용하는 커밋 scope 목록 (쉼표 구분) |

**작성 규칙:**

- 사용하지 않는 키는 행을 지우거나 값을 비운다. 플러그인이 **해당 기능 부분만** 스킵.
- 값은 백틱으로 감싸도 되고 평문이어도 된다 (파서가 둘 다 처리).
- `conventions_doc` · `conventions_evals` 는 선언 후 실제 파일을 사용자가 지정한 경로에 생성해야 한다.
- 키를 추가하려면 플러그인 수정이 필요하다. 임의 키 추가는 읽히지 않음.
