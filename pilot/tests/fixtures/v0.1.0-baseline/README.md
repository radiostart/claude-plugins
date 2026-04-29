# v0.1.0-baseline fixture

## 목적

v0.2.0 + config-post-accepted (마이그레이션 accepted 후 default 주입) 상태를 baseline 으로 캡처하여
향후 거동 회귀 검증에 사용한다. `diff.sh --actual {dir}` 로 재실행 결과와 비교한다.

## Stage 정의

- **Stage 1 (본 baseline)**: v0.2.0 + `config-post-accepted` — 마이그레이션 accepted 후 v0.1.0 default 5 언어 행이 주입된 상태.
  세 스킬 (`/pilot:learn`·`/pilot:project`·`/pilot:analyze`) 의 산출물을 `expected/` 로 캡처.
- **Stage 2 (v1.1 milestone 보류)**: 사용자 패턴 override 거동 캡처. 본 baseline 에 미포함.

> **D10 결정 영향**: v0.2.0 은 default 표 폐지 + 자동 마이그레이션 (M1) 을 포함한다.
> `migration_v0_2_0: accepted` 상태에서 캡처했으므로 `learn/expected/config.md` 는
> v0.1.0 default 5 언어 행이 주입된 상태다. config 가 비어있을 때 폴더 인접성 fallback 거동은
> `config/pass-empty/` fixture 가 별도로 검증한다.

## 사전 조건 (재생성 시)

1. **plugin version bump 완료**: `pilot/.claude-plugin/plugin.json` 이 `0.2.0` 이어야 마이그레이션 prompt 가 발화한다.
2. **빈 workspace 준비**: `workspace/context/config.md` 의 `## learn 언어 패턴` 두 표가 비어있어야 마이그레이션이 트리거된다.
3. `/pilot:doctor --fix` 실행 → 마이그레이션 prompt 에 `accepted` 선택 → config.md 에 default 5 언어 행 주입.

## 디렉터리 구조

```
v0.1.0-baseline/
├── README.md                  # 이 파일
├── diff.sh                    # 회귀 비교 도구 (--actual {dir})
├── _input/
│   └── python-sample/         # 토이 Python 코드베이스 (의존성 0)
│       ├── main.py            # FastAPI 진입점
│       ├── routes.py          # HTTP 라우트 6 개
│       ├── models/
│       │   ├── user.py        # User·UserProfile dataclass
│       │   └── order.py       # Order·OrderItem·OrderStatus
│       ├── services/
│       │   ├── __init__.py    # 빈 패키지 마커 (.gitignore 제외)
│       │   ├── auth.py        # AuthService
│       │   └── checkout.py    # CheckoutService
│       ├── helpers.py         # to_dict·paginate·format_price
│       ├── docs/
│       │   └── sample-spec.md # 토이 기획서 (analyze 입력)
│       ├── .gitignore         # */__init__.py 무시 포함
│       └── README.md          # 실행 금지 안내
├── config/                    # doctor 검증 케이스 (0a)
│   ├── pass-empty/config.md
│   ├── pass-valid/config.md
│   ├── error-column-mismatch/config.md
│   ├── error-bad-header-char/config.md
│   └── error-no-prefix/config.md
├── migration/                 # 마이그레이션 전·후 config 캡처 (0a)
│   ├── config-pre.md          # 마이그레이션 전 (빈 표)
│   ├── config-post-accepted.md # accepted 후 (default 주입)
│   └── config-post-declined.md # declined 후 (빈 채로)
├── learn/expected/            # /pilot:learn _input/python-sample/main.py 산출
│   ├── MANIFEST.md
│   ├── config.md              # migration accepted 상태 (default 주입)
│   └── python-sample/
│       ├── index.md
│       └── inventory.md
├── project/expected/          # /pilot:project python-sample-demo 산출
│   └── projects/python-sample-demo/
│       ├── project.md         # ## 관련 파일 H3 + 빈 표 (analyze 전)
│       ├── .agent-state.yml
│       └── prompts/
│           ├── planner.md
│           ├── generator.md
│           └── evaluator.md
└── analyze/expected/          # /pilot:analyze 산출 (docs/sample-spec.md)
    ├── scope/
    │   └── python-sample.md   # Routes·Models·Services 표
    └── projects/python-sample-demo/
        ├── project.md         # ## 관련 파일 표 본문 채워진 상태
        ├── .agent-state.yml   # analyzed: true, migration_v0_2_0: accepted
        └── prompts/
            ├── planner.md
            ├── generator.md
            └── evaluator.md
```

