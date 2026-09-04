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

Confluence 기획서 fetch / 검색 (`pilot/skills/confl/SKILL.md:11`). docs/ 파일은 이 커맨드를 통해서만 접근하고 직접 Read 하지 않는다.

- **사전 확인**: P1 (`pilot/skills/confl/SKILL.md:15-17`).
- **모드 판별** — `$ARGUMENTS` 를 순서대로 (`pilot/skills/confl/SKILL.md:21`):

  | 패턴 | 모드 |
  | --- | --- |
  | `http(s)://` 시작 또는 순수 숫자 (page_id) | **fetch** — 페이지를 `docs/` 에 저장 |
  | `all` | **all** — 저장된 docs 전체 출력 |
  | `>` 구분자 포함 | **search+action** — `검색어 > 작업지시` |
  | `--local` 포함 | **search:local** — Rovo 우회, 로컬 grep 강제 |
  | 그 외 텍스트 | **search** — Rovo MCP 우선 → 로컬 폴백 |

- **원문 보존 원칙** (`pilot/skills/confl/SKILL.md:23-24`):
  - 어떤 모드든 **fetch 만이 docs/ 를 작성**한다 — search 결과는 캐싱하지 않는다.
  - 정책 이행 점검 (기획서 vs 구현 비교) 이 목적이면 반드시 `--local` 또는 `all` — Rovo 응답은 요약·랭킹 개입으로 원문 인용 근거에 부적합.
- **Fetch 모드** (`pilot/skills/confl/SKILL.md:26-34`): `python3 {PLUGIN}/tools/confluence.py fetch "$ARGUMENTS"`. **내용은 컨텍스트에 로드하지 않는다** — 저장 경로와 섹션 제목 목록만 출력.
- **Search 모드** (`pilot/skills/confl/SKILL.md:36-47`): `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql` 등록 확인 → 미등록이면 곧장 로컬 폴백. 등록 시 CQL (`text ~ "{검색어}"`) + cloudId (`getAccessibleAtlassianResources`) + `limit: 5`. 결과에 `[source: rovo-mcp]` 태그. **자동 fetch 하지 않는다** (유도만). 폴백은 `confluence.py search` + `[source: local]`, 결과 0 건이면 `confl_no_match`.
- **Search:local 모드** (`pilot/skills/confl/SKILL.md:49-57`): `--local` 제거 후 `confluence.py search-local`. **MCP 호출을 시도하지 않는다.** 용도 — 정책 이행 점검 (원문 인용 필수)·오프라인·재현성.
- **Search+Action 모드** (`pilot/skills/confl/SKILL.md:59-63`): `>` 기준 분리 후 Search 선행 → 결과 있으면 컨텍스트로 작업지시 수행 (`rovo-mcp` 출처는 산출물 직접 인용 금지 — 요약·참조만) → 없으면 안내 후 종료.
- **All 모드** (`pilot/skills/confl/SKILL.md:65-73`): `confluence.py all` 로 저장된 docs 전체 출력.
- **도구 표면** (`pilot/tools/confluence.py:847-857`): argparse 가 아닌 수동 `sys.argv` 디스패처 — `fetch`·`search`·`search-local`·`all`. `--force` 는 argv 에서 위치 무관 제거되며 fetch 만 사용 (`pilot/tools/confluence.py:12·848-850`). 인증은 `CONFLUENCE_EMAIL`·`CONFLUENCE_TOKEN` (루트 `.env`·`workspace/.env`·셸 env, `pilot/tools/confluence.py:14-20`).

---

## `/pilot:analyze`

`docs/` 기획서를 `features/` 기능 명세로 분할 (`pilot/skills/analyze/SKILL.md:13-14`).

- **사전 확인**: P-1, P0, P1 + `workspace/projects/{PROJECT}/docs/` Glob 확인 — 없거나 `.md` 부재면 `docs_missing` 후 종료 (`pilot/skills/analyze/SKILL.md:18-20`).
- **인자 판별** — `--force`·`--regen-agents` 를 먼저 분리하고 나머지 텍스트로 모드 결정 (`pilot/skills/analyze/SKILL.md:22-31`):

  | 플래그 / 나머지 텍스트 | 모드 |
  | --- | --- |
  | `--regen-agents` (단독) | **재생성 전용** — features 기반으로 `prompts/*.md` 만 재작성 |
  | 없음 (빈 문자열) | 전체 분석 — docs/ 내 모든 원본 |
  | 파일명 또는 page_id | 파일 지정 |
  | 그 외 텍스트 | 키워드 필터 분석 |

