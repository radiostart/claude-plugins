# #13 부트스트랩 마법사 — `/pilot:init` 1.5 단계 신설 + 자동 감지 도구

> source: features/13-init-bootstrap-wizard.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도 세션)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (직전 turn 협상 결과 — Q1~Q7)

본 plan 은 사용자가 다음 7 건을 확정한 뒤 작성한다. generator 는 본 plan 만 보고 추가 질의 없이 구현 가능.

- **Q1 — scope 후보 "빈도 ≥ 1" (A 채택)**: spec line 24 의 "빈도 ≥ 2" 룰을 "빈도 ≥ 1 (= 존재 시)" 로 완화한다. fixture `_input/python-sample/` 의 `models/`·`services/` 가 각각 단일 폴더이지만 wizard 가 자동 매핑할 수 있어야 회귀 검증 시나리오 성립. 본 plan 작성과 함께 spec 본문 line 24 단어를 함께 교정 ("≥ 2" → "≥ 1") — "변경 파일" 의 "수정" 절에 명시.
- **Q2 — `.gitignore` 무시 + sane default 하드코딩 (A 채택)**: `.gitignore` 파싱 없이 `IGNORE_BASELINE` 상수만 적용. Python 표준 라이브러리만 사용, 의존성 0 원칙 엄수 (spec line 36 와 정합).
- **Q3 — `## 언어·도구 기본값` 의 `language` 키 자동 주입 안 함 (A)**: wizard 는 spec 명시 3곳 (`## learn 언어 패턴`, `## scope 카테고리`, `## Ignore`) 만 채운다. `## 언어·도구 기본값` 표는 사용자 수동 작성 영역으로 보존.
- **Q4 — 회귀 검증 첫 init 산출만 캡처 (A)**: idempotency 는 단위 테스트로 분리 (Q5 참조). 회귀 fixture 는 "빈 workspace → `/pilot:init` 첫 실행" 의 산출만 캡처한다.
- **Q5 — 단위 + 회귀 양쪽 (C)**: `pilot/tests/tools/test_init_detect.py` 신설 (unittest + tmp_path) + `wizard/expected/` 회귀 fixture 도 별도 추가. 양쪽 모두 작성.
- **Q6 — `--no-wizard` 토큰은 SKILL.md 자연어 분기 (A)**: slash command 라 argparse 없음. SKILL.md 본문에 "사용자 입력에 `--no-wizard` 포함 시 wizard step skip" 1 단락만 추가한다. 별도 파서 없음.
- **Q7 — version bump milestone 끝 일괄 (A)**: 본 PR 은 patch bump 안 함. v0.3.0 합본 PR 에서 일괄 처리.

## 범위 (포함/제외)

- **포함**:
  - `pilot/tools/init_detect.py` 신설 (3 함수 + `IGNORE_BASELINE` 상수, Python 표준 라이브러리만)
  - `pilot/tests/tools/test_init_detect.py` 신설 (단위 테스트 — 언어 감지 / scope 감지 / IGNORE 병합 / 샘플링 / 빈도 0 fallback / dedupe)
  - `pilot/skills/init/SKILL.md` 본문 갱신 (동작 1.5 단계 신설 + `--no-wizard` 자연어 분기 + 결과 출력 포맷 3 줄 추가)
  - `workspace/projects/build-plugin/features/13-init-bootstrap-wizard.md` 본문 line 24 patch (Q1 결정 반영)
  - `pilot/tests/fixtures/v0.1.0-baseline/wizard/expected/config.md` 회귀 fixture 캡처 (첫 init 산출 1 케이스)
  - `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` 의 `EXPECTED_SUBDIRS` 배열에 `"wizard/expected"` 1 줄 추가
- **제외**:
  - `--rewizard` v2 명령 (spec line 31, 본 milestone 외)
  - `## 언어·도구 기본값` 의 `language` 키 자동 주입 (Q3)
  - `--max-files` 사용자 CLI 인자 (spec line 35 의 max_files 는 함수 default `50000` 으로만 노출, slash command UI 미노출)
  - `plugin.json` patch bump (Q7 — v0.3.0 합본 PR 일괄)
  - `.gitignore` 동적 파싱 (Q2)
  - idempotency 회귀 fixture (Q4 — 단위 테스트만)
  - 모노레포 서브트리별 자동 안내 — spec line 36 의 INFO 1 줄만 출력하고 끝

## 변경 파일

### 신설

