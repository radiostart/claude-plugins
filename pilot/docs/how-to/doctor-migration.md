# Doctor 진단 및 마이그레이션

!!! info "한 줄 요약"
    `workspace/` 정합성을 검사하고 불일치 사안을 자동 마이그레이션합니다. `.agent-state.yml` 의 schema 업그레이드(예: v1.1 → v1.2), STATE/MANIFEST/config 파일 누락, 또는 `analyzed` 와 `tdd` 플래그와 실제 파일 상태 간의 불합치(STATE corrupt) 등을 조기 감지합니다.

## 전제 조건

- `workspace/` 디렉터리가 이미 존재해야 합니다 (`/pilot:init` 실행 완료 상태).
- 다음과 같이 정기 점검이 필요하거나 정합성이 의심되는 상황에 사용합니다:
    - 새 버전의 plugin으로 업그레이드한 후 첫 작업을 시작하기 전
    - subagent 호출 과정에서 원인을 알 수 없는 에러가 지속적으로 발생할 때
    - `.agent-state.yml` 또는 `STATE.md` 파일을 임의로 수동 편집했을 때

## 작업 절차

### 1. 진단 실행 (Read-only)

```bash
/pilot:doctor
```

이 명령은 다음 항목을 중점적으로 검사합니다:

- `STATE.md` 내의 활성화된 project 개수 검사 (오직 1개만 허용됩니다).
- 각 활성 project의 `.agent-state.yml` schema 버전 및 필수 항목(key) 누락 여부 검사.
- `MANIFEST.md` 및 `config.md` 파일의 존재 유무 및 형식 정합성.
- `analyzed` 플래그 정보와 실제 `features/` 디렉터리 내 파일 상태와의 정합성.
- `tdd` 플래그 정보와 실제 `prompts/*.md` 파일 내용의 일치 여부.
- 의존하고 있는 기획서 문서(`docs/`) 파일의 누락 유무.

출력 결과는 카테고리별로 PASS, WARN, FAIL로 구분되어 표시되며, 각 이슈 사항을 바로잡기 위한 추천 해결 방법이 안내됩니다.

### 2. 자동 정합성 수정 (`--fix`)

자동 조치가 가능한 정합성 문제들을 해결합니다:

```bash
/pilot:doctor --fix
```

주요 수정 조치:

- **schema 마이그레이션**: v1.0 → v1.1 → v1.2 업그레이드를 수행합니다. 필수 필드(`plugin_version`, `mode` 등) 누락 시 안전한 default 값으로 채우며, 원본 파일은 `.agent-state.yml.bak-{version}` 형태로 backup 본을 남깁니다.
- **MANIFEST 테이블 보정**: 문법이나 형식이 어긋난 표 구조(row)를 파악하여 사용자 확인을 거친 뒤 수정합니다.
- **prompts/ 재생성**: `project.md` 의 `[analyze-managed]` 영역을 토대로 prompts 파일을 다시 생성합니다. (`--regen-agents` 와 동일한 동작을 수행합니다)

*사용자 몰래 백그라운드에서 임의로 수정하는 작업은 전혀 없으며, 모든 수정 액션 전에 사용자 확인을 요청합니다.*

### 3. 수정 후 검증

마이그레이션이 끝난 뒤 다시 진단을 실행합니다:

```bash
/pilot:doctor
```

모든 검사 항목이 PASS로 출력되는지 확인합니다. WARN 상태가 일부 남아있더라도 플러그인 동작은 가능하지만, 추후 정상 작동을 위해 가급적이면 조치하는 것을 권장합니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:doctor`](../reference/skills/doctor.md) · [state-schema](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/state-schema.md)
- :material-lightbulb-on: Explanation: schema 호환성 및 업그레이드 정책에 관한 내용은 [릴리스 및 업그레이드](../explanation/release-and-upgrade.md) 문서에서 다룹니다.
