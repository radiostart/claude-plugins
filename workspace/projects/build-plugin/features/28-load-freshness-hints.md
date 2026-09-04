# #28 로드 시 신선도 힌트 — 인용 기반 변경 감지 (+ 로드 정책 문서 정합)

> source: prompt
> created: 2026-09-04T02:50:24Z
> user_prompt: "feature 생성해줘 — docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md §4 F-D + F-E 등록"
> renumbered: 2026-09-04 — 원격 main 의 #24~#26 선점(pilot-update·schema-validate·issue-cycle)으로 #24~#27 → #27~#30 재번호
> plan: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-D · § F-E (설계 상세·근거 SSOT. §2 P5 패턴)

## 요구사항

- **조건**: 로드 대상 도메인 지식 파일이 `` `path/file.ext:12` `` 또는 `:12-34` 형식의 file:line 인용을 포함한다 (없으면 나이만 표기). #29 의 `learned_at` frontmatter 는 **선택** — 없어도 동작.
- **트리거**: (1) `orchestrate-load.py` 가 도메인 진입 파일·경계 문서를 `files_to_read` 에 넣을 때마다 (2) `/pilot:doctor` 실행 시 같은 로직으로 지식 파일 단위 검사.
- **기대결과**:
  - 로드되는 지식 파일마다 힌트 1줄: `[신선도] {file}: 학습 {age}일 전 · 인용 {changed}/{total} 파일이 이후 변경 · 미존재 {missing} — 인용 전 현재 코드 확인`. 나이 1일 이하이고 변경 0·미존재 0 이면 생략 (노이즈 억제).
  - doctor 가 지식 파일 단위로 `changed/total ≥ 30%` 또는 `missing ≥ 1` → WARN "재학습 권장: `/pilot:learn {진입점}`", 그 외 INFO.
  - 실사례 검증: `features/22-context-drift-relearn.md` 의 삭제 스크립트 3종(`memory-hint.py`·`init_detect.py`·`diagnose.py`) 서술이 `workspace/context/pilot/index.md`·`lifecycle.md` 로드 시 `미존재 ≥ 1` 로 즉시 노출된다.
  - **(F-E) 문서 정합**: `GUIDE.md:51-58` 와 `state-schema.md` `analyzed` 절의 "analyzed: true 면 MANIFEST 진입 파일 재로드 생략" 서술을 코드 실제 거동("진입 파일은 항상 로드, analyze 는 prompts/ 압축본 신뢰 여부만") 으로 정정. **구현 변경 없음** — 코드가 옳다 (색인·진입은 항상 로드 = 계획서 §2 P1 정합).

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **기준 시각 우선순위** (Open Q (d) 확정): frontmatter `learned_at` > 파일의 최근 git 커밋 시각(`git log -1 --format=%cI -- {file}`) > mtime. git 우선 이유 — clone·checkout 이 mtime 을 흔든다. git 부재 환경은 mtime 만 사용 + 힌트에 `(mtime 기준)` 표기.
- **인용 파싱**: `` `?([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`? `` — 경로·시작·끝 라인. 코드블록 안 인용도 포함. 같은 경로는 1회로 합친다.
- **경로 해석**: 저장소 루트 기준 → 실패 시 `config.md` `source_root` 기준 → 실패 시 지식 파일 디렉토리 기준. 셋 다 실패면 `missing`.
- **변경 판정**: 인용 파일의 기준 시각(git 커밋 시각 > mtime) 이 지식 파일 기준 시각보다 뒤면 `changed`. `line_end ≤ 파일 줄 수` 검사로 `line_out_of_range` 별도 카운트.
- **신호만 낸다** — 자동 수정·자동 재학습 트리거 금지 (drift-protocol 승인 원칙 유지). 기존 doctor 의 "context mtime > analyzed_at" 검사(파생물 재생성 축) 와 **별개 축**(지식 자체의 부패) 으로 공존.
- **상한·성능**: 파일당 인용 500개 초과 시 앞 500개만 + `(표본 500/{n})` 표기. stat 실패는 skip(카운트 제외). orchestrate-load 지연 상한 200ms — 초과 시 나이만 표기하고 "인용 검사는 `/pilot:doctor` 로" 힌트.
- **공용 모듈**: `pilot/tools/freshness.py` 를 orchestrate-load 와 doctor 가 함께 import (라이브러리 + CLI). 표준 라이브러리 + `git` subprocess 만.

## 예외 케이스

- 인용 경로가 디렉토리/glob (`app/services/wms/`) → 디렉토리 최신 변경 시각으로 판정.
- 심볼릭 링크 → 대상 기준.
- 인용이 라인 번호 없이 경로만 → 존재 여부만 검사 (변경 판정은 수행).
- 지식 파일 자체가 git 미추적(새 파일) → git 시각 없음 → mtime fallback.
- `git` 호출 실패(비 git 디렉토리·타임아웃 1s) → mtime fallback + 표기, abort 안 함 (A2).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] 신선도 기준 시각 — git 커밋 시각 우선 vs mtime 만 vs learned_at 필수 → git 커밋 시각 우선 (`learned_at` > `git log -1` > mtime) (2026-09-04 사용자 확정)

## 검증 기준

- 픽스처: 지식 파일 1 + 인용 소스 3 (변경 1 · 미변경 1 · 삭제 1) → 힌트 문구·카운트 정확성. mtime 조작은 `os.utime`, git 경로는 임시 저장소.
- doctor 출력 스냅샷 (WARN/INFO 임계 경계: 30% 정확히·missing 1).
- 실사례: 현재 `workspace/context/pilot/` 로 orchestrate-load 실행 시 `미존재 ≥ 1` 힌트 발화 (#22 미해소 상태 기준).
- F-E: `GUIDE.md`·`state-schema.md` 정정 후 `orchestrate-load.py build_load_plan` 코드 변경 0 (`git diff --stat pilot/tools/` 에 미포함).
- 전체 unittest 통과 + doctor 클린 + orchestrate-load 지연 측정 200ms 이내.

## 관련 파일 범위

- **신규**: `pilot/tools/freshness.py` · `pilot/tests/tools/test_freshness.py`
- **변경**: `pilot/tools/orchestrate-load.py` — 4) 진입 파일(`:467`)·5) 경계 문서(`:487`) 로드 직후 `[신선도]` 힌트
- **변경**: `pilot/tools/doctor/integrity.py` `check_project` (`:456`; 기존 context mtime drift `:718-770` 옆) — 인용 검사 WARN/INFO
- **변경**: `pilot/skills/context/lifecycle/drift-protocol.md` — "자동 신호" 절 추가 (신호 → 사용자 판단 → 승인 하 재학습 경로)
- **변경 (F-E)**: `pilot/skills/context/lifecycle/projects/GUIDE.md:51-58` · `pilot/skills/context/lifecycle/state-schema.md` `analyzed` 절 — 코드 거동으로 정정
- **불변**: `orchestrate-load.py build_load_plan` 의 로드 정책 코드 (F-E 는 문서만)
