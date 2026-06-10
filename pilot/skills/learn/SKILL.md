---
name: learn
description: >-
  기존 소스 코드에서 진입점(컨트롤러·서비스 파일 또는 폴더)을 받아
  `workspace/context/` 의 도메인 문서를 부트스트랩한다. `/pilot:analyze`
  가 docs/ 기획서를 features/ 로 가공하는 짝이라면, 이 스킬은 코드를
  읽어 컨텍스트를 만든다. 의존성을 N 단계까지 따라가며 파일 분류·정적
  추출(메서드·라우트·상태값·검증 규칙) 후 코드의 자연스러운 모양에
  맞춘 `{domain}.md` 또는 `{domain}/` 폴더를 생성하고 MANIFEST.md 색인을
  갱신한다. `--boundary B --from A` 는 외부 도메인 B 전체 대신 A 가 호출하는
  표면만 `boundaries/{A}--{B}.md` 로 포착한다 (cross-domain 경량 학습).
  추측 금지 — 코드에 적힌 것만 file:line 인용으로 정리한다.
---

# /pilot:learn

> **페르소나 — ethnographer** (이 스킬 SSOT, 공통 톤 [`identity.yml`](../context/shared/identity.yml) 위에 덧씌움)
> - voice: 코드에 적힌 것만. 추측은 빈 칸으로 둔다
> - phrasing: 사실 + file:line 인용
> - forbid: "'아마도'·'~일 것이다' 같은 추정 표현" / "코드에 없는 동작 서술"

소스 코드 진입점에서 도메인 컨텍스트를 부트스트랩한다.

대상: $ARGUMENTS

**사용 예:** `/pilot:learn app/controllers/api/<entity>s_controller.rb` · `/pilot:learn app/services/<domain>/ --depth 1 --force` · `/pilot:learn --boundary schoice --from wms`

**옵션:** `{entry-point}` (필수 — 단, `--boundary` 모드에선 생략) · `--domain NAME` · `--depth N` (기본 2) · `--force` · `--boundary B --from A` (경계 계약 모드 — 아래 별도 섹션).

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행 (P-1: TodoWrite 선로딩 · P0: memory-hint).

> **P1 미적용** — 활성 프로젝트 없어도 실행 가능 (workspace 부트스트랩 단계). `workspace/` 자체가 없으면 [messages.md](../context/shared/messages.md) 의 `workspace_missing` 출력 후 종료.

`workspace/context/config.md` 를 Read 하여 `Ignore` 패턴, `language`, `source_root` 확보. 파일·섹션 없으면 경고 한 줄만 출력하고 진행 (기본값: 모든 파일 포함, 휴리스틱은 진입 파일 확장자에서 추론).

**인자 파싱** — 플래그 분리 후 나머지를 `{entry-point}` 로 본다. 비어있음·경로 미존재·`--depth` 가 음수/비숫자면 에러 출력 후 종료.

---

## 수행 절차

5 phase. 사용자 확인 게이트 최대 2 회 (Phase 2 끝, Phase 4 중간). **발견 파일 ≤ 10 개 인 작은 진입점에서는 Phase 2 확인 자동 skip** (좁힐 여지 적은 작은 도메인의 사용자 prompt 피로 방지).

> **Abort cleanup 계약** — 어느 Phase 에서든 사용자가 중단하면 **어떤 Write 도 수행하지 않는다**. P5 의 batch Write 진입 후라면 abort 불가.

### Phase 1. 도메인 도출

진입점 경로에서 도메인 후보 추출:

- 파일 (`*_controller.rb`·`*_service.rb`·`*Controller`·`*Service`) → 접미사 제거.
- 폴더 → 마지막 폴더명. 동명 파일 있으면 진입 파일 채택.
- 일반 진입점 (`main.*`·`app.*`·`server.*`·`index.*`) → 부모 폴더명. 부모도 일반 (`src/`·`app/`·`lib/`) 이면 2단계 상위 또는 레포 root. 모두 일반이면 사용자 질의.

