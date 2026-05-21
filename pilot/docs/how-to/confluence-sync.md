# Confluence 동기화

!!! info "한 줄 요약"
    원격 Confluence 페이지를 `workspace/projects/{PROJECT}/docs/` 로 fetch 하거나, 이미 가져온 docs/ 를 search·all·search+action 모드로 조회. 가져온 docs/ 를 feature 로 가공하는 작업은 [`/pilot:analyze`](analyze-docs.md) 가 담당.

## 전제

- 활성 프로젝트가 있다.
- Atlassian MCP 서버 (또는 동등한 도구) 가 Claude Code 에 등록돼 있다 — `getConfluencePage`·`searchConfluenceUsingCql` 같은 fetch 도구가 사용 가능해야 한다.
- 동기화 대상 페이지의 *page ID* 또는 *제목 검색 키워드* 를 안다.

## 절차

### 1. 단건 fetch (page ID)

```bash
/pilot:confl 1234567890
```

해당 page ID 를 fetch 해서:

```
workspace/projects/{PROJECT}/docs/1234567890_{slug}.md
```

으로 저장. slug 는 페이지 제목에서 자동 추출.

### 2. 검색 모드

```bash
/pilot:confl search "쿠폰 발급 정책"
```

CQL 검색을 돌려 매치된 페이지 목록만 보고 — fetch 는 하지 않는다. 결과 보고 `search+action` 으로 일괄 가져오기.

### 3. 검색 + 일괄 가져오기

```bash
/pilot:confl search+action "쿠폰 발급 정책"
```

검색 결과의 모든 페이지를 한 번에 fetch. 사용자 확인 후 진행 — 페이지 수가 많으면 비용·노이즈 주의.

### 4. 가져온 docs 전체 보기

```bash
/pilot:confl all
```

현재 `docs/` 폴더 상태를 표 형식으로 표시 (파일명·제목·fetch 일시).

### 5. features 로 가공

```bash
/pilot:analyze
```

이후 흐름은 [기획서로 features 일괄 생성](analyze-docs.md) 참조.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:confl`](../reference/skills/confl.md)
- :material-tools: How-to: 가져온 docs 를 다음 단계로 — [기획서로 features 일괄 생성](analyze-docs.md).
- :material-lightbulb-on: Explanation: docs/ 가 *원본 보관소* 이고 features/ 가 *작업 단위* 라는 분리 원칙은 [컨텍스트 관리](../explanation/index.md) 에서.
