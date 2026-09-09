#!/usr/bin/env python3
"""
pilot context-search — 섹션 단위 결정적 검색 도구.

workspace/context/ 마크다운 지식 파일을 H2·H3 섹션 단위로 색인하고, 질의 토큰과
헤딩·경로·인용·description·본문 신호를 채점해 순위가 매겨진 섹션 목록을 반환한다.
에이전트가 본문 파일 전체 Read·무차별 Grep 대신 사용하는 부분 로드 진입점 — 권장 흐름은
탐색(`--format manifest`) → 에이전트 선별 → 주입(`select:… --inject`) 3단계 (wrapper-protocol §6).

Usage:
    python3 pilot/tools/context-search.py "<질의>" [--workspace PATH] [--project NAME]
        [--scope DOMAIN] [--include PATH ...] [--limit N] [--format md|json|manifest]
        [--inject] [--max-bytes N]

    질의는 반드시 첫 위치 인자로 지정한다 — `--include` 는 nargs="+" 라 뒤에 두면
    질의 문자열을 흡수해버린다.

질의 3형식:
    select:{path}[#{헤딩 일부}][,{path}[#{헤딩 일부}]...]
                                  경로(및 헤딩 일부)를 직접 지정 — 점수 없이 반환. 쉼표로
                                  여러 대상. 경로는 코퍼스 루트 기준이며 md·manifest 에 표시된
                                  경로(CWD 기준)를 그대로 붙여 넣어도 된다 — `--include` 부속
                                  문서도 표시 경로나 `../projects/…` 로 지정 가능(봉쇄: workspace
                                  안). 헤딩은 백틱·`*`·`_` 를 무시한 부분 문자열 대조. 쉘에서는
                                  인자를 작은따옴표로 감싼다(백틱·`$` 치환 방지) — `#` 뒤가
                                  비어 오면 파일 전체 + INFO.
    키워드 나열                    공백으로 구분된 선택 토큰 (OR 성격)
    +필수어 선택어                 `+` 접두 토큰은 사전필터 겸 채점 대상(D6)

    토큰이 경로처럼 보이면(`/` 포함 + 확장자) 인용 경로 일치와 frontmatter `sources` glob
    일치를 자동 가중한다 — "이 소스 파일을 다루는 지식 섹션" 을 찾는 역방향 질의.

점수표 (토큰마다 신호별 최대 1회 합산 — 빈도는 반영하지 않는다):
    헤딩 토큰 정확 일치              10
    파일 경로 세그먼트 일치           8
    인용 경로 세그먼트 일치           6
    헤딩 토큰 부분 일치               5
    frontmatter description 일치     4
    본문 단어경계 일치                2
    경로형 질의 ↔ 인용 경로 suffix    6 (질의 경로마다 1회)
    경로형 질의 ↔ sources glob        6 (질의 경로마다 1회)

    한글 복합어: 질의의 인접 2~3 한글 단어 연쇄(`선발송 접수 상태`)가 본문·description 에 붙어
    있으면(`선발송접수`·`선발송접수상태`) 구성 토큰이 body/description 신호를 받고, 헤딩 토큰이
    연쇄와 같으면 구성 토큰 전부 정확 일치(10). 4자 이상 순수 한글 질의 토큰(`진입파일`)은
    띄어 쓴 텍스트(`진입 파일`)와도 대조된다 — 본문·description 은 해당 신호, 헤딩은 부분
    일치(5; 헤딩의 한글 토큰이 2글자부터 질의 토큰에 포함될 때도). 같은 토큰·같은 신호는 한
    번만 — 붙여 쓴 텍스트와 띄어 쓴 텍스트의 점수가 같다. 질의 쪽 조사는 흡수하지 않는다
    (조사 붙은 4자+ 토큰이 헤딩에서 부분 일치할 수는 있다 — 본문은 조사 제거 재질의).
    frontmatter `type`·`domain` 은 점수에 쓰지 않고 출력 필드로만 노출한다.

    level 1 섹션(서문·H1-only·헤딩 없는 파일)은 헤딩 신호(10/5)를 받지 않는다 —
    경로·인용·description·본문 신호만 채점된다.

출력 스키마 (--format json):
    {"query", "root", "scope", "include": [...], "candidates": N, "returned": k,
     "results": [{"file", "heading", "level", "line_start", "line_end", "score",
                  "matched", "snippet", "read_hint",
                  "type"?, "domain"?,                                  # frontmatter 값이 있을 때만
                  "text"?, "truncated"?, "inject_rest"?, "inject_skip"?}],  # --inject 시
     "info": [...], "zero_hit": {...} | null}

    --format md (기본): 1줄 헤더 + 결과 표 + 섹션별 snippet/read_hint + INFO·0건 안내.
    --format manifest: 후보당 1줄 `[#n] score [type] | file :: heading | L{s}-{e} | {age}d |
        matched: a,b | snippet≤80` — 2차 선별 입력. age 는 파일 mtime 표기 전용(점수·정렬 불변)이며
        후보가 전부 같은 값이면(clone 직후) `-` 로 표기해 최신성으로 오독되지 않게 한다.
    --inject: 결과 순서대로 본문을 싣는다 — md/manifest 는 `<context-snippet file heading lines>`
        블록, json 은 `text`. `--max-bytes`(기본 12,000 · 상한 24,000) 는 md/manifest **렌더
        총량 근사**(헤더·후보 줄·래퍼 포함 — Bash 도구 출력 스왑 임계 ≈30,000B 실측 아래) ·
        섹션당 400줄, 잘리면 `[잘림 — 나머지: Read …]`, 앞선 결과가 완전히 덮는 하위 섹션은
        중복 주입 생략. json 은 이스케이프·snippet 중복으로 ≈1.5× 크므로 CLI 가 json + --inject
        의 예산을 65% 로 축소하고 INFO 로 알린다(상한 근처에선 md/manifest 권장). 헤딩 줄만
        들어갈 예산이면 그 섹션은 생략(`inject_skip`). 키워드 질의 + --inject 는 --limit 미지정 시 3.

Exit:
    0 — 성공 (0건 포함 — 실패가 아니라 상태 안내)
    2 — 빈 질의·토큰 전멸 / scope·project·include traversal / select 대상이 workspace 밖 /
        --limit < 1 / --max-bytes < 1 / --format 오류 / 코퍼스 루트 부재

제약:
    - 지식 파일은 읽기 전용 — 어떤 경로도 workspace/context/ 를 쓰지 않는다.
    - 같은 코퍼스·질의 → 같은 출력·순서 (결정적 — set 순회 결과를 출력에 노출하지 않는다).
      manifest 의 age 표기만 예외(파일 mtime·실행 시각을 표시하는 정보이지 순위 근거가 아니다).
    - 표준 라이브러리만: re · pathlib · json · argparse · os · sys · time · html · fnmatch ·
      dataclasses · importlib.util (형제 모듈 지연 로드).
    - 캐시 없음 = 실행 간 영속 캐시 없음(파일·mtime 키 캐시 금지). 실행 1회 안에서만
      쓰는 memo(예: 인용 경로 토큰화 결과)는 허용한다.
"""

