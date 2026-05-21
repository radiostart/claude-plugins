# Plan — pilot 매뉴얼 사이트 (MkDocs Material)

> status: draft (review 대기)
> created: 2026-05-21
> 도구: **MkDocs Material**
> 정보구조: **Diataxis 4 분류** (Tutorial / How-to / Reference / Explanation)
> 호스팅: **GitHub Pages**

## 1. 목표·범위

현재 `pilot/README.md` 는 600+ 줄에 11 개 H2 섹션·다중 표·트리 다이어그램이 한 페이지에 압축돼 있다. 처음 사용자는 길이에 압도되고, 숙련 사용자는 reference 를 찾기 어렵다. 매뉴얼을 별도 사이트로 분리해 *역할별 진입* 을 제공한다.

### in scope

- MkDocs Material 기반 정적 사이트, GitHub Pages 배포 (`mkdocs gh-deploy`).
- Diataxis 4 분류 정보구조.
- `skills/`·`agents/`·`tools/` 의 사용자 facing 메타데이터 자동 추출 → reference 페이지 자동 생성.
- README 는 *단축본 + 사이트 링크* 로 슬림화 (완전본은 사이트가 SSOT).
- Mermaid 다이어그램 (planner→critic→generator→evaluator 흐름, workspace 구조, doctor 마이그레이션 트리).

### out of scope

- 다국어 (한국어만 — pilot 의 SSOT 가 한국어이므로 fallback 없음).
- 인터랙티브 데모 (critic 시뮬레이션 UI 등 — 향후 별도 plan).
- 검색·다크모드 외 사용자 JS (Material 기본 제공 외 추가 안 함).
- 사이트 안에서의 콘텐츠 *작성* — 모든 문서는 SSOT (skills/agents/tools/README) 에서 *유도*. 사이트 자체는 view layer.
- doctor 의 docs drift 감지 확장 (별도 plan 으로 분리).

## 2. 사이트 구조 (Diataxis 4 분류)

```
docs/
├── index.md                        # 랜딩 (가치 제안 + 4 경로 안내)
├── tutorial/
│   ├── installation.md             # ← README §설치 및 초기 세팅
│   ├── quick-start.md              # ← README §Quick Start (init→project→planner 1 사이클)
│   └── getting-started.md          # ← 기존 docs/getting-started.md (그대로 이동)
├── how-to/
│   ├── tdd-mode.md                 # TDD 활성화 (skills/tdd)
│   ├── characterize-mode.md        # 레거시 코드 보강 (skills/characterize)
│   ├── critic-review.md            # planner-critic 활용 (v0.4.0 신규)
│   ├── focus-direction.md          # 방향 조정 (skills/focus)
│   ├── analyze-docs.md             # docs→features (skills/analyze)
│   ├── create-feature.md           # 단건 추가 (skills/create-feature)
│   ├── cross-domain-learn.md       # 외부 도메인 부트스트랩 (skills/learn)
│   ├── doctor-migration.md         # 스키마 마이그레이션 (skills/doctor/references)
│   ├── confluence-sync.md          # Confluence 연동 (skills/confl)
│   ├── slack-notify.md             # Slack 알림 (skills/slack)
│   └── moai-adk-integration.md     # ← docs/INTEGRATION-MOAI-ADK.md
├── reference/
│   ├── agents/                     # 자동 추출 — agents/*.md (5 개)
│   ├── skills/                     # 자동 추출 — skills/*/SKILL.md (18 개)
│   ├── tools/                      # 자동 추출 — tools/*.py CLI 인터페이스
│   ├── config.md                   # 언어·도구 기본값 표 (← config.md.template)
│   ├── state-schema.md             # ← skills/context/lifecycle/state-schema.md
│   ├── plan-schema.md              # ← skills/context/lifecycle/plan-schema.md
│   ├── identity.md                 # 페르소나 SSOT (← shared/identity.yml)
│   ├── hooks.md                    # ← README §Hooks & Tools
│   └── supported-env.md            # ← README §지원 환경
└── explanation/
    ├── concepts.md                 # ← README §핵심 개념
    ├── agent-flow.md               # planner→critic→generator→evaluator 흐름 + 페르소나 분리
    ├── workspace-layout.md         # STATE.md / projects/ / context/ 구조 + Mermaid
    ├── modes.md                    # Standard vs TDD vs Characterize 비교
    ├── drift-protocol.md           # ← skills/context/lifecycle/drift-protocol.md
    ├── ssot-and-derivation.md      # skill·agent·tool SSOT, README/site 가 derived 임을 명시
    └── release-and-upgrade.md      # ← README §릴리스 및 업데이트
```

