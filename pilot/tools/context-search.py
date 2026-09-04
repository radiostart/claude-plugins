#!/usr/bin/env python3
"""
pilot context-search — 섹션 단위 결정적 검색 도구.

workspace/context/ 마크다운 지식 파일을 H2·H3 섹션 단위로 색인하고, 질의 토큰과
헤딩·경로·인용·description·본문 신호를 채점해 순위가 매겨진 섹션 목록을 반환한다.
에이전트가 본문 파일 전체 Read·무차별 Grep 대신 사용하는 부분 로드 진입점.

Usage:
    python3 pilot/tools/context-search.py "<질의>" [--workspace PATH] [--project NAME]
        [--scope DOMAIN] [--include PATH ...] [--limit N] [--format md|json]

    질의는 반드시 첫 위치 인자로 지정한다 — `--include` 는 nargs="+" 라 뒤에 두면
    질의 문자열을 흡수해버린다.

질의 3형식:
    select:{path}[#{헤딩 일부}]   경로(및 헤딩 일부)를 직접 지정 — 점수 없이 반환
    키워드 나열                    공백으로 구분된 선택 토큰 (OR 성격)
    +필수어 선택어                 `+` 접두 토큰은 사전필터 겸 채점 대상(D6)

    토큰이 경로처럼 보이면(`/` 포함 + 확장자) 인용 경로 일치를 자동 가중한다 —
    "이 소스 파일을 다루는 지식 섹션" 을 찾는 역방향 질의.

점수표 (토큰마다 신호별 최대 1회 합산 — 빈도는 반영하지 않는다):
    헤딩 토큰 정확 일치              10
    파일 경로 세그먼트 일치           8
    인용 경로 세그먼트 일치           6
    헤딩 토큰 부분 일치               5
    frontmatter description 일치     4
    본문 단어경계 일치                2

    level 1 섹션(서문·H1-only·헤딩 없는 파일)은 헤딩 신호(10/5)를 받지 않는다 —
    경로·인용·description·본문 신호만 채점된다.

출력 스키마 (--format json):
    {"query", "root", "scope", "include": [...], "candidates": N, "returned": k,
     "results": [{"file", "heading", "level", "line_start", "line_end", "score",
                  "matched", "snippet", "read_hint"}],
     "info": [...], "zero_hit": {...} | null}

    --format md (기본): 1줄 헤더 + 결과 표 + 섹션별 snippet/read_hint + INFO·0건 안내.

Exit:
    0 — 성공 (0건 포함 — 실패가 아니라 상태 안내)
    2 — 빈 질의·토큰 전멸 / scope·project·include·select traversal / --limit < 1 /
        --format 오류 / 코퍼스 루트 부재

제약:
    - 지식 파일은 읽기 전용 — 어떤 경로도 workspace/context/ 를 쓰지 않는다.
    - 같은 코퍼스·질의 → 같은 출력·순서 (결정적 — set 순회 결과를 출력에 노출하지 않는다).
    - 표준 라이브러리만: re · pathlib · json · argparse · os · sys · dataclasses ·
      importlib.util (형제 모듈 지연 로드).
    - 캐시 없음 = 실행 간 영속 캐시 없음(파일·mtime 키 캐시 금지). 실행 1회 안에서만
      쓰는 memo(예: 인용 경로 토큰화 결과)는 허용한다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ── 상수 ────────────────────────────────────────────────────────
DEFAULT_LIMIT = 5
MAX_LIMIT = 20
SNIPPET_CHARS = 240
LARGE_SECTION_LINES = 400

SCORE = {
    "heading_exact": 10,
    "path": 8,
    "citation": 6,
    "heading_partial": 5,
    "description": 4,
    "body": 2,
}

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "be", "with", "as", "at", "by", "from", "this", "that", "it",
}
STOPWORDS_KO = {
    "및", "등", "또는", "그리고", "경우", "때", "것", "수", "위한", "대한",
    "통해", "따라", "이후", "이전", "모든",
}

WORD = "[0-9A-Za-z가-힣]"  # 경계 판정 문자 클래스 — `\w` 는 `_` 를 포함하므로 쓰지 않는다.


# ── 토큰화 ──────────────────────────────────────────────────────
_ALNUM_HANGUL_RE = re.compile(r"[A-Za-z0-9]+|[가-힣]+")
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,5}$")


def _is_hangul_token(token: str) -> bool:
    return any("가" <= ch <= "힣" for ch in token)


def tokenize(text: str) -> list[str]:
    """소문자화 · 영숫자/한글 경계 분리 · CamelCase 분리(원형 유지) · 1글자·불용어
    제거 · 순서 보존 dedupe. `_`·`-`·`.`·`/`·`:`·공백·구두점·백틱은 알아서 분리된다
    (문자 클래스 밖이므로 토큰 경계가 된다)."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []

    def add(tok: str) -> None:
        tok = tok.lower()
        if len(tok) <= 1:
            return
        if tok in STOPWORDS_EN or tok in STOPWORDS_KO:
            return
        if tok in seen:
            return
        seen.add(tok)
        out.append(tok)

    for run in _ALNUM_HANGUL_RE.findall(text):
        if run.isascii():
            parts = [p for p in _CAMEL_SPLIT_RE.split(run) if p]
            for p in parts:
                add(p)
            if len(parts) > 1:
                add(run)
        else:
            add(run)
    return out