from __future__ import annotations

import argparse
import functools
import html
import importlib.util
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ── 상수 ────────────────────────────────────────────────────────
DEFAULT_LIMIT = 5
MAX_LIMIT = 20
SNIPPET_CHARS = 240
LARGE_SECTION_LINES = 400
INJECT_DEFAULT_LIMIT = 3  # 키워드 질의 + --inject 에서 --limit 미지정 시 (E9)
INJECT_MAX_BYTES_DEFAULT = 12_000  # md/manifest 렌더 총량 근사 기준 (C8)
# Bash 도구 출력 스왑 임계 실측(2026-09-08, Claude Code 원격 세션): 28,000B 인라인 · 31,200B 파일 스왑.
# 24,000 은 INFO·[잘림] 줄 여유를 둔 렌더 총량 상한 — json 은 이스케이프·snippet 중복으로 1.3~1.7× 크다.
INJECT_MAX_BYTES_CAP = 24_000
RENDER_RESERVE_BYTES = 600  # 헤더·INFO 줄 여유 (C8)
JSON_INJECT_BUDGET_FACTOR = 0.65  # json 렌더는 이스케이프·snippet 중복으로 md 의 ≈1.5× — CLI 가 예산을 축소 (C8)
MANIFEST_SNIPPET_CHARS = 80

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
    # select: 다중 대상 (E8) — `select:a.md#h1,b.md#h2`. 첫 대상은 select_path/select_heading 에도 복사.
    select_targets: list[tuple[str, str | None]] = field(default_factory=list)
    # 한글 결합어 후보 (E3·C11) — 원문 인접 2~3단어 연쇄 (t1, t2[, t3]). 텍스트에 이어 붙어 있으면 매칭(E2).
    compounds: list[tuple[str, ...]] = field(default_factory=list)


_PATH_LIKE_RE = re.compile(r"\.[A-Za-z0-9]{1,5}$")


def parse_query(raw: str) -> Query:
    raw = raw.strip()
    if raw.startswith("select:"):
        rest = raw[len("select:") :]
        targets: list[tuple[str, str | None]] = []
        for part in rest.split(","):
            part = part.strip()
            if not part:
                continue
            heading: str | None
            if "#" in part:
                path_part, heading_part = part.split("#", 1)
                # "" = '#' 뒤가 빈 경우 — 쉘이 백틱·$ 를 치환해 헤딩을 지운 사고의 흔적(C1).
                # 헤딩 생략과 구분해 _select_result 가 INFO 를 낸다.
                heading = heading_part.strip()
            else:
                path_part, heading = part, None
            targets.append((path_part.strip(), heading))
        if not targets:
            targets = [("", None)]
        return Query(
            kind="select",
            optional=[],
            required=[],
            raw_paths=[],
            select_path=targets[0][0],
            select_heading=targets[0][1] or None,
            select_targets=targets,
        )

    optional: list[str] = []
    required: list[str] = []
    raw_paths: list[str] = []
    word_tokens: list[list[str] | None] = []  # 결합어 판정용 — 경로형 단어는 None
    for word in raw.split():
        is_required = word.startswith("+") and len(word) > 1
        w = word[1:] if is_required else word
        if "/" in w and _PATH_LIKE_RE.search(w):
            raw_paths.append(w)
            toks = path_tokens(w)
            word_tokens.append(None)
        else:
            toks = tokenize(w)
            word_tokens.append(toks)
        (required if is_required else optional).extend(toks)
    return Query(
        kind="keywords", optional=optional, required=required, raw_paths=raw_paths,
        compounds=_adjacent_hangul_chains(word_tokens),
    )


def _is_pure_hangul(token: str) -> bool:
    return bool(token) and all("가" <= ch <= "힣" for ch in token)


COMPOUND_MAX_WORDS = 3  # E3·C11 — 결합어 후보는 인접 2~3단어 연쇄


def _adjacent_hangul_chains(word_tokens: "list[list[str] | None]") -> list[tuple[str, ...]]:
    """E3·C11 — 원문 공백 분리 단어의 인접 2~3단어 연쇄 중 **모두 순수 한글 토큰 1개씩**일 때만
    결합어 후보(`선발송 접수 상태` → (선발송,접수)·(선발송,접수,상태)·(접수,상태)). 불용어·1글자
    (토큰 0개)·ASCII·경로형 단어가 끼면 연쇄가 끊긴다(`선발송 및 접수` 는 결합어가 아니다).
    순서 보존 dedupe."""
    singles: list[str | None] = [
        w[0] if (w and len(w) == 1 and _is_pure_hangul(w[0])) else None for w in word_tokens
    ]
    chains: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for i in range(len(singles)):
        for n in range(2, COMPOUND_MAX_WORDS + 1):
            window = singles[i : i + n]
            if len(window) < n or any(t is None for t in window):
                break
            chain = tuple(t for t in window if t is not None)
            if chain not in seen:
                seen.add(chain)
                chains.append(chain)
    return chains


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
    # frontmatter 메타 (E6) — description·domain·type·sources 중 값이 있는 키만. 점수에는
    # sources(E7 glob 보너스)만 쓰고 type·domain 은 출력 필드로만 노출한다.
    meta: dict = field(default_factory=dict)


