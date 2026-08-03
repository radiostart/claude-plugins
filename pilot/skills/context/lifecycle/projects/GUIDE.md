# Projects — 작성 가이드

프로젝트 폴더는 **오케스트레이터(project.md) + 에이전트 컨텍스트(prompts/) + 기능 명세(features/)** 구조로 구성한다.

> 참조 파일이 100줄을 넘으면 상단에 목차를 추가한다. Claude가 부분적으로 읽을 때도 전체 구조를 파악할 수 있다.

> 완성된 예시: [example/project.md](example/project.md) + [prompts/](example/prompts/)

---

## 프로젝트 폴더 구조

```text
projects/{PROJECT}/
├── project.md          # 오케스트레이터 — 개요, 목표, 에이전트 호출 흐름 (필수)
├── prompts/
│   ├── planner.md      # 기능 분석 및 구현 계획 수립
│   ├── generator.md    # 코드 구현 참조 (패턴, 서비스, 모델)
│   └── evaluator.md    # 구현 검토 체크리스트
├── docs/               # 원본 기획서 (/pilot:confl fetch, 직접 Read 금지)
│   └── {page_id}_{slug}.md
├── features/           # 분석된 기능 명세 (/pilot:analyze, 직접 Read 가능)
│   ├── {NN}-{slug}.md       # 기능 명세
│   └── {NN}-{slug}.plan.md  # 구현 계획 (Planner가 자동 생성, Generator가 참조)
└── *.md                # 추가 문서 (screens.md, schema.md 등)
```

### docs/ → features/ 관계

- `docs/` — 원본 기획서 보관. `/pilot:confl`로 저장하며 직접 Read하지 않는다.
- `features/` — 분석된 기능 명세. `/pilot:analyze`로 생성하며 에이전트가 직접 Read한다.
- `/pilot:project` 에 URL을 함께 전달하면 저장과 분석이 자동으로 수행된다.

---

## 에이전트 동작 구조

플러그인 루트 `agents/` 에 등록된 래퍼 에이전트(`@pilot-planner`, `@pilot-generator`, `@pilot-evaluator`)가 실제 별도 인스턴스로 실행된다 (`.claude-plugin/plugin.json` 기반 자동 로드). 래퍼는 `STATE.md`에서 현재 프로젝트를 읽고, 프로젝트별 `prompts/*.md`를 로드해 지침을 따른다.

```
사용자: @pilot-planner 실행
  └── ${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md (래퍼)
        └── STATE.md에서 현재 프로젝트 확인
              └── workspace/projects/{PROJECT}/prompts/planner.md (프로젝트별 지침) 로드
```

`projects/{PROJECT}/prompts/` 파일은 **프로젝트 종속 내용만** 담는다. 공통 동작(STATE.md 읽기, 프로젝트 로드)은 래퍼가 처리한다.

### pre / post-analyze 게이트

래퍼는 프로젝트의 **`.agent-state.yml` 의 `analyzed` 필드** 를 "analyze 가 이미 실행됐는가?" 의 시그널로 사용한다.

