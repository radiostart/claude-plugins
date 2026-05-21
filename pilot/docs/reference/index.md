# Reference

에이전트·스킬·CLI·설정 키의 *정확한 값*. 사용자 facing 메타데이터는 `skills/`·`agents/`·`tools/` 의 SSOT 에서 자동 추출됩니다 (drift 방지).

!!! note "작성 중"
    자동 추출 스크립트 (`pilot/tools/docs_build.py`) 는 매뉴얼 plan 의 §4 로 정의됐고 다음 단계에서 구현됩니다. 본 사이트 step 1 에서는 reference/ 가 비어 있습니다.

## 카테고리 (구현 예정)

- **agents/** — `pilot-planner`, `pilot-planner-critic`, `pilot-generator`, `pilot-evaluator`, `pilot-code-review`
- **skills/** — `/pilot:*` 13 종 (analyze, characterize, commit, confl, create-feature, doctor, focus, init, issue, learn, pr, project, review, slack, tdd 등)
- **tools/** — `orchestrate-load.py`, `plan-validate.py`, `doctor`, `init_detect.py` 등의 CLI 인터페이스
- **config 키** — `language`, `test_command`, `source_root` 등 14 개
- **state schema** — `.agent-state.yml` 필드와 버전
- **plan schema** — `features/NN-{slug}.plan.md` 의 모드별 계약
- **identity / personas** — `archetype`·`voice`·`phrasing`·`forbid` 의 SSOT
- **Hooks & Tools** — Claude Code hook 통합 지점
- **지원 환경** — OS·Claude Code 버전·언어