_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_OPEN_RE = re.compile(r"^\s*(```+|~~~+)")
FRONTMATTER_SCALAR_KEYS = ("description", "domain", "type")
FRONTMATTER_LIST_KEYS = ("sources",)
_FM_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
_FM_LIST_ITEM_RE = re.compile(r"^-\s+(.*)$")
_FM_BLOCK_INDICATORS = (">", ">-", ">+", "|", "|-", "|+")


def _strip_fm_value(value: str) -> str:
    """스칼라 값 정리(E6) — 따옴표로 시작하면 짝 따옴표 안만, 아니면 ` #` 이후 주석을 떼고 trim.
    #29 예시의 `type: services   # index | routes | …` 가 enum 8단어로 번지지 않게."""
    value = value.strip()
    if value and value[0] in "\"'":
        end = value.find(value[0], 1)
        return value[1:end] if end != -1 else value[1:]
    cut = re.search(r"\s#", value)
    if cut:
        value = value[: cut.start()]
    return value.strip()


def _parse_fm_list(value: str) -> list[str]:
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        return [x for x in (_strip_fm_value(p) for p in v[1:-1].split(",")) if x]
    s = _strip_fm_value(v)
    return [s] if s else []


def parse_frontmatter(fm_lines: list[str]) -> dict:
    """frontmatter(`---` 사이) 에서 description·domain·type(스칼라)·sources(리스트)를 읽는다(E6).
    YAML 파서가 아니다 — 다루는 것: `key: value` · 트레일링 ` # 주석` · 따옴표 · 블록 리스트
    (`- item`) · 인라인 리스트(`[a, b]`) · 접힘 스칼라(`>-` 다음 들여쓴 첫 줄만). 미지 키는
    무시하고 값 없는 키는 결과에 없다 — frontmatter 없는 코퍼스의 출력이 바뀌지 않게."""
    meta: dict = {}
    current_list: str | None = None
    pending_scalar: str | None = None
    for raw in fm_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pending_scalar is not None:
            if raw[:1].isspace():
                v = _strip_fm_value(stripped)
                if v:
                    meta[pending_scalar] = v
                pending_scalar = None
                continue
            pending_scalar = None
        im = _FM_LIST_ITEM_RE.match(stripped)
        if im and current_list is not None:
            v = _strip_fm_value(im.group(1))
            if v:
                meta[current_list].append(v)
            continue
        current_list = None
        km = _FM_KEY_RE.match(stripped)
        if not km:
            continue
        key = km.group(1).lower()
        value = (km.group(2) or "").strip()
        if value.startswith("#"):
            value = ""
        if key in FRONTMATTER_SCALAR_KEYS:
            if value in _FM_BLOCK_INDICATORS:
                pending_scalar = key
                continue
            v = _strip_fm_value(value)
            if v:
                meta[key] = v
        elif key in FRONTMATTER_LIST_KEYS:
            items = _parse_fm_list(value) if value else []
            meta[key] = items
            if not items:
                current_list = key
    for key in FRONTMATTER_LIST_KEYS:
        if key in meta and not meta[key]:
            del meta[key]
    return meta


def split_sections(text: str, rel_path: str) -> list[Section]:
    """H2·H3 를 색인 헤딩으로 섹션 분할. frontmatter 제외 + description 보관,
    펜스(``` / ~~~) 안의 `#` 는 헤딩으로 인식하지 않는다. D7: 첫 H2/H3 이전
    구간은 level 1 서문 섹션(본문이 비면 생략), H2/H3 이 전혀 없으면 파일 전체가
    level 1 섹션 1개(H1 있으면 그 텍스트, 없으면 `(파일 전체)`)."""
    lines = text.splitlines()
    n = len(lines)

    meta: dict = {}
    content_start = 0
    if lines and lines[0].strip() == "---":
        close_idx = None
        for i in range(1, n):
            if lines[i].strip() == "---":
                close_idx = i
                break
        if close_idx is not None:
            meta = parse_frontmatter(lines[1:close_idx])
            content_start = close_idx + 1
    description: str | None = meta.get("description")

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
                body_lines=body_lines, description=description, meta=meta,
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
                body_lines=preface_body, description=description, meta=meta,
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
                body_lines=lines[idx + 1 : end_idx], description=description, meta=meta,
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


@functools.lru_cache(maxsize=4096)
def _boundary_regex(token: str) -> "re.Pattern[str]":
    # 실행 내 memo(C6) — 토큰당 1회 컴파일. 프로세스 메모리에만 남고 실행 간 영속 캐시가 아니다.
    return re.compile(boundary_pattern(token))


def boundary_search(token: str, text_lc: str) -> "re.Match[str] | None":
    if token not in text_lc:
        return None  # C6·C11 — 리터럴이 없으면 정규식 없이 거부 (경계 패턴은 리터럴 + 전후 lookaround 뿐)
    return _boundary_regex(token).search(text_lc)


REVERSE_MIN_CHARS = 4  # E4 — 역방향(붙여 쓴 질의 ↔ 띄어 쓴 텍스트) 대조를 시도하는 한글 토큰 최소 길이


def _reverse_candidate(token: str) -> bool:
    return len(token) >= REVERSE_MIN_CHARS and _is_pure_hangul(token)


def flex_pattern(token: str) -> str:
    """E4 — 한글 토큰의 글자 사이에 공백을 허용하는 좌측 경계 패턴
    (`진입파일` ↔ `진입 파일`). ASCII 에는 쓰지 않는다(`payload` ≠ `pay load`).
    (계획서 E4 의 'compact' 방식은 공백을 지우면 좌측 경계도 사라져 부적합 — flex 정규식으로 대체.)"""
    return f"(?<!{WORD})" + r"\s*".join(re.escape(ch) for ch in token)


