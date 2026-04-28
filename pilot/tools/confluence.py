#!/usr/bin/env python3
"""
Confluence docs fetcher / searcher.

Usage:
  python confluence.py fetch <url_or_page_id> [--force]
  python confluence.py search <keyword>
  python confluence.py search-local <keyword>      # search 의 alias (SKILL.md 와 정합)
  python confluence.py all

Flags:
  --force          기존 저장 파일이 있어도 덮어쓴다 (fetch 모드 한정)

Required env vars (둘 중 하나로 설정):
  1) 프로젝트 루트 `.env` 또는 `workspace/.env` 파일에 기록
  2) shell profile에서 `export`

  CONFLUENCE_EMAIL  — Atlassian 계정 이메일 (예: user@example.com)
  CONFLUENCE_TOKEN  — Atlassian API 토큰 (https://id.atlassian.com/manage-profile/security/api-tokens 에서 생성)
"""

import sys
import os
import re
import json
import base64
import requests
from pathlib import Path
from datetime import date, datetime, timezone
from bs4 import BeautifulSoup

WORKSPACE_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


# ---------------------------------------------------------------------------
# .env loader (shell profile 없이도 동작하도록 함)
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """프로젝트 루트 `.env` 또는 `workspace/.env`에서 KEY=VALUE 로드.

    이미 환경에 존재하는 값은 덮어쓰지 않는다 (export가 우선).

    CONFLUENCE_* 같은 credential 키가 .env 에서 로드된 경우 (= env 에 없어서 폴백) stderr 에 한 줄 INFO 를 출력한다.
    non-interactive subshell 에서 .env 와 interactive shell env 가 drift 나면 조용히 구토큰을 쓰는 failure mode 방지.
    """
    CREDENTIAL_PREFIXES = ("CONFLUENCE_",)
    candidates = [
        WORKSPACE_ROOT / ".env",
        WORKSPACE_ROOT / "workspace" / ".env",
    ]
    loaded_credentials: list[tuple[str, Path]] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
                    if any(key.startswith(pfx) for pfx in CREDENTIAL_PREFIXES):
                        loaded_credentials.append((key, path))
        except OSError:
            continue
    if loaded_credentials:
        keys = ", ".join(k for k, _ in loaded_credentials)
        src = loaded_credentials[0][1]
        print(
            f"[INFO] Loaded credentials from {src} (env var not set): {keys}. "
            f"If fetch fails with 401/403, run `/pilot:doctor` to check credential drift.",
            file=sys.stderr,
        )


_load_dotenv()

# Atlassian Confluence 인스턴스 URL. `.env` 또는 shell profile 에 설정.
# 예: CONFLUENCE_HOST=https://yourorg.atlassian.net/wiki
CONFLUENCE_HOST = os.environ.get("CONFLUENCE_HOST", "").rstrip("/")

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def get_active_project() -> str:
    state_file = WORKSPACE_ROOT / "workspace" / "STATE.md"
    if not state_file.exists():
        raise RuntimeError("workspace/STATE.md 가 없습니다. `/pilot:init` 후 `/pilot:project {프로젝트명}` 으로 활성화하세요.")
    for line in state_file.read_text().splitlines():
        if "진행중" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                return parts[1]
    raise RuntimeError("진행중인 프로젝트가 없습니다. /pilot:project {프로젝트명} 으로 먼저 프로젝트를 활성화하세요.")


def docs_dir(project: str) -> Path:
    return WORKSPACE_ROOT / "workspace" / "projects" / project / "docs"


# ---------------------------------------------------------------------------
# Confluence API
# ---------------------------------------------------------------------------

