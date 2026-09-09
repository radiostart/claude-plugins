"""doctor rules_pointer — 경로 트리거 도메인 규칙 파일 생성·판정 (#30 C1, plan r2).

`.claude/rules/pilot-{domain}.md` 를 워크스페이스 도메인 지식에서 **결정적으로** 만든다.
같은 함수를 `/pilot:learn` Phase 5(생성) · `/pilot:doctor`(점검) · `hooks/domain-pointer.sh`
(보완 훅 — Write·Edit 는 조건부 규칙을 발화시키지 않으므로) 가 공유한다 — 판정 1벌 원칙.

파일 형식:
    ---
    paths:                       # gitignore 의미 (하네스 `.claude/rules paths:` · context-search._glob_regex 와 동일)
      - app/services/wms/**
    ---
    <!-- managed by /pilot:learn … -->          # 관리 마커 — 이 줄이 있는 파일만 덮어쓴다
    <!-- paths: 인용 경로 추정 … -->             # sources frontmatter 가 없어 인용으로 추정했을 때만
    이 경로는 `wms` 도메인이다. 수정 전 확인:    # ← 여기부터가 하네스가 주입하는 본문 (≤ 8줄 · ≤ 500자)
    - 진입: workspace/context/wms/index.md
    - 규칙/본문/경계: …
    - 상세 조회: /pilot:ask (메인) · wrapper-protocol §6 3단계 (래퍼)

`paths` 도출: 도메인 문서(진입 파일 + `{domain}.md` + `{domain}/**/*.md`) 의 frontmatter `sources`
합집합 우선 → 없으면 인용 경로를 실파일로 해석(#28 인용 체인)해 하위 트리 합산 후 탐욕 분할
(≤ 8 globs · 깊이 ≤ 3 · 분할로 잃는 파일 ≤ max(1, 10%)). `workspace/**`·`.claude/**`·config `## Ignore`·
`test_path_convention` 은 제외. 전 도메인을 함께 집계해 동일 glob 은 하위 트리가 큰 도메인에만(동률 제거).

지식 파일은 읽기 전용. 표준 라이브러리만. context-search.py 는 importlib 로 지연 로드(파서·glob 의미 단일화).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from doctor._common import Result
from doctor import integrity as _integ

MARKER_PREFIX = "<!-- managed by /pilot:learn"
MARKER_LINE = (
    "<!-- managed by /pilot:learn — 수동 편집 금지. 재생성: python3 ${CLAUDE_PLUGIN_ROOT}/tools/rules-pointer.py "
    "--all --write · 점검: /pilot:doctor. 규칙은 세션당 1회 로드 — 재생성분은 새 세션부터 -->"
)
ESTIMATE_COMMENT = "<!-- paths: 인용 경로 추정 (sources frontmatter 없음) -->"
RULES_SUBDIR = Path(".claude") / "rules"
FILE_PREFIX = "pilot-"
DOMAIN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
MAX_GLOBS = 8
MAX_GLOB_DEPTH = 3
MIN_FILES = 2
MAX_LINES = 8
MAX_CHARS = 500
MAX_BODY_POINTERS = 2
MAX_BOUNDARY_POINTERS = 2
HOOK_MAX_DOMAINS = 2
POINTER_TYPES = ("rules", "services", "enums")
DETAIL_LINE = "- 상세 조회: /pilot:ask (메인) · wrapper-protocol §6 3단계 (래퍼)"
ALWAYS_EXCLUDE = ("workspace/**", ".claude/**")
_POINTER_LINE_RE = re.compile(r"^- (?:진입|규칙|본문|경계): (\S+)$", re.M)


class RulesPointerError(Exception):
    pass


_cs_module = None


def _cs():
    """context-search.py 지연 로드 — frontmatter 파서(`parse_frontmatter`)·gitignore 의미 glob(`_glob_regex`)."""
    global _cs_module
    if _cs_module is None:
        path = Path(__file__).resolve().parent.parent / "context-search.py"
        spec = importlib.util.spec_from_file_location("_rules_pointer_context_search", path)
        if spec is None or spec.loader is None:
            raise RulesPointerError(f"context-search.py 로드 실패: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["_rules_pointer_context_search"] = module
        spec.loader.exec_module(module)
        _cs_module = module
    return _cs_module


def glob_regex(glob: str):
    return _cs()._glob_regex(glob)


def rules_dir(workspace: Path) -> Path:
    return workspace.parent / RULES_SUBDIR


def rules_path(workspace: Path, domain: str) -> Path:
    return rules_dir(workspace) / f"{FILE_PREFIX}{domain}.md"


# ── MANIFEST · 문서 집합 ────────────────────────────────────────
def _clean_entry(entry: str) -> str:
    entry = entry.strip().strip("`").strip().lstrip("/")
    for prefix in ("workspace/context/", "context/"):
        if entry.startswith(prefix):
            entry = entry[len(prefix):]
    return entry


def list_domains(workspace: Path) -> list[tuple[str, list[str]]]:
    """MANIFEST `## 도메인 분류` 표 → [(도메인, [진입 파일(루트 기준)])] 표 순서."""
    manifest = workspace / "context" / "MANIFEST.md"
    if not manifest.is_file():
        return []
    text = manifest.read_text(encoding="utf-8", errors="replace")
    out: dict[str, list[str]] = {}
    for table in _integ._parse_md_tables_in_section(text, "## 도메인 분류"):
        for row in table[1:]:  # 헤더 행 제외
            if len(row) < 2:
                continue
            domain = row[0].strip().strip("`").strip()
            entry = _clean_entry(row[1])
            if not domain or not entry:
                continue
            out.setdefault(domain, [])
            if entry not in out[domain]:
                out[domain].append(entry)
    return list(out.items())


def domain_docs(workspace: Path, domain: str, entries: list[str]) -> list[Path]:
    root = workspace / "context"
    files: set[Path] = set()
    for e in entries:
        p = root / e
        if p.is_file():
            files.add(p)
    single = root / f"{domain}.md"
    if single.is_file():
        files.add(single)
    folder = root / domain
    if folder.is_dir():
        files.update(p for p in folder.rglob("*.md") if p.is_file())
    return sorted(files)


def boundary_docs(workspace: Path, domain: str) -> list[Path]:
    bdir = workspace / "context" / "boundaries"
    if not bdir.is_dir():
        return []
    return sorted(
        p for p in bdir.glob("*.md")
        if p.name.startswith(f"{domain}--") or p.stem.endswith(f"--{domain}")
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return _cs().parse_frontmatter(lines[1:i])
    return {}


# ── 제외 규칙 · 인용 해석 ───────────────────────────────────────
def exclusion_globs(workspace: Path) -> list[str]:
    """항상 제외 + config `## Ignore` 패턴 + `test_path_convention` (스켈레톤 예시 셀은 미선언 취급)."""
    globs = list(ALWAYS_EXCLUDE)
    config = workspace / "context" / "config.md"
    if not config.is_file():
        return globs
    text = _read(config)
    for table in _integ._parse_md_tables_in_section(text, "## Ignore"):
        for row in table[1:]:
            if not row:
                continue
            pat = row[0].strip().strip("`").strip()
            if pat:
                globs.append(pat)
    for table in _integ._parse_md_tables_in_section(text, "## 언어·도구 기본값"):
        for row in table[1:]:
            if len(row) < 2 or row[0].strip().strip("`").strip() != "test_path_convention":
                continue
            value, _ambiguous = _integ._extract_declared_path(row[1])
            if value:
                globs.append(value)
    return globs


def resolved_sources(workspace: Path, docs: list[Path], exclude_res) -> list[str]:
    """문서 인용을 실파일로 해석(#28 체인) → repo 기준 상대경로 목록(정렬). workspace 내부·제외 패턴 제거."""
    repo = workspace.parent
    repo_resolved = repo.resolve()
    source_root = _integ._read_source_root(workspace)
    files: set[str] = set()
    for doc in docs:
        for cited in _integ._iter_cited_paths(_read(doc)):
            src = _integ._resolve_cited(repo, source_root, cited)
            if src is None or _integ._is_workspace_internal(src, workspace):
                continue
            try:
                rel = src.resolve().relative_to(repo_resolved).as_posix()
            except (ValueError, OSError):
                continue
            if any(rx.match(rel) for rx in exclude_res):
                continue
            files.add(rel)
    return sorted(files)


# ── glob 집계 ───────────────────────────────────────────────────
def aggregate_globs(files: list[str]) -> list[tuple[str, int]]:
    """실파일 목록 → [(glob, 하위 트리 파일 수)] — 최상위 디렉토리에서 시작해 가장 큰 glob 부터 탐욕 분할.
    분할 조건: 자식 디렉토리(각 ≥ MIN_FILES)로 쪼갤 때 잃는 파일 ≤ max(1, 10%), 결과 ≤ MAX_GLOBS,
    깊이 ≤ MAX_GLOB_DEPTH. 파일 < MIN_FILES 인 glob 은 제거(유일하면 유지). 결정적(이름순)."""
    if not files:
        return []
    counts: dict[str, int] = {}
    children: dict[str, set[str]] = {}
    root_files: list[str] = []
    for f in sorted(set(files)):
        parts = f.split("/")
        if len(parts) == 1:
            root_files.append(f)
            continue
        for i in range(1, len(parts)):
            d = "/".join(parts[:i])
            counts[d] = counts.get(d, 0) + 1
            children.setdefault("/".join(parts[: i - 1]), set()).add(d)
    globs: list[str] = sorted(children.get("", set())) + root_files

    def split_of(d: str) -> list[str] | None:
        if d not in counts or d.count("/") + 1 >= MAX_GLOB_DEPTH:
            return None
        kids = sorted(c for c in children.get(d, ()) if counts[c] >= MIN_FILES)
        if not kids:
            return None
        dropped = counts[d] - sum(counts[c] for c in kids)
        if dropped > max(1, counts[d] // 10):
            return None
        return kids

    while True:
        progressed = False
        for g in sorted(globs, key=lambda x: (-counts.get(x, 0), x)):
            kids = split_of(g)
            if kids is None or len(globs) - 1 + len(kids) > MAX_GLOBS:
                continue
            globs = sorted([x for x in globs if x != g] + kids)
            progressed = True
            break
        if not progressed:
            break
    kept = [g for g in globs if counts.get(g, 1) >= MIN_FILES]
    if not kept:
        kept = globs
    kept = sorted(kept, key=lambda x: (-counts.get(x, 1), x))[:MAX_GLOBS]
    return sorted(((g + "/**") if g in counts else g, counts.get(g, 1)) for g in kept)


@dataclass
class DomainPaths:
    domain: str
    entries: list[str]
    globs: list[str]
    counts: dict[str, int] = field(default_factory=dict)
    estimated: bool = False
    info: list[str] = field(default_factory=list)


def derive_paths(workspace: Path, domains: "list[str] | None" = None) -> dict[str, DomainPaths]:
    """전 등록 도메인을 함께 집계(배타 규칙)하고 요청한 도메인만 돌려준다. 미등록 도메인 → RulesPointerError."""
    registered = dict(list_domains(workspace))
    if not registered:
        raise RulesPointerError("MANIFEST `## 도메인 분류` 에 등록된 도메인이 없다")
    if domains is not None:
        unknown = [d for d in domains if d not in registered]
        if unknown:
            raise RulesPointerError(f"MANIFEST 미등록 도메인: {', '.join(unknown)} — `/pilot:learn {{진입점}}` 으로 등록")
    exclude_res = [glob_regex(g) for g in exclusion_globs(workspace)]
    results: dict[str, DomainPaths] = {}
    for domain, entries in registered.items():
        docs = domain_docs(workspace, domain, entries)
        sources: set[str] = set()
        for doc in docs:
            for g in _frontmatter(_read(doc)).get("sources", []):
                g = g.strip()
                if not g:
                    continue
                sources.add(g.rstrip("/") + "/**" if g.endswith("/") else g)
        dp = DomainPaths(domain, list(entries), [])
        if sources:
            globs = sorted(sources)
            if len(globs) > MAX_GLOBS:
                dp.info.append(f"sources {len(globs)}개 — 앞 {MAX_GLOBS}개만 사용")
                globs = globs[:MAX_GLOBS]
            dp.globs = globs
        else:
            files = resolved_sources(workspace, docs, exclude_res)
            if len(files) < MIN_FILES:
                dp.info.append(
                    f"해석 가능한 인용 {len(files)}건 (< {MIN_FILES}) — 규칙 파일 생성 skip. "
                    "`sources` frontmatter 기입 또는 `/pilot:learn` 재실행"
                )
            else:
                agg = aggregate_globs(files)
                dp.globs = [g for g, _ in agg]
                dp.counts = dict(agg)
                dp.estimated = True
                covered = sum(n for _, n in agg)
                dp.info.append(f"paths 인용 경로 추정 — 해석 {len(files)}건 → glob {len(agg)}개 (커버 {covered}/{len(files)})")
        results[domain] = dp
    # 도메인 간 배타 — 추정 glob 만 대상 (sources 명시는 사용자 의도)
    owners: dict[str, list[str]] = {}
    for d, dp in results.items():
        if dp.estimated:
            for g in dp.globs:
                owners.setdefault(g, []).append(d)
    for g, ds in owners.items():
        if len(ds) < 2:
            continue
        best = max(results[d].counts.get(g, 0) for d in ds)
        winners = [d for d in ds if results[d].counts.get(g, 0) == best]
        for d in ds:
            if len(winners) > 1 or d not in winners:
                results[d].globs = [x for x in results[d].globs if x != g]
                why = "동률" if len(winners) > 1 else f"`{winners[0]}` 우선"
                results[d].info.append(f"공유 경로 `{g}` — {why} 으로 제외 (index 참조)")
    if domains is None:
        return results
    return {d: results[d] for d in domains}


# ── 포인터 · 렌더 ───────────────────────────────────────────────
def select_pointers(workspace: Path, domain: str, entries: list[str]) -> tuple[list[str], int]:
    """포인터 줄 목록과 접힌 개수. 순서: 진입 → rules/{domain}.md → 본문(type rules·services·enums ≤2) → 경계 ≤2."""
    root = workspace / "context"
    lines: list[str] = []
    entry_paths = []
    for e in entries:
        p = root / e
        if p.is_file():
            lines.append(f"- 진입: workspace/context/{e}")
            entry_paths.append(p)
    if (root / "rules" / f"{domain}.md").is_file():
        lines.append(f"- 규칙: workspace/context/rules/{domain}.md")
    bodies: list[Path] = []
    for doc in domain_docs(workspace, domain, entries):
        if doc in entry_paths:
            continue
        meta = _frontmatter(_read(doc))
        kind = str(meta.get("type") or doc.stem).lower()
        if kind in POINTER_TYPES:
            bodies.append(doc)
    extra = max(0, len(bodies) - MAX_BODY_POINTERS)
    for doc in bodies[:MAX_BODY_POINTERS]:
        lines.append(f"- 본문: workspace/context/{doc.relative_to(root).as_posix()}")
    bounds = boundary_docs(workspace, domain)
    extra += max(0, len(bounds) - MAX_BOUNDARY_POINTERS)
    for b in bounds[:MAX_BOUNDARY_POINTERS]:
        lines.append(f"- 경계: workspace/context/boundaries/{b.name}")
    return lines, extra


def compose_body(domain: str, pointer_lines: list[str], extra: int) -> str:
    """주입 본문(frontmatter·주석 제외). 캡 ≤ MAX_LINES 줄·≤ MAX_CHARS 자 — 초과 시 경계 → 본문 순으로 접는다."""
    lines = list(pointer_lines)
    while True:
        body = [f"이 경로는 `{domain}` 도메인이다. 수정 전 확인:"] + lines
        if extra:
            body.append(f"- 그 외 {extra}개 — index 참조")
        body.append(DETAIL_LINE)
        text = "\n".join(body)
        if len(body) <= MAX_LINES and len(text) <= MAX_CHARS:
            return text
        idx = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("- 경계:")), None)
        if idx is None:
            idx = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("- 본문:")), None)
        if idx is None:
            return text
        del lines[idx]
        extra += 1


