---
name: learn
description: >-
  기존 소스 코드에서 진입점(컨트롤러·서비스 파일 또는 폴더)을 받아
  `workspace/context/` 의 도메인 문서를 부트스트랩한다. `/pilot:analyze`
  가 docs/ 기획서를 features/ 로 가공하는 짝이라면, 이 스킬은 코드를
  읽어 컨텍스트를 만든다. 의존성을 N 단계까지 따라가며 파일 분류·정적
  추출(메서드·라우트·상태값·검증 규칙) 후 코드의 자연스러운 모양에
  맞춘 `{domain}.md` 또는 `{domain}/` 폴더를 생성하고 MANIFEST.md 색인을
  갱신한다. 추측 금지 — 코드에 적힌 것만 file:line 인용으로 정리한다.
---

# /pilot:learn

소스 코드 진입점에서 도메인 컨텍스트를 부트스트랩한다.

대상: $ARGUMENTS

**사용 예:**

```
/pilot:learn app/controllers/api/orders_controller.rb
/pilot:learn app/services/payments/
/pilot:learn src/main/kotlin/com/example/billing/ --domain billing
/pilot:learn app/models/order.rb --depth 1
/pilot:learn app/controllers/admin/refund_controller.rb --domain refund --force
```

**옵션:**

- `{entry-point}` (필수) — 컨트롤러·서비스 파일 또는 폴더 경로.
- `--domain NAME` (선택) — 자동 도출된 도메인명 override.
- `--depth N` (선택, 기본 `2`) — 의존성 추적 깊이 (`0` 이면 진입점만).
- `--force` (선택) — 기존 컨텍스트 파일을 묻지 않고 덮어쓰기.

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행.

- P-1: TodoWrite 선로딩 (다단계 스킬 — 5 phase).
- P0: 진입 경로 keyword (파일명·폴더명·도메인 후보) 로 memory-hint 실행. 출력 메모를 Read 하여 과거 동일 도메인 분석 이력 확인.

> **P1 미적용** — 이 스킬은 활성 프로젝트가 없어도 실행 가능하다 (workspace 부트스트랩 단계에서 사용). `workspace/` 자체가 없으면 [messages.md](../context/shared/messages.md) 의 `workspace_missing` 출력 후 종료.

`workspace/context/config.md` 를 Read 하여 `Ignore` 패턴, `language`, `source_root` 를 확보한다. 파일·섹션이 없으면 경고 한 줄만 출력하고 진행 (기본값: 모든 파일 포함, 언어 휴리스틱은 진입 파일 확장자에서 추론).

---

## 인자 파싱

`$ARGUMENTS` 에서 플래그 (`--domain`·`--depth`·`--force`) 를 분리하고 나머지를 `{entry-point}` 로 본다.

검증:

- `{entry-point}` 비어있음 → "진입점 경로를 입력하세요. 예: `/pilot:learn app/controllers/orders_controller.rb`" 출력 후 종료.
- 경로 미존재 → "진입점 `{path}` 가 존재하지 않습니다. 경로를 확인하세요." 출력 후 종료.
- `--depth N` 이 음수·비숫자 → "depth 는 0 이상 정수여야 합니다." 출력 후 종료.

---

## 수행 절차

5 phase 로 진행한다. 사용자 확인 게이트가 최대 2 회 (Phase 2 끝, Phase 4 중간) — 코드 분석 비용이 높아 잘못된 방향으로 진행 후 되돌리면 시간이 크게 낭비되기 때문. 단, **발견 파일 ≤ 5 개 인 작은 진입점에서는 Phase 2 확인을 자동 skip** (좁힐 여지가 거의 없으므로 사용자 피로 방지).

> 본 절차의 "Phase N" 은 이 스킬 내부 단계 번호. preamble 의 P-1·P0·P1 (사전 확인) 과는 별개 namespace.
>
> **Abort cleanup 계약** — 어느 Phase 에서든 사용자가 중단하면 **어떤 Write 도 수행하지 않는다** (메모리 폐기). MANIFEST·context 파일은 그대로 유지. 이미 P5 진입 후라면 batch Write 가 끝난 상태이므로 abort 불가.

### Phase 1. 도메인 도출

1. **자동 도출 규칙** — 진입점 경로에서 도메인 후보 추출:
   - 파일: `app/controllers/api/orders_controller.rb` → `orders` (파일명에서 `_controller`·`_service`·`Controller`·`Service` 접미사 제거).
   - 폴더: `app/services/payments/` → `payments` (마지막 폴더명).
   - 폴더 내부에 동명 파일이 있으면 그것을 진입 파일로 채택 (예: `payments/payments_service.rb`).
