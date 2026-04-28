# Characterization Test 정책

레거시 코드의 **현재 동작** 을 포착해 spec 으로 고정하는 모드. 안전하게 리팩터할 발판을 만들기 위한 단계. `rgr.md` (TDD Red-Green-Refactor) 와 병렬 존재.

> **언어 중립 규약:** `{test_command}`·`{source_root}`·`{test_path_convention}` 토큰은 [`rgr.md`](rgr.md) 상단 규약과 동일하게 `workspace/context/config.md` `## 언어·도구 기본값` 에서 해석. 언어별 테스트 프레임워크 관행은 `conventions_doc` 문서를 우선 따른다.

## 전제

- `.agent-state.yml` 의 `mode: characterize` 가 활성화된 프로젝트·사이클에서만 적용.
- `tdd: true` 와 `mode: characterize` 가 동시 설정된 경우 **characterize 가 우선** (Red 계약 대신 Characterization Contract 사용).
- **구현 변경 없음** — spec 만 추가. 리팩터는 characterization spec 이 녹색인 상태에서 **별도 사이클** 로 진행.
- Planner → Generator → Evaluator 흐름 유지.

## 역할 분담

| 에이전트 | 역할 | 건드리는 파일 |
| --- | --- | --- |
| Planner | 포착 대상 분할 + **Characterization Contract 작성** (테스트 코드 X) | `features/NN-{slug}.plan.md` |
| Generator | **현재 동작 실행·기록** (테스트 디렉터리·factories 만 추가) + 증거 기록 | 테스트 계층 + `.plan.md` (**`{source_root}` 절대 금지**) |
| Evaluator | **`{source_root}` 미수정 검증** + 테스트 pass + 3 축 일치 확인 | 읽기 전용 + `{test_command}` + `git diff` |

## 스텝 단위

Planner 가 포착 대상을 분할하는 기준:

- 단일 진입점 (메서드·엔드포인트·CLI 명령) 1 개 또는 관련 경로 묶음
- 이미 작성된 다른 characterization spec 이 독립적으로 pass 하는 단위
- 사이드 이펙트 경계가 명확한 단위 (DB 테이블·로그 파일·외부 API 호출 범위)

## Planner — Characterization Contract

Planner 는 **테스트 코드를 직접 쓰지 않는다**. 대신 현재 동작의 **3 축** 을 `.plan.md` 에 남긴다.

### 3 축

1. **입력** — 호출 인자 / HTTP request body / CLI args / 환경변수 등 진입 데이터
2. **현재 출력** — 반환값 / response body / stdout / exit code. **추정하지 않고 Generator 가 실제 실행해서 기록**
3. **관찰된 사이드 이펙트** — DB write / 로그 / 파일 / 외부 API 호출 중 **탐지 가능한 것**. 탐지 불가 사이드 이펙트는 "탐지 불가 가능성" 으로 명시 (숨기지 말 것). 언어별 비동기 큐·캐시·이벤트 러너 후보는 `conventions_doc` 참조

### plan 파일 형식

```markdown
### 스텝 목록 (Characterization Contract)

1. **[스텝 1]** {대상 메서드/엔드포인트} — {포착 단위 설명}
   - 테스트 대상: `{test_path_convention 에 따른 경로}`
   - 입력: {호출 인자 / request body / CLI args — 값 예시}
   - 현재 출력: {Generator 가 실행 후 기록} — 계약 시점엔 "Generator 실행 예정" 으로 비워둠
   - 관찰된 사이드 이펙트: {DB/로그/파일/외부 API — 탐지 가능한 것 나열 or "없음" or "탐지 불가"}
   - 탐지 불가 가능성 영역: {비동기 큐·캐시 invalidation·웹훅 등 — 해당 시}

2. **[스텝 2]** ...
```

Generator 가 현재 동작 실행 후 각 스텝에 `[Captured]` 증거 라인을 추가한다.

### 경계 규칙

- 테스트 프레임워크 문법·factories·fixtures 를 **몰라도 작성 가능**. Generator 가 실제 값 채워 넣음.
- Planner 가 "현재 출력" 을 **예측해서 기록하지 말 것**. 실제 실행한 Generator 만 기록.
- 탐지 불가 사이드 이펙트를 전부 나열할 필요 없음. "가능성 있는 영역" 표시만으로 충분 — Evaluator 가 실행 중 추가 발견 시 계약 갱신 요구.

## Generator — Capture

Planner 가 남긴 `.plan.md` 의 3 축 계약을 이행한다. **`{source_root}` 수정 절대 금지**.

