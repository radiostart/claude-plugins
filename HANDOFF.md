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

**v0.14.0** (tag `pilot-v0.14.0`) — 스킬 17 · 에이전트 5 · 훅 6 · 테스트 345.

사내 원본 플러그인에서 파생된 범용판이며, **범용화 리팩터는 완료**됐다 (사내 식별자 sweep 0건). 현재는 원본의 미포팅 기능을 선별 흡수하며 자체 dogfooding(`workspace/projects/build-plugin/`)으로 개발한다 — feature 27건 중 26건 완료, 미완 1건은 `#22 context 드리프트 재학습`.

릴리스 이력은 [GitHub Releases](https://github.com/radiostart/claude-plugins/releases)가 SSOT. 직전 릴리스 v0.14.0 은 issue 단건 사이클+slug · Open Questions fail-closed 게이트 · knowledge-sync · `pilot-init`/`pilot-review` 개명을 담았다.

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
    ├── skills/                  ← 스킬 17종 + context/ (공유 계약·라이프사이클 문서)
    ├── hooks/                   ← commit-format · scope-guard · protect-managed · coding-rules · slack-notify · session-context
    ├── tools/                   ← orchestrate-load · doctor · plan-validate · auto_pilot · docs_build · confluence · slack-notify · regen-verify · release.sh
    ├── docs/                    ← 매뉴얼 소스 (mkdocs). reference/ 하위 생성물은 gitignored
    ├── examples/                ← 언어별 코드리뷰 룰 예시
    └── tests/tools/             ← 단위 테스트 15 파일
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

# 릴리스 (main clean + 버전 표기 3곳 동기 후)
pilot/tools/release.sh
```

> `orchestrate-load.py` 는 워크스페이스를 인자로 받는다: `python3 pilot/tools/orchestrate-load.py --phase planner --workspace workspace`

## 다음 작업 후보

- **`#22` context 드리프트 재학습** — `workspace/context/pilot/` 이 삭제된 스크립트 3종(`memory-hint`·`init_detect`·`diagnose.py`)과 개명 전 스킬명, issue 경량 모드를 서술 중. `/pilot:learn ./pilot/skills` 재실행으로 일괄 해소한다 (**직접 Edit 금지** — drift-protocol § A). doctor 가 `spec.md` mtime drift 로 이미 감지 중.
- **사내 원본 미포팅 백로그** — greenfield 즉석 등재 · HOTL 다중 순회 · AskUserQuestion 기반 사전 인터뷰 (pilot 의 OQ 소비형 인터뷰와는 다른 설계라 통째 이식 금지).
- **신규 기능 사용자 문서** — knowledge-sync(`metrics.domain_impact` 승인 블록)와 Open Questions fail-closed 게이트는 랜딩 highlights·생성 reference 에만 있고 how-to 가 없다.
- **`orchestrate-load` placeholder leak** — `parse_lang_tools` 가 config 표의 예시 표기를 실값으로 반환 (doctor 의 구조 기반 판정을 재사용해 해소 가능).
- **Slack `pr` 이벤트가 기본값에서 누락** — `tools/slack-notify.py` 는 `complete`·`approval`·`pr` 3종을 지원하고 `/pilot:pr` 이 실제로 `pr` 을 발송하는데, `/pilot:slack` 활성화 절차가 제안하는 기본값은 `complete,approval` 이라 스킬로 설정한 사용자는 PR 알림을 받지 못한다. 문서에는 경고를 달았으나(how-to § 지원 이벤트) 기본값 자체를 바꿀지는 제품 판단 필요.
- **영어 README** — 보류 (사용자 판단).

## 이력 — v1 dogfooding 검증 (2026-04-30)

`/pilot:learn` 이 실제 대형 레거시에서 작동하는지 검증한 기록. 126K 라인 Ruby monolith 의 한 도메인(33 파일 / 4,112 라인)을 대상으로 측정했다.

- **산출**: 7분 / 922 라인 5파일 — 외부화 효율 22.4%, `file:line` 인용 217개 중 샘플 10건 전수 정확
- **feature spec 작성 3 시나리오**: 단순·중간 난이도는 부분 충족(백엔드 변경 지점·다중 service 분리 패턴 정확 캡처), 복잡 시나리오는 **외부 도메인 산출물 부재 시 막힘**
- **결론** — 단일 도메인 외부화는 충족, cross-domain 이 진짜 gap. 이 발견이 v0.3.0 milestone 재구성(cross-domain 처리 가이드 · MANIFEST 외부 도메인 섹션 · feature spec Open Questions 템플릿)의 근거가 됐다.