| `analyzed` 값 | 래퍼 동작 |
| ------------- | --------- |
| `true` (post-analyze) | prompts/*.md 가 analyze 주입 압축본이라 신뢰. MANIFEST 진입 파일 재로드 생략 |
| `false` (pre-analyze) | MANIFEST 진입 파일 fallback 로드 |
| state.yml 부재 | 에러 + 마이그레이션 안내 후 종료 |

스키마 상세: [state-schema.md](../state-schema.md).

**이 게이트 때문에 지켜야 할 규칙:**

1. `analyzed` 필드를 수동으로 편집하지 않는다. `/pilot:analyze` 가 유일한 정식 writer.
2. 신규 프로젝트는 `/pilot:project` 가 `analyzed: false` 로 초기화.
3. `prompts/*.md` 안의 섹션명 (`## 기능별 사전 확인 사항`, `## 핵심 서비스/모델` 등) 은 analyze 가 주입·갱신할 때 anchor 로 사용하므로 임의 변경 금지.

### drift 감지

`.agent-state.yml` 의 optional 필드 `analyzed_at` · `last_analyzed_features` 를 기반으로 `/pilot:pilot-doctor` 가 drift 를 감지하고 경고한다.

| 신호 | 원인 | 대응 |
| ---- | ---- | ---- |
| `features_count > last_analyzed_features + 1` | features 가 여러 개 추가됨 → prompts/*.md 구식 가능성 | `/pilot:analyze --regen-agents` |
| `scope/*.md mtime > analyzed_at` | 팀 도메인 지식 업데이트됨 → prompts/*.md 구식 | `/pilot:analyze --regen-agents` |

**언제 재생성 돌려야 하나:**

- MANIFEST 의 도메인 진입 파일을 업데이트한 직후
- 프로젝트 features 가 처음 analyze 시점의 2 배 이상 증가
- `doctor` 가 drift WARN 을 출력할 때
- 장기간 작업 없던 프로젝트 재개 시 한 번

재생성해도 사용자가 손수 편집한 섹션 (예: `## 주의사항`) 은 보존. analyze 가 주입하는 섹션만 갱신.

---

## 설정 (config.md)

플러그인 훅이 runtime 에 읽는 상수는 `workspace/context/config.md § 설정` 표에 선언한다. 스키마·키·작성 규칙 SSOT 는 [`setup/templates/config.md.template`](../setup/templates/config.md.template) `## 설정` 섹션.

**키 추가 시 플러그인 측 절차:** template 표 업데이트 → 소비자 (훅/스킬) 파싱 로직 추가 → 두 지점 동기화. 임의 키는 읽히지 않음.

---

## agent 파일 책임 경계

프로젝트 agent 파일 (`prompts/planner.md`·`generator.md`·`evaluator.md`) 에 **담아야 할 것**과 **담지 말아야 할 것** 을 분리한다. 경계가 흐려지면 지식 중복·drift 의 주원인이 된다.

> **이하의 `scope/{domain}.md` · `rules/{domain}.md` 언급은 권장 컨벤션이며 강제가 아니다.** 두 축 분리가 자연스러운 도메인 (CRUD + 비즈니스 룰) 에서 유용. 워크스페이스 구조는 자유 — 다른 형태로 작성하고 MANIFEST 가 가리키도록 해도 됨. 플러그인은 MANIFEST 만 알고 폴더 구조를 강제하지 않는다.

### 담을 것 (프로젝트 고유)

- 이 프로젝트만의 서비스 메서드 시그니처·콜백 체인·쿼리 헬퍼 (generator)
- 이 프로젝트만의 비즈니스 규칙 특이점 (상태 전환 순서, 검증 예외 등) — **단, rules/{domain}.md 에 이미 있으면 거기로 참조만**
- 기능별 사전 확인 사항·체크리스트 (analyze 가 주입)

### 담지 말 것 (다른 곳이 SSOT)

| 내용 | 올바른 위치 |
|---|---|
| 도메인 비즈니스 규칙 (메모 문구 패턴·상태값 의미 등) | `workspace/context/rules/{domain}.md` |
| 도메인 파일 경로·모델 구조 | `workspace/context/scope/{domain}.md` |
| 상태 enum 정의 | `workspace/context/enums/...` |
| 언어 공통 컨벤션 (수정 최소화·시그니처 보존·검증 루프) | `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md` |
| TDD 절차 (Red·Green·Refactor) | `${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md` |
| 컨텍스트 로드·detection 로직 | 래퍼 + `orchestrate-load.py` |

### 원칙

- **하드코드 금지:** 도메인 규칙을 agent 파일에 직접 박으면 규칙 변경 시 양쪽을 고쳐야 함. rules/ · scope/ 에 두고 참조.
- **공통 내용 금지:** 모든 feature·모든 프로젝트 공통 체크는 plugin-level 문서로. agent 파일은 프로젝트 특유만.
- **SSOT 위반 감지:** `/pilot:analyze --regen-agents` 실행 시 agent 파일 내용이 rules/scope 와 충돌하면 rules/scope 쪽이 우선.

### agent 파일 간 사실 데이터 복사 금지

`generator.md` 와 `evaluator.md` 가 **동일한 사실 데이터** (예: 메모 문구 패턴·상태값 리스트·특정 제외 규칙) 를 양쪽에 하드코드하면 **한쪽 수정 시 나머지와 sync 가 깨진다**. 이는 두 에이전트의 **역할 분리 (generator=제출 전 sanity / evaluator=완성도 심사)** 와는 **별개 축의 문제** 로, 방어선 이중화가 아니라 **사실 데이터의 이중 기록**이다.

**올바른 위치:**

- 메모 문구·네이밍 패턴 → `rules/{domain}.md`
- 모델·서비스 경로·시그니처 → `scope/{domain}.md`
- 상태 enum → `enums/...`

**agent 파일은 "이 규칙 / 이 경로 확인" 형태로 참조만** 한다. 예: "주문 메모는 `rules/{도메인}.md` 의 '메모 포맷' 섹션 준수" 한 줄. 실제 포맷 문자열은 적지 않음.

**감지 방법:**

- `/pilot:analyze --regen-agents` 실행 시 양쪽 파일에 동일 코드 블록·문구가 중복되면 **WARN 후 rules/scope 로 이관 제안**.
- doctor 확장 (향후): 프로젝트 agent 파일 2 개 이상에서 동일 3-line 블록 감지 시 WARN.

---

## TDD 모드

| 상황 | 커맨드 |
| --- | --- |
| 신규·기존 프로젝트에 활성화 | `/pilot:project {PROJECT} --tdd` |
| 기존 코드에 사후 적용 | `/pilot:tdd` (활성 프로젝트 필요) |

활성화 시 3-phase 흐름은 유지되고 각 에이전트가 Red/Green/Refactor 역할을 추가로 수행한다. 사이클 절차·Red Contract·증거 기록 세부는 [`rgr.md`](../../modes/rgr.md) 가 SSOT.

활성화 시 `project.md § 에이전트 호출 흐름` 이 RGR 변형으로 교체되는 세부는 [`tdd-activation.md`](../../modes/tdd-activation.md) 참조.

---

## features/ 폴더 작성 규칙

`project.md` 의 `## 목표` 체크리스트는 **한 줄 요약 + 상세 문서 링크** 형식으로 작성한다. 상세 요구사항·화면·동작·예외 케이스는 `features/NN-{slug}.md` 파일에 기술한다.

**목표 작성 형식**

```markdown
## 목표

- [ ] 예시 기능 A -> [상세](features/01-<feature-slug-a>.md)
- [ ] 예시 기능 B -> [상세](features/02-<feature-slug-b>.md)
- [x] 예시 기능 C -> [상세](features/03-<feature-slug-c>.md)
```

**규칙**

- 파일명은 `NN-{slug}.md` (두 자리 순번 + kebab-case 영문 슬러그). 순번은 구현/우선순위 순서.
- 각 feature 파일은 다음 섹션을 포함한다: `## 요구사항` (조건/트리거/기대결과), `## 상태 전환`, `## 비즈니스 규칙`, `## 예외 케이스`, `## Open Questions` (4 카테고리).
- `project.md` 의 체크박스(`[ ]` / `[x]`) 는 feature 단위의 완료 상태를 나타낸다. Evaluator 가 feature 문서의 모든 요구사항 충족을 확인한 뒤 체크한다.
- planner 는 feature 문서를 먼저 읽고 RGR 스텝으로 분할한다. feature 문서가 없으면 planner 가 생성하거나 사용자에게 확인한다.
- `.plan.md` 파일은 Planner가 계획 확정 시 자동 생성한다. Generator가 구현 지침으로 Read하며, 수동 편집하지 않는다. `features/` 폴더가 없는 프로젝트에서는 생성하지 않는다.

---

## project.md — 오케스트레이터

전체 흐름을 조율하는 진입점. 구체적 구현 지식은 `prompts/` 에 위임한다. 실제 템플릿·섹션 예시는 [`example/project.md`](example/project.md) 가 SSOT.

**필수 섹션 (순서 고정):**

| # | 섹션 | 역할 |
| --- | --- | --- |
| 1 | `## 개요` | 프로젝트 목적·배경 1~2문장 |
| 2 | `## 제한사항` | 구현 제약 (DB 단일 조회·TDD 모드 등). `tdd: true` 와 `mode: characterize` 는 여기 literal 로 기술 |
| 3 | `## 목표` | 완료 조건 체크리스트. 항목마다 `features/NN-{slug}.md` 링크 |
| 4 | `## 에이전트 호출 흐름` | Planner → Generator → Evaluator 순서·로드 파일·완료 기준. TDD 모드면 RGR 변형 ([`tdd-activation.md`](../../modes/tdd-activation.md)) |
| 5 | `## 관련 파일` | Models / Endpoints / Services 표. scope/{domain}.md 컨벤션 사용 시 `/pilot:analyze` 가 거기로부터 자동 기입 (다른 구조면 사용자가 직접 작성) |

> base 브랜치는 `/pilot:pr` 가 `.agent-state.yml` (`pr_base_branch`) → `workspace/context/config.md` (`pr_default_base`) → fallback `develop` 순서로 결정한다. project.md 에는 기록하지 않는다.

섹션명·순서는 `/pilot:analyze` 가 anchor 로 사용한다. **임의 변경 금지.**

---

## prompts/planner.md

이 프로젝트에서 플래닝 시 따를 지침. 래퍼(`@pilot-planner`)가 로드해 실행한다.

### 포함 내용

- `## 기능별 사전 확인 사항` — **pre-analyze 상태에선 빈 상태**. `/pilot:analyze` 가 feature 별 소항목 + 각 소항목 하위의 `**관련 파일 범위**` subsection (Routes/Models/Services) 을 자동 주입 (`[analyze-managed]` 영역). 래퍼의 pre/post-analyze 분기는 `.agent-state.yml` 의 `analyzed` 필드로 판정 — 위 "pre / post-analyze 게이트" 참조.

> **플래닝 프로세스 공통 가이드** (요구사항 파악 → 영향 범위 분석 → 계획 출력 형식) 는 래퍼 (`${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md`) 가 제공한다. 프로젝트별 `prompts/planner.md` 는 프로젝트 고유 사전 확인 사항만 담는다 (공통 템플릿 반복 금지 — GUIDE "agent 파일 책임 경계" 원칙).

> **TDD 모드**일 때: `/pilot:tdd` 가 파일 말미에 Red 단계 앵커를 추가한다 (본 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 참조).

---

## prompts/generator.md

이 프로젝트에서 코드 구현 시 참조할 기술 레퍼런스. 래퍼(`@pilot-generator`)가 로드해 실행한다.

### 포함 내용

- `## 컨텍스트 로드` — 이 프로젝트가 의존하는 `MANIFEST` + `rules/{domain}.md` + `scope/{domain}.md` 경로 선언. 래퍼가 자동 로드. analyze 실행 시 `{domain}` 이 구체 도메인명으로 치환됨 (`[analyze-managed]` 영역).
- `## 핵심 서비스/모델` — **pre-analyze 상태에선 섹션 자체가 없다.** `/pilot:analyze` 가 scope/{domain}.md 의 Models·Services 중 features 관련 행을 선별해 자동 주입 (`[analyze-managed]` 영역).
- `## 구현 패턴` / `## 주의사항` — 이 프로젝트 고유 패턴·엣지 케이스. 사용자가 직접 기술.
- `## 코드 생성 후 검증` — [`evals/coding.json`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/evals/coding.json) 참조 (필수 · 템플릿에 포함).

> **TDD 모드**일 때: `/pilot:tdd` 가 파일 최상단에 경고 앵커를 추가한다 — Red(실패 테스트 작성·실패 확인) → Green(최소 구현) → Refactor 를 순환. 앵커 문구 정본: [`tdd-activation.md`](../../modes/tdd-activation.md) § 3.

---

## prompts/evaluator.md

이 프로젝트 구현 완료 후 검토할 체크리스트. 래퍼(`@pilot-evaluator`)가 로드해 실행한다.

### 포함 내용

- `## 기능 완성도` — `project.md` 목표 기대결과 충족 확인 (템플릿에 기본 항목 포함). analyze 실행 시 features 별 기대결과가 추가됨.
- `## 프로젝트 고유 항목` — **pre-analyze 상태에선 빈 상태**. analyze 실행 시 features/ 의 비즈니스 규칙·예외 케이스를 체크리스트로 주입.
- `## 일관성` / `## 테스트` — 언어 컨벤션·공통 테스트 체크 (템플릿에 기본 항목 포함).

> **TDD 모드**일 때: `/pilot:tdd` 가 파일 상단에 `## TDD 테스트 실행` 앵커를 추가한다 — 변경 관련 테스트 실행 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 참조.

---

## 템플릿 원본

스캐폴딩 소스는 [example/](example/) 폴더 4종 (`project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md`) 이다. 본 가이드는 **구조 설명용** 이며, 실제 프로젝트 생성 시에는 `/pilot:project` 가 example 파일을 그대로 복사한다 (상세: [project SKILL.md Step 2](../../../project/SKILL.md)).

가이드 본문의 섹션 설명과 example 의 실제 파일이 충돌할 경우 **example 이 SSOT**. 가이드 쪽을 동기화할 것.

---

## 작은 변경은 phase 를 우회한다

오타 수정·주석 추가·의존성 bump 같은 trivial 변경은 3-phase pipeline (Planner → Generator → Evaluator) 을 강제하지 않는다. 아래 criteria **모두** 만족하면 메인 대화에서 직접 처리:

- 변경 파일 1~2 개
- 로직 변경 아님 (리팩토링·주석·상수·네이밍)
- 기존 테스트 영향 없음
- `/pilot:pilot-doctor` ERROR 없음

**왜 우회가 정식 경로인가:**

- pipeline 의 가치는 **deliberate checkpoint** — 큰 변경에서 효과
- trivial 변경에 3-phase 강제는 의식(ritual) 비용만 발생시키고 품질 이득 미미
- 프레임워크 우회가 "규칙 위반" 이 아니라 **명시적 선택지** 로 문서화되면 사용자가 프레임워크 밖으로 도망가지 않음

**우회 기준 불분명 시:**

- `@pilot-planner` 에게 "trivial 로 판단되면 간단히만 계획" 지시 (`.focus.md` 또는 `/pilot:focus "{지시}"` 로 전달)
- Planner 가 스스로 "이건 trivial 이라 바로 구현 가능" 이라고 판단하면 Generator 로 scope 축소해서 진행

이 경로는 pipeline **우회 정식 선택지**. 우회했다고 평가·품질 이슈가 되지 않는다.
