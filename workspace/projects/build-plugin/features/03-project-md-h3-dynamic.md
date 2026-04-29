# #03 project.md 템플릿 H3 동적 생성 + SSOT

> source: design-pilot-generic-2026-04-29.md

## 요구사항

- **조건**: `pilot/skills/context/lifecycle/projects/example/project.md` 의 `## 관련 파일` H2 본문이 가이드 주석만 갖고 H3 비어있음 (현재 하드코드된 `### Models / ### Endpoints / ### Services` 제거).
- **트리거**: `/pilot:project {PROJECT}` 호출 시 신규 폴더 생성 직후 (template 복사 직후 1 회 가공).
- **기대결과**: project skill 이 config.md 의 `## scope 카테고리` 의 `project.md 대상 H3` 컬럼을 따라 `## 관련 파일` 안에 H3 + 빈 표 채움. 재실행 시 기존 H3 보존. config 비어있으면 SKILL.md default (Models/Endpoints/Services) 사용 — 기존 거동 유지.

## 상태 전환

| 전환 전 | 전환 후 | 조건 | 처리 |
| --- | --- | --- | --- |
| example 템플릿 복사 직후 (`## 관련 파일` 비어있음) | H3 + 빈 표 채워짐 | `/pilot:project` 가 신규 폴더 생성 시점 | 1 회 가공 (project skill 책임) |
| `/pilot:project` 재실행 (기존 H3 존재) | 기존 H3 그대로 | 사용자 수동 추가 H3 보존 | 변경 없음 |
| `/pilot:analyze` 또는 `/pilot:create-feature` 5-2 진입 | 표 본문 채워짐 | 매번 갱신 | analyze/create-feature 책임 |
| 사용자가 H3 삭제 후 `/pilot:project` 재실행 | 삭제된 H3 복구 안 함 | 사용자 의도로 간주 | 변경 없음 |

## 비즈니스 규칙

- **SSOT 정의**:
  - **H3 헤더** = `/pilot:project` 가 1 회 생성 (신규 폴더 생성 시점, example 복사 직후 1 회 가공)
  - **표 본문** = `/pilot:analyze` 또는 `/pilot:create-feature` 가 매번 갱신 (5-2 단계)
  - **사용자 수동 추가 H3** = 양쪽 모두 보존 (analyze 5-2 의 기존 보존 규칙 "기존 사용자 수동 기입 행은 보존" 을 H3 단위로 확장)
  - **사용자가 H3 삭제** = 다음 `/pilot:project` 재실행 시 복구하지 않음
- **template 변경**: example/project.md 의 `## 관련 파일` H2 + 가이드 주석만 유지. H3 + 표 모두 제거.
- **project skill 변경**: SKILL.md 본문 절차에 "template 복사 직후 config.md `## scope 카테고리` 의 `project.md 대상 H3` 컬럼을 읽어 `## 관련 파일` 안에 H3 + 빈 표 추가" 단계 신설.
- **fallback**: config 비어있으면 SKILL.md default 표 사용 (현재 하드코드된 Models/Endpoints/Services 와 동일 결과).

## 예외 케이스

- **example/project.md 자체 변경되어 `## 관련 파일` H2 없음**: project skill 이 H2 + H3 모두 새로 생성.
- **config 의 `project.md 대상 H3` 값이 부적절 문자 포함** (슬래시·콜론·#·| 등): doctor ERROR (#04 doctor 검증 룰).
- **재실행 시 기존 project.md 가 신규 H3 (config 추가 후) 누락**: `/pilot:project` 재실행으로 누락 H3 보충 (기존 H3 는 보존).
