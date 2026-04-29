# HANDOFF — 리팩토링 진행 상황

다른 환경에서 작업을 이어받기 위한 인계 문서. 사내 `dp-skills` 플러그인을 범용 `pilot` 플러그인으로 리팩토링 중.

## 새 환경 셋업

```bash
# 1. 클론
git clone https://github.com/radiostart/claude-plugins.git
cd claude-plugins

# 2. 테스트 환경 확인 (Python 3.11+ 권장, pytest 필요)
pytest pilot/tests/ -q --ignore=pilot/tests/tools/test_confluence.py
# → 93 passed 가 나오면 정상

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
abed86e refactor: scope/rules 를 플러그인 컨트랙트에서 권장 컨벤션으로 demote
d10799d feat: /pilot:learn 스킬 — 소스코드에서 도메인 컨텍스트 부트스트랩
de499a1 docs: tdd_batch 미구현 contract 제거
865f6d6 refactor: 프로젝트쪽 agents/ → prompts/ rename
c949152 refactor: 감사 결과 반영 — 버그·과적합·dead reference 정리
af9d65b refactor: 사내 특화 항목 제거 → 범용화
8ee766e chore: 잔존 정리 — fixture · 사내 마커 · 팀 표현
2f228c8 chore: ai-review 스킬 제거
c3df02c init: pilot 플러그인 + claude-plugins 마켓플레이스 셋업
```

테스트 93/93 통과. clean working tree.

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

## 보류·미정 사항

- **영어 README** — 사용자가 "최종 완성 후 변경 예정" 으로 보류
- **plugin.json version 0.1.0** — 별도 릴리스 시점에 bump
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

언급되었으나 미진행:

- 한국어 anchor lock 제거 (`## 언어·도구 기본값`·`## 설정` regex anchor 를 HTML comment anchor 로) — 비한국어 fork 대비
- doctor `--diagnose` 패턴 추가 검증
- 영어 README 작성 (보류)
- `/pilot:learn` 실제 codebase 에 dry-run 검증 (실전 휴리스틱 정확도)

## 평가 보고서 (참고)

- 1차 감사 (사내 특화 항목): commit `c949152` 메시지
- 2차 감사 (전체 평가): chat 로그 (커밋 메시지에 핵심 반영됨)
- `/pilot:learn` 평가: commit `d10799d` 메시지에 핵심 반영
