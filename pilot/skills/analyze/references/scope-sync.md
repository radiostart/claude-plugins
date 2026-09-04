# analyze — scope 동기화 & Open Questions

`/pilot:analyze` 의 5-1.5 (scope 자동 생성), 5-2 (cross-domain detect + Open Questions 갱신), `--force` prompt-origin 보호 알고리즘. 본문 SKILL.md 의 분량을 줄이기 위해 분리.

---

## `--force` 실행 시 prompt-origin 보호

`--force` 는 기존 features/ 파일을 덮어쓸 수 있다. 그 전에 `/pilot:create-feature` 로 생성된 **prompt-origin features** 가 있는지 확인하고 사용자에게 승인받는다 (자동 진행 시 사용자 의도로 만든 기능 명세가 소리 없이 사라져 데이터 손실로 직결되기 때문):

1. `features/*.md` 를 Grep 하여 `> source: prompt` 태그가 있는 파일 목록 수집.
2. 1 건 이상 있으면 사용자에게 경고 + 승인 대기:

   ```
   ⚠ --force 재분석이 prompt-origin features 를 덮어쓸 가능성이 있습니다:
     - features/05-<feature-slug-a>.md (source: prompt)
     - features/07-<feature-slug-b>.md (source: prompt)

   이 파일들은 /pilot:create-feature 로 생성됐으며, docs/ 에 대응 원본이
   없습니다. --force 진행 시 slug 충돌이 발생하면 덮어쓰여 데이터가 손실될
   수 있습니다. 계속? (y/n)
   ```

3. 사용자 `n` → 종료. `y` → 진행. 명시 승인 없이 자동 진행하지 않는다.

0 건이면 이 절차를 건너뛴다.

---

## 5-1.5. scope/{domain}.md 자동 생성

5-2 진입 전 scope 파일 부재를 detect 하고 자동 생성한다.

**트리거 조건 (둘 다 만족):**

- `workspace/context/scope/{domain}.md` 부재 또는 빈 파일.
- MANIFEST 진입파일 (`workspace/context/{domain}/index.md` 또는 `workspace/context/{domain}.md`) 에 `config.md` 의 `## scope 카테고리` `scope 헤더` 컬럼 값과 일치하는 H2 헤더 존재.

**본문 구성:**

- H2 헤더 = `config.md` 의 `scope 헤더` 컬럼 값 그대로 (예: `## Routes`·`## Models`·`## Services`).
- 표 헤더 = `config.md` 의 `표 헤더` 컬럼 값 (예: `엔드포인트, Method, 목적`).
- 표 본문 행 추출 우선순위:
  1. `workspace/context/{domain}/index.md` 본문의 매칭 표 (사용자 수동 정의 가능성). 복사 시 표 위 **고지 3 줄** ([learn extraction](../../learn/references/extraction.md) § Routes 표 고지 의무) 도 함께 복사한다 — 고지가 떨어지면 선별 표가 전수 목록으로 읽힌다.
  2. 본문 추출 실패 → 표 헤더만 있는 빈 표 + `[INFO] scope/{domain}.md 표 본문 추출 실패 — 사용자 수동 채움 권장` 1 줄.

**idempotency:**

- `scope/{domain}.md` 가 이미 존재 (빈 파일 아님) → 새로 만들지 않는다. 5-2 가 그대로 사용.
- 사용자가 직접 작성한 행도 그대로 보존. 자동 갱신은 별도 옵션 (`/pilot:analyze --regen-scope` v2 외).

> **A2 runtime fallback**: 본 단계 실패 (MANIFEST 진입파일 부재·본문 추출 실패) → 빈 표 + INFO 1 줄 + 5-2 진행 (abort 안 함).

**예외:**

