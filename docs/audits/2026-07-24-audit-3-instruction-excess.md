# 감사 축 3 — 지시 과잉 (원본 결과)

전제: 각 SKILL.md 는 `preamble.md`·`messages.md`·`references/*.md`·`modes/*.md` 등 공유 문서에 이미 상세를 위임하는 구조다. 따라서 "불변 조건"에는 **참조 링크 자체**(SSOT 포인터)가 다수 포함된다 — 링크가 사라지면 위임 구조가 끊긴다.

## 스킬별 분석

### analyze (현재 202줄 → 목표 ~95줄)

- **축약 후보**:
  - L45-53 필터 분석 모드 설명 — "키워드 매칭으로 관련 섹션만 추출"은 표 한 줄이면 충분.
  - L69-88 "원본 파일 읽기" — Read 전략 표(소/중/대형, limit 150/80)와 절차 4단계는 마이크로 관리. "대형 표 중심 문서는 목차 선파악 후 targeted Read, rejection 시 limit 1/3 축소" 원칙 2줄로 압축 가능.
  - L139-169 (5-1~5-2) — 이미 scope-sync.md 로 위임돼 있는데 본문에 요약이 중복 서술됨. 핵심 규칙만 남기고 압축.
  - L179-193 (7.5·8) — interview.md 위임 후 절차 재서술 중복.
- **불변 조건 체크리스트**:
  - [ ] preamble P-1/P0/P1 수행 + `workspace_missing`/`no_active_project`/`docs_missing`/`analyze_all_done` 메시지 게이트
  - [ ] 인자 판별 계약: `--regen-agents`(prompts만 재작성) / 빈 인자(전체) / 파일명·page_id / 키워드 필터 / `--force`
  - [ ] `--force` 시 `> source: prompt` Grep → 사용자 y/n 승인 게이트 (prompt-origin 데이터 손실 방지)
  - [ ] 스킵 판단 기준 = features/ 상단 `> source:` 메타데이터
  - [ ] 추측 금지 + 읽지 않은 섹션은 생성 제외 + 전체 미스캔 시 범위 보고 후 확정
  - [ ] Read rejection 시 limit **1/3** 축소 (learn 의 1/2 와 의도된 차이 — 표 중심 토큰 밀도)
  - [ ] feature 파일 계약: `features/{NN}-{slug}.md`, H2=기능 단위, 섹션 구조(요구사항 조건/트리거/기대결과 · 상태 전환 표 · 비즈니스 규칙 · 예외 케이스) — planner/generator 가 직접 Read 하는 포맷
  - [ ] 도메인 결정: `.agent-state.yml.domain` 이 SSOT, non-null 이면 재질의 금지, 기록은 반드시 사용자 확인 후
  - [ ] project.md `## 목표` 갱신 규칙: `[x]` 완료 항목 불변 / force 로 사라진 항목 제거 / NN 순
  - [ ] `## 관련 파일`: features 명시 심볼 누락 금지, 신규 대상 `(from features/NN-{slug})` 주석, 사용자 수동 행 보존
  - [ ] Open Questions 섹션 보존 + 4 카테고리 (open-questions.md SSOT)
  - [ ] 6단계 → prompts-update.md 위임 + **`.agent-state.yml.analyzed: true` 게이트**
  - [ ] 7.5 인터뷰: **신규 생성 features 만** 대상, `--regen-agents` 미발동, 우선순위 (d)>(b)>(c)>(a), 최대 8문항, `- [x] {원문} → {답변 요약}` 체크 형식 (interview.md SSOT)
  - [ ] 해소 ≥1건 시 `--regen-agents` 권장 INFO 출력
  - [ ] references 링크 5종: regen-mode.md · scope-sync.md · prompts-update.md · self-verify.md · interview.md
  - [ ] **단계 번호 앵커 (1~8, 5-1, 5-2, 6-5, 7)** — project·create-feature 가 "분석 프로세스 5~6단계", "6-5 단계" 로 인용. 번호 유지 또는 인용부 동시 수정 필수
- **frontmatter**: 적절. confl/create-feature 와의 경계 구분이 트리거 판단에 유효.

### autopilot (현재 198줄 → 목표 ~85줄)

- **축약 후보**:
  - L19-24 사용 예, L49-65 재개 확인 대화 스크립트 전문 — "AUTO_LOG 존재 시 재개/재시작/취소 3지선다 1회 확인, 응답 전 진행 금지" 원칙으로 압축.
  - L141-159 로그 형식 예시 블록 — 필드 목록으로 압축 가능 (파싱 대상 아님, 사람용 감사 로그).
  - L163-175 STOP 보고 형식 — 포함 항목 나열로 압축.