def get_credentials():
    email = os.environ.get("CONFLUENCE_EMAIL", "")
    token = os.environ.get("CONFLUENCE_TOKEN", "")
    missing = []
    if not CONFLUENCE_HOST:
        missing.append("CONFLUENCE_HOST   (Atlassian 인스턴스 URL, 예: https://yourorg.atlassian.net/wiki)")
    if not email:
        missing.append("CONFLUENCE_EMAIL  (Atlassian 계정 이메일, 예: user@example.com)")
    if not token:
        missing.append("CONFLUENCE_TOKEN  (Atlassian API 토큰, https://id.atlassian.com/manage-profile/security/api-tokens 에서 생성)")
    if missing:
        raise RuntimeError(
            "Confluence 환경변수가 설정되지 않았습니다.\n"
            "아래 중 한 가지 방법으로 설정하세요:\n\n"
            "  1) 프로젝트 루트 `.env` 또는 `workspace/.env` 파일에 기록 (권장)\n"
            "     CONFLUENCE_HOST=https://yourorg.atlassian.net/wiki\n"
            "     CONFLUENCE_EMAIL=user@example.com\n"
            "     CONFLUENCE_TOKEN=your-api-token\n\n"
            "  2) shell profile(~/.zshrc, ~/.bashrc 등)에 export\n"
            "     export CONFLUENCE_HOST=\"https://yourorg.atlassian.net/wiki\"\n"
            "     export CONFLUENCE_EMAIL=\"user@example.com\"\n"
            "     export CONFLUENCE_TOKEN=\"your-api-token\"\n\n"
            "필요한 환경변수:\n" + "\n".join(f"  - {m}" for m in missing)
        )
    return email, token


def extract_page_id(arg: str) -> str:
    """URL 또는 숫자 문자열에서 page_id 추출."""
    if re.match(r"^\d+$", arg):
        return arg
    m = re.search(r"/pages/(\d+)", arg)
    if m:
        return m.group(1)
    raise ValueError(f"page_id를 추출할 수 없습니다: {arg}")


def fetch_page(page_id: str) -> dict:
    """Fetch page via v2 API with `body-format=view`.

    view 포맷은 멘션·날짜·status 매크로가 모두 사용자 표시명으로 렌더링되어 있어
    storage 포맷보다 변환 품질이 월등히 좋다.
    """
    email, token = get_credentials()
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    resp = requests.get(
        f"{CONFLUENCE_HOST}/api/v2/pages/{page_id}",
        params={"body-format": "view"},
        headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        timeout=30,
    )
    # 사용자가 읽을 수 있는 메시지로 변환. 그 외 상태코드는 raise_for_status 에 위임.
    if resp.status_code == 401:
        raise RuntimeError(
            "인증 실패 (401). CONFLUENCE_EMAIL / CONFLUENCE_TOKEN 이 유효한지 확인하세요.\n"
            "  진단: /pilot:doctor 또는 https://id.atlassian.com/manage-profile/security/api-tokens 에서 토큰 재발급"
        )
    if resp.status_code == 403:
        raise RuntimeError(
            f"권한 없음 (403, page_id={page_id}). 해당 페이지/스페이스 접근 권한이 있는 계정인지 확인하세요."
        )
    if resp.status_code == 404:
        raise RuntimeError(
            f"페이지를 찾을 수 없음 (404, page_id={page_id}). URL 또는 page_id 가 올바른지 확인하세요."
        )
    resp.raise_for_status()
    data = resp.json()
    return {
        "title": data.get("title", page_id),
        "body": {"storage": {"value": data.get("body", {}).get("view", {}).get("value", "")}},
        "_links": data.get("_links", {}),
    }


# ---------------------------------------------------------------------------
# HTML → Markdown
# ---------------------------------------------------------------------------

def html_to_md(soup) -> str:
    lines = []
    for el in soup.children:
        lines.append(_node_to_md(el))
    return "\n".join(lines).strip()


