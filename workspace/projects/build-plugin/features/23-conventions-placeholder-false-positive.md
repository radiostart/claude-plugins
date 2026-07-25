# #23 doctor conventions 플레이스홀더 오탐 (D-3)

> source: prompt
> created: 2026-07-25T00:00:00Z
> user_prompt: "#21 planner 가 발견한 `config.md:32-33` conventions 오탐 — 본 범위 제외하고 별도 feature 로 분리 (D-3 결정)"

## 요구사항

- **조건**: #20 완료 상태의 `pilot/tools/doctor/integrity.py`.
- **트리거**: `check_conventions_paths` 가 config 표의 **설명용 플레이스홀더를 실선언으로 파싱**해 doctor 실행마다 WARN 2건을 발화한다 (현행 WARN 4건 중 2건).
- **기대결과**:
  - `workspace/context/config.md:32-33` 의 `conventions_doc`·`conventions_evals` 행 값 셀 `` 예: `context/conventions.md` `` 같은 **플레이스홀더 패턴이 실선언으로 오인되지 않는다.**
  - 현행 오탐 메시지: `conventions: conventions_doc=예: \`context/conventions.md 로 선언됐으나 파일 없음`
  - **근본 원인은 파서** — 문서(config.md)만 고치면 다른 사용자 workspace 의 동일 오탐이 남는다. 따라서 `check_conventions_paths` (`integrity.py:872-937`) 수정이 본체다.
  - 수정 후 doctor WARN 이 4건 → 2건으로 줄어든다 (나머지 2건은 본 feature 범위 밖).

## 상태 전환

_(없음)_

## 비즈니스 규칙

- 오탐 제거가 **정상 미선언까지 침묵시키면 안 된다** — 실제로 `conventions_doc` 을 선언했는데 파일이 없는 경우는 계속 WARN 이어야 한다.
- 플레이스홀더 판정 기준을 코드에 하드코딩한 한국어 문자열(`예:`)에만 의존하면 취약하다 — 판정 규칙을 명시적으로 설계할 것.
- 기존 doctor 테스트가 깨지지 않아야 한다 (`pilot/tests/tools/`).

## 예외 케이스

- config.md 템플릿 자체가 플레이스홀더를 값 셀에 적도록 유도하고 있다면, 파서 수정과 **템플릿 표기 규약**을 함께 정해야 재발하지 않는다.
- `--fix` 자동 조치 대상으로 삼을지 여부는 미결 — 사용자 workspace 파일을 자동 편집하는 범위 확대라 신중해야 한다.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [ ] 플레이스홀더 판정 규칙 — (i) 값 셀이 백틱 코드 스팬 **단독**이 아니면 미선언 취급 (ii) 특정 접두사(`예:`·`e.g.`) 인식 (iii) config.md 템플릿에 미선언 표기(`—`)를 규약화하고 파서는 그것만 인정. 어느 쪽을 채택할 것인가
- [ ] 본 수정을 `--fix` 자동 조치에 포함할 것인가, 진단(WARN 정확화)까지만 할 것인가
