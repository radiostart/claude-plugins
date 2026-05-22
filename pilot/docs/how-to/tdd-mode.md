# TDD 모드 활성화

!!! info "한 줄 요약"
    Red→Green→Refactor 를 강제해 planner 가 *실패 테스트 먼저*, generator 가 *최소 구현으로 통과*, evaluator 가 *변경 관련 테스트만 실행* 하도록 한다.

## 전제

- 활성 프로젝트가 있다 (`workspace/STATE.md` 에 "진행중" 1 개).
- 프로젝트의 `config.md` 또는 `project.md` 에 `test_command` 가 정의돼 있다 (예: `bundle exec rspec`).
- 신규 프로젝트라면 TDD 로 *시작* 하는 게 더 깔끔 — `/pilot:project --tdd` 를 사용하고 본 how-to 는 건너뛴다.

## 절차

### 1. 현재 상태 확인

```bash
/pilot:tdd
```

`.agent-state.yml` 의 `tdd` 플래그와 `prompts/*.md` 본문이 *일치하는지* 보고한다. 두 위치가 어긋나 있으면 다음 step 의 `--fix` 가 필요.

### 2. TDD 활성화

```bash
/pilot:tdd on
```

3 곳을 한 번에 갱신:

- `.agent-state.yml` 의 `tdd: true`
- `project.md` 제한사항 섹션에 "TDD 모드" 표시
- `prompts/planner.md` · `prompts/generator.md` · `prompts/evaluator.md` 에 TDD 모드 절차 주입

### 3. 정합성 보정 (이상 발견 시)

3 곳 중 한 곳만 어긋난 상태가 의심되면:

```bash
/pilot:tdd --fix
```

3-way 정합성 보정 — 사용자 확인 후 안전한 방향(`tdd: true` 가 *정답인지 false 가 정답인지*) 을 묻고 일괄 갱신한다. 절대 자체 판단으로 침묵 수정하지 않는다.

### 4. 비활성화

```bash
/pilot:tdd off
```

위 3 곳에서 TDD 관련 섹션을 제거. 테스트 파일은 그대로 둔다 (사용자가 별도로 정리).

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:tdd`](../reference/skills/tdd.md) · [`@pilot-planner`](../reference/agents/pilot-planner.md)
- :material-lightbulb-on: Explanation: [모드 — Standard / TDD / Characterize](../explanation/modes.md)
- :material-tools: How-to: 레거시 코드는 TDD 대신 [Characterize 모드](characterize-mode.md) 가 더 안전합니다.