- [x] `pilot/tools/init_detect.py` — wizard 감지 로직. 함수 3 개 + 상수 1 개.
  - `IGNORE_BASELINE: list[str]` — `.git/`, `node_modules/`, `__pycache__/`, `vendor/`, `dist/`, `build/`, `.next/`, `target/`, `*.pyc`, `*.lock` (spec line 28).
  - `detect_languages(cwd: Path, max_files: int = 50000) -> list[str]` — 상위 3 개 확장자 → features/01 의 5 default 언어 (`ruby`/`python`/`typescript`/`go`/`java`) 매핑. 비매핑 확장자는 결과에서 skip + 호출자에게 INFO 메시지 전달 가능한 형태 (반환 tuple `(languages, info_messages)` 권장 — generator 가 SKILL.md 출력 단계에서 활용).
  - `detect_scope_candidates(cwd: Path) -> dict[str, str]` — depth ≤ 2 폴더명 빈도 ≥ 1 (Q1 적용) + 영문 소문자 → features/02 의 default 매핑 (`controllers`/`routes` → `Endpoints`, `models`/`entities` → `Models`, `services`/`workers`/`jobs` → `Services`) 적용. 매핑 안 되는 폴더는 결과 dict 미포함 (info 메시지로 별도 노출).
  - shebang `#!/usr/bin/env python3` + module docstring + `if __name__ == "__main__":` 가드 (doctor.py 컨벤션 참조).
  - 외부 의존성 0 — `pathlib` · `collections.Counter` · `os.walk` 만 사용 (Q2).
  - **확장자 매핑 (모듈 상수 `LANG_EXT_MAP`)**: `.rb` → `ruby`, `.py` → `python`, `.ts`/`.tsx` → `typescript`, `.go` → `go`, `.java` → `java` (features/01 line 16~20 매핑 + java 추가).
  - **scope 매핑 (모듈 상수 `SCOPE_FOLDER_MAP`)**: 위 9 폴더명 → 3 카테고리 (Endpoints/Models/Services).
- [x] `pilot/tests/tools/test_init_detect.py` — unittest 기반. 케이스 6 건:
  1. `test_detect_languages_python_only` — tmp_path 에 `.py` 5개 → `["python"]`.
  2. `test_detect_languages_top3_truncation` — `.py` 10개, `.ts` 8개, `.go` 5개, `.java` 3개 → `["python", "typescript", "go"]` (상위 3).
  3. `test_detect_languages_zero_match_returns_empty` — 매핑 안 되는 확장자만 → `[]` + info 메시지에 비매핑 확장자 명시.
  4. `test_detect_languages_respects_ignore_baseline` — `node_modules/` 하위 `.py` 100개는 빈도 집계 제외 확인.
  5. `test_detect_scope_candidates_single_folder` — `models/` 단일 존재 → `{"models": "Models"}` (Q1: 빈도 ≥ 1 확인).
  6. `test_detect_scope_candidates_unmapped_folder_excluded` — `lib/`, `utils/` 등은 결과 dict 미포함 + info 메시지에 노출.
  7. `test_detect_languages_sampling_max_files` — `max_files=10` 으로 잘라도 함수가 예외 없이 종료 + INFO 메시지 발생 (spec line 35).
  8. `test_ignore_baseline_constant_has_required_patterns` — `IGNORE_BASELINE` 에 spec line 28 의 10 패턴 전부 포함 확인.
- [x] `pilot/tests/fixtures/v0.1.0-baseline/wizard/expected/` — 회귀 fixture 디렉터리.
- [x] `pilot/tests/fixtures/v0.1.0-baseline/wizard/expected/config.md` — `/pilot:init` 첫 실행을 `_input/python-sample/` 에서 수행했을 때 wizard 가 채워준 `workspace/context/config.md` 산출. 다음을 포함:
  - `## learn 언어 패턴` — `python` default 1 행 주입 (python-sample 은 `.py` 만이라 상위 3 ↘ python 단일).
  - `## scope 카테고리` — `models` → Models, `services` → Services 2 행 주입 (Q1 결과: `_input/python-sample/{models,services}/` 단일 폴더라도 빈도 ≥ 1 로 매핑됨).
  - `## Ignore` — `IGNORE_BASELINE` 10 패턴 주입.
  - `## 언어·도구 기본값` 표는 spec 의 빈 스켈레톤 그대로 유지 (Q3).

### 수정

