# TDD 정책 (Red-Green-Refactor)

TDD 모드가 활성화된 프로젝트에서 기능을 구현할 때 아래 절차를 따른다.

> **언어 중립 규약:** 이 문서의 `{...}` 중괄호 토큰은 `workspace/context/config.md` 의 `## 언어·도구 기본값` 에서 해당 키 값으로 해석한다. 래퍼 (`orchestrate-load.py`) 가 `config` 로 주입.
>
> - `{test_command}` — 테스트 러너 (예: Ruby `bundle exec rspec`, Kotlin `./gradlew test --tests`)
> - `{test_command_fail_fast}` — 첫 실패 중단 모드 (없으면 `{test_command}` 사용)
> - `{source_root}` / `{test_path_convention}` — 소스·테스트 경로 매핑. 프로젝트 관례는 `conventions_doc` 파일 참조.
>
> `workspace/context/config.md` 미정의 시 Evaluator/Generator 가 사용자에게 `{test_command}` 를 질의한다. 언어별 관행 (테스트 프레임워크 함수·Mock 패턴) 은 `conventions_doc` 가 가리키는 문서를 우선 따른다.

## 전제

- `project.md` 제한사항에 **TDD 모드** 문구가 있는 프로젝트에서만 적용한다.
- Planner → Generator → Evaluator 흐름을 유지한다. 별도 에이전트를 추가하지 않는다.
- 테스트 없이 프로덕션 코드부터 작성하지 않는다.

## 실행 단위

호출 1 회 = **feature 1 개** 단위. 사용자가 `@planner` → `@generator` → `@evaluator` 를 feature 별로 명시 호출한다.

- Planner 1 회 = 해당 feature 의 전체 스텝 Red 계약을 `.plan.md` 에 작성
- Generator 1 회 = 그 .plan.md 의 모든 스텝을 한 컨텍스트에서 Red→Green→Refactor 순환

## 역할 분담

| 에이전트  | TDD 역할 | 건드리는 파일 |
| --------- | -------- | ------------- |
| Planner   | 스텝 분할 + **Red 계약 작성** (테스트 코드 X) | `features/NN-{slug}.plan.md` |
| Generator | **Red 작성·실패 확인 → Green → Refactor** (+ 증거 기록) | 테스트 디렉터리 + `{source_root}` + `.plan.md` |
| Evaluator | **Red 증거 검증 + 변경 관련 테스트 실행 + 커버리지 확인** | 읽기 전용 + `{test_command}` 실행 |

Planner 는 테스트 프레임워크 문법을 몰라도 계약만 작성 가능하다. Red 작성·실행·인프라 수정은 Generator 가 한 컨텍스트에서 순환한다. Evaluator 는 `.plan.md` 의 Red 증거를 교차 검증하여 TDD 디스립틴을 보장한다.

## 스텝 단위

Planner가 기능을 분할하는 기준:

- 테스트 1~3개로 커버 가능한 행위 단위
- 외부 의존성 없이 테스트 가능한 단위부터 시작 (모델 → 서비스 → 컨트롤러 순)
- 각 스텝은 이전 스텝이 그린 상태일 때 착수 가능해야 한다

## Planner — Red Contract

Planner 는 **테스트 코드를 직접 쓰지 않는다**. 대신 아래 계약을 `features/NN-{slug}.plan.md` 에 남긴다. Generator 는 이 계약을 이행하여 Red 테스트를 작성한다.

### 절차

1. `features/NN-{slug}.md` 에서 **조건 / 트리거 / 기대결과** 확인
2. 기능을 스텝 단위로 분할
3. 각 스텝에 대해 **Red 계약 3 축** 을 기술:
   - **테스트 대상 경로** — `{test_path_convention}` 에 따른 예상 경로. feature 번호·슬러그를 파일명에 붙이지 않는다
   - **검증할 행동** — 조건 + 트리거 + 기대결과 한 문장
   - **기대 실패 유형** — 구현 미완 시 발생할 실패 형태 (예: `NoMethodError` / `undefined method` / `expected X got Y` / `AssertionError` — 언어별 형태는 `conventions_doc` 참조)
