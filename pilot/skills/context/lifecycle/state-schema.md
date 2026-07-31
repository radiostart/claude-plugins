# `.agent-state.yml` 스키마

프로젝트 단위 machine-readable 상태 파일. Wrapper agents (`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator`) 가 분기 결정에 사용한다. 문자열 detection literal 을 대체한다.

## 위치

`workspace/projects/{PROJECT}/.agent-state.yml`

- 프로젝트 루트에 숨김 파일
- `example/` 폴더에는 존재하지 않음 (스캐폴딩 대상 아님)

## 스키마 v1.2

```yaml
schema: v1.2
analyzed: false                      # /pilot:analyze 실행되어 prompts/*.md 가 분석본으로 채워졌는지
tdd: false                           # TDD 모드 활성 여부 (Red-Green-Refactor 흐름 강제)
domain: null                         # 도메인명 (자유 문자열, 사용자 정의) — null 이면 analyze 전 질의 필요

# Optional — /pilot:characterize 가 설정:
mode: null                           # null | characterize — characterize 는 레거시 현재 동작 포착 모드 ({source_root} 잠금, 테스트만 추가)

# Optional — /pilot:analyze 가 기록:
analyzed_at: "2026-04-18T10:30:00Z"  # 마지막 analyze ISO 8601 UTC timestamp
last_analyzed_features: 3            # 그 시점 features/*.md 개수 (.plan.md 제외)

# Optional — /pilot:confl fetch 가 기록:
docs_last_fetched_at: "2026-04-19T05:00:00Z"  # 마지막 confluence fetch 성공 timestamp

# Optional — /pilot:project 신규 생성 시 기록:
plugin_version: "0.1.75"             # .agent-state.yml 을 마지막으로 쓴 플러그인 버전 (semver)

# Optional — /pilot:pr 가 사용자 명시 입력 시 기록 (v1.2 신규):
pr_base_branch: "release/4.5"        # PR 생성 시 자동 타겟. 부재 시 context/config.md 의 pr_default_base 사용
```

필수 4 개 (`schema`·`analyzed`·`tdd`·`domain`) + optional 6 개. optional 필드는 drift 감지 (`/pilot:pilot-doctor`) · 모드 분기 (`mode`) · 플러그인 업그레이드 감지 (`plugin_version`) · PR 자동 타겟 (`pr_base_branch`) 에 사용. 부재 시 해당 체크·분기만 skip.

## 필드 의미

### `schema`

- 값: `v1.2` (현재). 필수 필드.
- `v1` · `v1.1` 로 기록된 파일도 **읽을 수는 있음** (하위호환). 신규 optional 필드 (`pr_base_branch`) 는 부재로 처리.
- Wrapper/skill 로드 시 schema 값이 미지이면 **즉시 에러 + 마이그레이션 안내 후 종료**.
- 버전 정책:
  - 필드 **추가** = minor bump (`v1.1` → `v1.2`, 리더 하위호환 유지)
  - 필드 **삭제** 또는 의미 **변경** = major bump (`v1.x` → `v2`)

### `analyzed`

- `true`: `/pilot:analyze` 가 실행되어 `prompts/planner.md` · `prompts/generator.md` · `prompts/evaluator.md` 에 도메인 압축본이 주입된 상태.
- `false`: pre-analyze 상태. 프로젝트 agent 파일은 example 템플릿 원본 (`{플레이스홀더}`) 에 가까움.

Wrapper 동작 차이:

