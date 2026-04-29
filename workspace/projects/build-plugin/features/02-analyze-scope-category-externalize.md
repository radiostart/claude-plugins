# #02 analyze scope 카테고리 외부화 (`/pilot:create-feature` 동일 적용)

> source: design-pilot-generic-2026-04-29.md

## 요구사항

- **조건**: `workspace/context/config.md` 에 신규 섹션 `## scope 카테고리` 정의 가능. analyze SKILL.md 본문의 5-2 단계가 config lookup 형태로 generalize 됨. SKILL.md default 섹션에 web-app 매핑 (Routes/Models/Services) 이 그대로 유지 + "config 가 비면 사용" 주석.
- **트리거**: `/pilot:analyze` 또는 `/pilot:create-feature` 호출 시 5-2 단계 진입.
- **기대결과**: scope/{domain}.md 의 매칭 H2 표를 추출하여 project.md 의 `## 관련 파일` 안 H3 표로 기입. config 비어있으면 SKILL.md default 사용 (기존 거동). 사용자가 config 에 행 override 시 즉시 반영.

## 비즈니스 규칙

- **표 스키마**: `| scope 헤더 | project.md 대상 H3 | 표 헤더 (3 컬럼) |`
- **default 매핑** (SKILL.md default 섹션 유지):

  | scope 헤더 | project.md 대상 H3 | 표 헤더 |
  | --- | --- | --- |
  | `## Routes` | Endpoints | `엔드포인트, Method, 목적` |
  | `## Models` | Models | `Class, DB, 목적` |
  | `## Services` | Services | `Class, 파일, 목적` |

- **사용자 행 조작**: 추가·교체·삭제 가능. 빈 표 → 5-2 가 해당 표만 skip.
- **`/pilot:create-feature` 동일 적용**: prompts 동기화 단계 (analyze 5-2 를 인용 호출) 에 동일 lookup 적용. 단일 SKILL.md 본문 갱신으로 두 진입점 모두 커버.
- **책임 위치**: analyze SKILL.md 5-2 본문에 "config.md 의 `## scope 카테고리` 를 먼저 Read" 1 줄 추가. create-feature SKILL.md 가 analyze 5-2 를 인용 호출하므로 자동 동일 거동.

## 예외 케이스

- **MANIFEST 진입 파일에 scope 헤더 없음** (config 또는 default 매핑의 헤더가 진입 파일에 부재): 해당 표만 skip + `[INFO]` 1 줄 (`MANIFEST 진입 파일에 {scope 헤더} 없음 — 5-2 에서 해당 표 skip`). `analyzed: true` 게이트는 정상 켬 (Open Q #3 결정).
- **scope 파일 자체 부재**: 동일하게 skip (기존 5-2 거동과 일관).
- **config 의 빈 표 (헤더만 있고 행 없음)**: SKILL.md default 사용 (= config 부재와 동일 처리).
- **config 의 `project.md 대상 H3` 컬럼이 부적절 문자 포함**: doctor 가 ERROR (#04 doctor 검증 룰).