def _node_to_md(node) -> str:
    if isinstance(node, str):
        return node

    tag = node.name
    if not tag:
        return ""

    # v2 view 에 끼어드는 메타 태그 제거
    if tag in ("style", "script", "colgroup", "col"):
        return ""

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        return f"\n{'#' * level} {_inline_md(node)}\n"

    if tag == "p":
        text = _inline_md(node)
        return f"\n{text}\n" if text else ""

    if tag in ("ul", "ol"):
        items = []
        for i, li in enumerate(node.find_all("li", recursive=False)):
            prefix = f"{i+1}." if tag == "ol" else "-"
            items.append(f"{prefix} {_inline_md(li)}")
        return "\n" + "\n".join(items) + "\n"

    if tag == "table":
        return _table_to_md(node)

    if tag in ("strong", "b"):
        text = _inline_md(node)
        return f"**{text}**" if text else ""

    if tag in ("em", "i"):
        text = _inline_md(node)
        return f"_{text}_" if text else ""

    if tag == "code":
        return f"`{node.get_text(strip=True)}`"

    if tag in ("pre",):
        return f"\n```\n{node.get_text(strip=True)}\n```\n"

    if tag == "br":
        return "\n"

    if tag == "hr":
        return "\n---\n"

    if tag == "a":
        text = _inline_md(node)
        href = node.get("href", "")
        if not text:
            return ""
        if href and not href.startswith("#") and "user-mention" not in (node.get("class") or []):
            return f"[{text}]({href})"
        return text

    if tag == "img":
        alt = node.get("alt", "")
        src = node.get("src", "")
        if src and not src.startswith("blob:"):
            return f"![{alt}]({src})"
        return f"![{alt}]" if alt else ""

    if tag == "time":
        return node.get("datetime") or node.get_text(strip=True)

    if tag in ("div", "section", "span", "tbody", "thead", "tfoot"):
        parts = [_node_to_md(child) for child in node.children]
        return "".join(parts)

    return node.get_text(separator=" ", strip=True)


def _inline_md(node) -> str:
    """인라인 텍스트 + 강조(**) 마크업을 보존해서 한 줄 문자열로 반환."""
    if isinstance(node, str):
        return re.sub(r"\s+", " ", node)

    out = []
    for child in node.children:
        if isinstance(child, str):
            out.append(re.sub(r"\s+", " ", child))
            continue
        cname = child.name
        if cname in ("strong", "b"):
            inner = _inline_md(child).strip()
            if inner:
                out.append(f"**{inner}**")
        elif cname in ("em", "i"):
            inner = _inline_md(child).strip()
            if inner:
                out.append(f"_{inner}_")
        elif cname == "code":
            out.append(f"`{child.get_text(strip=True)}`")
        elif cname == "a":
            text = _inline_md(child).strip()
            href = child.get("href", "")
            if not text:
                continue
            if href and not href.startswith("#") and "user-mention" not in (child.get("class") or []):
                out.append(f"[{text}]({href})")
            else:
                out.append(text)
        elif cname == "br":
            out.append(" ")
        elif cname == "img":
            alt = child.get("alt", "")
            src = child.get("src", "")
            if src and not src.startswith("blob:"):
                out.append(f"![{alt}]({src})")
            elif alt:
                out.append(f"![{alt}]")
        elif cname == "time":
            out.append(child.get("datetime") or child.get_text(strip=True))
        elif cname in ("style", "script"):
            continue
        elif cname in ("p", "div", "span"):
            inner = _inline_md(child).strip()
            if inner:
                out.append(inner)
        else:
            out.append(child.get_text(separator=" ", strip=True))
    text = "".join(out)
    return re.sub(r"[ \t]+", " ", text).strip()


def _cell_md(cell) -> str:
    """셀 안의 콘텐츠를 마크다운 표 1셀로 안전하게 변환.

    - <p>, <br> 등 블록 구분은 `<br>` 로 (마크다운 표 호환)
    - 중첩 <table> 은 `<details>...</details>` HTML 로 보존하지 않고, 행 단위 텍스트로 평탄화
      (외부 표 컬럼 폭주 방지)
    - 강조(**bold**) 보존
    - 파이프(`|`) escape
    """
    blocks: list[str] = []

    def walk(el):
        if isinstance(el, str):
            txt = re.sub(r"\s+", " ", el).strip()
            if txt:
                blocks.append(txt)
            return
        nm = el.name
        if not nm or nm in ("style", "script", "colgroup", "col"):
            return
        if nm == "table":
            # 중첩 표 → 텍스트로 평탄화 (행마다 ` / ` 로 컬럼 구분)
            for tr in el.find_all("tr", recursive=True):
                cells = []
                for c in tr.find_all(["td", "th"], recursive=False):
                    inner = _inline_md(c).strip()
                    if inner:
                        cells.append(inner)
                if cells:
                    blocks.append(" / ".join(cells))
            return
        if nm in ("p", "div", "li", "tr"):
            inner = _inline_md(el).strip()
            if inner:
                blocks.append(inner)
            return
        if nm in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                inner = _inline_md(li).strip()
                if inner:
                    blocks.append(f"• {inner}")
            return
        if nm == "br":
            return
        # 그 외(예: section, td 직속 inline) → inline 변환
        inner = _inline_md(el).strip()
        if inner:
            blocks.append(inner)

    for child in cell.children:
        walk(child)

    text = "<br>".join(b for b in blocks if b)
    text = text.replace("|", "\\|")
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" <br> ", "<br>").replace("<br> ", "<br>").replace(" <br>", "<br>")
    return text.strip()