@functools.lru_cache(maxsize=4096)
def _flex_regex(token: str) -> "re.Pattern[str]":
    return re.compile(flex_pattern(token))


def flex_search(token: str, text_lc: str) -> "re.Match[str] | None":
    if not text_lc or token[0] not in text_lc:
        return None  # C6 — 첫 글자가 본문에 없으면 정규식 없이 거부
    return _flex_regex(token).search(text_lc)


@functools.lru_cache(maxsize=1024)
def _glob_regex(glob: str) -> "re.Pattern[str]":
    """E7·C7 — frontmatter `sources` glob 을 gitignore 의미로 정규식화 (#30 `.claude/rules paths:`
    와 같은 집합을 가리키게): `*`·`?` 는 `/` 를 넘지 않고, `**` 만 경로를 가로지른다. 슬래시가
    든 패턴은 루트 앵커(`app/services/*.rb` 는 `app/services/wms/x.rb` 와 불일치), 슬래시 없는
    패턴(`*.rb`·`wms`)은 어느 깊이의 이름과도 맞는다. 디렉토리(`app/x`·`app/x/`)는 하위 전부."""
    g = glob.strip()
    if g.startswith("/"):
        g = g[1:]
    g = g.rstrip("/")
    anchored = "/" in g
    out: list[str] = []
    i = 0
    while i < len(g):
        if g.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if g.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        ch = g[i]
        if ch == "*":
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        elif ch == "[":
            j = g.find("]", i + 1)
            if j == -1:
                out.append(re.escape(ch))
            else:
                out.append("[" + g[i + 1 : j].replace("\\", "\\\\") + "]")
                i = j
        else:
            out.append(re.escape(ch))
        i += 1
    prefix = "^" if anchored else "(?:^|.*/)"
    return re.compile(prefix + "".join(out) + "(?:/.*)?$")


def _source_glob_match(path: str, glob: str) -> bool:
    g = glob.strip().rstrip("/")
    if not g or g == "/":
        return False
    return _glob_regex(glob).match(path) is not None


def score_text(
    query: Query,
    *,
    heading: str,
    body: str,
    path_tokens: "tuple[str, ...] | set[str] | list[str]" = (),
    citation_tokens: "tuple[str, ...] | set[str] | list[str]" = (),
    citation_paths: "tuple[str, ...] | list[str]" = (),
    description: str | None = None,
    sources: "tuple[str, ...] | list[str]" = (),
) -> tuple[int, list[str]]:
    """문자열 기반 채점 진입점 (confluence.py `search_docs` 재사용 대상, C4).

    토큰마다 신호별 최대 1회 합산. `heading=""` 로 호출하면 헤딩 신호(10/5) 가
    통째로 꺼진다 — level 1 섹션(서문 등)에 score_section 이 이렇게 호출한다(C2).
    `required` 토큰 중 하나라도 이 텍스트 조합에서 신호가 0 이면 전체 0점(사전필터,
    D6) — 단 진단용 `matched` 는 개별 신호가 있던 토큰을 그대로 반환한다.
    """
    heading_tokens = set(tokenize(heading)) if heading else set()
    heading_lc = heading.lower() if heading else ""
    path_set = set(path_tokens)
    citation_set = set(citation_tokens)
    body_lc = body.lower() if body else ""
    desc_lc = description.lower() if description else None

    all_tokens = list(dict.fromkeys(list(query.required) + list(query.optional)))
    token_score: dict[str, int] = {}
    token_signals: dict[str, set[str]] = {}  # 토큰별 이미 받은 신호 — 결합어 중복 가산 방지(E2)
    for t in all_tokens:
        s = 0
        sig: set[str] = set()
        exact = t in heading_tokens
        if exact:
            s += SCORE["heading_exact"]
            sig.add("heading_exact")
        if t in path_set:
            s += SCORE["path"]
        if t in citation_set:
            s += SCORE["citation"]
        partial = not exact and any(t in h for h in heading_tokens)
        if partial:
            s += SCORE["heading_partial"]
            sig.add("heading_partial")
        if desc_lc is not None and boundary_search(t, desc_lc):
            s += SCORE["description"]
            sig.add("description")
        if body_lc and boundary_search(t, body_lc):
            s += SCORE["body"]
            sig.add("body")
        if _reverse_candidate(t):
            # E4 역방향 — 붙여 쓴 한글 질의 토큰(≥4자) ↔ 띄어 쓴 헤딩·description·본문.
            # 헤딩은 글자 사이 공백 허용 대조, 또는 헤딩의 한글 토큰이 질의 토큰에 포함되면 부분 일치.
            if heading_lc and not exact and not partial and (
                flex_search(t, heading_lc)
                or any(_is_pure_hangul(h) and h in t for h in heading_tokens)
            ):
                s += SCORE["heading_partial"]
                sig.add("heading_partial")
            if desc_lc is not None and "description" not in sig and flex_search(t, desc_lc):
                s += SCORE["description"]
                sig.add("description")
            if body_lc and "body" not in sig and flex_search(t, body_lc):
                s += SCORE["body"]
                sig.add("body")
        if s > 0:
            token_score[t] = s
        token_signals[t] = sig

    # E2·C11 결합어(인접 2~3단어) — 띄어 쓴 질의 ↔ 붙여 쓴 본문·description·헤딩. 구성 토큰이
    # 그 신호를 이미 받았으면 가산하지 않는다(붙여 쓴 텍스트 = 띄어 쓴 텍스트 점수 — 역전 없음).
    # 헤딩 토큰이 결합어와 같으면 구성 토큰 전부를 정확 일치(10)로 올린다(부분 일치 5 는 회수).
    for chain in query.compounds:
        compound = "".join(chain)
        for text_lc, signal in ((body_lc, "body"), (desc_lc, "description")):
            if not text_lc or boundary_search(compound, text_lc) is None:
                continue
            for t in chain:
                sig = token_signals.setdefault(t, set())
                if signal in sig:
                    continue
                sig.add(signal)
                token_score[t] = token_score.get(t, 0) + SCORE[signal]
        if compound in heading_tokens:
            for t in chain:
                sig = token_signals.setdefault(t, set())
                if "heading_exact" in sig:
                    continue
                gain = SCORE["heading_exact"] - (SCORE["heading_partial"] if "heading_partial" in sig else 0)
                sig.add("heading_exact")
                token_score[t] = token_score.get(t, 0) + gain

    matched_raw_paths: list[str] = []
    path_bonus = 0
    for p in query.raw_paths:
        hit = False
        for c in citation_paths:
            if c == p or c.endswith("/" + p):
                path_bonus += SCORE["citation"]
                hit = True
                break
        # E7 — frontmatter `sources` glob 이 질의 경로를 덮으면 인용 경로와 같은 층위의 파일 보너스
        # 1회. 세그먼트 토큰 매칭은 하지 않는다(path·citation 신호와 중복이라 파일 단위 점수만 부풀린다).
        if any(_source_glob_match(p, g) for g in sources):
            path_bonus += SCORE["citation"]
            hit = True
        if hit:
            matched_raw_paths.append(p)

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
        sources=section.meta.get("sources", ()),
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
        if m is None and _reverse_candidate(t):
            m = flex_search(t, lc)  # E5 — 역방향 일치 위치도 스니펫 창의 기준이 된다
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
        if any(_reverse_candidate(t) for t in zero_korean):
            guidance.append(
                "한글 복합어는 붙여쓰기·띄어쓰기 양쪽을 자동 대조한다 — 그래도 0 이면 "
                "다른 표현(동의어·영문명)으로 재질의"
            )
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
    inject: bool = False,
    max_bytes: int = INJECT_MAX_BYTES_DEFAULT,
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
    if inject:
        if max_bytes < 1:
            raise SearchError(f"--max-bytes 는 1 이상이어야 합니다: {max_bytes}", 2)
        if max_bytes > INJECT_MAX_BYTES_CAP:
            limit_info.append(
                f"--max-bytes {max_bytes} 이 상한 {INJECT_MAX_BYTES_CAP} 초과 — "
                f"{INJECT_MAX_BYTES_CAP} 로 제한"
            )
            max_bytes = INJECT_MAX_BYTES_CAP

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
        return _select_result(
            query, sections, root, scope, includes, info,
            inject=inject, max_bytes=max_bytes, workspace=workspace,
        )

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

    results = [_result_entry(sec, root, sc, matched) for sec, sc, matched in ranked]
    if inject:
        info = info + _apply_inject(results, [sec for sec, _sc, _m in ranked], max_bytes)

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


