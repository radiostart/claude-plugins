# #28 로드 시 신선도 힌트 — 인용 기반 변경 감지 (+ 로드 정책 문서 정합)

> source: prompt
> created: 2026-09-04T02:50:24Z
> user_prompt: "feature 생성해줘 — docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md §4 F-D + F-E 등록"
> renumbered: 2026-09-04 — 원격 main 의 #24~#26 선점(pilot-update·schema-validate·issue-cycle)으로 #24~#27 → #27~#30 재번호
> plan: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-D · § F-E (설계 상세·근거 SSOT. §2 P5 패턴)

## 요구사항

- **조건**: 원격 v0.16.0 이 이미 `check_context_citations_stale` (`pilot/tools/doctor/integrity.py:1182`) 로 인용 stale 검사를 수행한다. 본 feature 의 범위는 **그 판정을 로드 시점에 노출**하는 것이다 — 새 판정 로직·새 기준 시각을 만들지 않는다 (2026-09-04 범위 축소, Open Q (d) 참조).
- **트리거**: `orchestrate-load.py` 가 도메인 진입 파일·경계 문서를 `files_to_read` 에 넣을 때마다. (`/pilot:doctor` 쪽은 이미 같은 검사를 수행하므로 신규 트리거가 아니다.)
- **기대결과**:
  - 로드되는 지식 파일마다 힌트 1줄: `[신선도] {file}: 갱신 {age}일 전 · 인용 {stale}/{resolved} 변경 · 미해석 {unresolved} — 인용 전 현재 코드 확인`. 갱신 1일 이하이고 stale 0 이면 생략 (노이즈 억제).
  - **doctor 는 기존 검사를 그대로 유지한다** — WARN 문구·임계·출력 불변. 두 소비처가 **같은 판정 함수 1벌**을 호출해 결과가 갈리지 않게 한다 (중복 WARN 방지).
  - 실사례 검증: 2026-09-04 시점 `workspace/context/pilot/index.md`·`spec.md` 가 `orchestrate-load.py` 변경으로 stale 판정된다 (doctor WARN 2건 실측). 같은 판정이 래퍼 진입 시 힌트로도 보여야 한다 — 지금은 사용자가 doctor 를 따로 돌려야만 안다.
  - **(F-E) 문서 정합**: `GUIDE.md:51-58` 와 `state-schema.md` `analyzed` 절의 "analyzed: true 면 MANIFEST 진입 파일 재로드 생략" 서술을 코드 실제 거동("진입 파일은 항상 로드, analyze 는 prompts/ 압축본 신뢰 여부만") 으로 정정. **구현 변경 없음** — 코드가 옳다 (색인·진입은 항상 로드 = 계획서 §2 P1 정합).

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **기준 시각 = 파일 mtime 단일** (2026-09-04 정정, Open Q (d)). 지식 파일 mtime 과 인용 소스 mtime 을 비교하며, 이는 기존 `check_context_citations_stale` 과 **동일 기준**이다. 당초 확정했던 `learned_at` > git 커밋 시각 > mtime 3단 우선순위는 폐기한다.
- **인용 파싱·해석은 기존 구현을 재사용한다. 새 정규식 작성 금지** — `_CITE_RE` (`integrity.py:1117`, 슬래시 필수·앵커 선택) · `_iter_cited_paths` (`:1154`) · `_resolve_cited` (`:1164`, repo 루트 → `source_root` 접두) · `_is_workspace_internal` (`:1176`) · `_read_source_root` (`:1125`). 두 벌이 되면 같은 파일에 대해 doctor 와 로더의 판정이 갈린다.
- **집계 축은 기존 검사와 같다**: `resolved` (실파일로 해석된 인용) · `stale` (인용 소스 mtime > 문서 mtime) · `unresolved` (`n_cited - n_resolved`). workspace 내부로 해석되는 인용은 context 상호 링크라 세지 않으며, `CONTEXT_META_FILES` (MANIFEST·config 등) 는 대상에서 제외한다.
- **신호만 낸다** — 자동 수정·자동 재학습 트리거 금지 (drift-protocol 승인 원칙 유지). doctor 의 "context mtime > analyzed_at" 검사(파생물 재생성 축) 와는 여전히 별개 축이다.
- **상한·성능**: 파일당 인용 500개 초과 시 앞 500개만 + `(표본 500/{n})` 표기. stat 실패는 skip(카운트 제외). orchestrate-load 지연 상한 200ms — 초과 시 갱신 나이만 표기하고 "인용 검사는 `/pilot:doctor` 로" 힌트.
- **공용 모듈 추출**: 위 헬퍼와 파일 단위 집계를 `doctor` 패키지 안의 공용 모듈로 옮기고 `check_context_citations_stale` 과 orchestrate-load 가 함께 import 한다. `orchestrate-load.py` 는 이미 `doctor._common` 을 import 하므로 새 최상위 모듈(`freshness.py`)은 만들지 않는다. 배치(`_common.py` 확장 vs `citations.py` 신설)는 planner 결정. 표준 라이브러리만.