랜딩 `index.md` 는 4 경로 카드 (Tutorial: "처음이라면" / How-to: "이걸 하려면" / Reference: "정확한 값 찾기" / Explanation: "왜 이렇게 동작하는지") 와 v0.4.0 highlights 만.

## 3. 콘텐츠 소싱 매핑

| 사이트 위치 | SSOT 출처 | 변환 방식 |
|---|---|---|
| `tutorial/installation.md` | `README.md` §설치 및 초기 세팅 | 수동 1 회 분리 + README 는 stub 만 |
| `tutorial/quick-start.md` | `README.md` §Quick Start | 동일 |
| `tutorial/getting-started.md` | `docs/getting-started.md` | 이동 (1:1) |
| `how-to/*` | 각 `skills/{name}/SKILL.md` + `references/*.md` | 사용자 facing 섹션만 수동 발췌 (절차 H2/H3 일부 + 예시) |
| `reference/agents/*` | `agents/*.md` | **자동 추출** — frontmatter + 책임 경계 + 절차 헤더 |
| `reference/skills/*` | `skills/*/SKILL.md` | **자동 추출** — frontmatter + 본문 |
| `reference/tools/*` | `tools/*.py` docstring + argparse | **자동 추출** — `--help` 출력 + module docstring |
| `reference/config.md` | `skills/context/lifecycle/setup/templates/config.md.template` | snippet include |
| `reference/state-schema.md` · `plan-schema.md` | `skills/context/lifecycle/*.md` | snippet include |
| `reference/identity.md` | `skills/context/shared/identity.yml` | YAML → 표 변환 (스크립트) |
| `reference/hooks.md` · `supported-env.md` | `README.md` 해당 섹션 | 수동 1 회 분리 |
| `explanation/concepts.md` | `README.md` §핵심 개념 | 이동 + Mermaid 추가 |
| `explanation/agent-flow.md` | `agents/*.md` + `README.md` §에이전트 | 새로 작성 (critic 포함) |
| `explanation/workspace-layout.md` | `skills/context/INDEX.md` + 트리 | 새로 작성 |
| `explanation/modes.md` | `skills/context/modes/*.md` | 비교 표로 재구성 |
| `explanation/drift-protocol.md` | `skills/context/lifecycle/drift-protocol.md` | snippet include |
| `explanation/ssot-and-derivation.md` | (새 콘텐츠) | site 자체의 메타 — README/site 가 derived 임을 명시 |

## 4. 자동 추출 스크립트

`pilot/tools/docs_build.py` (신규).

- **입력**: `pilot/agents/*.md`, `pilot/skills/*/SKILL.md`, `pilot/tools/*.py`, `pilot/skills/context/shared/identity.yml`.
- **출력**: `pilot/docs/reference/{agents|skills|tools|identity.md}/*.md` (gitignored — build artifact, 또는 commit 정책은 §6 에서 결정).
- **변환 규칙**:
  - 에이전트·스킬: frontmatter (`name`, `description`) 를 첫 H1·subtitle 로, 본문은 "wrapper 인용 블록" 까지 제거하고 나머지 그대로.
  - tools: `python3 {tool}.py --help` 캡처 + module docstring 추출.
  - identity.yml: `personas` 키를 표 (archetype·voice·phrasing·forbid) 로 렌더.
- **호출 지점**: `mkdocs build` / `mkdocs serve` 전 prebuild hook (mkdocs `on_pre_build` 또는 GitHub Actions 의 별도 step).
- **idempotent**: 재실행해도 같은 결과. drift 감지를 위해 `--check` 모드 (출력이 git 과 다르면 exit 1).

