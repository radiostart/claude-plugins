---
name: analyze
description: >-
  이미 저장된 docs/ 기획서를 features/ 기능 명세로 분할·구조화할 때 사용한다.
  PM 작성 표 중심 기획서를 기능 단위 문서로 변환하고 project.md 의 목표 섹션
  과 agents/ 파일(planner·generator·evaluator)을 자동 갱신한다. 기획서 fetch 는
  `/pilot:confl`, 프롬프트 기반 단일 기능 추가는 `/pilot:create-feature`
  를 사용한다.
---

# /pilot:analyze

Confluence 기획서(docs/)를 분석하여 기능별 구조화된 명세(features/)를 생성한다.
PM이 작성한 표 중심 기획서를 AI가 읽기 쉬운 형태로 변환한다.

대상: $ARGUMENTS

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0, P1** 수행.

- P-1: TodoWrite 선로딩 (다단계 스킬).
- P0: `{PROJECT}` 와 `$ARGUMENTS` 키워드로 memory-hint 실행. 출력된 메모를 Read 하여 과거 분석·구현 이력 확인.
- P1: `{PROJECT}` 획득. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

추가: `workspace/projects/{PROJECT}/docs/` 폴더를 Glob 으로 확인한다.

- 폴더가 없거나 `.md` 파일이 없으면 [messages.md](../context/shared/messages.md) 의 `docs_missing` 출력 후 종료.

---

## 인자 판별

`$ARGUMENTS`에서 `--force` · `--regen-agents` 플래그를 먼저 분리하고, 나머지 텍스트로 모드를 결정한다.

| 플래그 / 나머지 텍스트 | 모드 | 동작 |
| ---------------------- | ---- | ---- |
| `--regen-agents` (단독) | **재생성 전용** | docs/features 변화 여부와 무관하게 현재 features/ 기반으로 `agents/*.md` 만 재작성. 상세: [`references/regen-mode.md`](references/regen-mode.md) |
| 없음 (빈 문자열) | 전체 분석 | docs/ 내 **모든** 원본 파일의 전체 내용 분석 |
| 파일명 또는 page_id | 파일 지정 | 해당 파일만 분석 |
| 그 외 텍스트 (키워드) | 필터 분석 | docs/ 전체 파일에서 **키워드 관련 기능만** 추출하여 분석 |

### 필터 분석 모드

기획서에는 프론트엔드, API, 관리자 등 여러 영역의 기능이 혼재되어 있다.
키워드가 주어지면 docs/ 전체 파일을 읽되, **키워드와 관련된 섹션만** 추출하여 features/ 파일을 생성한다.

- 예: `/pilot:analyze 관리자 기능` → 관리자(어드민) 관련 기능만 분석
- 예: `/pilot:analyze 결제` → 결제 영역 기능만 분석
- 키워드 매칭은 섹션 제목과 내용 모두에서 판단한다.
- 관련 없는 섹션은 스킵한다.

---

## 분석 프로세스

### 1. 대상 파일 결정

- `workspace/projects/{PROJECT}/docs/*.md` 에서 원본 파일 목록을 수집한다.
- `--force` 가 없으면: `features/` 폴더에 이미 분석 파일이 존재하는 원본은 스킵한다.
  - 스킵 판단: features/ 파일 상단 `> source:` 메타데이터에 원본 파일명이 기록됨
- 분석 대상이 없으면 [messages.md](../context/shared/messages.md) 의 `analyze_all_done` 출력 후 종료한다.

#### `--force` 실행 시 prompt-origin 보호

`--force` 는 기존 features/ 파일을 덮어쓸 수 있다. 그 전에 `/pilot:create-feature` 로 생성된 **prompt-origin features** 가 있는지 확인하고 사용자에게 승인받는다 (자동 진행 시 사용자 의도로 만든 기능 명세가 소리 없이 사라져 데이터 손실로 직결되기 때문):

