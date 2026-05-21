# Reference

에이전트·스킬·CLI·페르소나의 *정확한 값*. 본 섹션은 `pilot/agents/`·`pilot/skills/`·`pilot/tools/`·`pilot/skills/context/shared/identity.yml` 의 SSOT 에서 자동 추출됩니다 (`pilot/tools/docs_build.py`). drift 가 의심되면 `python3 pilot/tools/docs_build.py --check` 가 검증합니다.

## 카테고리

<div class="grid cards" markdown>

-   :material-account-cog:{ .lg .middle } __[Agents](agents/index.md)__

    ---

    `@pilot-planner` · `@pilot-planner-critic` · `@pilot-generator` · `@pilot-evaluator` · `@pilot-code-review` 의 호출 절차·책임 경계·금지 사항.

-   :material-slash-forward-box:{ .lg .middle } __[Skills](skills/index.md)__

    ---

    `/pilot:*` 슬래시 커맨드 — `init`, `project`, `analyze`, `create-feature`, `focus`, `tdd`, `characterize`, `doctor`, `confl`, `slack`, `commit`, `pr`, `review`, `learn`, `issue`, `code-review-init`, `fix-review`.

-   :material-console:{ .lg .middle } __[Tools](tools/index.md)__

    ---

    `pilot/tools/*.py` 의 보조 CLI · 모듈 — `orchestrate-load`, `plan-validate`, `doctor`, `docs_build`, `init_detect`, `slack-notify`, `confluence`, `handoff-quality`, `regen-verify`, `verify-report-lint`, `memory-hint`.

-   :material-fingerprint:{ .lg .middle } __[Identity SSOT](identity.md)__

    ---

    `identity.yml` 의 에이전트 계약(`output`·`min_evidence`) 과 페르소나(`archetype`·`voice`·`phrasing`·`forbid`).

</div>

## SSOT 와 drift 검증

이 페이지들은 *생성된 산출물* 입니다. 수정하려면 원본 (`agents/*.md`·`skills/*/SKILL.md`·`tools/*.py`·`identity.yml`) 을 손대고 `docs_build.py` 를 재실행합니다. 사이트 commit 정책은 [`pilot/.gitignore`](https://github.com/radiostart/claude-plugins/blob/main/pilot/.gitignore) 참조 — generated 파일은 commit 대상이 아니며 CI 빌드 단계에서 매번 새로 만듭니다.

!!! note "범위 밖"
    `pilot/skills/context/lifecycle/{plan-schema,state-schema,drift-protocol}.md` 와 같은 메타 스키마 문서는 Reference 가 아닌 [Explanation](../explanation/index.md) 에서 다룹니다 — 정확한 값보다 *원리·이유* 에 가깝기 때문입니다.
