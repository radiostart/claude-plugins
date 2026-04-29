# Generator — build-plugin

코드 구현 시 참조하는 기술 레퍼런스.

**역할:** 계획 (plan.md) 에 따라 코드 작성 + **제출 전 sanity check** (`evals/coding.json` 체크리스트로 자체 검증). 완성도 심사는 Evaluator 가 담당 — 본 단계는 "내가 방금 쓴 코드가 컨벤션을 벗어나지 않았나" 를 자가 확인.

> **⚠️ 이 파일은 `@generator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/generator.md`](${CLAUDE_PLUGIN_ROOT}/agents/generator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@generator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
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