- **불변 조건 체크리스트**:
  - [ ] **스킬은 신호를 직접 해석하지 않는다** — 모든 전이는 `auto_pilot.py` 반환 `kind` 로만 분기
  - [ ] CLI 호출 계약 3종: `--phase planner --plan-valid {bool}` / `--phase critic --critic-file {path}` / `--phase evaluator --report-file {path} --retries-used {R}`
  - [ ] plan-validate.py mode 매핑: tdd:true→`tdd`, mode:characterize→`characterize`, 그 외→`standard`
  - [ ] **retry 시 `{R}` 반드시 1 증가** (미증가 시 MAX_RETRIES=1 무력화 → 무한 루프)
  - [ ] 재시도는 정확히 1회, 항상 generator 재진입
  - [ ] hard-stop 사유 enum: plan-validate 실패 · critic-blocking · signal-parse · retry-exhausted · agent-error(generator 예외/빈 출력) — STOP 시 로그 기록 후 **종료** (추가 진행 금지)
  - [ ] critic `kind=reflect` 시 planner 재호출 + `## 합의` 표 채움 후 generator 진행
  - [ ] `{AUTO_LOG}` = `features/{NN}-{slug}.auto.md`, 매 전이 즉시 append, 새 실행은 새 `## Run N` 섹션
  - [ ] 재개 확인: AUTO_LOG 존재 시 사용자 응답 전 진행 금지 (DONE 이어도 동일)
  - [ ] feature 부재 시 create-feature 안내 후 종료; `{FEAT}` glob 에서 `.plan.md`·`.plan.critic.md`·`.auto.md` 제외
  - [ ] 단일 feature 단위 · opt-in 예외 모드 (기본은 수동 명시 호출)
- **frontmatter**: 적절. hard-stop 신호 나열이 트리거·기대 설정에 유효.

### characterize (현재 56줄 → 목표 ~35줄)

- **축약 후보**: L33-50 절차 4단계 + 출력 블록 — "state 파일 Read → mode 키 설정/제거 → 결과 안내" 로 압축. 분기 표(L28-31)는 2행이라 유지 부담 없음.
- **불변 조건 체크리스트**:
  - [ ] 이 스킬은 **상태 전환 명령**일 뿐, 절차 정본은 `modes/characterize.md`
  - [ ] `.agent-state.yml` 의 `mode: characterize` ↔ null 전이 (on/off)
  - [ ] schema v1.1 미만이면 중단 + `/pilot:doctor --fix` 안내
  - [ ] `tdd: true` 동시 설정 시 **characterize 우선**
  - [ ] `{source_root}` 잠금은 scope-guard.sh 훅 + Evaluator `git diff` 이중 강제 — 리팩터는 off 후 별도 사이클
- **frontmatter**: 적절.

### code-review-init (현재 121줄 → 목표 ~65줄)

- **축약 후보**:
  - L20-28 확장자→슬러그 매핑 전체 나열 — 모델이 아는 상식. "dominant 확장자 감지 후 사용자 확인" 원칙으로 압축.
  - L51-58 언어별 프레임워크 질의 목록 — "프레임워크 특화 섹션은 사용 여부 확인 후 미사용분 제거" 한 줄로.
  - L89-104 결과 출력 블록 — 포함 항목으로 압축.
- **불변 조건 체크리스트**:
  - [ ] 대상 경로: `workspace/context/review/{lang}.md` (부재 시 폴더 생성)
  - [ ] 워크스페이스 미초기화 시 `/pilot:init` 안내 후 종료
  - [ ] 기존 파일은 사용자 확인 없이 덮어쓰기 금지 (덮어쓰기/`.bak.{timestamp}` 백업/취소 질의)
  - [ ] 3 전략: A=`examples/code-review/{lang}.md` 복사 (부재 시 비활성) / B=`review-rules-template.md` / C=AI 생성
  - [ ] **전략 C 는 미리보기 → 사용자 승인 후에만 저장** (자동 저장 금지, draft 임을 명시)
  - [ ] `workspace/` 외부 Write 금지
  - [ ] 생성 파일은 `/pilot:review`(→ pilot-code-review 에이전트) 가 자동 로드하는 계약
- **frontmatter**: 적절.

### commit (현재 22줄 → 목표 20줄)

- **축약 후보**: 없음 — 이미 원칙 중심 완성형. 재작성의 참조 모델로 쓸 만하다.
- **불변 조건 체크리스트**:
  - [ ] preamble P1
  - [ ] `shared/commit.md` 가 규칙 SSOT + 부재 시 fallback (scope 없음·한국어·50자)
  - [ ] unstaged 포함 여부 사용자 질의 + 메시지 초안 사용자 확인 (fallback 시에도 동일)
- **frontmatter**: 적절.

### confl (현재 155줄 → 목표 ~75줄)

- **축약 후보**:
  - 각 모드의 "수행할 작업" 번호 절차 (L48-58, L66-98, L106-117, L126-139, L147-155) — CLI 호출 + 출력 규칙만 남기면 절반 이하로 줄어듦. 안내 문구 전문 인용은 요지로 압축.
  - L135-139 사용 예시 3종 — 1종으로.
