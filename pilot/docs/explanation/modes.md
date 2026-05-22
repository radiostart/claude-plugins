# 모드 — Standard / TDD / Characterize

`.agent-state.yml` 의 `tdd` (불리언) 와 `mode` (`null` 또는 `"characterize"`) 두 값이 각 wrapper 의 행동을 분기시킵니다.

## 진입 분기

```mermaid
flowchart TD
    Start([orchestrate-load.py 실행])
    Start --> ReadState{.agent-state.yml<br/>읽기}
    ReadState --> ModeCheck{mode 값?}

    ModeCheck -->|"characterize"| CharMode["**Characterize 모드**<br/>characterize.md 로드<br/>(source_root 수정 금지)"]
    ModeCheck -->|null 또는 미설정| TddCheck{tdd 값?}

    TddCheck -->|true| TddMode["**TDD 모드**<br/>rgr.md 로드<br/>(Red→Green→Refactor)"]
    TddCheck -->|false 또는 미설정| Standard["**Standard 모드**<br/>모드별 추가 가이드 없음"]

    CharMode --> ApplyHints[wrapper 에 hints 주입]
    TddMode --> ApplyHints
    Standard --> ApplyHints

    Note["mode + tdd 동시 설정 시<br/>characterize 가 우선"]
    ModeCheck -.- Note
```

`tdd: true` 와 `mode: characterize` 가 동시에 설정돼도 **characterize 가 우선**입니다 — 안전망 확보가 더 먼저라는 판단.

## 모드별 책임 비교

| 차원 | Standard | TDD | Characterize |
|---|---|---|---|
| **Planner 산출물** | `plan.md` 자유 형식 | Red Contract — *테스트 대상 / 검증할 행동 / 기대 실패 유형* | Characterization Contract — *입력 / 현재 출력(placeholder) / 관찰된 사이드 이펙트* |
| **Generator 행동** | 구현 작성 | 실패 테스트 작성 후 *최소 구현* | `{source_root}` 수정 금지. **테스트만 추가**, 실제 실행으로 "현재 출력" 측정 |
| **Evaluator 검증** | 요구사항 충족 + 패턴 일관성 | 변경 관련 테스트만 실행 (`{test_command} {paths}`) | 추가된 테스트가 *현재 동작을 그대로 확인* 하는지 |
| **plan-validate 강제** | 자유 (doc-level 만 검증) | `### 스텝 목록` 필수, 스텝별 3 라벨 의무 | `### 스텝 목록 (Characterization Contract)` 필수, 스텝별 4 라벨 의무 |
| **언제 쓰나** | 명세가 명확하고 보강할 테스트는 사이클 내 자연 산출 | 새 기능, 사양이 검증 가능한 행동으로 표현됨 | 레거시 코드의 *현재 동작 포착* 후 리팩터 안전망 |

상세 schema 는 [plan-schema.md](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/plan-schema.md) 가 SSOT.

## 모드 전환

| 명령 | 효과 | 3-way 동기화 |
|---|---|---|
| `/pilot:tdd on` / `off` | `.agent-state.yml` + `project.md` + `prompts/*.md` 갱신 | 자동 |
| `/pilot:tdd --fix` | 3 곳이 어긋났을 때 정합성 보정 | 사용자 확인 후 |
| `/pilot:characterize` | `mode: characterize` 설정 | 자동 |
| `/pilot:characterize off` | `mode` 해제 | 자동 |

3-way 동기화는 [Doctor 진단·마이그레이션](../how-to/doctor-migration.md) 가 일상 검증을 담당합니다.

## 왜 mode 와 tdd 가 *분리* 인가

언뜻 보기에 한 enum (`mode: standard | tdd | characterize`) 으로 합치는 게 단순해 보입니다. 하지만:

- **`tdd` 는 *프로젝트 전체* 의 정책** — 어떤 feature 든 Red Contract 로 시작한다는 약속.
- **`mode: characterize` 는 *임시 모드*** — 특정 feature 의 *현재 동작 포착* 작업. 끝나면 해제되고 다시 일반 (tdd 또는 standard) 으로 복귀.

두 값을 분리해서 *TDD 프로젝트에서 일부 feature 만 characterize* 같은 조합이 자연스럽게 표현됩니다 (characterize 후 → tdd 로 리팩터).

## 다음

- [Drift Protocol](drift-protocol.md) — 모드와 무관하게 컨텍스트가 코드와 어긋났을 때.
- How-to: [TDD 모드 활성화](../how-to/tdd-mode.md) · [Characterize 모드](../how-to/characterize-mode.md).
- Reference: [`/pilot:tdd`](../reference/skills/tdd.md) · [`/pilot:characterize`](../reference/skills/characterize.md).
