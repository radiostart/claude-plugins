# learn — cross-domain detect & MANIFEST 갱신

`/pilot:learn` 의 Phase 2 ~ Phase 5 에 걸친 외부 도메인 reference 추출·transaction nesting detect·MANIFEST 갱신 알고리즘. 본문 SKILL.md 의 분량을 줄이기 위해 분리. 절차 자체는 본문에 짧게 호출되며 상세는 여기에 둔다.

---

## Phase 2 — 외부 도메인 클래스 reference 추출 (#09)

의존성 추적 중 발견된 클래스/모듈 reference 를 내부 vs 외부로 분류한다.

- **내부 판정**: 진입점에서 추론된 본 도메인 namespace prefix 와 일치 (예: 진입점이 `app/services/<domain>/` 이면 `<Domain>::*` namespace 가 내부).
- **외부 후보**: 그 외 namespace 첫 segment 가 있는 reference (예: `<OtherDomain>::<ClassName>`).
- **ignore 패턴 필터**: 외부 후보에서 standard library / framework 클래스를 제외한다.

  > **config lookup**: `workspace/context/config.md` 의 `## learn 외부 도메인 ignore 패턴` 섹션을 먼저 조회. 섹션·행이 없으면 아래 Ruby default 12 항목을 사용:
  > `ActiveRecord::Base`, `ApplicationRecord`, `String`, `Hash`, `Array`, `Integer`, `Float`, `Symbol`, `Time`, `Date`, `BigDecimal`, `Set`
  >
  > **A2 runtime fallback**: namespace 추출 실패 시 (예: 클래스명에 `::` 없어 도메인 추정 불가) → 해당 클래스 무시 + `[WARN] 외부 클래스 namespace 추출 실패: {class_name} — 수동 확인 권장` 1 줄. abort 하지 않는다.

- 필터 후 남은 외부 클래스 목록을 **메모리에 누적** (추정 도메인별 grouping). Phase 5 의 MANIFEST 갱신에서 사용.

---

## Phase 3 — cross-domain transaction nesting

outer / inner transaction 의 receiver 가 다른 도메인 namespace 이면 nesting detect:

- inner transaction block 안의 외부 클래스 메서드 호출 (`update` / `destroy` / `find` / `create`) 추출.
- 변경 type 매핑: `update` → `write`, `destroy` → `destroy`, `find` / `where` / `select` → `read`, `create` / `insert` → `create`.
- **본 도메인 nested transaction 은 제외** — receiver namespace 가 본 도메인과 동일하면 캡처 안 함. 외부 namespace 만 캡처.
- A2 runtime fallback: namespace 판별 불가 시 해당 호출 단순 무시 + WARN 1 줄 (`[WARN] transaction nesting detect 실패 — 수동 확인 권장`). 나머지 추출 정상 진행.
- 추출 결과를 메모리의 `cross_domain_transactions` 카테고리에 누적 (Phase 4 에서 sub-section 생성에 사용).

Grep 패턴 (라인 번호 수집용):

| 추출 대상 | Grep 패턴 |
| --------- | --------- |
| transaction nesting (cross-domain) | `\.transaction\s*do\s*$\|ActiveRecord::Base\.transaction\|\w+Record\w*\.transaction` — 매치 시 ±20 줄 추가 Read |

---

## Phase 4 — Cross-domain Transaction Contracts sub-section

Phase 3 에서 누적된 `cross_domain_transactions` 결과 사용:

