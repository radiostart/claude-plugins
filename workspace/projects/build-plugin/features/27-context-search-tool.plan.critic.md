# Plan Critic — #27 context-search — 섹션 단위 결정적 검색 도구

> 입력 plan: `features/27-context-search-tool.plan.md` (검토 시각 2026-09-04T03:39:19Z)
> 입력 feature: `features/27-context-search-tool.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (`.focus.md` 부재 · orchestrate-load `focus: null`)
> 검증 방법: plan 스텝 1 의 규칙(토큰화·D1 경계·D6·D7·점수표·정렬 키)을 그대로 옮긴 프로토타입으로 라이브 코퍼스 `--scope pilot` 실측 + 1,000섹션 합성 코퍼스 cProfile. 프로토타입은 scratch 전용(산출물 아님).

## 챌린지

### C1 — `--scope`·`--project` 인자에 traversal 검증이 없다
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: 스텝 1 「코퍼스」 `--scope d` 항 (`features/27-context-search-tool.plan.md:120-122`) · 스텝 2 "include: `..`·절대경로 → 2" / "select: traversal → 2" (`:151-152`) · G5 (`:220`)
- **챌린지**: spec 비즈니스 규칙 "코퍼스 밖 traversal(`..`·절대경로 인자) 거부" 가 plan 에서는 `--include` 와 `select:` 에만 적용된다. `--scope d` 는 `{root}/d/**/*.md`·`{root}/d.md` 로 그대로 보간되는데 pathlib 는 절대경로를 결합하면 좌측을 버린다 — 실측 `Path("workspace/context") / "/etc"` → `/etc` (`.exists()` True), `--scope ../projects` → `workspace/context/../projects` (`.exists()` True). 즉 `--scope /etc` 는 코퍼스 루트를 통째로 바꿔치기하고 `--scope ../projects` 는 Open Q (d)-1 "지식 루트만" 기본 범위를 무력화한다. `--project ../../x` 도 `{workspace}/projects/{project}/X` 보간에 검증 없이 들어간다. G5 의 세 케이스(`select:../x`·`--include /etc`·`--include ../../x`) 를 모두 통과하면서 규칙을 위반하는 구현이 가능하다.
- **제안**: `--scope`·`--project` 를 orchestrate-load 의 `has_path_traversal()` (`pilot/tools/orchestrate-load.py:365`, `/`·`\`·`..` 거부 — orchestrate-load 자신도 `:662`·`:729` 에서 project·domain 에 같은 검사를 한다) 로 검증해 stderr + exit 2. D8 모듈 로드 실패 폴백 경로에서도 같은 판정이 필요하므로 동등한 1줄 로컬 판정 허용. 스텝 2 테스트 목록과 G5 에 `--scope ../projects`·`--scope /etc`·`--project ../x` 3건 추가.

### C2 — D7 서문 섹션이 골든 3 수계산에서 빠져 있다 (마진 66 vs 46 → 실제 66 vs 57)
- **severity**: suggestion
- **category**: premise
- **plan 인용**: D7 (`:26`) "골든 3 의 순위에는 영향 없음(아래 계산)" · 스텝 2 골든 수계산 (`:162`) "3) 66 vs `index.md` `## 스킬 17 개` 46, 다른 `## /pilot:x` 42"
- **챌린지**: plan 규칙 그대로의 프로토타입으로 라이브 코퍼스 `--scope pilot` 실측한 골든 3 top-5: `spec.md ## /pilot:learn` **66** · `modes.md` 서문(L1) **57** · `review.md` 서문(L1) **57** · `index.md` 서문(L1) **53** · `index.md ## 스킬 17 개` 46. 수계산이 D7 이 추가한 섹션 자체를 빠뜨렸다. 원인은 모든 `pilot/*.md` H1 이 "pilot — X skills" 형태라 서문이 `pilot`·`skills` 에 헤딩 정확 일치 +10 을 두 번 받는 것 — 도메인명이나 "skills" 를 포함하는 질의(역방향 경로 질의는 항상 포함)에서 서문 6개가 동일 고득점 decoy 가 되어 top-5 의 60% 를 차지한다. hit@3 는 통과(목표 1위)하므로 게이트 결함은 아니고, 골든 1·2 는 서문 영향 없음(각 22 vs 10 — plan 의 "차순위 8" 도 실제는 `## /pilot:project` 10).
- **제안**: (a) plan 의 마진 서술을 66 vs 57 로 정정하고 G2 `## 실측 기록` 에 서문 순위를 남긴다. (b) planner 가 1줄로 결정: level 1 서문 섹션은 헤딩 신호(+10/+5) 없이 경로·인용·본문만 채점(`heading` 은 표시용) — 또는 현행 유지하고 decoy 특성을 docstring 에 기록. 어느 쪽이든 골든 3 의 1위는 변하지 않는다.

