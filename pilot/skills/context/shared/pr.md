# Pull Request 컨벤션 (플러그인 default)

pilot 플러그인이 제공하는 **표준 PR 컨벤션 fallback**. 팀이 별도 override 를 두지 않으면 이 문서가 적용된다.

> **위치 정책**
>
> - 본 문서 (`skills/context/shared/pr.md`) = 플러그인 내장 default. 모든 워크스페이스 공통.
> - 워크스페이스 override = `workspace/context/pr.md`. 존재 시 본 문서를 **완전 대체**. PR 템플릿은 **레포지터리 단위** 산출물 (`.github/PULL_REQUEST_TEMPLATE`) 이므로 같은 레포 = 같은 워크스페이스를 공유하는 모든 팀이 동일한 PR 컨벤션을 따른다. → 팀별 분기 없이 워크스페이스 공통에 둔다.
> - 키-값 설정 (base branch default 등) = `workspace/context/config.md` 표. 산문 규칙과 분리.
>
> **fallback 순서:** `workspace/context/pr.md` (워크스페이스 override) → 본 문서 (플러그인 default). PR 스킬은 `workspace/context/pr.md` 가 없으면 본 문서를 자동 적용 (별도 생성 없이 메모리 내 fallback).

---

## 1. Base branch 정책 (자동 타겟팅)

PR 생성 시 base branch 결정 흐름:

```
/pilot:pr 진입
├─ .agent-state.yml 의 pr_base_branch 존재
│   └─ "타겟: <X> (저장됨). Enter=유지 / 입력=변경"
│       ├─ Enter      → X 사용. state 갱신 없음
│       └─ 새 입력    → state 갱신 + 새 값 사용
└─ 부재
    └─ "타겟 브랜치? (Enter=<default>)"
        ├─ Enter      → config 의 pr_default_base 사용. state 미저장
        └─ 입력       → state 에 pr_base_branch 기록 + 입력값 사용
```

### 관련 키

| 위치 | 키 | 용도 |
|---|---|---|
| `.agent-state.yml` | `pr_base_branch` (optional) | 사용자가 명시 입력한 base. 부재 시 default 사용 |
| `workspace/context/config.md` | `pr_default_base` (optional) | 팀별 default base. `workspace/context/config.md` 보다 우선 |
| `workspace/context/config.md` | `pr_default_base` | 전사 default base (예: `develop`, `main`). 미선언 시 하드 fallback `develop` |

### 사전 검증

PR 생성 직전 `git ls-remote --exit-code origin <base>` 로 remote 존재 확인. 없으면 WARN + 재질의.

### Stale 감지 (doctor)

`/pilot:doctor` 가 `pr_base_branch` 가 가리키는 브랜치의 remote 존재를 확인하여 사라졌으면 WARN.

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

팀별 템플릿이 있으면 (`.github/PULL_REQUEST_TEMPLATE`) 그것을 우선 사용. 없으면 아래 default:

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
- AI 리뷰 자동화: `/pilot:ai-review`
- state 스키마 (`pr_base_branch` 위치): [`lifecycle/state-schema.md`](../lifecycle/state-schema.md)
- 워크스페이스 override: `workspace/context/pr.md`
- default base 키: `pr_default_base` (`config.md` 우선, fallback `workspace/context/config.md`)
