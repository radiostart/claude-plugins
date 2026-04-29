# Planner — build-plugin

구현 대상 기능을 분석하고, Generator가 실행 가능한 단계별 계획을 수립한다.

> **⚠️ 이 파일은 `@planner` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/planner.md`](${CLAUDE_PLUGIN_ROOT}/agents/planner.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@planner` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 기능별 사전 확인 사항

### #00 회귀 골든 픽스처 (features/00-regression-fixture.md)

- 조건: `pilot/tests/fixtures/v0.1.0-baseline/` 미존재. v0.1.0 의 `/pilot:learn` `/pilot:project` `/pilot:analyze` 산출물 + #04 의 PASS/ERROR 케이스 fixture 캡처 가능.
- 트리거: 수동 1 회 캡처 + Next Steps 5번에서 `diff.sh` 재실행.
- 기대결과: config 비어있을 때 v1 출력이 v0.1.0 capture 와 diff 0 (#01·#02·#04 backward-compat 1 차 검증). #03 default H3 도 v0.1.0 의 하드코드 H3 와 동일.

**관련 파일 범위**:
- 신설: `pilot/tests/fixtures/v0.1.0-baseline/` (전체 트리, 1 언어 input)
- 참조: `pilot/skills/{learn,analyze,project}/SKILL.md` 의 default 섹션 + `example/project.md`

### #01 learn 언어 패턴 외부화 (features/01-learn-language-pattern-externalize.md)

- 조건: `workspace/context/config.md` 신규 섹션 `## learn 언어 패턴` 정의 가능, SKILL.md 본문의 두 표 default 섹션 격하 + "config 비면 사용" 주석.
- 트리거: `/pilot:learn` 호출 시 진입 파일 확장자에서 언어 추론 → config.md lookup → 매칭 없으면 default.
- 기대결과: config 비면 0.1.0 동일 거동 (회귀 픽스처 검증), 사용자 override 시 즉시 반영.

**관련 파일 범위**:
- 변경: `pilot/skills/learn/SKILL.md` (Phase 2 본문 lookup 추가)
- 변경: `workspace/context/config.md` (신규 섹션, 표 1·2)
- 회귀 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/learn/`

### #02 analyze scope 카테고리 외부화 (features/02-analyze-scope-category-externalize.md)

- 조건: config.md 신규 섹션 `## scope 카테고리` 정의 가능, SKILL.md default (Routes/Models/Services 매핑) 격하.
- 트리거: `/pilot:analyze` 또는 `/pilot:create-feature` 의 5-2 진입.
- 기대결과: scope/{domain}.md 의 매칭 H2 표를 추출해 project.md `## 관련 파일` 안 H3 표로 기입. config 빈 행 또는 MANIFEST 표 부재 시 해당 표만 skip + INFO 1 줄, `analyzed:true` 정상 게이트.

**관련 파일 범위**:
- 변경: `pilot/skills/analyze/SKILL.md` (5-2 본문 lookup 추가, MANIFEST 부재 처리)
- 변경: `pilot/skills/create-feature/SKILL.md` (5-2 인용 호출 — 동일 거동 자동 적용)
- 변경: `workspace/context/config.md` (신규 섹션)

### #03 project.md H3 동적 생성 + SSOT (features/03-project-md-h3-dynamic.md)

- 조건: example/project.md 의 `## 관련 파일` H2 본문이 가이드 주석만 갖고 H3 비어있음.
- 트리거: `/pilot:project {PROJECT}` 신규 폴더 생성 시점 (template 복사 직후 1 회 가공).
- 기대결과: project skill 이 config 의 `project.md 대상 H3` 컬럼을 보고 H3 + 빈 표 채움. 재실행 시 기존 H3 보존. 사용자 H3 삭제 후 재실행 시 복구 안 함 (사용자 의도).

**관련 파일 범위**:
- 변경: `pilot/skills/project/SKILL.md` (template 복사 후 1 회 가공 단계 추가)
- 변경: `pilot/skills/context/lifecycle/projects/example/project.md` (`## 관련 파일` H3 + 표 제거, H2 + 가이드 주석만 유지)

### #04 doctor config 정합성 검증 (features/04-doctor-config-validation.md)

- 조건: `pilot/tools/doctor/integrity.py` 에 신규 검사 함수 추가.
- 트리거: `/pilot:doctor` 또는 `python3 .../doctor.py workspace`.
- 기대결과: 신규 섹션 존재 시 스키마 검증 (컬럼 수·헤더 화이트리스트·`## ` prefix). 부재 시 INFO 1 줄. 위반 시 ERROR + 수정 안내.

**관련 파일 범위**:
- 변경: `pilot/tools/doctor/integrity.py` (신규 검증 함수)
- 신규: `pilot/tests/tools/test_doctor_integrity.py` (`test_doctor_slack.py` 패턴 답습 — unittest + importlib.util)
- 회귀 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/config/{pass-empty,pass-valid,error-*}` (test 와 fixture 공유)

> `workspace/context/scope/pilot.md` · `workspace/context/rules/pilot.md` 부재 — 본 프로젝트는 사용자 커스텀 layer 미작성. features/ 의 file:line 인용을 1 차 근거로 활용한다 (예: `pilot/skills/learn/SKILL.md:90-111`).
