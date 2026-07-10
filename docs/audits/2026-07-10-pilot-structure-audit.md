# pilot 구조 감사 및 개선 기록 — 2026-07-10

> 멀티에이전트 감사(검토 6관점 → 발견별 adversarial 검증)로 확정한 발견 31건 + GAP 3건을
> 일괄 반영한 기록. 감사 축: (1) 모델 업그레이드로 불필요해진 부분 (2) 스킬 군더더기
> (3) 구조 적합성 (4) 목적 부합성. 변경 규모: **75 files, +408 / −1,707**.

## 핵심 판정

**구조 개편은 불필요 — 뼈대는 건강하다.** 필요한 변화는 두 갈래로 확인됐다:

- **축소 대상**: 약한 모델 시절의 보정 장치 — prose 로 반복하는 행동 지시(동일 지시 4중 복제,
  강조 인플레이션, 모드 규칙 6곳 재기술, 페르소나 3층).
- **유지·강화 대상 (keep 판정)**: 모델 능력과 무관하게 성립하는 층 —
  - 파일 매개 장치(`.focus.md`, 전달사항, `.plan.critic.md` 합의 표): 서브에이전트가 메인
    대화를 못 보는 구조적 제약의 해법.
  - 결정론적 신호·게이트 계층: `orchestrate-load.py`(컨텍스트 결정), `plan-validate.py`
    (쓰기/읽기 양방향 게이트 — plan-schema § 호출 지점의 문서화된 계약), `auto_pilot.py`
    ("판단하지 않는" 전이), `verify-report-lint.py`, hooks 5종.
  - planner-critic 별도 에이전트: fresh-context 적대 검토의 앵커링 회피 가치 (강제 기본값만 완화).
  - Slack 의 스킬–훅–CLI 3층: 관측 가능성에 따른 정당한 분리 (검증 단계에서 "오염" 주장 기각).
  - Quick Start 의 learn 생략: 의도된 2-트랙 progressive disclosure (기각된 발견).

prose 지시를 축소할 때의 표준 흡수 경로는 **기계 검증 계층으로의 이관**이다
(예: wrapper 모드 재기술 삭제 → plan-validate `--mode` 게이트가 담보,
JSON 처리 지시 → orchestrate-load 의 `instructions` 필드).

## 적용된 변경

### 1. 에이전트 업그레이드로 불필요해진 부분 (축 1)

| 변경 | 내용 |
|---|---|
| critic 스킵 완화 (F1) | 별도 스킵 동의 질의 폐지 — planner 가 계획 요약에 critic 권장 여부 1줄 포함, 계획 확인 응답 1회로 통합. 스킵 주체는 사용자 유지, 사유는 plan.md 기록. autopilot 의 "critic 항상 실행" 은 유지 (무감독 구간 유일 hard-stop). |
| wrapper 보일러플레이트 제거 (F2, F29) | orchestrate-load.py 가 `instructions` 필드(공통 JSON 처리 지시 + phase 별 focus 지시)를 emit — 4개 wrapper 의 5불릿 복제 삭제. `[불변]` 규칙은 1문장으로 압축해 인라인 유지 (스크립트 실행 전 방어라 JSON 대체 불가). |
| 강조 인플레이션 정리 (F3, L18) | "기록은 Edit 으로" 일반 규칙을 guardrails.md 에 1회 신설, wrapper 별 전문 1회만 유지, 괄호 리마인더 삭제. 훅이 기계 강제하는 규칙의 중복 프롬프트 금지문 완화. |
| evaluator step 8 폐지 (F4) | REPORT↔체크박스 동기화 전용 재검증 패스 삭제 → step 7 말미 1줄 (guardrails § SSOT 룰 참조) 로 대체. |
| SSOT 3층 → 2층 (F5, F17, G3) | instincts.yaml 삭제 (5개 항목 전부 파생 요약). identity.yml 은 archetype+forbid 만 유지 (voice/phrasing 산문 제거). orchestrate-load 강제 로드 목록 2파일 + 존재 확인(add_if_exists 경로) 으로 전환. |
| 모드 분기 포인터화 (F28) | generator/evaluator 의 rgr.md·characterize.md 전문 재기술을 step 슬롯 유지 + 1-2줄 포인터로 교체 (step 번호 원격 참조 보존). guardrails 에 capture_lockdown 축 신설 + tdd_evidence 에 [Captured] 케이스 포함 (기존 축 누락 결함 동시 수정). |
| drift 참조 정리 (F30) | planner 내부 2중 기술 해소 (footer 삭제, step 3 정본). drift-protocol 트리거 매트릭스에 Planner-Critic 행 신설 (§B 감지·보고만) — critic footer 와 protocol 간 모순 해소. |
| Slack caveat 표준화 (F31) | 4곳 호출 블록의 caveat 를 동일 표준문으로 통일 (grep 동기화 가능). hook 릴레이 채널(PermissionRequest/Notification) 문서화 + 이중 발송 가능성 '참고' 명시. |
| enums 부분 로드 축소 (L3) | offset/limit 마이크로 절차 → 1문장. |

