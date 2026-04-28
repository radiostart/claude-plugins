#!/usr/bin/env python3
"""
pilot slack notifier — 프로젝트별 Slack Incoming Webhook 으로 알림 전송.

설정 SSOT: `workspace/projects/{PROJECT}/.slack.env`
    SLACK_WEBHOOK_URL=...          (필수. 비어있거나 파일 없음 → no-op)
    SLACK_CHANNEL=#project-x       (표시용 라벨)
    SLACK_EVENTS=complete,approval,pr (생략 시 모두)

No-op 조건 (어느 하나라도 → exit 0, 파이프라인 차단 금지):
    - 프로젝트 미해석 (workspace/STATE.md 부재)
    - .slack.env 부재
    - SLACK_WEBHOOK_URL 비어있음
    - 이벤트가 SLACK_EVENTS 목록 밖
    - .slack.env 가 git tracked 상태 → 전송 차단 + [CRITICAL] 경고

Usage:
    python3 slack-notify.py --event {complete|approval|pr}
                           [--project PATH] [--workspace PATH]
                           [--message TEXT] [--feature-id ID]

모든 실패 경로에서 exit 0 을 반환한다 (훅·파이프라인이 알림 실패 때문에
차단되지 않도록). stderr 에 원인만 1줄 기록.
"""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


SUPPORTED_EVENTS = ("complete", "approval", "pr")
DEFAULT_EVENTS = ("complete", "approval", "pr")
HTTP_TIMEOUT_SEC = 3
HOOK_DETAIL_MAX = 500


def parse_hook_stdin(raw: str) -> tuple[str, str]:
    """Claude Code 훅(PermissionRequest / Notification) stdin JSON 을 (event, message) 로.

    슬랙 훅 어댑터(`hooks/slack-notify.sh`) 의 인라인 파싱 로직을 이전한 것.
    실패 경로에서도 (event, message) 기본값을 돌려 — 호출측에서 무조건 메시지를
    송출할 수 있게 한다.
    """
    try:
        d = json.loads(raw or "{}")
    except Exception:
        return "Unknown", "승인이 필요합니다"

    event = d.get("hook_event_name") or "Unknown"
    if event == "PermissionRequest":
        tool = d.get("tool_name") or ""
        tin = d.get("tool_input") or {}
        # 도구별 주요 필드: Bash=command, Edit/Write=file_path, MCP=자유. description 은 거의 공통.
        detail = (
            tin.get("command")
            or tin.get("file_path")
            or tin.get("description")
            or ""
        )
        truncated = len(detail) > HOOK_DETAIL_MAX
        if truncated:
            detail = detail[:HOOK_DETAIL_MAX] + "\n… (잘림)"
        if tool and detail:
            msg = f"[{tool}]\n```\n{detail}\n```"
        elif tool:
            msg = f"[{tool}]"
        else:
            msg = "승인이 필요합니다"
    else:
        # Notification 또는 미지 이벤트 — message > title > 기본 문구.
        msg = d.get("message") or d.get("title") or "승인이 필요합니다"
    return event, msg


def parse_slack_env(path: Path) -> dict[str, str] | None:
    """`.slack.env` 파일을 KEY=VALUE 로 파싱. 파일 없음 → None."""
    if not path.is_file():
        return None
    data: dict[str, str] = {}
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                data[k] = v
    except Exception:
        return None
    return data


def _active_project_name(state_md: Path) -> str | None:
    if not state_md.is_file():
        return None
    try:
        for line in state_md.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("|") and "진행중" in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 3 and cells[2] == "진행중":
                    return cells[1]
    except Exception:
        return None
    return None


def resolve_project(workspace: Path, explicit: str | None) -> Path | None:
    """프로젝트 폴더 경로 결정. --project 명시 우선, 없으면 STATE.md 진행중 사용."""
    if explicit:
        p = Path(explicit)
        if p.is_absolute() and p.is_dir():
            return p
        rel = workspace / explicit
        if rel.is_dir():
            return rel
        return None

    active = _active_project_name(workspace / "STATE.md")
    if not active:
        return None
    proj = workspace / "projects" / active
    return proj if proj.is_dir() else None


