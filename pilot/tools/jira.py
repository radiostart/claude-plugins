#!/usr/bin/env python3
"""
Jira issue fetcher / commenter (QA phase 어댑터).

`confluence.py` 와 같은 패턴을 따른다 — stdlib (`urllib.request` / `json` /
`base64`) 만 사용, 외부 의존성 없음.

Usage:
  python3 tools/jira.py fetch <KEY>            # GET /rest/api/3/issue/{KEY}
  python3 tools/jira.py comment <KEY> "<msg>"  # POST /rest/api/3/issue/{KEY}/comment

`list` 명령은 의도적으로 미구현 — 다건 추적은 Jira UI 가 SSOT.

Required env vars (둘 중 하나로 설정):
  1) 프로젝트 루트 `.env` 또는 `workspace/.env` 파일에 기록
  2) shell profile 에서 `export`

  ATLASSIAN_BASE_URL  — Atlassian Cloud 루트 URL (예: https://your-domain.atlassian.net)
                        Jira 와 Confluence 가 같은 사이트라면 본 키 하나로 양쪽 도구가 공용.
  ATLASSIAN_EMAIL     — Atlassian 계정 이메일
  ATLASSIAN_TOKEN     — Atlassian API 토큰 (https://id.atlassian.com/manage-profile/security/api-tokens)

  도구별 키 (JIRA_BASE_URL / JIRA_EMAIL / JIRA_TOKEN) 가 설정돼 있으면 그쪽이 우선
  — 기존 .env 와 backward compatible. 둘 다 부재 시 ATLASSIAN_* 권장 메시지를 안내.

Optional env var:
  JIRA_QA_PROJECT_KEY — 키 화이트리스트 (예: QAPRJ). 미설정 시 모든 `^[A-Z]+-\\d+$` 허용.
                       `workspace/context/config.md` 의 `jira_qa_project_key` 설정이 우선.

Exit codes:
  0 — 성공
  1 — 인자/환경/네트워크/HTTP/사용자 거절 등 모든 실패. comment 실패는 stderr 첫 줄에
      `[ERROR] COMMENT FAILED for {KEY}` 헤더 강제 출력.
"""

from __future__ import annotations

import sys
import os
import re
import json
import base64
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# tools/ 를 sys.path 에 추가 — sibling 모듈 `_net` import 용 (doctor.py 와 동일 패턴).
# script 실행·importlib 로드 양쪽에서 보장된다.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from _net import http_timeout, ssl_context  # noqa: E402
from _cred import resolve_credential, load_dotenv as _cred_load_dotenv  # noqa: E402

WORKSPACE_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))

KEY_FORMAT_RE = re.compile(r"^[A-Z]+-\d+$")


# ---------------------------------------------------------------------------
# .env loader (confluence.py 와 동일 정책 — JIRA_*/ATLASSIAN_* prefix 만 INFO 로 알린다)
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """프로젝트 루트 `.env` 또는 `workspace/.env` 에서 KEY=VALUE 로드.

    이미 환경에 있으면 덮어쓰지 않는다 (export 우선). credential 키가 .env 로 폴백되면
    stderr 에 INFO 한 줄 — non-interactive subshell 에서의 token drift failure mode 방지.
    """
    _cred_load_dotenv(
        candidates=[
            WORKSPACE_ROOT / ".env",
            WORKSPACE_ROOT / "workspace" / ".env",
        ],
        credential_prefixes=("JIRA_", "ATLASSIAN_"),
        info_message_fn=lambda src, keys: (
            f"[INFO] Loaded credentials from {src} (env var not set): {keys}."
        ),
    )


_load_dotenv()


# ---------------------------------------------------------------------------
# Credentials helpers
# ---------------------------------------------------------------------------

def _resolve_credential(jira_key: str, atlassian_key: str) -> str:
    """도구별 키 (JIRA_*) 우선, 부재 시 통합 키 (ATLASSIAN_*) fallback.

    두 키 모두 비어있으면 빈 문자열. 호출자가 missing 판정.
    """
    return resolve_credential(jira_key, atlassian_key)