def path_tokens(path_str: str) -> list[str]:
    """경로 문자열을 토큰화하되 **마지막 세그먼트의 확장자만** 제거한다 —
    `md`·`py` 같은 확장자 토큰이 경로·인용 신호를 오염시키지 않게."""
    idx = path_str.rfind("/")
    head, tail = (path_str[: idx + 1], path_str[idx + 1 :]) if idx != -1 else ("", path_str)
    tail = _EXT_RE.sub("", tail)
    return tokenize(head + tail)


# ── 질의 파싱 ───────────────────────────────────────────────────
@dataclass
class Query:
    kind: str  # "select" | "keywords"
    optional: list[str]
    required: list[str]
    raw_paths: list[str]
    select_path: str | None = None
    select_heading: str | None = None


_PATH_LIKE_RE = re.compile(r"\.[A-Za-z0-9]{1,5}$")


def parse_query(raw: str) -> Query:
    raw = raw.strip()
    if raw.startswith("select:"):
        rest = raw[len("select:") :]
        if "#" in rest:
            path_part, heading_part = rest.split("#", 1)
        else:
            path_part, heading_part = rest, ""
        return Query(
            kind="select",
            optional=[],
            required=[],
            raw_paths=[],
            select_path=path_part.strip(),
            select_heading=heading_part.strip() or None,
        )

    optional: list[str] = []
    required: list[str] = []
    raw_paths: list[str] = []
    for word in raw.split():
        is_required = word.startswith("+") and len(word) > 1
        w = word[1:] if is_required else word
        if "/" in w and _PATH_LIKE_RE.search(w):
            raw_paths.append(w)
            toks = path_tokens(w)
        else:
            toks = tokenize(w)
        (required if is_required else optional).extend(toks)
    return Query(kind="keywords", optional=optional, required=required, raw_paths=raw_paths)


# ── 섹션 분할 ───────────────────────────────────────────────────
@dataclass
class Section:
    file: str  # 코퍼스 루트(workspace/context) 기준 상대경로, posix 구분자
    heading: str
    level: int  # 2·3 = 색인 헤딩, 1 = 서문/H1-only/헤딩 없음
    line_start: int  # 1-based inclusive
    line_end: int  # 1-based inclusive
    body_lines: list[str]  # 헤딩 라인 제외 본문
    description: str | None = None


_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_OPEN_RE = re.compile(r"^\s*(```+|~~~+)")
_DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$")


