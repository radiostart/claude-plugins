#!/usr/bin/env python3
"""
memory-hint — Claude Code auto-memory 에서 현재 작업과 관련된 메모만 추려
스킬 진입 시 컨텍스트 선조회에 사용한다.

작동 흐름:
  1. 현재 cwd → slug (슬래시→대시) → `~/.claude/projects/{slug}/memory/MEMORY.md`
  2. MEMORY.md 인덱스 파싱 (`- [Title](file.md) — hook` 형식)
  3. 각 항목의 Title + hook + 파일 frontmatter(description) 를 입력 키워드와 매칭
  4. 점수 ≥ 1 인 항목만 상위 N 개 출력

출력 예:
  [memory-hint] 관련 메모 2 건:
    - project_presend_admin_review.md (점수 3) — 미송선발송 관리자 화면 기획서 vs 구현 점검 결과
    - feedback_policy_review_mode.md (점수 1) — 정책 이행 점검 시 소스 수정 금지
  다음 단계에서 Read 후 컨텍스트 반영 권장.

출력 없음 = auto-memory 가 없거나 매칭 실패 (정상).

Usage:
    python3 memory-hint.py "{PROJECT_OR_ARGS}" [KEYWORDS...]

    첫 번째 인자는 프로젝트명 또는 스킬 인자 전체 (공백 포함 가능, 따옴표 권장).
    추가 키워드는 positional 로 여러 개.
"""

import os
import re
import sys
from pathlib import Path

MAX_RESULTS = 5
MIN_SCORE = 1


def slug_for_cwd(cwd: Path) -> str:
    # Claude Code harness 와 동일한 규칙: 경로의 슬래시를 대시로 치환
    return str(cwd).replace("/", "-")


def memory_dir_candidates(cwd: Path) -> list[Path]:
    """현재 cwd 용 memory 디렉토리 + worktree fallback (원본 cwd)."""
    home = Path.home()
    base = home / ".claude" / "projects"
    primary = base / slug_for_cwd(cwd) / "memory"

    # worktree 슬롯 감지: ...--claude-worktrees-* 패턴
    # 원본 cwd 는 `--claude-worktrees-` prefix 이전 부분을 슬래시로 복원
    candidates = [primary]
    slug = slug_for_cwd(cwd)
    marker = "--claude-worktrees-"
    if marker in slug:
        parent_slug = slug.split(marker, 1)[0]
        parent = base / parent_slug / "memory"
        if parent != primary:
            candidates.append(parent)
    return candidates


def parse_index(index_path: Path) -> list[dict]:
    """MEMORY.md 인덱스에서 (title, filename, hook) 추출."""
    if not index_path.is_file():
        return []
    entries: list[dict] = []
    try:
        text = index_path.read_text(encoding="utf-8")
    except Exception:
        return []
    # 패턴: `- [Title](file.md) — hook` 또는 `- [Title](file.md) - hook`
    line_re = re.compile(r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s*[—\-:]\s*(.+)$")
    for line in text.splitlines():
        stripped = line.strip()
        m = line_re.match(stripped)
        if not m:
            continue
        entries.append(
            {
                "title": m.group(1).strip(),
                "filename": m.group(2).strip(),
                "hook": m.group(3).strip(),
            }
        )
    return entries


def read_description(memory_dir: Path, filename: str) -> str:
    """파일 frontmatter 의 description 필드 추출."""
    path = memory_dir / filename
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def tokenize(s: str) -> list[str]:
    """간단한 토큰화: 한/영/숫자 단어 추출 + 소문자화."""
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_가-힣]+", s) if t]


def score_entry(entry: dict, description: str, keywords: list[str]) -> int:
    """title + hook + description + filename 에 키워드가 등장한 횟수."""
    if not keywords:
        return 0
    haystack = " ".join(
        [entry.get("title", ""), entry.get("hook", ""), description, entry.get("filename", "")]
    ).lower()
    score = 0
    for kw in keywords:
        if not kw:
            continue
        if kw in haystack:
            score += haystack.count(kw)
    return score


def main() -> int:
    if len(sys.argv) < 2:
        # 인자 없으면 조용히 빈 출력 (정상 — 스킬이 호출만 하고 인자 미제공)
        return 0

    raw_args = sys.argv[1:]
    # 첫 인자 + 나머지 모두를 한 묶음으로 토큰화
    merged = " ".join(raw_args)
    keywords = list(dict.fromkeys(tokenize(merged)))  # 중복 제거, 순서 보존

    if not keywords:
        return 0

    cwd = Path.cwd()
    for mem_dir in memory_dir_candidates(cwd):
        index = mem_dir / "MEMORY.md"
        if not index.is_file():
            continue
        entries = parse_index(index)
        if not entries:
            continue

        scored: list[tuple[int, dict, str]] = []
        for e in entries:
            desc = read_description(mem_dir, e["filename"])
            s = score_entry(e, desc, keywords)
            if s >= MIN_SCORE:
                scored.append((s, e, desc))

        if not scored:
            continue

        scored.sort(key=lambda x: x[0], reverse=True)
        scored = scored[:MAX_RESULTS]

        rel = mem_dir.relative_to(Path.home()) if mem_dir.is_relative_to(Path.home()) else mem_dir
        print(f"[memory-hint] 관련 메모 {len(scored)} 건 ({rel}):")
        for s, e, desc in scored:
            label = desc or e["hook"]
            # 200 자 미만으로 truncate
            if len(label) > 160:
                label = label[:157] + "..."
            print(f"  - {e['filename']} (점수 {s}) — {label}")
        print("다음 단계에서 해당 파일을 Read 하여 컨텍스트에 반영 권장.")
        return 0  # 첫 매칭 디렉토리만 보고

    # 매칭 없음 — 조용히 종료 (정상)
    return 0


if __name__ == "__main__":
    sys.exit(main())