- [x] `pilot/skills/init/SKILL.md` — 본문 변경 3 군데:
  1. **`## 동작` 섹션에 `### 2. wizard 적용 (created 인 경우만)` 신설** (기존 `### 1. 스켈레톤 생성` 다음). 절차:
     - `config.md` 상태가 `created` 인 경우만 진입. `exists` 면 skip.
     - 사용자 입력에 `--no-wizard` 토큰 포함 시 skip (Q6 자연어 분기 — argparse 없음).
     - `${CLAUDE_PLUGIN_ROOT}/tools/init_detect.py` 의 3 함수를 import 또는 subprocess 로 호출하여 `(languages, scopes, ignore_patterns)` 추출.
     - 추출 결과를 `workspace/context/config.md` 의 3 섹션 (`## learn 언어 패턴`, `## scope 카테고리`, `## Ignore`) 표 본문에 주입. 기존 행이 있으면 dedupe 병합 (spec line 29).
     - 단계별 감지 0 건 → 해당 섹션은 features/01·02 의 default 표 사용 (spec line 21·26) + INFO 1 줄.
     - 어느 단계 실패해도 abort 금지 — 다른 단계는 계속 진행 (spec line 38, A2 fallback 정책 일관).
  2. **`## 결과 출력` 블록 본문에 3 줄 추가** (spec line 30):
     - `언어 감지: {N}개 자동 주입 ({언어목록})`
     - `scope 후보: {M}개 매핑 ({폴더목록})`
     - `Ignore baseline: {P}개 추가`
     - wizard skip 시 위 3 줄 대신 `wizard skipped (config.md exists 또는 --no-wizard)` 1 줄.
  3. **`## 참고` 섹션 마지막에 `--no-wizard` 한 단락 추가** (Q6):
     - "사용자 입력에 `--no-wizard` 토큰이 포함되어 있으면 wizard 단계를 건너뛴다. v0.2.x 이전 동작과 동일하게 빈 스켈레톤만 생성된다."
- [x] `workspace/projects/build-plugin/features/13-init-bootstrap-wizard.md` — line 24 단어 patch (Q1):
  - 변경 전: `빈도 ≥ 2 이고 영문 소문자 폴더명 → scope 후보.`
  - 변경 후: `빈도 ≥ 1 (= 존재) 이고 영문 소문자 폴더명 → scope 후보.`
  - 같은 줄의 default 매핑 (`controllers`/`routes` 등) 은 그대로 유지.
- [x] `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` — `EXPECTED_SUBDIRS` 배열에 `"wizard/expected"` 1 줄 추가 (line 70 인근). 회귀 비교 대상에 wizard 산출 포함.
- [ ] (검토 결과: 변경 불요) `pilot/skills/context/lifecycle/setup/templates/config.md.template` — spec line 51·52 가 "표 헤더는 그대로 유지, 본문 행만 wizard 가 동적 주입" 으로 못박은 그대로. Read 결과 헤더는 이미 정확. **변경 불요**. generator 는 확인 후 변경하지 않는다.

## 단계별 구현 순서 (generator 진행 순서)

1. **spec patch 선행** — `workspace/projects/build-plugin/features/13-init-bootstrap-wizard.md` line 24 의 "빈도 ≥ 2" → "빈도 ≥ 1 (= 존재)" 1 단어 교정. 이후 단계가 본 spec 본문을 참조하므로 가장 먼저 정합화.
2. **`init_detect.py` 작성** — 3 함수 + `IGNORE_BASELINE`/`LANG_EXT_MAP`/`SCOPE_FOLDER_MAP` 상수. doctor.py 의 shebang·docstring·`__main__` 가드 컨벤션 차용. 외부 의존성 0.
3. **`test_init_detect.py` 작성** — 위 케이스 8 건. `unittest.TestCase` + `tempfile.TemporaryDirectory` 패턴. `python3 -m unittest pilot.tests.tools.test_init_detect` (또는 기존 테스트 동일 runner) 로 통과 확인.
4. **`pilot/skills/init/SKILL.md` 본문 갱신** — 변경 3 군데 (`### 2. wizard 적용`, `## 결과 출력`, `## 참고` 의 `--no-wizard`). 1.5 단계 = 기존 `### 1.` 다음 `### 2.` 로 번호 재배치 (현재 1 개 단계만 있으므로 단순 추가).
5. **회귀 fixture 캡처** — v0.3.0 환경 (init_detect 적용 후) 에서 빈 workspace 를 만들고 `cd _input/python-sample && /pilot:init` 수행. 산출된 `workspace/context/config.md` 를 `pilot/tests/fixtures/v0.1.0-baseline/wizard/expected/config.md` 로 복사. wizard skip 분기는 본 fixture 에 포함하지 않음 (Q4 — 첫 init 산출만).
6. **`diff.sh` 의 `EXPECTED_SUBDIRS` 1 줄 추가** — `"wizard/expected"` 항목 삽입. 기존 3 항목 (learn/project/analyze) 뒤에 4 번째로.
7. **`bash diff.sh --actual /tmp/regen` 수동 1 회 실행** — 빈 workspace 에서 `/pilot:init` + `/pilot:learn` + `/pilot:project` + `/pilot:analyze` 4 스킬 cycle 재실행한 결과 디렉터리와 expected 의 4 서브트리 모두 비교. 회귀 0 확인.
8. **단위 + 회귀 양쪽 통과 확인 후 commit** — 1 PR 로 묶음. v0.3.0 milestone 합본 PR 의 일부 (Q7 — patch bump 별도 처리).

