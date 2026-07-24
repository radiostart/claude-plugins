#!/usr/bin/env python3
"""
pilot docs_build — agents/skills/tools/identity SSOT 를 docs/reference/ 로 추출.

호출:
    python3 pilot/tools/docs_build.py                # 생성 (덮어쓰기)
    python3 pilot/tools/docs_build.py --check        # 생성하지 않고 디스크 상태가 source 와 일치하는지 검증
    python3 pilot/tools/docs_build.py --root PATH    # 다른 pilot 디렉토리에 대해 실행 (기본: 본 파일 기준 자동 탐지)

입력:
    {root}/agents/*.md
    {root}/skills/*/SKILL.md
    {root}/tools/*.py                                # docstring 만 추출 (CLI --help 캡처는 별도 단계)
    {root}/skills/context/shared/identity.yml

출력:
    {root}/docs/reference/agents/{name}.md
    {root}/docs/reference/skills/{name}.md
    {root}/docs/reference/tools/{tool_stem}.md
    {root}/docs/reference/identity.md

Exit:
    0 — 성공
    1 — --check 모드에서 drift 발견 또는 입력 디렉토리 누락
"""

from __future__ import annotations

import argparse
import ast
import posixpath
import re
import sys
from pathlib import Path

import yaml

# ── 입력·출력 경로 (root 기준 상대) ──────────────────────────────
SRC_AGENTS_DIR = "agents"
SRC_SKILLS_DIR = "skills"
SRC_TOOLS_DIR = "tools"
SRC_IDENTITY = "skills/context/shared/identity.yml"

OUT_AGENTS_DIR = "docs/reference/agents"
OUT_SKILLS_DIR = "docs/reference/skills"
OUT_TOOLS_DIR = "docs/reference/tools"
OUT_IDENTITY = "docs/reference/identity.md"

# 본 파일이 SSOT 가 아니므로 reference 에서 제외 (자기 자신·테스트 헬퍼 등).
TOOL_EXCLUDE_PREFIXES = ("_", "test_")

# GitHub blob URL 의 base — repo_url 변경 시 단일 지점 갱신.
GITHUB_BLOB_BASE = "https://github.com/radiostart/claude-plugins/blob/main/pilot"

# 마크다운 inline link: `](path)` 의 path 부분. 외부 URL·anchor·mailto 는 건드리지 않는다.
_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
_PLUGIN_ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"

# pilot/ 기준 path → site 의 reference/ 안 path 매핑.
# 이 두 패턴에 매치되는 link 만 *site internal* 로 변환되고, 나머지는 GitHub URL 로 간다.
_INTERNAL_AGENT_RE = re.compile(r"^agents/(pilot-[\w-]+)\.md$")
_INTERNAL_SKILL_RE = re.compile(r"^skills/([\w-]+)/SKILL\.md$")


def site_path_for(pilot_rel_path: str) -> str | None:
    """pilot/ 기준 path 가 site 의 reference/ 안에 매핑되면 site path 반환, 아니면 None.

    예:
        agents/pilot-planner.md           → reference/agents/pilot-planner.md
        skills/tdd/SKILL.md               → reference/skills/tdd.md
        skills/context/lifecycle/foo.md   → None (사이트에 없음, GitHub URL 로 fallback)
        tools/orchestrate-load.py         → None (tool 변환은 stem 기반이라 별도 매핑 — site internal 변환 대상 아님)
    """
    m = _INTERNAL_AGENT_RE.match(pilot_rel_path)
    if m:
        return f"reference/agents/{m.group(1)}.md"
    m = _INTERNAL_SKILL_RE.match(pilot_rel_path)
    if m:
        return f"reference/skills/{m.group(1)}.md"
    return None


