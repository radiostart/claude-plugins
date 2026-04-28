# Context — 보조 자료 컨테이너

> 이 폴더 (`skills/context/`) 는 **다른 스킬·에이전트가 참조하는 자료 모음**이다. 슬래시 커맨드로 직접 호출하는 스킬이 아니다.
>
> - 자료 분류: [`shared/`](shared/) · [`domain/`](domain/) · [`modes/`](modes/) · [`lifecycle/`](lifecycle/)
> - 자동 진입 경로: `/pilot:project` · `/pilot:issue` 가 [`shared/preamble.md`](shared/preamble.md) 의 P3 단계에서 본 문서의 "도메인별 컨텍스트 로딩" 규칙을 참조한다.

## Work Mode

작업 모드는 아래 우선순위로 결정됩니다:

1. **명령어** — `/pilot:project {이름}`, `/pilot:issue` 등 명시적 모드 선언 (최우선)
2. **현재 모드** — `STATE.md`에 등록된 작업 컨텍스트
3. **기본값** — 1, 2 모두 해당 없으면 **이슈(issue) 모드**로 동작

## 컨텍스트

도메인 지식 + 런타임 설정은 **소비 프로젝트의 `workspace/context/`** 에 분리되어 있다.

| 파일 | 역할 | 파서 사용 | 구조 |
| --- | --- | --- | --- |
| `workspace/context/MANIFEST.md` | 도메인 지식 (도메인 분류·판단 기준·공통 모델/서비스·교차 참조 등) | ❌ 에이전트가 자연어로 읽음 | **자유롭게 정의** |
| `workspace/context/config.md` | 런타임 설정 (Ignore · 언어·도구 기본값 · commit_scopes) | ✅ scope-guard·commit-format·orchestrate-load | **고정 스키마** |

**플러그인 경로 컨트랙트** (이 부분은 강제):

| 경로 | 역할 |
| --- | --- |
| `workspace/context/scope/{domain}.md` | 도메인 결정 시 자동 로드 |
| `workspace/context/rules/{domain}.md` | 도메인 결정 시 자동 로드 |

폴더 이름 (`scope/`, `rules/`) 과 파일명 (`{domain}.md`) 은 변경 불가. 그 외 카테고리 (예: `enums/`) 와 폴더 안 구조·파일 내부 섹션은 자유.

에이전트·스킬은 **탐색·코드 수정 전에 MANIFEST.md 를 먼저 로드**하고, 도메인이 결정되면 위 컨트랙트 경로의 파일을 읽는다. 플러그인은 언어 컨벤션(`coding.md`), TDD 도구(`rgr.md`), 커밋·메시지 규약(`commit.md`, `messages.md`) 같은 메커니즘 자원만 보유한다.

도메인 지식은 사용자가 직접 채운다.

## STATE.md

`workspace/STATE.md` (gitignore 대상, 로컬 전용)

### 형식

```markdown
| 모드    | 이름/이슈명 | 상태   |
| ------- | ----------- | ------ |
| project | TICKET-435  | 진행중 |
```

### 규칙

- `진행중` 상태인 행은 **항상 1개만** 존재한다
- `/pilot:project`, `/pilot:issue` 실행 시 기존 `진행중` 행을 모두 `보류`로 변경 후 새 행을 추가한다
- `진행중` 행이 없거나 2개 이상이면 비정상 상태 — 에이전트는 사용자에게 `/pilot:project` 또는 `/pilot:issue`로 활성화하도록 안내하고 종료한다

## 프로젝트 폴더 구조

```text
projects/{PROJECT}/
├── project.md          # 오케스트레이터 — 개요, 목표, 에이전트 호출 흐름 (필수)
├── agents/
│   ├── planner.md      # 기능 분석 및 구현 계획 수립
│   ├── generator.md    # 코드 구현 참조 (패턴, 서비스, 모델)
│   └── evaluator.md    # 구현 검토 체크리스트
├── docs/               # 원본 기획서 (/pilot:confl fetch, 직접 Read 금지)
├── features/           # 분석된 기능 명세 (/pilot:analyze, 직접 Read 가능)
└── *.md                # 추가 문서 (screens.md, schema.md 등)
```

> **예약 폴더** — `projects/example/` 은 작성 예시 전용이다. STATE.md 에 등록하거나 실제 작업에 사용할 수 없다.

### docs/ 폴더 (원본 기획서)

```text
projects/{PROJECT}/docs/
└── {page_id}_{title}.md   # /pilot:confl {url} 로 저장된 Confluence 기획서
```

**접근 규칙:**

`docs/` 에는 기획서 원본(대용량 파일)이 저장된다. 직접 Read 하면 컨텍스트가 급격히 소모되므로 **기본적으로 직접 접근을 금지**하고 `/pilot:confl` 스킬을 통해 필요한 부분만 로드한다.

