# 워크스페이스 설정 (config.md)

!!! info "한 줄 요약"
    `workspace/context/config.md` 는 플러그인 훅·에이전트가 직접 파싱하는 *런타임 설정* 파일이다. 표 헤더·키 이름은 고정 스키마 — 사용자는 *값만* 채운다.

## config.md 란

`/pilot:init` 이 스켈레톤을 만든다. 같은 `context/` 폴더 안에서 도메인 *지식* 은 `MANIFEST.md`, 런타임 *설정* 은 `config.md` 로 분리돼 있다.

!!! warning "고정 스키마 — 값만 채운다"
    표 헤더와 키 이름은 플러그인이 *정확히 이 형태로* 파싱한다. 헤더·키를 바꾸거나 임의 키를 추가하면 읽히지 않는다. 섹션 구조는 그대로 두고 **값만** 채운다.

## 전제

- `/pilot:init` 으로 `workspace/context/config.md` 스켈레톤이 생성돼 있다.

## 절차

### 1. `## 언어·도구 기본값` — 가장 중요

에이전트 래퍼가 `{test_command}`·`{source_root}` 같은 플레이스홀더를 여기서 해석한다. Ruby 는 fallback 이 있지만 **다른 언어는 이 표가 비어 있으면 에이전트가 동작하지 않는다.**

| 키 | 예시 | 용도 |
|---|---|---|
| `language` | `ruby` · `kotlin` · `typescript` | 프로젝트 주 언어 (hint) |
| `test_command` | `bundle exec rspec` · `./gradlew test --tests` | 테스트 러너 — evaluator 가 변경 테스트 실행 |
| `source_root` | `app/` · `src/main/` | 소스 루트 — characterize 잠금·scope-guard 기준 |
| `test_path_convention` | `spec/**/*_spec.rb` | 테스트 파일 경로 규약 |
| `conventions_doc` | `context/conventions.md` | 언어·프레임워크 관행 문서 — generator 가 자동 로드 |
| `conventions_evals` | `context/evals/conventions.json` | 언어별 검증 케이스 JSON — generator 가 자동 로드 |
| `pr_default_base` | `develop` · `main` | `/pilot:pr` 기본 base 브랜치 |

선택 키: `test_command_fail_fast` (Red 단계 빠른 실패) · `coverage_command` · `lint_command` · `test_framework_hints`.

### 2. `## Ignore` — 탐색 제외 + 수정 차단

탐색·분석에서 빼고, `scope-guard.sh` 훅이 *수정까지 차단* 하는 경로. Glob 패턴으로:

```markdown
| 패턴 | 사유 |
| ---- | ---- |
| `vendor/**` | 서드파티 코드 |
| `*.generated.ts` | 빌드 산출물 |
```

### 3. `## 설정` — 훅 상수

플러그인 훅이 런타임에 읽는 상수. 현재 키:

```markdown
| 키 | 값 | 용도 |
| --- | --- | --- |
| commit_scopes | `feat,fix,refactor,skills,chore,docs,test,wip` | 커밋 메시지 scope 허용 목록 |
```

### 4. `## learn 언어 패턴` · `## scope 카테고리` — 보통 자동

`/pilot:init` wizard 가 언어를 감지해 자동으로 채운다. 감지가 틀렸거나 패턴을 보강할 때만 직접 손본다.

## 작성 규칙

- **안 쓰는 키는 행을 지우거나 값을 비운다** → 플러그인이 해당 기능만 skip 한다 (에러 아님).
- 값은 백틱으로 감싸도, 평문이어도 된다 — 파서가 둘 다 처리.
- `conventions_doc`·`conventions_evals` 는 *선언만으로 끝이 아니다* — 지정한 경로에 실제 파일을 만들어야 한다.
- 헤더·키를 추가하려면 플러그인 수정이 필요하다. 임의 키는 무시된다.

!!! tip "검증"
    각 스킬 완료 후 `/pilot:doctor` 가 config.md 정합성을 점검한다. credential drift·키 누락이 있으면 WARN 으로 알린다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:doctor`](../reference/skills/doctor.md) — config.md 정합성 점검.
- :material-gavel: How-to: [도메인 규칙 작성](authoring-domain-rules.md) — `config.md` 가 *설정*, `MANIFEST.md`+도메인 문서가 *지식*.
- :material-lightbulb-on: Explanation: [Workspace 레이아웃](../explanation/workspace-layout.md) — `context/` 가 어떻게 구성되는지.