def _table_to_md(table) -> str:
    """Render a table to Markdown, flattening rowspan/colspan.

    rowspan: 병합된 셀의 텍스트를 N개 행에 동일하게 복제해 모든 행을 self-contained 로 만든다.
             (마크다운 표는 셀 병합을 표현 못 하므로, 분석용으로는 복제가 안전하다.)
    colspan: 병합된 셀 텍스트를 가장 왼쪽 컬럼에만 두고 나머지 컬럼은 빈 칸으로.
             (보통 헤더 그룹화 용도라, 데이터 행과 컬럼 정렬을 보존하기 위함.)
    """
    # 직속 tbody/thead/tfoot 또는 직접 tr 자식만 수집 (중첩 테이블 row 흡수 방지)
    tr_list: list = []
    for c in table.children:
        if getattr(c, "name", None) == "tr":
            tr_list.append(c)
    for section in table.find_all(["thead", "tbody", "tfoot"], recursive=False):
        for c in section.children:
            if getattr(c, "name", None) == "tr":
                tr_list.append(c)

    if not tr_list:
        return ""

    # Sparse grid: (row, col) → cell text. occupied 로 rowspan/colspan 점유 추적.
    grid: dict[tuple[int, int], str] = {}
    occupied: set[tuple[int, int]] = set()
    max_col = 0

    def _safe_int(v, default=1) -> int:
        try:
            n = int(v)
            return n if n > 0 else default
        except (TypeError, ValueError):
            return default

    for r_idx, tr in enumerate(tr_list):
        c_idx = 0
        for td in tr.find_all(["td", "th"], recursive=False):
            while (r_idx, c_idx) in occupied:
                c_idx += 1
            rs = _safe_int(td.get("rowspan", 1))
            cs = _safe_int(td.get("colspan", 1))
            content = _cell_md(td)
            for dr in range(rs):
                for dc in range(cs):
                    pos = (r_idx + dr, c_idx + dc)
                    occupied.add(pos)
                    # rowspan: 모든 행에 복제. colspan: 첫 컬럼에만 텍스트, 나머지는 빈칸.
                    grid[pos] = content if dc == 0 else ""
            c_idx += cs
            if c_idx > max_col:
                max_col = c_idx

    # rowspan 이 마지막 tr 너머까지 확장될 수 있으므로 occupied 기반으로 행 수 산정
    max_row = max((r for r, _ in occupied), default=-1) + 1
    if max_row == 0 or max_col == 0:
        return ""

    rows = [[grid.get((r, c), "") for c in range(max_col)] for r in range(max_row)]

    lines = []
    for i, row in enumerate(rows):
        lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            lines.append("| " + " | ".join(["---"] * max_col) + " |")

    return "\n" + "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------

def split_sections(soup) -> list[dict]:
    """H1/H2 기준으로 섹션 분할. 반환: [{"heading": str, "level": int, "content": str}]"""
    sections = []
    current_heading = "(서문)"
    current_level = 0
    current_nodes = []

    def flush():
        # 빈 H1 그룹 헤딩(예: "# 1. 배경 및 목적")도 보존: nodes 가 비어 있어도 섹션 1개로 추가.
        if current_nodes:
            content_soup = BeautifulSoup("".join(str(n) for n in current_nodes), "html.parser")
            content = html_to_md(content_soup)
        else:
            content = ""
        # 최초 (서문) 자리에 실제 컨텐츠가 없으면 스킵
        if current_heading == "(서문)" and not content.strip():
            return
        sections.append({
            "heading": current_heading,
            "level": current_level if current_level > 0 else 1,
            "content": content,
        })

    for child in soup.children:
        if not hasattr(child, "name") or not child.name:
            current_nodes.append(child)
            continue

        if child.name in ("h1", "h2"):
            flush()
            current_heading = child.get_text(strip=True)
            current_level = int(child.name[1])
            current_nodes = []
        else:
            current_nodes.append(child)

    flush()
    # 빈 H1 그룹 헤딩(예: "# 1. 배경 및 목적")은 하위 섹션 묶음 라벨이므로 보존한다.
    return sections