2. `--domain NAME` 가 있으면 그 값을 채택 (자동 도출 무시).
3. 자동 도출 결과가 모호 (`app/controllers/api/v2/admin_orders_controller.rb` 처럼 다층) → 사용자에게 후보 2~3 개 제시 후 선택.
4. 결정된 `{domain}` 으로 후속 단계 진행.

### Phase 2. Inventory — Glob/Grep 만 사용 (Read 금지)

목적: 어떤 파일들이 도메인에 속하는지 **선읽기 없이** 파악. 큰 코드베이스에서 무작정 Read 하면 토큰이 폭발한다.

**핵심 가드 (cycle + cap):**

- **방문 set** — 의존성 추적 시 이미 본 파일은 재방문 금지. 순환 의존 (`Order` ↔ `OrderService`) 에서 무한 루프 방지.
- **파일 수 cap** — 발견 파일 > **50 개** 면 통계 출력 직후 **사용자에게 좁히기를 강력 권유** (depth 축소·서브폴더 한정·helpers 제외 등). 그대로 진행도 허용하나 Phase 3 비용 경고 명시. 50 은 휴리스틱 — 너무 적으면 일반 controller-service-model 탐색이 막히고, 너무 많으면 토큰이 터진다.

> **config lookup**: 본 단계 시작 전 `workspace/context/config.md` 의 `## learn 언어 패턴` 섹션을 Read. 두 표 (의존성 추적 + 역할 분류) 의 행이 있으면 우선 사용. 표가 비어있거나 매칭 행이 없으면 폴더 인접성 fallback. 이 플러그인은 특정 언어를 가정하지 않는다 — config 에 정의된 패턴만 사용하고 없으면 인접성 fallback.
>
> **A2 runtime fallback 절차**: config 표의 각 행을 사용 전 검증 (컬럼 수·헤더 일치). 잘못된 행은 무시하고 폴더 인접성 fallback 을 사용. 오류 1 건당 stderr 에 `[WARN] config.md ## learn 언어 패턴 {행번호 또는 사유}: fallback 사용` 1 줄 출력. abort 하지 않는다 — 1 행 오류로 전체 워크플로를 중단하는 것보다 fallback 이 안전하다. doctor 가 별도 실행될 때만 ERROR 로 보고 (integrity.py `check_workspace_config_sections`).

1. 진입점에서 시작해 의존성을 `--depth N` 만큼 추적한다.
   - **언어별 추적 패턴** (Grep 으로 의존 식별자 추출). `workspace/context/config.md` 의 `## learn 언어 패턴` › `### 의존성 추적` 표에서 해당 언어 행이 있으면 그 패턴을 사용하고, 없으면 폴더 인접성 fallback (같은 폴더·하위 폴더) 을 사용한다.

   > config lookup: 본 단계에서 `workspace/context/config.md` 의 `## learn 언어 패턴` › `### 의존성 추적` 표를 먼저 조회. 표가 비어있거나 해당 언어 행이 없으면 폴더 인접성 fallback. 이 플러그인은 특정 언어를 가정하지 않는다 — 언어 패턴은 사용자가 config 에 직접 정의 (참조: `pilot/README.md` 의 example block).

   - 식별 안 되는 언어는 단순 폴더 인접성 (같은 폴더·하위 폴더) 으로 fallback.
2. 발견 파일을 역할별 분류 (Glob 패턴·파일명 패턴·간단 Grep 헤더로 판단 — Read 없이). `workspace/context/config.md` 의 `## learn 언어 패턴` › `### 역할 분류` 표에서 해당 역할 행이 있으면 그 패턴을 사용하고, 없으면 폴더 인접성 fallback 으로 분류한다.

   > config lookup: 표가 비어있거나 매칭 행이 없으면 폴더 인접성 fallback — 같은 폴더 내 파일을 `other` 로 분류. 잘못된 행 발견 시 stderr 에 `[WARN] config.md ## learn 언어 패턴: {사유} — fallback 사용` 1 줄 (abort 안 함).

3. **필터링**:
   - `config.md` 의 `Ignore` 패턴 매칭 파일 제외.
   - 테스트 파일 기본 제외 (`*_spec.rb`·`*_test.rb`·`*Test.kt`·`__tests__/**`·`*.test.ts`·`*.spec.ts`).
   - 벤더링·생성 파일 제외 (`vendor/**`·`node_modules/**`·`build/**`·`dist/**`·`.gen.*`).