- MANIFEST 진입파일 부재 → scope 파일 생성 skip + `[INFO] MANIFEST 진입 파일 없음 — scope 파일 생성 skip` 1 줄. 5-2 도 skip.
- `config.md` 의 `## scope 카테고리` 빈 표 → default 매핑 사용 (Routes/Models/Services → Endpoints/Models/Services).
- `scope 헤더` 컬럼 값이 `## ` prefix 미준수 → 모델 자기 검증으로 발견 시 A2 fallback 으로 default 적용 (stderr `[WARN] config.md ## scope 카테고리: scope 헤더 '## ' prefix 미준수 — default 사용` 1 줄, abort 안 함). doctor 는 이 스키마를 더 이상 사전 차단하지 않는다.

---

## 5-2. `## 관련 파일` 갱신 — 상세

> **config lookup**: 본 단계 시작 전 `workspace/context/config.md` 의 `## scope 카테고리` 섹션을 Read. 표 행이 default 매핑보다 우선. 잘못된 행은 stderr `[WARN] config.md ## scope 카테고리: {사유} — default 사용` 1 줄 (abort 안 함).
>
> **A2 runtime fallback**: config 표의 각 행을 사용 전 검증 (컬럼 수·헤더 일치). 잘못된 행은 무시하고 default 사용. doctor 가 별도 실행될 때만 ERROR 로 보고.

로드한 `scope/{domain}.md` 의 매칭 H2 섹션 표를 추출해 project.md 의 `## 관련 파일` 표를 자동 기입한다.

> default — `workspace/context/config.md` 의 `## scope 카테고리` 가 비어있을 때 사용.
> **canonical** — 아래 3컬럼 표가 scope 카테고리 default 의 유일한 정본이다. analyze·project·init·create-feature·doctor 는 이 표를 참조하며 값을 복제하지 않는다.

| scope 헤더 | project.md 대상 H3 | 표 헤더 |
| --- | --- | --- |
| ## Routes | Endpoints | 엔드포인트, Method, 목적 |
| ## Models | Models | Class, DB, 목적 |
| ## Services | Services | Class, 파일, 목적 |

**프로세스:**

1. project.md 의 `## 관련 파일` 섹션을 찾는다 (없으면 `## 에이전트 호출 흐름` 뒤에 GUIDE.md 템플릿대로 생성).
2. config (또는 default) 매핑의 각 행을 순서대로 처리:
   - scope/{domain}.md 에서 `scope 헤더` 일치 H2 섹션을 찾는다.
   - 섹션 없으면 해당 표만 skip + `[INFO] MANIFEST 진입 파일에 {scope 헤더} 없음 — 5-2 에서 해당 표 skip` 1 줄. `analyzed: true` 게이트는 정상 켬.
   - 섹션 있으면 `project.md 대상 H3` 의 이름으로 H3 표를 `표 헤더` 형식에 맞춰 기입.
3. **Endpoints 표**:
   - **전제**: 도메인 문서의 `## Routes` 는 전수 목록이 아니라 **선별 기재**다 ([learn extraction](../../learn/references/extraction.md) § Routes 표) — 5-1.5 가 그 표를 복사해 만든 `scope/{domain}.md` 도 같다. 표의 행 수는 도메인의 라우트 수가 아니고, 표에 없는 route 가 없는 route 라는 근거도 아니다.
   - features/ 요구사항과 관련된 route 를 우선 선별한다. 매칭은 **경로·핸들러명**을 1 순위로 본다 — 목적 칸에는 재진술 금지 규율상 "경로만 봐선 모를 것" 만 적혀 있어 feature 문구와 키워드가 겹치지 않을 수 있다 (Models·Services 표는 목적 칸이 아예 빈칸일 수 있다 — extraction § 목적 컬럼).
   - 매칭이 불명확해도 **표의 나머지 행을 통째로 옮기지 않는다** — 선별 표를 복제해봐야 "도메인 전체" 가 되지 않으면서 project.md 만 전수 목록처럼 읽힌다. 실재 확인이 필요하면 표 위 고지 3 줄의 **전수 조회 수단**을 쓰고, 확인 못 한 route 는 기입하지 않는다 (추측 금지).