def _strip_description_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_sections(text: str, rel_path: str) -> list[Section]:
    """H2·H3 를 색인 헤딩으로 섹션 분할. frontmatter 제외 + description 보관,
    펜스(``` / ~~~) 안의 `#` 는 헤딩으로 인식하지 않는다. D7: 첫 H2/H3 이전
    구간은 level 1 서문 섹션(본문이 비면 생략), H2/H3 이 전혀 없으면 파일 전체가
    level 1 섹션 1개(H1 있으면 그 텍스트, 없으면 `(파일 전체)`)."""
    lines = text.splitlines()
    n = len(lines)

    description: str | None = None
    content_start = 0
    if lines and lines[0].strip() == "---":
        close_idx = None
        for i in range(1, n):
            if lines[i].strip() == "---":
                close_idx = i
                break
        if close_idx is not None:
            for i in range(1, close_idx):
                dm = _DESCRIPTION_RE.match(lines[i].strip())
                if dm:
                    description = _strip_description_quotes(dm.group(1))
                    break
            content_start = close_idx + 1

    # 펜스 추적 + 헤딩 수집 (frontmatter 밖 구간만)
    headings: list[tuple[int, int, str]] = []  # (0-based line idx, level, text)
    in_fence = False
    fence_char = ""
    for i in range(content_start, n):
        line = lines[i]
        if in_fence:
            stripped = line.strip()
            if stripped and set(stripped) == {fence_char} and len(stripped) >= 3:
                in_fence = False
            continue
        fm = _FENCE_OPEN_RE.match(line)
        if fm:
            in_fence = True
            fence_char = fm.group(1)[0]
            continue
        hm = _HEADING_RE.match(line)
        if hm:
            headings.append((i, len(hm.group(1)), hm.group(2).strip()))

    indexed = [h for h in headings if h[1] in (2, 3)]
    sections: list[Section] = []

    def body_between(start_idx: int, end_idx: int, skip_idx: int | None) -> list[str]:
        return [lines[i] for i in range(start_idx, end_idx) if i != skip_idx]

    if not indexed:
        h1 = next((h for h in headings if h[1] == 1), None)
        if content_start >= n:
            return sections
        if h1 is not None:
            heading_text = h1[2]
            body_lines = body_between(content_start, n, h1[0])
        else:
            heading_text = "(파일 전체)"
            body_lines = body_between(content_start, n, None)
        sections.append(
            Section(
                file=rel_path, heading=heading_text, level=1,
                line_start=content_start + 1, line_end=n,
                body_lines=body_lines, description=description,
            )
        )
        return sections

    first_idx = indexed[0][0]
    h1_in_preface = next(
        (h for h in headings if h[1] == 1 and content_start <= h[0] < first_idx), None
    )
    preface_body = body_between(
        content_start, first_idx, h1_in_preface[0] if h1_in_preface else None
    )
    if any(ln.strip() for ln in preface_body):
        sections.append(
            Section(
                file=rel_path,
                heading=h1_in_preface[2] if h1_in_preface else "(서문)",
                level=1, line_start=content_start + 1, line_end=first_idx,
                body_lines=preface_body, description=description,
            )
        )

    for idx, level, htext in indexed:
        end_idx = n
        for h2_idx, h2_level, _h2_text in headings:
            if h2_idx > idx and h2_level <= level:
                end_idx = h2_idx
                break
        sections.append(
            Section(
                file=rel_path, heading=htext, level=level,
                line_start=idx + 1, line_end=end_idx,
                body_lines=lines[idx + 1 : end_idx], description=description,
            )
        )

    return sections


# ── 인용 경로 추출 ──────────────────────────────────────────────
_CITATION_RE = re.compile(
    r"[A-Za-z0-9_.\-]*(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]{1,5}(?::\d+(?:-\d+)?)?"
)
_CITATION_LINE_SUFFIX_RE = re.compile(r":\d+(?:-\d+)?$")


def extract_citations(
    body: str, memo: dict[str, list[str]] | None = None
) -> tuple[set[str], list[str]]:
    """본문에서 `path/like/this.ext[:N[-M]]` 형태의 인용 경로를 추출.

    반환: (모든 인용 경로의 path_tokens 합집합, `:line` 을 뗀 인용 경로 목록).
    `memo` 는 **실행 1회 안에서만** 쓰는 캐시 — 같은 인용 문자열의 path_tokens
    재계산을 막는다(실행 간 영속 캐시 아님, C5).
    """
    citation_tokens: set[str] = set()
    citation_paths: list[str] = []
    if not body:
        return citation_tokens, citation_paths
    for m in _CITATION_RE.finditer(body):
        path_part = _CITATION_LINE_SUFFIX_RE.sub("", m.group(0))
        citation_paths.append(path_part)
        if memo is not None and path_part in memo:
            toks = memo[path_part]
        else:
            toks = path_tokens(path_part)
            if memo is not None:
                memo[path_part] = toks
        citation_tokens.update(toks)
    return citation_tokens, citation_paths


# ── 점수 ────────────────────────────────────────────────────────
# boundary_pattern/boundary_search 는 D1 경계 규칙의 SSOT — score_text 내부뿐 아니라
# confluence.py `search_docs` 의 match_pos 계산(C4-2)도 이 함수를 그대로 재사용한다.
def boundary_pattern(token: str) -> str:
    escaped = re.escape(token)
    if _is_hangul_token(token):
        return f"(?<!{WORD}){escaped}"  # 한글 포함 토큰 — 좌측 경계만(우측 조사 허용)
    return f"(?<!{WORD}){escaped}(?!{WORD})"  # ASCII 토큰 — 양측 경계


def boundary_search(token: str, text_lc: str) -> "re.Match[str] | None":
    return re.search(boundary_pattern(token), text_lc)


