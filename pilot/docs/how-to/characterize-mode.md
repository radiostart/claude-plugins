# Characterize 모드 — 레거시 코드 안전망

!!! info "한 줄 요약"
    기존 코드의 *현재 동작* 을 spec 으로 포착하는 모드. 구현 변경 없이 (`{source_root}` 잠금) 테스트만 추가해 안전망을 먼저 확보. 리팩터는 별도 사이클로 분리.

## 전제

- 활성 프로젝트가 있고 대상 도메인의 코드가 이미 존재한다 (신규 기능이 아닌 *기존 동작 보존* 작업).
- `config.md` 에 `test_command` · `source_root` 가 정의돼 있다.
- 신규 기능이거나 spec 부재 코드를 *처음 작성* 하는 거라면 [TDD 모드](tdd-mode.md) 가 맞다.

## 절차

### 1. Characterize 모드로 전환

```bash
/pilot:characterize
```

`.agent-state.yml` 에 `mode: characterize` 를 기록하고, prompts 가 다음과 같이 변형된다:

- **Planner** — Characterization Contract 작성: 스텝별 *입력 / 현재 출력(placeholder) / 관찰된 사이드 이펙트*. "현재 출력" 은 Generator 가 실제 실행 후 채운다 — Planner 가 예측 기록 금지.
- **Generator** — `{source_root}` *수정 금지*. spec/test 파일만 추가. 실제 동작을 호출해서 "현재 출력" 을 plan.md 에 다시 적는다.
- **Evaluator** — 작성한 테스트가 *현재 동작을 그대로 확인* 하는지 검증. 회귀 방지 목적.

### 2. feature 추가 후 사이클 실행

```bash
/pilot:create-feature "결제 취소 시 환불 정책 포착"
@pilot-planner
@pilot-planner-critic   # 선택, 권장
@pilot-generator
@pilot-evaluator
```

`tdd` 와 `characterize` 가 동시에 켜져 있어도 **characterize 가 우선**. plan-validate 가 schema 를 강제한다.

### 3. 안전망 확보 후 일반 모드 복귀

테스트로 코드가 충분히 둘러싸였다면:

```bash
/pilot:characterize off
```

`mode` 를 해제. 이후 사이클은 표준 (또는 `tdd` 활성 시 TDD) 로 돌아간다. 이때부터 본격 리팩터 가능.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:characterize`](../reference/skills/characterize.md) · [plan-schema 의 characterize 모드](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/plan-schema.md)
- :material-lightbulb-on: Explanation: [모드 — Standard / TDD / Characterize](../explanation/modes.md)
- :material-tools: How-to: 안전망이 확보되면 [TDD 모드](tdd-mode.md) 로 전환해 리팩터를 진행하는 흐름이 자연스럽습니다.