def _result_entry(sec: Section, root: Path, score: int | None, matched: list[str]) -> dict:
    """결과 항목 1개 — 키워드·select 경로가 같은 키 순서를 쓴다(JSON 바이트 동일성의 근거).
    `type`·`domain` 은 frontmatter 에 값이 있을 때만 붙는다(E6 — 없는 코퍼스의 출력 불변)."""
    display_file = _display_path(root / sec.file)
    entry = {
        "file": display_file,
        "heading": sec.heading,
        "level": sec.level,
        "line_start": sec.line_start,
        "line_end": sec.line_end,
        "score": score,
        "matched": matched,
        "snippet": build_snippet(sec, matched),
        "read_hint": build_read_hint(sec, display_file),
    }
    for key in ("type", "domain"):
        if sec.meta.get(key):
            entry[key] = sec.meta[key]
    return entry


def _heading_key(text: str) -> str:
    """select 헤딩 대조 키 — 백틱·강조 마커를 벗기고 소문자화(C1). 코퍼스 헤딩 다수가
    `` `/pilot:x` `` 꼴이라 에이전트가 백틱을 뺀 안쪽 텍스트만 넘겨도 맞아야 한다."""
    return text.replace("`", "").replace("*", "").replace("_", "").strip().lower()


def _normalize_select_path(
    raw: str, root: Path, workspace: Path, known_files: "set[str]"
) -> str:
    """select: 대상을 코퍼스 루트 기준 상대경로로 정규화(E8·C4). 받아들이는 형태:
    루트 기준(`pilot/index.md`) · `workspace/context/…`·`context/…` 접두 · md/manifest 표시
    경로(CWD 기준 — 코퍼스 파일과 `--include` 부속 문서 모두) · include 후보의 루트 기준
    표기(`../projects/…`). 후보 해석 중 실제 색인된 파일(`known_files`)과 맞는 첫 것을 쓴다.
    봉쇄: 결과가 workspace 안이어야 한다 — collect_files 와 같은 기준(`..` 자체는 include
    후보 때문에 허용, workspace 밖으로 나가면 거부)."""
    raw_path = raw.strip().replace("\\", "/")
    if raw_path.startswith("/"):
        raise SearchError(f"select: 대상에 절대경로 사용 불가: {raw}", 2)
    candidates: list[str] = [raw_path]
    root_display = _display_path(root).replace("\\", "/").rstrip("/")
    for prefix in (root_display + "/", "workspace/context/", "context/"):
        if prefix != "/" and raw_path.startswith(prefix):
            candidates.append(raw_path[len(prefix) :])
    try:
        # CWD 기준 표시 경로 → 루트 기준 (`workspace/projects/P/x.md` → `../projects/P/x.md`)
        candidates.append(Path(os.path.relpath(raw_path, start=str(root))).as_posix())
    except ValueError:
        pass
    select_path = next((c for c in candidates if c in known_files), None)
    if select_path is None:
        select_path = candidates[1] if len(candidates) > 2 else raw_path  # 접두를 뗀 형태로 후보 제안
    try:
        inside = _is_within((root / select_path).resolve(), workspace.resolve())
    except OSError:
        inside = False
    if not inside:
        raise SearchError(f"select: 대상이 workspace 밖입니다 (절대경로·'..' 탈출 불가): {raw}", 2)
    return select_path


