# Doctor 진단 및 마이그레이션

!!! info "한 줄 요약"
    `workspace/` 정합성을 검사합니다. 기본 모드는 **검사만 수행하며 아무것도 고치지 않습니다** — 수정은 `--fix` 를 붙였을 때만 일어납니다. 검사 대상은 STATE/MANIFEST/config 파일 존재, `.agent-state.yml` schema 버전, `analyzed`·`tdd` 플래그와 실제 파일 상태 간의 정합성 등입니다.

## 전제 조건

- `workspace/` 디렉터리가 이미 존재해야 합니다 (`/pilot:init` 실행 완료 상태).
- 다음과 같이 정기 점검이 필요하거나 정합성이 의심되는 상황에 사용합니다:
    - 새 버전의 plugin으로 업그레이드한 후 첫 작업을 시작하기 전
    - subagent 호출 과정에서 원인을 알 수 없는 에러가 지속적으로 발생할 때
    - `.agent-state.yml` 또는 `STATE.md` 파일을 임의로 수동 편집했을 때

## 작업 절차

### 1. 정합성 검사 (기본)

```bash
/pilot:doctor
```

검사 범위는 세 카테고리로 나뉩니다:

- **Workspace** — `workspace/` 존재 여부, `.slack.env` 가 git 추적되지 않는지(중대), `STATE.md` 의 `진행중` 개수(1개만 허용)와 이력 행, `context/MANIFEST.md`·`context/config.md` 존재, `workspace/.env` credential drift, `.gitignore` secret 패턴, auto-memory 감지 안내.
- **Conventions** — `conventions_doc`·`conventions_evals` 로 선언된 경로가 실제로 존재하는지.
- **Project** — `projects/{프로젝트}` 존재, `.agent-state.yml` 존재·파싱·schema 지원 범위, `analyzed` ↔ `features/` 정합, `tdd` 플래그와 `prompts/*.md` 내용의 3-way 정합, `domain`·`pr_base_branch`·`plugin_version` 값, features 증감 drift, `prompts/*.md` 중복 주입·레거시 섹션 잔존.

각 항목은 `PASS`·`INFO`·`WARN`·`ERROR` 4단계로 표시되고, `WARN`·`ERROR` 에는 처방이 함께 출력됩니다. 종료 코드는 `ERROR` 가 하나도 없으면 `0`, 하나라도 있으면 `1` 입니다.

### 2. 자동 수정 (`--fix`)

```bash
/pilot:doctor --fix
```

`--fix` 로 자동 수정되는 항목은 정확히 3종입니다:

| 항목 | 동작 |
| --- | --- |
| STATE.md 이력 행 정리 | `진행중` 이 아닌 행을 제거. `진행중` 이 2건 이상이면 어느 쪽이 맞는지 판단할 수 없어 자동 정리를 보류합니다(사용자 판단 필요). |
| `.agent-state.yml` schema 업그레이드 | 라벨 `v1`/`v1.1` 을 `v1.2` 로 직접 올립니다(버전 체인을 따라가지 않고 현재 schema 로 바로 bump). `v1` 을 올릴 때는 `domain: null` 필드를 함께 주입합니다. |
| `prompts/planner.md` 레거시 섹션 제거 | 래퍼로 이관된 `## 플래닝 프로세스` 섹션을 삭제합니다. |

**주의할 점 두 가지:**

- **백업을 남기지 않습니다.** 수정 대상 파일은 원본 백업 없이 그 자리에서 덮어씁니다.
- **확인 절차 없이 즉시 적용됩니다.** `--fix` 를 실행하면 위 3종 중 대상이 되는 항목이 사용자 확인 없이 바로 수정됩니다.

이 밖에, `--fix` 여부와 **무관하게** 항상 실행되는 자동 조치가 하나 있습니다 — `.gitignore` 에 `.slack.env` 패턴이 없으면 기본 검사 단계에서도 즉시 추가합니다(secret 유출 방지가 read-only 원칙보다 우선합니다).

`--regen-agents` 로 하는 `prompts/` 전체 재생성이나 MANIFEST 표 보정은 `--fix` 대상이 **아닙니다** — 정합성 검사가 drift 를 발견하면 `/pilot:analyze --regen-agents` 실행을 **권장 안내**만 하고, 실제 재생성은 사용자가 해당 명령을 직접 실행해야 합니다.

### 3. 수정 후 검증

```bash
/pilot:doctor
```

모든 검사 항목이 `PASS` 로 출력되는지 확인합니다. `WARN` 상태가 일부 남아있더라도 플러그인 동작은 가능하지만, 추후 정상 작동을 위해 가급적이면 조치하는 것을 권장합니다.

### 4. 실패 진단 (`--diagnose`)

`--diagnose` 는 `doctor.py` 스크립트의 플래그가 **아닙니다.** `python3 doctor.py --diagnose` 처럼 스크립트에 직접 넘기면 인식하지 못하는 인자로 실패합니다. `/pilot:doctor --diagnose` 로 슬래시 커맨드를 경유했을 때만 동작하는 모델 지시문 모드입니다 — 정합성 검사와 독립적으로, 진행 중인 작업이 반복 실패하는 패턴을 진단합니다.

호출 시점: evaluator 가 `NOT_READY` 를 2회 반복했을 때, 동일 도구를 반복 호출하는 듯 의심될 때, 또는 완료를 선언했는데 체크리스트·REPORT 가 비어 있을 때.

4가지 패턴(`loop`·`red-miss`·`repeat-not-ready`·`scope-violation`) 중 해당하는 것을 판정해 `## DIAGNOSIS` 블록(`project`·`pattern`·`evidence`·`recommended_action`·`confidence` 5필드)으로 출력합니다. 해당하는 패턴이 없으면 `pattern: none` 으로 표시합니다.

### 5. 플러그인 구조 검사 (`--schema`)

```bash
python3 doctor.py --schema
```

`workspace` 인자를 받지 않는, 플러그인 구조 전용 검사입니다 — `workspace` 경로 자체가 필요 없습니다. 저장소의 `.github/workflows/validate.yml` 이 `skills/`·`agents/`·`hooks/`·`.claude-plugin/`·`doctor` 스키마 관련 파일이 바뀔 때 CI 로 자동 실행합니다.

## Onboarding Health

`doctor.py` 자체 출력에는 온보딩 점검 섹션이 없습니다. `/pilot:doctor` **스킬 경유 호출에서만**, `MANIFEST.md` 의 `## 도메인 분류` 표가 비어 있거나 `STATE.md` 에 등록된 프로젝트가 하나도 없을 때 모델이 직접 5가지 항목(config 필수 섹션 채움·scope 파일 존재·활성 프로젝트 유무·도메인 분류 표 유무·features 파일 유무)을 점검하고 다음 단계(`/pilot:learn`·`/pilot:project`·`/pilot:create-feature`)를 안내합니다. `project`·`create-feature`·`analyze`·TDD 활성화 절차 등 다른 스킬이 내부에서 doctor 를 호출하는 경우에는 이 온보딩 안내가 나오지 않습니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:doctor`](../reference/skills/doctor.md) · [state-schema](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/state-schema.md)
- :material-lightbulb-on: Explanation: schema 호환성 및 업그레이드 정책에 관한 내용은 [릴리스 및 업그레이드](../explanation/release-and-upgrade.md) 문서에서 다룹니다.
