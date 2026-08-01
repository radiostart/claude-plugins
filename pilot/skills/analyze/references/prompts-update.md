# 6 단계: prompts/ 자동 갱신 상세

features/ 분석 결과를 바탕으로 `workspace/projects/{PROJECT}/prompts/` 의 에이전트 파일을 자동 갱신한다. 에이전트 파일이 없으면 새로 생성하고, 이미 존재하면 features/ 내용을 반영하여 업데이트한다.

이 6 단계는 래퍼의 pre/post-analyze 게이트 판정 필드 (`.agent-state.yml` 의 `analyzed`) 를 `true` 로 전환시키는 유일한 경로다 (6-4 단계에서 실제 전환 수행).

## `[analyze-managed]` 주석의 의미

6-1 / 6-2 / 6-3 이 갱신하는 섹션들은 example 템플릿에 `<!-- [analyze-managed] -->` 주석이 달려 있다. 이 주석이 있는 섹션은 다음 analyze 실행 시 **덮어쓰기 대상** 이라 사용자 수동 편집 내용은 유실된다. 사용자가 커스텀 내용을 추가하고 싶을 때는 이 주석이 없는 별도 섹션 (`## 주의사항`, `## 구현 패턴` 등) 에 기술해야 한다.

---

## 6-1. planner.md 갱신

features/ 에서 추출한 내용 + 메인 5-2 에서 로드한 `scope/{domain}.md` 매칭 결과로 `## 기능별 사전 확인 사항` 섹션을 갱신한다.

- 각 feature 의 **요구사항** (조건/트리거/기대결과) 과 **상태 전환** 정보를 요약하여 기능별 소항목으로 작성한다.
- 각 feature 하위에 **관련 파일 범위** subsection 을 추가해 scope 에서 매칭된 Routes·Models·Services 만 선별 기입한다 (탐색 범위 사전 정의 → planner 가 영향 범위 파악 시 활용).
- 기존에 사용자가 수동으로 추가한 내용 중 feature 와 무관한 항목 (`## 기능별 사전 확인 사항` 밖에 위치) 은 보존한다.

**갱신 형식:**

```markdown
## 기능별 사전 확인 사항

### {기능명} (features/{NN}-{slug}.md)

- {핵심 조건/트리거/기대결과 요약}
- {상태 전환이 있으면 전환 전→후 나열}
- {비즈니스 규칙 중 플래닝에 영향을 주는 항목}

**관련 파일 범위** (scope/{domain}.md 매칭):
- Routes: `/<entity>s/:id/<action>` (POST)
- Models: `<Entity>`, `<EntityItem>`
- Services: `<DomainService>`
```

**매칭 규칙:**

- feature 의 요구사항·상태 전환·예외 케이스에서 언급된 route/model/service 이름을 scope 와 대조한다.
- 매칭이 없거나 불명확하면 해당 하위 항목은 생략한다 (추측을 들이면 후속 단계 전체가 오염되므로).

---

## 6-2. generator.md 갱신

features/ 내용 + 5-2 에서 로드한 `scope/{domain}.md` 로 기술 레퍼런스를 갱신한다.

**주요 변경점:**

- `## 컨텍스트 로드` 를 **구체 도메인 파일 경로** 로 기입한다 (일반 안내 금지). "반드시 로드" 같은 지시문은 넣지 않는다 — 래퍼가 자동 로드하는 참조 목록일 뿐이며, 지시문이 들어가면 모델이 중복 로드를 시도해 토큰을 낭비한다.
- `## 핵심 서비스/모델` 표에 scope 의 Services·Models 중 features/ 와 관련된 행을 자동 기입한다.
- `## 코드 생성 후 검증` — evals/coding.json 참조 섹션은 항상 유지한다.
- 기존에 사용자가 수동으로 추가한 `## 주의사항` · `## 구현 참고 사항` 등 커스텀 섹션은 보존 (덮어쓰지 않는다).

**갱신 형식 예시:**

```markdown
<!-- [analyze-managed] -->
## 컨텍스트 로드

이 프로젝트가 의존하는 도메인 지식 (래퍼가 자동 로드 — 수동 Read 불필요):

- `workspace/context/MANIFEST.md`
- `workspace/context/scope/<domain>.md`
- `workspace/context/rules/<domain>.md`
- `workspace/context/enums.md` — 관련 섹션: `<Entity>`

<!-- [analyze-managed] -->
## 핵심 서비스/모델

| 대상 | 파일 | 용도 |
| --- | --- | --- |
| `<Entity>` | {source_root}/models/<entity>.{ext} | (예시 entity) |
| `<DomainService>` | {source_root}/services/<domain>_service.{ext} | (예시 domain service) |

<!-- [analyze-managed] -->
## 관계 구조

{features/에서 언급된 모델 간 관계만 text 다이어그램으로}

## 구현 참고 사항

{features/ 의 비즈니스 규칙·엣지 케이스 중 구현 시 주의할 항목. analyze 는 이 섹션을 덮지 않는다 — 사용자 수동 편집 영역}

## 코드 생성 후 검증

... (evals/coding.json 참조)
```

**갱신 시 규칙:**

- `## 컨텍스트 로드` 파일 경로는 로드한 scope/domain 실제 경로로 기입한다.
- `## 핵심 서비스/모델` 은 scope/{domain}.md 의 Models·Services 표와 features/ 에 언급된 대상을 조합한다. features 언급 > scope 목록 순서로 정렬한다.
- features/ 에 명시된 정보만 반영한다. 코드베이스를 추가 탐색해 시그니처·메서드를 추측하지 않는다 (추측은 generator 가 잘못된 코드를 양산하는 첫 단추).
- 상태 전환 테이블이 있으면 그대로 옮긴다.
- 관계 구조는 features/ 에서 언급된 모델 간 관계만 text 다이어그램으로 정리한다.