def _select_result(
    query: Query, sections: list[Section], root: Path,
    scope: str | None, includes: "list[str] | None", info: list[str],
    inject: bool = False, max_bytes: int = INJECT_MAX_BYTES_DEFAULT,
    workspace: Path | None = None,
) -> dict:
    """`select:` 결과. 대상이 여러 개(E8)면 대상 순서대로 이어 붙이고 같은 섹션은 1회만.
    일부 대상만 없으면 결과는 내고 INFO 로 알린다. 전부 없으면 zero_hit — 단일 대상의
    기존 형태(파일 부재 `suggestions` / 헤딩 부재 `guidance`)를 그대로 유지한다.
    헤딩 대조는 `_heading_key`(백틱·강조 무시) 부분 문자열. `#` 뒤가 빈 대상은 파일 전체를
    돌려주되 INFO 로 쉘 인용 사고 가능성을 알린다(C1 — 무음 전체 주입 차단)."""
    targets = query.select_targets or [(query.select_path or "", query.select_heading)]
    if workspace is None:
        workspace = root.parent
    known_files = {s.file for s in sections}
    all_files: list[str] | None = None

    results: list[dict] = []
    picked: list[Section] = []
    seen: set[tuple[str, int]] = set()
    display_parts: list[str] = []
    guidance: list[str] = []
    suggestions: list[str] = []
    select_info: list[str] = []

    for raw_path, heading in targets:
        select_path = _normalize_select_path(raw_path, root, workspace, known_files)
        display_parts.append(select_path + (f"#{heading}" if heading else ""))
        heading_key = _heading_key(heading) if heading else ""
        if heading is not None and not heading_key:
            select_info.append(
                f"select 대상 '{select_path}': '#' 뒤 헤딩이 비어 파일 전체를 반환 — "
                "쉘 인용 확인 (백틱·$ 이 든 헤딩은 작은따옴표로 감싼다)"
            )
        matches = [s for s in sections if s.file == select_path]
        if matches:
            found = False
            for sec in matches:
                if heading_key and heading_key not in _heading_key(sec.heading):
                    continue
                found = True
                key = (sec.file, sec.line_start)
                if key in seen:
                    continue
                seen.add(key)
                results.append(_result_entry(sec, root, None, []))
                picked.append(sec)
            if not found:
                guidance.append(
                    f"'{select_path}' 에 헤딩 '{heading}' 을 포함하는 섹션 없음 — "
                    "select_heading 을 좁히거나 제거"
                )
        else:
            if all_files is None:
                all_files = sorted({s.file for s in sections})
            target = set(path_tokens(select_path))
            scored_suggestions = [
                (-(len(target & set(path_tokens(f)))), f)
                for f in all_files
                if target & set(path_tokens(f))
            ]
            scored_suggestions.sort()
            top = [f for _n, f in scored_suggestions[:3]]
            for f in top:
                if f not in suggestions:
                    suggestions.append(f)
            select_info.append(
                f"select 대상 없음: '{select_path}'" + (f" — 후보: {', '.join(top)}" if top else "")
            )

    zero_hit: dict | None = None
    if results:
        info = info + select_info + guidance  # 일부 대상 부재 — 결과는 내고 INFO 로만
    else:
        zero_hit = {}
        if guidance:
            zero_hit["guidance"] = guidance
        if suggestions or not guidance:
            zero_hit["suggestions"] = suggestions[:3]
    if inject:
        info = info + _apply_inject(results, picked, max_bytes)

    return {
        "query": "select:" + ",".join(display_parts),
        "root": str(root),
        "scope": scope,
        "include": includes or [],
        "candidates": len(results),
        "returned": len(results),
        "results": results,
        "info": info,
        "zero_hit": zero_hit,
    }


# ── 본문 주입 (--inject, E9) ─────────────────────────────────────
def _section_text(section: Section) -> list[str]:
    """주입용 라인 — 색인 헤딩(H2/H3)은 원문 형태로 복원해 맨 앞에 둔다. level 1 은
    H1 텍스트가 있을 때만 `# {H1}` 을 붙이고 합성 헤딩(`(파일 전체)`·`(서문)`)은 뺀다."""
    if section.level in (2, 3):
        head = [f"{'#' * section.level} {section.heading}"]
    elif section.heading not in ("(파일 전체)", "(서문)"):
        head = [f"# {section.heading}"]
    else:
        head = []
    return head + list(section.body_lines)


def _render_overhead(r: dict, index: int) -> int:
    """결과 1건이 본문 없이도 md/manifest 출력에 차지하는 바이트 근사(C8) — 표 행과 manifest
    줄 중 큰 쪽 + `<context-snippet>` 래퍼 2줄. 예산은 이 값을 먼저 뗀 뒤 본문에 쓴다."""
    matched = ",".join(r["matched"])
    row = (
        f"| {index} | {r['file']} | {r['heading']} | {r['line_start']}-{r['line_end']} | "
        f"{r['score']} | {matched} |"
    )
    manifest = (
        f"[#{index}] {r['score']} [boundary] | {r['file']} :: {r['heading']} | "
        f"L{r['line_start']}-{r['line_end']} | 999d | matched: {matched} | "
        f"{r['snippet'][:MANIFEST_SNIPPET_CHARS]}…"
    )
    wrapper = (
        f'<context-snippet file="{r["file"]}" heading="{r["heading"]}" '
        f'lines="{r["line_start"]}-{r["line_end"]}"></context-snippet>'
        f"[잘림 — 나머지: Read {r['file']} offset={r['line_end']}0 limit={r['line_end']}0]"
    )
    skip_line = f"[{index}] {r['file']} :: {r['heading']} — 바이트 예산 소진 — read_hint 로 Read ({r['read_hint']})"
    return (
        max(len(row.encode("utf-8")), len(manifest.encode("utf-8")))
        + max(len(wrapper.encode("utf-8")), len(skip_line.encode("utf-8")))
        + 4
    )