**sanitize** — 영숫자·하이픈·**언더스코어** 외 제거하고 소문자화 (Ruby/Python snake_case 폴더명 보존 목적). 공집합이면 사용자 질의. **절대경로 정규화** — 상대경로로 변환 후 부모 폴더명 추출. `--domain NAME` 있으면 자동 도출 무시. 모호하면 후보 2~3 개 제시 후 선택.

> **폴더-suffix 처리** — 파일과 달리 폴더에서는 `_service`·`_controller` 접미사를 strip 하지 **않는다** (예: `app/services/coupon_service/` → `coupon_service` 유지). Ruby 의 module namespace (`CouponService::*`) 와 일치시키기 위함.

### Phase 2. Inventory — Glob/Grep 만 사용 (Read 금지)

어떤 파일이 도메인에 속하는지 **선읽기 없이** 파악.

**핵심 가드:**

- **방문 set** — 의존성 추적 시 이미 본 파일 재방문 금지 (순환 의존 무한 루프 방지).
- **파일 수 cap** — 발견 파일 > **50 개** 면 통계 출력 직후 **사용자에게 좁히기 강력 권유**.

> **config lookup**: `workspace/context/config.md` 의 `## learn 언어 패턴` 섹션 Read. 두 표 (의존성 추적 + 역할 분류) 행이 있으면 우선 사용. 비어있으면 폴더 인접성 fallback. 잘못된 행은 무시하고 fallback + `[WARN] config.md ## learn 언어 패턴 {사유}: fallback 사용` 1 줄 (abort 안 함).