def get_credentials(quiet: bool = False) -> tuple[str, str, str] | None:
    """Atlassian 자격정보를 도구별 (JIRA_*) → 통합 (ATLASSIAN_*) 순으로 해석해 반환.

    Args:
      quiet: True 이면 누락 시 stderr 출력·exit 없이 None 을 반환한다 (호출자가 stderr
             순서를 직접 통제할 때 — 예: `cmd_comment` 가 `COMMENT FAILED` 헤더를 line 1 로
             강제하기 위함). False (기본) 면 기존처럼 stderr 안내 후 exit 1.
    """
    base = _resolve_credential("JIRA_BASE_URL", "ATLASSIAN_BASE_URL").rstrip("/")
    email = _resolve_credential("JIRA_EMAIL", "ATLASSIAN_EMAIL")
    token = _resolve_credential("JIRA_TOKEN", "ATLASSIAN_TOKEN")
    missing = []
    if not base:
        missing.append("ATLASSIAN_BASE_URL  (예: https://your-domain.atlassian.net) — 또는 JIRA_BASE_URL")
    if not email:
        missing.append("ATLASSIAN_EMAIL     (Atlassian 계정 이메일) — 또는 JIRA_EMAIL")
    if not token:
        missing.append("ATLASSIAN_TOKEN     (https://id.atlassian.com/manage-profile/security/api-tokens) — 또는 JIRA_TOKEN")
    if missing:
        if quiet:
            return None
        print(
            "[ERROR] Atlassian env not set.\n"
            "Atlassian API token 발급: https://id.atlassian.com/manage-profile/security/api-tokens\n"
            "필요한 환경변수 (ATLASSIAN_* 권장 — Jira·Confluence 공용; JIRA_* 도 인식):\n"
            + "\n".join(f"  - {m}" for m in missing),
            file=sys.stderr,
        )
        sys.exit(1)
    return base, email, token


def _read_allowed_project_key() -> str | None:
    """화이트리스트 project key 해석.

    우선순위:
      1. `workspace/context/config.md` 의 `jira_qa_project_key` 설정
         (`## 설정` 표 행 `| jira_qa_project_key | KEY | ... |` 또는
          `- jira_qa_project_key: KEY` 라인 — 파서가 둘 다 처리)
      2. env `JIRA_QA_PROJECT_KEY`
      3. None (미설정)
    """
    path = WORKSPACE_ROOT / "workspace" / "context" / "config.md"
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if text:
            m = re.search(
                r"^\|\s*`?jira_qa_project_key`?\s*\|\s*`?([A-Z][A-Z0-9_]*)`?\s*\|",
                text,
                re.MULTILINE,
            )
            if not m:
                m = re.search(
                    r"^\s*[-*]?\s*`?jira_qa_project_key`?\s*:\s*`?([A-Z][A-Z0-9_]*)`?\s*$",
                    text,
                    re.MULTILINE,
                )
            if m:
                return m.group(1).strip()

    env_val = os.environ.get("JIRA_QA_PROJECT_KEY", "").strip()
    return env_val or None


# ---------------------------------------------------------------------------
# Key validation
# ---------------------------------------------------------------------------

def validate_key_format(key: str) -> None:
    """형식 검증 — `^[A-Z]+-\\d+$` 위배 시 stderr 출력 후 exit 1."""
    if not key or not KEY_FORMAT_RE.match(key):
        print(f"[ERROR] invalid key format: {key!r} (expected ^[A-Z]+-\\d+$)", file=sys.stderr)
        sys.exit(1)