def _apply_inject(results: list[dict], secs: list[Section], max_bytes: int) -> list[str]:
    """결과 순서대로 본문을 `text` 에 싣는다(E9). 규칙:
    - `max_bytes` 는 **md/manifest 렌더 총량 근사**(C8): 헤더·INFO 여유(RENDER_RESERVE_BYTES)와
      결과별 표/manifest 줄·래퍼(`_render_overhead`)를 먼저 뗀 나머지를 본문(개행 포함 UTF-8)에
      쓴다. json 은 이스케이프·snippet 중복으로 이보다 크다.
    - 섹션당 최대 LARGE_SECTION_LINES 줄. 잘리면 `truncated: true` + `inject_rest`.
    - 같은 파일에서 **앞선** 결과의 주입 범위가 이 섹션 전체를 덮으면(H2 본문은 하위 H3
      본문을 포함한다) 중복 주입을 생략하고 `inject_skip` 에 사유를 둔다.
    - 예산이 남지 않아 한 줄도 못 실으면 `inject_skip` — read_hint 로 Read.
    반환: INFO 줄 목록."""
    info: list[str] = []
    overhead = RENDER_RESERVE_BYTES + sum(_render_overhead(r, i) for i, r in enumerate(results, 1))
    budget = max_bytes - overhead
    covered: list[tuple[str, int, int, int]] = []  # (file, line_start, 주입된 마지막 파일 라인, 결과 번호)
    skipped_budget = 0
    for idx, (r, sec) in enumerate(zip(results, secs), 1):
        r["text"] = ""
        r["truncated"] = False
        parent = next(
            (
                c for c in covered
                if c[0] == sec.file and c[1] <= sec.line_start and sec.line_end <= c[2]
                and (c[1], c[2]) != (sec.line_start, sec.line_end)
            ),
            None,
        )
        if parent is not None:
            r["inject_skip"] = (
                f"앞선 결과 [#{parent[3]}](L{parent[1]}-{parent[2]}) 본문에 포함 — 중복 주입 생략"
            )
            continue
        # 텍스트 줄마다 파일 라인 범위를 나란히 둔다 — 접힌 자식 범위(C5)와 잘림 힌트의 라인 계산 근거
        lines = _section_text(sec)
        spans: list[tuple[int, int]] = [
            (sec.line_start + i, sec.line_start + i) for i in range(len(lines))
        ]
        if sec.level == 2:
            # C5 — 앞서 주입된 하위 섹션(H3)이 이 H2 본문 안에 있으면 그 범위를 1줄 표지로 접는다
            # (키워드 질의에서는 H3 정확 일치가 H2 보다 앞서는 순서가 기본이라 이 방향이 흔하다)
            children = sorted(
                (c for c in covered if c[0] == sec.file and sec.line_start < c[1] and c[2] <= sec.line_end),
                key=lambda c: c[1], reverse=True,
            )
            for c in children:
                lo, hi = c[1] - sec.line_start, c[2] - sec.line_start
                if 0 < lo <= hi < len(lines):
                    lines[lo : hi + 1] = [f"[L{c[1]}-{c[2]} 는 [#{c[3]}] 에 주입됨 — 생략]"]
                    spans[lo : hi + 1] = [(c[1], c[2])]
        total = len(lines)
        kept = 0
        used = 0
        cap = LARGE_SECTION_LINES + (1 if sec.level in (2, 3) else 0)  # 복원한 헤딩 줄은 캡 밖(C12)
        for ln in lines[: min(total, cap)]:
            nbytes = len(ln.encode("utf-8")) + 1  # 개행 포함
            if used + nbytes > budget:
                break
            kept += 1
            used += nbytes
        if kept == 0 or (kept == 1 and total > 1 and sec.level in (2, 3)):
            # 예산이 없거나 헤딩 줄 하나만 들어가는 경우 — 헤딩만 주입하는 것은 정보가 없다(C8)
            r["inject_skip"] = "바이트 예산 소진 — read_hint 로 Read"
            skipped_budget += 1
            continue
        budget -= used
        r["text"] = "\n".join(lines[:kept])
        last_line = spans[kept - 1][1]
        if kept < total:
            r["truncated"] = True
            rest_start = last_line + 1
            r["inject_rest"] = (
                f"Read {r['file']} offset={rest_start} limit={max(sec.line_end - rest_start + 1, 1)}"
            )
        covered.append((sec.file, sec.line_start, last_line if r["truncated"] else sec.line_end, idx))
    if skipped_budget:
        info.append(
            f"--inject 예산({max_bytes}B, 렌더 총량 기준) 소진 — {skipped_budget}개 섹션 본문 생략, "
            "read_hint 로 Read"
        )
    return info


# ── 출력 렌더링 ─────────────────────────────────────────────────
def _render_header(result: dict) -> str:
    scope_display = result["scope"] or "(전체)"
    return (
        f"검색: `{result['query']}` · scope={scope_display} · "
        f"후보 {result['candidates']}건 중 {result['returned']}건 표시"
    )


def _render_tail(result: dict) -> list[str]:
    lines: list[str] = []
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
    return lines


def _is_injected(result: dict) -> bool:
    return any("text" in r for r in result["results"])


def _render_inject_blocks(result: dict) -> list[str]:
    """`<context-snippet file heading lines>` 블록 — 속성값은 html.escape 로 따옴표를 봉인."""
    out: list[str] = []
    for i, r in enumerate(result["results"], 1):
        if r.get("inject_skip"):
            out.append(f"[{i}] {r['file']} :: {r['heading']} — {r['inject_skip']} ({r['read_hint']})")
            continue
        attrs = (
            f'file="{html.escape(r["file"], quote=True)}" '
            f'heading="{html.escape(r["heading"], quote=True)}" '
            f'lines="{r["line_start"]}-{r["line_end"]}"'
        )
        out.append(f"<context-snippet {attrs}>")
        out.append(r["text"])
        out.append("</context-snippet>")
        if r.get("truncated"):
            out.append(f"[잘림 — 나머지: {r['inject_rest']}]")
    return out