테스트는 `pilot/tests/tools/test_docs_build.py` — fixture 로 가짜 SKILL.md 와 agent.md 1 개씩 두고 생성 결과 비교.

## 5. MkDocs 설정 (`mkdocs.yml` 핵심 키)

```yaml
site_name: pilot
site_url: https://radiostart.github.io/claude-plugins/
docs_dir: docs                       # mkdocs.yml 이 pilot/ 안에 있으므로 상대 경로
site_dir: docs-site                  # build artifact, gitignored
theme:
  name: material
  language: ko
  features:
    - navigation.tabs                # Tutorial / How-to / Reference / Explanation 상단 탭
    - navigation.sections
    - navigation.indexes
    - content.code.copy
    - search.suggest
  palette:
    - scheme: default
    - scheme: slate                  # 다크 모드
plugins:
  - search:
      lang: ko
  - mermaid2                         # 다이어그램
markdown_extensions:
  - admonition                       # !!! note 블록
  - pymdownx.tabbed                  # 코드 예시 탭
  - pymdownx.snippets                # 다른 파일 include
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
nav:
  - Home: index.md
  - Tutorial: tutorial/
  - How-to: how-to/
  - Reference: reference/
  - Explanation: explanation/
```

`mkdocs.yml` 위치는 **`pilot/mkdocs.yml`** (plugin 내부). 실행은 `cd pilot && mkdocs serve`. 다른 plugin 과의 결합 회피. 향후 plugin 별 매뉴얼을 합치게 되면 `{plugin}/` path 분리로 통합.

## 6. 빌드/배포

- **로컬 개발**: `cd pilot && mkdocs serve` (포트 8000).
- **수동 배포**: `cd pilot && mkdocs gh-deploy --force` (gh-pages 브랜치에 push).
- **자동 배포**: GitHub Actions `.github/workflows/docs.yml`.
  - 트리거: `main` push when `pilot/{docs,skills,agents,tools,README.md,mkdocs.yml}` 변경.
  - step: checkout → setup-python → `pip install mkdocs-material mkdocs-mermaid2-plugin` → `python pilot/tools/docs_build.py` → `cd pilot && mkdocs gh-deploy --force`.
  - permissions: `contents: write` (gh-pages branch push 용).
- **GitHub Pages 활성화**: repo settings → Pages → source: `gh-pages` branch, `/` root.
- **자동 추출 결과 commit 정책**: gitignored. 빌드 시점에만 생성. 이유 — 매 변경마다 reference/ 가 변경되면 diff 노이즈 큼. drift 감지는 CI 의 `docs_build.py --check` 가 담당 (실패 시 PR block).

## 7. 이미지·다이어그램

- **Mermaid 우선**. 텍스트로 유지보수 가능. `mkdocs-mermaid2-plugin` 으로 렌더.
- 최소 4 개 다이어그램:
  1. `explanation/agent-flow.md` — planner↔critic↔generator↔evaluator 흐름 (시퀀스).
  2. `explanation/workspace-layout.md` — `workspace/` 트리 (graph).
  3. `explanation/modes.md` — Standard / TDD / Characterize 진입 조건 (decision tree).
  4. `how-to/doctor-migration.md` — schema 마이그레이션 트리.
- **스크린샷**: 필요한 경우만 (Slack 알림 1 장 정도). `docs/assets/` 에 저장. 다크/라이트 모드 둘 다 캡처 강제 안 함.

## 8. 유지보수

- **SSOT**: `skills/`·`agents/`·`tools/` 가 SSOT. README 와 site 는 모두 derived.
- **drift 감지**:
  - CI 가 매 PR 에서 `pilot/tools/docs_build.py --check` 실행. 자동 추출 결과가 source 와 어긋나면 fail.
  - 수동 분리 페이지 (tutorial/installation 등) 는 SSOT 가 README 인데 양쪽 동기화 필요. 1 회 분리 후 README 를 stub 으로 줄이는 방향 — 즉 **분리 후 README §해당 섹션은 사이트 링크로 대체**해서 동기화 부담 자체를 제거.