- **불변 조건 체크리스트**:
  - [ ] 모드 판별 계약: URL·순수 숫자→fetch / `all` / `>` 포함→search+action / `--local` / 그 외→search
  - [ ] **원문 보존 원칙: fetch 만이 docs/ 를 작성** — search 결과는 캐싱 금지
  - [ ] **정책 이행 점검(기획서 vs 구현)은 `--local` 또는 `all` 필수** — Rovo 는 요약·랭킹 개입으로 원문 인용 근거 부적합
  - [ ] `confluence.py` 서브커맨드 계약: `fetch` / `search` / `search-local` / `all`
  - [ ] fetch 는 내용을 컨텍스트에 로드하지 않음 — 파일 경로 + 섹션 제목만 출력
  - [ ] 출처 태그 필수: `[source: rovo-mcp]` / `[source: local]`
  - [ ] rovo 결과는 산출물 직접 인용 금지 (요약·참조만) + 자동 fetch 금지 (사용자 유도만)
  - [ ] MCP 미등록·실패·0건 → 로컬 폴백 + 원인 안내
  - [ ] docs/ 는 이 커맨드로만 접근 (직접 Read 금지 — 다른 스킬과의 계약)
  - [ ] `confl_no_match` 메시지 키
- **frontmatter**: 적절.

### create-feature (현재 180줄 → 목표 ~85줄)

- **축약 후보**:
  - L49-58 slug 결정 예시 블록 — 규칙 서술로 충분.
  - L143-164 결과 요약 블록 전문 — 포함 항목으로 압축.
  - L98-122 (3-bis·3-ter) — open-questions.md·interview.md 위임 후 절차 재서술 중복. 발동 조건·순서·상한만 남기기.
- **불변 조건 체크리스트**:
  - [ ] preamble P-1/P0/P1, 빈 인자 시 안내 후 종료
  - [ ] NN 결정: 기존 features 번호 최댓값+1 (`.plan.md` 제외), 폴더 없으면 01
  - [ ] 파일 메타 계약: `> source: prompt` + `> created:` + `> user_prompt:` (analyze `--force` 보호 게이트가 이 태그를 Grep)
  - [ ] 섹션 구조 = analyze 와 동일 4섹션 + **`## Open Questions` 4 카테고리 (a~d) + `- (없음)` placeholder 필수** (open-questions.md SSOT)
  - [ ] 추측성 내용 금지 — placeholder 유지, planner 가 보강
  - [ ] 3-bis: MANIFEST lookup 으로 cross-domain detect → (b)/(c) 분류
  - [ ] **3-ter 는 step 4 보다 앞** (답변 반영 후 prompts 재생성 — 순서 불변), 발동 조건 = unchecked 항목 ≥1 (soft gate), 최대 4문항, `{domain}` 은 `.agent-state.yml.domain` 만 사용 (null 이면 대조 스킵)
  - [ ] C1 재개봉 방지: 해소된 (b) 행의 중복 판정 SSOT = scope-sync.md 5-2 규칙 2
  - [ ] step 4~5: **analyze 5~6단계 + 6-5 가 SSOT** — 절차 복제 금지, 위임 인용 유지
  - [ ] doctor 실행 + ERROR/WARN 원문 출력
  - [ ] **에이전트 자동 호출 금지** — 시작점은 사용자의 `@pilot-planner` 명시 호출
- **frontmatter**: 적절.

### doctor (현재 63줄 → 목표 ~50줄)

- **축약 후보**: L50-56 "언제 실행하나" 목록 — description 과 중복, 삭제 가능. 이미 "로직 SSOT = tools/doctor.py" 구조라 축약 여지 적음.
- **불변 조건 체크리스트**:
  - [ ] 검사 로직 SSOT = `tools/doctor.py` (진단은 `tools/doctor/diagnose.py`) — 스킬은 실행 + 원문 출력만
  - [ ] 호출 계약: `doctor.py workspace` (+`--project {P}`), exit 0=ERROR 없음 / 1=ERROR 존재
  - [ ] 플래그 계약: `--fix` (마이그레이션 상세는 references/migration.md) / `--diagnose` (실패 패턴 enum + 호출 시점) / `--schema` (CI·workspace 무관)
  - [ ] 비파괴 원칙 (`--fix` 제외 읽기 전용), fix 제안은 출력만 하고 자동 적용 금지
  - [ ] diagnostician 페르소나 (증상→근거→처방)
- **frontmatter**: 적절.

### focus (현재 102줄 → 목표 ~55줄)

- **축약 후보**: L55-87 기록/제거 모드 마이크로 절차 + 출력 블록 — 경로·형식·아카이브 규칙만 남기면 절반 압축.
- **불변 조건 체크리스트**:
  - [ ] 경로 계약: `.focus.md` (현재) / `.focus.history/{timestamp}.md` (아카이브 — 삭제가 아닌 이동)
  - [ ] 파일 형식: `# Focus — {ISO timestamp}` + 원문 본문 (4 에이전트가 Read 하는 계약)
  - [ ] **래퍼는 Read 만** — 수정·삭제·아카이브 안 함 → 한 focus 가 여러 phase 에 걸쳐 유효, 해제는 사용자의 `--clear` 만
  - [ ] 활성 focus 최대 1개 (신규 기록 시 기존을 history 로 이동)
  - [ ] note-taker 페르소나: 사용자 발화 원문 보존, 해석·확장 금지
  - [ ] gitignore 대상