1. `features/*.md` 를 Grep 하여 `> source: prompt` 태그가 있는 파일 목록 수집
2. 1 건 이상 있으면 사용자에게 경고 + 승인 대기:

   ```
   ⚠ --force 재분석이 prompt-origin features 를 덮어쓸 가능성이 있습니다:
     - features/05-refund-policy.md (source: prompt)
     - features/07-notification-queue.md (source: prompt)

   이 파일들은 /pilot:create-feature 로 생성됐으며, docs/ 에 대응 원본이
   없습니다. --force 진행 시 slug 충돌이 발생하면 덮어쓰여 데이터가 손실될
   수 있습니다. 계속? (y/n)
   ```

3. 사용자 `n` → 종료. `y` → 진행. 명시 승인 없이 자동 진행하지 않는다.

0 건이면 이 절차를 건너뛴다.

### 2. 원본 파일 읽기

- 대상 파일을 Read 툴로 로드한다.
- **항상 먼저 수행 (default path, 실패 대응 아님)**:
  1. `confluence.py fetch` 출력 또는 `wc -l {path}` 로 파일 크기·라인 수 확인.
  2. Grep `^##+` 으로 전체 H2/H3 라인 번호 수집 (문서 구조 파악).
  3. 사용자 필터 (다운로드된 docs 의 실제 H2 키워드 2~4개를 예시로 노출 후 사용자 선택) 또는 키워드 매칭으로 관심 H2 섹션 결정.
  4. 각 관심 섹션을 **targeted Read**.
- **파일 크기 분기** (Read 툴 25k 토큰 한도 대응 — 실전 기획서는 표가 많아 300KB 이상 빈번):

  | 파일 크기 | 토큰 추정 | 권장 Read 전략 |
  | --------- | --------- | -------------- |
  | **소형** ≤ 50KB | ≤ 5k | 전체 1 회 Read 가능 |
  | **중형** 50 ~ 150KB | 5k ~ 15k | H2 목차 + 섹션 단위 Read (limit 150) |
  | **대형** > 150KB | > 15k | 섹션 단위 targeted Read (limit **80** — 표 많은 문서 보수적 기본값) |

- **Read rejection 발생 시 재시도 규칙**: `limit` 을 **1/3 로 축소** (1/2 는 대형 파일에서 재실패 확률 높음 — 실측). `offset` 유지.
- **추측 금지 원칙 유지:** 읽지 않은 섹션은 features/ 생성 대상에서 제외. 전체 스캔하지 않았다면 **사용자에게 범위 보고** 후 확정.
- 사용자가 "전체 분석" 을 요청했는데 파일이 대형이면 H2 목차 기반으로 모든 섹션을 순회하여 빠짐없이 커버.

### 3. 기능 분할 및 구조화

원본 문서를 아래 기준으로 기능 단위로 분할한다:

**분할 기준:**

- H2(`##`) 섹션을 기능 단위로 인식
- 번호 패턴(`#N`, `N.`, `N)`)이 있으면 기능 번호로 사용
- 번호가 없으면 순차 번호 부여

**각 기능에서 추출할 항목:**

```markdown
# #{번호} {기능명}

> source: {원본 docs 파일명}

## 요구사항

각 요구사항을 아래 구조로 정리한다:

- **조건**: 이 기능이 동작하기 위한 전제 조건
- **트리거**: 이 기능을 실행시키는 사용자 액션 또는 시스템 이벤트
- **기대결과**: 실행 후 예상되는 결과 (UI 변경, 데이터 변경, 알림 등)

## 상태 전환

상태값 변경이 포함된 경우만 작성한다:

| 전환 전 | 전환 후 | 조건 | 처리 |
| ------- | ------- | ---- | ---- |

## 비즈니스 규칙

- 검증 조건, 제약사항, 계산 로직 등을 목록으로 정리
- 표로 정의된 규칙은 표 형태를 유지하되, 행/열 의미를 명확히 보완

## 예외 케이스

- 정상 흐름에서 벗어나는 케이스를 목록으로 정리
- 각 케이스의 조건과 처리 방법을 명시
```

