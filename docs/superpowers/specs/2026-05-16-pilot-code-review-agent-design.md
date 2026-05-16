# pilot code-review 에이전트 설계

- 날짜: 2026-05-16
- 대상 플러그인: `pilot`
- 목적: 프로젝트 진행 중 작성된 코드를 품질 관점에서 리뷰하는 독립 에이전트 추가. 기존 `pilot-evaluator` 와 별개.

## 배경

pilot 플러그인은 `pilot-planner → pilot-generator → pilot-evaluator` 3단계 래퍼 에이전트 체인으로 동작한다. `pilot-evaluator` 는 **요구사항 충족 여부와 게이트(test_run, scope, drift, tdd_evidence) 통과**를 판정한다.

이와 별개로, 진행 중 작성된 코드의 **품질 결함**(로직·설계·관용구·중복·보안 등)을 적발하는 역할이 없다. 본 설계는 그 역할을 담당하는 독립 호출형 에이전트 `pilot-code-review` 와 `/pilot:review` 스킬을 추가한다.

evaluator 와 축이 다르다:

- `pilot-evaluator` (auditor): 요구사항·게이트 **통과 판정**. 사이클의 일부.
- `pilot-code-review` (critic): 코드 품질 **결함 적발**. 사이클과 독립, 아무 때나 호출.

## 비목표 (YAGNI)

- orchestrate-load.py 의 4번째 phase 로 통합하지 않는다. 사이클·도메인 컨텍스트 로딩과 독립이다.
- 코드를 직접 수정하지 않는다 (report-only).
- planner/generator/evaluator 의 `prompts/*.md` 같은 프로젝트별 프롬프트 파일을 두지 않는다. 언어별 규칙 파일로 충분하다.
- GitHub PR 을 다루지 않는다. PR 게시·`gh` 연동은 본 에이전트의 범위가 아니다 (아래 경계 참조).

## 관련 도구와의 경계

공식 `claude-plugins-official/code-review` 플러그인(`/code-review`)·내장 `/security-review` 와 **목적·시점이 다르다**. `pilot-code-review` 는 이들을 대체하지 않으며, **PR 생성 이전 사이클 내부 리뷰** 전용이다.

| 축 | 공식 `/code-review` | `pilot-code-review` |
| --- | --- | --- |
| 시점 | PR 생성 후 | 사이클 진행 중, PR 이전 |
| 대상 | GitHub PR (`gh` 필요) | 로컬 git diff |
| 출력 | GitHub PR 코멘트 | 대화창 리포트 + 재진입 라우팅 |
| 범위 | 버그 + CLAUDE.md 준수 (좁게) | 언어별 워크스페이스 규칙 + baseline 품질 |
| 후속 | 사람이 읽고 수정 | feature/planner/generator 재진입 라우팅 |

공식 플러그인에서 가져올 점:

- **신뢰도 기반 false positive 억제** — 다중 에이전트·0-100 채점까지 도입하지 않는다 (오버엔지니어링). 대신 `review-principles.md` 의 항목별 **blocking 격상 기준**으로 critic 의 과잉 격상을 가볍게 억제한다.
- **역할 분담 안내** — `/pilot:review` SKILL.md 에 "PR 생성 후 게이트형 리뷰는 공식 `/code-review`, 심층 보안 패스는 `/security-review` 권장"을 한 줄 명시한다. `/pilot:pr` 의 다음 단계로 자연스럽게 이어진다.

## 구성 요소

### 신규 파일

| 경로 | 역할 |
| --- | --- |
| `pilot/agents/pilot-code-review.md` | 에이전트 래퍼. `agents/` 폴더 자동 로드. |
| `pilot/skills/review/SKILL.md` | `/pilot:review` 스킬. 인자 파싱 후 `@pilot-code-review` dispatch 하는 얇은 래퍼. |
| `pilot/skills/context/shared/review-principles.md` | 언어 무관 baseline 리뷰 루브릭. 플러그인 SSOT. |

### 수정 파일

| 경로 | 변경 |
| --- | --- |
| `pilot/skills/context/shared/identity.yml` | `personas.code-review` 추가. personas 주석에 code-review 는 orchestrate phase 아님을 명시. |
| `pilot/skills/init/SKILL.md` + setup 템플릿 | `/pilot:init` 가 `workspace/context/review/` 폴더와 `_TEMPLATE.md` 생성. |
| `pilot/.claude-plugin/plugin.json` | description 갱신, version bump (v0.3.0 범위 내). |

에이전트는 `agents/` 폴더에서 자동 로드되므로 plugin.json 에 별도 등록이 필요 없다.

## 동작 흐름

### `/pilot:review [target]` 스킬

1. `target` 인자 파싱:
   - 인자 없음 → git diff (uncommitted 변경 + 현재 브랜치 변경분)
   - 경로 인자 → 해당 경로로 한정
   - 커밋 범위 인자 (예: `HEAD~3..HEAD`) → 해당 범위 diff
2. 확정한 target 을 전달하며 `@pilot-code-review` dispatch.

### `@pilot-code-review` 에이전트

1. **대상 확정** — git diff 로 변경 파일·헌크 수집. diff 가 비어 있으면 사용자에게 알리고 종료.
2. **언어 감지** — 변경 파일 확장자 → 언어 집합 도출.
3. **규칙 로드**:
   - 항상 plugin `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-principles.md` 적용.
   - 감지된 언어별로 `workspace/context/review/{lang}.md` 가 있으면 Read 해 적용. 없으면 baseline 만.