# ── 공통 파서 ─────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """YAML frontmatter(`---` ... `---`) 분리. (meta, body) 반환. frontmatter 없으면 ({}, text)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fm_text = text[4:end]
    body = text[end + len("\n---\n") :]
    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def rewrite_links(text: str, source_rel_dir: str, output_rel_dir: str) -> str:
    """markdown inline link 를 site internal 또는 GitHub URL 로 재작성.

    - `source_rel_dir`: 원본 파일의 pilot/ 기준 상대 디렉토리 (예: 'agents', 'skills/project').
      SKILL.md 의 `../X` 같은 상대 link 를 해석할 때 base 로 사용.
    - `output_rel_dir`: 생성될 site 페이지의 reference/ 기준 디렉토리 (예: 'agents', 'skills').
      site internal link 의 상대 path 를 계산할 때 from 으로 사용.

    변환 규칙 (우선순위 순):
        외부 URL · anchor · mailto    → 변경 없음
        site internal 매핑 가능        → reference/ 안의 상대 path (예: '../agents/pilot-planner.md')
        pilot/ 안의 그 외 path        → GITHUB_BLOB_BASE/{pilot_path}
        pilot/ 밖으로 나가는 상대     → 원본 유지 (사용자 검토용)
    """

    def _replace(match: re.Match[str]) -> str:
        link = match.group(1)
        if link.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)

        # pilot/ 기준 path 로 정규화.
        if link.startswith(_PLUGIN_ROOT_PREFIX):
            pilot_path = link[len(_PLUGIN_ROOT_PREFIX) :]
        else:
            pilot_path = posixpath.normpath(posixpath.join(source_rel_dir, link))
            if pilot_path.startswith(".."):
                return match.group(0)

        # 1) site internal 매핑 시도 — Reference 안의 agent / skill 페이지로.
        site_path = site_path_for(pilot_path)
        if site_path:
            rel = posixpath.relpath(site_path, f"reference/{output_rel_dir}")
            return f"]({rel})"

        # 2) 그 외 → GitHub blob URL.
        return f"]({GITHUB_BLOB_BASE}/{pilot_path})"

    return _LINK_RE.sub(_replace, text)


def strip_wrapper_quote(body: str) -> str:
    """본문 시작의 `>` 인용 블록(wrapper 안내) 1 개 제거.

    에이전트 wrapper 의 첫 블록은 사용자 facing 정보가 아니라 호출자(Claude Code)용
    안내라서 reference 페이지에서 빼는 것이 옳다. 인용 블록이 없으면 그대로 반환.
    """
    lines = body.splitlines(keepends=True)
    i = 0
    # 시작 빈 줄 skip
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines) or not lines[i].lstrip().startswith(">"):
        return body
    # 인용 블록 끝까지 skip ('>' 라인 + 이어지는 빈 줄 또는 '>' 라인)
    while i < len(lines) and (lines[i].lstrip().startswith(">") or lines[i].strip() == ""):
        i += 1
        # 인용 블록 다음의 빈 줄 1 개까지 skip 해서 markdown 이 깔끔하게 시작
        if i < len(lines) and lines[i].strip() != "" and not lines[i].lstrip().startswith(">"):
            break
    return "".join(lines[i:])


# ── 변환 함수 ─────────────────────────────────────────────────


def transform_agent(src_path: Path) -> str:
    text = src_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    name = meta.get("name", src_path.stem)
    description = (meta.get("description") or "").strip()
    body_stripped = strip_wrapper_quote(body).lstrip("\n").rstrip() + "\n"
    body_rewritten = rewrite_links(
        body_stripped,
        source_rel_dir=SRC_AGENTS_DIR,
        output_rel_dir="agents",
    )
    desc_block = f"> {description}\n\n" if description else ""
    return f"# `@{name}`\n\n{desc_block}{body_rewritten}"


def transform_skill(src_dir: Path) -> str | None:
    skill_md = src_dir / "SKILL.md"
    if not skill_md.is_file():
        return None
    text = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    name = meta.get("name", src_dir.name)
    description = (meta.get("description") or "").strip()
    body_stripped = body.lstrip("\n").rstrip() + "\n"
    desc_block = f"> {description}\n\n" if description else ""
    # 기존 SKILL.md 가 본문 시작에 `# /name` 헤딩을 가진 경우 중복 회피 — body 의 H1 한 줄 제거.
    body_lines = body_stripped.splitlines(keepends=True)
    if body_lines and body_lines[0].lstrip().startswith("# "):
        body_lines = body_lines[1:]
        # 다음 빈 줄도 skip
        while body_lines and body_lines[0].strip() == "":
            body_lines = body_lines[1:]
    body_final = "".join(body_lines)
    body_rewritten = rewrite_links(
        body_final,
        source_rel_dir=f"{SRC_SKILLS_DIR}/{src_dir.name}",
        output_rel_dir="skills",
    )
    return f"# `/{name}`\n\n{desc_block}{body_rewritten}"


