# Plan Critic — #18 정비 prune — 미사용·드리프트 정리

> 입력 plan: `features/18-consolidation-prune.plan.md` (검토 시각 2026-07-24T14:05:49Z)
> 입력 feature: `features/18-consolidation-prune.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (.focus.md 미설정 — 호출자 지정 검증 축 4개는 아래 C1·C2·C3·C4 에 반영)

## 챌린지

### C1 — `_input/` 삭제 전제 오류: 배포 튜토리얼이 살아있는 소비자다
- **severity**: blocking
- **category**: premise
- **plan 인용**: 변경 파일 4번째 항목 (`features/18-consolidation-prune.plan.md:13`) + 스텝 1
- **챌린지**: plan 은 `_input/` 을 "유일 소비자 diff.sh 삭제로 고아화" 로 규정하지만, `pilot/docs/tutorial/getting-started.md:16` 이 `cp -r "${CLAUDE_PLUGIN_ROOT}/tests/fixtures/v0.1.0-baseline/_input/python-sample" /tmp/pilot-tutorial` 로 이 픽스처를 복사해 전체 walkthrough (:3 부터 Step 1~5) 를 진행한다. 튜토리얼은 mkdocs 커밋 소스 (감사 축1 § D-1: "tutorial·how-to·explanation 은 커밋됨") 로 gh-pages 에 배포된다. 삭제 시 배포 문서의 사전 준비 절차가 즉시 깨진다. 참고로 감사 축1 § C (`2026-07-24-audit-1-reference-graph.md:32`) 는 `_input/` 을 삭제 후보로 올린 적이 없다 — planner 편입분이며, 승인은 "유일 소비자" 전제 위에서 이뤄졌다. plan 의 게이트 (④ `test_doc_links.py` = md 링크 검사, docs.yml `mkdocs --strict`) 는 코드블록 안 셸 경로를 검사하지 않아 이 파손을 잡지 못한다.
- **제안**: `_input/` 삭제 결정을 사용자에게 재확인 — 선택지: (a) `_input/python-sample` 을 `pilot/examples/` 등으로 이관 + 튜토리얼 :3·:16 경로 갱신, (b) `_input/` 만 보존으로 되돌림 (diff.sh·expected 삭제는 유지), (c) 삭제 강행 + 튜토리얼 사전 준비 절차 재작성. 어느 쪽이든 `pilot/docs/tutorial/getting-started.md` 를 변경 파일 목록에 추가해야 한다.

### C2 — 스텝 1 잔존 참조 grep "매칭 0" 은 현재 코드베이스에서 달성 불가능한 게이트
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: 스텝 1 마지막 (`features/18-consolidation-prune.plan.md:36`)
- **챌린지**: `grep -rn "handoff-quality\|diff\.sh\|lifecycle/INDEX\|setup/README\|issues/example\|_input" pilot/` 의 기대결과 "매칭 0" 은 삭제를 완벽히 수행해도 실패한다. `_input` 부분문자열이 (i) hooks 의 `tool_input` (`coding-rules.sh:9-10`·`scope-guard.sh:9-10`·`commit-format.sh:10`·`protect-managed.sh:63,71`·`slack-notify.py:56`), (ii) 테스트 메서드명 (`test_memory_hint.py:46` `test_empty_input_returns_empty`·`test_confluence.py:185` `test_invalid_input_raises`), (iii) C1 의 튜토리얼 2곳에 매칭된다. 추가로 `-r` 이 gitignored 로컬 산출물 (`pilot/docs-site/` 116파일·`docs/reference/` stale·`__pycache__`) 까지 스캔한다. 이대로면 generator 가 게이트 실패를 임의 해석해 완화하거나 스킵하게 된다 — 삭제 feature 의 핵심 검증 장치가 실행 불가능한 상태.
- **제안**: 패턴을 경로형으로 앵커 — `_input` → `fixtures/v0.1.0-baseline/_input\|_input/python-sample` 등 — 하고 `git grep` 사용 (untracked 산출물 자동 제외) 또는 `--exclude-dir={docs-site,__pycache__}` 명시. 기대결과를 "매칭 0" 대신 "허용 잔존 목록 (hooks `tool_input` 등) 외 매칭 0" 으로 재정의해 plan 에 허용 목록을 못 박는다.

### C3 — B-9 정정이 `scope-sync.md:107` 을 누락 — 실행하면 새 모순 드리프트가 생긴다
- **severity**: blocking
- **category**: scope
- **plan 인용**: 스텝 2 B-9 (`features/18-consolidation-prune.plan.md:47`) + 변경 파일 목록 (analyze/SKILL.md 만 포함)
- **챌린지**: 동일 INFO 문구가 `pilot/skills/analyze/references/scope-sync.md:107` 에도 실재한다 (`[INFO] features/ 의 일부 영역이 {외부 도메인} 도메인에 의존 — ... 후 재분석 권장`). `analyze/SKILL.md:167` 은 바로 그 문장 끝에서 "상세: references/scope-sync.md" 로 위임한다. plan 대로 SKILL.md:167 만 open-questions.md:54 문구로 바꾸면 SKILL 본문과 그 위임처가 서로 다른 INFO 를 주장하는 새 모순이 생긴다 — 모순 제거가 목적인 feature 가 모순을 만드는 결과. 부수 문제: 정본 문구 "이 feature 는 {외부 도메인} 의존성이 감지됨" 은 create-feature 단건 컨텍스트 wording 이라 features/ 전체를 배치 스캔하는 analyze 5-2 에서는 의미가 어긋나고, analyze 고유 안내인 "후 재분석 권장" 도 소실된다.
- **제안**: 둘 중 하나로 재확정 — (a) `scope-sync.md:107` 을 변경 파일에 추가하고 배치 컨텍스트에 맞는 통일 문구 (예: `[INFO] features/ 의 일부가 {외부 도메인} 의존성 — 먼저 \`/pilot:learn {추천 경로}\` 후 재분석 권장`) 를 두 곳에 동일 적용, (b) B-9 를 "두 문구는 단건/배치 컨텍스트 차이로 의도적 분기" 로 재판정하고 #19 (A-5 통합) 로 이월. 감사 축2 § B-9 도 "통일 **권장**" 수준이라 (b) 가 감사 위반은 아니다.

