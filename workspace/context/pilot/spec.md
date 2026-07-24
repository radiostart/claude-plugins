# pilot — Spec skills

기획서·feature 명세·도메인 context 의 변환·생성 파이프라인. 4 개 스킬: `confl` `analyze` `create-feature` `learn`.

데이터 흐름:

```
Confluence  ──/pilot:confl──▶  docs/  ──/pilot:analyze──▶  features/  ──@pilot-planner──▶ 구현
사용자 프롬프트 ──/pilot:create-feature──▶  features/
소스 코드  ──/pilot:learn──▶  workspace/context/{domain}/
```

---

## `/pilot:confl`

Confluence 기획서 fetch / 검색 (`pilot/skills/confl/SKILL.md:9`).

- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/confl/SKILL.md:18-21`).
- **모드 판별** (`pilot/skills/confl/SKILL.md:28-37`):

  | 패턴 | 모드 |
  | --- | --- |
  | `http://`·`https://` 또는 순수 숫자 | **fetch** — 페이지를 `docs/` 에 저장 |
  | `all` | **all** — 저장된 docs 전체 출력 |
  | `>` 포함 | **search+action** — `검색어 > 작업지시` |
  | `--local` | **search:local** — Rovo MCP 우회, 로컬 grep 강제 |
  | 그 외 텍스트 | **search** — Rovo MCP 우선, 로컬 폴백 |

- **원문 보존 원칙** (`pilot/skills/confl/SKILL.md:39-40`):
  - **fetch 만이 docs/ 를 작성**. search 결과는 캐싱 안 함.
  - 정책 이행 점검 (기획서 vs 구현 비교) 은 `--local` 또는 `all` 사용 — Rovo 응답은 요약·랭킹 개입으로 인용 부적합.
- **Search 모드** (`pilot/skills/confl/SKILL.md:62-85`):
  - `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql` 호출 (cloudId 는 `getAccessibleAtlassianResources` 로 사전 확인).
  - 결과에 `[source: rovo-mcp]` 태그 + `confl_search_source_rovo` 안내.
  - 폴백: `python3 {PLUGIN}/tools/confluence.py search "{검색어}"` + `[source: local]` 태그.
- **Fetch 모드**: `python3 {PLUGIN}/tools/confluence.py fetch "$ARGUMENTS"` (`pilot/skills/confl/SKILL.md:50-58`).
- **All 모드**: `python3 {PLUGIN}/tools/confluence.py all` (`pilot/skills/confl/SKILL.md:130-142`).

---

## `/pilot:analyze`

`docs/` 기획서를 `features/` 기능 명세로 분할 (`pilot/skills/analyze/SKILL.md:13-14`).

- **사전 확인**: P-1, P0, P1 — `docs/` 폴더 + `.md` 파일 존재 검증. 없으면 `messages.md:docs_missing` 후 종료 (`pilot/skills/analyze/SKILL.md:20-30`).
- **인자** (`pilot/skills/analyze/SKILL.md:34-43`):

  | 플래그/텍스트 | 모드 |
  | --- | --- |
  | `--regen-agents` 단독 | 재생성 전용 — `prompts/*.md` 만 |
  | 빈 문자열 | 전체 분석 |
  | 파일명/page_id | 파일 지정 |
  | 그 외 | 키워드 필터 분석 |

- **`--force` + prompt-origin 보호** (`pilot/skills/analyze/SKILL.md:67-86`):
  - `> source: prompt` tag 가진 features 검색 → 1 건 이상이면 사용자 승인 대기 (slug 충돌 시 데이터 손실 방지).