4. 통계 한 줄 출력:

   ```
   발견 파일 N개 (controllers M · services K · models L · routes R · helpers H · 기타 P)
   진입점: {entry-point}
   추적 깊이: {depth}
   도메인: {domain}
   ```

5. **사용자 확인 1** — 범위 승인 (단 **발견 파일 ≤ 5 개면 자동 skip**, 통계만 출력하고 Phase 3 진입):

   ```
   위 범위로 진행할까요?
     a) 그대로 진행
     b) 좁히기: helpers 제외 / depth 1 로 축소 / 특정 폴더 제외 …
     c) 도메인명 변경
     d) 중단
   ```

   사용자가 좁히기를 요청하면 해당 조건으로 inventory 를 재산출한 뒤 재확인.

### Phase 3. Read & 추출 (소스 코드 특화 전략)

승인된 범위의 파일에서 정적 정보만 추출. **소스 코드는 docs/ 산문과 다르다** — 전체 본문이 의미적으로 중요한 docs 와 달리, 코드에서는 **구조적 추출 (시그니처·선언·검증 규칙) 이 본문 전체보다 가치가 높다**. 이 차이가 read 전략을 결정한다.

**파일 크기별 read 전략:**

| 파일 크기 (라인) | 전략 |
| --------------- | ---- |
| ≤ 300 줄 | **전체 Read** — 작은 파일은 컨텍스트 비용이 작고 정보 밀도가 높다 |
| 301 ~ 1000 줄 | **Targeted Read** — header (1~30 줄) Read + 언어별 패턴 Grep 으로 라인 번호 수집 + 매치 주변 ±10 줄만 추가 Read |
| > 1000 줄 | **Skip + 사용자 알림** — 통상 god file. 도메인 지식 추출에 부적합. "이 파일은 너무 커서 자동 추출에서 제외했습니다 — 필요하면 따로 진입점으로 호출하세요" 안내. 진입 파일 자체가 1000 줄 초과면 그냥 진행 (사용자가 의도) |

**Targeted Read 시 Grep 패턴 (라인 번호 수집용):**

| 추출 대상 | Grep 패턴 (예시 — 언어별) |
| --------- | ------------------------- |
| 클래스 선언·헤더 | `^class \|^module \|^interface \|^@RestController` |
| public 메서드 시그니처 | `^\s*def \|^\s*public \|^\s*fun ` |
| route / endpoint | `@GetMapping\|@PostMapping\|^get \|^post ` (Rails routes.rb·decorator) |
| state enum 선언 | `enum \|STATUSES =\|@Entity\|case class ` |
| validation·guard | `validates \|@Valid\|require\|assert ` |

각 매치 라인을 `Read` 의 `offset` 으로 ±10 줄 (또는 다음 빈 줄까지) 만 읽는다. 25k 토큰 거부 발생 시 `limit` 1/2 축소 재시도.

**read budget 가드:**

- Phase 2 의 발견 파일 수 × 평균 read 비용으로 사전 추정. 30 파일 × 평균 200 줄 = ~6k 줄 ≈ 50k 토큰. 100 파일이면 위험. Phase 2 의 "50 cap 권유" 가 1 차 방어선.
- 추출 과정에서 토큰 사용량이 누적 50k 토큰 초과시 (전체 컨텍스트 한도 ~200k 의 25%) **사용자에게 진행 여부 재확인**.

각 파일에서 추출:

- **파일 목적** — 파일 상단 docstring·주석 (있으면 인용).
- **public interface** — 메서드 시그니처, route path/method (Rails: `routes.rb` 매칭 행 / Kotlin: `@GetMapping` 등 / TS: router 정의), 클래스명·상속·include.
- **의존성** — import/require/use 목록 (P2 에서 이미 추출됐다면 검증 차원).
- **state enum** — 언어별 상수·enum 패턴:
  - Ruby: `STATUSES = %w[draft paid shipped]`·`enum status: { ... }`
  - Kotlin: `enum class OrderStatus { DRAFT, PAID, SHIPPED }`
  - TS: `enum OrderStatus`·`type Status = "draft" | "paid"`
- **business rule** — validation·conditional branch with domain 의미:
  - validation 행 (`validates :amount, presence: true`)
  - 상태 전환 가드 (`if status == :paid && ...`)
  - 도메인 의미가 담긴 if/case 분기

집계 시 **추측 금지**:

- 코드에 문자 그대로 있는 내용만 인용. 주석 인용은 허용.
- "아마 이런 의도일 것이다" 같은 해석은 절대 본문에 쓰지 않는다 (한 번 추측이 들어가면 후속 사용자·planner 가 잘못된 사실을 근거로 의사결정).
- 모든 추출 항목은 `file:line` 인용을 남긴다 — 예: `상태 전환은 paid → ready_to_ship 만 허용 (app/services/order_service.rb:42)`.
- 인용된 file:line 은 `/pilot:doctor` 가 mtime drift 로 stale 여부를 추후 감지할 수 있게 한다.

추출 결과는 메모리에 카테고리별 (routes·controllers·services·models·enums·rules) 로 누적.

### Phase 4. 구조 결정 + 미리보기 + 생성

1. **구조 결정** — 휴리스틱으로 폴더 구조 선택. 상세는 [`references/heuristics.md`](references/heuristics.md). 요약:

   | 코드 형태 | 추천 구조 |
   | --------- | --------- |
   | 단일 도메인, 작음 (총 ≤200 줄) | `{domain}.md` 한 파일 |
   | 단일 도메인, 큼 | `{domain}/` 폴더 + 카테고리 (`routes.md`·`models.md`·`services.md`) 또는 sub-cluster |
   | 명확한 sub-domain (예: `payments/auth/` · `payments/refund/`) | 코드 구조 미러 — `{domain}/{sub}.md` |
   | Routes/Models/Services 가 코드에서 명확 분리 | `{domain}/routes.md` · `models.md` · `services.md` |
   | State machine 풍부 | 자연스러우면 `enums/{Model}.md` 추가 |

2. **파일 크기 정책** 적용:
   - 진입/index 파일 (예: `{domain}/index.md`) ≤ **100 줄** — 요약 + 링크만.
   - 본문 파일 ≤ **200 줄** — 초과 시 자연스러운 축으로 분할:
     - 1 순위: sub-domain 분할 (`payments/refund.md` + `payments/auth.md`)
     - 2 순위: 카테고리 분할 (`services.md` + `models.md`)
     - 3 순위: 알파벳 분할 (`services-a-m.md` + `services-n-z.md` — 마지막 수단)
3. **미리보기 출력**:

   ```
   생성될 파일 (tree):
     workspace/context/{domain}/
       index.md           (~85 줄)
       routes.md          (~140 줄)
       services.md        (~190 줄)
       models.md          (~120 줄)

   샘플 (각 파일 첫 1~2 줄):
     index.md       → "# {domain} — 도메인 요약 ..."
     routes.md      → "# {domain} — Routes ..."
     ...
   ```

4. **사용자 확인 2** — 구조 승인:

   ```
   이 구조로 생성할까요?
     a) 이대로
     b) 다르게 분할 (예: sub-domain 별로 나눠줘)
     c) 중단
   ```

5. **충돌 처리** — `workspace/context/{domain}.md` 또는 `workspace/context/{domain}/` 가 이미 존재하면:
   - `--force` 있음 → 조용히 덮어쓰기.
   - `--force` 없음 → 3-way 질의:

     ```
     `workspace/context/{domain}.md` 가 이미 존재합니다. 어떻게 처리할까요?
       a) overwrite (기존 파일 백업 없이 덮어쓰기)
       b) sub-domain 추가 (`{domain}/{sub-name}.md` 로 합병하거나 `{domain}-v2` 로 별도 생성)
       c) 중단
     ```

6. 승인 후 **batch Write** — 같은 turn 안에서 여러 Write tool_use 를 한 번에 묶어 호출한다 (3~5 개 단위 권장; harness 가 병렬 실행).

### Phase 5. MANIFEST.md 갱신 + doctor

MANIFEST 의 자유 형식 원칙 준수 — **기존 정의가 있으면 그에 따르고, 정의가 없을 때만 새로 만든다**.

1. `workspace/context/MANIFEST.md` 를 Read.
2. **기존 도메인 분류 구조 detect** — 아래 순서로 판별:

   | 발견된 형태 | 처리 |
   | ----------- | ---- |
   | `## 도메인 분류` H2 + 표 (3 컬럼 이상) | 표에 행 추가 (기존 컬럼 수에 맞춰 정렬) |
   | `## 도메인 분류` H2 + 산문/리스트 (표 아님) | 동일 형식으로 한 항목 append (예: `- {domain}: \`{entry}\` — {설명}`) |
   | `## 도메인` 또는 다른 헤딩으로 도메인 목록이 있음 | 그 헤딩 안에 동일 형식으로 append |
   | 도메인 분류 섹션이 전혀 없음 | 새 섹션 생성 — 표준 3 컬럼 표 (`| 도메인 | 진입 파일 | 설명 |`) |

   파싱은 best-effort — 모호하면 사용자에게 1 줄 질의 ("MANIFEST 에 도메인 항목을 어떻게 추가할까요? a) 기존 표에 행, b) 산문 1 줄, c) 새 섹션 생성").