4. **현재 feature 파악 (라우팅용)** — `workspace/STATE.md` → 현재 프로젝트 → 진행 중 feature 확인. 가볍게 시도하고, 실패해도 리뷰는 계속한다.
5. **리뷰** — diff 헌크를 규칙 대비 검토. 결함마다 severity·근거·개선안·재진입 라우팅 판정.
6. **CODE REVIEW REPORT 출력** — 코드는 수정하지 않는다. 사용자가 라우팅을 선택하면 해당 단계로 안내.

## 페르소나

`identity.yml` 의 `personas` 에 추가:

```yaml
code-review:
  archetype: critic
  voice: "변경분만 본다. 결함은 근거 없이 지나치지 않는다"
  phrasing: "severity(blocking|suggestion|nit) + file:line 인용 + 개선안 + 재진입 라우팅"
  forbid:
    - "취향·스타일 차이를 blocking 으로 격상"
    - "변경분 밖 코드 지적"
```

`personas` 섹션 주석은 현재 "키는 orchestrate-load 의 `--phase` 와 1:1 매칭"이라 적혀 있다. `code-review` 는 orchestrate phase 가 아니므로, 주석에 "단 `code-review` 는 독립 호출 에이전트로 phase 매칭 예외"를 한 줄 추가한다.

톤·언어(`tone`, `language: ko`, `verbosity`)는 identity.yml 전역 설정을 그대로 따른다.

## 재진입 라우팅

코드를 수정하지 않는 대신, 결함마다 어느 단계부터 다시 시작해야 하는지 판정해 사용자가 선택하게 한다.

| 라우팅 | 판정 기준 | 후속 동작 |
| --- | --- | --- |
| `feature` | feature 명세 자체의 누락·오류가 결함의 원인 (스펙 빈틈) | `features/NN-{slug}.md` 수정 후 사이클 재실행 |
| `planner` | 설계·구조 결함 — 책임 분리, 의존성 방향, 잘못된 추상화 | `@pilot-planner` 재호출 |
| `generator` | 구현 수준 결함 — 로직 버그, 패턴 미준수, 누락된 처리 | `@pilot-generator` 직접 재호출 |
| `local` | 국소·단순 수정 — 네이밍, nit | 즉시 수정 |

에이전트는 추천만 하고, 실제 후속 단계는 사용자가 선택한다.

## 출력 형식

메시지 끝에 아래 블록을 붙인다:

```
## CODE REVIEW REPORT
- target: {diff 범위 / 경로}
- languages: {감지된 언어 — 각 언어 규칙 파일 적용 여부}
- summary: blocking N · suggestion N · nit N
- findings:
  - [blocking] {요약} — {file:line}
    개선안: {...}
    재진입: generator | planner | feature | local
  - [suggestion] {요약} — {file:line}
    개선안: {...}
    재진입: ...
  - [nit] {요약} — {file:line}
- routing:
  - feature 단계부터: #{finding 번호}… | none
  - planner 부터: #{finding 번호}… | none
  - generator 부터: #{finding 번호}… | none
  - 로컬 수정: #{finding 번호}… | none
- 다음: 위 라우팅 중 선택해 주세요
```

- blocking 0건이면 `summary` 에 명시하고 findings 는 suggestion/nit 만 나열.
- 결함이 전혀 없으면 findings 를 `- none` 으로, routing 을 전부 `none` 으로 출력.

## 언어별 설정 파일

### 경로·형식

`workspace/context/review/{lang}.md` — 언어마다 한 파일. 사용자가 작성하는 자유 형식 리뷰 규칙(산문 + 체크리스트).

- 파일이 있는 언어 → 해당 규칙 + baseline 적용.
- 파일이 없는 언어 → `review-principles.md` baseline 만 적용.
- 선택적으로 파일 첫머리에 `lint:` 한 줄을 선언하면, 에이전트가 해당 언어의 변경 파일에 그 lint 명령을 실행해 결과를 findings 에 반영한다. 선언이 없으면 lint 를 실행하지 않는다.

config.md 의 기존 단일 `language`/`lint_command`/`conventions_doc` 키와는 별개다. 다언어 프로젝트를 위해 언어별 파일로 분리한다. 리뷰 규칙은 `review/{lang}.md` 가 단일 소스이며 config.md 와 중복 기재하지 않는다.

### `/pilot:init` 변경

`/pilot:init` 가 `workspace/context/review/` 폴더와 `_TEMPLATE.md` 를 생성한다. `_TEMPLATE.md` 는 작성 가이드(파일명 규칙, 선택적 `lint:` 줄, 체크리스트 예시)를 담는다. 사용자는 이를 복사해 `{lang}.md` 로 채운다.

## review-principles.md (baseline 루브릭)

언어 무관 항목을 한 화면 분량으로 정리한다. 각 항목에 **blocking 격상 기준**을 명시해 critic 이 취향 차이를 과잉 격상하지 않게 한다.

대상 항목 (예시):

- 명확성·네이밍
- 함수·책임 크기 (한 가지 일)
- 중복 / 불필요한 추상화
- 에러 처리 경계 (시스템 경계만 검증, 내부 과잉 방어 금지)
- 죽은 코드 / 미사용
- 보안 (주입, 비밀값 하드코딩)
- 테스트 가능성

## 영향 범위 / 호환성

- 기존 사이클(planner→generator→evaluator)·orchestrate-load·hooks 동작은 변경 없음.
- identity.yml 추가는 기존 3개 페르소나 키에 영향 없음 (신규 키 추가).
- `/pilot:init` 변경은 신규 워크스페이스에만 적용. 기존 워크스페이스는 `review/` 폴더가 없어도 에이전트가 baseline 으로 정상 동작.

## 미해결 사항

없음.
