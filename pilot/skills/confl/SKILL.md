---
name: confl
description: >-
  Confluence 기획서를 프로젝트 docs/ 폴더에 fetch 하거나 저장된 docs/ 를
  search·all·search+action 모드로 조회할 때 사용한다. 저장된 docs/ 를
  features/ 로 가공하는 작업은 `/pilot:analyze` 가 담당한다.
---

# /pilot:confl

Confluence 기획서를 프로젝트 docs/ 폴더에 저장하거나, 저장된 내용을 검색한다. docs/ 파일은 이 커맨드를 통해서만 접근한다 — 직접 Read 하지 않는다.

대상: $ARGUMENTS

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료. `${CLAUDE_PLUGIN_ROOT}` 를 `{PLUGIN}` 으로 사용한다.

## 모드 판별

`$ARGUMENTS` 를 순서대로 판별: `http(s)://` 시작 또는 순수 숫자(page_id) → **fetch** · `all` → **all** · `>` 구분자 포함 → **search+action**(`검색어 > 작업지시`) · `--local` 포함 → **search:local**(Rovo 우회, 로컬 grep 강제) · 그 외 → **search**(Rovo MCP 우선 → 로컬 폴백).

> **원문 보존 원칙**: 어떤 모드든 **fetch 만이 docs/ 를 작성**한다 — search 결과는 캐싱하지 않는다.
> **정책 이행 점검 모드 가드**: 기획서 vs 구현 비교가 목적이면 반드시 `--local` 또는 `all` 사용 (Rovo 응답은 요약·랭킹 개입으로 원문 인용 근거 부적합).

## Fetch 모드

Confluence 페이지를 가져와 `docs/` 에 저장한다. **내용은 컨텍스트에 로드하지 않는다.**

```bash
python3 {PLUGIN}/tools/confluence.py fetch "$ARGUMENTS"
```

실패 시 에러 원문 전달(환경변수 가이드 포함). 성공 시 **저장된 파일 경로와 섹션 제목 목록만** 출력(내용 미출력) + "`/pilot:confl {검색어}` 로 필요한 섹션을 검색하세요" 안내.

## Search 모드 (기본: Rovo MCP 우선 → 로컬 폴백)

1. `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql` 등록 여부 확인 — 없으면 곧장 로컬 폴백.
2. 등록돼 있으면 CQL 쿼리(`text ~ "{검색어}"`, 필요 시 space 필터) + cloudId(`getAccessibleAtlassianResources` 로 확인) + `limit: 5` 로 호출.
3. 결과 각 항목에 **`[source: rovo-mcp]`** 태그 + 제목·page_id·스니펫 출력. 마지막에 "원문 인용·정책 점검에는 `/pilot:confl {page_id}` 로 fetch 하세요" 안내. **자동 fetch 하지 않는다** (유도만).
4. **로컬 폴백** (MCP 미등록/호출 실패/결과 0건):

   ```bash
   python3 {PLUGIN}/tools/confluence.py search "{검색어}"
   ```

   결과 각 항목에 **`[source: local]`** 태그. 호출 실패로 인한 폴백이면 원인 + "강제 로컬만 사용하려면 `--local`" 안내 추가. 결과 없으면 [messages.md](../context/shared/messages.md) 의 `confl_no_match` 출력.

## Search:local 모드 (`--local`)

`--local` 제거 후 나머지를 검색어로 사용. **MCP 호출을 시도하지 않는다.**

```bash
python3 {PLUGIN}/tools/confluence.py search-local "{검색어}"
```

결과 각 항목에 **`[source: local]`** 태그. 결과 없으면 `confl_no_match` 출력. 용도: 정책 이행 점검(원문 인용 필수)·오프라인·재현성 확보.

## Search+Action 모드

`$ARGUMENTS` 를 `>` 기준으로 `{검색어} > {작업지시}` 분리. `{검색어}` 로 Search 모드(MCP 우선→로컬 폴백, `--local` 포함 시 Search:local)를 먼저 실행 → 결과 있으면 컨텍스트로 `{작업지시}` 수행(`rovo-mcp` 출처는 산출물에 직접 인용 금지 — 요약·참조만, 원문 필요 시 fetch 후 재실행 권유) → 결과 없으면 Search 안내 후 종료.

**`prompts/*.md` 의 `[analyze-managed]` 섹션은 편집 대상에서 제외한다** — `/pilot:analyze`·`/pilot:create-feature` 가 features 전체 기준으로 regen 하므로 여기서 추가한 항목은 다음 실행에서 소리 없이 유실된다. 도메인 지식을 남겨야 하면 `features/NN-*.md` 나 `project.md` 의 수동 편집 영역에 쓴다.

예: `/pilot:confl 배송상태 > project.md에 요구사항 정리`

## All 모드

저장된 모든 docs/ 파일 전체 내용을 출력한다.

```bash
python3 {PLUGIN}/tools/confluence.py all
```

실패 시 에러 원문 전달.