def transform_tool(src_path: Path) -> str | None:
    """tool/*.py 의 module docstring 만 추출. CLI --help 캡처는 별도 단계 (후속 강화)."""
    if src_path.suffix != ".py":
        return None
    if any(src_path.name.startswith(p) for p in TOOL_EXCLUDE_PREFIXES):
        return None
    try:
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    docstring = (ast.get_docstring(tree) or "").strip()
    if not docstring:
        return None
    quoted = "\n".join(f"> {ln}" if ln else ">" for ln in docstring.splitlines())
    return (
        f"# `{src_path.name}`\n\n"
        f"{quoted}\n\n"
        f"소스: [`tools/{src_path.name}`]({GITHUB_BLOB_BASE}/tools/{src_path.name})\n"
    )


def _md_escape_cell(value: str) -> str:
    """markdown 표 셀에 들어가는 값의 `|` 만 escape. 줄바꿈은 `<br>` 로 변환."""
    return value.replace("|", "\\|").replace("\n", "<br>")


def transform_identity(yml_path: Path) -> str:
    data = yaml.safe_load(yml_path.read_text(encoding="utf-8")) or {}
    out: list[str] = [
        "# Identity SSOT\n\n",
        "`skills/context/shared/identity.yml` 의 페르소나·에이전트 계약 SSOT 를 표로 추출한 결과.\n\n",
    ]
    agents = data.get("agents") or {}
    if agents:
        out.append("## Agents\n\n")
        out.append("| agent | output | min_evidence |\n")
        out.append("|---|---|---|\n")
        for name, fields in agents.items():
            fields = fields or {}
            output = _md_escape_cell(str(fields.get("output", "")))
            mev = _md_escape_cell(str(fields.get("min_evidence", "")))
            out.append(f"| `{name}` | `{output}` | `{mev}` |\n")
        out.append("\n")
    personas = data.get("personas") or {}
    if personas:
        out.append("## Personas\n\n")
        out.append("| persona | archetype | voice | phrasing | forbid |\n")
        out.append("|---|---|---|---|---|\n")
        for name, fields in personas.items():
            fields = fields or {}
            arch = _md_escape_cell(str(fields.get("archetype", "")))
            voice = _md_escape_cell(str(fields.get("voice", "")))
            phrasing = _md_escape_cell(str(fields.get("phrasing", "")))
            forbid_list = fields.get("forbid") or []
            forbid = "<br>".join(_md_escape_cell(str(f)) for f in forbid_list)
            out.append(f"| `{name}` | {arch} | {voice} | {phrasing} | {forbid} |\n")
    return "".join(out)


# ── 빌드·검증 ─────────────────────────────────────────────────


def build_category_index(title: str, entries: list[tuple[str, str]]) -> str:
    """카테고리 index.md 생성. entries 는 (link_target_filename, description) 의 정렬된 리스트.

    카드 link 가 디렉토리 자체로 가는 INFO warning 을 피하기 위한 진입 페이지 — 카테고리 안의 모든
    항목을 알파벳 순으로 나열한다.
    """
    lines = [f"# {title}\n\n", f"전체 {len(entries)} 항목 — `pilot/` SSOT 에서 자동 추출.\n\n"]
    for filename, description in entries:
        display = filename[:-3] if filename.endswith(".md") else filename
        if description:
            lines.append(f"- [`{display}`]({filename}) — {description}\n")
        else:
            lines.append(f"- [`{display}`]({filename})\n")
    return "".join(lines)


def _extract_description(text: str) -> str:
    """frontmatter description 추출 (`>` 또는 `|` block scalar 포함). 1 줄로 정리."""
    meta, _ = parse_frontmatter(text)
    desc = (meta.get("description") or "").strip()
    # YAML block scalar 가 join 된 결과의 줄바꿈을 공백으로.
    return " ".join(desc.split())


