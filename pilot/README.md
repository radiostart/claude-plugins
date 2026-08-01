# pilot

> **pilot** is a Claude Code plugin for AI-assisted work on large legacy codebases. It externalizes
> domain knowledge from code into a versioned `workspace/` metastructure and drives complex projects
> through an explicit four-agent cycle — *plan → critic → generate → evaluate* — keeping the user in
> control between every phase. Full documentation (Korean) lives at
> **<https://radiostart.github.io/claude-plugins/>**.

**레거시 시스템에서 AI 활용을 위한 도메인 지식 외부화 + 프로젝트 단위 작업 틀.**

큰 레거시 코드베이스 (수만~수십만 라인) 에서 AI 가 도메인을 한 번에 이해하지 못하는 문제를 해결한다. 코드에서
도메인 지식을 추출해 `workspace/context/` 에 외부 문서로 보관하고, 프로젝트 단위로 격리된 작업 틀을 제공해
AI 가 필요한 지식만 효율적으로 load 하며 작업하게 한다. 플러그인은 **메커니즘** (에이전트 래퍼·스킬·훅) 만
제공하고, 도메인 지식 (비즈니스 규칙·파일 경로·상태값) 은 소비 프로젝트의 `workspace/context/` 에서
사용자가 직접 관리한다.

- **L1 — 도메인 지식 외부화:** `/pilot:learn` 이 코드 → `workspace/context/{domain}/` 산출, `/pilot:characterize` 가 레거시 동작을 테스트로 포착.
- **L2 — 프로젝트 단위 작업 틀:** 1 workspace / N projects, 같은 도메인 지식 공유.
- **L3 — 결정 trace + 자동 마이그레이션:** 설계 결정 문서 + `.agent-state.yml` schema 자동 주입.

> 📖 **전체 매뉴얼 (한국어): <https://radiostart.github.io/claude-plugins/>**
> 본 README 는 설치·부트스트랩만 다룬다. 개념·스킬·에이전트·운영의 정본은 매뉴얼 사이트가 SSOT.

---

## 설치

### 1. 플러그인 등록

