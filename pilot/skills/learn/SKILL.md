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

**옵션:** `{entry-point}` (필수 — `--boundary` 모드는 생략) · `--domain NAME` · `--depth N`(기본 2) · `--force` · `--boundary B --from A`(경계 계약 모드).

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행. **P1 미적용** — 활성 프로젝트 없어도 실행 가능 (workspace 부트스트랩 단계, STATE.md 불변경). `workspace/` 자체가 없으면 [messages.md](../context/shared/messages.md) 의 `workspace_missing` 출력 후 종료.

`workspace/context/config.md` 를 Read 하여 `Ignore` 패턴·`language`·`source_root` 확보 (없으면 경고 1줄 + 진행, fallback: 모든 파일 포함·진입 확장자로 언어 추론). 인자 파싱 후 `{entry-point}` 비어있음·경로 미존재·`--depth` 음수/비숫자면 에러 후 종료.

## 수행 절차

5 phase. 사용자 확인 게이트 최대 2 회 (Phase 2 끝 · Phase 4 중간). **발견 파일 ≤10개면 Phase 2 확인 자동 skip**. **Abort cleanup 계약** — 어느 Phase 에서든 중단 시 **어떤 Write 도 수행하지 않는다** (Phase 5 batch Write 진입 후엔 abort 불가).

### Phase 1. 도메인 도출

진입점에서 도메인 후보 추출: 파일(`*_controller.rb`·`*Service` 등) → 접미사 제거 / 폴더 → 마지막 폴더명 / 일반 진입점(`main.*`·`app.*`) → 부모 폴더명(부모도 일반이면 2단계 상위 또는 질의). **sanitize** — 영숫자·하이픈·**언더스코어** 외 제거 + 소문자화. **폴더-suffix 는 strip 하지 않는다** (`app/services/coupon_service/` → `coupon_service` 유지 — Ruby module namespace 일치 목적. 파일명은 접미사 제거와 대비되는 의도된 차이). `--domain NAME` 있으면 자동 도출 무시. 모호하면 후보 2~3개 제시 후 선택.

### Phase 2. Inventory — Glob/Grep 만 사용 (Read 금지)

**핵심 가드**: 방문 set(순환 의존 무한 루프 방지) · 발견 파일 >**50개**면 통계 출력 후 좁히기 강력 권유.

**config lookup**: `## learn 언어 패턴` 두 표(의존성 추적/역할 분류) 행이 있으면 우선, 없으면 폴더 인접성 fallback. 잘못된 행은 무시 + `[WARN] config.md ## learn 언어 패턴 {사유}: fallback 사용` (A2).