4. plan 파일을 `features/NN-{slug}.plan.md` 로 저장 (에이전트 래퍼 6 단계에서 수행)

### plan 파일 형식

```markdown
### 스텝 목록

1. **[스텝 1]** {서비스/메서드} — {행위 요약}
   - 테스트 대상: `{test_path_convention 에 따른 경로}`
   - 검증할 행동: {조건} → {트리거} → {기대결과}
   - 기대 실패 유형: {예상 실패 원인 1 줄}

2. **[스텝 2]** ...
```

Generator 가 Red 를 실제로 작성·실행한 뒤 각 스텝에 [Red] / [Green] / [Refactor] 증거 라인을 추가한다 (아래 Generator 절차 참조).

### 경계 규칙

- 테스트 프레임워크 문법·factories·fixtures·helpers 를 **몰라도 작성 가능** 해야 함. 알면 기술해도 되지만 **테스트 대상 경로 이외의 인프라 파일명 명시 금지** (Generator 가 판단).
- 스텝 계약이 모호하면 Generator 가 Red 재설계를 요구할 수 있음 (Evaluator 가 반려 경로 확보).

## Generator — Red + Green + Refactor

Planner 가 남긴 `.plan.md` 의 스텝 계약을 이행한다. **Red 작성 → Green → Refactor** 를 한 에이전트에서 순환한다.

### 효율 규칙

- 컨텍스트 로드 단계에서 필요한 파일을 한 번에 읽는다 (구현 중 추가 탐색 최소화)
- 동일 파일을 반복 Read 하지 않는다 — 이미 읽은 내용은 기억하고 재사용한다
- 여러 줄 수정은 개별 Edit 이 아닌 한 번의 Edit 으로 처리한다
- Grep/Glob 탐색은 대상이 불확실할 때만 사용한다 — generator.md 에 경로가 명시된 파일은 직접 Read 한다

### Red

1. plan 파일의 스텝 계약 Read — 테스트 대상 경로, 검증할 행동, 기대 실패 유형 확인
2. 실패 테스트 작성 — 파일명은 대상 소스 파일과 1:1 매칭 (`{test_path_convention}`). 같은 대상의 여러 feature 는 하나의 테스트 파일 안에서 구조화 (언어별 그룹핑 문법은 `conventions_doc` 참조). `pending` / `@Ignore` 등 비활성화가 아닌 **명시적 실패** 여야 한다
3. `{test_command} {file}` 실행 — 실패 확인
   - **fail-fast 사용 금지**. Red 단계에선 모든 테스트의 실패·오류 유형을 끝까지 확인해야 한다. 첫 실패에서 끊으면 뒤쪽 테스트의 구문 오류 등이 묻힌다
   - 실패 메시지가 **구현 미완성** 징후인지 확인 (예: `NoMethodError`, `expected X got Y`, `undefined method`, `AssertionError: method X not found` — 언어별 양상은 `conventions_doc` 참조)
   - **인프라 오류** (`SyntaxError`, `LoadError`, factory·fixture 미정의, 테스트 러너 부팅 실패 등) 가 나오면 **테스트 대상이 아니라 인프라를 수정** 한다
4. **[필수 게이트]** `.plan.md` 해당 스텝에 Red 증거 기록. 없으면 Green 으로 넘어가지 않는다:

   ```markdown
   - [Red] 실패 메시지: {`{test_command}` 출력 마지막 3-5 줄}
   - [Red] 실패 유형: {구현 미완 ✅ / 인프라 오류 ⚠️}
   ```

### Green

1. 테스트를 통과시키는 **가장 단순한** 코드만 작성
   - 다음 스텝에서 다룰 범위는 구현하지 않는다
2. `{test_command_fail_fast} {file}` — 통과 확인. 첫 실패 즉시 중단으로 시간 절약 (MANIFEST 미정의 시 `{test_command}` 로 fallback)
3. `.plan.md` 해당 스텝에 Green 증거 기록:

   ```markdown
   - [Green] 통과: {ISO 8601 timestamp}
   ```