## 예외 케이스

- 해석된 인용 0건 → 힌트 생략 (doctor 는 기존대로 INFO 유지).
- 미해석 인용 (실파일 없음) → `unresolved` 카운트만. `stale` 로 세지 않는다 (기존 검사 거동).
- 인용이 라인 번호 없이 경로만 → 기존 정규식이 앵커를 선택으로 두므로 그대로 집계된다.
- **clone 직후 전 파일 mtime 이 같아 stale 0 이 되는 것은 기존 검사의 알려진 한계다.** 본 feature 는 이를 바꾸지 않는다 — 기준을 바꾸면 doctor 와 로더가 갈린다.
- 200ms 초과 → 갱신 나이만 표기하고 "인용 검사는 `/pilot:doctor` 로" 힌트 (A2).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] 신선도 기준 시각 → **mtime 단일** (2026-09-04 사용자 승인, 당초 `learned_at` > git > mtime 3단 확정을 정정). 정정 사유 2가지: (1) knowledge-sync (v0.14.0, `skills/context/lifecycle/knowledge-sync.md`) 가 사이클 종료마다 승인 하에 context 문서를 갱신하므로 지식 문서는 learn 단독 산출물이 아니다. learn 이 아닌 writer 가 갱신하면 `learned_at` 은 그대로 남아 실제보다 오래된 값이 되고 과잉 경고를 낸다 (2) 원격 v0.16.0 의 `check_context_citations_stale` 이 이미 mtime 기준으로 동작하며 실측 WARN 을 낸다 (2026-09-04 doctor 실행: `context/pilot/index.md`·`spec.md` 2건). 두 검사가 다른 기준을 쓰면 같은 파일에 대해 결과가 어긋난다
- [x] `learned_at` frontmatter 필요 여부 → **불필요, #29 스키마에서 삭제** (위와 같은 사유. 2026-09-04 사용자 승인)

## 검증 기준

- **기존 doctor 검사 회귀 0** — 헬퍼 추출 후 `check_context_citations_stale` 의 출력이 추출 전과 동일 (기존 doctor 테스트 무손 + 같은 워크스페이스 실행 결과 diff 0).
- 픽스처: 지식 파일 1 + 인용 소스 3 (변경 1 · 미변경 1 · 미해석 1) → 힌트 문구·카운트 정확성. mtime 조작은 `os.utime`.
- 실사례: 현재 `workspace/context/pilot/` 로 orchestrate-load 실행 시 `index.md`·`spec.md` 에 stale ≥ 1 힌트 발화 (doctor 가 같은 2건을 WARN 으로 내는 것과 일치).
- F-E: `GUIDE.md`·`state-schema.md` 정정 후 `orchestrate-load.py build_load_plan` 코드 변경 0 (`git diff --stat pilot/tools/` 에 미포함).
- 전체 unittest 통과 + doctor 클린 + orchestrate-load 지연 측정 200ms 이내.

## 관련 파일 범위

- **변경**: `pilot/tools/doctor/integrity.py` — 인용 헬퍼 5종과 파일 단위 집계를 공용 모듈로 추출, `check_context_citations_stale` (`:1182`) 은 그것을 import (거동 불변)
- **신규 (배치는 planner 결정)**: `doctor/citations.py` 신설 또는 `doctor/_common.py` 확장 · 대응 테스트
- **변경**: `pilot/tools/orchestrate-load.py` — 4) 진입 파일·5) 경계 문서 로드 직후 `[신선도]` 힌트
- **불변**: `pilot/tools/freshness.py` 는 **만들지 않는다** (당초 계획 폐기 — 판정 로직 1벌 원칙)
- **변경**: `pilot/skills/context/lifecycle/drift-protocol.md` — "자동 신호" 절 추가 (신호 → 사용자 판단 → 승인 하 재학습 경로)
- **변경 (F-E)**: `pilot/skills/context/lifecycle/projects/GUIDE.md:51-58` · `pilot/skills/context/lifecycle/state-schema.md` `analyzed` 절 — 코드 거동으로 정정
- **불변**: `orchestrate-load.py build_load_plan` 의 로드 정책 코드 (F-E 는 문서만)
