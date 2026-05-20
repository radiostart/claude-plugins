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

### 2. wizard 적용 (created 인 경우만)

`config.md` 상태가 `created` 인 경우에만 진입. `exists` 이면 이 단계를 skip.

사용자 입력에 `--no-wizard` 토큰이 포함되어 있으면 이 단계를 skip (Q6 자연어 분기).

wizard 가 활성화되면 아래 3 단계를 순서대로 실행한다. **어느 단계가 실패해도 abort 금지 — 다른 단계는 계속 진행 (A2 fallback 정책).**

> **표 헤더 고정 스키마 (doctor strict 검증 대상)** — wizard 가 만들거나 갱신하는 표는 아래 헤더를 **정확히** 사용해야 한다. 한 글자라도 다르면 doctor 가 ERROR 로 차단한다.
>
> - `## learn 언어 패턴` 표 1 (의존성 추적): `| 언어 | 의존성 추출 패턴 |`
> - `## learn 언어 패턴` 표 2 (역할 분류): `| 역할 | 식별 패턴 |`
> - `## scope 카테고리`: `| scope 헤더 | project.md 대상 H3 | 표 헤더 |` (정확히 3 컬럼). `scope 헤더` 컬럼 값은 반드시 `## ` 로 시작.
> - `## Ignore`: `| 패턴 | 사유 |`

1. **언어 감지** — `${CLAUDE_PLUGIN_ROOT}/tools/init_detect.py` 의 `detect_languages(cwd_path)` 를 호출 (`cwd_path` 는 `pathlib.Path` 객체). 주 언어 목록을 추출한다.
   - 반환된 언어 목록을 `workspace/context/config.md` 의 `## learn 언어 패턴` 두 표 본문에 주입:
     - 표 1 (의존성 추적): `| {언어} | {의존성 추출 패턴} |` 형식. 언어별 default 패턴 (ruby: `require_relative`·`include`·`extend`·`Module::Class` / typescript: `import.*from`·`require\(` / python: `^from\|^import` / kotlin: `import\s`·`package\s` / go: `^import\s`).
     - 표 2 (역할 분류): `| {역할} | {식별 패턴} |` 형식. 일반적 5 역할 (controllers·services·models·workers·jobs) + 언어별 파일 glob 패턴.
   - 기존 행이 있으면 dedupe 병합 (사용자 수동 추가 보존).
   - 감지 0건 → 두 표는 헤더만 남기고 빈 행 + INFO 1줄.
2. **scope 후보 감지** — `detect_scope_candidates(cwd_path)` 를 호출. 폴더명 → scope 카테고리 매핑을 추출한다.
   - 반환된 매핑을 `workspace/context/config.md` 의 `## scope 카테고리` 표 본문에 주입. **3 컬럼 강제**:
     - `scope 헤더`: 폴더가 mapping 한 H2 헤더 — 반드시 `## ` 로 시작 (예: `## Routes`·`## Models`·`## Services`).
     - `project.md 대상 H3`: project.md `## 관련 파일` 안에 생성될 H3 이름 (예: `Endpoints`·`Models`·`Services`).
     - `표 헤더`: 해당 표의 컬럼 헤더 (쉼표 구분, 예: `엔드포인트, Method, 목적`).
   - 같은 `project.md 대상 H3` 가 여러 폴더에서 매핑되면 (예: services·workers·jobs → Services) 1 행만 남기고 dedupe.
   - 기존 행이 있으면 dedupe 병합.
   - 후보 0건 → default 3 행 (Routes·Models·Services) 그대로 주입 + INFO 1줄.
3. **Ignore baseline 주입** — `IGNORE_BASELINE` 상수의 10 패턴을 `workspace/context/config.md` 의 `## Ignore` 표 본문에 주입한다. 헤더: `| 패턴 | 사유 |`.
   - 기존 행이 있으면 dedupe 병합 (사용자 수동 추가 보존).

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

wizard 결과:
  언어 감지: {N}개 자동 주입 ({언어목록})
  scope 후보: {M}개 매핑 ({폴더목록})
  Ignore baseline: {P}개 추가

▶ 다음 단계 (필수):
  /pilot:project {프로젝트명}        # 바로 시작 가능

▶ 채우면 좋은 것 (점진적, 미작성 시 fallback 동작):
  - context/MANIFEST.md                 # 첫 도메인 작업 시 도메인 지식 (자유 구조)
  - context/config.md                   # Ignore 패턴 · 언어·도구 기본값 · commit_scopes
  - context/{rules,scope}/{도메인}.md   # 도메인 파일은 첫 추가 시 폴더 함께 생성

> 모든 파일은 비워둬도 동작합니다. 코드 작업 중 필요해지는 순간에 채우세요.
```

wizard skip 시 위 "wizard 결과" 블록 대신:

```
  wizard skipped (config.md exists 또는 --no-wizard)
```

---

## 참고

- 이 스킬은 **워크스페이스를 처음 만들 때만** 사용한다. 프로젝트를 추가하려면 `/pilot:project`.
- 생성되는 모든 파일은 사용자가 직접 채워야 하는 스켈레톤이다 (도메인·공통 모델·Ignore 등).
- 생성 후 스켈레톤을 실제 값으로 채우는 작업은 이 스킬 범위 밖. 사용자가 문서를 편집한다.
- 각 스켈레톤 상단에 "이 파일은 `/pilot:init` 가 생성했다" 주석이 있어, 어디서 왔는지 역추적 가능.
- 사용자 입력에 `--no-wizard` 토큰이 포함되어 있으면 wizard 단계를 건너뛴다. v0.2.x 이전 동작과 동일하게 빈 스켈레톤만 생성된다.
