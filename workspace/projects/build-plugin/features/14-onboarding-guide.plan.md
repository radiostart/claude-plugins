# #14 Onboarding 시나리오 가이드 — `pilot/docs/getting-started.md` 신설 + README 진입 callout

> source: features/14-onboarding-guide.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도 세션)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (직전 turn 협상 결과 — Q1~Q7)

본 plan 은 사용자가 다음 7 건을 확정한 뒤 작성한다. generator 는 본 plan 만 보고 추가 질의 없이 가이드 작성 가능.

- **Q1 — 가이드 위치 (a 채택)**: `pilot/docs/getting-started.md`. spec line 39 그대로. 기존 `pilot/docs/INTEGRATION-MOAI-ADK.md` 와 동일 위치 — 사용자 대상 가이드 한 폴더 집결.
- **Q2 — 더미 저장소 사용법 (b 채택)**: 가이드 step 1 (사전 준비) 본문에 `cp -r {플러그인 fixture 경로} /tmp/pilot-tutorial/` 1 줄 명령 포함. 사용자는 `/tmp/pilot-tutorial/` 에서 진행 — fixture 트리 오염 방지. 가이드 본문은 모든 명령 예시를 `/tmp/pilot-tutorial/` 기준으로 작성.
- **Q3 — 기대 출력 캡처 (a 채택)**: 5 step 각각 핵심 3~5 줄만 캡처 + 나머지는 `... (생략)` 처리. drift 비용 최소화. `golden_output` reference 인프라는 v0.4.0 검토 — 본 feature 범위 외.
- **Q4 — 5 분 측정 (b 채택)**: 본 #14 plan 의 "주의사항" 또는 가이드 마지막 절에 timing 측정 가이드 1 단락. 실측 책임은 features/05 dogfooding (별도 feature). 본 feature 는 측정 자체를 수행하지 않음.
- **Q5 — 영어 버전**: spec line 32 확정대로 한국어만. 결정 사항 아님.
- **Q6 — README 진입 링크 (a 채택)**: `pilot/README.md` 의 line 5 직전 (line 3·4 의 product tagline 직후) 또는 line 7 직후 (도메인 외부화 설명 다음) callout 1 줄. 형식: `> 처음 사용하시나요? → [Getting Started](docs/getting-started.md)` 단일 blockquote.
- **Q7 — troubleshooting 5 건 (교체 채택)**: spec line 24 의 5 건 중 "wizard skip 조건" 을 "wizard 잘못 매핑 정정 경로" 로 교체. 인수인계 line 124 (`#13 의 Q1 결정 (빈도 ≥ 1) 부작용 — wizard 가 무관한 폴더를 scope 후보로 매핑할 수 있음 → 정정 경로 명문화 권장`) 반영.

## 범위 (포함/제외)

- **포함**:
  - `pilot/docs/getting-started.md` 신설 (~300 줄, 5 step + 사전 준비 + troubleshooting + 마무리).
  - `pilot/README.md` 상단 1 줄 callout 삽입 (line 5 직전 또는 line 7 직후).
  - 가이드 모든 명령 예시는 `/tmp/pilot-tutorial/` 기준 (Q2 적용).
  - 5 step 각각 기대 출력 핵심 3~5 줄 캡처 (Q3 적용).
  - troubleshooting 5 건: (1) config.md fallback 동작 모드 (2) **wizard 잘못 매핑 정정 경로** (Q7 교체) (3) learn 의 H2 매칭 실패 (4) planner 진입 직전 STATE.md 누락 (5) generator 의 orchestrate-load 누락.
- **제외**:
  - **cross-domain 시나리오** — `_input/python-sample/secondary-domain/` 서브트리는 가이드 범위 외. 5 분 budget 초과 위험. 가이드는 단일 도메인 시나리오만. (단 troubleshooting 에서 cross-domain 시도하는 사용자를 features/09 의 cross-domain 가이드로 안내하는 1 줄 포함 가능 — 별도 안내, 본 가이드의 5 step 흐름에는 미포함).
  - **영어 버전** (Q5 spec 확정).
  - **`golden_output` reference 인프라** (Q3 — v0.4.0 검토).
  - **5 분 실측 자체** (Q4 — features/05 dogfooding 책임). 본 plan 은 timing 측정 가이드 1 단락만 명시.
  - **README 본문 reference 성격 변경** — spec line 42 "본문은 그대로 유지" 그대로. callout 1 줄만 추가, 다른 줄 일체 변경 없음.

