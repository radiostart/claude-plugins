# Confluence sync

!!! info "한 줄 요약"
    원격 Confluence 페이지를 `workspace/projects/{PROJECT}/docs/` 디렉터리로 fetch 하거나, 이미 가져온 docs/ 목록을 search, all, search+action 모드로 조회합니다. 가져온 docs/ 기획서를 feature로 변환하는 작업은 [`/pilot:analyze`](analyze-docs.md) 가 담당합니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- fetch 에는 `CONFLUENCE_EMAIL`·`CONFLUENCE_TOKEN` 환경변수가 필요합니다 (프로젝트 루트 `.env`·`workspace/.env` 또는 shell profile 의 `export`).
- 검색은 Atlassian Rovo MCP 가 등록돼 있으면 우선 사용하고, 미등록·호출 실패·결과 0건이면 로컬 `docs/` grep 으로 폴백합니다 — MCP 는 필수가 아닙니다.
- 동기화하려는 대상 페이지의 *URL 또는 page ID*, 혹은 *검색 키워드* 를 알고 있어야 합니다.

!!! info "인자로 모드를 판별합니다"
    `/pilot:confl` 에는 `search` 같은 리터럴 서브커맨드가 없습니다. `$ARGUMENTS` 를 순서대로 판별해 모드가 정해집니다 — `http(s)://` 시작 또는 순수 숫자 → **fetch** · `all` → **all** · `>` 포함 → **search+action** · `--local` 포함 → **search:local** · 그 외에는 **입력 텍스트 전체가 검색어**입니다.

## 작업 절차

### 1. 단건 fetch (URL 또는 page ID 기반)

```bash
/pilot:confl 1234567890
```

지정된 page ID에 해당하는 페이지를 fetch하여 다음 경로에 markdown 파일로 저장합니다:

```
workspace/projects/{PROJECT}/docs/1234567890_{slug}.md
```

(`slug` 파일명은 페이지 제목을 기반으로 자동 추출되어 명명됩니다)

### 2. 검색 모드 (search)

```bash
/pilot:confl 쿠폰 발급 정책
```

키워드만 넘기면 검색 모드입니다 (입력 전체가 검색어이므로 `search` 라는 앞머리 인자를 붙이지 않습니다). Rovo MCP 우선 → 로컬 폴백 순으로 조회해 제목·page_id·스니펫을 출처 태그(`[source: rovo-mcp]` / `[source: local]`)와 함께 출력하며, **fetch 를 자동으로 수행하지는 않습니다**. 원문 인용이 필요하면 안내에 따라 page_id 로 fetch 하십시오.

MCP 를 건너뛰고 로컬 `docs/` 만 검색하려면 `--local` 을 포함합니다:

```bash
/pilot:confl 쿠폰 발급 정책 --local
```

기획서와 구현을 대조하는 정책 이행 점검처럼 원문 인용이 필수인 경우에는 `--local` 또는 `all` 을 사용하십시오 — Rovo 응답은 요약·랭킹이 개입해 인용 근거로 부적합합니다.

### 3. 검색 결과 위에서 작업 수행 (search+action)

```bash
/pilot:confl 쿠폰 발급 정책 > project.md에 요구사항 정리
```

`>` 를 포함하면 `{검색어} > {작업지시}` 로 분리됩니다. 검색을 먼저 실행한 뒤 **그 결과를 컨텍스트로 삼아 뒤쪽 작업지시를 수행**하는 모드이며, 검색된 페이지를 일괄 fetch 하는 기능이 아닙니다 (`docs/` 에 파일을 쓰는 모드는 fetch 뿐입니다). 결과가 없으면 검색 안내만 출력하고 종료합니다. `rovo-mcp` 출처는 산출물에 직접 인용하지 않고 요약·참조만 하며, 원문이 필요하면 fetch 후 재실행합니다.

### 4. 저장된 docs 전체 확인 (all)

```bash
/pilot:confl all
```

현재 `docs/` 디렉터리에 저장된 모든 문서 파일의 **전체 내용**을 출력합니다.

### 5. feature 단위로 분할 가공

```bash
/pilot:analyze
```

가져온 문서를 기반으로 실제 작업을 진행하기 위한 feature 생성 단계로 넘어갑니다. 이후의 자세한 프로세스는 [기획서 기반 feature 일괄 생성](analyze-docs.md) 가이드를 확인하십시오.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:confl`](../reference/skills/confl.md)
- :material-tools: How-to: 가져온 기획서를 기능 단위로 나누려면 [기획서 기반 feature 일괄 생성](analyze-docs.md) 가이드를 참고하십시오.
- :material-lightbulb-on: Explanation: `docs/`를 원본 보존 영역으로 두고 `features/`를 실제 작업 단위로 분리하여 관리하는 정책의 상세 내용은 [컨텍스트 관리](../explanation/index.md)에서 확인할 수 있습니다.