### C3 — 골든 3개가 전부 영문 헤딩 토큰 질의라 Open Q (d)-2 재검토 조건이 구조적으로 발동하지 않는다
- **severity**: suggestion
- **category**: scope
- **plan 인용**: 스텝 2 골든 (`:158-161`) · spec Open Q (d)-2 "골든 질의 `hit@3` 부족 시에만 보강 검토" · spec 검증 기준 예시 "부분 로드 라인 범위"
- **챌린지**: 세 골든의 변별 토큰은 `doctor`·`slack`·`learn` — 모두 `## /pilot:x` 헤딩 정확 일치 +10 이고 한글 토큰은 본문 +2 만 기여해 순위를 바꾸지 못한다. 한글 토큰화 결정의 유일한 재검토 트리거가 hit@3 인데 게이트가 한글 질의를 하나도 측정하지 않는다. spec 의 예시 질의 "부분 로드 라인 범위" 는 실측 최고점 4(`lifecycle.md ## /pilot:project`), `pilot/index.md` 매트릭스는 2점 2위 — 코퍼스가 skills/ 만 학습해 wrapper-protocol 내용이 없으므로 답이 없는 질의라 대체 자체는 타당하지만 plan 에 사유가 없다.
- **제안**: 한글 단독 골든 1개를 4번째로 추가(spec "3개" 는 하한). 프로토타입 실측으로 답이 서는 후보: `"도메인 진입 파일 자동 로드"` → `pilot/index.md ## Cluster 진입` 14 (2위 `index.md` 서문 10) · `"조건부 인터뷰"` → `spec.md ## /pilot:analyze` = `## /pilot:create-feature` 동점 12 (둘 다 정답 허용). spec 예시를 뺀 사유 1줄 기록. fixture 골든도 `--scope pilot` 으로 실행해 G2 라이브 실측(`--scope pilot --format json`)과 조건을 맞춘다(fixture 에는 `config.md` 가 없어 무-scope 시 후보 집합이 라이브와 다르다).

### C4 — D4 confluence 재사용 경계 미정의 3건
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 스텝 4 (`:186-190`) · 스텝 1 「신호 추출」 (`:90`)
- **챌린지**: (1) `confluence.py` main 은 `" ".join(rest_args)` 를 그대로 `cmd_search` 에 넘기므로 `select:...`·1글자·불용어만인 keyword 가 랭커의 `parse_query` 로 들어간다. 기존 substring 은 "A" 한 글자도 찾았는데 랭커 경로에서 토큰 0개 → 0건이면 조용한 회귀. `select:` 의 `workspace/context/` 상대경로 의미는 confluence docs/ 에 없다. (2) "첫 일치 위치 기준 2,000자 창" 의 "첫 일치" 가 미정의 — 헤딩·경로 신호만 맞고 본문 일치 0 인 섹션·CamelCase 조각 토큰의 시작점, 창의 앞 여백. (3) `citation_tokens=..., citation_paths=...` 가 말줄임 — 스텝 1 에 인용 추출이 공개 함수로 명명되지 않아 스텝 4 가 호출할 이름이 없다.
- **제안**: (1) `parse_query` 결과가 `select` 이거나 토큰 0개면 `ranker=None` 과 같은 substring 경로로 폴백(WARN 아닌 무음 또는 INFO) 을 스텝 4 에 1줄 명시. (2) "첫 일치 = 소문자 본문에서 `matched` 토큰 중 가장 앞선 D1 경계 일치 위치, 없으면 0 · 창 = `[max(0, pos-200), pos+1800)`" 식으로 고정. (3) 스텝 1 에 `extract_citations(body) -> (citation_tokens, citation_paths)` 를 공개 함수로 명명.

