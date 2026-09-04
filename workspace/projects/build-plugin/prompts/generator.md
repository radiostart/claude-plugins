# Generator — build-plugin

코드 구현 시 참조하는 기술 레퍼런스.

**역할:** 계획 (plan.md) 에 따라 코드 작성 + **제출 전 sanity check** (`evals/coding.json` 체크리스트로 자체 검증). 완성도 심사는 Evaluator 가 담당 — 본 단계는 "내가 방금 쓴 코드가 컨벤션을 벗어나지 않았나" 를 자가 확인.

> **⚠️ 이 파일은 `@pilot-generator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-generator.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-generator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-generator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 컨텍스트 로드

이 프로젝트가 의존하는 도메인 지식 (래퍼가 자동 로드 — 수동 Read 불필요):

- `workspace/context/MANIFEST.md`
- `workspace/context/pilot/index.md` (도메인 pilot 진입 파일)
- `workspace/context/pilot/lifecycle.md` (init·project·issue·doctor·focus)
- `workspace/context/pilot/spec.md` (confl·analyze·create-feature·learn — #02 #03 #04 변경 대상 다수)
- `workspace/context/pilot/modes.md` (tdd·characterize)
- `workspace/context/pilot/delivery.md` (commit·pr·slack)

> `workspace/context/scope/pilot.md` · `workspace/context/rules/pilot.md` 는 사용자 커스텀 layer 로 본 프로젝트는 미작성. features/ 의 file:line 인용을 1 차 근거로 사용.

---

<!-- [analyze-managed] -->
## 핵심 변경 대상

| 대상 | 파일 | 용도 |
| --- | --- | --- |
| learn 스킬 본문 | `pilot/skills/learn/SKILL.md` | Phase 2 lookup 추가, 두 표 default 섹션 격하 (#01) |
| analyze 스킬 본문 | `pilot/skills/analyze/SKILL.md` | 5-2 lookup 추가, default 섹션 격하, MANIFEST 부재 처리 (#02) |
| create-feature 스킬 본문 | `pilot/skills/create-feature/SKILL.md` | 5-2 인용 호출 동일 적용 (#02) |
| project 스킬 본문 | `pilot/skills/project/SKILL.md` | template 복사 후 H3 동적 생성 단계 추가 (#03) |
| project 템플릿 | `pilot/skills/context/lifecycle/projects/example/project.md` | `## 관련 파일` H2 + 가이드 주석만 유지 (#03) |
| doctor 검증 | `pilot/tools/doctor/integrity.py` | 신규 검증 함수 (#04) |
| doctor 단위 테스트 | `pilot/tests/tools/test_doctor_integrity.py` (신규) | unittest + importlib.util, `test_doctor_slack.py` 패턴 답습 (#04) |
| 워크스페이스 설정 | `workspace/context/config.md` | 신규 섹션 2 개 (`## learn 언어 패턴`, `## scope 카테고리`) (#01 #02) |
| 회귀 픽스처 | `pilot/tests/fixtures/v0.1.0-baseline/` | v0.1.0 거동 캡처 + v1 검증 (#01~#04 공통) |
| 인터뷰 규칙 SSOT | `pilot/skills/context/shared/interview.md` (신설) | 조건부 인터뷰 발동 조건·우선순위·상한·답변 반영 규칙 (#17) |
| create-feature 스킬 본문 | `pilot/skills/create-feature/SKILL.md` | 3-bis 직후 3-ter 조건부 인터뷰 + 산출물 대조 단계 (#17) |
| analyze 스킬 본문 | `pilot/skills/analyze/SKILL.md` | 7↔8 사이 7.5 일괄 질의 단계 (#17) |
| 미사용 파일·픽스처 삭제 | `pilot/tests/fixtures/handoff-quality/` · `v0.1.0-baseline/` 수동 하네스 · `examples/code-review/README.md` · `context/lifecycle/{INDEX.md,setup/README.md,issues/example/issue.md}` | 감사 승인 삭제 + 드리프트 B-1~B-9 정정 (#18) |
| 스킬·에이전트 전체 재작성 | `pilot/skills/*/SKILL.md` · `pilot/agents/*.md` · `context/shared/` (wrapper-protocol.md 신설) | 원칙 중심 100줄 이하 (agents 는 계약 보존 우선), 불변 조건 체크리스트 = 감사 축 3 (#19) |
| Python 슬림화 | `pilot/tools/doctor/integrity.py` · `verify-report-lint.py` · `doctor.py` · 삭제 3종 (`diagnose.py`·`memory-hint.py`·`init_detect.py`) + 연동 테스트 | 마이그레이션 삭제·lint 이관·파서 흡수, schema.py 유지 + validate.yml CI 신설 (#20) |
| 문서 정합 | `pilot/docs/reference/index.md` · `pilot/docs/how-to/doctor-migration.md` · `pilot/docs/tutorial/getting-started.md` | #20 삭제·이관 반영 — 도구 목록 정정·how-to 현행화·Troubleshooting 무효 항목 삭제, md 만 수정, 파일명 보존 (#21) |
| context 재학습 | `workspace/context/pilot/` 6 파일 | 완료 — `/pilot:learn … --force` 재실행으로 전부 재생성 (인용 172건 전건 유효). **직접 Edit 금지** 는 상시 규칙 (drift-protocol § A) (#22) |
| doctor 파서 오탐 | `pilot/tools/doctor/integrity.py` (`check_conventions_paths`) · `pilot/tools/doctor/_common.py` (`count_real_features`) | (A) config 표 플레이스홀더를 실선언으로 오탐 (B) `.plan.critic.md` 를 feature 로 계수 — 둘 다 파서 수정 (#23) |
| 업그레이드 도구 | ~~`pilot/tools/pilot-update.sh`~~ (삭제 완료) · `pilot/README.md` · `pilot/docs/tutorial/getting-started.md` | 폐기 확정 — 스크립트 삭제 + 안내를 `/plugin` 2단계 + 세션 재시작으로 일원화. **변경 대상으로 잡지 말 것** (#24) |
| 스키마 검사 중복 | (코드 변경 없음) | 결론 **현행 유지** — `schema.py` 와 CLI 는 서로 대체하지 않는다. CI 는 `doctor --schema` 단독 유지 (#25) |
| issue 사이클 + slug | `pilot/tools/orchestrate-load.py` · `pilot/agents/pilot-*.md` 4종 · `preamble.md`·`messages.md`·`wrapper-protocol.md` · `pilot/hooks/protect-managed.sh` · `pilot/skills/{focus,issue}/SKILL.md` · `issues/GUIDE.md` · `pilot/tools/doctor/integrity.py` · 테스트 3종 · `docs/how-to/issue-cycle.md` | dp-skills 0.25.0/0.30.0 포팅 — work_mode 계약·이슈 블록 자기완결 인라인·slug 규약. qa/lint/인터뷰/oq-gate 이식 제외, 사내 식별자 0건 (#26) |
| context-search 도구 | `pilot/tools/context-search.py` (신규) · `pilot/tools/orchestrate-load.py` (힌트 1줄) · `pilot/skills/context/shared/wrapper-protocol.md` §6 · `pilot/skills/context/domain/scope-exploration.md` · `pilot/tools/confluence.py` `cmd_search` | 섹션 단위 결정적 랭커 — 질의 3형식·점수표·read_hint. 표준 라이브러리만, 읽기 전용, soft 배선 (#27) |
| 신선도 힌트 | `pilot/tools/freshness.py` (신규) · `pilot/tools/orchestrate-load.py` (4)·5) 직후) · `pilot/tools/doctor/integrity.py` `check_project` · `drift-protocol.md` · `GUIDE.md`·`state-schema.md` (F-E 문서 정정) | file:line 인용 파싱 → `learned_at`>git>mtime 비교 → `[신선도]` 힌트·doctor WARN. 신호만, 자동 수정 금지 (#28) |
| frontmatter 매니페스트 | `pilot/skills/learn/SKILL.md` Phase 4 · `references/heuristics.md` · `pilot/tools/orchestrate-load.py` (`context_manifest`) · `wrapper-protocol.md` §4 · `pilot/tools/doctor/integrity.py` `check_workspace` | 본문 frontmatter 5 키 + 30줄 스캔 매니페스트(200 캡) + 캡 WARN 3종. 마이그레이션은 `--fix` 제안 후 승인 (#29) |
| 경로 트리거 | `pilot/skills/learn/SKILL.md` Phase 5 · `pilot/tools/doctor/integrity.py` · (C2 시) `pilot/hooks/context-pointer.sh` + `hooks.json` PostToolUse | `.claude/rules/pilot-{domain}.md` 포인터 파일(C1) 또는 훅 additionalContext(C2). **실측 후 C1/C2 확정 전 구현 금지** (#30) |

---

## 구현 패턴

> 이 프로젝트 고유 패턴 (특정 콜백 체인, 트랜잭션 경계, 도메인 특화 쿼리 헬퍼 등) 을 여기에 기술한다.
> 일반적 언어·프레임워크 관행은 팀 `conventions_doc` (MANIFEST 선언) 을 따르고, 언어 중립 메타 원칙은 [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) 를 따른다.

---

## 주의사항

> 이 프로젝트 고유의 엣지 케이스·제약을 여기에 기술한다.
> 예: 특정 DB 단일 조회, 외부 API 호출 금지, 상태값 전환 규칙 등.

---

## 코드 생성 후 검증

코드 작성 완료 시 체크리스트를 합쳐 적용한다:

- **플러그인 공통 evals** — [`evals/coding.json`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/evals/coding.json) 의 언어 중립 케이스 (`existing-code-modification` 등).
- **프로젝트 언어별 evals** — `workspace/context/config.md` 의 `conventions_evals` 가 가리키는 파일. 언어·프레임워크별 케이스 (예: 컨트롤러·모델·서비스 레이어 가드) 는 팀이 정의한다.

작업 유형에 해당하는 케이스의 `criteria` 를 체크리스트로 확인. 미충족 시 수정 후 재확인. 상세 Merge 규칙: [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) § 검증.