### 절차

1. plan 파일의 스텝 계약 Read — 테스트 대상 경로, 입력, 사이드 이펙트 목록 확인
2. 현재 코드를 **수정 없이** 호출 경로 실행. 선택지:
   - 테스트 파일에 포착 대상 호출 코드 먼저 작성 → `{test_command}` 실행 → 출력 관찰
   - 콘솔·REPL·스크립트 러너에서 1 회 실행 후 결과 수집 (언어별 수단은 `conventions_doc` 참조)
3. 실제 관찰된 입력·출력·사이드 이펙트를 테스트 assertion 으로 기록
   - 파일명은 대상 소스 파일과 1:1 매칭 (`{test_path_convention}`)
   - 일반 TDD 테스트와 구분되도록 "characterization" 그룹으로 묶음 (언어별 그룹핑 문법은 `conventions_doc`)
4. `{test_command} {file}` — 통과 확인. **인프라 오류 시 factory·helper·부팅 설정 수정은 허용** (테스트 계층). `{source_root}` 수정은 절대 금지.
5. **[필수 게이트] `{source_root}` 미수정 검증** — `git diff --stat {source_root}` 이 비어있어야 함. 1 줄이라도 변경됐으면 **`git checkout {source_root}`** 로 원복 후 처음부터
6. **[필수 게이트] `.plan.md` 증거 기록** — 해당 스텝에 아래 라인 추가:

   ```markdown
   - [Captured] 실행 명령: {test_command 호출 전체}
   - [Captured] 테스트 pass: {ISO 8601 timestamp}
   - [Captured] {source_root} 미수정 확인: ✅  (git diff --stat → empty)
   - [Captured] 추가 발견 사이드 이펙트: {계약에 없던 것 — 있으면 나열, 없으면 "없음"}
   ```

### 완료 게이트

아래 조건을 **모두** 충족해야 완료:

- 테스트 계층 파일 **1 개 이상** 추가·수정됨
- `{source_root}` 하위 변경 **0 줄** (`git diff --stat {source_root}` empty)
- 직전 `{test_command} {file}` 전체 통과
- `.plan.md` 의 모든 스텝에 `[Captured]` 증거 4 라인 기록

조건 미충족 시 종료하지 않고 계속한다.

## Evaluator — Snapshot 검증

1. **테스트 실행** — `{test_command} {이번 사이클 관련 테스트}` 전체 pass 확인
2. **`{source_root}` 미수정 검증** (capture_lockdown gate) — `git diff --stat {source_root}` 확인
   - 비어있음 → pass
   - 1 줄이라도 있음 → fail. Generator 에 원복 + 재작업 요청
3. **3 축 일치 확인** — `.plan.md` 계약의 입력·사이드 이펙트가 실제 테스트 assertion 과 일치하는지 육안 점검
   - 불일치 → Generator 에 테스트 재작성 요청
   - `[Captured] 추가 발견 사이드 이펙트` 가 있으면 **Planner 에게 계약 갱신 요청** (후속 feature 로)
4. VERIFICATION REPORT 출력 — `capture_lockdown` gate 포함 (gate 판정은 [`guardrails.md`](../shared/guardrails.md) § 기본 판정 축 + 이 문서의 추가 축 을 따름)

## 사후 리팩터 사이클

Characterization spec 이 녹색인 상태에서 **별도 feature 또는 mode 전환** (`mode: null` → `tdd: true` 등) 으로 리팩터 진행.

리팩터 중 characterization spec 이 깨지면:

- **의도된 동작 변경** — 계약을 업데이트하고 spec 수정. 커밋 메시지에 근거 명시.
- **의도하지 않은 회귀** — 리팩터 롤백.

## 탐지 불가 사이드 이펙트 전제

Planner·Generator 모두 아래 영역은 **자동 탐지 어려움** (언어·프레임워크별 구체 예는 `conventions_doc`):

- 비동기 큐·워커 (예: Sidekiq/ActiveJob, Kafka producer, JVM `ExecutorService`)
- 캐시 invalidation (Rails.cache, Redis, JVM Caffeine 등)
- 외부 웹훅 / 푸시 발사
- 다단계 간접 호출 체인 (깊이 3 이상)

계약 시점에 "탐지 불가 가능성 영역" 으로 명시만 해두고, Evaluator 가 실행 중 추가로 발견하면 후속 계약 갱신으로 처리한다. **1 회 완벽한 계약을 요구하지 않는다** — 점진적 개선 원칙.