# ---------------------------------------------------------------------------
# Fetch mode
# ---------------------------------------------------------------------------

def _update_docs_last_fetched_at(project: str) -> bool:
    """Update `docs_last_fetched_at` in project's .agent-state.yml.

    Returns True if file was updated, False if file missing or schema unknown.
    Silent on unknown schemas (migrate required first).
    """
    state_path = WORKSPACE_ROOT / "workspace" / "projects" / project / ".agent-state.yml"
    if not state_path.is_file():
        return False

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        lines = state_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False

    # Replace existing line or append
    updated = False
    out: list[str] = []
    for line in lines:
        if line.strip().startswith("docs_last_fetched_at:"):
            out.append(f'docs_last_fetched_at: "{now_iso}"')
            updated = True
        else:
            out.append(line)
    if not updated:
        out.append(f'docs_last_fetched_at: "{now_iso}"')

    content = "\n".join(out)
    if not content.endswith("\n"):
        content += "\n"
    state_path.write_text(content, encoding="utf-8")
    return True


def cmd_fetch(arg: str, force: bool = False):
    page_id = extract_page_id(arg)
    project = get_active_project()
    

    # 파일명 slug — 타이틀을 아직 모르지만 page_id 부분은 고정이므로 idempotency 체크는 page_id prefix 로 수행
    out_dir = docs_dir(project)
    existing = []
    if out_dir.is_dir():
        existing = sorted(out_dir.glob(f"{page_id}_*.md"))

    if existing and not force:
        paths = "\n    ".join(str(p.relative_to(WORKSPACE_ROOT)) for p in existing)
        print(
            f"기존 저장 파일 발견 (page_id={page_id}):\n    {paths}\n"
            f"이미 같은 기획서가 저장돼 있습니다. overwrite 하시겠습니까? [y/N]: ",
            end="",
            flush=True,
        )
        # stdin 이 tty 가 아니면 (비 interactive) 기본 N 로 안전 종료
        if not sys.stdin.isatty():
            print("\n(non-interactive stdin — overwrite 건너뜀. 재실행 시 `fetch --force` 사용)")
            return
        answer = sys.stdin.readline().strip().lower()
        if answer not in ("y", "yes"):
            print("overwrite 취소. 기존 파일 유지.")
            return

    print(f"Fetching page {page_id} for project [{project}]...")
    data = fetch_page(page_id)

    title = data.get("title", page_id)
    html = data["body"]["storage"]["value"]
    # v2 view 가 prepend 하는 <style> 블록은 변환 노이즈만 만들어 제거한다.
    # _node_to_md 에서도 style 태그를 무시하지만, BS4 가 잘못된 CSS 안의 `<` 토큰에서
    # 트리 파싱이 깨질 수 있어 사전 strip 으로 defense-in-depth.
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    soup = BeautifulSoup(html, "html.parser")
    sections = split_sections(soup)

    # 파일명 slug
    slug = re.sub(r"[^\w가-힣]", "_", title)[:50].strip("_")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{page_id}_{slug}.md"

    # v2 응답의 `_links.webui` 는 `/spaces/{key}/pages/{id}/{title-slug}` 형태의 상대 경로.
    # base 는 `_links.base` 가 있으면 그걸 쓰고, 없으면 모듈 상수로 폴백.
    links = data.get("_links", {}) or {}
    base = (links.get("base") or CONFLUENCE_HOST).rstrip("/")
    webui = links.get("webui") or f"/pages/{page_id}"
    if not webui.startswith("/"):
        webui = "/" + webui
    page_url = f"{base}{webui}"

    lines = [
        f"# {title}",
        f"",
        f"> source: {page_url}",
        f"> fetched: {date.today()}",
        f"> page_id: {page_id}",
        f"",
        f"---",
        f"",
    ]

    # 페이지 타이틀이 #이므로, 본문 H1 → ##, 본문 H2 → ### 로 한 단계 내림.
    for s in sections:
        level = s["level"] + 1 if s["level"] >= 1 else 2
        lines.append(f"{'#' * level} {s['heading']}\n")
        if s["content"].strip():
            lines.append(s["content"])
        lines.append("")

    content = "\n".join(lines)
    out_path.write_text(content, encoding="utf-8")

    # analyze 단계 Read 전략을 위한 메트릭 출력
    size_bytes = len(content.encode("utf-8"))
    size_kb = size_bytes / 1024
    line_count = content.count("\n") + 1
    # 한국어·표가 많은 기획서 특성을 감안해 보수적으로 추정 (문자 수 // 3)
    est_tokens = len(content) // 3
    if size_kb <= 50:
        read_strategy = "소형 — 전체 1회 Read 가능"
    elif size_kb <= 150:
        read_strategy = "중형 — H2 목차 확보 후 섹션 단위 Read (limit 150)"
    else:
        read_strategy = "대형 — H2 목차 확보 후 섹션 단위 targeted Read (limit 80)"

    # .agent-state.yml 의 docs_last_fetched_at 갱신 (drift 감지용)
    state_updated = _update_docs_last_fetched_at(project)

    print(f"\n저장 완료: {out_path.relative_to(WORKSPACE_ROOT)}")
    print(f"크기: {size_kb:.1f}KB · {line_count} 라인 · 추정 {est_tokens:,} 토큰")
    print(f"Read 전략 권장: {read_strategy}")
    if state_updated:
        print("state.yml 의 docs_last_fetched_at 갱신됨")
    print(f"총 {len(sections)}개 섹션\n")
    print("섹션 목록:")
    for s in sections:
        indent = "  " * (s["level"] - 1)
        print(f"{indent}- {s['heading']}")