3. **추가 항목 형식** (구조에 맞춰 변형):

   - 표 형식: `| {domain} | \`{entry-file-path}\` | {one-line summary} |`
   - 리스트 형식: `- **{domain}** — \`{entry-file-path}\` : {one-line summary}`
   - 산문 형식: `{domain} 도메인은 \`{entry-file-path}\` 가 진입점이며 {설명}.`

   `{entry-file-path}` 는 `workspace/context/` 기준 상대 경로 — `{domain}.md` 한 파일이면 그것, 폴더 구조면 `{domain}/index.md` 또는 첫 본문 파일.

   > **새 섹션 생성 시** — 표준 3 컬럼 표를 만들고 그 위에 안내 한 줄: "_도메인 분류 — `/pilot:learn` 이 자동 갱신. 진입 파일은 workspace/context/ 기준 상대 경로._"

4. **`orchestrate-load.py` 와의 호환성** — 표 형식으로 적은 경우 plugin 이 자동 파싱해 wrapper 진입 시 자동 로드한다 (`parse_manifest_domain_files`). 산문·리스트 형식은 자동 파싱 대상이 아니지만 MANIFEST 자체가 항상 로드되므로 agent 가 자연어로 추적 가능.

5. doctor 실행 — 결과를 사용자에게 그대로 출력:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
   ```

6. **결과 출력**:

   ```
   learn 완료: {domain}

   생성:
     - workspace/context/{domain}/index.md          (NN 줄)
     - workspace/context/{domain}/routes.md         (NN 줄)
     - workspace/context/{domain}/services.md       (NN 줄)
     - workspace/context/{domain}/models.md         (NN 줄)
   읽은 파일 N 개 / 발견 N 개 (제외 N 개: ignore·tests)

   갱신:
     - workspace/context/MANIFEST.md (도메인 분류 +1 행)

   검증: {doctor 결과 한 줄}

   다음 단계:
   → 생성된 파일을 검토하고 필요한 경우 수정·보강
   → 도메인 작업 시작: `/pilot:project {프로젝트명}` 또는 `/pilot:issue`
   → 같은 도메인의 다른 진입점을 추가 학습하려면 `/pilot:learn {다른 진입점} --domain {domain}`
   ```

---

## 제약

- 플러그인 v1 — **단일 언어·단일 진입점** 가정. 멀티 언어 모노레포는 진입점을 나눠 여러 번 호출.
- **추측 금지** — 코드에 없는 비즈니스 의도는 본문에 쓰지 않는다. 주석 인용만 허용.
- **diff 모드 없음** — 기존 컨텍스트와의 차이 분석은 v1 범위 밖. 갱신은 `--force` 또는 sub-domain 추가.
- 활성 프로젝트와 무관 — STATE.md 를 변경하지 않는다.
- **출력 구조는 codebase 따라 자유** — `scope/{domain}.md` 같은 고정 컨벤션을 강제하지 않는다. **MANIFEST.md 가 discovery contract** — 에이전트는 MANIFEST 를 먼저 읽고 표의 진입 파일을 따라간다 (`orchestrate-load.py:parse_manifest_domain_files` 가 자동 파싱). 자연 구조가 우연히 `scope/{domain}.md` 와 일치해도 보너스로 자동 로드.
- `scope/{domain}.md` · `rules/{domain}.md` 는 **사용자 커스텀 layer** — 이 스킬이 만드는 자동 산출물 위에 사용자가 손으로 추가하는 코드 스타일·세부 규칙용. 본 스킬은 이 두 경로를 직접 만들지 않는다.

---

## 참고

- `/pilot:analyze` — docs/ 기획서를 features/ 로 가공 (이 스킬의 짝).
- `/pilot:init` — workspace 스켈레톤 생성. 이 스킬 실행 전 1 회 필요.
- `/pilot:doctor` — 갱신 후 정합성 점검 (자동 호출됨).
- 구조 결정 휴리스틱 상세: [`references/heuristics.md`](references/heuristics.md).
- file:line 인용은 `/pilot:doctor` 의 mtime drift 감지 기반 — 코드가 변하면 stale 경고가 뜬다.
