---
name: analyze
description: >-
  이미 저장된 docs/ 기획서를 features/ 기능 명세로 분할·구조화할 때 사용한다.
  PM 작성 표 중심 기획서를 기능 단위 문서로 변환하고 project.md 의 목표 섹션
  과 prompts/ 파일(planner·generator·evaluator)을 자동 갱신한다. 기획서 fetch 는
  `/pilot:confl`, 프롬프트 기반 단일 기능 추가는 `/pilot:create-feature`
  를 사용한다.
---

# /pilot:analyze

Confluence 기획서(docs/)를 분석하여 기능별 구조화된 명세(features/)를 생성한다.
PM이 작성한 표 중심 기획서를 AI가 읽기 쉬운 형태로 변환한다.

대상: $ARGUMENTS

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0, P1** 수행 (실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료). `workspace/projects/{PROJECT}/docs/` 를 Glob 확인 — 없거나 `.md` 파일 없으면 `docs_missing` 출력 후 종료.

## 인자 판별

`$ARGUMENTS`에서 `--force` · `--regen-agents` 플래그를 먼저 분리하고, 나머지 텍스트로 모드를 결정한다.

| 플래그 / 나머지 텍스트 | 모드 | 동작 |
| ---------------------- | ---- | ---- |
| `--regen-agents` (단독) | **재생성 전용** | docs/features 변화와 무관하게 현재 features/ 기반으로 `prompts/*.md` 만 재작성. [`references/regen-mode.md`](references/regen-mode.md) |
| 없음 (빈 문자열) | 전체 분석 | docs/ 내 **모든** 원본 파일의 전체 내용 분석 |
| 파일명 또는 page_id | 파일 지정 | 해당 파일만 분석 |
| 그 외 텍스트 (키워드) | 필터 분석 | 섹션 제목·내용에서 키워드 매칭되는 부분만 추출 (관련 없는 섹션은 skip) |

## 분석 프로세스

### 1. 대상 파일 결정

- `docs/*.md` 원본 목록 수집. `--force` 없으면 features/ 상단 `> source:` 메타데이터로 이미 분석된 원본을 스킵.
- 분석 대상이 없으면 [messages.md](../context/shared/messages.md) 의 `analyze_all_done` 출력 후 종료.
- **`--force` prompt-origin 보호**: `> source: prompt` 태그를 Grep 하여 1 건 이상이면 경고 + y/n 승인 게이트 (`n`/미응답 시 종료). 상세: [`references/scope-sync.md`](references/scope-sync.md) `--force prompt-origin 보호`.

### 2. 원본 파일 읽기

파일 크기에 따라 전체 Read(≤50KB) · H2 목차 + 섹션 단위 Read(50~150KB, limit 150) · 섹션 단위 targeted Read(>150KB, limit **80**) 로 나눠 읽는다. **Read rejection 시 limit 1/3 축소** (표 중심 문서 — learn 의 소스 코드 1/2 규칙과 의도된 차이). **추측 금지**: 읽지 않은 섹션은 생성 대상에서 제외하고, 전체 스캔하지 않았으면 사용자에게 범위 보고 후 확정.

### 3. 기능 분할 및 구조화

**분할 기준:** H2(`##`) 섹션을 기능 단위로 인식. 번호 패턴(`#N`·`N.`·`N)`) 있으면 기능 번호로, 없으면 순차 부여.

각 기능은 `# #{번호} {기능명}` + `> source: {원본 파일명}` + `## 요구사항`(조건/트리거/기대결과) + `## 상태 전환`(표) + `## 비즈니스 규칙` + `## 예외 케이스` 섹션으로 작성한다. 원본 표는 서술형으로 풀되 상태 전환표는 표 유지. **원본에 없는 내용 추측 금지** (한 번 추측이 들어가면 후속 prompts/·planner·generator 가 오염된다). 하나의 H2 가 여러 기능을 포함하면 기능별로 분리.

### 4. 파일 저장

`workspace/projects/{PROJECT}/features/{NN}-{slug}.md` (`NN` 2자리 zero-pad, `slug` kebab-case 최대 30자). 여러 파일은 [coding.md](../context/shared/coding.md) `## 독립 파일 배치 작업` 절차로 병렬 Write.