- **버전 표시**: 사이트 헤더에 `plugin_version` 자동 표시 (`plugin.json` 의 `version` 을 `docs_build.py` 가 `mkdocs.yml` extra 로 주입).
- **릴리스 노트**: `pilot/CHANGELOG.md` 가 있으면 `explanation/release-and-upgrade.md` 에 snippet include.

## 9. 단계별 구현 순서

1. `mkdocs.yml` + `pilot/docs/index.md` + 4 분류 디렉토리 골격 + 한 페이지 (tutorial/quick-start) 작성 → 로컬 `mkdocs serve` 동작 확인.
2. `pilot/tools/docs_build.py` 작성 + 단위 테스트 (agents 1 개 + skills 1 개 + tools 1 개 fixture).
3. 자동 추출 결과를 `reference/` 에 채움 (전체 agents·skills·tools).
4. How-to 페이지 작성 (10 ~ 11 개 페이지, 각각 30 ~ 80 줄).
5. Explanation 페이지 작성 + Mermaid 4 개.
6. Tutorial 페이지 재정리 (기존 `getting-started.md` 이동 포함).
7. README 슬림화 (분리된 섹션은 사이트 링크로 대체).
8. `.github/workflows/docs.yml` 추가 + GitHub Pages 활성화.
9. 첫 배포 + 링크 검증 (`mkdocs --strict`).
10. doctor 에 docs 빌드 검증 추가 (선택 — out of scope 후보).

각 단계는 별도 PR 로 가능. 1~3 은 기반, 4~6 은 콘텐츠, 7~9 는 배포·정리.

## 10. 확정 결정

- **(a) `docs_build.py` 출력 — gitignored.** drift 감지는 CI `--check` 가 담당. PR diff 노이즈 회피. 사이트 깨졌을 때 원인 추적이 어려운 단점은 CI 로그·로컬 재현으로 보완.
- **(b) `quick-start.md` 와 `getting-started.md` — 역할 분리.** quick-start = **5 분 데모** (init → project → 첫 plan, 3 명령 + 결과 스크린샷 1 장). getting-started = **30 분 deep walkthrough** (현재 `docs/getting-started.md` 그대로 이동, 11 단계).
- **(c) 언어 — 한국어 단일.** pilot SSOT 가 한국어이므로 영어 매뉴얼은 영구 derived 부담. README 상단에 1 단락 영어 abstract 만 두고 "Korean docs at https://radiostart.github.io/claude-plugins/" 안내.
- **(d) `mkdocs.yml` 위치 — `pilot/mkdocs.yml`.** plugin 내부. §5·§6 본문 반영 완료.

## 11. Design Decisions (light pass)

가벼운 design pass 결과. mockup 생성은 건너뜀 (Material 테마의 제약이 design 자유도를 자연스럽게 좁힘).

### 11.1 랜딩 `index.md` 정보구조

- 헤더: `pilot v{version}` 배지 + 1 문장 가치 제안 ("도메인 지식 기반 에이전트 워크플로우 플러그인").
- 4 카드 — **균등 grid 아님**. Tutorial 카드가 *더 크고 위쪽*. 처음 사용자가 진입점 분명하도록.
  - **Tutorial** (primary, 큰 카드): "처음이라면" — quick-start / getting-started 링크.
  - **How-to** · **Reference** · **Explanation** (작은 카드 3 개, 균등): 각 1 문장 설명 + 대표 페이지 1~2 개 링크.
- "v{version} highlights" 1 블록 — 최신 변경 (현재 기준: planner-critic, doctor migration, init wizard).
- 푸터: GitHub 링크 · CHANGELOG · 버전.

### 11.2 How-to 페이지 표준 구조

Diataxis how-to 권장 패턴 — 모든 How-to 가 같은 구조여야 사용자 인지 부하 ↓.

```markdown
# {작업 제목}

!!! info "한 줄 요약"
    {이 작업이 해결하는 문제 · 결과물}

## 전제

- {필요한 사전 상태 1}
- {사전 상태 2}

## 절차

### 1. {step 제목}
{명령 + 예상 출력 + 실패 시 조치}

### 2. ...

## 다음 단계

- Reference: [{관련 reference 1}](...)
- How-to: [{다음에 자주 함께 하는 작업}](...)
```