- **분석 프로세스 8 단계** (`pilot/skills/analyze/SKILL.md:33-87`):
  1. **대상 파일 결정** (`:35-39`) — `--force` 없으면 features 상단 `> source:` 메타로 분석 완료 원본 skip. 대상 없으면 `analyze_all_done`. **`--force` prompt-origin 보호**: `> source: prompt` 를 Grep 해 1 건 이상이면 경고 + y/n 승인 게이트 (`n`·미응답 시 종료) — slug 충돌로 인한 데이터 손실 방지.
  2. **원본 파일 읽기** (`:41-43`) — 크기 분기: ≤50KB 전체 Read / 50~150KB H2 목차 + 섹션 단위 (limit 150) / >150KB 섹션 targeted Read (limit **80**). Read rejection 시 **limit 1/3 축소** (표 중심 문서 — learn 의 소스 코드 1/2 규칙과 의도된 차이). 읽지 않은 섹션은 생성 대상에서 제외.
  3. **기능 분할 및 구조화** (`:45-49`) — H2 섹션 = 기능 단위, 번호 패턴 (`#N`·`N.`·`N)`) 있으면 기능 번호로. 각 기능은 `# #{번호} {기능명}` + `> source:` + `## 요구사항`(조건/트리거/기대결과) + `## 상태 전환`(표) + `## 비즈니스 규칙` + `## 예외 케이스`. 원본 표는 서술형으로 풀되 상태 전환표는 표 유지.
  4. **파일 저장** (`:51-53`) — `workspace/projects/{PROJECT}/features/{NN}-{slug}.md` (`NN` 2 자리 zero-pad, slug kebab-case 최대 30 자). 여러 파일은 `shared/coding.md` § 독립 파일 배치 작업 절차로 병렬 Write.
  5. **project.md 자동 갱신** (`:55-69`):
     - **도메인 결정 (5-1·5-2 공통 전제)**: `.agent-state.yml.domain` non-null 이면 그대로, null 이면 (a) project.md 제한사항 파싱 → (b) MANIFEST 분류 + 키워드 매칭 후보 → (c) 사용자 질의 후 Edit. **자동 판정은 후보 제시용만 — 기록은 항상 사용자 확인.**
     - **5-1 `## 목표`**: 신규 feature 는 `- [ ] {기능명} -> [상세](...)` 추가, `[x]` 완료 항목 불변, `--force` 로 대응 파일이 사라진 항목 제거.
     - **5-1.5 `scope/{domain}.md` 자동 생성**: scope 부재 + MANIFEST 진입파일에 매칭 H2 존재 시.
     - **5-2 `## 관련 파일`**: `scope/{domain}.md` 매칭 H2 표를 추출해 채운다. features 에 명시된 모델·서비스·라우트 **누락 금지**, 사용자 수동 행 보존 (중복만 제거), 빈 행 삭제.
  6. **prompts/ 자동 갱신** (`:71-73`) — `prompts/{planner,generator,evaluator}.md` + `.agent-state.yml.analyzed: true` 게이트. 상세: `references/prompts-update.md`.
  7. **분석 품질 자가 검증** (`:75-77`) — 6-5(doctor) 완료 후 4 항목 (커버리지·구조·정합성·추측 혐의). 상세: `references/self-verify.md`.
  7.5. **조건부 인터뷰** (`:79-81`) — 대상은 **이번 실행에서 신규 생성된 features 만** (`--regen-agents` 는 미발동). (1) 5 단계에서 이미 Read 한 `scope/{domain}.md` 재사용 (2) (d)>(b)>(c)>(a) 우선순위 + 파일 NN 순, **최대 8 문항** 일괄 질의 (3) 답변 반영 후 `- [x] {원문} → {답변 요약}` 체크. 소비 규칙 SSOT: `pilot/skills/context/shared/interview.md`.
  8. **결과 출력** (`:83-87`) — `분석 완료: {원본}` + features 목록 + `총 N개` + 갱신 파일 + 검증 1 줄 + (7.5 발동 시) `인터뷰: 해소 N건 / 이월 M건`. 해소 ≥1 건이면 `--regen-agents` 권장 INFO. 다음 단계는 `/pilot:autopilot {NN}` 또는 `@pilot-planner` 병기.