**주입 금지 항목:** 공통 SSOT 위임 원칙은 [`analyze-inject-principles.md`](../../context/domain/analyze-inject-principles.md) 참조.

generator.md 고유:

- 코드 스니펫은 **프로젝트 고유 패턴** (특수 콜백 체인·도메인 특화 쿼리 헬퍼) 일 때만 주입한다. 일반 언어·프레임워크 관용구는 `coding.md` 로 위임.
- `## 주의사항`·`## 구현 패턴` 은 사용자 수동 편집 영역이므로 `[analyze-managed]` 없이 유지.

---

## 6-3. evaluator.md 갱신

features/ 의 **요구사항**, **비즈니스 규칙**, **예외 케이스** 를 체크리스트로 변환한다.

**분류 기준 (중복 기입 금지):**

| 섹션 | 주입 소스 |
| --- | --- |
| `## 기능 완성도` | features/ 의 **기대결과** (조건/트리거/기대결과 중 "기대결과" 만) |
| `## 프로젝트 고유 항목` | features/ 의 **비즈니스 규칙** + **예외 케이스** 중 검증 가능한 항목 |

동일 사실을 양쪽에 중복 기입하지 않는다 (evaluator 가 같은 항목을 두 번 검증하느라 시간을 낭비함). 기대결과 = 완성도, 규칙·예외 = 고유 항목.

**갱신 형식:**

```markdown
<!-- [analyze-managed] -->
## 기능 완성도

- [ ] {feature별 기대결과 충족 여부}

<!-- [analyze-managed] -->
## 프로젝트 고유 항목

- [ ] {비즈니스 규칙 검증 항목}
- [ ] {예외 케이스 처리 확인}

## 일관성

- [ ] 언어 컨벤션 준수 (coding.md 참조)
- [ ] 기존 코드 패턴과 조화

## 테스트

- [ ] 해피패스 커버
- [ ] 에러 케이스 처리
- [ ] 기존 테스트 영향 없음
```

**갱신 시 규칙:**

- 이전 evaluator.md 에서 `[x]` 로 체크된 항목은 보존한다 (이미 검증 완료된 항목 — 재실행 시 다시 검증하면 사용자가 같은 일을 두 번 한다고 느낀다).
- `## 일관성` 과 `## 테스트` 섹션은 기본 항목을 유지하되, features/ 에서 도출된 고유 항목을 추가한다.

**주입 금지 항목:** 공통 SSOT 위임 원칙은 [`analyze-inject-principles.md`](../../context/domain/analyze-inject-principles.md) 참조.

evaluator.md 고유:

- `## 전달사항 작성 가이드` 섹션은 example 템플릿의 커스텀 섹션. `[analyze-managed]` 가 아니므로 덮어쓰지 않는다.
- `## 일관성` · `## 테스트` 기본 항목은 유지하되, features/ 에서 도출된 고유 체크만 추가한다 (공통 템플릿을 매번 반복 주입하면 에이전트 파일이 기하급수적으로 비대해진다).

---

## 6-4. `.agent-state.yml` 갱신

분석이 실제 features/ 를 생성했고 6-1 / 6-2 / 6-3 갱신이 완료된 경우에만 실행한다.

1. `workspace/projects/{PROJECT}/.agent-state.yml` 을 Read 한다.
2. 파일이 없거나 `schema` 가 지원 버전 (`v1`, `v1.1`, `v1.2`) 이 아니면 에러 출력 후 중단:
   "프로젝트 상태 파일 누락 또는 구버전. `/pilot:pilot-doctor --fix` 실행 후 재시도하세요."
3. 아래 필드를 Edit 한다:
   - `analyzed: true`
   - `analyzed_at: "{ISO 8601 UTC timestamp, e.g. 2026-04-18T10:30:00Z}"`
   - `last_analyzed_features: {현재 features/*.md (.plan.md 제외) 개수}`
   - `domain: {사용자가 확인한 도메인}` — 5 단계에서 질의·확인한 값. null 로 두지 않는다 (null 이면 다음 analyze 가 다시 도메인 질의를 해 사용자가 같은 답을 두 번 입력하게 된다).
4. 그 외 필드 (`schema`, `tdd`, `docs_last_fetched_at`) 는 건드리지 않는다. `schema` 가 `v1` 또는 `v1.1` 이면 이번 기회에 최신(`v1.2`) 으로 업그레이드 + `domain` 기록까지 한 번에 처리.

이 단계를 통과해야 wrapper (`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator`) 가 post-analyze 분기 (`scope` 원본 재로드 생략) 로 동작한다.

`analyzed_at` 과 `last_analyzed_features` 는 `/pilot:pilot-doctor` 가 **drift 감지** 에 사용한다:

- features 개수가 `last_analyzed_features + 1` 초과 → "재분석 권장" WARN
- `context/scope/{domain}.md` mtime 이 `analyzed_at` 보다 최근 → "scope 업데이트됨, `--regen-agents` 권장" WARN
- `docs_last_fetched_at` 이 `analyzed_at` 보다 최근 → "기획서 업데이트됨, `--force` 재분석 권장" WARN

스키마 상세: [state-schema.md](../../context/lifecycle/state-schema.md).

---

## 6-5. 무결성 검증 (자동)

모든 갱신 완료 후 아래를 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

출력 규칙: [`pilot-doctor/SKILL.md`](../../pilot-doctor/SKILL.md) § 임베디드 호출 시 출력 규칙 (정본) 참조.
