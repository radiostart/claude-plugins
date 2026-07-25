"""Workspace / project 정합성 검사 + auto-fix.

`doctor.py` (default 모드 + --fix) 의 본체. 검사 함수와 자동 수정 헬퍼를
한 파일에 모은다. CLI 진입점은 `run_integrity_check`.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

from doctor._common import (
    BOLD,
    GREEN,
    RED,
    RESET,
    Result,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMAS,
    YELLOW,
    _git_repo_root,
    _parse_semver,
    count_real_features,
    detect_duplicate_h2_sections,
    parse_dotenv_file,
    parse_state_md,
    parse_state_md_all_rows,
    parse_state_yml,
    project_has_tdd_literal,
    read_current_plugin_version,
    run_auto_fixes,
    summarize,
)


# ---------------------------------------------------------------------------
# Credential drift (.env vs env)
# ---------------------------------------------------------------------------

def check_credential_drift(env_path: Path) -> list[Result]:
    """workspace/.env 값과 현재 환경변수 값을 비교해 drift 감지.

    둘 다 존재할 때만 비교 (한쪽만 있으면 drift 판정 불가 — skip).
    실제 값은 출력하지 않고 길이 + SHA-256 프리픽스(16자) 만 보고.

    대상 키: CONFLUENCE_EMAIL, CONFLUENCE_TOKEN
    (다른 credential 키도 필요하면 CREDENTIAL_KEYS 에 추가)
    """
    CREDENTIAL_KEYS = ("CONFLUENCE_EMAIL", "CONFLUENCE_TOKEN")
    results: list[Result] = []
    dotenv = parse_dotenv_file(env_path)
    if not dotenv:
        return results
    import hashlib

    for key in CREDENTIAL_KEYS:
        file_val = dotenv.get(key)
        env_val = os.environ.get(key)
        if not file_val or not env_val:
            continue
        if file_val == env_val:
            continue
        file_hash = hashlib.sha256(file_val.encode()).hexdigest()[:16]
        env_hash = hashlib.sha256(env_val.encode()).hexdigest()[:16]
        results.append(
            Result(
                Result.WARN,
                f"workspace/.env credential drift",
                f"{key}: .env(len={len(file_val)}, sha={file_hash}) ≠ env(len={len(env_val)}, sha={env_hash})",
                "`.env` 를 env 값으로 동기화 (interactive shell 에서 정상 토큰 export 된 경우)",
            )
        )
    return results


# ---------------------------------------------------------------------------
# Slack secret 보호
# ---------------------------------------------------------------------------

REQUIRED_GITIGNORE_PATTERNS = (".slack.env",)


def check_gitignore_required_patterns(workspace: Path) -> list[Result]:
    """리포 루트 `.gitignore` 에 secret 패턴이 있는지 확인. 없으면 **즉시 append**.

    `.slack.env` 는 프로젝트별 Slack Incoming Webhook URL 을 담는 secret 파일.
    누락된 상태로 커밋되면 URL 유출 → 즉시 재발급 필요. 이 리스크가 사용자 확인
    비용보다 훨씬 크므로 `--fix` 없이도 자동 주입한다.
    """
    results: list[Result] = []
    repo_root = _git_repo_root(workspace) or workspace.parent
    if not repo_root.is_dir():
        return results
    gitignore = repo_root / ".gitignore"
    existing: list[str] = []
    if gitignore.is_file():
        try:
            existing = [
                l.strip() for l in gitignore.read_text(encoding="utf-8").splitlines()
            ]
        except Exception:
            existing = []
    missing = [p for p in REQUIRED_GITIGNORE_PATTERNS if p not in existing]
    if not missing:
        results.append(
            Result(
                Result.PASS,
                ".gitignore secrets",
                f"{', '.join(REQUIRED_GITIGNORE_PATTERNS)} 보호됨",
            )
        )
        return results
    try:
        content = ""
        if gitignore.is_file():
            content = gitignore.read_text(encoding="utf-8")
            if content and not content.endswith("\n"):
                content += "\n"
        content += "\n# pilot: Slack webhook secret — 절대 커밋 금지\n"
        for p in missing:
            content += f"{p}\n"
        gitignore.write_text(content, encoding="utf-8")
        results.append(
            Result(
                Result.WARN,
                ".gitignore secrets",
                f"누락 패턴 자동 주입: {', '.join(missing)}",
                f"{gitignore} 수정됨 — 리포에 커밋하여 영구화하세요",
            )
        )
    except Exception as e:
        results.append(
            Result(
                Result.ERROR,
                ".gitignore secrets",
                f"{', '.join(missing)} 누락 + 자동 주입 실패: {e}",
                "리포 루트 `.gitignore` 에 `.slack.env` 를 수동 추가하세요",
            )
        )
    return results


def check_slack_env_not_tracked(workspace: Path) -> list[Result]:
    """모든 프로젝트의 `.slack.env` 가 git 에 추적되지 않는지 점검.

    tracked 상태면 [CRITICAL] — webhook URL 이 이미 리포 히스토리에 포함되었을
    가능성. `git rm --cached` 와 URL 재발급 안내. auto-fix 대상 아님 (사용자
    판단이 필요한 destructive 조치).
    """
    results: list[Result] = []
    projects_dir = workspace / "projects"
    if not projects_dir.is_dir():
        return results
    for proj in projects_dir.iterdir():
        if not proj.is_dir():
            continue
        slack_env = proj / ".slack.env"
        if not slack_env.is_file():
            continue
        try:
            r = subprocess.run(
                ["git", "ls-files", "--error-unmatch", slack_env.name],
                cwd=str(slack_env.parent),
                capture_output=True,
                timeout=3,
            )
            tracked = r.returncode == 0
        except Exception:
            continue
        if tracked:
            results.append(
                Result(
                    Result.ERROR,
                    f"[CRITICAL] {proj.name}/.slack.env",
                    "git 에 추적되고 있음 — webhook URL 유출 위험",
                    f"`git rm --cached {slack_env}` 실행 후 webhook URL 재발급",
                )
            )
    return results


# ---------------------------------------------------------------------------
# Auto-fix factories (whitelist 안전 대상만)
# ---------------------------------------------------------------------------

def _fix_state_md_prune_history(state_md: Path):
    """STATE.md 에서 `진행중` 이 아닌 행을 전부 제거. 헤더·구분선은 보존.

    - `진행중` 행이 0 건이면 헤더만 남긴다 (빈 상태).
    - `진행중` 이 2 건 이상이면 fix 시도하지 않고 False 반환 (사용자 판단 필요).
    """
    def _run():
        try:
            lines = state_md.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            return False, f"read 실패: {e}"
        kept: list[str] = []
        active_count = 0
        for line in lines:
            s = line.strip()
            if not s.startswith("|"):
                kept.append(line)
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 3:
                kept.append(line)
                continue
            first = cells[0]
            if first in ("모드", "mode") or set(first) <= set("-: "):
                kept.append(line)
                continue
            if cells[2] == "진행중":
                active_count += 1
                kept.append(line)
        if active_count > 1:
            return False, f"진행중 {active_count} 개 — 자동 정리 보류 (사용자가 1 개로 줄여야 함)"
        content = "\n".join(kept)
        if not content.endswith("\n"):
            content += "\n"
        try:
            state_md.write_text(content, encoding="utf-8")
        except Exception as e:
            return False, f"write 실패: {e}"
        return True, f"이력 행 제거 완료 (진행중 {active_count} 건 유지)"
    return _run


def _fix_migrate_state_to_current(state_yml: Path):
    """schema v1 / v1.1 → 현재 버전(v1.2) 업그레이드 (in-place).

    외부 프로세스 호출 대신 inline 수행 (간단 + 오류 진단 쉬움).
    - v1   → v1.2 : `domain: null` 주입 (없을 때만) + 스키마 라벨 bump
    - v1.1 → v1.2 : 스키마 라벨만 bump (domain 은 이미 존재)
    """
    def fixer():
        try:
            text = state_yml.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"read 실패: {e}"

        # 사전 스캔: 기존 schema 와 domain 필드 존재 여부 파악 (line-level 주입 시 중복 방지)
        data = parse_state_yml(state_yml) or {}
        old_schema = data.get("schema") or "미지"
        has_domain_field = "domain" in data
        needs_domain_injection = old_schema == "v1" and not has_domain_field

        lines = text.splitlines()
        out: list[str] = []
        schema_replaced = False
        domain_injected = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("schema:"):
                out.append(f"schema: {SCHEMA_VERSION}")
                schema_replaced = True
                continue
            out.append(line)
            if needs_domain_injection and not domain_injected and stripped.startswith("tdd:"):
                out.append("domain: null")
                domain_injected = True

        # tdd 라인이 없는 v1 파일 (드문 케이스) — 끝에 domain 추가
        if needs_domain_injection and not domain_injected:
            out.append("domain: null")
        if not schema_replaced:
            out.insert(0, f"schema: {SCHEMA_VERSION}")
        content = "\n".join(out)
        if not content.endswith("\n"):
            content += "\n"
        try:
            state_yml.write_text(content, encoding="utf-8")
        except Exception as e:
            return False, f"write 실패: {e}"
        return True, f"schema {old_schema} → {SCHEMA_VERSION}"
    return fixer


def _fix_remove_legacy_planning_section(planner_md: Path):
    """planner.md 의 `## 플래닝 프로세스` 섹션 자동 제거 (래퍼로 이관됨).

    섹션 시작부터 다음 `## ` 또는 EOF 까지 제거. 내부 코드블록 안 `## ` 은
    heading 아니므로 제외.
    """
    def fixer():
        try:
            text = planner_md.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"read 실패: {e}"
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        in_section = False
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
            if not in_code:
                if re.match(r"^##\s+플래닝 프로세스\s*$", line):
                    in_section = True
                    continue
                if in_section and re.match(r"^##\s+[^#]", line):
                    in_section = False
            if in_section:
                continue
            out.append(line)
        content = "".join(out)
        try:
            planner_md.write_text(content, encoding="utf-8")
        except Exception as e:
            return False, f"write 실패: {e}"
        return True, "래퍼로 이관된 `## 플래닝 프로세스` 섹션 제거"
    return fixer


# ---------------------------------------------------------------------------
# Workspace / Team / Project 검사
# ---------------------------------------------------------------------------

def check_workspace(workspace: Path) -> list[Result]:
    results = []
    if not workspace.is_dir():
        results.append(
            Result(
                Result.ERROR,
                "workspace/",
                "없음",
                "`/pilot:init` 실행",
            )
        )
        return results
    results.append(Result(Result.PASS, "workspace/", "존재"))

    state_md = workspace / "STATE.md"
    manifest = workspace / "context" / "MANIFEST.md"
    config_md = workspace / "context" / "config.md"

    # Slack webhook secret 이 git 에 tracked 되어 있지 않은지
    results.extend(check_slack_env_not_tracked(workspace))

    # STATE.md
    if state_md.is_file():
        active_count, active_names = parse_state_md(state_md)
        if active_count == 0:
            results.append(
                Result(
                    Result.WARN,
                    "STATE.md",
                    "진행중 프로젝트 없음",
                    "`/pilot:project {이름}` 으로 활성화",
                )
            )
        elif active_count == 1:
            results.append(
                Result(Result.PASS, "STATE.md", f"진행중: {active_names[0]}")
            )
        else:
            results.append(
                Result(
                    Result.ERROR,
                    "STATE.md",
                    f"진행중 {active_count} 개 ({', '.join(active_names)})",
                    "preamble P2 규칙상 1 개만 허용. STATE.md 수정 필요",
                )
            )

        # STATE.md 이력 행 검사 — 진행중 아닌 데이터 행이 있으면 WARN (auto-fixable)
        all_rows = parse_state_md_all_rows(state_md)
        history_rows = [r for r in all_rows if r[2] != "진행중"]
        if history_rows:
            labels = ", ".join(f"{r[1]}({r[2]})" for r in history_rows[:5])
            more = "" if len(history_rows) <= 5 else f" 외 {len(history_rows) - 5}건"
            results.append(
                Result(
                    Result.WARN,
                    "STATE.md 이력",
                    f"`진행중` 이 아닌 행 {len(history_rows)} 개 감지: {labels}{more}",
                    "STATE.md 는 진행중 1행만 유지 — 이력은 git log 로 추적. "
                    "`doctor --fix` 로 자동 정리 가능",
                    fix=_fix_state_md_prune_history(state_md),
                )
            )
    else:
        results.append(
            Result(
                Result.ERROR,
                "STATE.md",
                "없음",
                "`/pilot:init` 재실행",
            )
        )

    # MANIFEST.md
    if manifest.is_file():
        results.append(Result(Result.PASS, "context/MANIFEST.md", "존재"))
    else:
        results.append(
            Result(
                Result.ERROR,
                "context/MANIFEST.md",
                "없음",
                "`/pilot:init` 재실행",
            )
        )

    # config.md
    if config_md.is_file():
        results.append(Result(Result.PASS, "context/config.md", "존재"))
    else:
        results.append(
            Result(
                Result.WARN,
                "context/config.md",
                "없음",
                "`/pilot:init` 재실행 또는 직접 작성",
            )
        )

    # Credential drift (workspace/.env vs env var)
    results.extend(check_credential_drift(workspace / ".env"))
    # Slack webhook secret 보호 — .gitignore 에 .slack.env 패턴 강제 주입
    results.extend(check_gitignore_required_patterns(workspace))
    # Auto-memory 존재 안내 (플러그인은 Read 만 — 경고 아닌 INFO 수준 PASS 로 표시)
    results.extend(check_auto_memory_presence())
    return results


def check_auto_memory_presence() -> list[Result]:
    """harness auto-memory 가 존재하면 사용자에게 힌트 제공. P0 재환기용."""
    try:
        home = Path.home()
        cwd = Path.cwd()
        slug = str(cwd).replace("/", "-")
        memory_dir = home / ".claude" / "projects" / slug / "memory"
        index = memory_dir / "MEMORY.md"
        if not index.is_file():
            return []
        count = 0
        for p in memory_dir.glob("*.md"):
            if p.name != "MEMORY.md":
                count += 1
        if count == 0:
            return []
        return [
            Result(
                Result.PASS,
                "auto-memory",
                f"{count} 개 메모 감지 ({memory_dir.relative_to(home)})",
                "P0 절차로 스킬 진입 시 `tools/memory-hint.py` 로 관련 메모 조회 권장",
            )
        ]
    except Exception:
        return []


def check_project(workspace: Path, project: str) -> list[Result]:
    results = []
    proj_dir = workspace / "projects" / project
    if not proj_dir.is_dir():
        results.append(
            Result(
                Result.ERROR,
                f"projects/{project}",
                "프로젝트 폴더 없음",
                f"`/pilot:project {project}` 실행",
            )
        )
        return results

    state_yml = proj_dir / ".agent-state.yml"
    project_md = proj_dir / "project.md"
    features_dir = proj_dir / "features"

    # .agent-state.yml + schema
    state_data = parse_state_yml(state_yml)
    if state_data is None:
        results.append(
            Result(
                Result.ERROR,
                f"{project}/.agent-state.yml",
                "없음",
                "`/pilot:project {프로젝트명}` 재실행 또는 직접 작성",
            )
        )
        return results

    schema = state_data.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        results.append(
            Result(
                Result.ERROR,
                f"{project}/.agent-state.yml",
                f"schema: {schema!r} (지원: {', '.join(SUPPORTED_SCHEMAS)})",
                "플러그인 업그레이드 또는 schema 직접 갱신",
            )
        )
        return results

    # schema v1 / v1.1 이면 v1.2 로 업그레이드 권장 (auto-fixable)
    if schema in ("v1", "v1.1"):
        results.append(
            Result(
                Result.WARN,
                f"{project}/.agent-state.yml schema",
                f"schema {schema} (최신 v1.2 으로 업그레이드 가능)",
                "`doctor --fix` 로 자동 업그레이드",
                fix=_fix_migrate_state_to_current(state_yml),
            )
        )

    results.append(
        Result(Result.PASS, f"{project}/.agent-state.yml", f"schema {schema}")
    )

    # analyzed 정합성
    analyzed_flag = state_data.get("analyzed", False)
    feature_count = count_real_features(features_dir)
    if analyzed_flag and feature_count == 0:
        results.append(
            Result(
                Result.WARN,
                f"{project} analyzed",
                f"state.yml analyzed=true 이지만 features/ 에 실제 파일 없음",
                "`/pilot:analyze` 또는 state.yml 의 analyzed 를 false 로",
            )
        )
    elif not analyzed_flag and feature_count > 0:
        results.append(
            Result(
                Result.WARN,
                f"{project} analyzed",
                f"state.yml analyzed=false 이지만 features/ 에 {feature_count} 개 존재",
                "`/pilot:analyze` 재실행으로 state.yml 동기화",
            )
        )
    else:
        results.append(
            Result(
                Result.PASS,
                f"{project} analyzed",
                f"analyzed={analyzed_flag}, features={feature_count}",
            )
        )

    # tdd 정합성 (3-way: state.yml ↔ project.md ↔ prompts/*.md)
    tdd_flag = state_data.get("tdd", False)
    tdd_literal = project_has_tdd_literal(project_md)

    # prompts/*.md TDD 섹션 존재 여부 detect (백업 마커 기준)
    prompts_dir = proj_dir / "prompts"
    prompts_tdd: dict[str, bool] = {}
    for role, marker in [
        ("planner", "<!-- pilot-tdd-original-planner:start -->"),
        ("generator", "<!-- pilot-tdd-original-generator:start -->"),
        ("evaluator", "<!-- pilot-tdd-original-evaluator:start -->"),
    ]:
        prompt_file = prompts_dir / f"{role}.md"
        if prompt_file.is_file():
            try:
                content = prompt_file.read_text(encoding="utf-8")
                prompts_tdd[role] = marker in content
            except Exception:
                prompts_tdd[role] = False
        else:
            prompts_tdd[role] = False

    prompts_active_count = sum(1 for v in prompts_tdd.values() if v)
    prompts_total = len(prompts_tdd)
    prompts_status = (
        "TDD" if prompts_active_count == prompts_total
        else "표준" if prompts_active_count == 0
        else "MIXED"
    )

    # 3-way 일치 판정
    project_status = "TDD" if tdd_literal else "표준"
    state_status = "TDD" if tdd_flag else "표준"

    consistent = (
        (tdd_flag and tdd_literal and prompts_active_count == prompts_total)
        or (not tdd_flag and not tdd_literal and prompts_active_count == 0)
    )

    if consistent:
        results.append(
            Result(Result.PASS, f"{project} tdd", f"tdd={tdd_flag}, 3-way 일치")
        )
    else:
        results.append(
            Result(
                Result.WARN,
                f"{project} tdd",
                (
                    f"TDD 모드 정합성 불일치 — "
                    f"state.yml=tdd:{str(tdd_flag).lower()} · "
                    f"project.md={project_status} · "
                    f"prompts/*.md={prompts_status} ({prompts_active_count}/{prompts_total})"
                ),
                "`/pilot:tdd --fix` 실행 권장 (state.yml 값을 진실로 보정)",
            )
        )

    # domain 체크 (v1.1+ 필수 필드) — null 일 때만 WARN. 값은 자유 문자열.
    domain = state_data.get("domain")
    if schema in ("v1.1", "v1.2"):
        if domain is None:
            results.append(
                Result(
                    Result.WARN,
                    f"{project} domain",
                    "domain 미지정 (null)",
                    "`/pilot:analyze` 진입 시 사용자 확인 후 자동 기록됨",
                )
            )

    # pr_base_branch 체크 (v1.2 신규, optional)
    pr_base = state_data.get("pr_base_branch")
    if pr_base:
        if not isinstance(pr_base, str) or not pr_base.strip():
            results.append(
                Result(
                    Result.WARN,
                    f"{project} pr_base_branch",
                    f"형식 오류: {pr_base!r}",
                    "`/pilot:pr` 재실행하여 재입력",
                )
            )
        else:
            try:
                rc = subprocess.run(
                    ["git", "ls-remote", "--exit-code", "origin", pr_base],
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).returncode
                if rc == 0:
                    results.append(
                        Result(
                            Result.PASS,
                            f"{project} pr_base_branch",
                            f"{pr_base} (remote 존재)",
                        )
                    )
                else:
                    results.append(
                        Result(
                            Result.WARN,
                            f"{project} pr_base_branch",
                            f"{pr_base} 가 origin 에 없음 (stale)",
                            "`/pilot:pr` 로 재지정 또는 state 의 pr_base_branch 제거",
                        )
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                # 네트워크 / git 미설치 — 체크 skip (에러 아님)
                pass

    # plugin_version drift (optional — semver minor 이상 차이만 경고)
    state_pv = state_data.get("plugin_version")
    current_pv = read_current_plugin_version()
    if current_pv:
        sv = _parse_semver(state_pv) if state_pv else None
        cv = _parse_semver(current_pv)
        if state_pv is None:
            results.append(
                Result(
                    Result.WARN,
                    f"{project} plugin_version",
                    f"미기록 (현재 플러그인 {current_pv})",
                    "다음 `/pilot:analyze` 실행 시 자동 기록",
                )
            )
        elif sv and cv:
            if sv[:2] != cv[:2]:
                if sv < cv:
                    results.append(
                        Result(
                            Result.WARN,
                            f"{project} plugin_version",
                            f"{state_pv} → {current_pv} 업그레이드됨 (wrapper 계약 변경 가능)",
                            "`/pilot:analyze --regen-agents` 권장",
                        )
                    )
                else:
                    results.append(
                        Result(
                            Result.WARN,
                            f"{project} plugin_version",
                            f"state ({state_pv}) > 현재 ({current_pv}) — 다운그레이드 감지",
                            "플러그인 업데이트 또는 state 확인",
                        )
                    )
            else:
                results.append(
                    Result(
                        Result.PASS,
                        f"{project} plugin_version",
                        f"{state_pv} (현재 {current_pv})",
                    )
                )

    # Drift 감지 (optional 필드 — 없으면 skip)
    last_count = state_data.get("last_analyzed_features")
    analyzed_at = state_data.get("analyzed_at")
    docs_fetched_at = state_data.get("docs_last_fetched_at")

    # features 증가 drift
    if analyzed_flag and isinstance(last_count, int):
        if feature_count > last_count + 1:
            results.append(
                Result(
                    Result.WARN,
                    f"{project} drift",
                    f"features {last_count} → {feature_count} (증가 {feature_count - last_count})",
                    "`/pilot:analyze --regen-agents` 로 prompts/*.md 재생성 권장",
                )
            )

    # context mtime drift + docs drift (analyzed_at 이 있을 때만)
    if analyzed_flag and isinstance(analyzed_at, str) and analyzed_at:
        try:
            from datetime import datetime

            def _parse_iso(ts: str):
                return datetime.fromisoformat(ts.rstrip("Z").replace("T", " "))

            analyzed_dt = _parse_iso(analyzed_at)

            # context/ 하위 도메인 지식 .md 파일 mtime drift 검사
            # MANIFEST.md, config.md 같은 메타 파일은 제외 (도메인 지식 아님).
            # 워크스페이스 폴더 구조는 자유라 .md 파일 전체를 재귀 스캔.
            context_dir = workspace / "context"
            META_FILES = {"MANIFEST.md", "config.md", "pr.md", "coding.md"}
            newest_mtime = 0.0
            newest_path = None
            if context_dir.is_dir():
                for p in context_dir.rglob("*.md"):
                    if p.name in META_FILES:
                        continue
                    mt = p.stat().st_mtime
                    if mt > newest_mtime:
                        newest_mtime = mt
                        newest_path = p
            if newest_mtime > 0 and newest_path is not None:
                newest_dt = datetime.fromtimestamp(newest_mtime)
                if newest_dt > analyzed_dt:
                    rel = newest_path.relative_to(workspace)
                    results.append(
                        Result(
                            Result.WARN,
                            f"{project} drift",
                            f"context/ 도메인 파일 변경됨: {rel} ({newest_dt.isoformat(timespec='seconds')}) > analyzed_at ({analyzed_at})",
                            "`/pilot:analyze --regen-agents` 권장",
                        )
                    )

            # docs drift — state 의 docs_last_fetched_at 이 analyzed_at 보다 최근
            if isinstance(docs_fetched_at, str) and docs_fetched_at:
                try:
                    fetched_dt = _parse_iso(docs_fetched_at)
                    if fetched_dt > analyzed_dt:
                        results.append(
                            Result(
                                Result.WARN,
                                f"{project} drift",
                                f"docs_last_fetched_at ({docs_fetched_at}) > analyzed_at ({analyzed_at})",
                                "기획서가 analyze 이후 업데이트됨 — `/pilot:analyze --force` 권장",
                            )
                        )
                except Exception:
                    pass
        except Exception:
            pass

    # Duplicate section 감지 (regen-gone-wrong 신호)
    prompts_dir = proj_dir / "prompts"
    if prompts_dir.is_dir():
        for prompt_name in ("planner.md", "generator.md", "evaluator.md"):
            prompt_file = prompts_dir / prompt_name
            dups = detect_duplicate_h2_sections(prompt_file)
            if dups:
                results.append(
                    Result(
                        Result.WARN,
                        f"{project}/prompts/{prompt_name}",
                        f"duplicate section: {', '.join(dups)}",
                        "regen 으로 인한 중복 주입 가능성. `.prompts.bak/` 과 비교 후 수동 머지",
                    )
                )

        # Wrapper 로 이관된 섹션이 프로젝트 planner.md 에 잔존하는지 감지
        planner_file = prompts_dir / "planner.md"
        if planner_file.is_file():
            try:
                content = planner_file.read_text(encoding="utf-8")
                if re.search(r"^##\s+플래닝 프로세스\s*$", content, re.M):
                    results.append(
                        Result(
                            Result.WARN,
                            f"{project}/prompts/planner.md",
                            "`## 플래닝 프로세스` 섹션이 래퍼로 이관되었으나 프로젝트 파일에 잔존",
                            "`/pilot:analyze --regen-agents` / `doctor --fix` / 수동 삭제",
                            fix=_fix_remove_legacy_planning_section(planner_file),
                        )
                    )
            except Exception:
                pass

    return results


# ---------------------------------------------------------------------------
# config.md 신규 섹션 정합성 검증
# ---------------------------------------------------------------------------

def _parse_md_tables_in_section(text: str, section_header: str) -> list[list[list[str]]]:
    """마크다운 텍스트에서 특정 H2 섹션 내 표 목록을 반환.

    반환값: 표 리스트. 각 표 = 행 리스트. 각 행 = 셀 리스트 (헤더 행 포함).
    구분선 행 (`| --- |` 형태) 은 제외.
    코드블록 (``` ... ```) 안의 `| ... |` 줄은 표로 인식하지 않는다.
    """
    # 섹션 추출 (다음 H2 또는 EOF 까지)
    pattern = re.compile(
        rf"^{re.escape(section_header)}\s*$(.*?)(?=^##\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        return []
    section_text = m.group(1)

    tables: list[list[list[str]]] = []
    current_table: list[list[str]] = []
    in_table = False
    in_code_block = False  # ``` 펜스 추적

    for line in section_text.splitlines():
        stripped = line.strip()
        # 코드블록 진입/탈출 추적
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
                in_table = False
            continue
        # 코드블록 안은 표로 인식하지 않음
        if in_code_block:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # 구분선 행 제외 (모든 셀이 --- 패턴)
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue
            current_table.append(cells)
            in_table = True
        else:
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
                in_table = False

    if in_table and current_table:
        tables.append(current_table)

    return tables


CONVENTION_KEYS = ("conventions_doc", "conventions_evals")


def check_conventions_paths(workspace: Path, project: str | None) -> list[Result]:
    """config.md `## 언어·도구 기본값` 이 선언한 conventions_doc·conventions_evals 경로 실존 검사.

    선언됐는데 파일이 없으면 WARN — generator/evaluator 호출 시점에야 발견되는
    silent 갭을 doctor 가 조기 경고한다. 미선언 키는 결과 없음 (기능 미사용).
    project 지정 시 project.md 제한사항 override 를 병합해 최종 경로를 검사한다
    (orchestrate-load 와 동일 우선순위).
    """
    results: list[Result] = []
    declared: dict[str, str] = {}

    config_md = workspace / "context" / "config.md"
    if config_md.is_file():
        try:
            text = config_md.read_text(encoding="utf-8")
        except Exception as e:
            results.append(
                Result(
                    Result.WARN,
                    "context/config.md",
                    f"읽기 실패: {e}",
                    "파일 권한·인코딩 확인",
                )
            )
            return results
        for table in _parse_md_tables_in_section(text, "## 언어·도구 기본값"):
            for row in table:
                if len(row) < 2:
                    continue
                key = row[0].strip().strip("`").strip()
                value = row[1].strip().strip("`").strip()
                if key in CONVENTION_KEYS and value and value != "값":
                    declared[key] = value

    if project:
        project_md = workspace / "projects" / project / "project.md"
        if project_md.is_file():
            try:
                ptext = project_md.read_text(encoding="utf-8")
            except Exception:
                ptext = ""
            m = re.search(r"##\s*제한사항([\s\S]*?)(?:\n##\s|\Z)", ptext)
            if m:
                for line in m.group(1).splitlines():
                    row = re.match(
                        r"^\s*-\s*\*?\*?([a-z_]+)\*?\*?\s*:\s*`?([^`\n]+?)`?\s*$",
                        line,
                    )
                    if row and row.group(1) in CONVENTION_KEYS:
                        declared[row.group(1)] = row.group(2).strip()

    for key, rel in declared.items():
        rel_norm = rel.lstrip("/")
        if rel_norm.startswith("workspace/"):
            rel_norm = rel_norm[len("workspace/"):]
        if not (workspace / rel_norm).is_file():
            results.append(
                Result(
                    Result.WARN,
                    "conventions",
                    f"{key}={rel} 로 선언됐으나 파일 없음 — generator·evaluator 의 언어별 가드가 비활성",
                    f"workspace/{rel_norm} 생성 또는 config.md 선언 제거",
                )
            )
    return results


def determine_active_project(workspace: Path) -> str | None:
    state_md = workspace / "STATE.md"
    count, names = parse_state_md(state_md)
    if count == 1:
        return names[0]
    return None


# ---------------------------------------------------------------------------
# Default 모드 진입점
# ---------------------------------------------------------------------------

def run_integrity_check(workspace: Path, project: str | None, fix: bool) -> int:
    """Default 모드 진입점: workspace → project 순서로 검사 + 출력 + 요약.

    `--fix` 가 켜져 있으면 auto-fixable 항목 자동 수정 후 요약.
    """
    print(f"{BOLD}pilot doctor{RESET}  workspace: {workspace}\n")

    all_results: list[Result] = []

    # Workspace
    print(f"{BOLD}Workspace:{RESET}")
    ws_results = check_workspace(workspace)
    for r in ws_results:
        print(r.render())
    all_results.extend(ws_results)

    # Project
    project = project or determine_active_project(workspace)

    # conventions_doc/evals 선언-실존 검사 (workspace 선언 + project override 병합)
    conv_results = check_conventions_paths(workspace, project)
    for r in conv_results:
        print(r.render())
    all_results.extend(conv_results)

    if not project:
        print(
            f"\n{YELLOW}활성 프로젝트 없음 — 프로젝트 체크 건너뜀 "
            f"(--project 인자로 대상 지정 가능){RESET}"
        )
        if fix:
            run_auto_fixes(all_results)
        return summarize(all_results)

    print(f"\n{BOLD}Project ({project}):{RESET}")
    proj_results = check_project(workspace, project)
    for r in proj_results:
        print(r.render())
    all_results.extend(proj_results)

    if fix:
        run_auto_fixes(all_results)

    return summarize(all_results)