def score_text(
    query: Query,
    *,
    heading: str,
    body: str,
    path_tokens: "tuple[str, ...] | set[str] | list[str]" = (),
    citation_tokens: "tuple[str, ...] | set[str] | list[str]" = (),
    citation_paths: "tuple[str, ...] | list[str]" = (),
    description: str | None = None,
) -> tuple[int, list[str]]:
    """문자열 기반 채점 진입점 (confluence.py `search_docs` 재사용 대상, C4).

    토큰마다 신호별 최대 1회 합산. `heading=""` 로 호출하면 헤딩 신호(10/5) 가
    통째로 꺼진다 — level 1 섹션(서문 등)에 score_section 이 이렇게 호출한다(C2).
    `required` 토큰 중 하나라도 이 텍스트 조합에서 신호가 0 이면 전체 0점(사전필터,
    D6) — 단 진단용 `matched` 는 개별 신호가 있던 토큰을 그대로 반환한다.
    """
    heading_tokens = set(tokenize(heading)) if heading else set()
    path_set = set(path_tokens)
    citation_set = set(citation_tokens)
    body_lc = body.lower() if body else ""
    desc_lc = description.lower() if description else None

    all_tokens = list(dict.fromkeys(list(query.required) + list(query.optional)))
    token_score: dict[str, int] = {}
    for t in all_tokens:
        s = 0
        exact = t in heading_tokens
        if exact:
            s += SCORE["heading_exact"]
        if t in path_set:
            s += SCORE["path"]
        if t in citation_set:
            s += SCORE["citation"]
        if not exact and any(t in h for h in heading_tokens):
            s += SCORE["heading_partial"]
        if desc_lc is not None and boundary_search(t, desc_lc):
            s += SCORE["description"]
        if body_lc and boundary_search(t, body_lc):
            s += SCORE["body"]
        if s > 0:
            token_score[t] = s

    matched_raw_paths: list[str] = []
    path_bonus = 0
    for p in query.raw_paths:
        for c in citation_paths:
            if c == p or c.endswith("/" + p):
                path_bonus += SCORE["citation"]
                matched_raw_paths.append(p)
                break

    matched = [t for t in all_tokens if t in token_score] + matched_raw_paths
    required_ok = all(t in token_score for t in query.required)
    if not required_ok:
        return 0, matched
    return sum(token_score.values()) + path_bonus, matched


def score_section(
    section: Section, query: Query, memo: dict[str, list[str]] | None = None
) -> tuple[int, list[str]]:
    body = "\n".join(section.body_lines)
    citation_tokens, citation_paths = extract_citations(body, memo=memo)
    heading_for_score = section.heading if section.level in (2, 3) else ""
    return score_text(
        query,
        heading=heading_for_score,
        body=body,
        path_tokens=path_tokens(section.file),
        citation_tokens=citation_tokens,
        citation_paths=citation_paths,
        description=section.description,
    )


# ── 순위 ────────────────────────────────────────────────────────
def rank(
    scored: list[tuple[Section, int, list[str]]],
    limit: int,
    entry_rel: "frozenset[str] | set[str]" = frozenset(),
) -> list[tuple[Section, int, list[str]]]:
    """`scored` (score > 0 인 (Section, score, matched) 튜플)를 정렬해 상위
    `limit` 개만 반환. 정렬 키: 점수 내림차순 → H2 → H3 → level1 → 진입 파일
    우선 → 파일 경로 오름차순 → 시작 라인. `limit` 클램핑은 호출부(`search`) 책임."""

    def level_rank(level: int) -> int:
        return {2: 0, 3: 1}.get(level, 2)

    def is_entry(sec: Section) -> bool:
        return Path(sec.file).name == "index.md" or sec.file in entry_rel

    ordered = sorted(
        scored,
        key=lambda item: (
            -item[1],
            level_rank(item[0].level),
            0 if is_entry(item[0]) else 1,
            item[0].file,
            item[0].line_start,
        ),
    )
    return ordered[:limit]


# ── 스니펫 · read_hint ──────────────────────────────────────────
def build_snippet(section: Section, matched: list[str]) -> str:
    raw = " ".join(ln.strip() for ln in section.body_lines if ln.strip())
    normalized = re.sub(r"\s+", " ", raw).strip()
    if not normalized:
        return ""
    lc = normalized.lower()

    pos: int | None = None
    for t in matched:
        if not t:
            continue
        m = boundary_search(t, lc)
        if m is not None and (pos is None or m.start() < pos):
            pos = m.start()

    if pos is None:
        window = normalized[:SNIPPET_CHARS]
        return window + "…" if len(normalized) > SNIPPET_CHARS else window

    start = max(0, pos - 80)
    end = min(len(normalized), pos + 160)
    if end - start > SNIPPET_CHARS:
        end = start + SNIPPET_CHARS
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(normalized) else ""
    return f"{prefix}{normalized[start:end]}{suffix}"


