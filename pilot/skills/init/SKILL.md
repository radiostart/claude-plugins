---
name: init
description: >-
  새 워크스페이스 셋업 — `workspace/` 구조를 초기화한다.
  `workspace/STATE.md` 와 `workspace/context/` 하위의 `MANIFEST.md`·`config.md`
  스켈레톤을 일괄 생성한다. 처음 pilot 을 도입·셋업할 때 사용한다.
---

# /pilot:init

워크스페이스 구조를 일괄 생성한다.

---

## 사전 확인

1. workspace 경로 결정 — CWD 기준 `./workspace/`.
   - 폴더 없으면 생성 (`mkdir -p workspace/context`).

---

## 동작

### 1. 스켈레톤 생성

아래 각 파일에 대해 **대상 존재 시 skip, 없으면 템플릿으로 생성** (idempotent):

| 템플릿 | 대상 경로 |
| ------ | --------- |
| `templates/STATE.md.template` | `workspace/STATE.md` |
| `templates/MANIFEST.md.template` | `workspace/context/MANIFEST.md` |
| `templates/config.md.template` | `workspace/context/config.md` |

템플릿 위치: `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/`

> `MANIFEST.md.template` 에는 `## 외부 도메인 reference` 섹션 placeholder 주석이 포함되어 있다. 실제 섹션은 `/pilot:learn` 이 cross-domain reference 를 처음 발견할 때 자동으로 작성한다.

절차:

1. `workspace/context/` 폴더를 필요 시 생성.
2. 각 템플릿을 Read.
3. 대상 경로가 이미 존재하면 skip (마크 `exists`), 없으면 Write (마크 `created`).

> **`rules/`·`scope/`·`enums/` 등 카테고리 폴더는 생성하지 않는다.** 카테고리 구조는 사용자가 MANIFEST.md 를 채우면서 결정하고, 실제 도메인 파일을 추가할 때 필요한 폴더를 만든다. 플러그인은 MANIFEST 선언만 따른다.

---

## 결과 출력

아래 형식으로 요약:

```
워크스페이스 초기화 완료
Workspace: {workspace 절대 경로}

파일 상태:
  workspace/STATE.md                    {created|exists}
  workspace/context/MANIFEST.md         {created|exists}
  workspace/context/config.md           {created|exists}

▶ 다음 단계 (필수):
  /pilot:project {프로젝트명}        # 바로 시작 가능

▶ 채우면 좋은 것 (점진적, 미작성 시 fallback 동작):
  - context/MANIFEST.md                 # 첫 도메인 작업 시 도메인 지식 (자유 구조)
  - context/config.md                   # Ignore 패턴 · 언어·도구 기본값 · commit_scopes
  - context/{rules,scope}/{도메인}.md   # 도메인 파일은 첫 추가 시 폴더 함께 생성

> 모든 파일은 비워둬도 동작합니다. 코드 작업 중 필요해지는 순간에 채우세요.
```

---

## 참고

- 이 스킬은 **워크스페이스를 처음 만들 때만** 사용한다. 프로젝트를 추가하려면 `/pilot:project`.
- 생성되는 모든 파일은 사용자가 직접 채워야 하는 스켈레톤이다 (도메인·공통 모델·Ignore 등).
- 생성 후 스켈레톤을 실제 값으로 채우는 작업은 이 스킬 범위 밖. 사용자가 문서를 편집한다.
- 각 스켈레톤 상단에 "이 파일은 `/pilot:init` 가 생성했다" 주석이 있어, 어디서 왔는지 역추적 가능.
