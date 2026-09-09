# HANDOFF — 개발 인계

`pilot` 플러그인 저장소를 다른 환경에서 이어받기 위한 문서. **환경 셋업 · 확정된 설계 결정 · 현재 백로그**를 담는다.

> **정본 경계** — 플러그인 사용법은 [매뉴얼 사이트](https://radiostart.github.io/claude-plugins/)가, 저장소 오리엔테이션은 [CLAUDE.md](CLAUDE.md)가, 커밋 이력은 `git log` 가 SSOT다. 이 문서는 그 어디에도 안 담기는 인계 사항만 유지한다.

## 새 환경 셋업

```bash
git clone https://github.com/radiostart/claude-plugins.git
cd claude-plugins
pytest pilot/tests/ -q
```

- Python 3.11+ 권장. `pytest` 없이도 `python3 -m unittest discover -s pilot/tests/tools` 로 실행 가능.
- **외부 의존성 없음** — 테스트·도구 모두 표준 라이브러리만 쓴다 (문서 빌드는 예외: `pip install -r pilot/docs-requirements.txt`).
- Confluence 연동(`/pilot:confl`)을 쓸 경우에만 `.env` (gitignored) 작성:

  ```bash
  cat > .env <<'EOF'
  CONFLUENCE_HOST=https://yourorg.atlassian.net/wiki
  CONFLUENCE_EMAIL=user@example.com
  CONFLUENCE_TOKEN=your-api-token
  EOF
  ```

## 현재 상태

**v0.19.0** (tag `pilot-v0.19.0` 은 `release.sh` 로 생성 예정 — 이전 태그 `pilot-v0.18.0`) — 스킬 20 · 에이전트 5 · 훅 7(+opt-in 계측 1) · 도구 15 · 테스트 725.

**v0.19.0 내용 (브랜치 `claude/dp-skills-context-search-enhance-qp02xo`, 2026-09-08~09)** — (1) context-search 고도화: `select:` 다중 + `--inject` + `--format manifest`, 한글 결합어 양방향, frontmatter 파서·`sources` glob 보너스, 탐색 → 선별 → 주입 3단계 프로토콜(wrapper-protocol §6). (2) #30 경로 트리거 C1 확정·적용: `tools/rules-pointer.py` + `doctor/rules_pointer.py` 가 `.claude/rules/pilot-{domain}.md` 를 생성, `hooks/domain-pointer.sh` 보완, doctor 검사 6종. 두 작업 모두 별도 에이전트 red-team critic(각 12건·10건)을 거쳐 합의 반영 — 계획서·critic·실측: `docs/superpowers/plans/2026-09-08-*.md`. release-notes 미배포 절이 사용자 관점 요약.

사내 원본 플러그인에서 파생된 범용판이며, **범용화 리팩터는 완료**됐다 (사내 식별자 sweep 0건). 현재는 원본의 미포팅 기능을 선별 흡수하며 자체 dogfooding(`workspace/projects/build-plugin/`)으로 개발한다 — 미완 항목은 `#22 context 드리프트 재학습` 과 도메인 지식 검색·계층 탐색 로드맵 `#28 신선도 힌트 · #29 frontmatter 매니페스트` (계획서 `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md`). `#30 경로 트리거` 는 미배포 브랜치에서 C1 로 적용 완료(실측 기록은 feature 본문).

버전별 요약은 매뉴얼의 [릴리스 노트](https://radiostart.github.io/claude-plugins/release-notes/)(소스: `pilot/docs/release-notes.md`), 커밋 단위 원본은 [GitHub Releases](https://github.com/radiostart/claude-plugins/releases)가 SSOT.

- **v0.18.0** — `tools/context-search.py` 신설 (H2/H3 섹션 단위 결정적 랭커 · 질의 3형식 · 라인 범위 read_hint) · soft 배선 (orchestrate-load 힌트 1줄 · wrapper-protocol §6 · Explore 계약) · confluence 로컬 검색 랭커 공유 · features #27~#30 등록 (원격 #24~#26 선점으로 재번호).
- **v0.17.0** — autopilot 신호 파서 fail-open 9경로 봉쇄 (적대적 검토 기반) · plan 판정 기계 소유 (`--plan-file`·`--state-file`, `--plan-valid` 폐지) · reflect 후 plan 재검증 · 정지 사유 `agent-error` 정밀화.
- **v0.16.0** — 스킬 3종 신설 (`qa` Jira 결함 처리 phase · `switch` 작업 전환 · `ask` 구현 질의) · learn 기재 규격 (`extraction.md` — 층위 L1/L2/L3·Routes 선별 기재·인용 규격) · doctor 인용 drift 검사 · scope-guard 경로 판정·gitignore 규약 · `plan-target.md` SSOT · state schema **v1.3** (`phase`·`qa_started_at`).
- **v0.15.0** — evaluator REPORT 영속화 (`features/NN-*.eval.md`) · critic·autopilot·focus 훅 양립 개정 · description 감량.

## 확정된 아키텍처 결정

1. **마켓플레이스 구조** — `claude-plugins/` (root, marketplace `radiostart-plugins`) + `pilot/` (플러그인 본체)
2. **워크스페이스 단일 구조** — TEAM 레이어 없음. `workspace/{STATE.md, context/, projects/, issues/}` 직접
3. **agents/ vs prompts/** — 플러그인은 `pilot/agents/` (subagent wrapper), 프로젝트는 `workspace/projects/{P}/prompts/` (컨텍스트 파일)
4. **MANIFEST 가 discovery contract** — `orchestrate-load.py` 가 `## 도메인 분류` 표를 파싱해 진입 파일을 로드. 폴더 구조는 워크스페이스 자유
5. **scope/rules 는 권장 컨벤션** (강제 아님) — 플러그인은 MANIFEST 만 알고 폴더명을 강제하지 않는다
6. **scope schema 지원** — wrapper 실행: v1.1·v1.2 / doctor 읽기: v1·v1.1·v1.2
7. **TDD batch granularity** — feature 단위 (호출 1회 = 1 feature). step/all 모드는 미도입
8. **`/pilot:learn`** — 소스코드에서 도메인 컨텍스트 자동 부트스트랩 (analyze 의 짝)
9. **언어 중립** — 특정 언어 fallback 없음 (config 미정의 시 사용자 질의)
10. **역할 분류 표는 long-form** — wide-form(역할 × 언어) 폐기. "(역할, 언어) 매트릭스 = (역할, 프레임워크) 의 잘못된 압축"
11. **SKILL.md 에 default enumeration 금지** — pilot 은 특정 언어 대상이 아니므로 config 가 1급 시민이고 SKILL.md 는 메커니즘만 기술한다
12. **runtime 은 abort 하지 않는다** — 잘못된 config 행을 만나도 default fallback + stderr WARN 1줄. 1개 행 오류로 전체 워크플로를 멈추지 않는다
13. **issue 는 1급 work_mode** — `orchestrate-load` 가 STATE.md 의 mode 열을 읽어 `issues/{slug}/` 기반으로 사이클을 구동한다 (stateless — 상태 파일 없이 `issue.md` 가 단건 명세)
14. **이력은 STATE.md 에 쌓지 않는다** — 활성 1행만 유지. 과거 작업의 SSOT 는 `projects/*/`·`issues/*/` 로컬 폴더
15. **경로 트리거는 하네스 네이티브(C1)** — `/pilot:learn` 이 `.claude/rules/pilot-{domain}.md`(저장소 루트) 를 생성하고 Claude Code 조건부 규칙이 매칭 소스를 **Read 할 때** 주입한다. 내용은 **포인터만**(진입·규칙·본문·경계 문서 위치, ≤8줄·≤500자) — 지식 본문 복사 없음. Write·Edit 는 발화하지 않으므로(실측) `hooks/domain-pointer.sh` 가 같은 포인터를 세션·도메인당 1회 보완. 런타임 매처 CLI 는 만들지 않는다 (2026-09-09, #30 § 실측 기록)
16. **랭커에 시간 신호를 넣지 않는다** — mtime 은 clone 직후 전 파일이 같고 날짜에 따라 변해 결정성을 깨뜨린다. 신선도는 힌트·표기 전용(#28, context-search manifest 의 age 열)
17. **도메인 지식 본문은 탐색 → 선별 → 주입** — `context-search.py "<키워드>" --scope D --format manifest --limit 8` → 에이전트가 1~3개 선별(rules·boundary 는 핵심 토큰이 맞으면 유지) → `'select:{file}#{heading},…' --inject`. 자동 본문 주입은 두지 않는다(wrapper-protocol §6). 인자는 작은따옴표 — 헤딩의 백틱이 쉘에 치환된다
18. **glob 의미는 gitignore 로 통일** — `.claude/rules paths:` · frontmatter `sources` · `context-search._glob_regex` · scope-guard 가 같은 집합을 가리킨다(`*` 는 `/` 를 넘지 않음)

## 디렉토리 구조

```
claude-plugins/                  ← 마켓플레이스 root (= 이 레포)
├── .claude-plugin/marketplace.json
├── .github/workflows/           ← docs · tests · validate
├── CLAUDE.md                    ← 저장소 오리엔테이션
├── HANDOFF.md                   ← 본 파일
├── docs/                        ← 저장소 수준 감사·설계 이력 (audits · superpowers)
├── workspace/                   ← dogfooding 워크스페이스 (projects/build-plugin)
└── pilot/                       ← 플러그인 본체
    ├── .claude-plugin/          ← plugin.json · PLUGIN_SCHEMA_NOTES.md
    ├── README.md
    ├── agents/                  ← wrapper 5종 (planner · planner-critic · generator · evaluator · code-review)
    ├── skills/                  ← 스킬 20종 + context/ (공유 계약·라이프사이클 문서)
    ├── hooks/                   ← commit-format · scope-guard · protect-managed · coding-rules · domain-pointer · slack-notify · session-context · rules-trace(opt-in)
    ├── tools/                   ← orchestrate-load · doctor(rules_pointer 포함) · context-search · rules-pointer · plan-validate · auto_pilot · docs_build · confluence · slack-notify · regen-verify · release.sh
    ├── docs/                    ← 매뉴얼 소스 (mkdocs). reference/ 하위 생성물은 gitignored
    ├── examples/                ← 언어별 코드리뷰 룰 예시
    └── tests/tools/             ← 단위 테스트 (fixtures/context-search 골든 6질의 · golden-expected.json 포함)
```

## 자주 쓰는 커맨드

```bash
# 테스트 (저장소 루트에서)
python3 -m unittest discover -s pilot/tests/tools

# 매뉴얼 문서 재생성 + drift 검사
python3 pilot/tools/docs_build.py && python3 pilot/tools/docs_build.py --check

# 플러그인 스키마 검사 (CI 와 동일)
python3 pilot/tools/doctor.py --schema

# 워크스페이스 정합성 검사
python3 pilot/tools/doctor.py workspace

# 사내 식별자 sweep (정상이면 0건)
grep -rn 'dp-skills\|deali\|workspace/{TEAM}\|ag-planner' pilot/ \
  --include="*.md" --include="*.py" --include="*.sh" | grep -v 'docs/reference/'

# 릴리스 (main clean + 버전 표기 5곳 동기 후 — README § 릴리스 및 업데이트)
pilot/tools/release.sh
```

> `orchestrate-load.py` 는 워크스페이스를 인자로 받는다: `python3 pilot/tools/orchestrate-load.py --phase planner --workspace workspace`

## 다음 작업 후보

미배포 브랜치 작업의 후속 (우선순위 순):

1. **G6 dogfooding** — 다음 feature 사이클에서 래퍼(planner·generator·evaluator)가 `pilot/skills/**` 등 매칭 경로를 Read 할 때 규칙 포인터가 나타나고 그 문서를 Read 했는지, manifest → select --inject 3단계를 썼는지 기록. 효과 측정의 기준선은 evaluator 반려 사유 중 "규칙 미반영" 비율. 로드 증거는 `pilot/hooks/rules-trace.sh` 를 `.claude/settings.local.json` 의 `InstructionsLoaded` 훅으로 opt-in 등록해 남긴다(#30 § 실측 기록 스니펫). Explore·Plan 도 경로 규칙은 발화함(2026-09-09 실측).
2. **#29 frontmatter 매니페스트** — 머지 시 `rules-pointer.py --all --write` 로 `sources` 기반 재생성(추정 주석 소멸), `type` 기반 본문 포인터·manifest `[type]` 태그 실측. `context-search` 는 이미 `sources`·`type`·`domain` 을 읽는다.
3. **stale 컨텍스트 재학습** — `context/pilot/{index,review,spec}.md` 가 이번에 바뀐 `wrapper-protocol.md`·`orchestrate-load.py` 를 인용(doctor WARN). drift-protocol 상 `/pilot:learn` 재실행은 사용자 승인 사항.
4. **릴리스** — `plugin.json` 버전 확정 → release-notes 미배포 절을 버전 절로, 버전 목록 표 행 추가, HANDOFF 현재 상태 갱신.
5. **역방향 경로 질의 노이즈** — `context-search.py "app/x.rb"` 는 경로 세그먼트 토큰(`app`·`pilot` 등)이 무관 섹션에도 path 점수를 준다(라이브: 상위 2건 정확, 4건 노이즈). `matched` 에 원 경로가 있는 결과만 취하는 필터는 #27 비즈니스 규칙(세그먼트 자동 가중)을 바꾸는 일이라 사용자 결정 후 골든 재캡처와 함께.
6. **dp-skills 이식 시 주의** — 지시서의 함수명(`parse_frontmatter_description`·`_word_boundary_hit`)·`docs/reference/tools/context-search.md`·`workspace/{TEAM}`·`--team` 은 이 저장소에 없다. 경로 치환 전에 그쪽 코드가 분기했는지 diff 확인.


- **`#22` context 드리프트 재학습** — `workspace/context/pilot/` 이 삭제된 스크립트 3종(`memory-hint`·`init_detect`·`diagnose.py`)과 개명 전 스킬명, issue 경량 모드를 서술 중. `/pilot:learn ./pilot/skills` 재실행으로 일괄 해소한다 (**직접 Edit 금지** — drift-protocol § A). doctor 가 `spec.md` mtime drift 로 감지 중이며, v0.16.0 의 **인용 drift 검사**가 stale 인용까지 추가로 지목한다 (도그푸딩 워크스페이스에서 WARN 다건 예상 — 재학습이 정식 처방).
- **미포팅 백로그** — greenfield 즉석 등재 · HOTL 다중 순회 (autopilot 은 단일 feature 한정 유지) · AskUserQuestion 기반 사전 인터뷰 (pilot 의 OQ 소비형 인터뷰와는 다른 설계라 통째 이식 금지).
- **autopilot 재시도 카운터 보조 상한** — `{R}` 는 모델 컨텍스트 + 게이트 이력 1줄 앵커에 의존 (known limitation). `{AUTO_LOG}` 파생 상한을 도입하려면 먼저 SKILL.md 에 로그 행 문법을 기계 판정 가능하게 정본화(행 시작 `[generator]` 앵커)하고 "요약-유실 대비 보조 상한"(max 규칙)으로 설계할 것 — 2026-08-25 적대적 검토(R7)로 1차 안 기각.
- **`orchestrate-load` placeholder leak** — `parse_lang_tools` 가 config 표의 예시 표기를 실값으로 반환 (doctor 의 구조 기반 판정을 재사용해 해소 가능).
- ~~Slack pr 기본값~~ — 해소 (2026-08-03, 기본값 complete,approval,pr 로 통일 — 사용자 제품 판단).
- **영어 README** — 보류 (사용자 판단).

## 이력 — v1 dogfooding 검증 (2026-04-30)

`/pilot:learn` 이 실제 대형 레거시에서 작동하는지 검증한 기록. 126K 라인 Ruby monolith 의 한 도메인(33 파일 / 4,112 라인)을 대상으로 측정했다.

- **산출**: 7분 / 922 라인 5파일 — 외부화 효율 22.4%, `file:line` 인용 217개 중 샘플 10건 전수 정확
- **feature spec 작성 3 시나리오**: 단순·중간 난이도는 부분 충족(백엔드 변경 지점·다중 service 분리 패턴 정확 캡처), 복잡 시나리오는 **외부 도메인 산출물 부재 시 막힘**
- **결론** — 단일 도메인 외부화는 충족, cross-domain 이 진짜 gap. 이 발견이 v0.3.0 milestone 재구성(cross-domain 처리 가이드 · MANIFEST 외부 도메인 섹션 · feature spec Open Questions 템플릿)의 근거가 됐다.