1. 진입점에서 의존성을 `--depth N` 만큼 추적. 미식별 언어는 폴더 인접성 fallback.
2. 발견 파일을 역할별 분류 (Glob·파일명 패턴·간단 Grep 헤더 — Read 없이).
3. **필터링**: config `Ignore` 패턴 / 테스트 파일 (`*_spec.rb`·`*_test.rb`·`*Test.kt`·`__tests__/**`·`*.test.ts`·`*.spec.ts`) / 벤더링·생성 (`vendor/**`·`node_modules/**`·`build/**`·`dist/**`·`.gen.*`) 제외.
4. **외부 도메인 클래스 reference 추출 (#09)** — 발견된 클래스/모듈 reference 를 내부 vs 외부로 분류하여 메모리에 누적. 상세: [`references/cross-domain.md`](references/cross-domain.md) Phase 2 섹션.
5. 통계 한 줄 출력 (`발견 파일 N개 (controllers M · services K · models L · routes R · helpers H · 기타 P) / 진입점 / 추적 깊이 / 도메인`).
6. **사용자 확인 1** — 범위 승인 (단 **발견 ≤ 10 개면 자동 skip**):

   ```
   a) 그대로 진행
   b) 좁히기: helpers 제외 / depth 축소 / 특정 폴더 제외
   c) 도메인명 변경
   d) 중단
   ```

### Phase 3. Read & 추출 (소스 코드 특화 전략)

승인된 범위의 파일에서 정적 정보만 추출. 구조적 추출 (시그니처·선언·검증 규칙) 이 본문 전체보다 가치가 높다.

**파일 크기별 read 전략:**

| 라인 | 전략 |
| --- | ---- |
| ≤ 300 | **전체 Read** |
| 301 ~ 1000 | **Targeted Read** — header (1~30 줄) + 언어별 패턴 Grep 으로 라인 번호 수집 + 매치 주변 ±10 줄 |
| > 1000 | **Skip + 사용자 알림** — 통상 god file. 필요하면 별도 진입점으로 호출 권장 |

**Targeted Read Grep 패턴:**

| 추출 대상 | Grep 패턴 |
| --------- | --------- |
| 클래스 선언·헤더 | `^class \|^module \|^interface \|^@RestController` |
| public 메서드 시그니처 | `^\s*def \|^\s*public \|^\s*fun ` |
| route / endpoint | `@GetMapping\|@PostMapping\|^get \|^post ` |
| state enum | `enum \|STATUSES =\|@Entity\|case class ` |
| validation·guard | `validates \|@Valid\|require\|assert ` |

25k 토큰 거부 시 `limit` 1/2 축소 재시도. 누적 ~50k 토큰 초과시 사용자 진행 여부 재확인.

**추출 항목**: 파일 목적 (상단 docstring·주석) · public interface (시그니처·route·클래스·상속) · 의존성 · state enum · business rule · **cross-domain transaction nesting** (외부 namespace receiver만 capture — 상세: [`references/cross-domain.md`](references/cross-domain.md) Phase 3).

**추측 금지**:

- 코드에 문자 그대로 있는 내용만 인용. 주석 인용은 허용.
- 모든 추출 항목은 `file:line` 인용을 남긴다 (`/pilot:doctor` 가 mtime drift 로 stale 감지).

추출 결과는 메모리에 카테고리별 (routes·controllers·services·models·enums·rules) 로 누적.

### Phase 4. 구조 결정 + 미리보기 + 생성

1. **구조 결정** — 휴리스틱으로 폴더 구조 선택. 상세: [`references/heuristics.md`](references/heuristics.md). 요약:

   | 코드 형태 | 추천 구조 |
   | --------- | --------- |
   | 단일 도메인, 작음 (총 ≤200 줄) | `{domain}.md` 한 파일 |
   | 단일 도메인, 큼 | `{domain}/` 폴더 + 카테고리 또는 sub-cluster |
   | 명확한 sub-domain | 코드 미러 — `{domain}/{sub}.md` |
   | Routes/Models/Services 명확 분리 | `{domain}/routes.md` · `models.md` · `services.md` |
   | State machine 풍부 | `enums/{Model}.md` 추가 |

2. **Cross-domain Transaction Contracts sub-section** — Phase 3 누적 `cross_domain_transactions` 있으면 `## 다중 DB` 직후 sub-section 삽입. 0 건이면 skip. 상세: [`references/cross-domain.md`](references/cross-domain.md) Phase 4.

3. **파일 크기 정책**: 진입/index ≤ 100 줄 (요약 + 링크만), 본문 ≤ 200 줄 (초과 시 sub-domain → 카테고리 → 알파벳 순 분할).

4. **미리보기 출력** — 생성될 파일 tree + 각 파일 첫 1~2 줄 샘플.

5. **사용자 확인 2** — 구조 승인 (`a) 이대로 / b) 다르게 분할 / c) 중단`).

6. **충돌 처리** — `{domain}.md` 또는 `{domain}/` 이미 존재 시: `--force` 있으면 덮어쓰기, 없으면 3-way 질의 (`overwrite / sub-domain 추가 / 중단`).

7. 승인 후 **batch Write** — 같은 turn 안에서 여러 Write tool_use 묶어 호출 (3~5 개 단위).

### Phase 5. MANIFEST.md 갱신 + doctor

MANIFEST 자유 형식 — **기존 정의가 있으면 그에 따르고, 없을 때만 새로 만든다**.

1. `workspace/context/MANIFEST.md` Read.
2. **기존 도메인 분류 구조 detect**:

   | 발견된 형태 | 처리 |
   | ----------- | ---- |
   | `## 도메인 분류` H2 + 표 (3 컬럼 이상) | 표에 행 추가 |
   | `## 도메인 분류` H2 + 산문/리스트 | 동일 형식으로 append |
   | 다른 헤딩으로 도메인 목록 존재 | 그 헤딩 안에 append |
   | 도메인 분류 섹션 부재 | 새 섹션 + 표준 3 컬럼 표 (`| 도메인 | 진입 파일 | 설명 |`) 생성 |

   > **H2 헤더 정확 매칭** — `^##\s+도메인\s*분류\s*$` 정규식 매칭. 코드블록 안·prose 인용은 무시 (`orchestrate-load.py:parse_manifest_domain_files` 자동 파싱 호환 필수).

3. **추가 항목 형식** (구조에 맞춰 변형) — 표: `| {domain} | \`{entry-file-path}\` | {summary} |` · 리스트: `- **{domain}** — \`{entry-file-path}\` : {summary}` · 산문: `{domain} 도메인은 \`{entry-file-path}\` 가 진입점이며 {설명}.`. `{entry-file-path}` 는 `workspace/context/` 기준 상대 경로.

4. **외부 도메인 reference 섹션 갱신 (#09·#10)** — Phase 2 누적 외부 클래스 처리. 현재 도메인 stale row 제거 + 외부 클래스 0 건이면 skip, 1+ 이면 `## 외부 도메인 reference (learn 미완료)` 표에 행 추가. 상세: [`references/cross-domain.md`](references/cross-domain.md) Phase 5.

5. doctor 실행: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace`.

6. **결과 출력** — `learn 완료: {domain}` + 생성된 파일 목록 (`workspace/context/{domain}/*.md`, 각 NN 줄) + 읽은/발견/제외 파일 수 + MANIFEST 갱신 1 줄 + doctor 결과 + 다음 단계 안내 (`파일 검토` · `/pilot:project {프로젝트명}` · `/pilot:learn {다른 진입점} --domain {domain}`).

---

## Boundary 모드 — `--boundary {B} --from {A}`

외부 도메인 `{B}` 를 전체 학습하지 않고, **학습된 도메인 `{A}` 가 실제 호출하는 `{B}` 의 표면만** 포착해 `workspace/context/boundaries/{A}--{B}.md` 를 생성한다. cross-domain feature 에서 `{B}` 전체 learn 의 경량 대안 — 비용은 O(접점 크기), spec 작성에 필요한 정보 대부분은 접점에 있다.

**전제 검증:**

- `{A}` 가 MANIFEST `## 도메인 분류` 에 등록돼 있어야 한다. 미등록이면 에러 + `/pilot:learn {진입점}` 안내 후 종료.
- `--from` 생략 시 활성 프로젝트 `.agent-state.yml` 의 `domain` 사용. 그것도 없으면 사용자 질의.
- `{A}`·`{B}` sanitize 는 Phase 1 과 동일 (영숫자·하이픈·언더스코어, 소문자화).

**절차** — Phase 2 (외부 reference detect)·Phase 3 (transaction nesting) 알고리즘을 재사용한 3 단계. 상세: [`references/cross-domain.md`](references/cross-domain.md) § Boundary 모드.

1. **호출처 수집** — `{A}` 소스에서 `{B}` namespace reference Grep (ignore 패턴 동일 적용). 0 건이면 "경계 없음" 보고 후 종료 — 파일 생성 안 함.
2. **표면 추출** — 호출처 ±10 줄 Read 로 사용 형태 수집 + `{B}` 정의 파일은 **호출된 심볼만** Targeted Read. 전체 학습 금지.
3. **생성 + 색인** — `boundaries/{A}--{B}.md` Write (본문 ≤ 150 줄) → MANIFEST 외부 reference 표의 `{B}` 행 추천 컬럼에 ` · 경계: {A}--{B}.md` 표기 (행 제거 금지 — 전체 learn 완료가 아님) → doctor 실행.

**로드 배선** — orchestrate-load 가 활성 도메인 기준 `boundaries/{domain}--*.md` (정방향: 내가 호출하는 표면) 와 `*--{domain}.md` (역방향: 남이 나를 호출하는 표면 — 영향 분석) 를 자동 로드한다. 별도 MANIFEST 등록 불필요.

---

## 제약

- 플러그인 v1 — **단일 언어·단일 진입점** 가정. 멀티 언어 모노레포는 진입점을 나눠 호출.
- **추측 금지** — 코드에 없는 비즈니스 의도 본문에 쓰지 않음. 주석 인용만 허용.
- **diff 모드 없음** — 갱신은 `--force` 또는 sub-domain 추가.
- 활성 프로젝트와 무관 — STATE.md 변경하지 않음.
- **출력 구조는 codebase 따라 자유** — `scope/{domain}.md` 고정 컨벤션 강제 안 함. **MANIFEST.md 가 discovery contract**.
- `scope/{domain}.md` · `rules/{domain}.md` 는 **사용자 커스텀 layer**. 본 스킬은 이 두 경로를 직접 만들지 않는다.

---

## 참고

- `/pilot:analyze` — docs/ 기획서를 features/ 로 가공 (짝).
- `/pilot:init` — workspace 스켈레톤 생성 (이 스킬 실행 전 1 회).
- `/pilot:doctor` — 갱신 후 정합성 점검 (자동 호출됨).
- 구조 결정 휴리스틱: [`references/heuristics.md`](references/heuristics.md).
- cross-domain detect 알고리즘: [`references/cross-domain.md`](references/cross-domain.md).
