---
name: confl
description: >-
  Confluence 기획서를 프로젝트 docs/ 폴더에 fetch 하거나 저장된 docs/ 를
  search·all·search+action 모드로 조회할 때 사용한다. 저장된 docs/ 를
  features/ 로 가공하는 작업은 `/pilot:analyze` 가 담당한다.
---

# /pilot:confl

Confluence 기획서를 프로젝트 docs/ 폴더에 저장하거나, 저장된 내용을 검색한다.
docs/ 파일은 이 커맨드를 통해서만 접근한다. 직접 Read하지 않는다.

대상: $ARGUMENTS

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. (`{PROJECT}` 획득)
실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` 또는 `no_active_project` 출력 후 종료.

`${CLAUDE_PLUGIN_ROOT}` 를 `{PLUGIN}` 으로 사용한다.

---

## 모드 판별

`$ARGUMENTS`를 아래 순서로 판별한다:

| 패턴                                                        | 모드                                             |
| ----------------------------------------------------------- | ------------------------------------------------ |
| `http://` 또는 `https://` 로 시작하거나, 순수 숫자(page_id) | **fetch 모드**                                   |
| `all`                                                       | **all 모드**                                     |
| `>` 구분자를 포함                                           | **search+action 모드** (예: `검색어 > 작업지시`) |
| `--local` 플래그를 포함                                     | **search:local 모드** (Rovo MCP 우회, 로컬 grep 강제) |
| 그 외 텍스트                                                | **search 모드** (Rovo MCP 우선 → 로컬 폴백)      |

> **원문 보존 원칙**: 어떤 모드든 **fetch 만이 docs/ 파일을 작성**한다. Search 결과는 docs/ 에 캐싱하지 않는다.
> **정책 이행 점검 모드 가드**: 기획서 vs 구현 비교가 목적이라면 반드시 `--local` 또는 `all` 을 사용한다 (Rovo 응답은 요약·랭킹이 개입하여 원문 인용 근거로 부적합).

---

## Fetch 모드

Confluence 페이지를 가져와 `docs/` 폴더에 저장한다. 내용은 컨텍스트에 로드하지 않는다.

수행할 작업:

1. 아래 명령을 Bash로 실행한다:

   ```bash
   python3 {PLUGIN}/tools/confluence.py fetch "$ARGUMENTS"
   ```

2. 명령 실패 시 에러 메시지를 그대로 사용자에게 전달한다 (환경변수 미설정 가이드 포함).
3. 저장된 **파일 경로와 섹션 제목 목록만** 출력한다. 섹션 내용은 출력하지 않는다.
4. [messages.md](../context/shared/messages.md) 의 `confl_saved` 를 출력한다.

---

## Search 모드 (기본: Rovo MCP 우선 → 로컬 폴백)

Atlassian Rovo MCP 의 시맨틱 검색을 1차 경로로 사용하고, 실패·결과 0건이면 로컬 docs/ 검색으로 폴백한다.

수행할 작업:

1. **MCP 가용성 확인**: `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql` 도구가 등록되어 있는지 확인한다. 없으면 곧장 4번(로컬 폴백)으로 진행한다.
2. **MCP 호출**: `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql` 를 다음 인자로 호출한다.
   - `cql`: CQL 쿼리 (예: `text ~ "{검색어}"` · 스페이스 필터 시 ` AND space = "KEY"` 추가)
   - `cloudId`: 사용 중인 Atlassian site cloudId (먼저 `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources` 로 확인)
   - `limit`: 5
3. **결과 출력**:
   - 각 항목에 **`[source: rovo-mcp]` 태그**, 제목, `page_id`, 짧은 스니펫을 표시한다.
   - 마지막에 [messages.md](../context/shared/messages.md) 의 `confl_search_source_rovo` 안내를 출력한다.
   - 사용자가 원문이 필요하면 `/pilot:confl {page_id}` 로 fetch 하도록 유도한다 (자동 fetch 하지 않는다).
4. **로컬 폴백** (MCP 미등록 / 호출 실패 / 결과 0건):

   ```bash
   python3 {PLUGIN}/tools/confluence.py search "{검색어}"
   ```

   - 매칭된 섹션만 출력하고 각 결과 끝에 **`[source: local]`** 태그를 붙인다.
   - MCP 호출 실패로 인한 폴백이라면 [messages.md](../context/shared/messages.md) 의 `confl_mcp_unavailable` 을 함께 출력한다.
   - 결과가 없으면 [messages.md](../context/shared/messages.md) 의 `confl_no_match` 를 출력한다.

---

## Search:local 모드 (`--local`)

`$ARGUMENTS` 에서 `--local` 플래그를 제거한 나머지를 검색어로 사용한다. **MCP 호출을 시도하지 않는다.**

수행할 작업:

1. 아래 명령을 Bash로 실행한다:

   ```bash
   python3 {PLUGIN}/tools/confluence.py search-local "{검색어}"
   ```

2. 결과 각 항목에 **`[source: local]`** 태그를 붙여 출력한다.
3. 결과가 없으면 [messages.md](../context/shared/messages.md) 의 `confl_no_match` 를 출력한다.

용도: 정책 이행 점검(원문 인용 필수), 오프라인, 재현성 확보가 필요한 경우.

---

## Search+Action 모드

검색과 후속 작업을 한번에 수행한다.
`$ARGUMENTS`를 `>` 기준으로 분리한다: `{검색어} > {작업지시}`

수행할 작업:

1. `{검색어}` 부분으로 **Search 모드**를 먼저 실행한다 (MCP 우선 → 로컬 폴백).
2. 검색 결과가 있으면, 그 결과를 컨텍스트로 활용해 `{작업지시}`를 수행한다.
   - 결과 출처가 `rovo-mcp` 인 경우 작업 산출물(예: project.md, evaluator.md)에 직접 인용하지 말고 요약·참조로만 사용한다.
   - 원문 인용이 필요한 작업이라면 사용자에게 `/pilot:confl {page_id}` 로 fetch 후 재실행을 권한다.
3. 검색 결과가 없으면 Search 모드의 안내 메시지를 출력하고 종료한다.
4. 검색어에 `--local` 플래그가 포함되어 있으면 1번을 **Search:local 모드**로 실행한다 (정책 점검 모드 호환).

사용 예시:

- `/pilot:confl 배송상태 > project.md에 요구사항 정리`
- `/pilot:confl 주문취소 > evaluator.md 체크리스트 항목 추가`
- `/pilot:confl 정산 > 이 기능의 비즈니스 룰 요약해줘`

---

## All 모드

저장된 모든 docs/ 파일의 전체 내용을 출력한다.

수행할 작업:

1. 아래 명령을 Bash로 실행한다:

   ```bash
   python3 {PLUGIN}/tools/confluence.py all
   ```

2. 명령 실패 시 에러 메시지를 그대로 사용자에게 전달한다.