## 검증 방법

- **단위 테스트**:
  - `python3 -m unittest discover pilot/tests/tools -p "test_init_detect.py"` 8 케이스 전부 PASS.
  - `python3 -m unittest discover pilot/tests/tools` 기존 테스트 회귀 0 (다른 도구 테스트도 함께 실행).
- **회귀 fixture**:
  - `bash pilot/tests/fixtures/v0.1.0-baseline/diff.sh --actual /tmp/v0.3.0-regen` 실행 시 4 서브트리 (learn/project/analyze/wizard) 모두 `[OK] 일치` + 최종 `[OK] 회귀 없음 — 모든 expected 와 actual 일치` (exit 0).
  - `wizard/expected/config.md` 의 `## learn 언어 패턴` 표가 python 1 행만, `## scope 카테고리` 표가 Models · Services 2 행, `## Ignore` 표가 baseline 10 패턴 전부 포함 확인.
- **사용자 시나리오 수동 확인** (`/tmp/sandbox-wizard/` 빈 폴더에서):
  1. 빈 폴더에서 `/pilot:init` 실행 — wizard 분기 동작 확인. 결과 출력 블록에 "언어 N개 자동 감지" 3 줄 표시.
  2. 동일 폴더에서 `/pilot:init` 재실행 — `config.md exists` → wizard skip + 결과 출력 블록 1 줄 (`wizard skipped`).
  3. 빈 폴더에서 `/pilot:init --no-wizard` 실행 — wizard skip + 빈 스켈레톤만 생성 (Q6 자연어 분기 동작).
- **doctor 정합성**: `python3 pilot/tools/doctor.py /tmp/sandbox-wizard/workspace` 가 schema 검증 PASS — wizard 가 채운 표가 doctor schema 와 정합.

## 주의사항

- **의존성 0 원칙 (Q2)**: `init_detect.py` 는 `pip install` 없이 import 가능해야 한다. `os` · `pathlib` · `collections` · `re` 만 사용. `chardet` · `pathspec` 같은 외부 라이브러리 금지. spec line 50 와 정합.
- **Q1 — 빈도 ≥ 1 의 부작용 검토**: spec 의 원래 "≥ 2" 룰은 노이즈 폴더 (예: 우연히 `controllers/` 1 회 존재하지만 컨벤션 외) 를 걸러내려는 의도. ≥ 1 로 완화 시 fixture 통과는 가능하지만, 사용자 저장소에서 `controllers/` 단일 존재가 scope 후보로 자동 매핑될 수 있다. **결과 출력 블록의 "scope 후보: M개 매핑" 줄에 실제 폴더 목록을 명시** 하여 사용자가 잘못 매핑된 경우 수동 정정 가능하게 한다 (위 SKILL.md 수정 2번 참조).
- **`--no-wizard` 자연어 분기 (Q6)**: argparse 없이 사용자 입력 문자열을 SKILL.md 본문의 자연어 절차로 분기. claude code 가 사용자 입력에서 `--no-wizard` 토큰을 발견하면 wizard 단계를 건너뛴다. 별도 파서 작성 금지 — SKILL.md 본문의 1 단락만으로 충분.
- **fixture 재실행 환경 = v0.3.0 plugin**: wizard 산출 캡처는 v0.3.0 적용 후 환경에서 수행. v0.2.0 환경에서 캡처하면 wizard 가 동작하지 않아 빈 표가 캡처됨. generator 는 step 5 진입 전 `pilot/.claude-plugin/plugin.json` 의 version 이 0.3.0 (또는 dev branch) 인지 확인.
- **timestamp 정규화 보류**: `wizard/expected/config.md` 는 timestamp 포함 가능 (`> 이 파일은 /pilot:init 가 생성한 스켈레톤이다` 주석 외 추가 timestamp 없으면 무관). 만약 wizard 가 timestamp 를 주입한다면 `diff.sh` 가 단순 비교라 회귀 fail 위험. **wizard 본문에 timestamp 주입 금지** — 결과 출력 블록 (stdout) 에만 표시.
- **idempotency 단위 테스트 분리 (Q4)**: "두 번째 `/pilot:init` → wizard skip" 거동은 회귀 fixture 가 아닌 단위 테스트 (또는 SKILL.md 본문의 조건 분기) 로 검증. `test_init_detect.py` 에는 직접 포함하지 않고 (감지 로직만 테스트), SKILL.md 의 `config.md created` 조건 분기 자체로 보증.
- **에이전트 간 전달사항 소비**: `workspace/projects/build-plugin/project.md` 의 `## 에이전트 간 전달사항` 에 본 feature 와 관련된 미처리 항목이 있는지 generator 가 본 작업 시작 전 확인. 발견 시 wrapper protocol 에 따라 처리 후 `[x]` 체크.