### 5. project.md 자동 갱신

**도메인 결정 (5-1·5-2 공통 전제):** `.agent-state.yml.domain` 이 non-null 이면 그대로 사용. null 이면 (a) project.md 제한사항 파싱 → (b) MANIFEST 분류 + 키워드 매칭 후보 → (c) 사용자 질의 후 Edit 로 기록 (자동 판정은 후보 제시용만 — 기록은 항상 사용자 확인). 결정 후 `scope/{domain}.md` Read.

#### 5-1. `## 목표` 갱신

신규 feature 는 `- [ ] {기능명} -> [상세](features/{NN}-{slug}.md)` 추가, `[x]` 완료 항목은 불변, `--force` 로 대응 파일이 사라진 항목은 제거. 순서는 features NN 순.

#### 5-1.5. scope/{domain}.md 자동 생성

scope 부재 + MANIFEST 진입파일에 매칭 H2 존재 시 자동 생성. 상세(본문 구성·idempotency·예외·A2): [`references/scope-sync.md`](references/scope-sync.md) `5-1.5`.

#### 5-2. `## 관련 파일` 갱신

`scope/{domain}.md` 매칭 H2 표를 추출해 project.md `## 관련 파일` 표를 채운다. **핵심 규칙** — features/ 에 명시된 모델·서비스·라우트는 누락 금지(from features/NN-{slug} 주석으로 신규 추가), 사용자 수동 행 보존(중복만 제거), 빈 행 삭제. config lookup·default·cross-domain detect(#09)·Open Questions 보존(#11) 상세: [`references/scope-sync.md`](references/scope-sync.md) `5-2`.

### 6. prompts/ 자동 갱신

`prompts/{planner,generator,evaluator}.md` 갱신 + `.agent-state.yml.analyzed: true` 게이트. 상세(6-1~6-5): [`references/prompts-update.md`](references/prompts-update.md).

### 7. 분석 품질 자가 검증

6-5(doctor) 완료 후 4 항목(커버리지·구조·정합성·추측 혐의) 자가 점검. 상세+출력 형식: [`references/self-verify.md`](references/self-verify.md).

### 7.5 조건부 인터뷰 — 신규 features Open Questions 일괄 소비 (#17)

대상은 **이번 실행에서 신규 생성된 features 만** (`--regen-agents` 는 신규 생성이 없으므로 미발동). 절차: (1) 산출물 대조 — 5 단계에서 이미 Read 한 `scope/{domain}.md` 재사용 (2) (d)>(b)>(c)>(a) 우선순위 + 파일 NN 순 정렬, 최대 8 문항 일괄 질의 (3) 답변 반영 후 `- [x] {원문} → {답변 요약}` 체크. 상세(행 파싱·상한 산술): [`../context/shared/interview.md`](../context/shared/interview.md).

### 8. 결과 출력

`분석 완료: {원본 파일명}` + 생성된 features 목록 + `총 N개` + 갱신 파일(project.md/prompts/*.md/.agent-state.yml) + 검증 한 줄 + (7.5 발동 시) `인터뷰: 해소 N건 / 이월 M건` 줄. 해소 ≥1건이면 `[INFO] 인터뷰 답변이 spec 에 반영됨 — /pilot:analyze --regen-agents 권장` 추가.

**다음 단계 1줄** — `/pilot:autopilot {NN}` (feature 1건 자동 진행) 또는 `@pilot-planner` (수동 시작) 병기.

## 참고

- `features/` 파일은 프로젝트 에이전트(@pilot-planner, @pilot-generator)가 직접 Read하여 사용한다.
- `docs/` 파일은 원본 보관용이며 `/pilot:confl` 커맨드를 통해서만 접근한다.
- 분석 품질이 낮으면 `/pilot:analyze --force` 로 재분석할 수 있다.
- TDD 모드에서는 @pilot-generator 가 `.plan.md` 의 Red 계약을 따라 실패 테스트를 작성한다 (Planner 는 Red 계약만 — [`rgr.md`](../context/modes/rgr.md)).