**분석 시 주의사항:**

- 원본의 표(table)는 의미를 해석하여 서술형으로 풀어쓰되, 상태 전환표처럼 표 형태가 더 명확한 경우는 표를 유지한다.
- 원본에 없는 내용을 추측하여 추가하지 않는다 (한 번 추측이 들어가면 후속 6 단계의 agents/ 갱신·planner·generator 가 모두 잘못된 사실을 기반으로 동작한다).
- Figma 링크 등 디자인 참조는 유지한다.
- 하나의 H2 섹션이 여러 기능을 포함하면 기능별로 분리한다.

### 4. 파일 저장

- 저장 경로: `workspace/projects/{PROJECT}/features/`
- 기능 명세 파일명: `{NN}-{slug}.md`
  - `NN`: 기능 번호 (2자리 zero-padding, 예: `12`, `13`)
  - `slug`: 기능명을 kebab-case로 변환 (한글 허용, 특수문자 제거, 최대 30자)
  - 예: `13-order-modal.md`, `19-receipt-list.md`
- **배치 저장 (병렬 Write)** — features 파일은 서로 독립이므로, 동일 assistant turn 안에 여러 Write tool_use 를 묶어 호출한다. harness 가 병렬 실행한다. 실무상 **3~5 개 단위 묶음** 이 현실적 (파일당 사고 비용 > I/O 비용). 10 개 이상을 한 번에 묶으면 컨텍스트가 혼잡해지므로 분할 권장.

### 5. project.md 자동 갱신

features/ 생성 후 `project.md` 의 `## 목표` 와 `## 관련 파일` 을 자동 동기화한다.

**도메인 결정 (5-1, 5-2 공통 전제):**

아래 우선순위로 결정한다. 자동 판정은 **후보 제시용** 으로만 사용하고 기록은 항상 사용자 확인을 거친다 (한 번 잘못 기록되면 후속 분석이 전부 오염되며 되돌리려면 features 전체 재분석이 필요하다).

1. `.agent-state.yml` 의 `domain` 이 non-null → 그대로 사용 (이미 확정된 값).
2. null 이면:
   - (a) `project.md` 제한사항 섹션에서 `- domain: {x}` 라인 파싱 시도. 성공 시 후보로 채택.
   - (b) 실패 시 `workspace/context/MANIFEST.md` 의 도메인 분류 테이블과 프로젝트명·features 키워드로 매칭하여 후보 제시.
   - (c) 사용자에게 질의:

     ```
     이 프로젝트의 도메인을 확인해주세요.
     자동 판정 후보: {후보} (근거: {근거 한 줄})
     선택지: MANIFEST.md 의 도메인 분류에 정의된 값 또는 새 도메인명 입력
     ```

   - 사용자 응답을 `.agent-state.yml` 의 `domain` 필드에 Edit 로 기록.
3. 결정된 도메인으로 `workspace/context/scope/{domain}.md` 를 Read.

#### 5-1. `## 목표` 갱신

1. `workspace/projects/{PROJECT}/project.md`를 Read한다.
2. `## 목표` 섹션을 찾는다 (없으면 `## 에이전트 호출 흐름` 바로 앞에 생성한다).
3. 생성된 features/ 파일 목록을 기준으로 목표 체크리스트를 갱신한다:
   - **신규 feature:** `- [ ] {기능명} -> [상세](features/{NN}-{slug}.md)` 항목을 추가한다.
   - **기존 항목 유지:** 이미 `[x]`로 완료 처리된 항목은 변경하지 않는다 (사용자가 이미 끝낸 일을 미완료로 되돌리면 진행 상황이 거꾸로 보임).
   - **삭제된 feature:** `--force` 재분석으로 features/ 파일이 교체된 경우, 기존 항목 중 대응하는 features/ 파일이 없는 항목은 제거한다.
4. 목표 항목 순서는 features/ 파일의 번호(NN) 순서를 따른다.

**갱신 예시:**

