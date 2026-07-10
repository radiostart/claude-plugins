# Pull Request 컨벤션 (플러그인 default)

pilot 플러그인이 제공하는 **표준 PR 컨벤션 fallback**. 워크스페이스가 별도 override 를 두지 않으면 이 문서가 적용된다.

> **위치 정책**
>
> - 본 문서 (`skills/context/shared/pr.md`) = 플러그인 내장 default. 모든 워크스페이스 공통.
> - 워크스페이스 override = `workspace/context/pr.md`. 존재 시 본 문서를 **완전 대체**.
> - 키-값 설정 (base branch default 등) = `workspace/context/config.md` 표. 산문 규칙과 분리.
>
> **fallback 순서:** `workspace/context/pr.md` (워크스페이스 override) → 본 문서 (플러그인 default). PR 스킬은 `workspace/context/pr.md` 가 없으면 본 문서를 자동 적용 (별도 생성 없이 메모리 내 fallback).

---

## 1. Base branch 정책

base branch 결정(결정 트리·remote 검증·stale 감지)은 `/pilot:pr` 스킬의 동작이다 — 메커니즘 SSOT: `skills/pr/SKILL.md`.
키 스키마는 [`lifecycle/state-schema.md`](../lifecycle/state-schema.md), default 는 `workspace/context/config.md` 의 `pr_default_base`.

---

## 2. 라벨 / 제목

본문 또는 제목 prefix 에 변경 유형 라벨 표기:

| label | 의미 |
|---|---|
| `feat` | 사용자 관찰 가능한 기능 추가 |
| `fix` | 버그 수정 |
| `test` | 테스트 추가·수정만 |
| `doc` | 문서/주석 변경 |
| `ci` | CI·빌드·배포 스크립트 |
| `refactor` | 동작 보존 리팩터 |
| `style` | 포맷·들여쓰기·네이밍 |
| `perf` | 성능 개선 |

PR 제목은 자유 형식. 이슈 트래커 티켓이 있으면 `[TICKET-XXX]` 접두 권장. 본문 한국어 기본.

---

## 3. PR 본문 권장 구조

레포지터리 템플릿이 있으면 (`.github/PULL_REQUEST_TEMPLATE`) 그것을 우선 사용. 없으면 아래 default:

```markdown
## Summary
<1-3 줄: 무엇을 변경했는지>

## Why
<왜 변경했는지: 트리거·맥락·티켓 링크>

## Test plan
- [ ] <검증 항목>

## Notes
<공유할 트레이드오프·후속 작업 (선택)>
```

---

## 4. Stacked PR

긴 흐름은 base 를 default 가 아닌 **선행 PR 의 head 브랜치** 로 잡는다.

```
develop
  └── feature/foo (PR #1, base: develop)
        └── feature/foo-followup (PR #2, base: feature/foo)
```

- PR 본문에 **base 와 의존 PR 번호** 명시.
- 선행 PR 머지 시 GitHub 가 자동으로 base 재설정.
- 후속 PR 은 선행 머지 전엔 머지 불가.

---

## 5. 커밋 단위

- **하나의 PR = 하나의 의도.** 의도가 다른 변경은 PR 분리.
- 가능하면 리뷰 단위로 커밋 분리. squash 머지 환경이면 강제 X.
- 5 커밋 이상 + 도메인 혼합이면 분리 검토.

---

## 6. 머지·Force push

- **squash 머지 기본.** stacked PR 의 중간 PR 만 일반 merge 로 base 보존.
- base 브랜치 (`develop`/공유 브랜치) **force push 금지.**
- 본인 feature 브랜치 force push 는 허용. 리뷰 시작 후 force push 는 **rebase 사유를 코멘트로 명시.**
- 머지 후 origin 브랜치 자동 삭제 권장.

---

## 7. 금지 사항

- `--no-verify` / 훅 우회 금지. 실패하면 원인 수정.
- 자동 생성 파일 (`Gemfile.lock`, `yarn.lock`, lockfile 류) 의도치 않은 변경 포함 금지.
- secrets (`.env`, credentials) 절대 커밋 금지 — `.gitignore` 사전 확인.

---

## 참조

- 커밋 메시지 컨벤션: [`shared/commit.md`](commit.md)
- state 스키마 (`pr_base_branch` 위치): [`lifecycle/state-schema.md`](../lifecycle/state-schema.md)
- 워크스페이스 override: `workspace/context/pr.md`
- default base 키: `pr_default_base` (`workspace/context/config.md`, fallback `develop`)
