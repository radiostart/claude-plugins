# HANDOFF — 리팩토링 진행 상황

다른 환경에서 작업을 이어받기 위한 인계 문서. 사내 `dp-skills` 플러그인을 범용 `pilot` 플러그인으로 리팩토링 중.

## 새 환경 셋업

```bash
# 1. 클론
git clone https://github.com/radiostart/claude-plugins.git
cd claude-plugins

# 2. 테스트 환경 확인 (Python 3.11+ 권장, pytest 필요)
pytest pilot/tests/ -q --ignore=pilot/tests/tools/test_confluence.py
# → 107 passed 가 나오면 정상 (build-plugin v1 으로 +14: integrity 7 / migration 7)

# 3. (선택) Confluence 사용 시 의존성
pip install requests beautifulsoup4

# 4. (선택) Confluence 사용 시 .env (gitignored — 새 환경에서 직접 작성)
cat > .env <<'EOF'
CONFLUENCE_HOST=https://yourorg.atlassian.net/wiki
CONFLUENCE_EMAIL=user@example.com
CONFLUENCE_TOKEN=your-api-token
EOF
```

## 현재 상태 (origin/main)

```
f72ecd1 chore(workspace): build-plugin 프로젝트 메타 + workspace/context 산출물
8fc664c chore(gitignore): .slack.env + .claude/worktrees/ 보호 패턴 추가
6d1f2e0 docs(readme): config.md 언어 패턴 example block (#01 짝)
164fda3 feat(doctor): config 정합성 검증 + v0.1→v0.2 자동 마이그레이션 (#04 + #05)
b40bd3d feat(project): project.md H3 동적 생성 + SSOT 분리 (#03)
6ce4e6d feat(analyze): scope 카테고리 외부화 + create-feature 인용 동기화 (#02)
fbc69a6 feat(learn): 언어 패턴 외부화 + default 표 폐지 (#01, D10)
bc1ce77 test(fixtures): v0.1.0 회귀 골든 픽스처 인프라 (#00 0a)
917fa7b require gstack for AI-assisted work
2d15506 docs: HANDOFF.md — 다른 환경 인계용
```