## 재생성 절차

Stage 1 baseline 을 다시 캡처할 때 아래 순서를 따른다.

### (a) v0.2.0 환경 준비

```bash
# plugin version 확인
cat pilot/.claude-plugin/plugin.json | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"
# 기대 출력: 0.2.0

# workspace config 초기화 (## learn 언어 패턴 두 표를 빈 상태로)
# doctor --fix 로 마이그레이션 트리거
python3 pilot/tools/doctor.py workspace --fix
# 프롬프트에서 "accepted" 선택 → config.md 에 default 5 언어 행 주입
```

### (b) 임시 출력 디렉터리 준비

```bash
REGEN_DIR=$(mktemp -d)
mkdir -p "$REGEN_DIR/learn/expected"
mkdir -p "$REGEN_DIR/project/expected/projects/python-sample-demo"
mkdir -p "$REGEN_DIR/analyze/expected/scope"
mkdir -p "$REGEN_DIR/analyze/expected/projects/python-sample-demo"
```

### (c) 세 스킬 재실행

```bash
# 1. learn
/pilot:learn pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/main.py
# 산출물을 $REGEN_DIR/learn/expected/ 로 복사

# 2. project
/pilot:project python-sample-demo
# 산출물을 $REGEN_DIR/project/expected/projects/python-sample-demo/ 로 복사

# 3. analyze
/pilot:analyze
# 산출물을 $REGEN_DIR/analyze/expected/ 로 복사
```

### (d) diff 검증

```bash
bash pilot/tests/fixtures/v0.1.0-baseline/diff.sh --actual "$REGEN_DIR"
# exit 0 = 재현성 확인, exit 1 = 차이 발생 → 절차 보정 후 재캡처
```

### (e) expected 갱신 후 커밋

```bash
cp -r "$REGEN_DIR/learn/expected" pilot/tests/fixtures/v0.1.0-baseline/learn/
cp -r "$REGEN_DIR/project/expected" pilot/tests/fixtures/v0.1.0-baseline/project/
cp -r "$REGEN_DIR/analyze/expected" pilot/tests/fixtures/v0.1.0-baseline/analyze/
git add pilot/tests/fixtures/v0.1.0-baseline/
git commit -m "chore: regenerate v0.1.0-baseline expected (v0.2.0 + migration-accepted)"
```

## diff.sh 사용법

```bash
# 재실행 결과 REGEN_DIR 와 비교
bash pilot/tests/fixtures/v0.1.0-baseline/diff.sh --actual {REGEN_DIR}
```

exit 0 = 회귀 없음, exit 1 = diff 발견, exit 2 = 인자 오류 또는 `_input/` 미존재

## 운영 가이드

### timestamp 노이즈

`.agent-state.yml` 의 `analyzed_at` 등 timestamp 는 캡처 시점 그대로 보존.
재실행 시 timestamp 가 달라 `diff.sh` 가 exit 1 을 반환한다.
이는 의도된 동작 — v1.1 milestone 에서 placeholder 정규화 도입 시 expected 도 일괄 갱신.

### LLM wording 변동 (결정성 한계)

본 `expected/` 는 LLM 시뮬레이션으로 산출한 캡처다.
실제 스킬 실행 결과의 wording (문장 순서·약어·표현) 이 다를 수 있다.
diff 가 발생하면 실제 실행 결과를 재캡처한 뒤 expected 를 갱신한다.
"wording 차이 = 회귀" 가 아니라 "구조·필드·규칙 차이 = 회귀" 기준으로 판정.

### Stage 2 보류

config override 거동 (사용자가 자기 패턴 정의) 캡처는 v1.1 milestone.
본 baseline 은 Stage 1 (migration accepted + default 주입) 만 포함.