# ---------------------------------------------------------------------------
# Search mode
# ---------------------------------------------------------------------------

def cmd_search(keyword: str):
    project = get_active_project()
    
    s_dir = docs_dir(project)

    if not s_dir.exists():
        print(f"docs/ 폴더가 없습니다. 먼저 `/pilot:confl {{url}}`로 기획서를 저장하세요.")
        return

    md_files = list(s_dir.glob("*.md"))
    if not md_files:
        print("저장된 docs 파일이 없습니다.")
        return

    kw_lower = keyword.lower()
    results = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        # H2 기준 섹션 분할
        raw_sections = re.split(r"\n(?=#{1,2} )", text)
        for section in raw_sections:
            if kw_lower in section.lower():
                heading_match = re.match(r"(#{1,3} .+)", section)
                heading = heading_match.group(1) if heading_match else "(서문)"
                results.append({
                    "file": md_file.name,
                    "heading": heading.strip(),
                    "content": section.strip(),
                })

    if not results:
        print(f"'{keyword}' 검색 결과 없음")
        return

    print(f"'{keyword}' 검색 결과: {len(results)}개 섹션\n")
    for r in results:
        print(f"### [{r['file']}] {r['heading']}")
        print(r["content"][:2000])
        if len(r["content"]) > 2000:
            print("... (이하 생략)")
        print()


# ---------------------------------------------------------------------------
# All mode
# ---------------------------------------------------------------------------

def cmd_all():
    project = get_active_project()
    
    s_dir = docs_dir(project)

    if not s_dir.exists():
        print(f"docs/ 폴더가 없습니다. 먼저 `/pilot:confl {{url}}`로 기획서를 저장하세요.")
        return

    md_files = list(s_dir.glob("*.md"))
    if not md_files:
        print("저장된 docs 파일이 없습니다.")
        return

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        print(f"\n{'='*60}")
        print(f"# {md_file.name}")
        print('='*60)
        print(text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    # --force 플래그 추출 (fetch 전용, 위치 무관)
    rest_args = [a for a in sys.argv[2:] if a != "--force"]
    force_flag = "--force" in sys.argv[2:]
    arg = " ".join(rest_args)

    try:
        if mode == "fetch":
            cmd_fetch(arg, force=force_flag)
        elif mode in ("search", "search-local"):
            # search-local 은 SKILL.md 의 명시적 별칭. cmd_search 자체가 이미 로컬 docs/ 만 검색한다.
            cmd_search(arg)
        elif mode == "all":
            cmd_all()
        else:
            print(f"알 수 없는 모드: {mode}")
            sys.exit(1)
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