- **추측 금지** (`pilot/skills/analyze/SKILL.md:43·49`) — 원본에 없는 내용 추가 금지. 한 번 추측이 들어가면 후속 prompts/·planner·generator 가 모두 오염된다.

---

## `/pilot:create-feature`

활성 프로젝트에 **단일 기능** 을 프롬프트로 추가 (`pilot/skills/create-feature/SKILL.md:14`).

- **사전 확인**: P-1, P0, P1. `$ARGUMENTS` 비어있으면 안내 후 종료 (`pilot/skills/create-feature/SKILL.md:18-20`).
- **1. 기능명·slug·번호 결정** (`pilot/skills/create-feature/SKILL.md:24-26`) — 기능명 (한국어 허용, 30 자 이내) · slug (kebab-case, 최대 30 자) · `NN` = `features/*.md` (`.plan.md` 제외) 최댓값 +1 (폴더 없으면 `01`). slug 모호하면 후보 2~3 개 제시.
- **3. 명세 작성** (`pilot/skills/create-feature/SKILL.md:32-36`) — `> source: prompt` + `> created:` + `> user_prompt:` 메타 + analyze 와 동일 4 섹션 템플릿. 프롬프트에서 명시 추출 가능한 요소만 채우고 **추측성 내용은 placeholder** 로 남긴다. `## 예외 케이스` 직후 `## Open Questions` 4 카테고리 + `- (없음)` placeholder 필수.
- **3-bis. cross-domain 의존성 detect + Open Questions 분류** (`pilot/skills/create-feature/SKILL.md:38-40`) — MANIFEST 조회로 산출물 lookup 으로 답할 수 없는 영역을 detect. 매칭 외부 도메인은 `### (b)` 행 + INFO, 코드 외부 시스템은 `### (c)` 행.
- **3-ter. 조건부 인터뷰** (`pilot/skills/create-feature/SKILL.md:42-46`) — step 4 **보다 앞**에 위치 (답변이 spec 에 먼저 반영돼야 재생성이 최신 spec 기준으로 동작). 발동 조건: unchecked (`- [ ] `) ≥1 (soft gate). 절차: spec 명시 심볼 ↔ `scope/{domain}.md` **lookup only** (코드 탐색 금지, domain null 이면 skip) → (d)>(b)>(c)>(a) 순 **최대 4 문항** ("나중에 결정" 항상 제공) → `- [x]` 체크. **재개봉 방지**: 해소한 `### (b)` 행은 step 4 의 재detect 에서 재추가되지 않는다 (판정 키 = 외부 도메인명).
- **4~6 단계** (`pilot/skills/create-feature/SKILL.md:48-64`) — analyze 5~6 단계를 그대로 수행 (도메인 결정·5-1·5-2·6-1~6-4 절차·보존 규칙 모두 analyze 가 SSOT). 실제 차이는 2 가지뿐: 분석 소스가 docs/ 가 아니라 **현재 features/ 전체**, 첫 feature 추가 시 (`analyzed: false`) example placeholder 가 실내용으로 교체. 이후 `doctor.py workspace` 실행 → 결과 요약.
- **제약** (`pilot/skills/create-feature/SKILL.md:66-70`): 에이전트를 **자동 호출하지 않는다** (시작점은 `@pilot-planner`) · `> source: prompt` tag 는 `analyze --force` 의 덮어쓰기 승인 트리거 · docs 기반 다건 분할은 `/pilot:analyze`.

### Open Questions 4 카테고리 (SSOT: `pilot/skills/context/shared/open-questions.md`)