### 2. 스킬 군더더기 (축 2)

| 변경 | 내용 |
|---|---|
| fix-review 삭제 (F14) | 라우팅 어휘를 pilot-code-review 에 흡수: local→trivial 개칭, new-feature·dismiss 추가 (6종), routing 블록이 수정 규모(trivial 일괄/one-shot/full-cycle)까지 직접 안내. 고유 규칙 2줄(보수적 상향, evaluator 영역 dismiss) 이관. |
| preamble 적용표 SSOT 화 (F7, F15) | 적용표를 유일 SSOT 로 선언, P 정의부 산문 열거 전부 삭제. pr·slack·learn·characterize·autopilot·commit 행 추가, doctor P1 제거, slack SKILL 자기모순(P1→P2 오기) 수정, create-feature 선언 P-1·P0·P1 정렬. |
| regen-mode 백업 버그 (F6) | mkdir `.agents.bak` vs cp `.prompts.bak` 자기모순으로 **실행 시 실패하던 백업 스니펫** 수정. regen-verify.py 를 post-regen 검증 단계에 배선 (고아 도구 해소, G1). |
| scope default 표 단일화 (F9) | scope-sync.md 5-2 표를 canonical 지정 — analyze·project·init·create-feature·integrity.py 5곳이 참조로 전환. |
| project 정리 (F10, F11) | 7·8단계 stale 라벨 수정, H1 치환 40줄 스펙 → 3줄 (SSOT 4항목·A2 fallback 보존). |
| analyze/learn (F12) | batch Write → coding.md 링크. 1/3 vs 1/2 재시도 비율은 의도적 차이 근거 1줄씩 명시. |
| doctor 축소 (F13) | SKILL.md 163→63줄, references/diagnose.md·schema.md 삭제 (스크립트 출력이 SSOT). |
| commit 3중 표현 (F16) | commit.md 를 scope SSOT 로 훅 기본값 정렬 (chore·docs·test 제거), SKILL 슬림화, 훅 한계(heredoc 미검증·advisory) 명문화. |
| messages.md 정리 (F18) | 215→126줄 — dead key 3건 삭제, 1-소비 key 5건 인라인, stale verification_report_example 삭제, Slack 본문 복제 → build_message() 포인터. |
| pr 이중 기술 (F19) | shared/pr.md §1 의 메커니즘(트리·키 표·검증)을 삭제하고 pr/SKILL.md 를 SSOT 로 — 워크스페이스 override 시 메커니즘 소실 위험 제거. |
| 기타 (L4, L5, L6, L16) | heuristics.md 203→129줄 (worked example 축소), create-feature 재요약 15줄 삭제, tdd↔characterize 우선순위 링크, issue 경량 모드 성격 선언. |

### 3. 구조 (축 3)