def build_read_hint(section: Section, display_file: str) -> str:
    n_lines = section.line_end - section.line_start + 1
    if n_lines > LARGE_SECTION_LINES:
        return (
            f"섹션이 크다({n_lines}줄) — 소제목으로 재질의 권장 "
            f"(앞부분만: Read {display_file} offset={section.line_start} limit=80)"
        )
    return f"Read {display_file} offset={section.line_start} limit={n_lines}"


# ── 0건 안내 ────────────────────────────────────────────────────
def build_zero_hit(
    query_raw: str, query: Query, token_hits: dict[str, int],
    scope: str | None, scope_fallback: bool,
) -> dict:
    guidance: list[str] = []
    if scope:
        guidance.append(f"'--scope {scope}' 를 제거하고 코퍼스 전체로 재검색")
    if query.required:
        guidance.append("'+필수어' 를 제거하고 재검색 (필수어가 후보를 과도하게 좁혔을 수 있음)")
    split_word = next((w for w in query_raw.split() if "_" in w or "-" in w), None)
    if split_word:
        example = re.sub(r"[_\-]+", " ", split_word)
        guidance.append(f"토큰을 나눠 재질의 (예: `{split_word}` → `{example}`)")
    zero_korean = [t for t, c in token_hits.items() if c == 0 and _is_hangul_token(t)]
    if zero_korean:
        t0 = zero_korean[0]
        # 토큰이 이미 조사로 끝나면 그 토큰으로, 아니면 고정 예시로 (C8 — `섹션을을` 이중 조사 렌더 방지)
        ex_from, ex_to = (t0, t0[:-1]) if len(t0) > 1 and t0[-1] in "을를이가은는" else ("섹션을", "섹션")
        guidance.append(f"한글 토큰에 조사가 붙었을 수 있음 — 조사 제거 재질의 (예: `{ex_from}` → `{ex_to}`)")
    if scope and scope_fallback:
        guidance.append("도메인이 미등록이면 `/pilot:learn {진입점}` 으로 부트스트랩")
    return {"token_hits": token_hits, "guidance": guidance}


# ── 코퍼스 수집 ─────────────────────────────────────────────────
class SearchError(Exception):
    def __init__(self, message: str, exit_code: int = 2, show_usage: bool = False):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.show_usage = show_usage


def _traversal(value: str) -> bool:
    """식별자에 경로 구분자·`..` 포함 여부. orchestrate-load.has_path_traversal 과
    동등한 로컬 판정 — D8 모듈 로드 성패와 무관하게 **항상** 이 함수로 검사한다."""
    return "/" in value or "\\" in value or ".." in value


