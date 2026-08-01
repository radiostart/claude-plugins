# PR 컨벤션 설정

!!! info "한 줄 요약"
    `/pilot:pr` 명령 실행 시 생성되는 PR 본문 템플릿 및 규칙은 플러그인 내장 컨벤션을 기본으로 따릅니다. 팀 고유의 PR 규칙을 적용하려면 `workspace/context/pr.md` 파일을 생성하여 컨벤션을 **완전 대체**할 수 있습니다.

## 동작 방식

`/pilot:pr` 명령이 PR 본문을 작성할 때 참고하는 컨벤션의 fallback 순서는 다음과 같습니다:

1. `workspace/context/pr.md` — 워크스페이스 내 override 설정 (존재 시 최우선 적용)
2. 플러그인 내장 default 설정 (`skills/context/shared/pr.md`)

`workspace/context/pr.md` 파일이 존재할 경우 플러그인의 default 설정을 **완전히 대체**합니다 (부분 병합 처리가 아닌 통째로 대체). 파일이 없을 경우 내장 default 설정이 인메모리 상에서 자동 적용되므로 별도로 파일을 생성하지 않아도 무방합니다.

!!! note "컨벤션 텍스트와 키-값 설정의 분리"
    `pr.md` 에는 라벨 정의, PR 본문 구조, 머지(merge) 정책 등 *글 형식의 컨벤션*만 정의합니다. base branch 설정과 같은 *키-값 형태의 설정*은 `config.md` 의 `pr_default_base` 항목으로 관리합니다 ([워크스페이스 설정](workspace-config.md) 참고).

## 전제 조건

- `/pilot:pilot-init` 을 실행하여 `workspace/context/` 디렉터리가 생성되어 있어야 합니다.

## 작업 절차

### 1. 기본 컨벤션 적합 여부 판단

플러그인 default 컨벤션은 변경 유형 라벨(`feat`, `fix`, `refactor` 등), PR 본문 구조(Summary / Why / Test plan / Notes), stacked PR 관리, 커밋 단위 설정, 머지 및 force-push 정책, 금지 행동 지침 등을 기본적으로 내장하고 있습니다. 팀의 규칙과 부합한다면 **별도 설정을 진행하지 않고 넘어가도 좋습니다.**

### 2. 커스텀 pr.md 생성 및 편집

팀의 규칙이 다른 경우, 플러그인의 내장 default 파일을 복사하여 수정하는 방식이 가장 편리합니다:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/context/shared/pr.md" workspace/context/pr.md
```

복사한 파일 내용을 팀 규칙에 맞춰 수정합니다 (예: PR 본문의 상세 섹션 구성 수정, 지원 라벨 목록 변경, 머지 방식(squash vs merge) 조정 등).

!!! warning "완전 대체 동작 방식"
    `workspace/context/pr.md` 는 내장 default 설정을 *통째로* 덮어씁니다. 따라서 기존 default 내용 중 그대로 유지하고 싶은 항목이 있다면 해당 내용도 반드시 새 `pr.md` 파일 내에 작성되어 있어야 합니다 (따라서 *복사 후 편집*을 적극 권장합니다).

### 3. PR 생성 및 적용 확인

`/pilot:pr` 명령으로 PR 을 생성하면 수정한 `pr.md` 컨벤션에 맞춰 본문이 생성됩니다. 단, 레포지토리에 `.github/PULL_REQUEST_TEMPLATE` 파일이 이미 정의되어 있는 경우 해당 템플릿 양식이 우선적으로 적용됩니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:pr`](../reference/skills/pr.md) · [`/pilot:commit`](../reference/skills/commit.md) — 커밋 메시지 범위 설정을 다루는 `commit_scopes` 안내.
- :material-file-cog: How-to: [워크스페이스 설정](workspace-config.md) — 대상 브랜치의 default 값을 변경하는 `pr_default_base` 설정 가이드.