### C4 — docs_build "CI 거동 보존" 논거 오기: CI 는 `--check` 가 아니라 write 경로를 실행한다
- **severity**: suggestion
- **category**: premise
- **plan 인용**: 스텝 3 (`features/18-consolidation-prune.plan.md:52`)
- **챌린지**: plan 은 "`--check` 경로는 불변 (CI 거동 보존)" 을 안전 논거로 쓰지만, 실제 CI (`.github/workflows/docs.yml:50`) 는 `python3 pilot/tools/docs_build.py` — 즉 **write 경로** — 를 실행하고, `--check` 는 어떤 워크플로에도 등장하지 않는다 (`tests.yml` 포함). 정리 로직을 write 경로에 넣으면 CI 실행 경로를 건드리는 것이 맞다. 실제로 무해한 이유는 따로 있다: `docs/reference/{agents,skills,tools}/`·`identity.md` 가 gitignored (`pilot/.gitignore:8-11`, 커밋본은 `reference/index.md` 뿐) 라 CI fresh checkout 에는 stale 파일이 0건 → 정리 로직이 no-op. 결과는 안전하지만 근거가 틀린 채로 두면 #20 의 docs_build 후속 변경 시 잘못된 전제를 계승한다.
- **제안**: 스텝 3 의 논거를 "CI 는 clean checkout 이라 정리 로직 no-op — write 경로 변경이지만 CI 거동 동일" 로 정정. 카테고리 `index.md` (build 산출 집합에 포함되므로 보존됨) 비삭제 확인을 테스트 케이스에 포함하면 이 경계가 회귀 방지된다. 재확인만 필요 — 구현 설계 자체 (write_files 직후·3 하위 디렉터리 한정·`--check` 무변경) 는 타당함을 실측 확인했다.

### C5 — 정리 로직의 빈 카테고리 가드 부재
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 스텝 3 정리 함수 설계 (`features/18-consolidation-prune.plan.md:52-53`)
- **챌린지**: "build 산출 집합에 없는 `*.md` 삭제" 를 그대로 구현하면, `--root` 가 부분 트리 (예: `tools/` 없는 fixture root — `test_docs_build.py` 가 실제로 temp root 에 fixture 를 복사해 `main(["--root", ...])` 를 호출한다) 를 가리킬 때 해당 카테고리 build 산출이 0건 → 그 출력 디렉터리의 기존 `*.md` 전부가 "stale" 로 판정돼 일괄 삭제된다. 현 테스트는 fresh temp 라 안 깨지지만, 삭제 로직으로는 공격면이 넓다.
- **제안**: "해당 카테고리 build 산출 ≥ 1건일 때만 그 디렉터리를 정리" 가드 1줄 추가 + 신규 테스트 2케이스에 "빈 카테고리 비삭제" 확인을 포함할지 검토. 재확인만 필요.