- **frontmatter**: 적절.

### init (현재 125줄 → 목표 ~75줄)

- **축약 후보**:
  - L38-43 절차 3단계 (템플릿 Read→Write) — 자명.
  - L82-116 결과 출력 블록 전문 — 포함 항목으로 압축.
  - wizard 3단계 (L63-78) 의 언어별 default 패턴 나열 — init_detect.py 쪽으로 밀거나 요약.
- **불변 조건 체크리스트**:
  - [ ] 템플릿→대상 3종 매핑 (STATE.md / MANIFEST.md / config.md) + **idempotent** (존재 시 skip, created/exists 마킹)
  - [ ] 템플릿 경로: `skills/context/lifecycle/setup/templates/`
  - [ ] **카테고리 폴더 (rules/·scope/·enums/) 미생성 원칙** — 사용자가 MANIFEST 채우며 결정
  - [ ] wizard 는 config.md `created` 일 때만 + `--no-wizard` 로 skip
  - [ ] **표 헤더 고정 스키마 (doctor strict 검증 — 한 글자 오차도 ERROR)**: `| 언어 | 의존성 추출 패턴 |` · `| 역할 | 식별 패턴 |` · `| scope 헤더 | project.md 대상 H3 | 표 헤더 |` (scope 헤더는 `## ` 시작) · `| 패턴 | 사유 |` — 문자열 원문 그대로 보존 필수
  - [ ] `init_detect.py` 호출 계약: `detect_languages(cwd_path)` / `detect_scope_candidates(cwd_path)` (pathlib.Path)
  - [ ] dedupe 병합 (사용자 수동 행 보존), 감지 0건 시 default (scope 는 scope-sync.md canonical 3행) + INFO
  - [ ] A2 fallback: 단계 실패해도 abort 금지, 나머지 계속
  - [ ] MANIFEST `## 외부 도메인 reference` 는 placeholder 만 — 실제 작성은 learn
- **frontmatter**: 적절.

### issue (현재 33줄 → 목표 30줄)

- **축약 후보**: 거의 없음 — 이미 완성형.
- **불변 조건 체크리스트**:
  - [ ] 경량 모드 선언: 4-에이전트 사이클 없음, 컨텍스트 로드 + 기록만 (사이클 필요 시 project)
  - [ ] GUIDE.md 는 **신규 이슈 생성 시만** 로드, 기존 이슈는 issue.md 만
  - [ ] P2: STATE.md 본문을 `| issue | {이슈명} | 진행중 |` **1행 교체** (이력은 git log), 이슈명 없으면 `-`
  - [ ] preamble P-1/P0/P2/P3 참조
- **frontmatter**: 적절.

### learn (현재 207줄 → 목표 ~100줄)

- **축약 후보**:
  - L87-109 Phase 3 read 전략 표 + Targeted Read Grep 패턴 표 — 최신 모델이 스스로 구성 가능한 대표적 마이크로 절차. "구조적 추출 우선, god file(>1000줄) skip+알림, 누적 ~50k 초과 시 재확인" 원칙만 남기기.
  - L50-58 Phase 1 도메인 도출 휴리스틱 상세 — 원칙 + 모호 시 사용자 질의로 압축 (단, 폴더-suffix 규칙은 보존 — 아래).
  - L146-160 MANIFEST 형식 변형 표 — "기존 구조 detect 후 그 형식으로 append, 부재 시 표준 3컬럼" 으로 압축.