def is_tracked_by_git(file_path: Path) -> bool:
    """`.slack.env` 가 git 에 추적되고 있는지 확인. 리포 외부거나 git 부재 → False."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file_path.name],
            cwd=str(file_path.parent),
            capture_output=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def post_to_slack(url: str, text: str) -> tuple[bool, str]:
    """Slack Incoming Webhook 으로 POST. 실패 시 (False, 원인) 반환."""
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read(256).decode("utf-8", errors="replace")
            if 200 <= status < 300:
                return True, body
            return False, f"HTTP {status}: {body[:120]}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def build_message(
    event: str,
    env: dict[str, str],
    project_name: str,
    message: str | None,
    feature_id: str | None,
) -> str:
    """이벤트별 고정 텍스트 메시지. v1 은 Block Kit 미사용."""
    channel = env.get("SLACK_CHANNEL", "").strip()
    channel_tag = f" {channel}" if channel else ""
    prefix = f"[{project_name}]{channel_tag}"
    if event == "complete":
        feat = f" #{feature_id}" if feature_id else ""
        return f"✅ {prefix}{feat} 작업 완료 (evaluator READY)"
    if event == "approval":
        msg = message or "사용자 승인이 필요합니다"
        return f"⏸ {prefix} 승인 필요: {msg}"
    if event == "pr":
        # message 는 PR URL 또는 "title — URL" 자유 텍스트. /pilot:pr 가 채움.
        msg = message or "PR 생성됨"
        return f"🔗 {prefix} PR: {msg}"
    return f"[{event}] {prefix} {message or ''}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="pilot slack notifier")
    parser.add_argument(
        "--event",
        default=None,
        choices=SUPPORTED_EVENTS,
        help="이벤트 종류. --from-hook 사용 시 stdin 에서 'approval' 로 자동 결정.",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="프로젝트 폴더 경로 (생략 시 STATE.md 진행중 프로젝트 자동 해석)",
    )
    parser.add_argument(
        "--workspace", default="workspace", help="workspace 경로 (default: workspace)"
    )
    parser.add_argument("--message", default=None)
    parser.add_argument("--feature-id", default=None)
    parser.add_argument(
        "--from-hook",
        action="store_true",
        help="Claude Code 훅 stdin JSON 을 파싱해 approval 메시지를 구성한다 (--event/--message 무시).",
    )
    args = parser.parse_args(argv)

    # 훅 모드 — stdin JSON 에서 message 추출, event 는 항상 'approval'.
    if args.from_hook:
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
        _hook_event, hook_msg = parse_hook_stdin(raw)
        args.event = "approval"
        args.message = hook_msg

    if not args.event:
        print("slack-notify: --event 또는 --from-hook 가 필요합니다.", file=sys.stderr)
        return 0

    workspace = Path(args.workspace).resolve()
    proj = resolve_project(workspace, args.project)
    if proj is None:
        return 0

    slack_env = proj / ".slack.env"
    env = parse_slack_env(slack_env)
    if env is None:
        return 0

    webhook = env.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        print(
            f"slack-notify: {slack_env} 에 SLACK_WEBHOOK_URL 이 비어있어 알림을 건너뜁니다.",
            file=sys.stderr,
        )
        return 0

    events_raw = env.get("SLACK_EVENTS", "").strip() or ",".join(DEFAULT_EVENTS)
    events = {e.strip() for e in events_raw.split(",") if e.strip()}
    if args.event not in events:
        return 0

    # Critical defence: secret 이 채워진 파일이 git tracked 상태면 전송 차단.
    if is_tracked_by_git(slack_env):
        print(
            f"slack-notify: [CRITICAL] {slack_env} 가 git 에 추적되고 있습니다. "
            f"즉시 `git rm --cached {slack_env}` 실행 후 webhook URL 을 재발급하세요. "
            f"안전을 위해 이번 알림은 전송하지 않습니다.",
            file=sys.stderr,
        )
        return 0

    text = build_message(args.event, env, proj.name, args.message, args.feature_id)
    ok, info = post_to_slack(webhook, text)
    if not ok:
        print(f"slack-notify: 전송 실패 — {info}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