### C5 — 300ms 의 실제 병목은 인용 경로 재토큰화 — "캐시 없음" 이 실행 내 memo 까지 금지로 읽힌다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: 스텝 1 「신호 추출」 citations (`:90`) · 스텝 2 성능 (`:156`) · G3 (`:218`) · 주의사항 "캐시 없음" (`:227`)
- **챌린지**: 프로토타입 cProfile (1,201섹션 · 인용 30개/섹션 고밀도 4.5MB): 총 0.83s 중 `path_tokens` 31,202회 = 0.43s(52%) — 인용마다 `tokenize` 를 다시 돌리는 것이 병목. 경계 정규식은 `re` 내부 캐시로 이미 무료(memo 전후 433ms 동일). 라이브 밀도(≈1.3KB/섹션) 1,000섹션에서는 ~160ms + 인터프리터 20ms + D8 import 11ms ≈ 190ms 로 목표 안이지만, learn 산출물처럼 `file:line` 인용이 촘촘한 코퍼스에서는 초과한다. plan 의 성능 테스트 코퍼스 명세("200파일 × 5섹션")에 인용 밀도가 없어 병목 경로가 측정되지 않는다.
- **제안**: 스텝 1 에 "캐시 없음 = 실행 간 영속 캐시 없음. 실행 내 `path_tokens(citation)` dict memo(동일 인용 문자열 반복) 허용" 1줄. 스텝 2·G3 코퍼스 명세에 "섹션당 `file:line` 인용 ≥ 5" 를 넣는다.

### C6 — D8 재사용 범위의 빈틈 2건
- **severity**: nit
- **category**: edge-case
- **plan 인용**: D8 (`:27`) · 스텝 1 「순위」 `is_entry` (`:109`) · 「코퍼스」 (`:120`)
- **챌린지**: (a) `is_entry = 파일명 index.md 또는 MANIFEST 진입 파일(D8)` — `parse_manifest_domain_files(manifest, domain)` 은 도메인 인자를 요구하므로 `--scope` 미지정 시 어느 도메인의 진입 파일인지 정의가 없다(전 도메인 순회 함수는 orchestrate-load 에 없음). (b) `--scope d` 는 `{root}/d/**` 와 MANIFEST 진입 파일(`pilot/index.md` — 이미 `d/` 안)을 중복 수집 — dedupe 미명시 시 같은 섹션이 두 번 출력된다. 재사용 자체는 문제 없음: importlib 로드 11ms, 끌려오는 모듈은 `doctor`·`doctor._common` 2개, `parse_manifest_domain_files(..., "pilot")` → `['pilot/index.md']` 실측.
- **제안**: (a) "scope 미지정 시 `is_entry` = 파일명 `index.md` 만" 1줄. (b) `collect_files` 반환을 set 으로 모아 상대경로 정렬로 명시.

### C7 — 실측 baseline 헤딩 수 오기
- **severity**: nit
- **category**: premise
- **plan 인용**: `:12` "H2 24개 · H3 0개"
- **챌린지**: 실측 H2 26(`pilot/*` 만이면 20) · H3 2(`config.md:40`·`:45`). 설계 영향 없음 — 오히려 라이브 코퍼스에 H3 가 실재하므로 H3 포함 규칙이 G2 라이브 실측에서 실제로 실행된다는 뜻.
- **제안**: 수치 정정만 (재확인만 필요).

