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


def rewrite_links(text: str, source_rel_dir: str) -> str:
    """모든 markdown inline link 의 path 를 GitHub blob URL 로 변환.

    `source_rel_dir` 는 원본 파일의 pilot/ 기준 상대 디렉토리 (예: 'agents', 'skills/project').
    SKILL.md 등은 원본 위치를 기준으로 `../X` 같은 상대 path 를 해석하므로 이 인자가 필요하다.

    변환 규칙:
        ${CLAUDE_PLUGIN_ROOT}/Y       → GITHUB_BLOB_BASE/Y
        외부 URL (http/https/mailto)  → 변경 없음
        anchor `#fragment`            → 변경 없음
        상대 path                     → source_rel_dir 기준 resolve → GITHUB_BLOB_BASE/{resolved}

    site 내부 cross-link 로의 변환은 step 7 (README 슬림화 + cross-link 정책) 에서 점진 적용 예정.
    """

    def _replace(match: re.Match[str]) -> str:
        link = match.group(1)
        if link.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        if link.startswith(_PLUGIN_ROOT_PREFIX):
            target = link[len(_PLUGIN_ROOT_PREFIX) :]
            return f"]({GITHUB_BLOB_BASE}/{target})"
        # 상대 path — source_rel_dir 기준 resolve
        resolved = posixpath.normpath(posixpath.join(source_rel_dir, link))
        if resolved.startswith(".."):
            # pilot/ 밖으로 나간 link — 보수적으로 원본 유지 (사용자 검토용)
            return match.group(0)
        return f"]({GITHUB_BLOB_BASE}/{resolved})"

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
    body_rewritten = rewrite_links(body_stripped, source_rel_dir=SRC_AGENTS_DIR)
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
    body_rewritten = rewrite_links(body_final, source_rel_dir=f"{SRC_SKILLS_DIR}/{src_dir.name}")
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


def build(root: Path) -> dict[Path, str]:
    """모든 generated 파일들의 (절대 경로 → 내용) 매핑. 순서: agents → skills → tools → identity."""
    result: dict[Path, str] = {}

    agents_src = root / SRC_AGENTS_DIR
    agents_out = root / OUT_AGENTS_DIR
    if agents_src.is_dir():
        for f in sorted(agents_src.glob("*.md")):
            result[agents_out / f.name] = transform_agent(f)

    skills_src = root / SRC_SKILLS_DIR
    skills_out = root / OUT_SKILLS_DIR
    if skills_src.is_dir():
        for d in sorted(p for p in skills_src.iterdir() if p.is_dir()):
            content = transform_skill(d)
            if content is not None:
                result[skills_out / f"{d.name}.md"] = content

    tools_src = root / SRC_TOOLS_DIR
    tools_out = root / OUT_TOOLS_DIR
    if tools_src.is_dir():
        for f in sorted(tools_src.glob("*.py")):
            content = transform_tool(f)
            if content is not None:
                result[tools_out / f"{f.stem}.md"] = content

    identity_src = root / SRC_IDENTITY
    if identity_src.is_file():
        result[root / OUT_IDENTITY] = transform_identity(identity_src)

    return result


def write_files(files: dict[Path, str]) -> int:
    for p, content in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return len(files)


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
