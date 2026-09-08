# 경로 트리거 도메인 규칙 주입 — 검토·적용 플랜 (#30 C1)

- 작성: 2026-09-08 · 브랜치 `claude/dp-skills-context-search-enhance-qp02xo`
- 입력: 작업 지시 "경로 기반 동적 도메인 규칙 주입(Conditional Rule Injection)" — dp-skills 기준 `tools/match-context-rules.py` 신규 · `hooks/coding-rule-guard.sh` 본문 주입 고도화 · 테스트 2종. **파트 1 의 호출 인터페이스 1줄까지만 도착**(출력 형식·매칭 규칙·훅 통합·테스트 항목 미도착 — 그 부분은 검토 불가, 도착 시 § 2 표와 대조)
- 대상: pilot (`pilot/hooks/coding-rules.sh` · `pilot/skills/learn/SKILL.md` · `pilot/tools/doctor/integrity.py`). 지시서의 `workspace/{TEAM}/context` · `--team` 은 pilot 확정 결정(HANDOFF 2 — TEAM 레이어 없음)과 달라 `workspace/context` 로 읽는다
- 설계 SSOT: `workspace/projects/build-plugin/features/30-path-triggered-context.md` (§ 요구사항 C1/C2 · 비즈니스 규칙 "포인터만" · 선행 검증 절차) · `29-frontmatter-manifest.md` (`sources` 스키마) · `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-C · §0.4 불변 원칙
- 상태: **플랜 작성 완료 · 적용 전 (critic 검토 대기)**

## 0. 한 줄 결론

지시서의 목적("이 파일을 편집할 때 이 파일의 도메인 규칙이 따라오게")은 feature #30 이 이미 설계했고, 오늘 실측으로 **C1(`.claude/rules/*.md` `paths:` 조건부 규칙)이 메인·서브에이전트 모두, git 무시 여부와 무관하게 발화**함을 확인했다. 따라서 런타임 매처 CLI 와 훅 변경 없이 **생성기(`/pilot:learn`) + 점검기(`/pilot:doctor`)** 만으로 구현한다. 주입 내용은 #30 대로 **포인터만**(본문 복사 없음) — 본문은 이미 배선된 3단계(`--format manifest` → 선별 → `select:… --inject`)로 요청 시 가져온다.

## 1. 실측 기록 (2026-09-08, Claude Code 원격 세션 · 프로브는 실측 후 제거, 트리 clean)

| 실험 | 절차 | 결과 |
|---|---|---|
| C1 메인 에이전트 | `.claude/rules/zz-c1-probe.md` (`paths: pilot/tools/orchestrate-load.py`, 마커 QX7) 생성 → 메인 세션이 그 파일을 Read | Read 결과 직후 `Contents of …/.claude/rules/zz-c1-probe.md:` 블록으로 마커 문장 주입 |
| C1 서브에이전트 | general-purpose 서브에이전트가 같은 파일 1~10행만 Read(다른 파일 접근 금지 지시) | 마커 원문을 보고, 읽은 파일 1개뿐 → 서브에이전트에서도 주입 (#30 Open Q (c) 해소) |
| git 무시 | `.git/info/exclude` 에 `.claude/` 추가(로컬) + 마커 QX8 규칙(`paths: pilot/tools/docs_build.py`) → Read | 동일 주입 → **git 무시 여부는 로드에 영향 없음** (#30 예외 케이스 "gitignore 되면 로드 안 함 → doctor WARN" 은 이 하네스에서 성립하지 않는다) |
| 훅 사양 (공식 문서, 별도 에이전트) | hooks-guide · memory 문서 | PreToolUse·PostToolUse 모두 `hookSpecificOutput.additionalContext` 지원 · command 훅 timeout 기본 10분, 권고 "가능하면 1초 미만" · `paths:` 규칙은 "매칭 파일을 읽을 때" 로드(매 도구 호출 아님) · glob 은 gitignore 스타일 |
| 기존 역방향 질의 | `context-search.py "pilot/tools/orchestrate-load.py" --format manifest --limit 6` | 89ms · 상위 2건이 해당 소스를 다루는 섹션 · 경로 세그먼트 토큰(`pilot`·`tools`)으로 무관 섹션 4건이 34점 — 훅 용도엔 원 경로 매칭 필터 필요 |
| 현행 훅 | `coding-rules.sh` (PostToolUse `Edit\|Write`) | 61ms(python 2회 기동 포함) · 세션당 1회 포인터 · 테스트 없음 |
| 코퍼스 실태 | `workspace/context/rules/` · `sources:` | 디렉토리 없음 · `sources` 0건 (#29 미구현, rules 는 사용자 layer) |

## 2. 지시서 대비 판정 (사용자 확인으로 뒤집을 수 있음)

| 지시서 항목 | 판정 | 근거 |
|---|---|---|
| 신규 `tools/match-context-rules.py` (경로 → 규칙 고속 매처) | **만들지 않는다** | 매칭·주입은 하네스 네이티브(C1)가 맡는다 — 실측 발화. 만들면 하네스 기능의 재구현이자 파서·glob·섹션 분할의 세 번째 복제본 |
| `coding-rule-guard.sh` 본문 주입 고도화 | **`coding-rules.sh` 무변경** — 회귀 테스트만 신설 | #30 "포인터만 · 총 500자 · 같은 턴 같은 도메인 1회", 계획서 §0.4 "색인은 항상, 본문은 요청 시". 매 Edit 4,000B 는 세션 1회 마커로 막아 둔 누적을 되살린다. C1 은 규칙 파일당 세션 1회 로드라 dedup 이 하네스에 내장 |
| `--max-bytes 4000` 본문 반환 | 포인터 ≤8줄 · ≤500자 | 본문은 3단계 프로토콜로 요청 시 |
| `sources` glob 매칭 | `paths:` = 도메인 문서 `sources` 합집합, 부재 시 인용 경로 접두 추정(+표기) | #29 미구현 · `rules/`·`scope/` 는 frontmatter 비강제. glob 의미는 gitignore(하네스·`_glob_regex` 와 동일) |
| `workspace/{TEAM}/context` · `--team` | 없음 | pilot 은 TEAM 레이어 없음. dp-skills 분기면 경로 치환 외 인자 설계 필요 |
| PreToolUse "guard" 에 주입 | 하지 않음 | 기능상 가능(문서)하나 #30 "차단 훅과 컨텍스트 훅 분리". pilot 의 컨텍스트 훅은 PostToolUse `coding-rules.sh` |
| `tests/hooks/*.sh` | `pilot/tests/tools/test_*.py` unittest + subprocess | 저장소 규약(`test_scope_guard.py` 선례) |

## 3. 설계

### 3.1 산출물 — `.claude/rules/pilot-{domain}.md` (저장소 루트, `workspace/` 와 같은 층)

```markdown
---
paths:
  - app/services/wms/**
  - app/models/wms/**
---
<!-- managed by /pilot:learn — 수동 편집 금지. 재생성: /pilot:learn {진입점} · 점검: /pilot:doctor -->
이 경로는 `wms` 도메인이다. 수정 전 확인:
- 진입: workspace/context/wms/index.md
- 규칙: workspace/context/rules/wms.md
- 경계: workspace/context/boundaries/wms--schoice.md
- 상세 조회: python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py "<키워드>" --scope wms --format manifest --limit 8
```

- **캡**: `paths` ≤ 8 globs(초과 시 공통 상위 디렉토리로 접기) · 포인터 3~8줄 · 본문(frontmatter 제외) ≤ 500자 · 관리 마커 1줄. 지식 본문 복사 없음. 초과 항목은 "그 외 N개 — index 참조".
- **포인터 선정 순서**: 진입 index 1 → `rules/{domain}.md` 존재 시 1 → frontmatter `type` 이 rules·services·enums 인 본문 ≤ 2(frontmatter 없으면 파일명 규약 `rules.md`·`services.md`·`enums.md`) → `boundaries/{domain}--*` ≤ 2 → context-search 1줄(3단계 프로토콜 진입).
- **다중 도메인**: 하네스가 매칭되는 규칙 파일을 모두 로드하므로 런타임 상한은 둘 수 없다 — 파일당 500자 캡이 총량 상한(3도메인 ≈ 1.5K). #30 의 "최대 2 도메인 + 그 외 N" 은 C2 전용 규칙이라 폐기.
- **발화 조건의 한계**: 규칙은 매칭 파일을 **읽을 때** 로드된다. 새 파일 `Write` 만으로는 발화하지 않을 수 있다 — 그 틈은 현행 `coding-rules.sh`(세션 1회 포인터)가 메운다. 두 장치는 중복이 아니라 보완이며, 문서에 그렇게 적는다.

### 3.2 `paths` 도출 (결정적 · 읽기 전용)

1. 도메인 파일 집합 = MANIFEST 진입 파일 + `{domain}/**/*.md` + `boundaries/{domain}--*` — `context-search.collect_files(scope)` 재사용.
2. `sources` 합집합 — `context-search.parse_frontmatter` 재사용. 정규화: 끝 `/` → `/**`, 중복 제거, 정렬(결정성).
3. 0건이면 **인용 경로 추정**: 파일 본문 인용(`extract_citations`) 중 workspace 내부 인용 제외 → 디렉토리별 파일 수 집계 → 파일 ≥ 2 인 디렉토리를 `dir/**` 로, 최대 8개, 초과 시 공통 상위로 접기. 규칙 파일에 `<!-- paths: 인용 경로 추정 (sources frontmatter 없음) -->` 표기 + learn INFO.
4. 둘 다 0건 → 규칙 파일 생성 skip + INFO("인용 0건 — `sources` 기입 또는 재학습").

### 3.3 구현 위치

- **신규 `pilot/tools/rules-pointer.py`** (표준 라이브러리 · `context-search.py` 를 importlib 지연 로드 — confluence 선례 D5):
  - `build_rules_file(workspace: Path, domain: str, plugin_root: str) -> tuple[str | None, list[str]]` 순수 함수(내용, INFO). 도메인 미등록 → `SearchError` 류 exit 2.
  - CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/rules-pointer.py --domain D [--workspace workspace] [--write | --check] [--format md|json]`
    - `--write`: `.claude/rules/pilot-{D}.md` 생성/갱신. **관리 마커가 있는 파일만 덮어쓴다**, 마커 없으면 skip + INFO(사용자 관리 파일), 내용 동일이면 무변경(mtime 보존).
    - `--check`: 디스크 파일 vs 재생성 결과 diff → 일치 0 / 불일치 1 + 사유(doctor 가 같은 함수를 import 해 호출 — 판정 1벌 원칙, #28 선례).
    - 기본(플래그 없음): 내용을 stdout 으로 미리보기.
  - 지식 파일(`workspace/context/`)은 읽기만 한다. 결정적: 같은 코퍼스 → 같은 파일.
- **`pilot/skills/learn/SKILL.md` Phase 5** 에 스텝 추가: MANIFEST 갱신·doctor 직전에 `rules-pointer.py --domain {domain} --write` 실행, INFO 를 사용자 보고에 포함. Boundary 모드(`--boundary B --from A`)는 A 도메인 규칙 파일을 재생성(경계 포인터 갱신). Abort cleanup 계약: 규칙 파일 Write 는 Phase 5 batch 안에서.
- **`pilot/skills/learn/references/heuristics.md`**: "규칙 포인터 선정" 절(§3.1 순서·캡).
- **`pilot/tools/doctor/integrity.py` `check_workspace`**: `.claude/rules/pilot-*.md` 스캔 — (a) 파일명의 도메인이 MANIFEST 에 없으면 WARN stale(삭제 제안, `--fix` 는 제안만) (b) 포인터 경로 부재 WARN (c) `--check` 불일치 INFO "재생성 권장" (d) 마커 없는 파일 INFO(사용자 관리). **gitignore WARN 은 두지 않는다**(실측). `.claude/rules` 디렉토리 부재는 무음.
- **`pilot/hooks/coding-rules.sh`**: 무변경. 문서 주석에 C1 과의 역할 분담 1줄.
- **문서**: `pilot/docs/explanation/workspace-layout.md` 파생물 행(`.claude/rules/pilot-*.md`) · `features/30-path-triggered-context.md` § 실측 기록 기입 + C1 확정 · `pilot/docs/release-notes.md` 미배포 절 항목 · wrapper-protocol 은 무변경(규칙은 하네스가 넣는다).
- **init 템플릿**: 변경 없음(규칙 파일은 learn 산출).

### 3.4 변경 파일

- 신규: `pilot/tools/rules-pointer.py` · `pilot/tests/tools/test_rules_pointer.py` · `pilot/tests/tools/test_coding_rules.py` · `pilot/tests/tools/test_doctor_rules_pointer.py`
- 변경: `pilot/skills/learn/SKILL.md` (Phase 5 스텝 1개) · `pilot/skills/learn/references/heuristics.md` · `pilot/tools/doctor/integrity.py` (`check_workspace`) · `pilot/hooks/coding-rules.sh` (주석 1줄) · `pilot/docs/explanation/workspace-layout.md` · `pilot/docs/release-notes.md` · `workspace/projects/build-plugin/features/30-path-triggered-context.md` (실측 기록 절)
- 불변: `pilot/hooks/hooks.json` · `context-search.py`(재사용만) · `workspace/context/**`(읽기 전용) · wrapper-protocol

### 3.5 구현 순서

**Phase 0 — 현행 고정** (변경 0): `test_coding_rules.py` 신설(no-op 조건 4종: 프로젝트 밖·`workspace/` 내부·`source_root` 밖·규칙 없음 / 세션 1회 마커 / JSON `hookSpecificOutput` 형식) · #30 § 실측 기록 기입(§ 1 표).

**Phase 1 — 생성기**: `rules-pointer.py` + `test_rules_pointer.py`(§ 3.6). 라이브 `--domain pilot` 미리보기로 캡·포인터 확인(파일은 아직 쓰지 않음).

**Phase 2 — 배선**: learn Phase 5 스텝 · heuristics 절 · doctor 검사 4종 + 테스트 · 문서.

**Phase 3 — dogfooding**: `rules-pointer.py --domain pilot --write` 실제 실행 → 생성 파일로 발화 재확인(메인 + 서브에이전트, § 1 절차) → doctor 클린 → 결과를 #30 실측 기록에 추가. 커밋 여부는 § 3.9-1.

### 3.6 테스트 목록

- `test_coding_rules.py`: 위 Phase 0 항목 6건.
- `test_rules_pointer.py`: `sources` 합집합·정규화·정렬 · 인용 추정(내부 인용 제외·디렉토리 빈도·8개 캡·공통 상위 접기·표기) · 둘 다 0건 skip · 포인터 순서·캡(8줄·500자·그 외 N) · 템플릿 정확(마커·`${CLAUDE_PLUGIN_ROOT}` 리터럴) · `--write` 마커 보존(마커 없는 파일 무변경 + INFO) · 내용 동일 시 무변경 · `--check` 0/1 · 결정성(2회 생성 동일) · 도메인 미등록 exit 2 · glob 의미 = `_glob_regex`(대표 경로 3건 매칭 검증).
- `test_doctor_rules_pointer.py`: stale WARN · 포인터 부재 WARN · 불일치 INFO · 마커 없음 INFO · 디렉토리 부재 무음.
- 골든: `pilot/tests/fixtures/context-search/workspace`(MANIFEST + pilot 도메인)로 `pilot` 규칙 파일 기대값 fixture 1개(인용 추정 경로 — `pilot/skills/**` 류) 동등성.

### 3.7 게이트

| G | 기준 |
|---|---|
| G1 | `python3 -m unittest discover -s pilot/tests/tools` 전부 통과. 신규 ≥ 25건 |
| G2 | 결정성 — 라이브 `--domain pilot` 2회 생성 diff 0 · 지식 파일 무수정(`git status -- workspace/context` 변화 0) |
| G3 | 생성 시간 라이브 코퍼스 < 200ms(learn 1회당 1회 실행이라 훅 예산과 무관) |
| G4 | 발화 실측 — 생성 파일로 메인·서브에이전트 주입 확인(§ 1 절차 재실행), 주입 텍스트 ≤ 500자 |
| G5 | `docs_build.py --check` 통과 · doctor 클린(기존 `STATE.md` 부재 ERROR 는 로컬 파일, `.gitignore` 대상 — 제외) |
| G6 | 후속 feature 사이클에서 generator 가 `pilot/skills/**` 수정 시 `pilot` 규칙이 나타난 기록(#30 검증 기준) |

### 3.8 제외

- 런타임 매처 CLI(`match-context-rules.py`) · `coding-rules.sh` 본문 주입 · PreToolUse 주입 · `--team`.
- `.claude/rules` gitignore WARN(실측상 무관).
- 역방향 경로 질의의 세그먼트 노이즈 필터(`matched` 에 원 경로 있는 결과만) — 유용하나 본 feature 범위 밖, 별도 항목으로.
- C2 훅(`context-pointer.sh`) — C1 발화 실측으로 폐기. 하네스가 C1 을 지원하지 않는 환경이 확인되면 그때 재개.

### 3.9 사용자 결정 필요

1. `.claude/rules/pilot-*.md` **커밋 vs 로컬 전용** — 로드는 무관(실측). 팀 공유·리뷰 가시성엔 커밋이 유리하고 재생성 drift 는 doctor `--check` 가 잡는다. 제안: 커밋(파생물이지만 안정적).
2. 인용 경로 추정 glob 채택 여부 — #29 머지 전까지 유일한 `paths` 출처. 오탐(테스트·문서 경로 인용)을 `source_root` 접두로 제한할지.
3. 캡 값(500자·8줄·8 globs) 과 포인터 순서.
4. dp-skills 지시서의 잘린 나머지(매처 출력 규격·훅 통합·테스트)가 도착하면 § 2 표와 대조 후 판정 갱신.
