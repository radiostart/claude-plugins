# #01 learn 언어 패턴 외부화 (D10 default 폐지)

> source: design-pilot-generic-2026-04-29.md

## 요구사항

- **조건**: `workspace/context/config.md` 에 `## learn 언어 패턴` 섹션이 정의 가능. **SKILL.md 본문의 default 표는 D10 결정으로 폐지** — Phase 2 본문에서 표 0, 사용자 자유 정의 안내만. README example block 이 학습 가이드.
- **트리거**: `/pilot:learn {진입점}` 호출. 진입점 파일 확장자 추론 → config.md lookup → 매칭 행 없으면 **폴더 인접성 fallback** (SKILL.md Phase 2 의 기존 fallback 로직 그대로).
- **기대결과**: learn 의 Phase 2 Inventory 단계가 config 의 두 표 (의존성 추적 + 역할 분류) 를 lookup. config 비어있으면 폴더 인접성 fallback. 사용자가 config 에 자기 언어/프레임워크 행 정의 시 즉시 정확 동작. **backward-compat 보장은 D10 의 M1 자동 마이그레이션 (features/05) 으로 위임** — `/pilot:doctor --fix` 가 v0.1.0→v0.2.0 업그레이드 감지 시 사용자 config 에 v0.1.0 default 5 언어 표 자동 주입.

## 비즈니스 규칙

- **표 스키마 (1) 의존성 추적**: `| 언어 | 의존성 추출 패턴 |` (2 컬럼). Grep 패턴 문자열. **D10 default 폐지** — SKILL.md 본문에서 표 0. config 가 빈 표면 폴더 인접성 fallback. 사용자가 자기 언어 행 정의 (예: `Ruby` `require_relative · 클래스 참조 → app/**/*.rb Glob`).
- **표 스키마 (2) 역할 분류 — long-form (D9 결정 + D10 default 폐지)**: `| 역할 | 식별 패턴 |` (2 컬럼). 한 행 = 한 역할 (`routes`·`controllers`·`services`·`models`·`helpers`·`other` 또는 사용자 임의 카테고리). 식별 패턴 = 다중 언어·프레임워크 패턴 OR 결합 (`·` 구분자, 예: `*_controller.rb·@RestController·*.controller.ts`). **D10 default 폐지** — SKILL.md 본문에서 표 0. 사용자가 행을 자기 프로젝트 패턴으로 정의. 빈 표면 폴더 인접성 fallback.
- **언어 추론 매핑** (v1 default):
  - `.rb` → ruby
  - `.kt` / `.kts` → kotlin
  - `.ts` / `.tsx` → typescript
  - `.py` → python
  - `.go` → go
- **lookup 우선순위**: config.md 신규 섹션 행 → SKILL.md default 섹션 행. 동일 (언어, 역할) 키 행이 양쪽에 있으면 config 우선.
- **책임 위치**: SKILL.md Phase 2 본문 절차에 "config.md 의 `## learn 언어 패턴` 섹션을 먼저 Read" 1 줄 추가. 파싱은 기존 markdown 표 파서 재사용.
- **D10 default 폐지** — `pilot/skills/learn/SKILL.md` 의 default 표 (의존성 추적 + 역할 분류) 본문에서 제거. Q1 default 격하 blockquote 도 learn 의 두 표에 한해 폐지 (SKILL.md 본문에 표 0 이라 적용 대상 없음). `pilot/skills/analyze/SKILL.md` 5-2 의 scope 카테고리 default 표 + `pilot/skills/context/lifecycle/projects/example/project.md` 의 가이드 주석은 #02·#03 작업 결과 그대로 유지 (Q1 패턴 2 곳).
- **README example block (학습 가이드)**: `pilot/README.md` 또는 `pilot/skills/learn/README.md` 에 v0.1.0 default 5 언어/역할 분류 6 행 표를 example 으로 게시. 사용자가 복사하여 자기 `workspace/context/config.md` 에 붙여넣을 수 있게.
- **사용자 override 방식**: 신규 행 추가 또는 기존 default 행 위에 동일 (언어, 역할) 키 행 덮어쓰기.

## 예외 케이스

- **다중 확장자·확장자 없음** (`Makefile`·shebang 등): v1 외, v2 마일스톤. 본 v1 에서는 확장자 추론 실패 시 폴더 인접성 fallback 적용.
- **config.md 의 신규 섹션 부재**: doctor 가 INFO 1 줄 (WARN 아님). 폴더 인접성 fallback 동작. backward-compat 은 features/05 의 M1 자동 마이그레이션으로 보장.
- **config 표 컬럼 수 불일치**: doctor ERROR. 수정 안내 메시지 출력.
- **config 빈 표 (헤더만, 행 0)**: D10 결정으로 정상. SKILL.md default 가 부재이므로 폴더 인접성 fallback 동작.
- **`--language` CLI 옵션 요청**: v1 외. v2 에서 검토 (모노레포·shebang 케이스 동시 해결).