### Refactor

1. 테스트 그린 상태 유지하며 정리
   - 중복 제거, 네이밍 개선, 책임 분리 (외부 모델 의존 → 서비스)
   - 언어별 정리 대상 (시간·null·IO 계열 권장 API 등) 은 `conventions_doc` 참조
2. **[조건부 재실행]** Refactor 단계에서 **실제 코드가 수정된 경우에만** `{test_command_fail_fast} {file}` 재실행
   - 아무것도 안 바꿨으면 Green 유지로 간주하고 재실행 생략 (테스트 러너 부팅 비용 절약)
   - fail-fast 모드: Green 유지 확인이 목적이라 첫 실패 즉시 중단으로 충분
3. `.plan.md` 해당 스텝에 Refactor 증거 기록:

   ```markdown
   - [Refactor] {수정 내역 요약 또는 "변경 없음"}
   ```

### 완료 게이트

아래 조건을 **모두** 충족해야 완료로 간주:

- `{source_root}` 하위 파일을 **1 개 이상** 생성 또는 수정했다 (테스트 파일만 변경은 불가)
- 직전 `{test_command} {file}` 결과가 전체 통과였다 (재실행 생략 시 Green 단계의 결과 유지)
- `.plan.md` 의 모든 스텝에 **[Red] + [Green] 증거 기록**됨 (Refactor 는 선택)
- 조건 미충족 시 종료하지 않고 구현을 계속한다

## Evaluator — 실행 및 검증

1. **변경 관련 테스트만 실행** — `{test_command} {이번 feature 에서 추가·수정된 테스트 경로들}`
   - 전체 스위트 (인자 없는 `{test_command}`) 실행은 **금지**. 부팅·실행 비용이 수분~수십분이고 대부분 이번 변경과 무관한 결과.
   - 관련 테스트가 여러 개면 한 줄에 나열해 한 번에 실행
2. **Red 증거 검증** — `.plan.md` 의 **모든 스텝** 에 `[Red]` / `[Green]` 증거가 기록되어 있는지 확인:
   - **증거 누락** → Generator 에 TDD 사이클 재수행 요청 (반려)
   - **실패 유형이 "인프라 오류"** 로 기록된 스텝 → Generator 에 Red 재작성 요청 (factory·helper 수정 후 실제 구현 미완 실패로 재확인해야 함)
   - **실패 메시지 타당성 점검** — 기록된 실패 메시지가 `기대 실패 유형` 과 일치하는지, 정말 "미구현" 징후인지 사람 판단으로 점검. 예: `NoMethodError` 인데 서비스가 이미 존재하면 Red 가 엉뚱한 대상일 수 있음
3. 실패 항목 있으면 원인 보고 (수정은 Generator 에 재요청)
4. 신규 프로덕션 코드에 대응하는 테스트 파일 존재 여부 확인
5. 요구사항 체크리스트 검토

---

## Mock 안티패턴 (언어 공통)

테스트 작성 시 아래 패턴을 피한다. 언어별 구체 예시·권장 문법은 `conventions_doc` 가 가리키는 문서를 참조.

1. **Mock 호출 여부만 검증** — Mock 존재만 테스트하는 것은 실제 동작을 보장하지 않는다. 최종 관찰 가능한 상태·출력으로 검증한다.
2. **의존성을 이해하지 못하고 범위 초과 Mock** — Mock 범위는 외부 시스템 (API, 이메일, 외부 스토리지) 에 한정. 내부 서비스·도메인 로직은 실제로 실행한다.
3. **불완전한 Mock** — 일부 필드만 채운 응답 객체는 프로덕션 스키마와 괴리된 테스트를 낳는다. 실제 응답 구조를 그대로 반영한다.
4. **프로덕션 코드에 테스트 전용 분기·메서드 추가** — 테스트 편의를 위해 프로덕션 코드를 오염시키지 않는다 (예: `reset_for_test`, `@VisibleForTesting` 남용).