| 상황 | 접근 방식 |
| --- | --- |
| **기본 (사용자 질의, 에이전트, 기타 스킬)** | `/pilot:confl {검색어}` 로 필요한 섹션만 로드 |
| **저장이 필요할 때** | `/pilot:confl {url}` 로 저장 |
| **검색 + 후속 작업** | `/pilot:confl {검색어} > {작업지시}` 한 줄로 처리 |
| **전체 내용이 필요한 예외** | `/pilot:confl all` (사용자가 명시적으로 전체 요청) |

**구조적 예외 — 아래 2개 스킬만 docs/ 원본을 직접 다룰 수 있다:**

| 스킬 | 접근 방식 | 사유 |
| --- | --- | --- |
| `/pilot:analyze` | Read 로 원본 파일 로드 | 기능 분할을 위해 전체 원본이 필요 |
| `/pilot:project --url` | `confluence.py fetch` Bash 직접 호출 | 새 기획서 저장이 목적 |

에이전트(@planner/@generator/@evaluator)는 `features/` 를 우선 참조하고, 원본 확인이 필요한 경우에만 `/pilot:confl` 를 거친다.

### features/ 폴더 (분석된 기능 명세)

```text
projects/{PROJECT}/features/
└── {NN}-{slug}.md        # 기능 명세 (/pilot:analyze)
```

- `/pilot:analyze` 커맨드로 docs/ 원본을 분석하여 생성한다.
- `features/` 파일은 **직접 Read 가능**하다. 에이전트(@planner, @generator)가 요구사항 참조 시 사용한다.
- `features/` 가 있으면 docs/ 대신 features/ 를 우선 참조한다.
- TDD 모드에서는 @planner 가 Red 단계에서 `feature.md` 를 직접 읽어 실패 테스트를 작성한다.

## 에이전트

플러그인 루트 `agents/` 에 래퍼 에이전트가 등록되어 있다 (plugin.json 기반 자동 로드). 각 에이전트는 `STATE.md`에서 현재 프로젝트를 읽고 `projects/{PROJECT}/agents/{role}.md`를 로드해 프로젝트별 지침을 따른다.

| 에이전트     | 진입 조건                          | 기본 역할                        | TDD 모드                                        |
| ------------ | ---------------------------------- | -------------------------------- | ----------------------------------------------- |
| `@planner`   | 새 기능 시작 / 구현 방향 불명확 시 | 요구사항 분석 → 단계별 구현 계획 | + 스텝 분할 + 실패 테스트 작성 (Red)            |
| `@generator` | 코드 작성 시                       | 패턴·서비스·모델 참조, 구현 수행 | + 실패 테스트 통과 최소 구현 + Refactor (Green) |
| `@evaluator` | 구현 완료 후                       | 요구사항 충족 여부·일관성 검토   | + 변경 관련 테스트만 `{test_command} {paths}`     |

TDD 모드 활성화: `/pilot:tdd` — `project.md` 제한사항에 TDD 모드 문구 추가 + 각 에이전트 파일 책임 확장

프로젝트별 에이전트 파일(`projects/{PROJECT}/agents/`)이 없으면 `project.md`만으로 작업한다.

## 이슈 폴더 구조

```text
issues/{이슈명}/
└── issue.md     # 현상, 원인, 조치 내용 (필수)
```

## Fallback 규칙

| 상황                                                       | 동작                                                                                  |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `STATE.md` 가 없는 경우                                    | 빈 테이블(`\| 모드 \| 이름/이슈명 \| 상태 \|`)로 생성 후 계속 진행                    |
| `STATE.md` 형식이 깨진 경우                                | `/pilot:project` 또는 `/pilot:issue`로 초기화하도록 안내하고 종료             |
| `project.md` 가 없는 경우                                  | 사용자에게 파일 생성 여부를 확인 후 진행                                              |
| `agents/` 폴더 또는 파일이 없는 경우                       | `project.md`만으로 작업한다                                                           |
| `issue.md` 가 없는 경우                                    | 사용자에게 파일 생성 여부를 확인 후 진행                                              |
| `rules/{domain}.md` 가 `_(추가 예정)_` 또는 미존재인 경우 | scope만으로 작업하되, 도메인 규칙이 필요한 코드 수정은 사용자에게 규칙을 확인 후 진행 |
| `workspace/context/MANIFEST.md` 가 미존재인 경우 | 사용자에게 컨텍스트를 먼저 설정하라고 안내하고 종료 |
| `workspace/context/config.md` 가 미존재인 경우 | 파서 (`scope-guard`·`commit-format`·`orchestrate-load`) 가 해당 검증만 skip 하고 통과. toolchain 키 fallback 으로 Ruby 만 동작. 다른 언어는 `/pilot:doctor` 가 WARN |

## 코드 생성 정책

모델·서비스·컨트롤러를 **작성하거나 수정하는 모든 경우**, 요청 처리 전 [coding.md](shared/coding.md) 를 로드한다.