def _load_orchestrate_load():
    """orchestrate-load.py 를 importlib 로 지연 로드(D8) — `parse_manifest_domain_files`
    · `parse_state_md_active` 재사용. 실패 시 None(호출부가 폴더 기반 fallback, A2)."""
    try:
        path = Path(__file__).resolve().parent / "orchestrate-load.py"
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location(
            "_context_search_orchestrate_load", path
        )
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        # Python 3.13: exec 전에 sys.modules 등록 — 대상 모듈이 향후 @dataclass 를
        # 쓰게 되어도 __module__ 해석이 깨지지 않게 방어적으로 통일(test_auto_pilot.py 선례).
        sys.modules["_context_search_orchestrate_load"] = module
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def _walk_md_files(dir_path: Path) -> list[Path]:
    """dir_path 이하 `*.md` 를 심볼릭 링크 디렉터리도 포함해 재귀 수집.

    `Path.rglob("**/*.md")` 는 기본적으로 심볼릭 링크 디렉터리를 따라가지 않는다
    (`recurse_symlinks` 파라미터는 Python 3.13+ 전용이라 CI 의 3.12 에서 못 쓴다).
    `os.walk(followlinks=True)` 는 버전 무관하게 동일 거동을 보장하므로 이걸 쓴다
    — collect_files 의 봉쇄 검증(resolve() 가 루트 밖이면 제외)이 실제로 걸러낼
    대상이 있어야 두 번째 방어선으로서 의미가 있다.
    """
    out: list[Path] = []
    if not dir_path.is_dir():
        return out
    for dirpath, _dirnames, filenames in os.walk(dir_path, followlinks=True):
        for name in filenames:
            if name.endswith(".md"):
                out.append(Path(dirpath) / name)
    return out


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def collect_files(
    workspace: Path, scope: str | None, includes: "list[str] | None", project: str | None
) -> tuple[list[Path], list[str], list[Path]]:
    """코퍼스 파일 목록을 모은다. 반환: (files, info, entry_files).

    `files`/`entry_files` 는 dedupe + 상대경로 오름차순 정렬 완료 상태(C6-b) —
    결정성의 근거이기도 하다.
    """
    info: list[str] = []

    if scope is not None and _traversal(scope):
        raise SearchError(f"scope/project 인자에 경로 구분자·'..' 사용 불가: {scope}", 2)
    if project is not None and _traversal(project):
        raise SearchError(f"scope/project 인자에 경로 구분자·'..' 사용 불가: {project}", 2)

    root = workspace / "context"
    if not root.is_dir():
        raise SearchError(f"코퍼스 루트 없음: {root}", 2)

    ol_mod = _load_orchestrate_load()
    if ol_mod is None:
        info.append("orchestrate-load 로드 실패 — 폴더 기반 scope 만 적용, MANIFEST 진입 파일 조회 skip")

    corpus_candidates: set[Path] = set()
    entry_files: list[Path] = []

    if scope:
        scope_dir = root / scope
        scope_file = root / f"{scope}.md"
        found_any = False
        if scope_dir.is_dir():
            corpus_candidates.update(_walk_md_files(scope_dir))
            found_any = True
        if scope_file.is_file():
            corpus_candidates.add(scope_file)
            found_any = True

        if ol_mod is not None:
            try:
                entries = ol_mod.parse_manifest_domain_files(root / "MANIFEST.md", scope)
            except Exception:
                entries = []
        else:
            entries = []
        for rel in entries:
            p = root / rel
            if p.is_file():
                corpus_candidates.add(p)
                entry_files.append(p)
                found_any = True

        bdir = root / "boundaries"
        if bdir.is_dir():
            for p in bdir.glob("*.md"):
                if p.name.startswith(f"{scope}--") or p.stem.endswith(f"--{scope}"):
                    corpus_candidates.add(p)
                    found_any = True

        if not found_any:
            corpus_candidates.update(_walk_md_files(root))
            info.append(
                f"scope '{scope}' 가 MANIFEST/폴더에 없음 — 코퍼스 전체로 검색. "
                "도메인 미등록이면 /pilot:learn {진입점}"
            )
    else:
        corpus_candidates.update(_walk_md_files(root))

    include_candidates: set[Path] = set()
    if includes:
        resolved_project = project
        if resolved_project is None:
            if ol_mod is not None:
                try:
                    active = ol_mod.parse_state_md_active(workspace / "STATE.md")
                except Exception:
                    active = []
            else:
                active = []
            resolved_project = active[0] if active else None
            if resolved_project is None:
                info.append("--project 미지정 및 STATE.md 진행중 프로젝트 없음 — --include 는 workspace/ 직속 경로만 시도")

        for inc in includes:
            if inc.startswith("/") or ".." in Path(inc).parts:
                raise SearchError(f"--include 인자에 절대경로·'..' 사용 불가: {inc}", 2)
            found = False
            if resolved_project:
                proj_path = workspace / "projects" / resolved_project / inc
                if proj_path.is_dir():
                    include_candidates.update(_walk_md_files(proj_path))
                    found = True
                elif proj_path.is_file():
                    include_candidates.add(proj_path)
                    found = True
            if not found:
                ws_path = workspace / inc
                if ws_path.is_dir():
                    include_candidates.update(_walk_md_files(ws_path))
                    found = True
                elif ws_path.is_file():
                    include_candidates.add(ws_path)
                    found = True
            if not found:
                info.append(f"--include '{inc}' 대상 없음 — skip")

    # 수집 후 봉쇄 검증 (C1) — 코퍼스 후보는 root 안, include 후보는 workspace 안이어야 한다.
    root_resolved = root.resolve()
    ws_resolved = workspace.resolve()
    safe: list[Path] = []
    excluded = 0
    for p in corpus_candidates:
        try:
            ok = _is_within(p.resolve(), root_resolved)
        except OSError:
            ok = False
        if ok:
            safe.append(p)
        else:
            excluded += 1
    for p in include_candidates:
        try:
            ok = _is_within(p.resolve(), ws_resolved)
        except OSError:
            ok = False
        if ok:
            safe.append(p)
        else:
            excluded += 1
    if excluded:
        info.append(f"코퍼스 밖 링크 {excluded}건 제외")

    files = sorted(set(safe), key=lambda p: str(p.relative_to(workspace)))
    entry_files = sorted(set(entry_files), key=lambda p: str(p.relative_to(workspace)))
    return files, info, entry_files