- `cross_domain_transactions` 가 비어있음 (0 건) → sub-section 자체 추가 안 함. 단일 DB 시스템이거나 cross-domain transaction 없는 경우 정상.
- 1 건 이상이면:
  - `{domain}/index.md` (폴더 도메인) 또는 `{domain}.md` (단일 파일 도메인) 의 `## 다중 DB` 섹션 직후에 sub-section 삽입.
  - `## 다중 DB` 섹션 자체가 없으면 H2 `## 다중 DB` + sub-section 을 한 번에 추가.
  - sub-section 형식:

    ```markdown
    ### Cross-domain Transaction Contracts

    | 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |
    | --- | --- | --- | --- |
    | `<DomainA>::<ServiceClass>#<method>` | `<DomainB>::<ExternalClass>` field / `<OtherClass>` destroy | write·destroy | service_file.rb:NN-MM |
    ```

  - **변경 type 화이트리스트**: `read`, `write`, `destroy`, `create` 및 `·` 구분 조합 (예: `write·destroy`).
  - **inline vs 분리 룰**:
    - 표 데이터 행이 **5 행 이상** → `{domain}/transaction-contracts.md` 별도 파일로 분리. index.md 에 `→ [Cross-domain Transaction Contracts]({domain}/transaction-contracts.md)` 링크만 유지.
    - **5 행 미만** → `## 다중 DB` 섹션 직후 inline 유지.
  - **idempotency**: 두 번째 `/pilot:learn` 호출 시 자동 detect 행은 갱신 (기존 행 대체), 사용자 수동 추가 행 (` (auto)` 마커 없는 행) 은 보존. 자동 detect 행 끝에 ` (auto)` 마커 (선택).
  - **A2 runtime fallback**: detect 알고리즘 실패 시 → sub-section 헤더 + `| (자동 detect 실패 — 수동 작성 권장) | | | |` placeholder. abort 안 함.

---

## Phase 5 — MANIFEST.md 외부 도메인 reference 섹션 갱신 (#09·#10)

Phase 2 에서 누적된 외부 클래스 목록을 처리한다.

**idempotency — 현재 learn 도메인의 stale row 제거:**

- 현재 learn 의 `{domain}` 이 MANIFEST 의 `## 외부 도메인 reference` 표에 행으로 존재하면 그 행을 제거한다 (이미 학습됨 — 더 이상 "미완료" 아님).

**외부 클래스 목록이 0 이면:** 섹션 자체를 추가하지 않는다 (빈 섹션 방지). 이미 존재하는 섹션은 그대로 유지.

**외부 클래스 목록이 1 이상이면:**

- 추정 도메인별 grouping: Ruby `Module::Class` namespace 의 첫 segment 를 **CamelCase → snake_case 로 변환** (예: `ApiExceptions::Custom` → `api_exceptions`, `OrderModule::Foo` → `order_module`). namespace 없는 클래스는 skip.
  - 변환 규칙: 대문자 앞에 `_` 삽입 (단어 첫 글자 제외) 후 전체 소문자화. 연속 대문자 (`XMLParser` → `xml_parser`) 도 동일 규칙.
- 추정 도메인이 이미 `## 도메인 분류` 표에 등록된 도메인이면 제외 (이미 학습됨).
- 추천 경로 탐색: 사용자 코드베이스 root 에서 `app/{models,services,controllers}/{추정 도메인}/` 패턴 Glob. 존재하면 그 경로, 없으면 `(경로 자동 추정 실패 — 사용자 직접 지정)`.
- MANIFEST 의 `## 외부 도메인 reference (learn 미완료)` 섹션이 이미 존재하면:
  - 같은 추정 도메인 행이 있으면 클래스 목록·개수 갱신 (행 내용 교체). 사용자 수동 추가 행은 보존.
  - 없으면 새 행 추가 (행 끝에 ` (auto)` 마커).
- 섹션이 없으면 새 섹션 + 표 생성:

  ```markdown
  ## 외부 도메인 reference (learn 미완료)

  | 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |
  | --- | --- | --- |
  | {추정 도메인} | {Class1}, {Class2}... ({N}) | `/pilot:learn {추천 경로}` 또는 `/pilot:learn --boundary {추정 도메인} --from {domain}` (auto) |
  ```

  - 추천 컬럼은 두 경로를 함께 제시한다 — 전체 학습 (`/pilot:learn {추천 경로}`) 과 경계만 학습 (`--boundary`). 경로 자동 추정 실패 시 전체 학습 안내는 `(경로 자동 추정 실패 — 사용자 직접 지정)` 으로 대체하되 boundary 안내는 유지.