def render_md(result: dict) -> str:
    lines: list[str] = [_render_header(result), ""]

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
        if _is_injected(result):
            lines.extend(_render_inject_blocks(result))
        else:
            for i, r in enumerate(result["results"], 1):
                if r["snippet"]:
                    lines.append(f"{i}. > {r['snippet']}")
                lines.append(f"   {r['read_hint']}")
        lines.append("")

    lines.extend(_render_tail(result))
    return "\n".join(lines)


def _age_days(path_str: str, now: float | None = None) -> int | None:
    """파일 mtime 기준 경과 일수 — manifest 표기 전용. 점수·정렬에는 쓰지 않는다(E1:
    clone 직후엔 전 파일이 같은 값이고 날짜에 따라 변하므로 결정성 보증 밖의 정보)."""
    try:
        st = os.stat(path_str)
    except OSError:
        return None
    if now is None:
        now = time.time()
    return int(max(0.0, now - st.st_mtime) // 86400)


def _inferred_type_tag(display_file: str) -> str | None:
    """frontmatter `type` 이 없을 때 경로 규약으로 추정한 태그(C2) — `boundaries/` → `boundary?`,
    `rules/` → `rules?` (물음표 = 추정). 2차 선별의 "규칙·경계 후보는 버리지 않는다" 규칙이
    frontmatter 없는 코퍼스(#29 이전·사용자 layer)에서도 걸리게 한다. JSON `type` 에는 넣지 않는다."""
    parts = Path(display_file).parts
    if "boundaries" in parts:
        return "boundary?"
    if "rules" in parts:
        return "rules?"
    return None


def render_manifest(result: dict, now: float | None = None) -> str:
    """후보당 1줄 초경량 목록(E10) — wrapper-protocol §6 2차 선별의 입력.
    `[#n] {score} [type] | {file} :: {heading} | L{start}-{end} | {age}d | matched: a,b | {snippet≤80}`
    snippet 은 마지막 필드 — 표 본문의 `|` 가 섞일 수 있으므로 앞 5개 ` | ` 로만 분리한다(C12)."""
    lines: list[str] = [_render_header(result), ""]
    ages = [_age_days(r["file"], now) for r in result["results"]]
    # clone 직후엔 전 파일 mtime 이 같아 age 가 최신성으로 오독된다 — 후보 2개 이상이 전부 같은 값이면 `-` (정보 없음)
    uniform = len(ages) >= 2 and len(set(ages)) == 1
    for i, (r, age) in enumerate(zip(result["results"], ages), 1):
        score = r["score"] if r["score"] is not None else "-"
        type_tag = r.get("type") or _inferred_type_tag(r["file"])
        tag = f" [{type_tag}]" if type_tag else ""
        age_s = "-" if uniform or age is None else f"{age}d"
        matched = ",".join(r["matched"]) if r["matched"] else "-"
        snip = r["snippet"]
        if len(snip) > MANIFEST_SNIPPET_CHARS:
            snip = snip[:MANIFEST_SNIPPET_CHARS] + "…"
        heading_display = r["heading"].replace("`", "")  # C1 — select 에 그대로 붙여 넣기 안전
        lines.append(
            f"[#{i}] {score}{tag} | {r['file']} :: {heading_display} | "
            f"L{r['line_start']}-{r['line_end']} | {age_s} | matched: {matched} | {snip}"
        )
    if result["results"]:
        lines.append("")
        if _is_injected(result):
            lines.extend(_render_inject_blocks(result))
            lines.append("")
    lines.extend(_render_tail(result))
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
    parser.add_argument(
        "--limit", type=int, default=None,
        help=f"기본 {DEFAULT_LIMIT} (키워드 질의 + --inject 는 {INJECT_DEFAULT_LIMIT}), 최대 {MAX_LIMIT}",
    )
    parser.add_argument(
        "--format", choices=("md", "json", "manifest"), default="md",
        help="출력 형식 (기본 md). manifest = 후보당 1줄 초경량 목록 (2차 선별 입력)",
    )
    parser.add_argument(
        "--inject", action="store_true",
        help="선정 섹션 본문을 <context-snippet> 블록으로 함께 출력 (json 은 text 키)",
    )
    parser.add_argument(
        "--max-bytes", type=int, default=INJECT_MAX_BYTES_DEFAULT,
        help=f"--inject 본문 총 바이트 상한 (기본 {INJECT_MAX_BYTES_DEFAULT}, 최대 {INJECT_MAX_BYTES_CAP})",
    )
    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = _build_argparser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2

    limit = args.limit
    if limit is None:
        limit = INJECT_DEFAULT_LIMIT if args.inject else DEFAULT_LIMIT
    max_bytes = args.max_bytes
    json_scaled = args.inject and args.format == "json" and max_bytes >= 1
    if json_scaled:
        max_bytes = max(1, int(min(max_bytes, INJECT_MAX_BYTES_CAP) * JSON_INJECT_BUDGET_FACTOR))
    try:
        result = search(
            workspace=Path(args.workspace),
            project=args.project,
            scope=args.scope,
            includes=args.include,
            query_raw=args.query,
            limit=limit,
            inject=args.inject,
            max_bytes=max_bytes,
        )
    except SearchError as exc:
        print(exc.message, file=sys.stderr)
        if exc.show_usage:
            parser.print_usage(sys.stderr)
        return exc.exit_code
    if json_scaled:
        result["info"].append(
            f"--format json + --inject: 예산을 {max_bytes}B 로 축소 (json 렌더는 md 의 ≈1.5× — 상한 근처에선 md/manifest 권장)"
        )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.format == "manifest":
        print(render_manifest(result))
    else:
        print(render_md(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
