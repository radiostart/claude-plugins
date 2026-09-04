# 워크스페이스 설정

!!! info "한 줄 요약"
    `workspace/context/config.md` 는 플러그인 훅(hook)과 에이전트가 직접 파싱하여 활용하는 *런타임 설정* 파일입니다. 표의 헤더와 키(key) 이름은 고정된 schema이므로, 사용자는 매핑 데이터의 *값만* 채워서 사용합니다.

## config.md 란

`/pilot:pilot-init` 명령이 기본 스켈레톤(skeleton) 구조를 생성합니다. 동일한 `context/` 디렉터리 내에서 도메인 *지식* 정보는 `MANIFEST.md` 가 담당하고, 런타임 *설정* 정보는 `config.md` 파일이 담당하여 역할을 분리해 관리합니다.

!!! warning "고정 schema에 따른 값만 기입"
    표의 헤더 정보 및 키 이름은 플러그인이 정확히 정의된 형태로만 파싱합니다. 임의로 헤더와 키 이름을 수정하거나 신규 키를 단독 추가하면 설정값이 무시됩니다. 파일의 섹션 구조는 원본 그대로 보존한 상태에서 **설정값만** 수정하십시오.

## 전제 조건

- `/pilot:pilot-init` 을 실행하여 `workspace/context/config.md` 스켈레톤 파일이 생성되어 있어야 합니다.

## 작업 절차

### 1. `## 언어·도구 기본값` 섹션 설정 — 최우선 항목

에이전트 wrapper가 `{test_command}`, `{source_root}` 와 같은 placeholder 설정을 이곳에서 읽어 해석합니다. Ruby 언어는 fallback 정책이 작동하지만, **이외의 타 개발 언어로 프로젝트 진행 시 본 설정이 비어있으면 에이전트가 정상 작동하지 않습니다.**

| 설정 키 | 예시 설정값 | 용도 및 설명 |
|---|---|---|
| `language` | `ruby`, `kotlin`, `typescript` | 프로젝트의 주요 개발 언어 (hint 정보로 활용) |
| `test_command` | `bundle exec rspec`, `./gradlew test --tests` | 테스트 러너 실행 명령 (evaluator 가 변경분 검증 테스트 시 활용) |
| `source_root` | `app/`, `src/main/` | 제품 소스 디렉터리 루트 (characterize 수정 금지 범위 및 scope-guard 필터링 기준) |
| `test_path_convention` | `spec/**/*_spec.rb` | 프로젝트 내 테스트 파일 경로 생성 규칙 |
| `conventions_doc` | `context/conventions.md` | 언어/프레임워크 코딩 컨벤션 문서 경로 (generator·evaluator 가 자동 로드) |
| `conventions_evals` | `context/evals/conventions.json` | 언어별 검증 케이스 정의 JSON 파일 경로 (generator·evaluator 가 자동 로드) |
| `pr_default_base` | `develop`, `main` | `/pilot:pr` 실행 시 대상 base branch default 설정 |

그 외 선택 가능한 키: `test_command_fail_fast` (Red 단계 시 빠른 실패 지원), `coverage_command`, `lint_command`, `test_framework_hints`, `regression_command` 등.

`regression_command` 는 레거시 광역 회귀 스위트(전체 또는 광범위 테스트) 실행 명령입니다. `/pilot:pr` 진입 전 1회만 실행되는 soft gate 로 사용되며, **evaluator 는 이 키를 사용하지 않습니다** — 사이클 단위 전체 스위트 실행은 비용 원칙상 금지입니다 (`rgr.md` 의 비용 근거 참고).

### 2. `## Ignore` 섹션 설정 — 탐색 배제 및 수정 통제

코드 탐색 및 분석 대상에서 제외하고, `scope-guard.sh` 훅이 *해당 디렉터리의 수정 작업까지 차단*하도록 Glob 패턴 형식으로 작성합니다:

```markdown
| 패턴 | 사유 |
| ---- | ---- |
| `vendor/**` | 서드파티 라이브러리 코드 |
| `*.generated.ts` | 자동 빌드 생성 파일 |
```

### 3. `## 설정` 섹션 설정 — 훅 환경 변수

플러그인 훅이 런타임 도중에 해석할 상수 목록입니다. 현재 지원되는 키는 다음과 같습니다:

```markdown
| 키 | 값 | 용도 및 설명 |
| --- | --- | --- |
| commit_scopes | `feat,fix,refactor,skills,chore,docs,test,wip` | 커밋 메시지에 허용할 scope 목록 설정 |
```

### 4. `## learn 언어 패턴` 및 `## scope 카테고리` 설정

보통 `/pilot:pilot-init` 실행 도중 wizard 가 개발 언어를 감지하여 자동으로 해당 행을 채워 넣습니다. wizard 는 도중에 묻지 않고 감지·주입 후 결과만 보고하므로, 감지 결과가 정확하지 않거나 매칭 패턴을 커스텀 보강하려는 경우 수동으로 값을 편집합니다.

## 작성 규칙

- **비활성화할 키는 행 자체를 삭제하거나 값을 공란으로 둡니다** -> 플러그인은 해당 항목을 에러 없이 skip 처리합니다.
- 값은 백틱(`)으로 감싸도 되고 평문 형태로 적어도 파서가 자동 정규화합니다.
- `conventions_doc` 및 `conventions_evals` 의 경우 **경로 선언과 함께 실제로 해당 위치에 파일을 반드시 생성해 두어야 합니다.**
- 임의로 추가한 사용자 키는 무시되므로, 신규 설정을 추가하려면 플러그인 레벨의 패치가 필요합니다.

!!! tip "설정 적합성 검증"
    워크스페이스 설정을 변경한 뒤 `/pilot:pilot-doctor` 명령을 통해 config.md 설정 파일의 정합성을 한 번에 점검할 수 있습니다. 키 누락이나 credential drift 우려 사항 발견 시 WARN 리포트를 안내받게 됩니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:pilot-doctor`](../reference/skills/pilot-doctor.md) — config.md 정합성 및 구성 진단 도구 안내.
- :material-gavel: How-to: [도메인 규칙 작성](authoring-domain-rules.md) — 런타임 설정을 담당하는 `config.md` 와 도메인 지식을 관리하는 `MANIFEST.md` 의 구조적 비교 가이드.
- :material-code-braces: How-to: [언어 컨벤션 설정](language-conventions.md) — `conventions_doc` 및 `conventions_evals` 의 구체적인 작성 및 배포 지침.
- :material-lightbulb-on: Explanation: [Workspace 레이아웃](../explanation/workspace-layout.md) — `context/` 디렉터리의 내부 레이아웃 설계 가이드.