- **8 단계 프로세스**:
  1. **대상 파일 결정** — `--force` 없으면 `> source:` 로 분석 완료된 원본 스킵 (`pilot/skills/analyze/SKILL.md:59-65`).
  2. **원본 읽기** — 파일 크기 분기: 소형 (≤50KB) 전체 Read·중형 H2 단위 (limit 150)·대형 (>150KB) targeted Read (limit **80**, 표 많은 문서 보수). 25k rejection 시 `limit` **1/3 축소** (`pilot/skills/analyze/SKILL.md:88-105`).
  3. **분할** — H2 섹션 = 기능 단위. 번호 패턴 (`#N`·`N.`·`N)`) 검출 (`pilot/skills/analyze/SKILL.md:89-123`). 각 기능에서 추출: `요구사항` (조건·트리거·기대결과), `상태 전환`, `비즈니스 규칙`, `예외 케이스` + `> source:` 메타.
  4. **저장** — `workspace/projects/{PROJECT}/features/{NN}-{slug}.md`. 배치 Write (3~5 개 단위 권장) (`pilot/skills/analyze/SKILL.md:124-132`).
  5. **project.md 갱신** — 도메인 결정 → `## 목표` 체크리스트 + `## 관련 파일` 표 (Routes/Models/Services 를 `scope/{domain}.md` 에서 추출) (`pilot/skills/analyze/SKILL.md:133-176`).
  6. **prompts/ 갱신** — `references/prompts-update.md` 절차 + `.agent-state.yml.analyzed: true` (`pilot/skills/analyze/SKILL.md:177-180`).
  7. **자가 검증** — `references/self-verify.md` 4 항목 (커버리지·구조·정합성·추측 혐의).
  7.5. **조건부 인터뷰 (#17)** — 신규 생성 features 의 unchecked Open Questions (`- [ ]`) 존재 시에만 발동 (soft gate). (d)>(b)>(c)>(a) 우선순위로 최대 8 문항 일괄 질의, 답변 spec 반영 + `- [x]` 체크. 해소 ≥1 건 시 `--regen-agents` 권장 INFO. `--regen-agents` 모드는 미발동. 소비 규칙 SSOT: `pilot/skills/context/shared/interview.md` (`pilot/skills/analyze/SKILL.md:179-189`).
  8. **결과 출력** — (7.5 발동 시) `인터뷰: 해소 N건 / 이월 M건` 줄 포함 (`pilot/skills/analyze/SKILL.md:191-193`).
- **추측 금지** — 원본에 없는 내용 추가 금지. 한 번 추측 들어가면 후속 prompts/·planner/·generator 가 모두 잘못된 사실 기반 동작 (`pilot/skills/analyze/SKILL.md:153`).

---

## `/pilot:create-feature`

활성 프로젝트에 단일 feature 명세 추가 (`pilot/skills/create-feature/SKILL.md:14`).

- **사전 확인**: P1 — `{PROJECT}` 필수. 빈 인자 → 안내 후 종료 (`pilot/skills/create-feature/SKILL.md:27-33`).
- **NN 결정** (`pilot/skills/create-feature/SKILL.md:39-56`):
  - `features/*.md` 의 `.plan.md` 제외 번호 최댓값 + 1. 폴더 없으면 `01`.
  - slug 모호하면 후보 2~3 개 제시.
- **템플릿** (`pilot/skills/create-feature/SKILL.md:62-92`):
  ```markdown
  # #{NN} {기능명}

  > source: prompt
  > created: {ISO 8601 UTC}
  > user_prompt: "{원문 지시}"

  ## 요구사항
  - **조건**: _(상세 필요 — @pilot-planner 가 영향 분석 시 보강)_
  - **트리거**: _(상세 필요)_
  - **기대결과**: _({프롬프트에서 추출})_

  ## 상태 전환 / 비즈니스 규칙 / 예외 케이스
  ```
  - 추측성 내용 **금지** — placeholder 로 둠.
- **3-ter 조건부 인터뷰 (#17)** — 3-bis 직후, spec 의 unchecked Open Questions 존재 시에만 발동. 산출물 대조 (spec 심볼 ↔ `scope/{domain}.md` lookup only, 코드 탐색 금지) 후 (d)>(b)>(c)>(a) 우선순위 최대 4 문항 질의, 답변 spec 반영. 해소 (b) 행은 5-2 재detect 에서 재개봉 안 함 (판정 키 = 외부 도메인명). 소비 규칙 SSOT: `pilot/skills/context/shared/interview.md` (`pilot/skills/create-feature/SKILL.md:108-122`).
- **자동 갱신** — `analyze` 의 5 ~ 6 단계 그대로 호출 (소스가 docs/ 가 아니라 **현재 features/ 전체**).
- **제약** (`pilot/skills/create-feature/SKILL.md:146-150`):
  - 에이전트 자동 호출 안 함. 시작점은 `@pilot-planner`.
  - `> source: prompt` tag → `analyze --force` 가 덮어쓰기 시 사용자 승인 필요.

---

## `/pilot:learn`

소스 코드 → `workspace/context/` 도메인 문서 부트스트랩 (`pilot/skills/learn/SKILL.md:15`).

- **사전 확인**: P-1, P0 — **P1 미적용** (workspace 만 있으면 활성 프로젝트 없어도 실행 가능) (`pilot/skills/learn/SKILL.md:38-47`). `workspace/context/config.md` Read 하여 Ignore·language·source_root 확보.
- **인자** (`pilot/skills/learn/SKILL.md:29-34`):
  - `{entry-point}` 필수 — 파일 또는 폴더
  - `--domain NAME` (선택, 자동 도출 override)
  - `--depth N` (기본 `2`, 의존성 추적 깊이)
  - `--force` (선택, 묻지 않고 덮어쓰기)
- **5 Phase 절차** + 사용자 확인 게이트 최대 2 회 (Phase 2 끝, Phase 4 중간) — 발견 파일 ≤ 5 개면 Phase 2 자동 skip (`pilot/skills/learn/SKILL.md:65`).
- **Abort cleanup 계약** — 어느 Phase 든 사용자 중단 시 어떤 Write 도 수행 안 함 (P5 batch Write 후엔 abort 불가) (`pilot/skills/learn/SKILL.md:69`).

  | Phase | 동작 | 출력 |
  | --- | --- | --- |
  | 1. 도메인 도출 | 진입 경로에서 도메인 추출. `--domain` override. 모호하면 후보 제시 (`pilot/skills/learn/SKILL.md:71-79`) | `{domain}` |
  | 2. Inventory | Glob/Grep 만, **Read 금지**. 의존성 추적 → 역할별 분류 (routes·controllers·services·models·helpers·other) → 필터링 (Ignore·tests·vendor) → 통계 + 사용자 확인 1 (`pilot/skills/learn/SKILL.md:81-136`) | 발견 파일 N 개 |
  | 3. Read & 추출 | 크기별 전략: ≤300 줄 전체·301~1000 targeted·>1000 skip. 추출: 파일 목적·public interface·의존성·state enum·business rule (`pilot/skills/learn/SKILL.md:138-188`) | 카테고리별 누적 |
  | 4. 구조 결정 + 생성 | `references/heuristics.md` 휴리스틱 → 미리보기 → 사용자 확인 2 → batch Write (3~5 개 단위) (`pilot/skills/learn/SKILL.md:190-244`) | `workspace/context/{domain}/*.md` |
  | 5. MANIFEST 갱신 + doctor | 기존 도메인 분류 detect → 표/리스트/산문 형식 맞춰 append. `orchestrate-load.py` 와 호환 (표 형식만 자동 파싱) (`pilot/skills/learn/SKILL.md:246-301`) | MANIFEST 1 행 추가 + doctor PASS |

- **핵심 가드** (`pilot/skills/learn/SKILL.md:85-88`):
  - 방문 set — 순환 의존 무한 루프 방지
  - 파일 수 cap — 발견 파일 > **50** 면 좁히기 권유
- **추출 시 추측 금지** (`pilot/skills/learn/SKILL.md:181-186`):
  - 코드에 문자 그대로 있는 것만 인용. "아마 이런 의도" 같은 해석 금지.
  - 모든 항목에 `file:line` 인용 — `/pilot:doctor` 가 mtime drift 로 stale 감지.
- **제약** (`pilot/skills/learn/SKILL.md:305-312`):
  - v1 — 단일 언어·단일 진입점 가정. 멀티 언어 모노레포는 분할 호출.
  - diff 모드 없음. 갱신은 `--force` 또는 sub-domain 추가.
  - 활성 프로젝트와 무관 — STATE.md 변경 안 함.
  - 출력 구조 자유 — `scope/{domain}.md` 같은 고정 컨벤션 강제 안 함. **MANIFEST.md 가 discovery contract**.
