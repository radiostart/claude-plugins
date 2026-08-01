# Plan 파일 스키마 (`features/NN-{slug}.plan.md`)

Planner 가 작성하고 Generator 가 Read 하는 plan 파일의 **형식 계약**.
모드별 필수 섹션·필드를 정의하며, `tools/plan-validate.py` 가 이 스펙을 강제한다.

> **검증 대상은 형식만** — 내용 품질·계약 의미 검증은 Evaluator 의 책임.

## 모드 결정

호출자(wrapper)가 `orchestrate-load.py` 결과의 `tdd` / `mode` 를 읽어 다음 표로 매핑한다.

| `mode` | `tdd` | 적용 스키마 |
|---|---|---|
| `characterize` | (무시) | **characterize** |
| 미설정 | `true` | **tdd** |
| 미설정 | `false` 또는 미설정 | **standard** |

`mode: characterize` 와 `tdd: true` 동시 설정 시 우선순위(characterize 우선)는 [`modes/characterize.md`](../modes/characterize.md):10 이 정본이다.

## 공통 요건 (모든 모드)

- 파일 인코딩: UTF-8
- 최소 1개의 마크다운 제목 라인 (H1·H2·H3 등) 존재
- 빈 파일 / 제목 없음 → `invalid`

> **설계 원칙**: 본 스키마는 doc-level 형식을 느슨하게, **step-level 라벨을 엄격하게** 검증한다. 실제 운영 plan 들이 자유로운 doc 구성 (포착 대상 요약·기획 §·경계 노트 등 인라인 섹션 다양) 을 사용하므로, 형식 강제는 step 단위에서만 의미가 있다고 판단.

## standard 모드

근거: [`agents/pilot-planner.md`:64-88](../../../agents/pilot-planner.md)

### 필수 섹션

없음. doc-level 자유 형식 (Planner 가 출력 양식을 따르길 권장하지만 강제하지 않음).

### 권장 섹션 (검증 대상 아님)

- `### 변경 파일`
- `### 구현 순서`
- `### 주의사항`
- `### 교차 의존` — 다른 feature 영향 발견 시에만

### 스텝 단위 요건

없음.

## tdd 모드

근거: [`modes/rgr.md`:50-77](../modes/rgr.md)

### 필수 H3 섹션

- `### 스텝 목록` — 정확 일치 (characterize 의 `### 스텝 목록 (Characterization Contract)` 와 구분).
  스텝이 정의된 섹션은 검증의 핵심 — 누락은 fail.

### 스텝 단위 필수 필드

`### 스텝 목록` 안의 각 번호 항목(`1. **[스텝 N]** ...`)에 다음 라벨이 본문 어딘가에 존재해야 한다:

- `테스트 대상:`
- `검증할 행동:`
- `기대 실패 유형:`

스텝 0개 → `invalid` (최소 1 스텝).

## characterize 모드

근거: [`modes/characterize.md`:30-53](../modes/characterize.md)

### 필수 H3 섹션

- `### 스텝 목록 (Characterization Contract)` — 정확 일치 필요.

### 스텝 단위 필수 필드

각 번호 항목에 다음 라벨 필수:

- `테스트 대상:`
- `입력:`
- `현재 출력:` — Planner 단계에선 `Generator 실행 예정` 등 placeholder 허용
- `관찰된 사이드 이펙트:`

`탐지 불가 가능성 영역:` 은 선택 (해당 시).

### 권장 (검증 대상 아님)

- 파일 최상단에 `# #N {제목} — Characterization Contract` 형식의 H1 (실제 운영 plan 의 통상 패턴).
- mode·source·planner_at 등 frontmatter 인용구.

## 분량 가드 (모든 모드 공통 — WARN, 비차단)

plan 은 Generator·Critic·Evaluator 가 매 라운드 전문을 Read 하는 인계 문서다. 분량 초과는 후속 에이전트의 컨텍스트 윈도우를 선소모하므로 plan-validate 가 WARN 으로 보고한다. exit code 는 불변 — 차단하지 않는다.

| 검사 | 임계 | 근거 |
|---|---|---|
| 본문 길이 | 30,000자 초과 | ≈ 토큰 10~15k — 한 라운드 인계 문서 상한. 초과분은 대부분 회차 이력 잔재 |
| 최장 라인 | 1,500자 초과 | Read 툴 라인 절단(2,000자) 안전 마진 |

WARN 시 planner 는 회차 이력 잔재 — `N차 갱신`·`N회차 개정` 헤더, `[C# 해소]`·`1회차 대비 정정` 류 주석, 기각된 대안의 장문 사유 — 를 제거하고 **최신 확정 상태만** 남긴다. 반영·기각·이월 disposition 의 기록처는 critic 합의 표(현 회차)다 — 회차 간 이력은 git (형식: pilot-planner-critic 출력 `## 합의` 표 / 채움: pilot-planner 재호출 단계).

## 호출

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/plan-validate.py \
  features/NN-{slug}.plan.md \
  --mode {standard|tdd|characterize}
```

- exit 0 = valid
- exit 1 = invalid — stderr 에 누락 항목 출력, stdout 에 JSON 진단
- `[WARN]` (stderr, exit 불변) = 분량 가드 초과 — § 분량 가드 처리

JSON 형식:

```json
{
  "valid": false,
  "mode": "tdd",
  "missing_sections": ["### 스텝 목록"],
  "step_errors": [
    {"step": 2, "missing_fields": ["기대 실패 유형"]}
  ]
}
```

## 호출 지점

- **Planner** wrapper step 6 — plan 저장 직후. 실패 시 사용자에게 보고하고 plan 보완.
- **Generator** wrapper step 2 — plan Read 직전. 실패 시 Planner 재호출 요청 (구현 시작 금지).

## 변경 시

본 스키마 변경은 다음 파일과 동기화:

- `tools/plan-validate.py` — 검증 로직
- `tests/tools/test_plan_validate.py` — 회귀 테스트
- `agents/pilot-planner.md` step 6, `agents/pilot-generator.md` step 2 — 호출 지점
- 본 인덱스의 `INDEX.md` 표 — 본 문서 행 추가