# ── 검색 오케스트레이션 ─────────────────────────────────────────
def _display_path(abs_or_rel: Path) -> str:
    try:
        return os.path.relpath(abs_or_rel, start=Path.cwd())
    except ValueError:
        return str(abs_or_rel)


def _rel_to_root(p: Path, root: Path) -> str:
    return Path(os.path.relpath(p, start=root)).as_posix()


def search(
    *,
    workspace: Path,
    project: str | None,
    scope: str | None,
    includes: "list[str] | None",
    query_raw: str,
    limit: int,
) -> dict:
    query = parse_query(query_raw)
    if query.kind == "keywords" and not query.required and not query.optional:
        raise SearchError(
            "검색어가 비어 있거나 색인 불가 토큰(불용어·1글자)만 있습니다.", 2, show_usage=True
        )
    if limit < 1:
        raise SearchError(f"--limit 은 1 이상이어야 합니다: {limit}", 2)

    limit_info: list[str] = []
    if limit > MAX_LIMIT:
        limit_info.append(f"--limit {limit} 이 최대값 {MAX_LIMIT} 초과 — {MAX_LIMIT} 로 제한")
        limit = MAX_LIMIT

    root = workspace / "context"
    files, info, entry_files = collect_files(workspace, scope, includes, project)
    info = info + limit_info
    # 주의: root 는 **미해석(resolve() 하지 않은)** 경로를 그대로 쓴다. collect_files
    # 가 반환하는 files/entry_files 도 미해석 경로라 base 를 맞춰야 한다 — macOS 의
    # `/var` → `/private/var` 같은 심볼릭 링크가 낀 CWD/TMPDIR 에서 resolve() 된
    # root 를 base 로 relpath 를 구하면 공통 접두가 어긋나 "../../.." 투성이 상대
    # 경로가 나온다(select: 매칭·is_entry 비교가 전부 깨짐). resolve() 는 collect_files
    # 내부의 봉쇄 검증에서만 쓰고 여기서는 쓰지 않는다.
    entry_rel = {_rel_to_root(p, root) for p in entry_files}
    scope_fallback = any("가 MANIFEST/폴더에 없음" in i for i in info)

    sections: list[Section] = []
    for abs_path in files:
        rel = _rel_to_root(abs_path, root)
        try:
            text = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        sections.extend(split_sections(text, rel))

    if query.kind == "select":
        return _select_result(query, sections, root, scope, includes, info)

    memo: dict[str, list[str]] = {}
    all_tokens = list(dict.fromkeys(query.required + query.optional))
    token_hits: dict[str, int] = {t: 0 for t in all_tokens}
    scored: list[tuple[Section, int, list[str]]] = []
    for sec in sections:
        sc, matched = score_section(sec, query, memo=memo)
        for t in matched:
            if t in token_hits:
                token_hits[t] += 1
        if sc > 0:
            scored.append((sec, sc, matched))

    ranked = rank(scored, limit, entry_rel=entry_rel)

    results = []
    for sec, sc, matched in ranked:
        abs_p = (root / sec.file)
        display_file = _display_path(abs_p)
        results.append(
            {
                "file": display_file,
                "heading": sec.heading,
                "level": sec.level,
                "line_start": sec.line_start,
                "line_end": sec.line_end,
                "score": sc,
                "matched": matched,
                "snippet": build_snippet(sec, matched),
                "read_hint": build_read_hint(sec, display_file),
            }
        )

    zero_hit = None
    if not results:
        zero_hit = build_zero_hit(query_raw, query, token_hits, scope, scope_fallback)

    return {
        "query": query_raw,
        "root": str(root),
        "scope": scope,
        "include": includes or [],
        "candidates": len(scored),
        "returned": len(results),
        "results": results,
        "info": info,
        "zero_hit": zero_hit,
    }