### C8 — D1 비대칭: 질의 쪽 조사는 흡수되지 않는다
- **severity**: nit
- **category**: edge-case
- **plan 인용**: D1 (`:20`) · 스텝 1 「0건 안내」 guidance 4종 (`:126`)
- **챌린지**: D1 은 본문 쪽 조사(`섹션을`)만 좌측 경계로 흡수한다. 질의에 조사가 붙으면(`섹션을 로드` → 토큰 `섹션을`) 본문 `섹션 단위` 와 매칭 0 — 실측 `섹션을` 히트 0, `로드` 만 2점. feature 제목·사용자 발화에는 조사가 흔한데 0건 guidance 4종에 이 경우가 없다. 랭커 결정(Open Q (d)-2) 자체를 흔드는 지적은 아님.
- **제안**: guidance 에 조건부 1항 — `token_hits` 가 0 인 한글 토큰이 있으면 "조사 제거 재질의 (예: `섹션을` → `섹션`)". 랭커 변경 없음.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | `--scope`·`--project` 에 `has_path_traversal()` 재사용(D8 로드 실패 시 동등 로컬 1줄 판정) → exit 2 + 수집 후 `resolve()` 봉쇄 검증(심링크 탈출 파일 제외 + INFO). plan D8 · 스텝 1 「코퍼스」 · 스텝 2 traversal 케이스 · G5 3케이스+심링크 반영 (사용자 필수 지정) |
| C2 | accepted | (a) 수치 정정 — Q1 차순위 10, Q3 서문 57 기록. (b) 두 안 중 **level 1 섹션 heading 신호(+10/+5) 차단** 채택 + 동점 정렬 H2→H3→L1. 골든 1위 불변, 서문 ≤37. H1-only 파일은 path(+8)·본문으로 대표된다는 trade-off 를 D7 에 명시 |
| C3 | accepted | 골든 4번 `"도메인 진입 파일 자동 로드"` → `pilot/index.md ## Cluster 진입` (14 vs ≤4, `--scope pilot`) 추가 · fixture 골든도 `--scope pilot` 으로 실행 · spec 예시 "부분 로드 라인 범위" 제외 사유(코퍼스에 정답 부재, 최고 4) 기록. `"조건부 인터뷰"` 는 동점 정답 2개라 채택 안 함 |
| C4 | accepted | (1) `select:`·토큰 0개 keyword → 무음 substring 폴백(WARN 은 로드 실패만) (2) `match_pos` = matched 토큰 D1 경계 일치 최소 인덱스, 없으면 0, 창 `[max(0,pos-200), +2000)` (3) `extract_citations(body, memo=None)` 공개 함수 명명. 스텝 1·4 반영, confluence 테스트 3→5건 |
| C5 | accepted | "캐시 없음" = 실행 간 영속 캐시 금지로 정의(주의사항). `search()` 지역 memo dict 를 `extract_citations` 에 전달(전역 상태 없음). 성능 테스트·G3 코퍼스에 섹션당 인용 ≥5 명시, 프로토타입 참고치(190ms/0.83s) 기록 |
| C6 | accepted | (a) scope 미지정 시 `is_entry` = `index.md` 파일명만, `--scope d` 시 MANIFEST d 진입 파일 추가 (b) `collect_files` set → 상대경로 정렬 dedupe. 스텝 1 「순위」「코퍼스」 + 스텝 2 케이스 반영 |
| C7 | accepted | baseline 을 H2 26(pilot/* 20 · MANIFEST 1 · config 5) · H3 2(`config.md:40`·`:45`) 로 정정 (grep 재확인). H3 포함 규칙이 라이브 G2 에서 실행됨을 명시 |
| C8 | accepted | 0건 guidance 에 조건부 1항 — `token_hits` 0 인 한글 토큰 있으면 "조사 제거 재질의 (예: `섹션을` → `섹션`)". 랭커·D1 무변경 |

> 합의 기입: 2026-09-04 planner 재호출 (사용자 결정: planner 재호출 승인, C1 필수 반영, C2~C8 planner 위임). 반영 상세는 plan.md § critic 합의 반영.