- **작성 규칙** (`:12-15`): 4 카테고리 헤더는 항상 모두 포함, 질문 없으면 `- (없음)` (작성자가 "정말 없는지" 의식적 확인 강제). detect 실패 시 헤더 + placeholder 만 작성하고 abort 안 함 (A2).
- **분류 기준** (`:41-44`): **(a)** 같은 도메인 추가 read 필요 (시그니처는 캡처됐으나 line-by-line detail 부족) · **(b)** cross-domain 산출물 부재 (MANIFEST `## 외부 도메인 reference` 매칭 미학습 도메인) · **(c)** 외부 시스템 spec 부재 · **(d)** 비즈니스 결정 영역 (코드로 결정 불가).
- **판정 매트릭스 (게이트)** (`:68-75`) — 3 wrapper 와 `plan-validate.py` 가 공유하는 단일 기준. 미해결 잔존 시 plan 마커: (a) `범위 제외`\|`추정 구현` · (b) `추정 구현`(사용자 명시 전제)\|`범위 제외` · (c) `범위 제외`(기본)\|`추정 구현` · **(d) `범위 제외` 만 — `추정 구현` 불인정**. 마커 부재는 Evaluator **Major**.
- **마커 어휘 (기계 검증 계약)** (`:77-99`): 정밀 마커 = 카테고리 키와 마커 어휘가 **같은 라인** / 포괄 마커 = "산출물 부재 상태에서 추정 구현" 전체 문구 (**(d) 제외** 커버) / (d) 특칙 = `(d)` 키 + `범위 제외` 동일 라인 또는 해결(`[x]`) 만 통과.
- **fail-closed 게이트 (`oq` 필드)** — `plan-validate.py` 가 plan 경로에서 대응 feature 파일을 자동 유도 (`NN-{slug}.plan.md`·`.plan.r{N}.md` → `NN-{slug}.md`) 해 미해결 항목 ↔ 처리 마커를 대조하고 결과를 JSON `oq` 필드 (`checked`·`feature_file`·`unresolved`·`errors`) 로 반환한다 (`pilot/skills/context/lifecycle/plan-schema.md:90-96·131-137`). feature 파일 부재 또는 `## Open Questions` 섹션 부재면 **skip** (`oq.checked: false` — 사이클 밖 plan 호환), 미해결 카테고리에 마커가 없으면 **invalid (fail-closed)**. plan 본문 스캔 시 fenced 코드블록은 마스킹돼 예시 줄이 게이트를 만족시킬 수 없다 (`pilot/tools/plan-validate.py:235-248·336-338`). `oq.errors` 가 1 건이라도 있으면 `valid: false` → exit 1 (`pilot/tools/plan-validate.py:438-439`).
- **에스컬레이션** (`open-questions.md:101-108`): Generator·Evaluator 가 게이트 실패를 발견한 시점에 **planner 인스턴스는 이미 종료돼 있다** — "Planner 에 재확인" 은 대화가 아니라 **새 `@pilot-planner` 호출** (stateless 재진입) 이다. 발견한 에이전트는 직접 라우팅하지 않고 사용자에게 보고 후 종료한다 (자동 라우팅 금지).

---

## `/pilot:learn`

소스 코드 → `workspace/context/` 도메인 문서 부트스트랩 (`pilot/skills/learn/SKILL.md:22`). 페르소나 **ethnographer** — "코드에 적힌 것만, 추측은 빈 칸으로 둔다", 사실 + `file:line` 인용 (`pilot/skills/learn/SKILL.md:17-20`).

