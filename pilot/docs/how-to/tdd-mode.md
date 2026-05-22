# TDD 모드 활성화

!!! info "한 줄 요약"
    Red→Green→Refactor 개발 cycle을 강제하여, planner가 *실패하는 test를 먼저 정의*하고, generator가 *이를 통과하기 위한 최소한의 구현*만을 수행하며, evaluator가 *변경 사항과 관련된 test만 집중 실행*하도록 합니다.

## 전제 조건

- 활성화된 project가 있어야 합니다 (`workspace/STATE.md` 내 진행중인 project가 1개).
- project의 `config.md` 또는 `project.md` 파일에 `test_command` 설정이 정의되어 있어야 합니다 (자세한 설정 방법은 [워크스페이스 설정](workspace-config.md) 가이드 참고).
- 신규 project라면 TDD 모드로 *시작*하는 것을 권장합니다 — 프로젝트 초기화 시 `/pilot:project --tdd` 옵션을 적용하고 본 가이드는 생략하셔도 좋습니다.

## 작업 절차

### 1. 현재 상태 확인

```bash
/pilot:tdd
```

`.agent-state.yml` 설정의 `tdd` flag 상태와 `prompts/*.md` 파일의 내용이 일치하는지 점검합니다. 두 설정이 불일치하는 경우 다음 단계의 `--fix` 조치가 필요합니다.

### 2. TDD 활성화

```bash
/pilot:tdd on
```

다음 3가지 항목을 동시에 갱신합니다:

- `.agent-state.yml` 내 `tdd: true` 설정
- `project.md` 파일의 제약사항 섹션에 'TDD 모드' 표시 추가
- `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md` 템플릿에 TDD 관련 동작 가이드 주입

### 3. 정합성 보정 (오류 발생 시)

3가지 영역의 정합성이 맞지 않는 상황이 의심되는 경우:

```bash
/pilot:tdd --fix
```

3-way 정합성 복구를 수행합니다. 사용자 확인을 거쳐 기준이 될 설정(TDD 활성화 여부)을 파악한 후 일괄 수정합니다. 임의로 판단하여 백그라운드에서 동기화하지 않습니다.

### 4. TDD 모드 비활성화

```bash
/pilot:tdd off
```

위 3가지 영역에서 TDD 관련 가이드 및 설정을 제거합니다. 기존에 작성된 test 파일들은 삭제되지 않고 보존되므로 필요 시 수동으로 정리해야 합니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:tdd`](../reference/skills/tdd.md) · [`@pilot-planner`](../reference/agents/pilot-planner.md)
- :material-lightbulb-on: Explanation: [모드 — Standard / TDD / Characterize](../explanation/modes.md)
- :material-tools: How-to: 레거시 code에 작업을 시작하는 경우 TDD 모드 대신 [Characterize 모드](characterize-mode.md)를 적용하는 것이 안전합니다.