def validate_key_whitelist(key: str) -> None:
    """화이트리스트 검증. 형식 검증은 호출 전에 끝나 있어야 한다.

    - 미설정 → silent pass.
    - 설정 + prefix 일치 → silent pass.
    - 설정 + 불일치 → stderr WARN + 진행 확인. non-TTY 면 fail-safe 거절 (exit 1).
    """
    allowed = _read_allowed_project_key()
    if not allowed:
        return
    actual_prefix = key.split("-", 1)[0]
    if actual_prefix == allowed:
        return

    print(
        f"[WARN] key project mismatch — expected prefix {allowed!r}, got {actual_prefix!r} "
        f"(key={key}). 다른 Jira project 의 이슈를 다루려고 합니다.",
        file=sys.stderr,
    )
    if not sys.stdin.isatty():
        print(
            "[ERROR] non-interactive stdin — fail-safe 로 거절. "
            "의도된 경우 `JIRA_QA_PROJECT_KEY` 또는 `workspace/context/config.md` 의 "
            "`jira_qa_project_key` 를 조정하세요.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Proceed anyway? [y/N]: ", end="", flush=True, file=sys.stderr)
    answer = sys.stdin.readline().strip().lower()
    if answer not in ("y", "yes"):
        print("aborted.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# ADF (Atlassian Document Format) → plain markdown-ish text
# ---------------------------------------------------------------------------

def adf_to_text(node) -> str:
    """ADF JSON 노드를 평문 (가벼운 markdown) 으로 변환.

    지원 노드: doc / paragraph / text(+marks: strong/em/code) / heading / hardBreak /
              bulletList / orderedList / listItem / codeBlock / blockquote / rule
    그 외 노드 (mediaSingle, table, ...) 는 자식 텍스트만 평탄화.
    """
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    if not isinstance(node, dict):
        return ""

    ntype = node.get("type", "")
    content = node.get("content") or []

    if ntype == "text":
        text = node.get("text", "")
        for mark in node.get("marks") or []:
            mt = mark.get("type")
            if mt == "strong":
                text = f"**{text}**"
            elif mt == "em":
                text = f"_{text}_"
            elif mt == "code":
                text = f"`{text}`"
            elif mt == "link":
                href = (mark.get("attrs") or {}).get("href", "")
                if href:
                    text = f"[{text}]({href})"
        return text

    if ntype == "hardBreak":
        return "\n"

    if ntype == "paragraph":
        return adf_to_text(content) + "\n\n"

    if ntype == "heading":
        level = (node.get("attrs") or {}).get("level", 1)
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 1
        level = max(1, min(6, level))
        return f"{'#' * level} {adf_to_text(content).strip()}\n\n"

    if ntype == "bulletList":
        out = []
        for li in content:
            inner = adf_to_text(li.get("content") or []).strip()
            if inner:
                # 다중행 list item: 첫 줄만 `- ` 접두, 후속은 들여쓰기
                first, *rest = inner.splitlines()
                out.append(f"- {first}")
                for r in rest:
                    out.append(f"  {r}")
        return "\n".join(out) + "\n\n"

    if ntype == "orderedList":
        out = []
        for i, li in enumerate(content, 1):
            inner = adf_to_text(li.get("content") or []).strip()
            if inner:
                first, *rest = inner.splitlines()
                out.append(f"{i}. {first}")
                for r in rest:
                    out.append(f"   {r}")
        return "\n".join(out) + "\n\n"

    if ntype == "listItem":
        return adf_to_text(content)

    if ntype == "codeBlock":
        lang = (node.get("attrs") or {}).get("language", "")
        body = adf_to_text(content).rstrip()
        return f"```{lang}\n{body}\n```\n\n"

    if ntype == "blockquote":
        inner = adf_to_text(content).strip()
        return "\n".join(f"> {ln}" for ln in inner.splitlines()) + "\n\n"

    if ntype == "rule":
        return "\n---\n\n"

    # doc / 그 외 — 자식 텍스트만 이어붙임
    return adf_to_text(content)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _auth_header(email: str, token: str) -> str:
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {creds}"


def _http_request(
    method: str,
    url: str,
    *,
    email: str,
    token: str,
    body: dict | None = None,
    timeout: float | None = None,
) -> dict:
    """urllib 기반 요청. 응답 body 가 JSON 이면 파싱해 반환, 아니면 빈 dict.

    timeout 미지정 시 ATLASSIAN_HTTP_TIMEOUT 환경변수 (기본 30초)."""
    if timeout is None:
        timeout = http_timeout("ATLASSIAN_HTTP_TIMEOUT", 30)
    headers = {
        "Authorization": _auth_header(email, token),
        "Accept": "application/json",
    }
    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
        raw = resp.read()
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

def _extract_steps_to_reproduce(description_text: str, fields: dict) -> str | None:
    """description 의 `재현 경로` / `Steps to reproduce` 헤딩 본문, 또는 custom field
    `customfield_10*` 중 명시 라벨이 매칭되는 값을 반환."""
    # 1. description heading 매칭
    if description_text:
        m = re.search(
            r"(?im)^#{1,6}\s*(재현\s*경로|재현\s*방법|steps?\s*to\s*reproduce|repro\s*steps?)\s*$([\s\S]*?)(?:^#{1,6}\s|\Z)",
            description_text,
            re.MULTILINE,
        )
        if m:
            body = m.group(2).strip()
            if body:
                return body
    # 2. custom field 휴리스틱 — Jira Cloud 의 custom field 는 customfield_XXXXX 형태이고
    #    이름은 응답에 없을 수 있다. 값이 명백한 문자열인 경우만 채택.
    for k, v in fields.items():
        if not k.startswith("customfield_"):
            continue
        if isinstance(v, str) and re.search(r"재현|repro|reproduce|steps", v, re.IGNORECASE):
            return v
    return None


def cmd_fetch(key: str) -> int:
    validate_key_format(key)
    validate_key_whitelist(key)
    base, email, token = get_credentials()

    url = f"{base}/rest/api/3/issue/{urllib.parse.quote(key, safe='')}"
    try:
        data = _http_request("GET", url, email=email, token=token)
    except urllib.error.HTTPError as e:
        msg = f"HTTP {e.code} {e.reason}"
        if e.code == 401:
            msg += " — ATLASSIAN_EMAIL / ATLASSIAN_TOKEN (또는 JIRA_*) 확인 필요"
        elif e.code == 403:
            msg += f" — 권한 없음 (key={key})"
        elif e.code == 404:
            msg += f" — 이슈를 찾을 수 없음 (key={key})"
        print(f"[ERROR] fetch failed for {key}", file=sys.stderr)
        print(msg, file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"[ERROR] fetch failed for {key}", file=sys.stderr)
        print(f"network error: {e.reason}", file=sys.stderr)
        return 1

    fields = data.get("fields") or {}
    summary = fields.get("summary", "(no summary)")
    status_obj = fields.get("status") or {}
    status = status_obj.get("name", "(unknown)")
    reporter_obj = fields.get("reporter") or {}
    reporter = reporter_obj.get("displayName") or reporter_obj.get("emailAddress") or "(unknown)"

    description_adf = fields.get("description")
    description_text = adf_to_text(description_adf).strip() if description_adf else ""

    steps = _extract_steps_to_reproduce(description_text, fields)

    attachments = fields.get("attachment") or []
    attachment_names: list[str] = []
    for att in attachments:
        if isinstance(att, dict):
            name = att.get("filename") or att.get("name")
            if name:
                attachment_names.append(str(name))

    # Markdown 스켈레톤 — `/pilot:qa` 가 그대로 prefill 가능.
    lines: list[str] = []
    lines.append(f"# {key} — {summary}")
    lines.append("")
    lines.append(f"> status: {status}")
    lines.append(f"> reporter: {reporter}")
    lines.append("")
    lines.append("## 현상")
    lines.append("")
    lines.append(description_text if description_text else "_(no description)_")
    lines.append("")
    lines.append("## 재현 경로")
    lines.append("")
    lines.append(steps.strip() if steps else "_(본문에서 추출 불가 — 사용자 보강 필요)_")
    lines.append("")
    lines.append("## 첨부 파일")
    lines.append("")
    if attachment_names:
        for name in attachment_names:
            lines.append(f"- {name}")
    else:
        lines.append("_(없음)_")
    lines.append("")

    sys.stdout.write("\n".join(lines))
    if not lines[-1].endswith("\n"):
        sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# comment
# ---------------------------------------------------------------------------

def _comment_error_exit(key: str, cause: str) -> None:
    """COMMENT FAILED 의 표준 출력 형식 (print only — 호출자가 return 1 책임)."""
    print(f"[ERROR] COMMENT FAILED for {key}", file=sys.stderr)
    print(cause, file=sys.stderr)


def cmd_comment(key: str, msg: str) -> int:
    # 키 검증 단계에서 실패하면 `[ERROR] invalid key format` 가 먼저 나간다.
    # COMMENT 헤더는 모든 실패 케이스 (네트워크/4xx/5xx/auth/키부재) 에 강제하지만,
    # 형식 위배는 그보다 앞선 입력 검증으로 별도 처리한다.
    validate_key_format(key)
    validate_key_whitelist(key)

    if not msg:
        _comment_error_exit(key, "empty message")
        return 1

    # COMMENT FAILED 헤더가 모든 실패 케이스에서 stderr 첫 줄이 되도록 quiet 모드로
    # credential 누락을 사전 감지한다 (HTTP error 와 동일한 line-1 계약).
    creds = get_credentials(quiet=True)
    if creds is None:
        print(f"[ERROR] COMMENT FAILED for {key}", file=sys.stderr)
        # 누락된 env 키 목록을 두 번째 줄부터 안내 — get_credentials 의 상세 메시지는
        # quiet 모드에서 생략되므로 cause 만 간결히. 도구별 키와 통합 키가 모두
        # 비었을 때만 missing 으로 친다.
        missing_keys = [
            atl for tool, atl in (
                ("JIRA_BASE_URL", "ATLASSIAN_BASE_URL"),
                ("JIRA_EMAIL", "ATLASSIAN_EMAIL"),
                ("JIRA_TOKEN", "ATLASSIAN_TOKEN"),
            )
            if not os.environ.get(tool, "").strip()
            and not os.environ.get(atl, "").strip()
        ]
        print(f"Atlassian env not set: {', '.join(missing_keys)}", file=sys.stderr)
        print(
            "Atlassian API token 발급: https://id.atlassian.com/manage-profile/security/api-tokens",
            file=sys.stderr,
        )
        return 1
    base, email, token = creds

    url = f"{base}/rest/api/3/issue/{urllib.parse.quote(key, safe='')}/comment"
    body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": msg}],
                }
            ],
        }
    }

    try:
        _http_request("POST", url, email=email, token=token, body=body)
    except urllib.error.HTTPError as e:
        _comment_error_exit(key, f"HTTP {e.code} {e.reason}")
        return 1
    except urllib.error.URLError as e:
        _comment_error_exit(key, f"network error: {e.reason}")
        return 1
    except Exception as e:  # noqa: BLE001 — defensive: any other transport/encode failure
        _comment_error_exit(key, f"{type(e).__name__}: {e}")
        return 1

    print("OK")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(__doc__, file=sys.stderr)
        return 1

    mode = argv[0]

    if mode == "fetch":
        if len(argv) < 2:
            print("[ERROR] usage: jira.py fetch <KEY>", file=sys.stderr)
            return 1
        return cmd_fetch(argv[1])
    elif mode == "comment":
        if len(argv) < 3:
            print('[ERROR] usage: jira.py comment <KEY> "<msg>"', file=sys.stderr)
            return 1
        key = argv[1]
        msg = argv[2]
        return cmd_comment(key, msg)
    elif mode == "list":
        print(
            "[ERROR] `list` is out of scope — 다건 추적·잔여 현황은 Jira UI 가 SSOT.",
            file=sys.stderr,
        )
        return 1
    else:
        print(f"[ERROR] unknown mode: {mode}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