Claude Code 의 marketplace 기반 플러그인 시스템을 사용한다. 이 플러그인은
[`radiostart/claude-plugins`](https://github.com/radiostart/claude-plugins) 레포의 `pilot/` 폴더로 배포된다.

```
/plugin marketplace add radiostart/claude-plugins
/plugin install pilot@radiostart-plugins
```

설치 후 Claude Code 재시작 시 에이전트·스킬·훅이 자동 등록된다. 성공하면 `/pilot:*` 슬래시 커맨드와
`@pilot-planner`·`@pilot-planner-critic`·`@pilot-generator`·`@pilot-evaluator`·`@pilot-code-review`
subagent 호출이 가능해진다.

업데이트: `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins`
→ **세션 재시작**. 열려있는 세션은 시작 시점에 로드한 경로가 고정이라 재시작 전에는 구버전이 계속 쓰인다.

> 마켓플레이스 **id 는 `radiostart-plugins`** 이고 `radiostart/claude-plugins` 는 GitHub **레포 경로**다.
> `add` 에만 레포 경로를 쓰고, `install`·`update` 에는 id 를 쓴다.

#### `/plugin` 이 막힌 환경

지원 경로는 `/plugin` 하나다. IDE 내장 세션이라면 같은 `~/.claude` 설정을 공유하는 다른 터미널의
`claude` 에서 시도해 볼 수 있으나 환경에 따라 불가하며, 관리형 세션처럼 `/plugin` 자체가 제공되지
않는 환경에는 **현재 pilot 측이 제공하는 우회 수단이 없다**.

`~/.claude/plugins/` 를 직접 조작하는 절차는 안내하지 않는다 — 플러그인이 실제로 로드되는 경로는
`cache/{marketplace}/pilot/{version}/` 이고 `installed_plugins.json` 레지스트리가 이를 가리키는데,
마켓플레이스 클론만 당겨서는 이 경로가 갱신되지 않는다 (캐시 생성·전환은 `/plugin` 의 몫).

### 2. 워크스페이스 부트스트랩

작업할 저장소에서 한 줄이면 전체 구조가 생성된다 (idempotent):

```
/pilot:pilot-init
```

```
workspace/
├── STATE.md          # 진행중 프로젝트 추적
└── context/
    ├── MANIFEST.md   # 도메인 지식 진입점
    └── config.md     # 런타임 설정 (Ignore · 언어·도구 · commit_scopes)
```

모든 파일은 비워둬도 fallback 으로 동작한다 — 도메인 지식은 코드 작업 중 필요해질 때 점진적으로 채운다.

---

## Quick Start — 최소 시퀀스

```
/pilot:pilot-init                                  # (1회) 워크스페이스 부트스트랩
/pilot:project MyFeature                     # 프로젝트 생성·활성화
/pilot:create-feature "지연 주문 목록 UI"      # feature 명세 단건 추가

@pilot-planner          # features/NN-*.md → plan 수립
@pilot-planner-critic   # (권장) plan 을 red-team 챌린지
@pilot-generator        # plan 기반 구현
@pilot-evaluator        # 요구사항 충족·검증 리포트

/pilot:commit
```

각 에이전트는 사용자가 **명시 호출**한다 — 자동 파이프라인이 아니라 phase 사이 개입 가능한 흐름이다. 두 갈래의
따라하기는 [Tutorial](https://radiostart.github.io/claude-plugins/tutorial/quick-start/) 참조.

> 저위험·소규모 feature 의 호출 마찰을 줄이고 싶으면 `/pilot:autopilot NN` (감독형 자율 모드) 으로 위 4-에이전트 흐름을 자동 순차 진행할 수 있다 — critic blocking·재시도 소진 등 hard-stop 신호에 걸리면 즉시 사람에게 제어를 반환한다. opt-in 예외 모드이며 기본은 수동 호출이다.

### 모델·effort 기본값과 상위 모델 선택 사용

에이전트별 모델·effort 는 `agents/*.md` frontmatter 가 기본값이다 — `generator` 만 `model: opus` 명시 (나머지는 미지정 = 기본 모델), 계획 단계 2종 (planner·planner-critic) 은 `effort: xhigh` (나머지는 세션 상속). fable 은 토큰 소모가 커서 frontmatter 기본값으로 넣지 않는다. 특별히 어려운 feature 에서만 선택 사용한다: 메인 세션에 "이번 계획은 fable 로 돌려줘" 라고 요청하면 호출 단위 `model` 파라미터가 frontmatter 를 override 한다 (해석 순서: `CLAUDE_CODE_SUBAGENT_MODEL` env > 호출 파라미터 > frontmatter > 메인 세션 모델 — [sub-agents § Choose a model](https://code.claude.com/docs/en/sub-agents)). `effort:` frontmatter 반영은 Claude Code CLI **v2.1.78+** (플러그인 에이전트 지원 도입 버전) 이 필요하다.

---

## 문서

정본은 모두 매뉴얼 사이트에 있다 — README 는 더 이상 상세를 중복하지 않는다.

| 찾는 것 | 매뉴얼 위치 |
|---|---|
| 한 사이클 직접 따라하기 | [Tutorial](https://radiostart.github.io/claude-plugins/tutorial/quick-start/) |
| pilot 이 푸는 문제·아키텍처 | [Explanation → 핵심 개념](https://radiostart.github.io/claude-plugins/explanation/concepts/) |
| `/pilot:*` 스킬 커맨드 전체 | [Reference → Skills](https://radiostart.github.io/claude-plugins/reference/skills/) |
| 에이전트 5 종 책임·호출 절차 | [Reference → Agents](https://radiostart.github.io/claude-plugins/reference/agents/) · [에이전트 흐름](https://radiostart.github.io/claude-plugins/explanation/agent-flow/) |
| 보조 CLI (`orchestrate-load`·`doctor` 등) | [Reference → Tools](https://radiostart.github.io/claude-plugins/reference/tools/) |
| TDD·Characterize·Critic·Focus 등 작업별 레시피 | [How-to](https://radiostart.github.io/claude-plugins/how-to/) |
| `workspace/` 구조·도메인 컨텍스트 | [Explanation → Workspace 레이아웃](https://radiostart.github.io/claude-plugins/explanation/workspace-layout/) |
| drift 감지·대응 | [Drift Protocol](https://radiostart.github.io/claude-plugins/explanation/drift-protocol/) · [Doctor 마이그레이션](https://radiostart.github.io/claude-plugins/how-to/doctor-migration/) |
| 릴리스·schema 마이그레이션 정책 | [Explanation → 릴리스·업그레이드](https://radiostart.github.io/claude-plugins/explanation/release-and-upgrade/) |

---

## 핵심 원칙

- **플러그인은 도메인 지식을 내장하지 않는다.** `workspace/context/` 는 팀이 직접 유지한다.
- **레이어를 섞지 않는다.** 스킬 (환경 세팅) · 에이전트 (작업 수행) · 도메인 (팀 지식) 은 분리된 책임.
- **로컬 상태는 gitignore 권장.** `.agent-state.yml`·`STATE.md`·`.prompts.bak/`·`.focus.history/`.
- **래퍼 에이전트는 별도 인스턴스** — 메인 대화 컨텍스트를 못 본다. 의도 전달은 `/pilot:focus`.
- **도메인 규칙 하드코드 금지.** agent 파일에 메모 문구·상태값을 박으면 `rules/` 와 drift — "참조만" 원칙.

---

## 릴리스 및 업데이트

릴리스는 `gh` CLI 로 진행한다. **버전을 올리는 PR 에서 아래 세 곳을 같은 값으로 갱신**한 뒤 main 에 머지한다:

- `pilot/.claude-plugin/plugin.json` 의 `version` — 버전 SSOT
- `pilot/mkdocs.yml` 의 `extra.version` — 불일치 시 `release.sh` 가 릴리스를 중단
- `pilot/docs/index.md` 의 `v{version} highlights` 블록 — 제목·변경 내용 (patch 릴리스면 생략 가능)
- 루트 `.claude-plugin/marketplace.json` 의 `description` — plugin.json description 변경 시 동기화

그다음:

```bash
git checkout main && git pull --ff-only
python3 pilot/tools/doctor.py --schema   # CI(validate.yml) 와 동일한 구조 검사 — ERROR 0 만 확인
                                         # (version 은 올렸고 태그는 아래 release.sh 가 만드므로
                                         #  `version vs git tag` WARN 1건은 이 시점에 정상)
claude plugin validate ./pilot --strict  # 보조 — Claude Code 자체 검사 (아래 주 참조)
./pilot/tools/release.sh                 # plugin.json 버전 자동 인식 — 태그·GitHub Release 생성
```

> **두 검사는 서로 대체하지 않는다.** `doctor --schema` 만 SKILL description 바이트 상한과
> version↔git tag 정합을 보고, `claude plugin validate --strict` 만 `plugin.json` 미지 키를 잡는다
> (2026-07-26 손상본 주입 실측 — 대조표는 `workspace/projects/build-plugin/features/25-schema-vs-claude-validate.md`).
> manifest JSON 문법 파손·frontmatter 부재·`hooks.json` 미지 이벤트는 **양쪽 다** 잡는다.
> CI 게이트는 러너에 CLI 설치·인증이 필요 없는 `doctor --schema` 쪽을 쓰고
> (`.github/workflows/validate.yml`), CLI 검사는 릴리스 전 로컬 보조 수단으로 둔다.

사용자 측 업데이트는 `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins`
(또는 `/plugin` → Installed → pilot → Update) 후 세션 재시작. semver 기준·schema 마이그레이션·캐시
정리는 [Explanation → 릴리스·업그레이드](https://radiostart.github.io/claude-plugins/explanation/release-and-upgrade/) 참조.

---

## 지원 환경

Claude Code 가 실행되는 모든 환경 — CLI (`claude`), Desktop App, VS Code / JetBrains 확장,
Web (claude.ai/code).

> ⚠️ 앱 (데스크톱/웹) 세션은 `/plugin` 슬래시 커맨드를 지원하지 않는다. 터미널에서 `claude` 로 한 번
> 업데이트한 뒤 앱 세션을 재시작한다.

## 검증 데이터

Rails 4K 라인 도메인 (nimda wms) 산출 결과 — 922 라인 (22.4% 압축), 217 file:line 인용,
100% 인용 정확성 (V1-Full dogfooding, 2026-04-30).
