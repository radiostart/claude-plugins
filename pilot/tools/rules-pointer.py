#!/usr/bin/env python3
"""
pilot rules-pointer — 경로 트리거 도메인 규칙 파일(`.claude/rules/pilot-{domain}.md`) 생성·점검·보완 훅 CLI (#30 C1).

판정·생성 로직은 `doctor/rules_pointer.py` 가 소유한다(doctor 와 판정 1벌). 이 파일은 CLI 래퍼.

Usage:
    python3 pilot/tools/rules-pointer.py (--all | --domain D) [--workspace PATH]            # 미리보기
    python3 pilot/tools/rules-pointer.py (--all | --domain D) --write [--workspace PATH]    # 생성·갱신 (관리 마커 파일만 덮어씀)
    python3 pilot/tools/rules-pointer.py (--all | --domain D) --check [--workspace PATH]    # 디스크 vs 재생성 대조
    python3 pilot/tools/rules-pointer.py --hook [--workspace PATH] < hook-json            # PostToolUse Edit|Write 보완 훅

    `/pilot:learn` Phase 5 가 MANIFEST 등록 후 `--all --write` 를 호출한다 (도메인 간 배타 규칙 때문에 --all).
    `--domain` 도 전 도메인을 집계한 뒤 그 도메인만 다룬다. 규칙은 세션당 1회 로드 — 생성·갱신분은 새 세션부터.

paths 도출·포인터·캡·훅 규칙: doctor/rules_pointer.py 모듈 docstring.

Exit:
    0 — 성공 (훅은 항상 0 — 무음 실패)
    1 — --check 불일치 (missing · differs)
    2 — 인자 오류 · MANIFEST 부재 · 미등록 도메인 · context-search 로드 실패
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from doctor import rules_pointer as rp  # noqa: E402


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rules-pointer.py", description="경로 트리거 도메인 규칙 파일 생성·점검·훅")
    p.add_argument("--workspace", default="workspace", help="workspace 경로 (기본: workspace)")
    scope = p.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="MANIFEST 등록 도메인 전부")
    scope.add_argument("--domain", default=None, help="도메인 1개 (전 도메인 집계 후 이 도메인만)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="규칙 파일 생성·갱신")
    mode.add_argument("--check", action="store_true", help="디스크 파일과 재생성 결과 대조 (불일치 exit 1)")
    mode.add_argument("--hook", action="store_true", help="stdin 훅 JSON → additionalContext (PostToolUse)")
    p.add_argument("--format", choices=("md", "json"), default="md")
    return p


def main(argv: "list[str] | None" = None) -> int:
    parser = _build_argparser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    workspace = Path(args.workspace)

    if args.hook:
        try:
            payload = json.load(sys.stdin)
            file_path = str(payload.get("tool_input", {}).get("file_path", "") or "")
            session_id = str(payload.get("session_id", "") or "")
            text = rp.match_hook(workspace, file_path, session_id)
        except Exception:
            return 0  # 훅은 무음 실패 — 작업을 막지 않는다
        if text:
            print(json.dumps(
                {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}},
                ensure_ascii=False,
            ))
        return 0

    if not args.all and not args.domain:
        print("--all 또는 --domain 이 필요합니다", file=sys.stderr)
        return 2
    if not (workspace / "context" / "MANIFEST.md").is_file():
        print(f"MANIFEST 없음: {workspace / 'context' / 'MANIFEST.md'}", file=sys.stderr)
        return 2
    domains = None if args.all else [args.domain]
    try:
        if args.write:
            statuses, info = rp.write_rules_files(workspace, domains)
            if args.format == "json":
                print(json.dumps({"statuses": statuses, "info": info}, ensure_ascii=False, indent=2))
            else:
                for d, s in statuses:
                    print(f"{s:18s} {rp.rules_path(workspace, d)}")
                for m in info:
                    print(f"[INFO] {m}")
            return 0
        if args.check:
            rows = rp.check_rules_files(workspace, domains)
            bad = [r for r in rows if r[1] in ("missing", "differs")]
            if args.format == "json":
                print(json.dumps({"rows": rows, "ok": not bad}, ensure_ascii=False, indent=2))
            else:
                for d, s, note in rows:
                    print(f"{s:10s} {d:20s} {note}")
            return 1 if bad else 0
        derived = rp.derive_paths(workspace, domains)
        out: dict[str, dict] = {}
        for d in derived:
            content, info = rp.build_rules_file(workspace, d, derived)
            out[d] = {"content": content, "info": info}
        if args.format == "json":
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for d, entry in out.items():
                print(f"# {rp.rules_path(workspace, d)}")
                print(entry["content"] if entry["content"] is not None else "(생성 대상 아님)")
                for m in entry["info"]:
                    print(f"[INFO] {m}")
        return 0
    except rp.RulesPointerError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
