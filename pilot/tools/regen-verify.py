#!/usr/bin/env python3
"""
pilot regen-verify — `--regen-agents` 후 수동 편집 영역 보존 검증.

`prompts/*.md` 의 `<!-- [analyze-managed] -->` 주석이 달린 섹션은 regen 으로
덮어쓰여도 정상. 그 외 섹션 (사용자 수동 편집 영역) 이 변경됐다면 위반.

본 도구는 regen 전 백업 (`.prompts.bak/{timestamp}/`) 과 현재 `prompts/` 의
non-managed 섹션을 비교하여 변경 라인을 보고한다.

Usage:
    python3 tools/regen-verify.py \\
      --before workspace/projects/{PROJECT}/.prompts.bak/{timestamp}/ \\
      --after  workspace/projects/{PROJECT}/prompts/

    --json 으로 JSON 출력 가능.

Exit:
    0 — 보존 영역 변경 없음 (안전)
    1 — 보존 영역 변경 감지 (사용자 검토 필요)
    2 — 입력 오류 (디렉터리 없음 등)
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

MANAGED_MARKER_RE = re.compile(r"^\s*<!--\s*\[analyze-managed\]\s*-->\s*$")
H2_RE = re.compile(r"^##\s+(?!#)(.+)$")


def parse_sections(text: str) -> list[dict]:
    """파일을 H2 단위로 분할.

    Returns:
        [{
          "title": "## ...",
          "managed": bool,           # 직전 라인이 [analyze-managed] 주석이면 True
          "start": int,              # 0-indexed 라인 번호 (H2 라인 자체)
          "end": int,                # 다음 H2 직전 (또는 EOF)
          "body_lines": [str, ...],  # H2 라인 포함 본문
        }, ...]
    또한 첫 H2 이전 영역 (preface) 도 단일 섹션으로 포함 (title=None).
    """
    lines = text.splitlines()
    sections: list[dict] = []
    current_start = 0
    current_title: str | None = None
    current_managed = False

    def push(end_idx: int):
        if current_title is None and end_idx == 0:
            return  # 빈 preface
        body = lines[current_start:end_idx]
        sections.append({
            "title": current_title,
            "managed": current_managed,
            "start": current_start,
            "end": end_idx,
            "body_lines": body,
        })

    for i, line in enumerate(lines):
        h2 = H2_RE.match(line)
        if not h2:
            continue
        # 직전 라인이 marker 인지 (빈 줄 허용)
        managed = False
        for j in range(i - 1, max(-1, i - 4), -1):
            if j < 0:
                break
            stripped = lines[j].strip()
            if not stripped:
                continue
            managed = bool(MANAGED_MARKER_RE.match(lines[j]))
            break
        # 이전 섹션 종료
        push(i)
        current_start = i
        current_title = h2.group(0).strip()
        current_managed = managed

    push(len(lines))
    return sections


def compare_files(before: Path, after: Path) -> dict:
    """두 파일의 non-managed 섹션 비교.

    Returns:
        {
          "file": str,
          "preserved_violations": [
            {"section": str, "diff": [str, ...]},
            ...
          ],
          "managed_changed": [str, ...],   # info 만 (변경 정상)
        }
    """
    before_text = before.read_text(encoding="utf-8")
    after_text = after.read_text(encoding="utf-8")
    before_sections = parse_sections(before_text)
    after_sections = parse_sections(after_text)

    # title → section 매핑 (title 이 같으면 매칭. 없으면 추가/삭제로 분류)
    by_title_before = {s["title"]: s for s in before_sections if s["title"]}
    by_title_after = {s["title"]: s for s in after_sections if s["title"]}

    preserved_violations: list[dict] = []
    managed_changed: list[str] = []

    common_titles = set(by_title_before) & set(by_title_after)
    for title in common_titles:
        b = by_title_before[title]
        a = by_title_after[title]
        # managed 여부는 after 기준 (regen 후 마커가 정확)
        is_managed = a["managed"] or b["managed"]
        if "\n".join(b["body_lines"]) == "\n".join(a["body_lines"]):
            continue
        if is_managed:
            managed_changed.append(title)
        else:
            diff = list(difflib.unified_diff(
                b["body_lines"], a["body_lines"],
                lineterm="", n=2,
                fromfile=f"before/{title}",
                tofile=f"after/{title}",
            ))
            preserved_violations.append({"section": title, "diff": diff})

    # 추가/삭제된 섹션
    added = sorted(set(by_title_after) - set(by_title_before))
    removed = sorted(set(by_title_before) - set(by_title_after))
    for title in added:
        sec = by_title_after[title]
        if not sec["managed"]:
            preserved_violations.append({
                "section": title,
                "diff": [f"+ (신규 섹션, [analyze-managed] 없음)"]
            })
    for title in removed:
        sec = by_title_before[title]
        if not sec["managed"]:
            preserved_violations.append({
                "section": title,
                "diff": [f"- (섹션 삭제됨, before 기준 [analyze-managed] 없음)"]
            })

    return {
        "file": after.name,
        "preserved_violations": preserved_violations,
        "managed_changed": managed_changed,
    }


def verify_dirs(before_dir: Path, after_dir: Path) -> list[dict]:
    results: list[dict] = []
    after_files = sorted(after_dir.glob("*.md"))
    for af in after_files:
        bf = before_dir / af.name
        if not bf.is_file():
            results.append({
                "file": af.name,
                "preserved_violations": [{
                    "section": "(전체 파일)",
                    "diff": ["+ (신규 파일, before 백업 없음)"]
                }],
                "managed_changed": [],
            })
            continue
        results.append(compare_files(bf, af))
    # before 에만 있는 파일
    before_files = sorted(before_dir.glob("*.md"))
    after_names = {p.name for p in after_files}
    for bf in before_files:
        if bf.name not in after_names:
            results.append({
                "file": bf.name,
                "preserved_violations": [{
                    "section": "(전체 파일)",
                    "diff": ["- (파일 삭제됨)"]
                }],
                "managed_changed": [],
            })
    return results


def render_text(reports: list[dict]) -> str:
    out = ["# regen-verify: 보존 영역 검사\n"]
    has_violation = any(r["preserved_violations"] for r in reports)
    for r in reports:
        out.append(f"## {r['file']}\n")
        if not r["preserved_violations"] and not r["managed_changed"]:
            out.append("- 보존 OK · managed 변경 없음")
        else:
            for v in r["preserved_violations"]:
                out.append(f"- ⚠️ 보존 위반: {v['section']}")
                for line in v["diff"][:10]:
                    out.append(f"    {line}")
                if len(v["diff"]) > 10:
                    out.append(f"    ... (+{len(v['diff']) - 10} 줄)")
            for title in r["managed_changed"]:
                out.append(f"- info: managed 섹션 갱신됨 — {title}")
        out.append("")
    out.append("=== 결과 ===")
    out.append("FAIL" if has_violation else "PASS")
    return "\n".join(out) + "\n"


def render_json(reports: list[dict]) -> str:
    has_violation = any(r["preserved_violations"] for r in reports)
    return json.dumps({
        "passed": not has_violation,
        "files": reports,
    }, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="pilot regen-verify")
    parser.add_argument("--before", required=True, help="regen 전 백업 디렉터리")
    parser.add_argument("--after", required=True, help="regen 후 prompts 디렉터리")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    before = Path(args.before)
    after = Path(args.after)
    if not before.is_dir():
        print(f"error: --before not a dir: {before}", file=sys.stderr)
        return 2
    if not after.is_dir():
        print(f"error: --after not a dir: {after}", file=sys.stderr)
        return 2

    reports = verify_dirs(before, after)
    if args.json:
        print(render_json(reports))
    else:
        print(render_text(reports), end="")

    has_violation = any(r["preserved_violations"] for r in reports)
    return 1 if has_violation else 0


if __name__ == "__main__":
    sys.exit(main())