## 교차 의존

- **features/01 (learn 언어 패턴 외부화) — [x] 완료**: wizard 의 `## learn 언어 패턴` 표 주입은 features/01 의 5 default 언어 매핑 + lookup 우선순위 (config 우선) 를 따른다. wizard 가 채운 행 위에 사용자가 직접 행을 덮어쓰면 사용자 행이 우선 — features/01 line 21 의 lookup 우선순위와 일관.
- **features/02 (analyze scope 카테고리 외부화) — [x] 완료**: wizard 의 `## scope 카테고리` 표 주입은 features/02 의 default 매핑 (Endpoints/Models/Services) 그대로 사용. wizard 가 채운 표는 features/02 의 5-2 lookup 이 그대로 읽는다.
- **features/00 (회귀 골든 픽스처) — [x] 완료**: 본 feature 의 `wizard/expected/` 는 features/00 의 `_input/python-sample/` 를 입력으로 재활용 (spec line 53). `diff.sh` 의 `EXPECTED_SUBDIRS` 배열 1 줄 추가로 fixture 트리에 합류.
- **v0.3.0 milestone HIGH 4 건 (#09·#10·#11·#12)**: 본 feature 는 v0.3.0 milestone 의 부트스트랩 UX 개선. #09~#12 의 cross-domain 처리와 직접 의존 없음. 합본 PR 시점에 plugin.json patch bump 일괄 처리 (Q7).
- **plugin.json version bump 보류 (Q7)**: 본 PR 은 patch bump 안 함. v0.3.0 milestone 마지막 PR 에서 일괄. generator 는 `pilot/.claude-plugin/plugin.json` 의 version 필드 건드리지 않는다.

## focus 반영 사항

`.focus.md` 의 V1 검증 결과 (nimda Rails monolith dogfooding) 가 도출한 v0.3.0 milestone 재구성은 본 feature 의 우선순위 직접 영향:

- **도입 장벽 해소 (Tier 1)**: spec source 인 design-pilot-review-2026-05-20.md 가 본 feature 를 v0.3.0 의 도입 장벽 해소 항목으로 분류. V1 검증에서 "신규 사용자가 첫 명령부터 막힘" 이 실제 우려로 확인되어 wizard 자동화 필요성 입증.
- **A2 fallback 정합**: focus 의 "A2 runtime fallback (모든 신규 detect 알고리즘 실패 시 abort 안 함)" 원칙은 본 feature 의 spec line 38 (단계별 감지 실패 시 default 주입 + INFO) 와 일관. generator 는 본 plan 의 "주의사항" + spec line 38 양쪽 참조.
- **md / script 한정 + 어플리케이션 코드 변경 최소**: 본 feature 도 동일 — `init_detect.py` (Python script) + SKILL.md (md) + 회귀 fixture 만. 어플리케이션 코드 (예: doctor.py, analyze.py) 수정 없음.
- **TDD 비활성화 (md/script 변경 위주)**: 본 feature 도 `tdd: false`. 단위 테스트 작성은 features/00 의 회귀 검증 보강 차원이지 TDD Red-Green-Refactor 사이클 아님.