```markdown
## 목표

- [x] Order 모델 생성 및 관계 설정 -> [상세](features/01-order-model.md)
- [ ] 주문 생성 API -> [상세](features/02-order-create-api.md)
- [ ] 주문 취소 API -> [상세](features/03-order-cancel-api.md)
```

#### 5-2. `## 관련 파일` 갱신

로드한 `scope/{domain}.md` 의 `## Routes`, `## Models`, `## Services` 표를 추출해 project.md 의 `## 관련 파일` 표를 자동 기입한다.

**프로세스:**

1. project.md 의 `## 관련 파일` 섹션을 찾는다 (없으면 `## 에이전트 호출 흐름` 뒤에 GUIDE.md 템플릿대로 생성한다).
2. **Endpoints 표** — scope 의 `## Routes` 에서 행을 뽑아 `| 엔드포인트 | Method | 목적 |` 형식으로 기입한다.
   - features/ 요구사항과 관련된 route 를 우선 선별한다 (경로·목적 키워드 매칭).
   - 매칭이 불명확하면 도메인 전체 Routes 를 포함한다 (best-effort).
3. **Models 표** — scope 의 `## Models` 에서 `| Class | DB | 목적 |` 형식으로 기입한다.
4. **Services 표** — scope 의 `## Services` 에서 `| Class | 파일 | 목적 |` 형식으로 기입한다.

**갱신 규칙:**

- features/ 에 명시적으로 언급된 모델·서비스·라우트는 빠뜨리지 않고 포함한다 (누락 시 planner 가 영향 범위를 잘못 잡아 후속 작업이 어긋남).
- scope 에 없지만 features/ 에 등장한 신규 대상은 추가하되 `목적` 열 끝에 `(from features/NN-{slug})` 주석을 붙인다.
- 기존 사용자 수동 기입 행은 보존하되 중복만 제거한다.
- 빈 행(`|  |  |  |`) 은 모두 삭제한다.
- scope 파일에 해당 섹션이 비어있거나 없으면 해당 표는 건너뛰되, 표 헤더는 유지한다.

### 6. agents/ 자동 갱신

features/ 분석 결과로 `agents/planner.md`, `agents/generator.md`, `agents/evaluator.md` 를 갱신하고 `.agent-state.yml` 의 `analyzed: true` 게이트를 켠다.

상세 절차 (6-1 ~ 6-5): [`references/agents-update.md`](references/agents-update.md).

### 7. 분석 품질 자가 검증

6-5 (doctor) 가 끝나면 분석 내용 자체의 품질을 4 항목 (커버리지·구조·정합성·추측 혐의) 으로 자가 점검한다.

상세 절차 (7-1 ~ 7-4) + 출력 형식: [`references/self-verify.md`](references/self-verify.md).

### 8. 결과 출력

분석 완료 후 아래 형식으로 요약한다:

```
분석 완료: {원본 파일명}

생성된 features:
  - features/{NN}-{slug}.md — {기능명}
  ...

총 {N}개 기능 명세 생성.

갱신된 파일:
  - project.md — 목표 {N}개 동기화 + 관련 파일(Models/Endpoints/Services) 자동 기입
  - agents/planner.md — 기능별 사전 확인 사항 갱신
  - agents/generator.md — 기술 레퍼런스 갱신
  - agents/evaluator.md — 체크리스트 갱신
  - .agent-state.yml — analyzed: true

검증: {7 단계 요약 한 줄 — "all checks passed" 또는 "WARN N건" 등}
```

---

## 참고

- `features/` 파일은 프로젝트 에이전트(@planner, @generator)가 직접 Read하여 사용한다.
- `docs/` 파일은 원본 보관용이며 `/pilot:confl` 커맨드를 통해서만 접근한다.
- 분석 품질이 낮으면 `/pilot:analyze --force` 로 재분석할 수 있다.
- TDD 모드에서는 @planner 가 Red 단계에서 `features/NN-{slug}.md` 를 직접 읽어 실패 테스트를 작성한다 (상세: [`rgr.md`](../context/modes/rgr.md)).