- **불변 조건 체크리스트**:
  - [ ] **추측 금지** — 코드 문자 그대로만, 모든 항목 `file:line` 인용 (doctor 의 mtime drift 감지 입력)
  - [ ] Phase 2 는 **Glob/Grep 만 (Read 금지)** + 방문 set (순환 의존 무한 루프 방지) + 50개 cap 시 좁히기 권유
  - [ ] 사용자 확인 게이트 2회 (Phase 2 범위 / Phase 4 구조) + **발견 ≤10개면 확인 1 자동 skip**
  - [ ] **Abort cleanup 계약**: 어느 Phase 든 중단 시 Write 0건 (batch Write 진입 후엔 abort 불가)
  - [ ] P1 미적용 (활성 프로젝트 불요), STATE.md 불변경
  - [ ] 폴더-suffix 미strip (`coupon_service/` → `coupon_service` 유지 — Ruby namespace 일치), sanitize 에 언더스코어 허용
  - [ ] config lookup: `## learn 언어 패턴` 두 표 우선, 잘못된 행은 WARN + fallback (abort 금지)
  - [ ] 필터: config Ignore + 테스트 + 벤더·생성물 제외
  - [ ] Read rejection 시 limit **1/2** 축소 (analyze 1/3 과 의도된 차이)
  - [ ] 파일 크기 정책: 진입/index ≤100줄, 본문 ≤200줄
  - [ ] **MANIFEST `## 도메인 분류` H2 정확 매칭** (`^##\s+도메인\s*분류\s*$`) — `orchestrate-load.py:parse_manifest_domain_files` 자동 파싱 호환 필수
  - [ ] 외부 도메인 reference 갱신 (#09·#10) — cross-domain.md SSOT
  - [ ] Boundary 모드 계약: `{A}` MANIFEST 등록 전제 / 접점 0건 시 파일 미생성 / `boundaries/{A}--{B}.md` ≤150줄 / MANIFEST 행 **제거 금지** (` · 경계:` 표기만) / orchestrate-load 가 정·역방향 자동 로드 (별도 등록 불요)
  - [ ] `scope/`·`rules/` 는 사용자 커스텀 layer — 이 스킬이 직접 생성 금지
  - [ ] MANIFEST 가 discovery contract (출력 구조는 자유)
  - [ ] references 링크: heuristics.md · cross-domain.md / Phase 5 doctor 실행
- **frontmatter**: 트리거 판단엔 적절하나 17 스킬 중 가장 길다 (boundary 모드 문법까지 포함). description 은 축약 대상이 아니므로 유지 판단은 별도.

### pr (현재 170줄 → 목표 ~80줄)

- **축약 후보**:
  - L123-153 예시 흐름 2종 (~30줄) — 전체 삭제 가능.
  - L57-65 base 결정 ASCII 트리 — 산문 3줄로 압축 (규칙 자체는 보존).
  - L30-47 fallback 최소 본문 규칙 — 섹션 2개 구조만 남기고 서술 압축.
- **불변 조건 체크리스트**:
  - [ ] PR 컨벤션 lookup 순서: `workspace/context/pr.md` → 플러그인 `shared/pr.md` → 최소 본문 규칙 (Summary + Test plan)
  - [ ] `pr_default_base` 결정: config → 하드 fallback `develop`
  - [ ] `pr_base_branch` state 계약: **명시 입력만 저장, Enter(default)는 미저장**, 저장돼 있으면 유지/변경 질의
  - [ ] `git ls-remote --exit-code origin <base>` 검증 필수, 실패 시 재질의 (최대 3회 후 종료)
  - [ ] uncommitted 변경 차단 → `/pilot:commit` 선행 안내
  - [ ] `regression_command` **soft gate** (실패해도 사용자 확인 후 진행 가능, 미설정 시 권장 INFO)
  - [ ] **사용자 승인 게이트**: 제목·본문·base·head 확인 후 생성
  - [ ] `gh pr create` (HEREDOC), gh 미인증 시 안내 후 종료
  - [ ] Slack `--event pr` (SLACK_EVENTS default 포함, `--no-slack` skip, 실패해도 비차단)
  - [ ] `--no-verify`/hook 우회 금지, base==head 시 종료, 현재 head 만 대상
  - [ ] 옵션 계약: `--draft` / `--base` (state 기록) / `--no-slack` / `--title`
- **frontmatter**: 적절.

### project (현재 170줄 → 목표 ~95줄)

- **축약 후보**:
  - L44-53 인자 파싱 표 — 산문 2줄.
  - L155-170 결과 출력 분기 상세 — 안내 항목 목록으로 압축.
  - L63-85 example 복사 관련 서술 — 반복 경고("재작성 금지"류)가 3회 이상 중복. 1회 강한 선언으로 통합 가능.
- **불변 조건 체크리스트**:
  - [ ] 예약어 거부: `example`·`workspace`·`STATE`·`context`
  - [ ] **example 4종 그대로 복사 + H1 의 `{프로젝트명}` 토큰만 치환 — 본문 재작성·요약·환각·도메인 예시 삽입 절대 금지** (placeholder·표식 유지, GUIDE.md 본문 복사 금지)
  - [ ] A2 fallback: H1 토큰 부재 시 skip + INFO, abort 금지
  - [ ] `.agent-state.yml` 초기 스키마: `schema: v1.2` / `analyzed: false` / `tdd: false` / `domain: null` / `plugin_version`(optional — 획득 실패 시 라인 생략). **domain 자동 추론·기입 금지** (analyze 에서 사용자 확인)
  - [ ] `## 관련 파일` H3 SSOT 분리: H3 헤더=본 스킬 1회 생성·재실행 시 보존 / 표 본문=analyze·create-feature 갱신 / 사용자 H3 보존·삭제 시 미복구
  - [ ] 기존 프로젝트: schema v1 이하면 `/pilot:doctor --fix` 안내, drift 체크 3종 (docs_last_fetched_at / features 증가 / scope mtime → 재분석·regen 권장, 자동 실행 금지)
  - [ ] P2: STATE.md `| project | {P} | 진행중 |` 1행 교체 / P3 도메인 컨텍스트 로드
  - [ ] `--tdd` → tdd-activation.md 위임
  - [ ] **confl nested 호출 금지** — confluence.py 를 Bash 직접 실행 (컨텍스트 이중 적재·경로 어긋남 방지), fetch 실패 시 7·8 skip·템플릿 유지
  - [ ] 7·8단계는 analyze SSOT 위임 ("분석 프로세스 1~5 / 6~7")
  - [ ] doctor 실행 + 원문 출력
  - [ ] 중간 단계 안내 금지 — 결과 출력에서 1회만 (실측 기반 규칙)
- **frontmatter**: 적절.

### review (현재 41줄 → 목표 40줄)

- **축약 후보**: 거의 없음 — 위임 구조 완성형.
- **불변 조건 체크리스트**:
  - [ ] target 결정 3분기 (없음=변경분 전체 / 경로 / 커밋 범위) → `@pilot-code-review` 위임
  - [ ] 코드 수정하지 않음 — 라우팅 제시 후 사용자 선택
  - [ ] 언어 규칙 위치 계약: `workspace/context/review/{lang}.md` (있으면 +baseline, 없으면 baseline만)
  - [ ] 역할 경계 4자 구분 (이 스킬 / 내장 code-review / evaluator / security-review)
- **frontmatter**: 적절. "evaluator 와 별개 축" 명시가 오트리거 방지에 유효.

### slack (현재 134줄 → 목표 ~75줄)

- **축약 후보**: 활성화 대화식 입력 상세 (L60-85), status 표 상세 (L103-124) — 필드·판단 명령만 남기고 압축.
- **불변 조건 체크리스트**:
  - [ ] `.slack.env` = SSOT, 퍼미션 **0600**
  - [ ] **공통 선행: 모든 서브커맨드에서 doctor 로 gitignore 보호 점검** — `[CRITICAL]` 시 즉시 중단 (git rm --cached + webhook 재발급 선행), 자동 주입 시 커밋 안내
  - [ ] 활성화 후 `git check-ignore` 실패 시 **파일 즉시 삭제** + 경고 (secret 커밋 방지)
  - [ ] `SLACK_WEBHOOK_URL` 값 출력 금지 (설정됨/비어있음만)
  - [ ] `disable` 은 안내만 — **rm 직접 실행 금지** (destructive 는 사용자 몫)
  - [ ] env 필드 계약: SLACK_WEBHOOK_URL / SLACK_CHANNEL / SLACK_EVENTS (default `complete,approval`)
  - [ ] `slack-notify.py --event approval` 테스트 호출 계약, stderr 기준 성공 판정
  - [ ] messages.md 키: `slack.already_active`·`activated`·`test_ok`·`test_fail`·`tracked_critical`·`disable_hint`
  - [ ] 기존 `.slack.env` 존재 시 재활성화 안 함 (already_active 안내)
- **frontmatter**: 적절.

### tdd (현재 92줄 → 목표 ~60줄)

- **축약 후보**: 4 서브커맨드의 완료 출력 블록 (각 5~8줄) — 포함 항목으로 압축. 절차는 이미 tdd-activation.md 위임.
- **불변 조건 체크리스트**:
  - [ ] **state.yml `tdd:` 가 진실 (Q4)** — `--fix` 는 state 기준으로 on/off 절차 재실행
  - [ ] on/off idempotent (이미 해당 상태면 INFO 후 종료)
  - [ ] 절차 SSOT = tdd-activation.md (on: §1-1b 백업 마커 + §1~6 / off: off-1~7, 마커 부재 시 template fallback INFO)
  - [ ] 3-way 검증 대상: state.yml / project.md TDD 분기 / prompts 3파일 TDD 섹션
  - [ ] **Detect literal 문자열 4종 원문 보존**: `### 1. Planner — Red 계약 작성` · planner `## TDD — Red 계약` · generator `> **TDD 모드**: Red 작성` · evaluator `## TDD 테스트 실행` (기계적 존재 확인의 키)
  - [ ] characterize 동시 설정 시 characterize 우선 (characterize/SKILL.md 참조)
  - [ ] 신규 프로젝트는 `/pilot:project --tdd` 경로
- **frontmatter**: 적절.

## 에이전트별 분석

### pilot-code-review (현재 88줄 → 목표 ~70줄)

- **축약 후보**: step 1 의 diff 수집 명령 4종 나열 (L18-29) — "uncommitted 우선, 없으면 브랜치 범위, target 지정 시 그 범위" 원칙으로 압축. REPORT 블록은 라우팅 안내문 (L82) 과 일부 중복.
- **불변 조건 체크리스트**:
  - [ ] self-contained 선언 — **orchestrate-load 미사용** (사이클 독립), 호출자 target 그대로 사용
  - [ ] 코드 수정 금지 / 변경분 밖 기존 코드 지적 금지 / 광역 탐색 금지
  - [ ] 규칙 로드: review-principles.md (baseline, 항상) + `workspace/context/review/{lang}.md` (존재 시)
  - [ ] `lint:` 줄 계약: 있으면 1회 실행 후 findings 반영, 없으면 미실행
  - [ ] severity 3종 + blocking 격상은 principles 기준 (취향 격상 금지)
  - [ ] 재진입 라우팅 enum 6종 (feature/planner/generator/trivial/new-feature/dismiss) + 모호 시 보수적 상향 + 요구사항 판정 finding 은 dismiss("evaluator 책임 영역")
  - [ ] feature 번호 추정 금지 — 판별 불가 시 일반화, 파싱 실패해도 리뷰 계속
  - [ ] `CODE REVIEW REPORT` 블록 필수 (target/languages/summary/findings/routing 6행/다음) + 0건 시 표기 규칙
  - [ ] 페르소나 SSOT = identity.yml `personas.code-review`
- **frontmatter**: 적절.

### pilot-evaluator (현재 88줄 → 목표 ~75줄)

- **축약 후보**: 극히 제한적 — 본문 대부분이 게이트·파일 계약. step 2 모드 분기의 괄호 부연 정도.
- **불변 조건 체크리스트**:
  - [ ] wrapper 선언 + **[불변] orchestrate-load 를 호출자 프롬프트와 무관하게 최우선 실행**, error 시 원문 출력 종료, instructions 가 정본
  - [ ] domain null 시 사용자 확인 후 수동 Read / 상태 카테고리는 부분 Read (전체 로드 금지)
  - [ ] 모드별 검증 SSOT: characterize.md § Evaluator / rgr.md § Evaluator / 표준 = test_command 있으면 관련 테스트 실행·미설정 시 test_run skip
  - [ ] **prompts/evaluator.md 전 체크리스트를 Edit 로 [x]/[ ] 갱신 필수** (텍스트 보고만 금지 — guardrails SSOT)
  - [ ] **project.md 목표 [x] 는 evaluator 단독 권한** (전 항목 통과 시)
  - [ ] 전달사항 형식: `- [ ] {내용} (from #{번호})` → `## 에이전트 간 전달사항` (planner 가 소비하는 계약)
  - [ ] **`VERIFICATION REPORT` 블록 원문 보존** — `status: READY|NOT_READY` 를 auto_pilot.py 가 기계 파싱. gates 6종 (requirements/tdd_evidence/capture_lockdown/test_run/scope/drift) + skip 조건 + NOT_READY 시 issues_to_fix ≥1 / READY 시 `- none`
  - [ ] coverage 는 참고 지표 (gate 아님), REPORT↔체크박스 모순 시 guardrails 룰로 정정
  - [ ] Slack complete 는 **READY 시만** 1회 (notifier 항상 exit 0, no-op 이어도 호출)
  - [ ] 탐색 제약 scope-exploration.md / drift-protocol § A + 누적 임계
  - [ ] model 미지정 = opus 의도 (frontmatter 주석)
- **frontmatter**: 적절.

### pilot-generator (현재 56줄 → 목표 ~50줄)

- **축약 후보**: 거의 없음 — 이미 압축 완료형.
- **불변 조건 체크리스트**:
  - [ ] wrapper 선언 + [불변] orchestrate-load 최우선 + error 종료 + domain null 질의
  - [ ] **plan Read 직전 plan-validate.py 재검증 (읽기 게이트)** — invalid 면 구현 시작 금지, planner 보완 안내 후 종료
  - [ ] 모드별 SSOT: characterize (`{source_root}` 수정 금지 — 훅+evaluator 이중 강제, `[Captured]` 증거) / rgr (`[Red]`/`[Green]` 증거를 .plan.md 에 Edit) / 표준
  - [ ] 체크리스트 Edit 갱신 필수 + **project.md `## 목표` 체크박스 수정 금지 (evaluator 단독 권한)**
  - [ ] **evaluator 자동 실행 금지** — 호출 안내 후 종료
  - [ ] `model: sonnet` + 오버라이드 재평가 주석 보존
  - [ ] 탐색 제약 · drift-protocol 참조
- **frontmatter**: 적절.

### pilot-planner-critic (현재 126줄 → 목표 ~85줄)

- **축약 후보**: 5 카테고리 표 (L52-57) 는 유지 가치 있으나 질문 열 압축 가능. 출력 형식 (L73-96) 의 예시 헤더 부분 축약. "다른 에이전트와의 관계" 는 2줄로.
- **불변 조건 체크리스트**:
  - [ ] wrapper + [불변] orchestrate-load 최우선
  - [ ] 책임 경계: **plan.md 수정 금지 / 코드 수정 금지 / 테스트 작성 금지** — 산출물은 `.plan.critic.md` 1개만
  - [ ] 대상 확정: 후보 0개→planner 안내 종료 / **2개 이상+지시 없음→목록 제시 후 종료 (멋대로 선택 금지)** / 1개→명시 후 진행
  - [ ] 챌린지 필드 계약: severity(blocking/suggestion/nit) · category(premise/scope/edge-case/alternative/risk) · plan 인용 · 챌린지 · 제안 — **autopilot 의 auto_pilot.py 가 이 파일을 파싱** (blocking 유무·형식 이상=signal-parse stop)
  - [ ] 취향 격상 금지 / 무관 일반론 금지 / **0개면 억지로 만들지 않고 "plan 통과" 보고** (0개 시 합의 표 생략)
  - [ ] `## 합의` 표는 비워서 생성 — planner 재호출이 채움 (인수인계 계약)
  - [ ] 기존 파일 덮어쓰기 (누적은 합의 표, 본문은 최신만)
  - [ ] 보고 3항목 + blocking≥1→planner 재호출 권장 / 0→generator 진행 가능 분기
  - [ ] critic=사전 / evaluator=사후 책임 분리, evaluator 보증 단정 금지
  - [ ] 호출 선택적 · autopilot 에선 항상 실행
- **frontmatter**: 적절.

### pilot-planner (현재 134줄 → 목표 ~90줄)

- **축약 후보**: "플래닝 프로세스 (공통 가이드)" (L84-128) 중 계획 출력 형식 마크다운 블록 — 계약 축은 plan-validate.py·plan-schema.md 가 기계 검증하므로 "필수 섹션 + 검증기" 언급으로 압축 가능. step 8 의 부연 (L66-74) 중복 압축.
- **불변 조건 체크리스트**:
  - [ ] wrapper + [불변] orchestrate-load 최우선 + domain null 시 사용자 질의
  - [ ] **전달사항 소비 필수 선행** — 관련 항목은 계획 반영 후 [x], **무관 항목은 자체 판단 skip/[x] 금지** (사용자 3지선다), 전부 소화 전 계획 진행 금지
  - [ ] 모드별 계약 축: characterize Contract 3축 ("현재 출력"은 Generator 후 채움 — **예측 기록 금지**) / Red Contract 3축 / 표준 (변경 파일·순서·주의사항)
  - [ ] **테스트 코드 작성 금지** (Generator 담당)
  - [ ] plan 저장 계약: `features/NN-{slug}.plan.md` + **저장 직후 plan-validate.py 검증, 통과 전 다음 단계 진행 금지** (모드 매핑 = plan-schema.md)
  - [ ] 체크리스트 Edit 갱신 필수 (텍스트 보고만 금지)
  - [ ] **Slack approval 알림 필수 1회** (계획 확정·확인 대기 시점, 본문 미포함, notifier no-op 이어도 호출)
  - [ ] **generator/critic 자동 호출 금지** — critic 권장 여부 1줄 + 사용자 확인 응답 1회로 진행/스킵 통합, 스킵 사유 plan.md 기록, 기본 다음 단계 = critic
  - [ ] autopilot 예외: critic 항상 실행 + blocking auto-accept 금지 (유일한 사전 hard-stop)
  - [ ] 재호출 분기: critic 챌린지 전수 검토 + **`## 합의` 표를 accepted/rejected/deferred 로 채우기 전 generator 진행 금지**
  - [ ] drift-protocol / scope-exploration / model 미지정=opus 주석
- **frontmatter**: 적절.

## 총괄

- **현재 총 줄수**: 2,563줄 (스킬 17개 2,071 + 에이전트 5개 492)
- **목표 총 줄수 추정**: 약 1,490줄 (스킬 ~1,120 + 에이전트 ~370, 약 42% 감축). commit·issue·review·doctor·characterize·generator 는 이미 목표 수준이라 감축 여력은 대형 스킬 (analyze·learn·autopilot·pr·project·confl·create-feature) 에 집중된다. "모든 스킬 100줄 이하"는 달성 가능하나, learn 은 100줄 경계선이다.
- **축약이 특히 어려운 (위험한) 스킬 3개**:
  1. **analyze** — 자체 게이트 밀도도 높지만 진짜 위험은 **cross-file 앵커**: project(7·8단계)와 create-feature(step 4·5)가 "분석 프로세스 5~6단계"·"6-5" 같은 **단계 번호로 SSOT 인용**한다. 재작성 시 번호 체계가 바뀌면 3개 스킬이 동시에 깨진다. 재작성은 인용부와 반드시 동일 커밋으로 진행해야 한다.
  2. **learn** — 기계 계약(MANIFEST H2 정규식 = orchestrate-load 파싱 호환, boundary 파일 배선)과 **실측 기반 비자명 규칙**(1/2 vs 1/3 retry, 폴더-suffix 미strip, ≤10 자동 skip)이 산문 곳곳에 박혀 있다. "모델이 알아서" 처럼 보이는 줄 상당수가 실은 과거 실패의 교정치라 선별 실수 위험이 가장 크다.
  3. **autopilot** — 무감독 자율 모드라서 축약 실수의 비용이 가장 크다. 계약 대부분이 `auto_pilot.py`·`plan-validate.py` 파싱과 결합돼 있고, 특히 retries 증가 규칙은 누락 시 곧바로 무한 루프다. hard-stop enum 은 한 항목도 빠지면 안 된다.
- 에이전트 중에서는 **pilot-evaluator** 가 동급 위험: VERIFICATION REPORT 가 autopilot 의 기계 파싱 입력이고 gates 6종·SSOT Edit 규칙 전부가 계약이라 실질 축약 여지가 ~15% 뿐이다. 100줄 목표를 에이전트에 기계적으로 적용하기보다 "계약 보존 우선"으로 접근할 것을 권장한다.
- 공통 관찰: 다수 스킬이 이미 references/·modes/·shared/ 위임 구조를 갖췄으므로, 재작성의 주 작업은 "위임 후 본문에 남은 중복 요약 제거"다. 반대로 preamble P-단계 참조, messages.md 키, CLI 호출 시그니처, Detect literal·표 헤더 같은 **문자열 원문 계약**은 한 글자도 바꾸면 안 되는 축이며, 위 체크리스트가 그 검증 기준이다.