def _select_result(
    query: Query, sections: list[Section], root: Path,
    scope: str | None, includes: "list[str] | None", info: list[str],
) -> dict:
    select_path = (query.select_path or "").strip()
    if select_path.startswith("workspace/context/"):
        select_path = select_path[len("workspace/context/") :]
    elif select_path.startswith("context/"):
        select_path = select_path[len("context/") :]
    if select_path.startswith("/") or ".." in Path(select_path).parts:
        raise SearchError(f"select: 대상에 절대경로·'..' 사용 불가: {query.select_path}", 2)

    display_query = "select:" + select_path + (f"#{query.select_heading}" if query.select_heading else "")
    matches = [s for s in sections if s.file == select_path]

    results = []
    zero_hit = None
    if matches:
        for sec in matches:
            if query.select_heading and query.select_heading.lower() not in sec.heading.lower():
                continue
            display_file = _display_path(root / sec.file)
            results.append(
                {
                    "file": display_file, "heading": sec.heading, "level": sec.level,
                    "line_start": sec.line_start, "line_end": sec.line_end,
                    "score": None, "matched": [],
                    "snippet": build_snippet(sec, []),
                    "read_hint": build_read_hint(sec, display_file),
                }
            )
        if not results:
            zero_hit = {
                "guidance": [
                    f"'{select_path}' 에 헤딩 '{query.select_heading}' 을 포함하는 섹션 없음 — "
                    "select_heading 을 좁히거나 제거"
                ]
            }
    else:
        all_files = sorted({s.file for s in sections})
        target = set(path_tokens(select_path))
        scored_suggestions = [
            (-(len(target & set(path_tokens(f)))), f)
            for f in all_files
            if target & set(path_tokens(f))
        ]
        scored_suggestions.sort()
        zero_hit = {"suggestions": [f for _, f in scored_suggestions[:3]]}

    return {
        "query": display_query,
        "root": str(root),
        "scope": scope,
        "include": includes or [],
        "candidates": len(results),
        "returned": len(results),
        "results": results,
        "info": info,
        "zero_hit": zero_hit,
    }


# ── 출력 렌더링 ─────────────────────────────────────────────────
def render_md(result: dict) -> str:
    lines: list[str] = []
    scope_display = result["scope"] or "(전체)"
    lines.append(
        f"검색: `{result['query']}` · scope={scope_display} · "
        f"후보 {result['candidates']}건 중 {result['returned']}건 표시"
    )
    lines.append("")

    if result["results"]:
        lines.append("| # | file | heading | lines | score | matched |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for i, r in enumerate(result["results"], 1):
            score_display = r["score"] if r["score"] is not None else "-"
            matched_display = ", ".join(r["matched"]) if r["matched"] else "-"
            lines.append(
                f"| {i} | {r['file']} | {r['heading']} | "
                f"{r['line_start']}-{r['line_end']} | {score_display} | {matched_display} |"
            )
        lines.append("")
        for i, r in enumerate(result["results"], 1):
            if r["snippet"]:
                lines.append(f"{i}. > {r['snippet']}")
            lines.append(f"   {r['read_hint']}")
        lines.append("")

    for msg in result["info"]:
        lines.append(f"[INFO] {msg}")

    zh = result["zero_hit"]
    if zh is not None:
        if not result["results"]:
            lines.append("0건")
        if zh.get("token_hits"):
            hits_str = ", ".join(f"{t}={c}" for t, c in zh["token_hits"].items())
            lines.append(f"토큰별 일치 섹션 수: {hits_str}")
        for g in zh.get("guidance", []):
            lines.append(f"- {g}")
        for s in zh.get("suggestions", []):
            lines.append(f"- 후보: {s}")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────
def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-search.py",
        description="workspace/context/ 마크다운 지식 파일을 섹션 단위로 검색하는 결정적 랭커.",
    )
    parser.add_argument(
        "query",
        help="검색어(첫 위치 인자로 지정 — --include 뒤에 두면 nargs='+' 에 흡수됨). "
        "select:{path}[#heading] · '키워드 나열' · '+필수어 선택어' 3형식 지원.",
    )
    parser.add_argument("--workspace", default="workspace", help="workspace 경로 (기본: workspace)")
    parser.add_argument("--project", default=None, help="미지정 시 STATE.md 진행중 프로젝트")
    parser.add_argument("--scope", default=None, help="도메인 이름 — {root}/{scope}/ 등으로 코퍼스 축소")
    parser.add_argument("--include", nargs="+", default=None, help="부속 문서 경로 (예: features/ docs/)")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"기본 {DEFAULT_LIMIT}, 최대 {MAX_LIMIT}")
    parser.add_argument("--format", choices=("md", "json"), default="md", help="출력 형식 (기본 md)")
    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = _build_argparser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2

    try:
        result = search(
            workspace=Path(args.workspace),
            project=args.project,
            scope=args.scope,
            includes=args.include,
            query_raw=args.query,
            limit=args.limit,
        )
    except SearchError as exc:
        print(exc.message, file=sys.stderr)
        if exc.show_usage:
            parser.print_usage(sys.stderr)
        return exc.exit_code

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_md(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
