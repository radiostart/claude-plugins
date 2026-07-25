# #23 doctor 파서 오탐 2건 — conventions 플레이스홀더 · features 카운트

> source: prompt
> created: 2026-07-25T00:00:00Z
> user_prompt: "#21 planner 가 발견한 `config.md:32-33` conventions 오탐 — 본 범위 제외하고 별도 feature 로 분리 (D-3 결정)"
> scope_extended: 2026-07-25 — `count_real_features` 의 `.plan.critic.md` 미제외 오탐을 사용자 지시로 본 feature 에 편입

## 요구사항

- **조건**: #20 완료 상태의 `pilot/tools/doctor/`.
- **트리거**: doctor 파서가 **실제가 아닌 것을 세어** 잘못된 WARN 을 발화한다. 성격이 같은 2건을 한 feature 로 묶는다.
- **기대결과**:

  **(A) conventions 플레이스홀더 오탐** (D-3, 현행 WARN 4건 중 2건)
  - `workspace/context/config.md:32-33` 의 `conventions_doc`·`conventions_evals` 행 값 셀 `` 예: `context/conventions.md` `` 같은 **플레이스홀더 패턴이 실선언으로 오인되지 않는다.**
  - 현행 오탐 메시지: `conventions: conventions_doc=예: \`context/conventions.md 로 선언됐으나 파일 없음`
  - **근본 원인은 파서** — 문서(config.md)만 고치면 다른 사용자 workspace 의 동일 오탐이 남는다. 따라서 `check_conventions_paths` (`integrity.py:872-937`) 수정이 본체다.

  **(B) features 카운트 오탐** (2026-07-25 doctor 실행 중 발견, 현행 WARN 4건 중 1건)
  - `count_real_features` (`pilot/tools/doctor/_common.py:197-204`) 가 `.plan.md` 는 제외하지만 **`.plan.critic.md` 는 제외하지 않는다**:

    ```python
    if p.is_file() and p.suffix == ".md" and not p.name.endswith(".plan.md")
    ```
  - 실측: spec 24개 + `.plan.critic.md` 5개(#17~#21) = **29** 로 계산돼 `build-plugin drift: features 24 → 29 (증가 5)` WARN 발화. `.agent-state.yml` 의 `last_analyzed_features: 24` 가 정확한 값이다.
  - **증상이 해로운 이유** — WARN 처방이 `/pilot:analyze --regen-agents` 라, 따르면 불필요한 prompts 재생성을 수행하게 된다.
  - **critic 을 쓰는 프로젝트에서만 드러난다** — planner-critic 도입 이후 산출물이 쌓여야 발현하므로 그동안 잠복해 있었다.
  - 수정 후 doctor WARN 이 4건 → 1건으로 줄어든다 (남는 1건은 `plugin_version` 업그레이드 감지로 정상 동작).

## 상태 전환

_(없음)_

## 비즈니스 규칙

- 오탐 제거가 **정상 탐지까지 침묵시키면 안 된다** — (A) 실제로 `conventions_doc` 을 선언했는데 파일이 없으면 계속 WARN, (B) spec 이 실제로 늘어난 drift 는 계속 감지되어야 한다.
- 플레이스홀더 판정 기준을 코드에 하드코딩한 한국어 문자열(`예:`)에만 의존하면 취약하다 — 판정 규칙을 명시적으로 설계할 것.
- (B) 는 `.plan.critic.md` 하드코딩 추가로 끝내지 말 것 — 파생 산출물 접미사가 또 늘면 같은 버그가 재발한다. **"spec 이 아닌 파생 산출물"의 판정을 한 곳에서** 정의할 것.
- 기존 doctor 테스트가 깨지지 않아야 한다 (`pilot/tests/tools/`). (B) 는 회귀 테스트 신규 추가 대상 — critic 산출물이 있는 features/ 픽스처로 카운트를 검증한다.

## 예외 케이스

- config.md 템플릿 자체가 플레이스홀더를 값 셀에 적도록 유도하고 있다면, 파서 수정과 **템플릿 표기 규약**을 함께 정해야 재발하지 않는다.
- `--fix` 자동 조치 대상으로 삼을지 여부는 미결 — 사용자 workspace 파일을 자동 편집하는 범위 확대라 신중해야 한다.
- `count_real_features` 의 다른 호출처(`integrity.py:517` analyzed 플래그 정합성 검사)도 같은 함수를 쓴다 — 수정이 그쪽 판정을 바꾸지 않는지 확인할 것. `analyzed=true` 인데 features 0 인 케이스 판정이 영향받는다.
- `.agent-state.yml` 의 기존 `last_analyzed_features` 값들은 **spec 기준으로 기록돼 있다** — 파서를 spec 기준으로 고치면 기존 값과 정합이 맞고, 반대로 고치면 전 프로젝트에서 drift 오탐이 난다.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [ ] (A) 플레이스홀더 판정 규칙 — (i) 값 셀이 백틱 코드 스팬 **단독**이 아니면 미선언 취급 (ii) 특정 접두사(`예:`·`e.g.`) 인식 (iii) config.md 템플릿에 미선언 표기(`—`)를 규약화하고 파서는 그것만 인정. 어느 쪽을 채택할 것인가
- [ ] (A) 본 수정을 `--fix` 자동 조치에 포함할 것인가, 진단(WARN 정확화)까지만 할 것인가
- [ ] (B) 파생 산출물 판정 방식 — (i) 접미사 블랙리스트(`.plan.md`·`.plan.critic.md`…) 확장 (ii) spec 파일명 화이트리스트 정규식(`^\d+-[a-z0-9-]+\.md$`) (iii) 파생 산출물을 별도 하위 디렉터리로 이동. (ii) 는 파서가 단순해지지만 명명 규약을 강제하게 된다
