# Characterize 모드 — 레거시 코드 안전망

!!! info "한 줄 요약"
    테스트 없는 기존 코드를 리팩터하기 전에 — *지금 그 코드가 실제로 하는 동작* 을 그대로 테스트로 고정하는 모드. 구현은 한 줄도 바꾸지 않고 (`{source_root}` 잠금) 테스트만 추가해 회귀 안전망을 먼저 친다.

## Characterize 모드란

### 풀려는 문제

리팩터하려는 코드에 테스트가 없다. 이름 변경·구조 분리·의존성 업그레이드 — 무엇을 건드려도 *어딘가 조용히 깨질* 위험이 있다. 그렇다고 일반 테스트를 새로 쓰기도 어렵다. 이 코드가 *무엇을 해야 하는지* 적힌 명세가 없기 때문이다. 지금은 **코드의 현재 동작 자체가 사실상의 명세** 다 — 그 안에 버그가 섞여 있고, 다른 코드가 이미 그 버그 동작에 맞춰져 있을 수도 있다.

### 해결 — 현재 동작을 포착한다

Characterize 모드는 *characterization 테스트* 를 쓴다. 코드가 *해야 할* 동작이 아니라 *지금 실제로 하는* 동작을 포착해 고정하는 테스트다. 절차는 단순하다:

1. 대상 코드를 **수정 없이 실행** 한다.
2. 실제로 나온 출력·사이드 이펙트를 **관찰** 한다.
3. 관찰값을 그대로 assertion 으로 적는다 — 테스트는 작성 시점에 당연히 통과한다.

이 시점부터 리팩터가 동작을 바꾸면 테스트가 깨진다. 그 깨짐이 안전망이다 — "방금 무언가 달라졌다" 는 경보.

### TDD 와 무엇이 다른가

|  | TDD | Characterize |
|---|---|---|
| 무엇을 고정하나 | 코드가 *해야 할* 동작 | 코드가 *지금 하는* 동작 |
| 테스트 작성 시점 | 구현 *전* (Red 먼저) | 코드 관찰 *후* (출력은 측정값) |
| 버그를 만나면 | 고친다 | **버그째로 포착한다** |
| 모드 성격 | 프로젝트 정책 (지속) | 임시 단계 (안전망 확보 후 해제) |

핵심 차이는 **버그도 그대로 포착한다** 는 점이다. characterization 테스트의 목적은 코드를 *고치는* 게 아니라 *현 상태를 있는 그대로 보존* 하는 것이다. 버그 수정·동작 개선은 안전망이 갖춰진 뒤 별도 사이클에서 한다 — 그래야 "내가 의도한 변경" 과 "실수로 깨뜨린 회귀" 가 구분된다.

!!! warning "characterization 테스트가 실패하면"
    코드가 *틀렸다* 는 뜻이 아니라 동작이 *바뀌었다* 는 뜻이다. 의도한 변경이면 계약과 테스트를 함께 갱신하고, 의도하지 않았으면 회귀이므로 되돌린다.

### 왜 구현을 잠그나

`{source_root}` 잠금은 안전망의 신뢰성을 보장한다. 안전망을 만드는 도중 구현까지 같이 바꾸면, 테스트가 포착한 게 *원래 동작* 인지 *방금 바꾼 동작* 인지 알 수 없다. 잠금은 "이 테스트들은 네가 손대기 *전* 의 코드를 기술한다" 를 보증한다. Generator 가 픽스처·헬퍼 같은 테스트 계층을 손보는 건 허용되지만, `{source_root}` 아래는 1 줄도 안 된다 — Evaluator 가 `git diff` 로 강제한다.

## 전제

- 활성 프로젝트가 있고 대상 도메인의 코드가 이미 존재한다 (신규 기능이 아닌 *기존 동작 보존* 작업).
- `config.md` 에 `test_command` · `source_root` 가 정의돼 있다 ([워크스페이스 설정](workspace-config.md) 참조).
- 신규 기능이거나 테스트 부재 코드를 *처음 작성* 하는 거라면 [TDD 모드](tdd-mode.md) 가 맞다.

## 절차

### 1. Characterize 모드로 전환

```bash
/pilot:characterize
```

`.agent-state.yml` 에 `mode: characterize` 를 기록한다. 이후 사이클에서 세 에이전트의 동작이 바뀐다:

- **Planner** — *Characterization Contract* 를 쓴다. 포착 대상을 스텝으로 나누고 각 스텝의 *입력 / 현재 출력 / 관찰된 사이드 이펙트* 를 적되, **"현재 출력" 칸은 비워 둔다**. Planner 가 출력을 예측하면 그건 *명세를 추측* 하는 것이고, 추측은 안전망을 오염시킨다. 실제 값은 코드를 돌려 본 Generator 만 채운다.
- **Generator** — `{source_root}` 를 잠근 채 대상 코드를 실제로 실행하고, 관찰된 출력·사이드 이펙트를 테스트 assertion 으로 기록한다. 각 스텝에 `[Captured]` 증거 라인 (실행 명령·통과 시각·미수정 확인) 을 남긴다.
- **Evaluator** — `{source_root}` 가 정말 그대로인지 (`git diff` 비어 있음), 테스트가 통과하는지, 계약의 입력·사이드 이펙트가 실제 assertion 과 일치하는지 검증한다. 커버리지 숫자가 아니라 *회귀 방지* 가 판정 기준이다.

### 2. feature 추가 후 사이클 실행

```bash
/pilot:create-feature "결제 취소 시 환불 정책 포착"
@pilot-planner
@pilot-planner-critic   # 선택, 권장
@pilot-generator
@pilot-evaluator
```

포착 대상을 한 feature 에 다 몰아넣지 말고, 진입점 (메서드·엔드포인트·CLI 명령) 단위로 나눠 사이클을 반복한다. `tdd` 와 `characterize` 가 동시에 켜져 있어도 **characterize 가 우선** — 안전망 확보가 먼저다. plan-validate 가 Characterization Contract schema 를 강제한다.

!!! tip "탐지하기 어려운 사이드 이펙트"
    비동기 큐·캐시 무효화·웹훅 같은 사이드 이펙트는 자동 탐지가 어렵다. 한 번에 완벽한 계약을 요구하지 않는다 — 계약에 "탐지 불가 가능성 영역" 으로 표시만 해 두고, 사이클을 돌며 발견될 때마다 계약을 갱신한다.

### 3. 안전망 확보 후 일반 모드 복귀

대상 동작이 테스트로 충분히 둘러싸였다면:

```bash
/pilot:characterize off
```

`mode` 를 해제한다. 이후 사이클은 표준 (또는 `tdd` 활성 시 TDD) 으로 돌아가고, **이때부터 본격 리팩터** 를 한다. 방금 만든 characterization 테스트가 그 리팩터의 회귀 안전망이 된다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:characterize`](../reference/skills/characterize.md) · [characterize 모드 정책 (characterize.md)](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/modes/characterize.md)
- :material-lightbulb-on: Explanation: [모드 — Standard / TDD / Characterize](../explanation/modes.md)
- :material-tools: How-to: 안전망이 확보되면 [TDD 모드](tdd-mode.md) 로 전환해 리팩터를 진행하는 흐름이 자연스럽습니다.