### 11.3 모바일·접근성

- **Material 기본 의존**: 햄버거 nav, 다크 모드 토글, 검색, skip-to-content 링크.
- **명도 대비**: default + slate palette 둘 다 WCAG AA 통과 (Material 기본). 커스텀 컬러 도입 금지 (그러면 통과 검증 부담).
- **코드 블록 복사**: `content.code.copy` (§5 설정 완료).
- **터치 타겟**: 44px+ (Material 기본).
- **Mermaid alt text**: `docs_build.py` 가 alt 미정 다이어그램을 build 시 warning. 정책: title 1 줄 의무.

### 11.4 검색 (한국어)

- Material 검색은 lunr 기반 — 한국어 토큰화 약함 (공백 단위).
- 1 차: `search.lang: ko` + `search.separator: '[\s\-,:!=\[\]()"`/]+|\.(?!\d)'` (조사·구두점 분리).
- 첫 배포 후 검색 정확도 *수동 측정* — 5~10 개 대표 쿼리로 적중 평가. 부족 시 algolia DocSearch 또는 lunr-languages 확장 검토 (별도 plan).

### 11.5 다이어그램 (Mermaid 4 개의 내용)

| 위치 | 종류 | 내용 |
|---|---|---|
| `explanation/agent-flow.md` | sequenceDiagram | User → Planner → Critic → Planner(합의 표) → Generator → Evaluator. critic skip 분기 점선. |
| `explanation/workspace-layout.md` | graph TD | `workspace/` 트리 — STATE.md, context/{MANIFEST,config,shared,scope,rules}, projects/{P}/{features,prompts,.agent-state,.focus}. |
| `explanation/modes.md` | flowchart | `.agent-state.yml` 의 `mode`·`tdd` 값에 따른 진입 분기 (characterize > tdd > standard). |
| `how-to/doctor-migration.md` | flowchart | schema 버전 감지 → migration 경로 (v1.0→v1.1→v1.2). |

### 11.6 코드 블록·예시 정책

- 언어 명시 의무 (`yaml`, `bash`, `python`, `ruby`). 명시 없으면 build warning.
- 명령 예시는 `bash` + `# 주석` 으로 의도 설명. 출력은 별도 블록.
- 변형 (macOS / Linux 등) 은 `pymdownx.tabbed`.
- 긴 예시는 `pymdownx.snippets` 로 SSOT 파일 include — Reference 페이지는 원본 SKILL.md / agent.md 의 일부를 include 해서 drift 0.

### 11.7 버전·CHANGELOG 노출

- 헤더 우측 `v{version}` 배지 — `docs_build.py` 가 `plugin.json` 의 `version` 을 `mkdocs.yml` 의 `extra.version` 으로 주입.
- 배지 클릭 → `explanation/release-and-upgrade.md` 의 해당 버전 anchor.
- 본격 CHANGELOG 자동 생성은 out of scope. 현재는 `README §릴리스 및 업데이트` snippet include 로 충분.

### 11.8 Cross-link 정책

- 모든 How-to 페이지: "다음 단계" 에 **Reference 1~2 개 + 관련 How-to 1 개** link 의무.
- Explanation ↔ Reference 는 양방향 link.
- Tutorial 에서 Explanation 으로의 link 는 **최소화** — 처음 사용자가 깊이 빠지는 것 방지. 대신 Tutorial 끝에 "더 알아보려면 → Explanation" 한 줄.

## 12. Approved Mockups

본 plan 은 가벼운 design pass 로 진행되어 mockup 생성을 건너뜀 (Material 테마의 시각 제약이 강해서 mockup 으로 검증할 design 결정이 적음). 정식 mockup 이 필요해지면 `/plan-design-review` 또는 `/design-shotgun` 으로 별도 호출.

---

> 본 plan 은 design-complete 상태. 다음은 §9 단계별 구현 순서의 **step 1** (mkdocs.yml + 골격 + quick-start 1 페이지로 로컬 `mkdocs serve` 동작 확인) 부터 시작.