def build(root: Path) -> dict[Path, str]:
    """모든 generated 파일들의 (절대 경로 → 내용) 매핑.

    순서: agents → agents/index → skills → skills/index → tools → tools/index → identity.
    """
    result: dict[Path, str] = {}

    agents_src = root / SRC_AGENTS_DIR
    agents_out = root / OUT_AGENTS_DIR
    agent_entries: list[tuple[str, str]] = []
    if agents_src.is_dir():
        for f in sorted(agents_src.glob("*.md")):
            result[agents_out / f.name] = transform_agent(f)
            agent_entries.append((f.name, _extract_description(f.read_text(encoding="utf-8"))))
    if agent_entries:
        result[agents_out / "index.md"] = build_category_index("Agents", agent_entries)

    skills_src = root / SRC_SKILLS_DIR
    skills_out = root / OUT_SKILLS_DIR
    skill_entries: list[tuple[str, str]] = []
    if skills_src.is_dir():
        for d in sorted(p for p in skills_src.iterdir() if p.is_dir()):
            content = transform_skill(d)
            if content is not None:
                result[skills_out / f"{d.name}.md"] = content
                skill_md = d / "SKILL.md"
                skill_entries.append((f"{d.name}.md", _extract_description(skill_md.read_text(encoding="utf-8"))))
    if skill_entries:
        result[skills_out / "index.md"] = build_category_index("Skills", skill_entries)

    tools_src = root / SRC_TOOLS_DIR
    tools_out = root / OUT_TOOLS_DIR
    tool_entries: list[tuple[str, str]] = []
    if tools_src.is_dir():
        for f in sorted(tools_src.glob("*.py")):
            content = transform_tool(f)
            if content is not None:
                result[tools_out / f"{f.stem}.md"] = content
                # tool 은 module docstring 첫 줄을 description 으로 사용.
                try:
                    tree = ast.parse(f.read_text(encoding="utf-8"))
                    doc = (ast.get_docstring(tree) or "").strip()
                    first_line = doc.splitlines()[0] if doc else ""
                except (OSError, SyntaxError):
                    first_line = ""
                tool_entries.append((f"{f.stem}.md", first_line))
    if tool_entries:
        result[tools_out / "index.md"] = build_category_index("Tools", tool_entries)

    identity_src = root / SRC_IDENTITY
    if identity_src.is_file():
        result[root / OUT_IDENTITY] = transform_identity(identity_src)

    return result


def write_files(files: dict[Path, str]) -> int:
    for p, content in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return len(files)


# 정리 대상 3 개 카테고리 디렉터리. `docs/reference/index.md`(커밋본)·`identity.md` 는
# 이 목록 밖이라 대상이 아니다.
_STALE_CLEANUP_DIRS = (OUT_AGENTS_DIR, OUT_SKILLS_DIR, OUT_TOOLS_DIR)


def cleanup_stale_outputs(root: Path, files: dict[Path, str]) -> int:
    """이번 build 산출 집합에 없는 카테고리별 `*.md` 를 삭제하고 삭제 건수를 반환한다.

    `docs/reference/{agents,skills,tools}/` 3 개 디렉터리만 스캔. 카테고리별
    build 산출이 **1 건 이상일 때만** 그 디렉터리를 정리한다 — `--root` 가 부분
    트리(예: 테스트 fixture root)를 가리켜 해당 카테고리 산출이 0 건일 때 기존
    산출물을 일괄 오삭제하는 사고를 방지하기 위함.
    """
    removed = 0
    for out_rel in _STALE_CLEANUP_DIRS:
        out_dir = root / out_rel
        produced = {p for p in files if p.parent == out_dir}
        if not produced or not out_dir.is_dir():
            continue
        for existing in out_dir.glob("*.md"):
            if existing not in produced:
                existing.unlink()
                removed += 1
    return removed


def check_files(files: dict[Path, str]) -> list[Path]:
    """디스크 상태가 generated 와 다른 경로 목록 반환 (없으면 [])."""
    diffs: list[Path] = []
    for p, content in files.items():
        if not p.is_file():
            diffs.append(p)
            continue
        if p.read_text(encoding="utf-8") != content:
            diffs.append(p)
    return diffs


# ── 진입점 ────────────────────────────────────────────────────


def detect_root(here: Path) -> Path:
    """본 파일 위치 기준으로 pilot 디렉토리 탐지: tools/ 의 상위."""
    return here.resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="pilot docs_build — agents/skills/tools/identity SSOT 추출."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="생성하지 않고 디스크 상태가 source 와 일치하는지 검증 (drift 시 exit 1)",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="pilot 디렉토리 경로 (기본: 본 파일의 parent.parent)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else detect_root(Path(__file__))
    if not root.is_dir():
        print(f"root 디렉토리 없음: {root}", file=sys.stderr)
        return 1

    files = build(root)
    if args.check:
        diffs = check_files(files)
        if diffs:
            print("docs drift detected — `python3 pilot/tools/docs_build.py` 재실행 필요:", file=sys.stderr)
            for p in diffs:
                try:
                    rel = p.relative_to(root)
                except ValueError:
                    rel = p
                print(f"  - {rel}", file=sys.stderr)
            return 1
        return 0

    n = write_files(files)
    print(f"docs_build: wrote {n} files under {root / 'docs/reference'}", file=sys.stderr)
    removed = cleanup_stale_outputs(root, files)
    if removed:
        print(f"docs_build: removed {removed} stale file(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
