# Evaluator — python-sample-demo

구현 완료 후 요구사항 충족 여부와 일관성을 검토한다.

**역할:** **완성도 심사** — Generator 의 자체 sanity check 와 별개로, features 요구사항·비즈니스 규칙·예외 케이스 충족 여부를 최종 판정. 체크리스트 `[x]` 가 이 판정의 기록.

> **⚠️ 이 파일은 `@evaluator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/evaluator.md`](${CLAUDE_PLUGIN_ROOT}/agents/evaluator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@evaluator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

---

<!-- [analyze-managed] -->
## 기능 완성도

- [ ] `project.md` 잔여 목표의 **기대결과** 모두 충족
- [ ] #01 주문 생성: `POST /orders` → Order (status=PENDING) 반환 — 로그인 사용자만
- [ ] #02 결제 처리: `POST /orders/{id}/pay` → status PENDING → PAID 전환 확인

---

<!-- [analyze-managed] -->
## 프로젝트 고유 항목

- [ ] OrderStatus 상태 전환 규칙 준수: PENDING→PAID 만 허용 (checkout.py:17)
- [ ] SHIPPED 주문 취소 불가 (checkout.py:24)
- [ ] 이미 CANCELLED 주문 중복 취소 불가 (checkout.py:26)
- [ ] `AuthService.get_user` 의 user_id 유효성 위임 확인 (checkout.py:9)

---

## 일관성

- [ ] 언어 컨벤션 준수 ([`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) 참조)
- [ ] 기존 코드 패턴과 조화 (불필요한 리팩토링 없음)

---

## 테스트

- [ ] 해피패스 커버
- [ ] 에러 케이스 처리
- [ ] 기존 테스트 영향 없음

> **비 TDD 프로젝트**는 자동 테스트 실행 단계가 없다. "읽기만 하고 끝" 을 피하려면 아래 수동 확인 중 적합한 것을 선택:
>
> - dev server / console 에서 기능 직접 실행 (UI / API 응답 육안 확인)
> - 대표 시나리오를 수기 테스트 케이스로 `## 테스트` 에 체크 항목으로 추가
> - 변경 주변 기존 테스트가 있으면 `{test_command} {경로}` 로 회귀 확인

---

## 전달사항 작성 가이드

래퍼가 검토 완료 후 요구하는 `## 에이전트 간 전달사항` (project.md) 기록 기준.

**전달할 것:**

- 신규 메서드·서비스·상수 추가 — 다음 feature 에서 재사용 가능성
- 모델 스키마·상태값 변경 — 후속 feature 의 가정 조건이 바뀜
- 제약·엣지 케이스 발견 — 다음 계획에 선행 반영 필요
- 공통 패턴 정립 (예: 특정 factory 콜백 우회 기법) — 다른 spec 재사용

**전달하지 않을 것:**

- 구현 디테일 (코드에 이미 있음 — 읽으면 됨)
- 완료된 체크리스트 항목 (이 파일에 `[x]` 로 반영됨)
- 일반적 언어·프레임워크 관행 (팀 `conventions_doc` 에 이미 있음)

**형식:**

```markdown
- [ ] {내용 1줄 + 후속 feature 에서의 반영 방향} (from #{완료 feature 번호})
```

전달할 사항이 없으면 `## 에이전트 간 전달사항` 섹션을 건드리지 않는다 (빈 항목 추가 금지).
