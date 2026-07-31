# Context — 보조 자료 컨테이너

> 이 폴더 (`skills/context/`) 는 **다른 스킬·에이전트가 참조하는 자료 모음**이다. 슬래시 커맨드로 직접 호출하는 스킬이 아니다.
>
> - 자료 분류: [`shared/`](shared/) · [`domain/`](domain/) · [`modes/`](modes/) · [`lifecycle/`](lifecycle/)
> - 자동 진입 경로: `/pilot:project` · `/pilot:issue` 가 [`shared/preamble.md`](shared/preamble.md) 의 P3 단계에서 본 문서의 "도메인별 컨텍스트 로딩" 규칙(아래 § 컨텍스트)을 참조한다.

## Work Mode

우선순위: **명령어** (`/pilot:project {이름}`·`/pilot:issue` 등 명시적 선언) > **현재 모드** (`STATE.md` 등록 컨텍스트) > **기본값** (둘 다 없으면 이슈 모드).

## 컨텍스트 (도메인별 컨텍스트 로딩)

도메인 지식 + 런타임 설정은 **소비 프로젝트의 `workspace/context/`** 에 분리되어 있다.

| 파일 | 역할 | 파서 사용 | 구조 |
| --- | --- | --- | --- |
| `workspace/context/MANIFEST.md` | 도메인 지식 (도메인 분류·판단 기준·공통 모델/서비스·교차 참조 등) | ❌ 에이전트가 자연어로 읽음 | **자유롭게 정의** |
| `workspace/context/config.md` | 런타임 설정 (Ignore · 언어·도구 기본값 · commit_scopes) | ✅ scope-guard·commit-format·orchestrate-load | **고정 스키마** |

**플러그인 경로 컨트랙트** (강제):

| 경로 | 역할 |
| --- | --- |
| `workspace/context/MANIFEST.md` | 도메인 지식 진입점. 플러그인이 항상 로드 + `## 도메인 분류` 표 자동 파싱하여 도메인 진입 파일 추가 로드 |
| `workspace/context/boundaries/{A}--{B}.md` | cross-domain 경계 계약 (`/pilot:learn --boundary` 산출). orchestrate-load 가 활성 도메인 기준 정방향(`{domain}--*`)·역방향(`*--{domain}`) 글롭으로 자동 로드 — **고정 컨벤션** |

그 외 `workspace/context/` 하위 폴더 구조·파일명은 **자유** (`scope/`·`rules/`·`enums/` 등). 플러그인이 직접 아는 경로는 위 표뿐이고, 나머지는 MANIFEST 가 가리키는 경로를 따라 로드한다. 도메인 지식은 사용자가 직접 채운다.

에이전트·스킬은 **탐색·코드 수정 전에 MANIFEST.md 를 먼저 로드**하고, 도메인이 결정되면 그 진입 파일·하위 파일을 읽는다. 플러그인은 언어 컨벤션(`coding.md`), TDD 도구(`rgr.md`), 커밋·메시지 규약(`commit.md`, `messages.md`) 같은 메커니즘 자원만 보유한다.

컨텍스트 문서의 생애주기 프로토콜 2 종: 기존 문서-코드 불일치(우연 발견)는 [`drift-protocol.md`](lifecycle/drift-protocol.md), 사이클 종료 시 신규 지식 환류(evaluator 감지 → 사용자 승인 후 메인 대화가 기록)는 [`knowledge-sync.md`](lifecycle/knowledge-sync.md) 를 따른다.

## STATE.md

`workspace/STATE.md` — 추적 여부는 사용자 정책 ([state-schema.md](lifecycle/state-schema.md) 와 동일). 로컬 전용 운영 권장.

```markdown
| 모드    | 이름/이슈명 | 상태   |
| ------- | ----------- | ------ |
| project | TICKET-435  | 진행중 |
```

갱신 규칙(1행만 유지·누적 금지)의 정본은 [`preamble.md`](shared/preamble.md) § P2 — 본 문서는 형식 예시만 보유한다.

## 프로젝트 · 이슈 폴더 구조

프로젝트 폴더 구조(`project.md`·`prompts/`·`docs/`·`features/`)·agent 파일 책임 경계·drift 감지 규칙은 [`projects/GUIDE.md`](lifecycle/projects/GUIDE.md) 가 정본이다.

이슈 폴더는 `issues/{이슈명}/issue.md` 1 개만 가진다 (사이클 없는 경량 모드 — [`issue/SKILL.md`](../issue/SKILL.md)).

### docs/ 접근 규칙

`docs/` 는 기획서 원본(대용량)이라 직접 Read 하면 컨텍스트가 급격히 소모된다. 기본은 `/pilot:confl` 로 필요한 부분만 로드하고, 아래 2 스킬만 원본을 직접 다루는 **구조적 예외**다:

| 스킬 | 접근 방식 | 사유 |
| --- | --- | --- |
| `/pilot:analyze` | Read 로 원본 파일 로드 | 기능 분할을 위해 전체 원본이 필요 |
| `/pilot:project --url` | `confluence.py fetch` Bash 직접 호출 | 새 기획서 저장이 목적 |

에이전트(`@pilot-planner`/`@pilot-generator`/`@pilot-evaluator`)는 `features/` 를 우선 참조하고, 원본 확인이 필요한 경우에만 `/pilot:confl` 를 거친다.

## 에이전트

플러그인 루트 `agents/` 에 wrapper 에이전트가 등록되어 있다 (`plugin.json` 기반 자동 로드). 공통 계약(경로 규칙·orchestrate-load 처리·domain null 예외·부분 로드)은 [`wrapper-protocol.md`](shared/wrapper-protocol.md) 가 정본. TDD 모드에서 각 에이전트가 추가로 수행하는 Red/Green/Refactor 역할은 [`rgr.md`](modes/rgr.md) 참조.

프로젝트별 에이전트 파일(`projects/{PROJECT}/prompts/`)이 없으면 `project.md` 만으로 작업한다.

## Fallback 규칙

| 상황                                                       | 동작                                                                                  |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `STATE.md` 가 없는 경우                                    | `messages.md` 의 `workspace_missing` 안내 출력 후 종료                    |
| `STATE.md` 형식이 깨진 경우                                | `/pilot:project` 또는 `/pilot:issue`로 초기화하도록 안내하고 종료             |
| `project.md` 가 없는 경우                                  | 사용자에게 파일 생성 여부를 확인 후 진행                                              |
| `prompts/` 폴더 또는 파일이 없는 경우                      | `project.md`만으로 작업한다                                                           |
| `issue.md` 가 없는 경우                                    | 사용자에게 파일 생성 여부를 확인 후 진행                                              |
| MANIFEST 에 도메인 진입 파일이 등록되지 않은 경우 | `/pilot:learn {진입점}` 으로 부트스트랩 안내 또는 사용자에게 MANIFEST 행 추가 요청 |
| `workspace/context/MANIFEST.md` 가 미존재인 경우 | 사용자에게 컨텍스트를 먼저 설정하라고 안내하고 종료 |
| `workspace/context/config.md` 가 미존재인 경우 | 파서 (`scope-guard`·`commit-format`·`orchestrate-load`) 가 해당 검증만 skip 하고 통과. toolchain 키 fallback 으로 Ruby 만 동작. 다른 언어는 `/pilot:doctor` 가 WARN |

## 코드 생성 정책

모델·서비스·컨트롤러를 **작성하거나 수정하는 모든 경우**, 요청 처리 전 [coding.md](shared/coding.md) 를 로드한다.