build-plugin 프로젝트 v1 작업 (pilot 플러그인 범용화) 5/6 features 완료.
테스트 107/107 통과 (#04 +7, #05 +7). clean working tree.

## v1 (build-plugin 프로젝트) 완료 사항

`workspace/projects/build-plugin/` 에서 진행. office-hours + plan-eng-review
설계 결과:

- **#01 learn 언어 패턴 외부화** (D10): SKILL.md default 5 언어 표 폐지,
  workspace/context/config.md 의 `## learn 언어 패턴` 두 표 (의존성 추적
  + 역할 분류 long-form) 가 SSOT
- **#02 analyze scope 카테고리 외부화**: 5-2 단계의 scope 분류를
  `## scope 카테고리` 표로 외부화 (3 컬럼 + `## ` prefix + H3 화이트리스트)
- **#03 project.md H3 동적 생성 + SSOT 분리**: H3 헤더 = `/pilot:project`
  1 회 생성, 표 본문 = `/pilot:analyze` / `/pilot:create-feature` 매번 갱신
- **#04 doctor config 정합성 검증**: `check_workspace_config_sections` 신설,
  컬럼 수·헤더·prefix·H3 화이트리스트 검증 + Result.INFO 레벨
- **#05 v0.1→v0.2 자동 마이그레이션**: D10 default 폐지의 backward-compat
  보장. `migrate_v0_1_to_v0_2` 가 `/pilot:doctor --fix` 시 v0.1.0 사용자에게
  default 표 자동 주입 prompt (opt-in/out/postpone 3 분기)
- **#00 0a 회귀 픽스처 인프라**: `pilot/tests/fixtures/v0.1.0-baseline/`
  의 config 검증 6 케이스 + diff.sh 골격

**미완**: #00 0b (`_input/` + `learn/expected/` + 등) — Open Q #1 결정 후 PR.

## V1-Full 충실성 검증 (2026-04-30)

`/pilot:learn` stated purpose 가 진짜 큰 레거시에서 작동하는지 검증. 사용자 보유 nimda Rails monolith (126K Ruby + JSX/TS) 의 wms 도메인 dogfooding.

### 검증 데이터

- **wms 도메인 size**: 33 Ruby files / 4,112 lines (services 16 + models 10 + controllers 7)
- **소요 시간**: 7 분 (subagent simulation)
- **산출 size**: 922 lines / 5 files (`index.md` + `inventory.md` + `services.md` + `models.md` + `routes.md`)
- **외부화 효율**: 22.4% (4,112 → 922)
- **file:line 인용**: 217 개
- **인용 정확성**: 10/10 sample 정확 (cat-n 검증, NS #5 hotfix #1 교훈 적용)
- **추출 비즈니스 규칙**: 60+ (상태 전환, 검증 룰, 외부 통합, 권한, 다중 DB 패턴)

### Step D 3 시나리오 결과 — feature spec 작성 시도 (산출물만으로)

- **A (간단)** damage_reported PENDING_TYPE 추가 → 부분 충족 (백엔드 OK, 프론트엔드/locale 부족). 22 인용 활용
- **B (중간)** DHL 배송사 추가 → 부분 충족 (변경 지점/패턴 OK, DHL API spec 외부). 33 인용 활용. **다중 service 분리 패턴 (cyber_bongo_register/invoice/cancel) 정확 캡처 입증**
- **C (복잡)** 박스 단위 부분 취소 → 부분 ~40% (wms 안 OK, schoice 외부 도메인 부재 시 막힘). **cross-domain 한계 명확히 입증**

### stated purpose 충족 평가

- 도메인 지식 외부화 (single domain): **충족** (22.4% 압축 + 100% 인용 정확)
- AI 효율 활용: **충족** (7 분 산출, 단일 turn spec 작성)
- 큰 레거시 (single domain): **충족**
- 큰 레거시 (cross-domain): **부분** — schoice 같은 외부 도메인 부재 시 막힘 = pilot 의 진짜 gap

### V1 발견 → v0.3.0 milestone 재구성

V1 결과 토대로 v0.3.0 features priority 재조정:

- **HIGH (V1 발견)**:
  - #09 cross-domain 처리 가이드 — 외부 도메인 의존성 detect + 가이드
  - #10 MANIFEST.md 외부 도메인 섹션 자동 추가
  - #11 feature spec Open Questions 템플릿 (4 카테고리)
- **MED**: #12 cross-domain transaction 패턴 가이드
- **LOW** (기존, 표층 fix): #06~#08 SKILL.md 모호함

## 확정된 아키텍처 결정

1. **마켓플레이스 구조** — `claude-plugins/` (root) + `pilot/` (플러그인 본체)
2. **워크스페이스 단일 구조** — TEAM 레이어 제거. `workspace/{STATE.md, context/, projects/, issues/}` 직접
3. **agents/ vs prompts/** — 플러그인은 `pilot/agents/` (subagent wrapper), 프로젝트는 `workspace/projects/{P}/prompts/` (컨텍스트 파일)
4. **MANIFEST 가 discovery contract** — `orchestrate-load.py` 가 `## 도메인 분류` 표 자동 파싱해 진입 파일 로드. 폴더 구조는 워크스페이스 자유.
5. **scope/rules** — 권장 컨벤션 (강제 아님). 플러그인은 MANIFEST 만 알고 폴더명 강제하지 않음.
6. **scope schema 지원** — wrapper 실행: v1.1·v1.2 / doctor 읽기: v1·v1.1·v1.2
7. **TDD batch granularity** — 현재는 feature 단위 (호출 1회 = 1 feature). step/all 모드는 별도 feature 로 미루어둠.
8. **`/pilot:learn`** — 소스코드에서 도메인 컨텍스트 자동 부트스트랩 (analyze 의 짝)
9. **언어 중립** — Ruby fallback 제거 (config.md 미정의 시 사용자 질의)
10. **D9 long-form 역할 분류** (build-plugin v1) — 역할 분류 표는 wide-form
   (역할 × 언어) 폐기, long-form 2 컬럼 (`| 역할 | 식별 패턴 |`) 사용.
   "(역할, 언어) 매트릭스 = (역할, 프레임워크) 의 잘못된 압축" 통찰 반영.
11. **D10 default 표 폐지** (build-plugin v1) — pilot 은 특정 언어 대상이
   아니므로 SKILL.md 의 default enumeration 자체가 모순. config 가 1 급
   시민, SKILL.md 는 메커니즘만. README 에 v0.1.0 default example block 게시.
12. **M1 자동 마이그레이션** (build-plugin v1) — D10 backward-compat 메커니즘.
   `pilot/tools/doctor/integrity.py:migrate_v0_1_to_v0_2` 가 v0.1.0 →
   v0.2.0 업그레이드 사용자에게 default 표 자동 주입 prompt
   (opt-in/out/postpone). `.agent-state.yml.migration_v0_2_0` 에 결정 기록.
13. **A2 runtime fallback** (build-plugin v1) — `/pilot:learn`·`/pilot:analyze`
   등 runtime 은 잘못된 config 행을 만나도 abort 하지 않고 default fallback
   + stderr WARN 1 줄. doctor 가 별도 실행될 때만 ERROR 보고. 1 행 오류로
   전체 워크플로 중단 vs default fallback 안전성 — 후자.

## 보류·미정 사항

- **영어 README** — 사용자가 "최종 완성 후 변경 예정" 으로 보류
- **plugin.json version 0.1.0 → 0.2.0** — build-plugin v1 코드 변경 완료.
  bump 필요. 현재 v0.1.0 이라 #05 마이그레이션 함수가 조기 반환 상태
  (활성화 트리거).
- **Open Q #1 (#00 0b 입력 언어)** — 회귀 픽스처의 `_input/` 언어 결정 후
  `_input/`·`learn/expected/`·`project/expected/`·`analyze/expected/` 별도 PR.
- **5 번 회귀 검증** — `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` 로 v1
  출력 = v0.1.0 baseline 동일 확인 (0b 완료 시점까지 보류).
- **GitHub Release v0.2.0** — version bump + 0b 회귀 검증 후 발행.
- **Confluence 호스트** — `CONFLUENCE_HOST` 환경변수 (.env 또는 export)
- **자동 메모리** — 다른 환경에선 새로 축적 (per-project-dir, 이전 환경 메모리 transfer 안 됨)

## 디렉토리 구조

```
claude-plugins/                  ← 마켓플레이스 root (= 이 레포)
├── .claude-plugin/
│   └── marketplace.json         ← radiostart/claude-plugins, plugins=[pilot]
├── .gitignore
├── .markdownlint.json
├── HANDOFF.md                   ← 본 파일
└── pilot/                       ← 플러그인 본체
    ├── .claude-plugin/
    │   ├── plugin.json
    │   └── PLUGIN_SCHEMA_NOTES.md
    ├── README.md
    ├── agents/                  ← Claude Code subagent wrapper (planner/generator/evaluator)
    ├── hooks/                   ← commit-format · scope-guard · slack-notify
    ├── skills/                  ← 14개 스킬 (init·project·issue·confl·analyze·learn·...)
    ├── tools/                   ← orchestrate-load · doctor · confluence · slack-notify · ...
    └── tests/tools/             ← pytest 단위 테스트
```

## 자주 쓰는 커맨드

```bash
# 테스트
pytest pilot/tests/ -q --ignore=pilot/tests/tools/test_confluence.py

# orchestrate-load smoke
mkdir -p /tmp/t/workspace/{context,projects/X}
cat > /tmp/t/workspace/STATE.md <<'EOF'
| 모드 | 이름 | 상태 |
| --- | --- | --- |
| project | X | 진행중 |
EOF
cat > /tmp/t/workspace/projects/X/.agent-state.yml <<'EOF'
schema: v1.2
analyzed: false
tdd: false
domain: null
EOF
cd /tmp/t && python3 /Users/jay-p/Projects/pilot/pilot/tools/orchestrate-load.py --phase planner --workspace workspace

# doctor smoke (위 workspace 사용)
cd /tmp/t && python3 /Users/jay-p/Projects/pilot/pilot/tools/doctor.py workspace

# 잔존 사내 식별자 sweep (정상이면 0건)
grep -rn 'dp-skills\|deali-skills\|dealicious\|workspace/{TEAM}\|workspace/_common\|KNOWN_DOMAINS\|tdd_batch' pilot/ --include="*.md" --include="*.py" --include="*.sh" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.template" 2>/dev/null
```

## 다음 작업 후보

직전 작업 (build-plugin v1) 마무리:

1. `pilot/.claude-plugin/plugin.json` version bump 0.1.0 → 0.2.0 — M1 활성화
2. Open Q #1 결정 후 #00 0b PR (회귀 픽스처 입력·expected)
3. 5번 회귀 검증 (`pilot/tests/fixtures/v0.1.0-baseline/diff.sh`)
4. GitHub Release v0.2.0

언급되었으나 미진행 (별개 작업):

- 한국어 anchor lock 제거 (`## 언어·도구 기본값`·`## 설정` regex anchor 를 HTML comment anchor 로) — 비한국어 fork 대비
- doctor `--diagnose` 패턴 추가 검증
- 영어 README 작성 (보류)
- `/pilot:learn` 실제 codebase 에 dry-run 검증 (실전 휴리스틱 정확도)

## 평가 보고서 (참고)

- 1차 감사 (사내 특화 항목): commit `c949152` 메시지
- 2차 감사 (전체 평가): chat 로그 (커밋 메시지에 핵심 반영됨)
- `/pilot:learn` 평가: commit `d10799d` 메시지에 핵심 반영
