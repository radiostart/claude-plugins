# #06 learn SKILL.md 모호함 해소 (Phase 1 fallback + Phase 5 H2 매칭)

> source: v0.2.1 hotfix discovery (NS #5 cycle, 2026-04-29) — hotfix 후보 #2 + #5 통합

## 요구사항

- **조건**: v0.2.0 release 직후 NS #5 회귀 검증 cycle 1 회 시뮬레이션에서 `pilot/skills/learn/SKILL.md` 의 두 모호함 발견:
  - **Phase 1 도메인 도출** — `main.py`·`app.py`·`server.py`·`index.ts` 같은 일반적 진입파일 (controller/service suffix 없음, 도메인 단어 폴더 아님) 의 도메인 도출 규칙이 침묵. 사실상 부모 폴더명 fallback 으로 가야 하나 명시 안 됨.
  - **Phase 5 MANIFEST 갱신** — `## 도메인 분류` H2 헤더 정확 매칭 강제 명시 안 됨. 본문 prose 안내문에 동일 string (`## 도메인 분류` 라는 텍스트) 등장 시 "섹션이 진짜 없다" 판정 휴리스틱이 모호.
- **트리거**: `/pilot:learn {진입점}` 호출. v0.3.0 milestone 의 SKILL.md 본문 보강.
- **기대결과**: 위 두 모호함이 Phase 1·Phase 5 본문에 명시되어, LLM 이 SKILL.md 절차를 그대로 따라가며 추측·해석 없이 정확한 fallback 적용.

## 비즈니스 규칙

- **Phase 1 진입파일 폴더명 fallback**:
  - 진입파일 = 일반적 진입점 (`main.py`·`app.py`·`server.py`·`index.ts`·`index.js`·`__main__.py` 등 파일명에 도메인 식별자·역할 suffix 없음) 일 때 → **부모 폴더명을 도메인명으로 채택**.
  - 부모 폴더명도 일반적 (`src/`·`app/`·`lib/`·`source/` 등) 이면 → **2 단계 상위 폴더명** 또는 **레포 root 의 디렉터리명** fallback.
  - 모두 일반적이면 → 사용자 질의 (`/pilot:learn` 가 진행 전 도메인명 입력 prompt).
  - SKILL.md Phase 1 의 도메인 도출 표에 행 추가: `| 진입파일 = 일반 진입점 (suffix 없음) | 부모 폴더명 fallback (일반 폴더면 2단계 상위) | main.py · app.py · server.py · index.ts |`.
- **Phase 5 MANIFEST `## 도메인 분류` H2 정확 매칭**:
  - 섹션 detect = `^##\s+도메인\s*분류\s*$` 정규식 정확 매칭. **본문 prose 의 string 등장 (예: 가이드 주석 `이 섹션은 ## 도메인 분류 표를 자동 갱신합니다`) 무시**.
  - `orchestrate-load.py:parse_manifest_domain_files` 의 정규식과 동일 패턴 사용 — runtime 자동 파싱 호환 보존.
  - SKILL.md Phase 5 본문에 강조 1 줄 추가: "**H2 헤더 정확 매칭 강제** (`^##\s+도메인\s*분류\s*$`). 본문 prose 의 동일 string 등장은 무시 — `orchestrate-load.py` 자동 파싱 호환을 위해 필수."
- **default 격하 blockquote 추가 안 함**: 본 변경은 SKILL.md 본문 명료화. config.md 와 무관 (Q1 패턴 적용 대상 아님).
- **A2 runtime fallback 정합**: Phase 1 부모 폴더명 fallback 도 A2 패턴 — 도메인 도출 실패 시 사용자 질의 prompt (abort 안 함). Phase 5 H2 매칭 실패는 자동 섹션 생성 fallback (기존 룰 유지).

## 예외 케이스

- **진입파일이 절대경로** (예: `/Users/me/repo/main.py`): 절대경로 → 상대경로 정규화 후 부모 폴더명 추출. 정규화 실패 시 사용자 질의.
- **부모 폴더명이 비ASCII / 특수문자**: 도메인명 sanitize 룰 (영숫자·하이픈 외 제거 + 소문자화). 정규화 결과 공집합이면 사용자 질의.
- **MANIFEST 본문 prose 에 `## 도메인 분류` 정확 매칭 줄이 코드블록 (` ``` ```) 안에 있음**: 펜스 추적해 코드블록 안 줄 무시. 단 v1.1 milestone (코드블록 펜스 추적 보강) 까지는 false positive 가능 — features/04 의 전달사항 참조.
- **Phase 1 진입파일 폴더 추론과 사용자 명시 도메인 (`/pilot:learn --domain X`) 충돌**: `--domain` 옵션 우선. 본 v0.3.0 에는 옵션 자체 v2 외 (features/01 의 OQ #4 이월) — 충돌 시나리오 자체가 v0.3.0 범위 밖.

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md`
  - Phase 1 도메인 도출 표 (line 추정 50~70 범위) 에 행 1 개 추가 — 진입파일 일반 진입점 + 폴더명 fallback.
  - Phase 5 (line 추정 200~260 범위) 의 MANIFEST 섹션 detect 본문에 H2 정확 매칭 강조 1 줄 추가 + `^##\s+도메인\s*분류\s*$` 정규식 인용.
- **단위 테스트 (선택, 본 v0.3.0 에는 미포함)**: `pilot/tests/tools/test_orchestrate_load.py` 의 `parse_manifest_domain_files` 테스트가 본 변경과 정합. 추가 테스트 없이 기존 회귀로 충분.
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/` 의 `python-sample` 도메인 도출 결과는 본 변경 후에도 동일 (입력 = `_input/python-sample/main.py` → 부모 폴더명 fallback 적용 시 `python-sample` 동일).
- **사용자 영향**: 0 (LLM 이 사실상 알아서 fallback 하던 거동의 명문화). v0.2.x 사용자가 v0.3.0 으로 업그레이드 시 도메인 도출 결과 동일.