def render_rules_file(dp: DomainPaths, pointer_lines: list[str], extra: int) -> str:
    parts = ["---", "paths:"] + [f"  - {g}" for g in dp.globs] + ["---", MARKER_LINE]
    if dp.estimated:
        parts.append(ESTIMATE_COMMENT)
    parts.append(compose_body(dp.domain, pointer_lines, extra))
    return "\n".join(parts) + "\n"


def build_rules_file(
    workspace: Path, domain: str, derived: "dict[str, DomainPaths] | None" = None
) -> tuple[str | None, list[str]]:
    """(파일 내용 | None, INFO). None = 생성 대상 아님(paths 0건)."""
    if derived is None or domain not in derived:
        derived = derive_paths(workspace, [domain])
    dp = derived[domain]
    if not dp.globs:
        return None, list(dp.info)
    lines, extra = select_pointers(workspace, domain, dp.entries)
    return render_rules_file(dp, lines, extra), list(dp.info)


def injected_body(content: str) -> str:
    """하네스가 실제로 주입하는 부분 — frontmatter 와 HTML 주석 줄을 뺀 본문."""
    lines = content.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break
    return "\n".join(ln for ln in lines[start:] if not ln.strip().startswith("<!--")).strip()


def parse_paths(content: str) -> list[str]:
    """규칙 파일 frontmatter `paths:` 블록 리스트."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    paths: list[str] = []
    in_paths = False
    for ln in lines[1:]:
        s = ln.strip()
        if s == "---":
            break
        if s.startswith("paths:"):
            in_paths = True
            continue
        if in_paths:
            if s.startswith("- "):
                paths.append(s[2:].strip().strip("\"'"))
            elif s and not ln[:1].isspace():
                in_paths = False
    return paths


# ── 쓰기 · 점검 ─────────────────────────────────────────────────
def write_rules_files(
    workspace: Path, domains: "list[str] | None" = None
) -> tuple[list[tuple[str, str]], list[str]]:
    """규칙 파일 생성/갱신. 반환: [(도메인, created|updated|unchanged|skipped-empty|skipped-unmanaged|skipped-name)], INFO.
    관리 마커가 있는 파일만 덮어쓴다. 내용이 같으면 쓰지 않는다(mtime 보존)."""
    derived = derive_paths(workspace, domains)
    statuses: list[tuple[str, str]] = []
    info: list[str] = []
    for domain, dp in derived.items():
        if not DOMAIN_RE.match(domain):
            statuses.append((domain, "skipped-name"))
            info.append(f"{domain}: 도메인명 부적합(영숫자·_·- 만) — skip")
            continue
        content, dinfo = build_rules_file(workspace, domain, derived)
        info.extend(f"{domain}: {m}" for m in dinfo)
        if content is None:
            statuses.append((domain, "skipped-empty"))
            continue
        path = rules_path(workspace, domain)
        if path.is_file():
            existing = _read(path)
            if MARKER_PREFIX not in existing:
                statuses.append((domain, "skipped-unmanaged"))
                info.append(f"{domain}: 관리 마커 없음 — 사용자 파일로 간주, 덮어쓰지 않음 ({path})")
                continue
            if existing == content:
                statuses.append((domain, "unchanged"))
                continue
            path.write_text(content, encoding="utf-8")
            statuses.append((domain, "updated"))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        statuses.append((domain, "created"))
    if any(s in ("created", "updated") for _, s in statuses):
        info.append("규칙은 세션당 1회 로드 — 생성·갱신분은 새 세션부터 반영")
    return statuses, info


def check_rules_files(workspace: Path, domains: "list[str] | None" = None) -> list[tuple[str, str, str]]:
    """[(도메인, ok|differs|missing|unmanaged|skip, 설명)] — `--check` 용."""
    derived = derive_paths(workspace, domains)
    rows: list[tuple[str, str, str]] = []
    for domain in derived:
        content, _ = build_rules_file(workspace, domain, derived)
        path = rules_path(workspace, domain)
        if content is None:
            rows.append((domain, "skip", "생성 대상 아님 (paths 0건)"))
            continue
        if not path.is_file():
            rows.append((domain, "missing", str(path)))
            continue
        existing = _read(path)
        if MARKER_PREFIX not in existing:
            rows.append((domain, "unmanaged", "관리 마커 없음 — 사용자 파일"))
            continue
        rows.append((domain, "ok" if existing == content else "differs", str(path)))
    return rows


def check_rules_pointer(workspace: Path) -> list[Result]:
    """doctor 검사 — 마커 없는 파일은 INFO 만. 관리 파일: (a) 미등록 도메인 WARN (b) 포인터 경로 부재 WARN
    (c) 재생성 불일치 INFO (e) claudeMdExcludes INFO (f) 규칙 파일 간 동일 glob INFO."""
    rdir = rules_dir(workspace)
    if not rdir.is_dir():
        return []
    files = sorted(rdir.glob(f"{FILE_PREFIX}*.md"))
    if not files:
        return []
    results: list[Result] = []
    registered = dict(list_domains(workspace))
    derived: "dict[str, DomainPaths] | None" = None
    managed: list[tuple[Path, str]] = []
    hint_regen = "python3 ${CLAUDE_PLUGIN_ROOT}/tools/rules-pointer.py --all --write (새 세션부터 반영)"
    for f in files:
        content = _read(f)
        rel = f"{RULES_SUBDIR.as_posix()}/{f.name}"
        if MARKER_PREFIX not in content:
            results.append(Result(Result.INFO, rel, "관리 마커 없음 — 사용자 관리 파일로 간주, 검사 생략"))
            continue
        managed.append((f, content))
        domain = f.name[len(FILE_PREFIX):-3]
        if domain not in registered:
            results.append(Result(
                Result.WARN, rel, f"도메인 `{domain}` 이 MANIFEST 에 없음 — stale 규칙 파일",
                "파일 삭제 또는 MANIFEST `## 도메인 분류` 에 등록",
            ))
            continue
        missing = [
            m.group(1) for m in _POINTER_LINE_RE.finditer(content)
            if not (workspace.parent / m.group(1)).is_file()
        ]
        if missing:
            results.append(Result(
                Result.WARN, rel, f"포인터 경로 부재 {len(missing)}건: {', '.join(missing[:3])}", hint_regen,
            ))
        if derived is None:
            try:
                derived = derive_paths(workspace)
            except RulesPointerError:
                derived = {}
        expected = build_rules_file(workspace, domain, derived)[0] if domain in derived else None
        if expected is None:
            results.append(Result(Result.INFO, rel, "재생성 시 생성되지 않을 파일 (인용·sources 부족) — 유지 여부 확인"))
        elif expected != content:
            results.append(Result(Result.INFO, rel, "재생성 결과와 다름 — 재생성 권장", hint_regen))
    owners: dict[str, list[str]] = {}
    for f, content in managed:
        for g in parse_paths(content):
            owners.setdefault(g, []).append(f.name)
    for g, names in sorted(owners.items()):
        if len(names) > 1:
            results.append(Result(
                Result.INFO, "규칙 포인터 겹침", f"`{g}` 가 {', '.join(names)} 에 공통 — 매칭 파일 Read 시 모두 로드",
                "공유 경로는 한 도메인에만 두거나 index 참조로",
            ))
    for name in ("settings.json", "settings.local.json"):
        p = workspace.parent / ".claude" / name
        if not p.is_file():
            continue
        try:
            data = json.loads(_read(p))
        except ValueError:
            continue
        excludes = data.get("claudeMdExcludes") if isinstance(data, dict) else None
        if isinstance(excludes, list) and any(".claude/rules" in str(x) for x in excludes):
            results.append(Result(
                Result.INFO, f".claude/{name}", "claudeMdExcludes 가 .claude/rules 를 가리킴 — 규칙 포인터가 로드되지 않는다",
                "제외 패턴에서 .claude/rules 를 빼거나 규칙 포인터를 쓰지 않는다",
            ))
    if managed and not any(r.level == Result.WARN for r in results):
        results.append(Result(Result.PASS, "규칙 포인터", f"관리 파일 {len(managed)}개 — 정합"))
    return results


# ── 보완 훅 ─────────────────────────────────────────────────────
def match_hook(workspace: Path, file_path: str, session_id: str) -> str | None:
    """PostToolUse Edit|Write 보완(C1 은 Read 만 발화): 수정 파일이 관리 규칙 파일의 `paths:` 에 맞으면
    그 규칙의 주입 본문을 세션·도메인당 1회 돌려준다. 프로젝트 밖·workspace/·.claude/·session_id 부재 → None."""
    if not session_id or not file_path:
        return None
    rdir = rules_dir(workspace)
    if not rdir.is_dir():
        return None
    try:
        rel = Path(file_path).resolve().relative_to(workspace.parent.resolve()).as_posix()
    except (ValueError, OSError):
        return None
    if rel.startswith("workspace/") or rel.startswith(".claude/"):
        return None
    matched: list[tuple[str, str]] = []
    for f in sorted(rdir.glob(f"{FILE_PREFIX}*.md")):
        content = _read(f)
        if MARKER_PREFIX not in content:
            continue
        if any(glob_regex(g).match(rel) for g in parse_paths(content)):
            matched.append((f.name[len(FILE_PREFIX):-3], content))
    if not matched:
        return None
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    safe = re.sub(r"[^A-Za-z0-9_-]", "", session_id)
    fresh = [(d, c) for d, c in matched if not (tmp / f"pilot-domain-pointer.{safe}.{d}").exists()]
    if not fresh:
        return None
    shown = fresh[:HOOK_MAX_DOMAINS]
    text = "[도메인 포인터] " + "\n\n".join(injected_body(c) for _, c in shown)
    if len(fresh) > HOOK_MAX_DOMAINS:
        text += f"\n그 외 {len(fresh) - HOOK_MAX_DOMAINS} 도메인 — index 참조"
    for d, _ in shown:
        try:
            (tmp / f"pilot-domain-pointer.{safe}.{d}").touch()
        except OSError:
            pass
    return text