| 변경 | 내용 |
|---|---|
| 테스트 CI 신설 (F21) | `.github/workflows/tests.yml` — pilot/tools·tests·hooks 경로 트리거, 348개 테스트 실행. |
| 링크 검증 테스트 (F20 재발방지) | `test_doc_links.py` — skills/·agents/ 의 상대 링크 + `${CLAUDE_PLUGIN_ROOT}` 링크 실존 검증. |
| 끊어진 링크 5건 수정 (F20) | agents→prompts 리네임 전파 (example prompts 3 + INDEX + baseline 픽스처 12 동기 수정 포함). |
| 훅 테스트 (F24) | test_protect_managed.py 32건 + test_commit_format.py 14건 신설. **테스트가 실제 버그 발견**: `rm -rf workspace/projects/P` (trailing slash 없음) 이 보호를 우회 — 정규식 `(/|$)` 로 수정 완료. |
| STATE 정책 통일 (F22) | (c)안 — "추적 여부는 사용자 정책" 으로 INDEX·workspace-layout 동일 문구화. 이 저장소는 workspace/STATE.md·.focus.history/ untrack + gitignore. |
| drift-protocol docs 축소 (F23) | docs 판의 규칙 재기술 표 삭제 → 배경+예시+SSOT 링크 구조 (재기술 표의 §B 오부여 모순 소멸). |
| 위생 (L9~L14) | PLUGIN_SCHEMA_NOTES: PermissionRequest 추가·context/ 관행·tools 명명 동결 규칙 명문화. marketplace.json 설명 동기화 + 릴리스 체크리스트 4번째 항목. .pytest_cache 방어적 ignore. handoff-quality.py 삭제 (G1 — 소비처 없는 고아 도구). ssot-and-derivation 의 --check 허위 서술 수정 (L10). |

### 4. 목적 부합성 (축 4)

| 변경 | 내용 |
|---|---|
| 광역 회귀 soft gate (F25) | config.md `regression_command` 키 신설 (LANG_KEYS 등록) — /pilot:pr 진입 전 1회 실행, 실패 시 사용자 확인. 레거시의 대표 리스크(원거리 파손)를 PR 경계에서 포착. evaluator 는 미사용 (사이클 단위 전체 스위트 금지 원칙 유지). |
| 리뷰 축 경계 재서술 (F26) | "팀 규칙·사이클 라우팅 → /pilot:review, 범용 정확성 → 내장 /code-review" 로 갱신. 검출 파이프라인(pilot-code-review)은 유지 — 팀 규칙 파일·lint 훅·라우팅이 검출 시점 입력이라 내장 위임 불가. |
| 튜토리얼 드리프트 (F27) | quick-start 의 존재하지 않는 wizard 서술·산출물 오기·스킬 수 하드코딩·구버전 표기 4건 수정. |

## 이연 항목 (판단 근거와 함께)

| 항목 | 상태 | 근거 |
|---|---|---|
| plan-validate 형식 항목 동결 (L1) | 정책 선언만 | 동의어 완화 패치 누적은 계약 마찰 신호 — 검증 범위를 현 수준에서 동결하고, 추가 마찰 시 evaluator 판정 축으로 회귀 검토. |
| identity personas 인라인화 (L7) | 이연 | archetype+forbid 로 슬림화 완료. 에이전트 파일 인라인 이동은 docs_build 파이프라인 개조가 필요 — 다음 구조 정리 때. |
| doctor 표 헤더 ERROR→WARN (L15) | 이연 | 헤더는 scope-guard·commit-format·orchestrate-load 파서 계약 — 완화는 파서 유연 매칭과 함께 가야 하는 제품 결정. |
| characterize/tdd 병합 (L6) | 이연 | 명령어 표면은 사용자 습관 자산. 우선순위 규칙 상호 링크로 최소 조치 완료. |
| Slack 이중 발송 분리 (F31(2)) | 실측 대기 | planner approval + harness Notification 겹침은 실측 후 이벤트 분리(attention) 처방 — how-to 에 알려진 고려사항으로 문서화됨. |
| verify-report-lint --workspace 확장 (F4(2)) | 선택 | REPORT↔체크박스 교차 검증의 기계화 — 1줄 참조로 충분하다고 판단되면 불요. |
| config.md.template 의 commit_scopes 예시 정렬 | 후속 | 구 8-scope 목록이 명시 설정값 예시로 남아 있음 (동작 충돌 없음 — override 라서). 템플릿+baseline 픽스처 동기 갱신 필요라 별도 커밋 권장. |
| commit-format.sh JSON additionalContext 출력 (F16b) | 이연 | 현재는 advisory 한계를 주석·문서로 명시. 훅 프로토콜 변경은 별도 검증 필요. |

## 검증 결과

- `python3 -m unittest discover -s tests/tools` → **Ran 348 tests, OK** (감사 전 299 → 신규 테스트 3파일 추가 + 고아 도구 테스트 삭제 반영)
- `mkdocs build --strict` → PASS
- `test_doc_links` — 상대·플러그인 링크 전수 실존 검증 통과
- 잔존 참조 스캔 (instincts / fix-review / handoff-quality / agents-scaffold / .agents.bak) → 0건