- `analyzed: true` → context/ 도메인 파일 재로드 생략 (prompts/*.md 에 압축 기입돼 있다고 신뢰)
- `analyzed: false` → MANIFEST 의 도메인 진입 파일을 fallback 로드

### `tdd`

- `true`: TDD 모드 활성. Red-Green-Refactor 흐름 강제.
- `false`: 비 TDD 프로젝트. Planner → Generator → Evaluator 일반 흐름.

### `mode` (optional)

- 값: `null` (기본) 또는 `characterize`.
- `characterize`: 레거시 코드의 현재 동작 포착 모드. `{source_root}` 수정 금지, 테스트 (`{test_path_convention}`) 만 추가. 상세: [`characterize.md`](../modes/characterize.md).
- `tdd: true` 와 `mode: characterize` 동시 설정 시 우선순위는 [`characterize.md`](../modes/characterize.md):10 이 정본 (characterize 우선 — Red 계약 대신 Characterization Contract 사용).
- 전환 명령: `/pilot:characterize` (`on` / `off`).

### `domain` (v1.1 신규, 필수)

- 값: 자유 문자열 (사용자 정의 도메인명) 또는 `null`. MANIFEST.md 의 도메인 분류에 정의된 이름을 따른다.
- `null` → `/pilot:analyze` 진입 시 **반드시 사용자에게 질의** 후 값 기록. 자동 추론으로 기록 금지 (후보 제시는 허용 — 사용자 확인 필수).
- 값이 있으면 analyze·orchestrate-load 가 `MANIFEST.md` 의 `## 도메인 분류` 표에서 진입 파일을 찾아 자동 로드 대상으로 사용.

### `analyzed_at` (optional)

ISO 8601 UTC timestamp. `/pilot:analyze` 가 완료될 때 기록.

- 부재 (legacy 또는 pre-analyze) → drift 체크 skip.
- 존재 + `context/` 하위 도메인 파일 (MANIFEST·config 제외) mtime 이 더 최근 → doctor 가 "도메인 파일 업데이트됨, `--regen-agents` 권장" WARN.
- 존재 + `docs_last_fetched_at` 이 더 최근 → doctor 가 "기획서 업데이트됨, `--force` 재분석 권장" WARN.

### `last_analyzed_features` (optional)

마지막 analyze 실행 시점의 `features/*.md` (`.plan.md` 제외) 개수.

- 부재 → drift 체크 skip.
- 존재 + 현재 features 개수가 `last_analyzed_features + 1` 초과 → doctor 가 "features 가 증가함, `--regen-agents` 권장" WARN.

### `docs_last_fetched_at` (v1.1 신규, optional)

`/pilot:confl fetch` 또는 `/pilot:project {URL}` 의 fetch 성공 시 기록되는 ISO 8601 UTC timestamp.

- file system mtime 대신 이 필드를 drift 비교 기준으로 사용 (git clone·cp -p 로 mtime 이 흔들리는 문제 회피).
- `analyzed_at` 과 비교하여 기획서 변경 drift 감지.

### `pr_base_branch` (v1.2 신규, optional)

`/pilot:pr` 가 사용자에게 base branch 를 질의했을 때 **명시적으로 입력한 값** 만 기록. Enter (default 채택) 의 경우 미저장.

- 부재 → `config.md` 의 `pr_default_base` 사용 (부재면 하드 fallback `develop`).
- 존재 → PR 스킬이 자동 타겟. 단, "타겟: X (저장됨). 변경? [Enter=유지]" 한 줄 confirm 노출 (silent 사용 금지 — stale 가능).
- 새로 입력 시 기존 값을 덮어쓴다.
- doctor 가 remote 존재 (`git ls-remote --exit-code origin <X>`) 확인 → 없으면 WARN.

### `plugin_version` (optional)

`.agent-state.yml` 을 마지막으로 쓴 pilot 플러그인 버전 (semver, e.g. `"0.1.75"`). `.claude-plugin/plugin.json` 의 `version` 필드와 동일 포맷.

- **Writers**: `/pilot:project {PROJECT}` 신규 생성 시 · `/pilot:analyze` 완료 시 함께 갱신.
- **Reader**: `tools/orchestrate-load.py` 가 wrapper 진입 시 현재 실행 플러그인 버전과 비교 → major/minor 차이가 있으면 `hints` 에 WARN 주입. `doctor.py` 도 동일 체크.
- **semver 규칙**:
  - `state.plugin_version == current` → silent
  - `state.plugin_version < current` (minor 이상 차이) → WARN: wrapper 계약 변경 가능, `--regen-agents` 권장
  - `state.plugin_version > current` → WARN: 플러그인 다운그레이드 감지
  - patch 차이 (0.1.74 vs 0.1.75) → silent (내부 버그픽스 가정)
  - 부재 (legacy state) → INFO: 다음 writer 이벤트에 자동 기록
- **$CLAUDE_PLUGIN_ROOT 미설정 환경** (e.g. 테스트): reader 측이 비교 skip. writer 측은 값 없이 저장 (필드 자체 생략).

## Writers

| 시점 | 설정 |
|---|---|
| `/pilot:project NAME` | 신규 파일 생성: `{schema: v1.2, analyzed: false, tdd: false, domain: null, plugin_version: <현재>}` |
| `/pilot:project NAME --tdd` | 위 + `tdd: true` |
| `/pilot:analyze` 진입 | `domain` 이 null 이면 사용자 질의 후 기록 |
| `/pilot:analyze` 완료 후 | `analyzed: true`, `analyzed_at`, `last_analyzed_features`, `plugin_version` 갱신 |
| `/pilot:analyze --regen-agents` | `analyzed_at`, `last_analyzed_features`, `plugin_version` 갱신 |
| `/pilot:tdd` | `tdd: true` 갱신 |
| `/pilot:confl fetch` 성공 | `docs_last_fetched_at` 갱신 |
| `/pilot:pr` 사용자 명시 입력 | `pr_base_branch` 기록 (Enter=default 시 미기록) |
| `doctor --fix` (schema 업그레이드) | v1 / v1.1 → v1.2 in-place 업그레이드 시 `plugin_version` 기록 |

## Readers

Wrapper agents (`planner.md`·`generator.md`·`evaluator.md`) 가 컨텍스트 로드 단계에서 Read.

- 파일 부재 또는 `schema` 미지 → 에러 종료 + 안내
- `analyzed` 값으로 scope 재로드 분기
- `tdd` 값으로 rgr.md 로드 분기

## Schema 업그레이드 (in-place)

`.agent-state.yml` 이 이미 존재하고 schema 가 구버전이면 `doctor --fix` 가 in-place 업그레이드 한다:

- schema 가 `v1` 이면 기존 필드 보존 + `domain: null` 추가 + `schema` 를 `v1.2` 로 변경.
- schema 가 `v1.1` 이면 schema 문자열만 `v1.2` 로 갱신 (신규 필드는 모두 optional 이라 본문 변경 없음).
- schema 가 `v1.2` 이면 skip.

## 금지 사항

- **수동 편집 금지.** 사용자가 손으로 값 바꾸지 말 것. 관련 스킬 (`project`·`analyze`·`tdd`·`confl`) 을 통해서만 변경.
- `.gitignore` 포함 여부는 사용자 정책. 공유가 필요하면 commit, 개인 전용이면 ignore.