> **A2 runtime fallback**: 추정 도메인 추출 전체 실패 시 → 섹션 작성 skip + `[WARN] 외부 도메인 reference 추출 실패 — 수동 관리 권장` 1 줄. learn 본 작업은 정상 종료.

---

## Boundary 모드 — 호출 표면 추출 (`--boundary {B} --from {A}`)

SKILL.md § Boundary 모드의 상세 절차. Phase 2 의 detect 와 Phase 3 의 transaction nesting 알고리즘을 재사용한다.

### 1. 호출처 수집

- `{A}` 의 소스 파일 목록 확보: MANIFEST `## 도메인 분류` 의 `{A}` 진입 파일이 인용하는 `file:line` 경로들 + 해당 파일들에 Phase 2 의존성 추적 패턴 적용 (depth 1).
- 그 파일들에서 `{B}` namespace reference 를 Grep (예: `<B의 CamelCase>::`). `## learn 외부 도메인 ignore 패턴` 동일 적용.
- **호출처 0 건** → "경계 없음: {A} 는 {B} 를 직접 호출하지 않음" 보고 후 종료. 파일을 생성하지 않는다.

### 2. 표면 추출

- 각 호출처 라인 ±10 줄 Read — 호출 메서드·인자 형태·반환값 사용 방식 수집.
- `{B}` 의 정의 파일 탐색: `app/{models,services,controllers}/{B}/` 패턴 Glob (Phase 5 추천 경로와 동일 휴리스틱). 발견 시 **호출된 심볼의 시그니처·관련 상태값만** Targeted Read (Phase 3 의 Grep 패턴 재사용). 미발견 시 호출부 사용 형태만으로 기록하고 `정의 (B)` 컬럼은 `(미확인)`.
- transaction nesting: Phase 3 알고리즘을 호출처 파일에 적용, `{B}` receiver 만 캡처.

### 3. 산출 형식 — `workspace/context/boundaries/{A}--{B}.md`

본문 ≤ 150 줄. 추측 금지 — 모든 행에 `file:line` 인용. 파일명 구분자는 `--` 고정 (도메인명은 sanitize 로 `--` 미포함 보장).

```markdown
# 경계 계약: {A} → {B}

> `/pilot:learn --boundary` 생성. {A} 가 실제 호출하는 {B} 표면만 기록 — {B} 전체 학습이 아니다.
> 전체 학습: `/pilot:learn {B 추천 경로}` (완료 시 본 문서보다 도메인 산출물이 우선)

## 호출 표면

| {B} 심볼 | 사용 형태 (인자 → 반환) | 호출처 ({A}) | 정의 ({B}) |
| --- | --- | --- | --- |

## 상태값·상수 (관찰된 것만)

## 트랜잭션 중첩 (해당 시)

| 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |

## 미해결 (코드만으로 불명)

- (없음) 또는 전체 learn·사용자 확인이 필요한 항목
```

### 4. 색인·idempotency

- MANIFEST `## 외부 도메인 reference` 표에 `{B}` 행이 있으면 추천 컬럼 끝에 ` · 경계: {A}--{B}.md` 표기를 추가한다. **행을 제거하지 않는다** — 행 제거는 전체 learn 완료의 신호다 (Phase 5 idempotency).
- 같은 `{A}--{B}` 재실행 시 파일 전체 재생성 (diff 모드 없음 — 본 스킬 공통 제약).
- 로드는 orchestrate-load 의 boundaries 글롭이 담당 — MANIFEST 도메인 분류에 등록하지 않는다.

> **A2 runtime fallback**: 표면 추출 중 심볼 정의 탐색 실패·namespace 판별 실패는 해당 항목을 `미해결` 섹션으로 내리고 진행. abort 하지 않는다.
