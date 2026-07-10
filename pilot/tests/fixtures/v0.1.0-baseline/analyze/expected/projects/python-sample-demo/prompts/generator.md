# Generator — python-sample-demo

코드 구현 시 참조하는 기술 레퍼런스.

**역할:** 계획 (plan.md) 에 따라 코드 작성 + **제출 전 sanity check** (`evals/coding.json` 체크리스트로 자체 검증). 완성도 심사는 Evaluator 가 담당 — 본 단계는 "내가 방금 쓴 코드가 컨벤션을 벗어나지 않았나" 를 자가 확인.

> **⚠️ 이 파일은 `@pilot-generator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-generator.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-generator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-generator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [prompts-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/prompts-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 컨텍스트 로드

이 프로젝트가 의존하는 도메인 지식 (래퍼가 자동 로드 — 수동 Read 불필요):

- `workspace/context/MANIFEST.md`
- `workspace/context/python-sample/index.md` (도메인 python-sample 진입 파일)
- `workspace/context/python-sample/inventory.md` (의존성 추적 + 역할 분류)

---

<!-- [analyze-managed] -->
## 핵심 변경 대상

| 대상 | 파일 | 용도 |
| --- | --- | --- |
| 주문 엔티티 | `models/order.py` | Order·OrderItem·OrderStatus |
| 결제 서비스 | `services/checkout.py` | pay·cancel 메서드 상태 전환 |
| 라우트 | `routes.py` | `/orders` POST·GET·pay·cancel |

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
