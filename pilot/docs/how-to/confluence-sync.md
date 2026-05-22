# Confluence sync

!!! info "한 줄 요약"
    원격 Confluence 페이지를 `workspace/projects/{PROJECT}/docs/` 디렉터리로 fetch 하거나, 이미 가져온 docs/ 목록을 search, all, search+action 모드로 조회합니다. 가져온 docs/ 기획서를 feature로 변환하는 작업은 [`/pilot:analyze`](analyze-docs.md) 가 담당합니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- Atlassian MCP server (또는 동등한 연동 도구) 가 등록되어 있어야 합니다 (`getConfluencePage`, `searchConfluenceUsingCql` 등의 fetch 도구 필요).
- 동기화하려는 대상 페이지의 *page ID* 또는 *제목 검색 키워드* 를 알고 있어야 합니다.

## 작업 절차

### 1. 단건 fetch (page ID 기반)

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
/pilot:confl search "쿠폰 발급 정책"
```

CQL 검색을 수행하여 일치하는 페이지 목록을 조회하되, fetch를 직접 수행하지는 않습니다. 목록을 확인한 뒤 `search+action` 을 통해 일괄 fetch를 수행할 수 있습니다.

### 3. 검색 및 일괄 가져오기 (search+action)

```bash
/pilot:confl search+action "쿠폰 발급 정책"
```

검색 결과에 해당하는 모든 페이지를 한 번에 fetch합니다. 사용자 확인을 거친 뒤 실행하며, 대상 페이지 수가 많을 경우 API 호출 비용이나 불필요한 파일이 유입되지 않도록 유의합니다.

### 4. 동기화된 docs 목록 전체 확인 (all)

```bash
/pilot:confl all
```

현재 `docs/` 디렉터리에 로컬 저장된 문서 파일의 목록(파일명, 제목, fetch 일시 등)을 표 형태로 출력합니다.

### 5. feature 단위로 분할 가공

```bash
/pilot:analyze
```

가져온 문서를 기반으로 실제 작업을 진행하기 위한 feature 생성 단계로 넘어갑니다. 이후의 자세한 프로세스는 [기획서 기반 feature 일괄 생성](analyze-docs.md) 가이드를 확인하십시오.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:confl`](../reference/skills/confl.md)
- :material-tools: How-to: 가져온 기획서를 기능 단위로 나누려면 [기획서 기반 feature 일괄 생성](analyze-docs.md) 가이드를 참고하십시오.
- :material-lightbulb-on: Explanation: `docs/`를 원본 보존 영역으로 두고 `features/`를 실제 작업 단위로 분리하여 관리하는 정책의 상세 내용은 [컨텍스트 관리](../explanation/index.md)에서 확인할 수 있습니다.
