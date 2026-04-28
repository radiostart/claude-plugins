# 초기 세팅 가이드

플러그인을 처음 사용할 때 `workspace/` 구조를 초기화한다.

## 1. 워크스페이스 초기화 (권장)

```bash
/pilot:init
```

실행하면 아래가 일괄 생성된다 (idempotent — 이미 있는 파일은 skip):

```
workspace/
├── STATE.md                     # 작업 상태
└── context/
    ├── MANIFEST.md              # 도메인 지식 (스켈레톤)
    └── config.md                # 런타임 설정 (Ignore · 언어·도구 · commit_scopes)
```

카테고리 하위 폴더 (`rules/`·`scope/`·`enums/` 등) 는 **생성하지 않는다**. MANIFEST 를 채우면서 실제 도메인 파일을 추가할 때 폴더를 함께 만든다.

생성 후:

1. **즉시 시작 가능** — `/pilot:project {프로젝트명}` 으로 바로 첫 프로젝트 시작 (모든 파일 비워둬도 fallback 으로 동작).
2. **점진적으로 채우기** — 코드 작업 중 필요해지는 순간:
   - `context/MANIFEST.md` — 도메인 지식 (구조 자유, 강제 X)
   - `context/config.md` — `## Ignore` · 언어·도구 기본값 · commit_scopes (파서가 읽는 고정 스키마)
   - `context/{rules,scope}/{도메인}.md` — 첫 도메인 파일 추가 시 폴더 함께 생성

## 2. 수동 초기화 (대체)

`/pilot:init` 을 쓰지 않을 경우 수동 생성:

```bash
mkdir -p workspace/context
```

템플릿은 `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/` 에서 복사. 단, 가능하면 `/pilot:init` 을 사용하는 게 누락 방지에 안전.

## 3. `.env` — Confluence 환경변수 (선택)

`/pilot:confl`을 사용하려면 `CONFLUENCE_EMAIL` / `CONFLUENCE_TOKEN` 이 필요하다. 프로젝트 루트 `.env` 또는 `workspace/.env` 파일에 기록하면 shell 종류와 무관하게 `confluence.py`가 자동으로 로드한다.

```bash
cat > .env <<'EOF'
CONFLUENCE_EMAIL=user@example.com
CONFLUENCE_TOKEN=your-api-token
EOF

# 커밋에 포함되지 않도록 .gitignore 에 추가
grep -q '^\.env$' .gitignore 2>/dev/null || echo ".env" >> .gitignore
```

토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

shell profile(`~/.zshrc`, `~/.bashrc` 등)에 `export`한 값이 있으면 그 값이 우선한다.

## 디렉토리 구조 (예시 — 세팅 + 첫 프로젝트 + 도메인 추가 후)

```
workspace/
├── STATE.md                      # 작업 상태 (init)
├── context/                      # 자유 구성
│   ├── MANIFEST.md               # (init 이 스켈레톤 생성)
│   ├── config.md                 # (init 이 스켈레톤 생성)
│   ├── rules/{domain}.md         # (도메인 추가 시 작성)
│   ├── scope/{domain}.md         # (도메인 추가 시 작성)
│   └── enums/...                 # (필요 시 구성 — INDEX 여부·구조 모두 사용자 선택)
├── projects/                     # /pilot:project 로 생성
│   └── {PROJECT}/
│       ├── project.md
│       ├── .agent-state.yml      # machine-readable 상태 파일
│       ├── agents/
│       └── features/
└── issues/                       # /pilot:issue 로 생성
```

`context/` 하위 구조는 MANIFEST 에서 선언한 형태를 따른다. 위는 한 가지 컨벤션 예시일 뿐 강제 아님.
