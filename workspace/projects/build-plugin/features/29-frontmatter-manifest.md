# #29 본문 frontmatter 매니페스트 — 열기 전에 아는 한 줄

> source: prompt
> created: 2026-09-04T02:50:24Z
> user_prompt: "feature 생성해줘 — docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md §4 F-B 등록"
> renumbered: 2026-09-04 — 원격 main 의 #24~#26 선점(pilot-update·schema-validate·issue-cycle)으로 #24~#27 → #27~#30 재번호
> plan: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-B (설계 상세·근거 SSOT. §2 P1·P7 패턴)

## 요구사항

- **조건**: #27 (context-search) 머지 — description 가중치 4점이 이 feature 로 자동 활성된다. #28 (freshness) 는 `learned_at` 을 기준 시각 1순위로 소비.
- **트리거**: (1) `/pilot:learn` 이 본문·진입 파일을 생성·재생성할 때 frontmatter 자동 기입 (2) 래퍼 진입 시 `orchestrate-load.py` 가 활성 도메인 본문의 매니페스트 생성 (3) `/pilot:doctor` 가 캡 검증, `--fix` 가 기존 파일 마이그레이션 **제안**.
- **기대결과**:
  - `/pilot:learn` 산출 본문 파일마다 frontmatter:

    ```yaml
    ---
    description: 배송 취소 서비스 3종의 호출 순서와 상태 전환 규칙   # ≤150자 1줄, "무엇을 알 수 있나"
    domain: wms
    type: services            # index | routes | models | services | rules | enums | boundary | free
    sources:                  # 이 문서가 다루는 소스 범위 (glob 허용) — #30 의 paths 로 재사용
      - app/services/wms/**
    learned_at: 2026-09-04T03:12:00Z
    ---
    ```

  - orchestrate-load 반환 JSON 에 `context_manifest` 키 신설: 활성 도메인 폴더(+ `boundaries/{domain}--*`) 의 `*.md` 를 **앞 30줄만** 읽어 `- [type] path (age): description` 1줄씩. 최대 200개(초과 시 최신순 절단 + 표기). frontmatter 없는 파일은 `(description 없음 — 첫 H1: …)`.
  - 진입 파일(`index.md`) 은 기존대로 `files_to_read` 에 유지 — 본문은 매니페스트로 대체 **안 함**, 추가만 (soft). 에이전트는 매니페스트를 보고 필요한 본문만 Read 하거나 #27 로 섹션 조회.
  - doctor: description 부재 WARN · 150자 초과 WARN · 색인 파일(MANIFEST·진입 index) 200줄 또는 25KB 초과 WARN · `sources` 경로 미존재 INFO.

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **description 작성 규칙** (Claude Code MagicDocs 문서 철학 차용): 무엇을 알 수 있는지 한 문장. 파일명 반복 금지, 헤딩 나열 금지, 코드에서 자명한 것 금지, 개행 금지.
- **마이그레이션 = 제안 후 승인 기입** (Open Q (d) 확정): `/pilot:doctor --fix` 가 description 부재 파일에 대해 첫 H1 + 첫 문단 40자 후보를 제시하고 사용자 승인 시에만 기입. 자동 기입 금지. `workspace/context/` 산출물 직접 Edit 금지 원칙(drift-protocol §A) 의 예외 경로는 이 `--fix` 승인 흐름과 `/pilot:learn` 재실행 두 가지뿐.
- `workspace/context/MANIFEST.md` 자체는 frontmatter 를 두지 않는다 (형식 자유 원칙 유지). 도메인 진입 `index.md` 에는 둔다.
- 사용자가 손으로 만든 파일은 frontmatter 없이 허용 — doctor 는 WARN 만. `scope/{domain}.md`·`rules/{domain}.md` 는 사용자 커스텀 layer 로 frontmatter 강제 대상 아님.
- frontmatter 는 생성기 관리 영역이지만 본문은 아니다 — 재생성 시 본문 병합은 `/pilot:learn` 기존 정책(`--force`·sub-domain 추가) 을 따른다.
- 매니페스트 생성은 본문을 읽지 않는다 — 30줄 스캔 + stat 만. 대용량 본문에서도 orchestrate-load 지연 증가 100ms 이내.
- `type` 미지 값 → `free` 로 취급 + INFO. `description` 에 개행 → 첫 줄만 사용 + WARN.

## 예외 케이스

- 같은 도메인 폴더에 200개 초과 본문 → sub-folder 단위로 접고 "폴더별 N개" 표기.
- frontmatter 파싱 실패(YAML 오류) → 해당 파일 `(frontmatter 파싱 실패)` 로 매니페스트에 표기 + doctor WARN. abort 안 함 (A2).
- `sources` 가 glob 이고 매칭 0건 → INFO (소스 이동 가능성 안내).
- 기존 회귀 픽스처 `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/` 는 frontmatter 부재가 정상 — 픽스처 갱신 시 frontmatter 포함본으로 재캡처.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] 기존 본문 파일의 description 마이그레이션 — 제안 후 승인 기입 vs 자동 기입 vs learn 재실행만 → 제안 후 승인 기입. `doctor --fix` 는 후보만 제시 (2026-09-04 사용자 확정)

## 검증 기준

- `/pilot:learn` 골든 출력(회귀 픽스처) 에 frontmatter 5 키 포함 확인.
- doctor 테스트: WARN 3종(부재·150자 초과·색인 캡) + INFO 2종 + 파싱 실패 케이스.
- orchestrate-load 테스트: `context_manifest` 30줄 스캔이 본문을 읽지 않음(대용량 파일 픽스처 시간 측정) · 200개 절단 · frontmatter 부재 표기.
- #27 골든 질의 `hit@3` 가 description 가중치 활성 후 저하 없음.
- 전체 unittest 통과 + doctor 클린.

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md` Phase 4 구조 결정·생성 (`:66`) — frontmatter 기입 단계 · `pilot/skills/learn/references/heuristics.md` — description 작성 규칙
- **변경**: `pilot/tools/orchestrate-load.py` — `context_manifest` 키 (30줄 스캔·200 캡) · `build_instructions` 에 소비 지시 1줄
- **변경**: `pilot/skills/context/shared/wrapper-protocol.md` §4 반환 JSON 처리 — `context_manifest` 소비 규칙 1~2줄
- **변경**: `pilot/tools/doctor/integrity.py` `check_workspace` (`:320`) — 캡 검증 3종 + `--fix` 마이그레이션 제안 흐름
- **변경**: `pilot/skills/context/lifecycle/state-schema.md` 인접 문서 아님 — 매니페스트는 로더 출력이라 state 스키마 변경 없음 (확인용 기재)
- **테스트**: `pilot/tests/tools/test_orchestrate_load.py` 확장 · doctor 테스트 신규/확장 · 회귀 픽스처 `learn/expected/` 재캡처