- **인자** (`pilot/skills/learn/SKILL.md:28`): `{entry-point}` 필수 (`--boundary` 모드는 생략) · `--domain NAME` · `--depth N` (기본 2) · `--force` · `--boundary B --from A`.
- **사전 확인** (`pilot/skills/learn/SKILL.md:30-34`): P-1, P0 수행. **P1 미적용** — 활성 프로젝트 없어도 실행 가능 (workspace 부트스트랩 단계, STATE.md 불변경). `workspace/` 자체가 없으면 `workspace_missing` 후 종료. `config.md` 를 Read 해 `Ignore`·`language`·`source_root` 확보 (없으면 경고 1 줄 + 진행).
- **5 Phase 절차** — 사용자 확인 게이트 최대 2 회 (Phase 2 끝 · Phase 4 중간). **발견 파일 ≤10 개면 Phase 2 확인 자동 skip** (`pilot/skills/learn/SKILL.md:38·54`). **Abort cleanup 계약** — 어느 Phase 에서 중단해도 **어떤 Write 도 수행하지 않는다** (Phase 5 batch Write 진입 후엔 abort 불가).

  | Phase | 동작 | 출력 |
  | --- | --- | --- |
  | 1. 도메인 도출 | 파일 → 접미사 제거 / 폴더 → 마지막 폴더명 / 일반 진입점 → 부모 폴더명. sanitize = 영숫자·하이픈·**언더스코어** 외 제거 + 소문자화. **폴더-suffix 는 strip 하지 않는다** (파일명 접미사 제거와 대비되는 의도된 차이). `--domain` 이 자동 도출 override (`:40-42`) | `{domain}` |
  | 2. Inventory | **Glob/Grep 만, Read 금지.** 의존성 추적 (`--depth N`) → 역할별 분류 → 필터링 (config `Ignore`·테스트·벤더/생성물) → 외부 도메인 reference 추출 → 통계 1 줄 + 사용자 확인 1 (`:44-54`) | 발견 파일 N 개 |
  | 3. Read & 추출 | 크기별 전략: ≤300 줄 전체 / 301~1000 줄 targeted (헤더 1~30 줄 + Grep 매치 ±10 줄) / >1000 줄 skip + god file 알림. 25k 거부 시 **limit 1/2 축소** (`:56-66`) | 카테고리별 누적 |
  | 4. 구조 결정 + 생성 | `references/heuristics.md` 휴리스틱 → cross-domain transaction contracts 삽입 → 파일 크기 정책 적용 → 미리보기 + 사용자 확인 2 → 충돌 처리 → batch Write (`:68-75`) | `workspace/context/{domain}/*.md` |
  | 5. MANIFEST 갱신 + doctor | 기존 도메인 분류 구조 detect 후 형식에 맞춰 반영 → 외부 도메인 reference 섹션 갱신 → doctor 실행 → 결과 출력 (`:77-85`) | MANIFEST 갱신 + doctor 결과 |

- **핵심 가드** (`pilot/skills/learn/SKILL.md:46`): 방문 set (순환 의존 무한 루프 방지) · 발견 파일 >**50 개**면 통계 출력 후 좁히기 강력 권유.
- **파일 크기 정책** (`pilot/skills/learn/SKILL.md:72`): 진입/index **≤100 줄**, 본문 **≤200 줄** (초과 시 sub-domain → 카테고리 → 알파벳 순 분할).
- **추측 금지** (`pilot/skills/learn/SKILL.md:64`) — 코드 문자 그대로만 (주석 인용 허용), 모든 항목 `file:line` 인용 (`/pilot:pilot-doctor` 의 mtime drift 감지 입력).
- **프로젝트 식별자 배제** (`pilot/skills/learn/SKILL.md:66`) — scope·rules·MANIFEST·enums 는 개별 프로젝트보다 오래 사는 공유 지식이다. feature ID·티켓 키·PR/이슈 번호·분기/스프린트 라벨은 본문에 기록하지 않는다 (프로젝트 종료 후 의미를 잃어 공유 지식을 오염). 주석 인용·요약 시에도 토큰을 벗겨 도메인 사실만 적는다. **적용 범위는 `workspace/context/**` 산출물 한정** — 프로젝트-스코프 산출물의 feature ID 표기는 정상.
- **MANIFEST 갱신 규칙** (`pilot/skills/learn/SKILL.md:79-83`) — **기존 정의가 있으면 그에 따르고, 없을 때만 새로 만든다**. 표(3 컬럼+) → 행 추가 / 산문·리스트 → 동일 형식 append / 다른 헤딩 존재 → 그 안에 append / 부재 → 표준 3 컬럼 표 신설. H2 헤더는 `^##\s+도메인\s*분류\s*$` **정확 매칭** — `orchestrate-load.py:parse_manifest_domain_files` 자동 파싱 호환 필수라 이 정규식은 실측 wording 이며 "정정" 대상이 아니다 (파서 구현: `pilot/tools/orchestrate-load.py:256·260-316`).
- **Boundary 모드** (`pilot/skills/learn/SKILL.md:87-99`) — `--boundary {B} --from {A}` 는 `{B}` 전체 대신 **`{A}` 가 실제 호출하는 `{B}` 표면만** `boundaries/{A}--{B}.md` 로 포착 (O(접점 크기) 비용). 전제: `{A}` 가 MANIFEST `## 도메인 분류` 에 등록돼 있어야 함. 호출처 0 건이면 "경계 없음" 보고 후 **파일 미생성**. 본문 **≤150 줄**. 로드는 orchestrate-load 가 정방향 `boundaries/{domain}--*.md`·역방향 `*--{domain}.md` 를 자동 처리하므로 별도 MANIFEST 등록 불필요 (최대 6 건 — `pilot/tools/orchestrate-load.py:351`).
- **제약** (`pilot/skills/learn/SKILL.md:101-106`): v1 단일 언어·단일 진입점 가정 (멀티 언어 모노레포는 진입점을 나눠 호출) · **diff 모드 없음** (갱신은 `--force` 또는 sub-domain 추가) · 출력 구조 자유 — `scope/{domain}.md` 강제 안 함, **MANIFEST.md 가 discovery contract** · `scope/{domain}.md`·`rules/{domain}.md` 는 **사용자 커스텀 layer** 로 이 스킬이 직접 생성하지 않는다.

