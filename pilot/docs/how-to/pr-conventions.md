# PR 컨벤션 설정

!!! info "한 줄 요약"
    `/pilot:pr` 의 PR 본문은 플러그인 내장 컨벤션을 따른다. 팀 규칙이 다르면 `workspace/context/pr.md` 를 만들어 *완전 대체* 한다.

## 동작 방식

`/pilot:pr` 가 PR 본문을 작성할 때 따르는 컨벤션의 fallback 순서:

1. `workspace/context/pr.md` — 워크스페이스 override (있으면 이것만)
2. 플러그인 내장 default (`skills/context/shared/pr.md`)

`workspace/context/pr.md` 가 있으면 플러그인 default 를 **완전히 대체** 한다 (부분 병합 아님). 없으면 플러그인 default 가 메모리에서 자동 적용된다 — 별도 파일 생성은 불필요.

!!! note "산문 vs 키-값"
    `pr.md` 는 *산문 컨벤션* (라벨·본문 구조·머지 정책) 만 담는다. base branch 같은 *키-값 설정* 은 `config.md` 의 `pr_default_base` 로 분리돼 있다 ([워크스페이스 설정](workspace-config.md)).

## 전제

- `/pilot:init` 으로 `workspace/context/` 가 있다.

## 절차

### 1. 기본 컨벤션으로 충분한지 본다

플러그인 default 가 이미 다루는 것 — 변경 유형 라벨(`feat`·`fix`·`refactor`…), PR 본문 구조(Summary / Why / Test plan / Notes), stacked PR, 커밋 단위, 머지·force-push 정책, 금지 사항. 팀 규칙이 이와 같다면 **아무것도 안 해도 된다.**

### 2. 다르면 `pr.md` 를 만든다

플러그인 default 를 출발점으로 복사해 편집하는 것이 빠르다:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/context/shared/pr.md" workspace/context/pr.md
```

그다음 팀 규칙에 맞게 고친다 — 예: PR 본문 섹션 구성 변경, 라벨 집합 교체, 머지 정책(squash vs merge) 조정.

!!! warning "완전 대체"
    `workspace/context/pr.md` 는 default 를 *통째로* 대신한다. default 의 어떤 항목을 남기고 싶으면 그 부분도 `pr.md` 안에 있어야 한다 — 그래서 *복사 후 편집* 이 권장된다.

### 3. 확인

`/pilot:pr` 로 PR 을 만들면 본문이 `pr.md` 컨벤션을 따른다. 레포에 `.github/PULL_REQUEST_TEMPLATE` 가 있으면 그것이 우선 적용된다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:pr`](../reference/skills/pr.md) · [`/pilot:commit`](../reference/skills/commit.md) — 커밋 메시지 컨벤션 (`commit_scopes`).
- :material-file-cog: How-to: [워크스페이스 설정 (config.md)](workspace-config.md) — `pr_default_base` (base 브랜치 default).
