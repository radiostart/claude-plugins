# v0.1.0 baseline fixture

## 목적

v0.1.0 거동을 캡처하여 v1 변경 후 회귀 검증에 사용한다.
config 비어있을 때 v1 출력이 v0.1.0 캡처와 byte-for-byte 또는 의미 동등하게 일치하는지
`diff.sh` 로 검증한다 (#01 #02 #04 의 backward-compat 0 brittle 1 차 검증).

## 두 단계 baseline

- **Stage 1 (config 비움)**: v0.1.0 = v1 동일 출력 검증. #01 #02 #04 의 backward-compat 확인.
  #03 도 default H3 생성 시 v0.1.0 `example/project.md` 와 동일 결과 (Models/Endpoints/Services) 기대.
- **Stage 2 (config 채움)**: v1 의 override 거동 캡처. 사용자 행 우선·#03 동적 H3 채움 검증.

## 현재 범위 (0a)

이 커밋은 **config/ 인공 fixture + diff.sh 골격**만 포함한다.
`_input/`, `learn/expected/`, `project/expected/`, `analyze/expected/` 는
Open Q #1 (입력 언어 결정) 이후 0b PR 로 추가한다.

## 디렉터리 구조

```
v0.1.0-baseline/
├── README.md                  # 이 파일
├── diff.sh                    # 회귀 비교 도구 (골격 — _input/ 부재 시 exit 2)
└── config/                    # #04 doctor 검증 케이스 (PASS·ERROR 픽스처)
    ├── pass-empty/config.md   # 신규 섹션 부재 → INFO
    ├── pass-valid/config.md   # 신규 섹션 정상 → PASS/INFO
    ├── error-column-mismatch/config.md  # scope 카테고리 2 컬럼 → ERROR
    ├── error-bad-header-char/config.md  # project.md 대상 H3 에 슬래시 → ERROR
    └── error-no-prefix/config.md        # scope 헤더 ## prefix 누락 → ERROR
```

## 재생성 절차 (0b 대상 — placeholder)

0b 작업 시:
1. `_input/` 에 더미 코드베이스 배치 (Ruby 또는 Python, 의존성 0 plain 스크립트).
2. v0.1.0 에서 `/pilot:learn`, `/pilot:project`, `/pilot:analyze` 각 1 회 실행.
3. 산출물을 `learn/expected/`, `project/expected/`, `analyze/expected/` 에 복사.
4. timestamp (`analyzed_at` 등) 를 `{ANALYZED_AT}` placeholder 로 정규화.
5. 커밋.

## diff.sh 사용법 (0b 이후)

```bash
# Stage 1 검증 (config 비움)
bash pilot/tests/fixtures/v0.1.0-baseline/diff.sh --stage 1

# Stage 2 검증 (config 채움)
bash pilot/tests/fixtures/v0.1.0-baseline/diff.sh --stage 2
```

exit 0 = 회귀 없음, exit 1 = diff 발견, exit 2 = `_input/` 미존재 (0b 미완료)