### 역방향 — 도메인 지식 환류 (SSOT: `pilot/skills/context/lifecycle/knowledge-sync.md`)

learn 이 "코드 → context/" 라면, 환류는 "사이클이 만든 변경 → context/" 다. **기존 문서가 코드와 다름 (우연 발견)** 은 `drift-protocol.md` 가, **이번 변경이 만든 지식의 누락 (사이클 종료 시 체계 점검)** 은 본 프로토콜이 다룬다 (`:3-7`).

- **판정 주체는 evaluator — 감지·보고만** (`:11-16`). **evaluator 는 `context/` 파일을 직접 Edit 하지 않는다** — 기록 주체는 사용자 승인을 받은 메인 대화다.
- **detected 기준 6 항목** (`:18-31`): learn Phase 3 추출 항목 (라우트·도메인 모델/테이블/컬럼·enum/상태값/도메인 상수·외부 의존·비즈니스 용어) + 본 프로토콜 고유 항목인 **6. context 문서에 이미 기록된 항목의 동작 변경**.
- **none 노이즈 가드** (`:32-36`): 내부 리팩터 (공개 표면 불변)·버그 수정·테스트만 변경·스타일/주석. 휴리스틱은 **"이 변경을 모르는 다음 planner 가 잘못된 계획을 세울 수 있는가"** — 아니면 none. **skip** 은 `domain: null` 뿐이며, 도메인 진입 문서 부재는 skip 이 아니라 detected 다 (`:38-42`).
- **REPORT 표기** (`:44-57`): VERIFICATION REPORT 의 `metrics` 블록에 `domain_impact: none | detected | skip — {유형}: {요약} → {대상 문서}` 로 기록한다. **gate 가 아니다** — status 판정에 영향이 없고 READY 와 detected 의 공존이 정상이다.
- **질의 시점** (`:59-62`): 감지·기록은 status 무관이지만, 사용자에게 던지는 **질의 블록은 `status: READY` 한정**이다. `NOT_READY` 는 변경 미확정이라 generator 재작업으로 판정이 무효화될 수 있어 질의를 다음 READY 재평가로 미룬다.
- **기록 규칙** (`:99-124`): 항목별 before/after 제시 후 최종 승인 → Edit 반영. **항목 5 건 이상 또는 섹션 구조 개편이면 개별 Edit 대신 `/pilot:learn {진입점} --force` 재실행을 권장**한다 (learn 산출물은 diff 모드 없는 덮어쓰기 갱신이라 재실행이 더 안전하고, 사용자 커스텀 layer 인 `scope/`·`rules/` 는 learn 이 건드리지 않아 보존된다). 기록 문안에 프로젝트 생애주기 토큰을 남기지 않는다. **`workspace/context/` 변경 커밋은 feature 머지를 기다리지 말고 기본 브랜치에 조기 합류**시킨다 — 공유 자산이라 feature 브랜치에 남겨두면 다른 브랜치에서 그 도메인 지식이 보이지 않는다.
- **경계** (`:126-135`): `drift` 는 "기존 문서가 실제와 다름" 을 사이클 중 우연히 발견한 것으로 REPORT 의 `gates.drift` (READY 와 모순) 에 실린다. `domain_impact` 는 "이번 변경이 만든 신규·변경 지식의 미반영" 을 diff 기준으로 체계 점검한 것으로 `metrics.domain_impact` (READY 와 공존) 에 실린다.