### C6 — 인용 정밀도 2건: doctor/SKILL.md 는 :46, `_input` 은 15파일
- **severity**: nit
- **category**: premise
- **plan 인용**: 변경 파일 목록 (`features/18-consolidation-prune.plan.md:13,26`) + 스텝 2 doctor stale (`:49`)
- **챌린지**: validate.yml stale 문구의 실제 위치는 `pilot/skills/doctor/SKILL.md:46` (plan 은 :48). `_input/` 실측 파일 수는 15 (plan 은 12파일 — #00 인수인계의 "8+3 파일" 서술 기반 추정으로 보임). 실행에 지장은 없으나 이 feature 의 계약이 "file:line 인용 정확성" 인 만큼 정정 권장.
- **제안**: 두 수치 정정. 재확인만 필요.

### C7 — B-2 정정 후 같은 표의 generator 행이 반쪽 stale 로 남는다
- **severity**: nit
- **category**: scope
- **plan 인용**: 스텝 2 B-2 (`features/18-consolidation-prune.plan.md:40`)
- **챌린지**: `context/INDEX.md:117` planner 행을 "Red 계약 작성" 으로 고치면, 같은 표 :119 generator 행 "+ 실패 테스트 통과 최소 구현 + Refactor (Green)" 이 rgr.md 역할 분담 (Generator 가 Red 작성·실패 확인부터 수행) 과 어긋난 채 남는다 — 정정된 행 바로 옆에서 구서술이 재발화하는 모양새. plan 의 "INDEX.md 는 #19 재작성 대상이라 최소 문구만" 방침과의 충돌 여부만 정리하면 된다.
- **제안**: (a) B-2 범위에 :119 generator 행 1셀 추가 ("+ Red 작성·실패 확인 → Green → Refactor"), 또는 (b) 의도적 이월임을 plan 교차 의존 절에 1줄 명시. 재확인만 필요.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | 사용자 재결정 (2026-07-24): `_input/` 삭제 취소·보존 확정. 이관·튜토리얼 재작성 안 함 (#18 무동작변경 원칙). README 재작성에 튜토리얼 더미 저장소 용도 명시. plan 변경 파일·스텝 1·게이트에서 `_input` 제거 |
| C2 | accepted | planner 판단: `git grep -nE` + 경로 앵커 패턴으로 게이트 재설계 (untracked·gitignored 자동 제외). `_input` 은 보존 확정으로 패턴 자체에서 제거 — 허용 잔존 목록 불요해짐. 스텝 1 게이트 교체 |
| C3 | accepted | 사용자 재결정: 정본 문구 중립화 전면 통일. 통일 문안 `[INFO] {외부 도메인} 의존성 감지 — 먼저 \`/pilot:learn {추천 경로}\` 권장` 을 open-questions.md:54 (정본)·analyze/SKILL.md:167·scope-sync.md:107 3곳 동일 적용. "재분석 권장" 뉘앙스는 INFO literal 밖 주변 산문이 담당 (scope-sync 5-2). 변경 파일 2건 추가 |
| C4 | accepted | 논거 정정: CI (docs.yml:50) 는 write 경로 실행 — 안전 근거는 "clean checkout 이라 정리 로직 no-op". 카테고리 index.md 비삭제 테스트 케이스 추가 |
| C5 | accepted | "해당 카테고리 build 산출 ≥ 1건일 때만 정리" 가드 1줄 + 빈 카테고리 비삭제 테스트 케이스 추가 |
| C6 | accepted | doctor/SKILL.md :48 → :46 정정 (재실측 일치). `_input` 파일 수 15 로 정정 (보존 항목 설명에 반영) |
| C7 | accepted | (a) 채택 — context/INDEX.md:119 generator 행 TDD 셀 1건을 B-2 정정 범위에 추가 ("+ Red 실패 테스트 작성 → Green 최소 구현 → Refactor"). 1셀 변경으로 표 내 반쪽 stale 방지 |