4. **Models 표**·**Services 표**: scope 의 해당 섹션에서 추출.

**갱신 규칙:**

- features/ 에 명시적으로 언급된 모델·서비스·라우트는 빠뜨리지 않고 포함 (누락 시 planner 가 영향 범위를 잘못 잡음).
- scope 에 없지만 features/ 에 등장한 대상은 추가하되 `목적` 열 끝에 `(from features/NN-{slug})` 주석을 붙인다. 이 주석은 **출처 표기**다 — "scope 에 없음" 이지 "아직 구현되지 않음" 이 아니다.
  - **라우트는 특히 그렇다** — Routes 표는 선별 기재라 실재하는 라우트도 표에 없다. "scope 에 없음" 을 "신규" 로 옮겨 적으면 planner 가 **기존 엔드포인트를 신규 구현 대상으로 잡는다**.
  - 실재를 확인했으면 (고지 3 줄의 전수 조회 수단, 또는 라우트 정의 파일) 주석 없이 기입한다. 확인하지 못했으면 주석 뒤에 `— 실재 미확인` 을 덧붙여 판정을 planner 의 영향 범위 탐색으로 넘긴다 (추측 금지).
- 기존 사용자 수동 기입 행은 보존하되 중복만 제거.
- 빈 행(`|  |  |  |`) 은 모두 삭제.
- config 빈 표 (헤더만 있고 행 없음): default 사용.

---

## 5-2. cross-domain 의존성 detect (#09)

features/ 키워드와 scope/{domain}.md 매칭 시도 후, cover 되지 않는 외부 클래스/도메인 reference 를 감지한다.

`workspace/context/MANIFEST.md` 의 `## 외부 도메인 reference` 표 lookup:

- 매칭되는 도메인 있으면:
  ```
  [INFO] {외부 도메인} 의존성 감지 — 먼저 `/pilot:learn {추천 경로}` 권장
  ```
  `/pilot:learn` 완료 후 `/pilot:analyze` 재실행을 권장한다 (INFO 문구는 create-feature 단건 detect 와 동일 — 재분석 권장 뉘앙스는 이 산문이 담당).
- 표 부재 시 또는 매칭 없으면: 안내 없이 진행 (abort 안 함).

> **A2 runtime fallback**: lookup 실패 시 → 분석 정상 진행, INFO 출력 안 함.

---

## 5-2. Open Questions 섹션 보존 + 갱신 (#11)

features/ 갱신 시 기존 features/NN-*.md 파일의 `## Open Questions` 섹션을 다음 규칙으로 처리한다.

1. 기존 `## Open Questions` 섹션이 있으면 보존. 기존 `- (없음)` 행, 작성자 수동 기입 행 모두 그대로 유지.
2. cross-domain detect 결과 (외부 도메인 매칭) → 해당 feature 의 `### (b) cross-domain 산출물 부재` 에 행 추가만 (중복 행은 skip — 판정 키는 **외부 도메인명**: 동일 외부 도메인을 가리키는 (b) 행이 이미 있으면 체크 상태 `- [x]`·답변 append 여부와 무관하게 skip. 소비 규칙: [interview.md](../../context/shared/interview.md)).
3. 신규 features/NN-*.md 생성 시에는 `## Open Questions` 4 카테고리 섹션 + `- (없음)` 반드시 포함.
4. `## Open Questions` 섹션이 아예 없는 기존 파일은 수정하지 않음 (doctor 가 INFO 로 안내).

Open Questions 4 카테고리 분류 기준은 [`open-questions.md`](../../context/shared/open-questions.md) 참조 (create-feature 와 공유).

> **A2 runtime fallback**: Open Questions 갱신 실패 시 → 해당 파일 skip, 분석 정상 진행.