1. `--depth N` 만큼 의존성 추적 (미식별 언어는 폴더 인접성).
2. 발견 파일 역할별 분류 (Glob·파일명 패턴·Read 없는 간단 Grep 헤더).
3. **필터링**: config `Ignore` / 테스트 파일(`*_spec.rb`·`*_test.rb`·`__tests__/**` 등) / 벤더·생성물(`vendor/**`·`node_modules/**`·`build/**` 등) 제외.
4. **외부 도메인 클래스 reference 추출 (#09)** — 내부 vs 외부 분류해 메모리 누적. 상세: [`references/cross-domain.md`](references/cross-domain.md) Phase 2.
5. 통계 1줄 출력 후 **사용자 확인 1** (발견 ≤10개면 자동 skip): `a) 진행 b) 좁히기 c) 도메인명 변경 d) 중단`.

### Phase 3. Read & 추출

승인된 범위에서 정적 정보만 추출 (구조적 추출이 본문 전체보다 가치 높음). 크기별 전략: ≤300줄 전체 Read / 301~1000줄 targeted Read(헤더 1~30줄 + 언어별 Grep 패턴 매치 주변 ±10줄) / >1000줄 skip + 알림(god file — 별도 진입점 권장).

**Targeted Read Grep 패턴**: 클래스 선언(`^class |^module |^interface |^@RestController`) · public 메서드(`^\s*def |^\s*public |^\s*fun `) · route(`@GetMapping|@PostMapping|^get |^post `) · state enum(`enum |STATUSES =|@Entity|case class `) · validation(`validates |@Valid|require|assert `).

25k 토큰 거부 시 **limit 1/2 축소** 재시도 (소스 코드는 라인당 토큰 밀도가 낮아 1/2 로 충분 — analyze 의 표 중심 마크다운 1/3 규칙과 의도된 차이). 누적 ~50k 초과 시 진행 여부 재확인.

**추출 항목**: 파일 목적 · public interface(시그니처·route·클래스·상속) · 의존성 · state enum · business rule · **cross-domain transaction nesting**(외부 namespace receiver 만 — [`references/cross-domain.md`](references/cross-domain.md) Phase 3). **추측 금지** — 코드 문자 그대로만 (주석 인용 허용 — 아래 식별자 배제 적용), 모든 항목 `file:line` 인용 (`/pilot:pilot-doctor` 의 mtime drift 감지 입력). 카테고리별(routes·controllers·services·models·enums·rules) 메모리 누적.

**프로젝트 식별자 배제** — scope·rules·MANIFEST·enums 는 개별 프로젝트보다 오래 사는 공유 지식이다. 프로젝트 생애주기에 종속된 토큰 — feature ID (`F{숫자}`·`features/NN`·`#34`), 티켓 키 (`ABC-123`), PR·이슈 번호, 분기·스프린트 라벨 — 은 본문에 기록하지 않는다 (프로젝트 종료 후 "어느 프로젝트의 F9 인지" 알 수 없어 공유 지식을 오염). 주석 인용·요약 시에도 토큰을 벗겨 도메인 사실만 적는다: `# F14 B 승인 절차` → `B 승인 절차`. 이 규칙은 공유 context (`workspace/context/**`) 산출물에만 적용 — `projects/{P}/features/`·`*.plan.md` 등 프로젝트-스코프 산출물의 feature ID 표기는 정상이다.

### Phase 4. 구조 결정 + 미리보기 + 생성

1. **구조 결정** — 휴리스틱으로 폴더 구조 선택 (단일 도메인 소/대·sub-domain·Routes-Models-Services 분리·state machine 풍부 등). 상세: [`references/heuristics.md`](references/heuristics.md).
2. **Cross-domain Transaction Contracts** — Phase 3 누적 건 있으면 `## 다중 DB` 직후 sub-section 삽입(0건이면 skip). [`references/cross-domain.md`](references/cross-domain.md) Phase 4.
3. **파일 크기 정책**: 진입/index **≤100줄**, 본문 **≤200줄** (초과 시 sub-domain → 카테고리 → 알파벳 순 분할).
4. 미리보기(생성 파일 tree + 샘플 1~2줄) → **사용자 확인 2** (`a) 이대로 b) 다르게 분할 c) 중단`).
5. **충돌 처리** — 기존 파일 존재 시 `--force` 면 덮어쓰기, 없으면 3-way 질의(overwrite/sub-domain 추가/중단).
6. 승인 후 **batch Write** — [coding.md](../context/shared/coding.md) `## 독립 파일 배치 작업` 절차.

### Phase 5. MANIFEST.md 갱신 + doctor

MANIFEST 자유 형식 — **기존 정의가 있으면 그에 따르고, 없을 때만 새로 만든다**.

1. Read 후 **기존 도메인 분류 구조 detect**: 표(3컬럼+) → 행 추가 / 산문·리스트 → 동일 형식 append / 다른 헤딩 존재 → 그 안에 append / 부재 → 표준 3컬럼 표 신설.
2. **H2 헤더 정확 매칭** — `^##\s+도메인\s*분류\s*$` (코드블록·prose 인용 무시. `orchestrate-load.py:parse_manifest_domain_files` 자동 파싱 호환 필수 — 이 정규식은 실측 wording 이라 "정정"하지 않는다).
3. **외부 도메인 reference 섹션 갱신 (#09·#10)** — Phase 2 누적 처리(현재 도메인 stale row 제거 + 0건이면 skip, 1+ 이면 표에 행 추가). [`references/cross-domain.md`](references/cross-domain.md) Phase 5.
4. doctor 실행: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace`.
5. **결과 출력** — `learn 완료: {domain}` + 생성 파일 목록 + 읽은/발견/제외 파일 수 + MANIFEST 갱신 1줄 + doctor 결과 + 다음 단계 안내.

## Boundary 모드 — `--boundary {B} --from {A}`

`{B}` 전체 대신 **`{A}` 가 실제 호출하는 `{B}` 표면만** `boundaries/{A}--{B}.md` 로 포착 (O(접점 크기) 비용).

**전제**: `{A}` 가 MANIFEST `## 도메인 분류` 에 등록돼 있어야 함(미등록이면 에러+안내 후 종료). `--from` 생략 시 활성 프로젝트 `.agent-state.yml.domain` 사용(그것도 없으면 질의). `{A}`·`{B}` sanitize 는 Phase 1 과 동일.

**절차** (Phase 2·3 알고리즘 재사용 — 상세: [`references/cross-domain.md`](references/cross-domain.md) § Boundary 모드):

1. 호출처 수집 — `{A}` 소스에서 `{B}` namespace reference Grep. 0건이면 "경계 없음" 보고 후 종료 (**파일 미생성**).
2. 표면 추출 — 호출처 ±10줄 Read + `{B}` 정의 파일은 호출된 심볼만 targeted Read (전체 학습 금지).
3. 생성+색인 — `boundaries/{A}--{B}.md` Write (**본문 ≤150줄**) → MANIFEST 외부 reference 표의 `{B}` 행에 ` · 경계: {A}--{B}.md` 표기 (**행 제거 금지**) → doctor 실행.

**로드 배선** — orchestrate-load 가 활성 도메인 기준 `boundaries/{domain}--*.md`(정방향)와 `*--{domain}.md`(역방향)를 자동 로드. 별도 MANIFEST 등록 불필요.

## 제약

- 플러그인 v1 — 단일 언어·단일 진입점 가정. 멀티 언어 모노레포는 진입점을 나눠 호출.
- **diff 모드 없음** — 갱신은 `--force` 또는 sub-domain 추가.
- **출력 구조는 codebase 따라 자유** — `scope/{domain}.md` 강제 안 함. **MANIFEST.md 가 discovery contract**.
- `scope/{domain}.md`·`rules/{domain}.md` 는 **사용자 커스텀 layer** — 이 스킬은 직접 생성하지 않는다.

## 참고

- `/pilot:analyze` — docs/ 기획서를 features/ 로 가공 (짝). `/pilot:pilot-init` — workspace 스켈레톤 (선행 1회).
- 구조 결정 휴리스틱: [`references/heuristics.md`](references/heuristics.md) · cross-domain detect: [`references/cross-domain.md`](references/cross-domain.md)