## 변경 파일

### 신설

- [x] `pilot/docs/getting-started.md` (~300 줄). 본문 구조:
  - **H1**: `# Pilot — 5분 완주 가이드` (또는 동등 wording — generator 가 결정)
  - **첫 단락**: "이 가이드는 더미 저장소 `_input/python-sample/` 를 따라 5 분 안에 첫 plan 산출까지 진행" + Q4 의 timing 측정 1 단락 (가이드 마지막 절에 위치).
  - **사전 준비** (step 1 직전) — gstack 확인 명령 (`test -d ~/.claude/skills/gstack/bin && echo OK`) + 더미 저장소 복사 명령 (`cp -r {플러그인 fixture 경로} /tmp/pilot-tutorial/`) + 작업 진행 환경 안내 (1 줄: `cd /tmp/pilot-tutorial`).
  - **Step 1 — `/pilot:init`**: 명령 1 줄 + 기대 출력 3~5 줄 (wizard 가 채운 `## learn 언어 패턴`·`## scope 카테고리`·`## Ignore` 3 섹션 + 결과 출력 블록의 3 줄 — #13 의 SKILL.md `## 결과 출력` 형식 그대로). 본문 끝에 "wizard 가 자동 채움 — 잘못 매핑되면 troubleshooting (2) 참조" 1 줄 (Q7 반영).
  - **Step 2 — `/pilot:learn _input/python-sample/main.py`**: 명령 1 줄 + 기대 출력 3~5 줄 (Phase 1 도메인 도출 + Phase 2 inventory 표 일부 — `pilot/skills/learn/SKILL.md` Phase 1·2 출력 형식 그대로). 산출 파일 위치 (`workspace/context/python-sample/index.md`·`inventory.md`) 명시.
  - **Step 3 — `/pilot:project python-sample-demo`**: 명령 1 줄 + 기대 출력 3~5 줄 (폴더 트리 + `STATE.md` 또는 `.agent-state.yml` 일부 — `pilot/skills/project/SKILL.md` 10 단계 출력 형식 그대로). 생성 폴더 트리 (`workspace/projects/python-sample-demo/`) 명시.
  - **Step 4 — `/pilot:create-feature` 또는 첫 feature spec 작성**: 명령 1 줄 + 기대 출력 3~5 줄 (feature 파일 자동 생성). 산출 파일 (`features/01-{slug}.md`) 명시. (spec line 18 의 5 step 은 init→learn→project→planner→generator 인데, planner 진입 전 feature spec 이 있어야 하므로 step 4 = create-feature 또는 사용자 수동 feature 작성. generator 가 결정 — `/pilot:create-feature` 자동 호출 패턴이 자연스러움).
  - **Step 5 — `@pilot-planner` 호출**: 명령 1 줄 (`@pilot-planner` 호출 + 사용자 prompt) + 기대 출력 3~5 줄 (plan-validate 통과 1 줄 + 산출 파일명 `features/01-{slug}.plan.md`). 본 step 의 산출이 가이드 최종 목표 = "첫 plan 산출".
  - **다음 행보** (마무리 절): generator/evaluator 호출 시점 1 줄 + features/15 (TDD 모드 전환) 링크 + features/16 (doctor 점검) 링크 + Q4 의 timing 측정 가이드 1 단락 ("이 가이드를 처음 따라하는 사용자가 step 1 부터 step 5 완료까지 stopwatch 측정 권장 — 5 분 초과 시 어느 step 에서 막혔는지 피드백을 features/05 dogfooding 으로 전달").
  - **troubleshooting 절**: 5 건 각각 (증상 1 줄 + 해결 명령 1~2 줄).
    1. `config.md fallback 동작 모드` — wizard skip 또는 빈 workspace 에서 `/pilot:learn` 호출 시 default 표 사용 + INFO 1 줄 발화. 해결: `cat workspace/context/config.md` 로 확인 + `/pilot:init` 재실행.
    2. **`wizard 잘못 매핑 정정 경로`** (Q7 교체) — `_input/python-sample/` 외 사용자 저장소에서 `controllers/` 단일 폴더가 우연히 scope 후보로 자동 매핑된 경우. 해결: `workspace/context/config.md` 의 `## scope 카테고리` 표에서 잘못된 행 수동 삭제 + `/pilot:doctor` 로 schema 검증. (인수인계 line 124 의 SKILL.md `## 결과 출력` "scope 후보: M개 매핑 ({폴더목록})" 줄을 보고 정정 판단.)
    3. `learn 의 H2 매칭 실패` — `/pilot:learn` Phase 5 가 MANIFEST.md `## 도메인 분류` 표를 못 찾는 경우. 해결: MANIFEST.md 헤더 정확 일치 확인 + `/pilot:doctor` 로 schema 검증.
    4. `planner 진입 직전 STATE.md 누락` — `@pilot-planner` 호출 시 `.agent-state.yml` 부재로 orchestrate-load 실패. 해결: `/pilot:project {프로젝트명}` 재실행 + `ls workspace/projects/{프로젝트명}/.agent-state.yml` 확인.
    5. `generator 의 orchestrate-load 누락` — `@pilot-generator` 가 호출 시 orchestrate-load 단계 skip. 해결: agent wrapper 진입 규약 위반. `pilot/agents/pilot-generator.md` step 1 의 orchestrate-load 명령 확인.

### 수정

- [x] `pilot/README.md` — line 5 직전 (line 4 와 line 5 사이) 또는 line 7 직후 (line 7 와 line 9 사이의 빈 줄에 1 줄 삽입) 에 callout blockquote 1 줄:
  ```markdown
  > 처음 사용하시나요? → [Getting Started](docs/getting-started.md)
  ```
  - 위치 결정: line 7 직후가 적절 (line 3~5 의 product tagline 직후 + line 7 의 메커니즘 설명 다음 — 사용자가 product 이해 후 첫 가이드 진입). generator 가 line 5 직전 vs line 7 직후 중 본문 흐름이 자연스러운 곳 선택. **line 7 직후 = README line 8 (현재 빈 줄) 위치에 삽입 권장**.
  - 본문 다른 줄 일체 변경 없음. callout 1 줄만 추가.
- [ ] (선택) `workspace/projects/build-plugin/features/14-onboarding-guide.md` — Q1~Q7 결정 반영 필요 시. 단 현재 spec 본문 line 24 의 troubleshooting 5 건 wording (`wizard skip 조건`) 은 Q7 결정과 다름. 본 plan 에서 Q7 으로 교체된 내용을 spec 본문에 반영할지 결정 — 권고: **spec 본문은 그대로 유지**, plan 의 Q7 결정이 SSOT (직전 plan 협상이 spec patch 까지 함께 수행하지 않음 — features/13 plan 의 spec patch 패턴과 다르게 본 feature 는 spec 본문 wording 만 다른 사소한 차이로 patch 비효율). generator 는 spec 본문 patch 수행하지 않음.

## 단계별 구현 순서 (generator 진행 순서)

1. **사전 확인** — `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 트리 존재 확인 (`ls`). features/00 의 `_input/` 캡처가 완료된 상태 (이미 0b commit). `_input/python-sample/secondary-domain/` 은 본 가이드 범위 외 — 명시적으로 무시.
2. **`pilot/docs/getting-started.md` 골격 작성** — H1 + 사전 준비 + 5 step 헤더 (`## Step 1` ~ `## Step 5`) + 마무리 + troubleshooting 절 헤더만 먼저 작성. 본문은 다음 단계에서 채움.
3. **Step 1 본문 작성 (사전 준비 + `/pilot:init`)** — gstack 확인 명령 + `cp -r` 명령 + `cd /tmp/pilot-tutorial` 1 줄 + `/pilot:init` 실행 + 기대 출력 3~5 줄. 기대 출력은 `pilot/skills/init/SKILL.md` 의 `## 결과 출력` 블록 형식 그대로 + #13 의 SKILL.md 변경 (wizard 3 줄) 반영.
4. **Step 2 본문 작성 (`/pilot:learn`)** — 명령 1 줄 + Phase 1·2 출력 3~5 줄 캡처. 산출 파일 위치 (`workspace/context/python-sample/index.md`·`inventory.md`) 명시.
5. **Step 3 본문 작성 (`/pilot:project`)** — 명령 1 줄 + 폴더 트리 + STATE.md 일부 3~5 줄. 산출 폴더 (`workspace/projects/python-sample-demo/`) 명시.
6. **Step 4 본문 작성 (feature spec 작성)** — `/pilot:create-feature` 또는 사용자 수동 작성 중 generator 가 자연스러운 흐름 선택. 명령 1 줄 + 산출 파일 (`features/01-{slug}.md`) + 기대 출력 3~5 줄.
7. **Step 5 본문 작성 (`@pilot-planner` 호출)** — 명령 1 줄 (`@pilot-planner` 호출 + 사용자 prompt 1 줄) + plan-validate 통과 메시지 1 줄 + 산출 파일 (`features/01-{slug}.plan.md`) 1 줄.
8. **Troubleshooting 5 건 작성** — Q7 교체 반영 (case 2 = wizard 잘못 매핑 정정 경로). 각 case 증상 1 줄 + 해결 명령 1~2 줄.
9. **마무리 절 작성** — 다음 행보 (`@pilot-generator` 호출 시점 1 줄 + features/15·#16 링크) + Q4 의 timing 측정 가이드 1 단락.
10. **`pilot/README.md` callout 삽입** — line 7 직후 (line 8) 에 `> 처음 사용하시나요? → [Getting Started](docs/getting-started.md)` 1 줄. 본문 다른 줄 변경 없음.
11. **plan-validate.py 검증 + slack 알림** — 본 step 은 wrapper 책임이라 generator 는 별도 수행하지 않음. 단 본 feature evaluator 가 docstring drift 등 검증.
12. **분량 확인** — `wc -l pilot/docs/getting-started.md` 가 ~300 줄 범위 (250~350 줄 허용). 초과 시 출력 캡처 줄 줄이거나 troubleshooting 압축.

## 검증 방법

- **분량 확인**: `wc -l pilot/docs/getting-started.md` 가 250~350 줄 범위. spec line 27 의 "~300줄" 정합.
- **5 step 구조 확인**: 가이드에 `## Step 1` ~ `## Step 5` 헤더 5 개 모두 존재. 각 step 본문에 (a) 명령 1 줄 코드블록 + (b) 기대 출력 3~5 줄 코드블록 모두 존재.
- **troubleshooting 5 건 확인**: 가이드에 troubleshooting 5 개 sub-item 모두 존재 + Q7 교체 (case 2 = `wizard 잘못 매핑 정정 경로`) 반영. 각 case 에 명령 1~2 줄 동반.
- **README 진입 링크 확인**: `grep "Getting Started" pilot/README.md` 가 line 7 이하 30 라인 안에 1 회 hit + 다른 본문 변경 0 (`git diff pilot/README.md` 가 1 줄 추가만 보임).
- **링크 정책 확인**: 가이드 본문의 모든 내부 링크가 상대 경로 (`../skills/init/SKILL.md`·`../agents/pilot-planner.md` 등). 절대 경로 (`/Users/...` 또는 `workspace/projects/...`) 없음 — spec line 25.
- **분량 측정 가이드 1 단락 확인**: 가이드 마지막 절에 "5 분 측정 권장" 단락 1 회. features/05 dogfooding 으로 피드백 안내 1 줄.
- **향후 features/05 dogfooding 에서**: 신규 사용자 1 인이 본 가이드만 보고 step 1~5 완주 5 분 이내 성공 측정 (실측은 별도 feature 책임 — 본 feature 는 가이드 작성까지).

## 주의사항

- **가이드 본문의 명령 출력은 #14 작성 시점 (v0.3.0) 캡처**: 후속 SKILL.md 변경 시 stale 가능 (예: `/pilot:learn` 의 Phase 1 출력 형식이 #06 LOW priority 변경으로 달라지면 가이드 본문도 갱신 필요). `golden_output` reference 인프라 (v0.4.0) 까지 수동 갱신. 본 feature evaluator 가 가이드 본문 ↔ SKILL.md 의 일관성 1 회 확인.
- **`secondary-domain/` 은 가이드 범위 외**: 사용자가 cross-domain 시도하면 troubleshooting 별도 안내 가능 (features/09 의 cross-domain 가이드 링크). 본 가이드의 5 step 흐름에는 미포함. 단 troubleshooting 절 끝 (또는 마무리 절) 에 "cross-domain 시나리오는 features/09 cross-domain 처리 가이드 참조" 1 줄 추가 권장.
- **5 분 budget 준수 검증 책임 분리**: 본 #14 plan 은 가이드 작성 책임. 실측 (`스톱워치 5 분 이내`) 은 features/05 dogfooding 의 책임. 본 plan 의 "마무리 절" timing 측정 1 단락은 사용자 자가 측정 가이드만 — 자동 측정 인프라 없음.
- **링크 정책 (spec line 25)**: pilot/ 내부 파일은 상대 경로. 외부 (`workspace/projects/...`) 는 사용자 환경마다 다름 — 가이드 본문에서는 `workspace/context/python-sample/` 같은 상대 경로 표현만 사용. 절대 경로 (`/Users/...`) 사용 금지.
- **wizard 잘못 매핑 정정 경로 (Q7 = case 2)**: 인수인계 line 124 의 부작용 — `_input/python-sample/` 자체는 `models/`·`services/` 단일 폴더라 우연히도 매핑 정확. 사용자 자체 저장소에서 우연한 폴더 (예: 의도와 다른 `controllers/`) 가 매핑된 경우만 정정 필요. 가이드 본문에서는 fixture 시나리오에서는 정정 불필요하나, 자체 저장소 사용 시 troubleshooting (2) 가 발화하도록 명시.
- **README 본문 보존 (spec line 42)**: callout 1 줄만 추가. line 24~30 의 `## 목차` · line 16 의 `## ecosystem 안 위치` · 기타 본문 일체 변경 없음. `git diff pilot/README.md` 가 +1 / -0 만 보여야 함.
- **에이전트 간 전달사항 line 122·123·124 소비 확인**: 본 plan 의 step 2 (Step 1 `/pilot:init`) + troubleshooting (2) 가 line 122·123·124 의 부산물 (wizard 출력 형식 + scope 후보 자동 매핑 부작용 + 정정 경로 명문화) 모두 반영. 본 feature 완료 시 wrapper step 2 에서 line 122·123·124 를 `[x]` 처리. 다른 인수인계 (line 87~121) 는 본 feature 와 무관 — 다음 evaluator 또는 사용자 결정에 위임 (본 turn 에서 자체 판단으로 체크 금지).

## 교차 의존

- **features/00 (회귀 골든 픽스처) — [x] 완료**: 본 feature 의 가이드는 `_input/python-sample/` 트리 (5 파일 + docs + secondary-domain) 를 입력으로 사용. 본 feature 는 fixture 트리를 수정하지 않음 — `_input/` 은 read-only 입력으로만 활용. Q2 의 `cp -r` 명령으로 사용자가 `/tmp/pilot-tutorial/` 에 복제 후 진행하여 fixture 트리 보존.
- **features/13 (부트스트랩 마법사 `/pilot:init` 확장) — [x] 완료**: 본 가이드 Step 1 의 `/pilot:init` 기대 출력은 #13 의 wizard 3 줄 (`언어 감지: N개...`·`scope 후보: M개...`·`Ignore baseline: P개...`) + #13 의 SKILL.md `## 결과 출력` 블록 형식 그대로. 본 feature 의 가이드 본문 캡처는 #13 적용 후 환경에서 수행.
- **features/09·#10·#11·#12 (v0.3.0 HIGH 4 건) — [x] 완료**: 본 feature 의 가이드는 cross-domain 시나리오 범위 외 (`secondary-domain/` 제외). 단 troubleshooting 또는 마무리 절에 cross-domain 시나리오 안내 1 줄 (features/09 링크) 가능. #11 의 Open Questions 4 카테고리 템플릿은 본 가이드 Step 4 (feature spec 작성) 의 기대 출력에 반영 가능 — `/pilot:create-feature` 호출 결과로 Open Questions 4 카테고리가 자동 생성됨.
- **features/05 (사용자 dogfooding) — [ ] 미완료**: 본 가이드의 5 분 실측 검증은 features/05 dogfooding 책임. 본 feature 는 가이드 작성 완료까지. features/05 가 본 가이드를 입력으로 사용해 1 인 실측 + 피드백 수집.
- **features/15 (TDD 모드 사후 토글) · #16 (Doctor onboarding-health) — [ ] 미완료**: 본 가이드의 "다음 행보" 절에서 링크. 본 feature 의 가이드 본문에는 향후 링크 placeholder 만 (현재 features 파일 부재면 spec 본문에 링크 placeholder + "(현재 작업 중)" 1 줄). 본 feature 진행 시점에 features/15·#16 spec 본문이 존재하면 직접 링크.
- **plugin.json version bump 보류**: 본 PR 은 patch bump 안 함. v0.3.0 합본 PR 에서 일괄 처리 (features/13 plan Q7 와 일관).
- **인수인계 line 122·123·124 (#13 후속)**:
  - line 122 (`init_detect.py` 의 `(list, list)` / `(dict, list)` tuple 반환 패턴): 본 가이드의 Step 1 기대 출력에 wizard 결과 3 줄 형식 그대로 반영 (특별한 변경 없음 — #13 결과 그대로 캡처).
  - line 123 (wizard 의 `## learn 언어 패턴` 표 "의존성 추출 패턴" 셀 출처 명시): 본 가이드의 Step 1 기대 출력 또는 step 2 (`/pilot:learn`) 본문에 "wizard 가 features/01 default 표의 행을 인용 주입" 1 줄 명시 (line 123 의 권고 직접 반영).
  - line 124 (wizard scope 후보 자동 매핑 부작용 정정 경로): 본 가이드의 troubleshooting (2) = wizard 잘못 매핑 정정 경로 (Q7 교체) 직접 반영.

## focus 반영 사항

`.focus.md` 의 V1 검증 결과 (nimda Rails monolith dogfooding) 가 도출한 v0.3.0 milestone 재구성은 본 feature 의 우선순위 직접 영향:

- **도입 장벽 해소 (Tier 1)**: spec source (features/14-onboarding-guide.md) 가 본 feature 를 v0.3.0 의 도입 장벽 해소 항목으로 분류. V1 검증에서 "신규 사용자가 첫 명령부터 막힘" 이 실제 우려로 확인 — features/13 wizard 와 본 feature 가이드가 함께 1 차 진입 비용 해소.
- **단일 도메인 시나리오 충실 (V1 발견)**: focus 의 "도메인 지식 외부화 (single domain) ⭐⭐⭐ 충족" 결과는 본 가이드의 single domain 범위 결정 (cross-domain 제외) 과 일관. cross-domain 시나리오는 features/09 의 별도 가이드로 위임.
- **md / script 한정 + 어플리케이션 코드 변경 최소**: 본 feature 도 동일 — `pilot/docs/getting-started.md` (md) + `pilot/README.md` 1 줄 추가만. 어플리케이션 코드 (Python script, 모든 skills/) 수정 없음.
- **TDD 비활성화 (md 변경 위주)**: 본 feature 도 `tdd: false`. 가이드는 문서 — 자동 테스트 없음. 검증은 features/05 dogfooding 의 실측 1 회 + evaluator 의 분량·구조·링크 정책 확인.
- **5 분 budget 책임 분리**: focus 의 "AI 효율 활용 ⭐⭐⭐ 충족 (7 분 / 단일 turn spec 작성)" 평가는 V1 검증 시 nimda 1 도메인 spec 작성 시간. 본 가이드의 "5 분 = init→learn→project→create-feature→planner" 는 가이드 작성 책임만 — 실측은 features/05 dogfooding. 본 feature 의 마무리 절 timing 측정 가이드 1 단락이 사용자 자가 측정 + 피드백 경로 명시.
