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
        # 외부 도메인 reference 섹션 schema 검증 (#10)
        results.extend(check_workspace_external_domain_section(manifest))
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
        # 신규 섹션 정합성 검증 (## learn 언어 패턴, ## scope 카테고리)
        results.extend(check_workspace_config_sections(config_md))
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

    # features/ Open Questions 섹션 schema 검증 (#11)
    results.extend(check_features_open_questions(features_dir))

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


def check_workspace_config_sections(config_path: Path) -> list[Result]:
    """workspace/context/config.md 의 신규 섹션 (## learn 언어 패턴, ## scope 카테고리) 정합성 검증.

    부재 시 INFO 1 줄. 위반 시 ERROR. backward-compat 0 brittle.
    """
    results: list[Result] = []

    if not config_path.is_file():
        # config.md 자체 부재는 check_workspace 에서 처리 — 여기서는 skip
        return results

    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception as e:
        results.append(
            Result(
                Result.ERROR,
                "context/config.md",
                f"읽기 실패: {e}",
                "파일 권한·인코딩 확인",
            )
        )
        return results

    # ------------------------------------------------------------------
    # ## learn 언어 패턴 검증
    # ------------------------------------------------------------------
    LEARN_SECTION = "## learn 언어 패턴"
    learn_tables = _parse_md_tables_in_section(text, LEARN_SECTION)

    if not learn_tables:
        results.append(
            Result(
                Result.INFO,
                "context/config.md",
                f"{LEARN_SECTION} 미정의 — 폴더 인접성 fallback 동작",
            )
        )
    else:
        # 표 1: 2 컬럼 (언어, 의존성 추출 패턴)
        table1 = learn_tables[0]
        LEARN_TABLE1_EXPECTED_COLS = 2
        LEARN_TABLE1_EXPECTED_HEADERS = ["언어", "의존성 추출 패턴"]
        if table1:
            header_row = table1[0]
            col_count = len(header_row)
            if col_count != LEARN_TABLE1_EXPECTED_COLS:
                results.append(
                    Result(
                        Result.ERROR,
                        "context/config.md",
                        (
                            f"{LEARN_SECTION} 표 1: 컬럼 수 {col_count}개 "
                            f"({LEARN_TABLE1_EXPECTED_COLS}개 필요) "
                            f"— 기대 헤더: {', '.join(LEARN_TABLE1_EXPECTED_HEADERS)}"
                        ),
                        f"{LEARN_SECTION} 표 1 헤더를 '| 언어 | 의존성 추출 패턴 |' 형태로 수정",
                    )
                )
            elif header_row != LEARN_TABLE1_EXPECTED_HEADERS:
                results.append(
                    Result(
                        Result.ERROR,
                        "context/config.md",
                        (
                            f"{LEARN_SECTION} 표 1: 헤더 불일치 "
                            f"(받은: {', '.join(header_row)}) "
                            f"— 기대: {', '.join(LEARN_TABLE1_EXPECTED_HEADERS)}"
                        ),
                        f"헤더를 정확히 '언어', '의존성 추출 패턴' 으로 수정",
                    )
                )
            else:
                # 행 수 0 허용 (D10 default 폐지) — 빈 표 = 헤더만 있는 표 (data_rows = 0)
                data_rows1 = len(table1) - 1  # 헤더 제외
                if data_rows1 == 0:
                    results.append(
                        Result(
                            Result.INFO,
                            "context/config.md",
                            f"{LEARN_SECTION} 의 의존성 추적 표가 비어있음 — 폴더 인접성 fallback 동작",
                        )
                    )

        # 표 2: long-form — 정확히 2 컬럼 (역할, 식별 패턴)
        LEARN_TABLE2_EXPECTED_COLS = 2
        LEARN_TABLE2_EXPECTED_HEADERS = ["역할", "식별 패턴"]
        if len(learn_tables) >= 2:
            table2 = learn_tables[1]
            if table2:
                header_row2 = table2[0]
                col_count2 = len(header_row2)
                if col_count2 != LEARN_TABLE2_EXPECTED_COLS:
                    results.append(
                        Result(
                            Result.ERROR,
                            "context/config.md",
                            (
                                f"{LEARN_SECTION} 표 2 (역할 분류): 표 컬럼 수 {col_count2}개 "
                                f"({LEARN_TABLE2_EXPECTED_COLS}개 필요) "
                                f"— 기대 헤더: {', '.join(LEARN_TABLE2_EXPECTED_HEADERS)}"
                            ),
                            f"표 2 헤더를 '| 역할 | 식별 패턴 |' 형태로 수정 (long-form)",
                        )
                    )
                elif header_row2 != LEARN_TABLE2_EXPECTED_HEADERS:
                    results.append(
                        Result(
                            Result.ERROR,
                            "context/config.md",
                            (
                                f"{LEARN_SECTION} 표 2 (역할 분류): 헤더 불일치 "
                                f"(받은: {', '.join(header_row2)}) "
                                f"— 기대: {', '.join(LEARN_TABLE2_EXPECTED_HEADERS)}"
                            ),
                            "헤더를 정확히 '역할', '식별 패턴' 으로 수정",
                        )
                    )
                else:
                    # 행 수 0 허용 (D10 default 폐지)
                    data_rows2 = len(table2) - 1
                    if data_rows2 == 0:
                        results.append(
                            Result(
                                Result.INFO,
                                "context/config.md",
                                f"{LEARN_SECTION} 의 역할 분류 표가 비어있음 — 폴더 인접성 fallback 동작",
                            )
                        )

    # ------------------------------------------------------------------
    # ## scope 카테고리 검증
    # ------------------------------------------------------------------
    SCOPE_SECTION = "## scope 카테고리"
    scope_tables = _parse_md_tables_in_section(text, SCOPE_SECTION)

    if not scope_tables:
        results.append(
            Result(
                Result.INFO,
                "context/config.md",
                f"{SCOPE_SECTION} 미정의 — SKILL.md default 사용",
            )
        )
    else:
        scope_table = scope_tables[0]
        SCOPE_EXPECTED_COLS = 3
        SCOPE_EXPECTED_HEADERS = ["scope 헤더", "project.md 대상 H3", "표 헤더"]

        if scope_table:
            header_row = scope_table[0]
            col_count = len(header_row)

            # 컬럼 수 검증
            if col_count != SCOPE_EXPECTED_COLS:
                results.append(
                    Result(
                        Result.ERROR,
                        "context/config.md",
                        (
                            f"{SCOPE_SECTION}: 표 컬럼 수 {col_count}개 "
                            f"({SCOPE_EXPECTED_COLS}개 필요) "
                            f"— 기대 헤더: {', '.join(SCOPE_EXPECTED_HEADERS)}"
                        ),
                        f"표 헤더를 '| scope 헤더 | project.md 대상 H3 | 표 헤더 |' 형태로 수정",
                    )
                )
            else:
                # 헤더 정확 일치 확인
                if header_row != SCOPE_EXPECTED_HEADERS:
                    results.append(
                        Result(
                            Result.ERROR,
                            "context/config.md",
                            (
                                f"{SCOPE_SECTION}: 헤더 불일치 "
                                f"(받은: {', '.join(header_row)}) "
                                f"— 기대: {', '.join(SCOPE_EXPECTED_HEADERS)}"
                            ),
                            f"헤더를 정확히 '{', '.join(SCOPE_EXPECTED_HEADERS)}' 로 수정",
                        )
                    )

                # 데이터 행 검증 (헤더 행 제외, 1-indexed 로 행 번호 표시)
                ALLOWED_H3_PATTERN = re.compile(r"^[A-Za-z0-9가-힣 \-]+$")
                for row_idx, row in enumerate(scope_table[1:], start=2):
                    if len(row) < SCOPE_EXPECTED_COLS:
                        continue  # 셀 수 부족 행은 스킵 (컬럼 수 오류와 중복 보고 방지)

                    scope_header_val = row[0]
                    h3_val = row[1]

                    # scope 헤더 "## " prefix 강제
                    if not scope_header_val.startswith("## "):
                        results.append(
                            Result(
                                Result.ERROR,
                                "context/config.md",
                                (
                                    f"{SCOPE_SECTION}:{row_idx}행: "
                                    f"scope 헤더 값 \"{scope_header_val}\" "
                                    f"— ## prefix 필요 (\"## \" 로 시작해야 함)"
                                ),
                                f"scope 헤더 값을 '## {scope_header_val}' 형태로 수정",
                            )
                        )

                    # project.md 대상 H3 허용 문자 검증
                    if not ALLOWED_H3_PATTERN.match(h3_val):
                        # 차단 문자 식별
                        bad_chars = sorted(set(
                            ch for ch in h3_val
                            if not re.match(r"[A-Za-z0-9가-힣 \-]", ch)
                        ))
                        bad_desc = "·".join(
                            {"/" : "슬래시", ":" : "콜론", "#" : "해시", "|" : "파이프"}
                            .get(ch, repr(ch))
                            for ch in bad_chars
                        )
                        results.append(
                            Result(
                                Result.ERROR,
                                "context/config.md",
                                (
                                    f"{SCOPE_SECTION}:{row_idx}행: "
                                    f"project.md 대상 H3 값 \"{h3_val}\" "
                                    f"에 차단 문자 {bad_desc} 포함 "
                                    f"— 영숫자·공백·하이픈만 허용"
                                ),
                                "H3 값에서 슬래시·콜론·#·| 등 마크다운 메타 문자를 제거",
                            )
                        )

    return results


def check_workspace_external_domain_section(manifest_path: Path) -> list[Result]:
    """workspace/context/MANIFEST.md 의 외부 도메인 reference 섹션 schema 검증.

    부재 → INFO 1 줄 (backward-compat: 모든 기존 사용자는 부재 상태).
    존재 → 표 스키마 검증: 정확히 3 컬럼 + 헤더 정확 일치.
    추가 검증: 표 행의 추정 도메인이 ## 도메인 분류 표에도 등록돼 있으면 INFO (stale row).
    """
    results: list[Result] = []

    if not manifest_path.is_file():
        # MANIFEST.md 자체 부재는 check_workspace 에서 처리
        return results

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except Exception as e:
        results.append(
            Result(
                Result.ERROR,
                "context/MANIFEST.md",
                f"읽기 실패: {e}",
                "파일 권한·인코딩 확인",
            )
        )
        return results

    # ## 외부 도메인 reference 섹션 lookup (헤더에 "(learn 미완료)" 등 sub-string 허용)
    EXT_SECTION_PATTERN = re.compile(r"^## 외부 도메인 reference", re.M)
    has_ext_section = bool(EXT_SECTION_PATTERN.search(text))

    if not has_ext_section:
        results.append(
            Result(
                Result.INFO,
                "context/MANIFEST.md",
                "## 외부 도메인 reference 미정의 — 첫 cross-domain reference detect 시 `/pilot:learn` 이 자동 작성",
            )
        )
        return results

    # 섹션 헤더를 정확히 추출 (sub-string 매칭으로 실제 헤더 얻기)
    ext_header_match = re.search(r"^(## 외부 도메인 reference[^\n]*)", text, re.M)
    ext_section_header = ext_header_match.group(1).rstrip() if ext_header_match else "## 외부 도메인 reference"

    ext_tables = _parse_md_tables_in_section(text, ext_section_header)

    if not ext_tables:
        # 섹션은 있지만 표 없음 → 표 형식 강제 안 함 (산문 허용), INFO 만
        results.append(
            Result(
                Result.INFO,
                "context/MANIFEST.md",
                f"{ext_section_header} 섹션 존재하나 표 없음 — 표 형식이면 자동 갱신 대상",
            )
        )
        return results

    # 표 schema 검증
    EXT_EXPECTED_COLS = 3
    EXT_EXPECTED_HEADERS = ["추정 도메인", "클래스 (개수)", "추천 후속 학습"]

    ext_table = ext_tables[0]
    if not ext_table:
        return results

    header_row = ext_table[0]
    col_count = len(header_row)

    if col_count != EXT_EXPECTED_COLS:
        results.append(
            Result(
                Result.ERROR,
                "context/MANIFEST.md",
                (
                    f"{ext_section_header} 표: 컬럼 수 {col_count}개 "
                    f"({EXT_EXPECTED_COLS}개 필요) "
                    f"— 기대 헤더: {', '.join(EXT_EXPECTED_HEADERS)}"
                ),
                f"표 헤더를 '| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |' 형태로 수정",
            )
        )
        return results

    if header_row != EXT_EXPECTED_HEADERS:
        results.append(
            Result(
                Result.ERROR,
                "context/MANIFEST.md",
                (
                    f"{ext_section_header} 표: 헤더 불일치 "
                    f"(받은: {', '.join(header_row)}) "
                    f"— 기대: {', '.join(EXT_EXPECTED_HEADERS)}"
                ),
                f"헤더를 정확히 '{', '.join(EXT_EXPECTED_HEADERS)}' 로 수정",
            )
        )
        return results

    # stale row 검증: 외부 도메인 표의 추정 도메인이 ## 도메인 분류 표에도 있으면 INFO
    domain_tables = _parse_md_tables_in_section(text, "## 도메인 분류")
    learned_domains: set[str] = set()
    if domain_tables:
        domain_table = domain_tables[0]
        for row in domain_table[1:]:  # 헤더 제외
            if row and len(row) >= 1:
                learned_domains.add(row[0].strip().lower())

    for row in ext_table[1:]:  # 헤더 제외
        if not row or len(row) < 1:
            continue
        estimated_domain = row[0].strip().lower()
        if estimated_domain and estimated_domain in learned_domains:
            results.append(
                Result(
                    Result.INFO,
                    "context/MANIFEST.md",
                    f"## 외부 도메인 reference 표: '{estimated_domain}' 은 이미 ## 도메인 분류 에 등록됨 — 해당 행 제거 권장 (idempotency)",
                )
            )

    return results


def check_features_open_questions(features_dir: Path) -> list[Result]:
    """features/NN-*.md 각 파일의 Open Questions 섹션 schema 검증.

    ## Open Questions H2 부재 → INFO 1 줄 (backward-compat: 기존 파일은 INFO 만).
    존재 → 4 카테고리 H3 모두 존재 검증. 일부 누락 → INFO (ERROR 아님 — 사용자 수동 작성 friendly).
    4 카테고리 모두 빈 상태 (- (없음) 만) → PASS (정상 단순 feature).
    """
    EXPECTED_H3 = [
        "### (a) 같은 도메인 추가 read 필요",
        "### (b) cross-domain 산출물 부재",
        "### (c) 외부 시스템 spec 부재",
        "### (d) 비즈니스 결정 영역",
    ]
    OQ_PATTERN = re.compile(r"^## Open Questions\s*$", re.M)
    H3_PATTERNS = [re.compile(re.escape(h3) + r"\s*$", re.M) for h3 in EXPECTED_H3]

    results: list[Result] = []

    if not features_dir.is_dir():
        return results

    feature_files = sorted(
        p for p in features_dir.glob("*.md")
        if re.match(r"^\d{2}-", p.name) and not p.name.endswith(".plan.md")
    )

    for feature_path in feature_files:
        try:
            text = feature_path.read_text(encoding="utf-8")
        except Exception:
            continue

        rel = feature_path.name

        if not OQ_PATTERN.search(text):
            results.append(
                Result(
                    Result.INFO,
                    f"features/{rel}",
                    "## Open Questions 섹션 부재 — 추측 회피 위해 권장",
                )
            )
            continue

        # Open Questions 섹션 존재 — 4 카테고리 H3 검증
        missing = [h3 for h3, pat in zip(EXPECTED_H3, H3_PATTERNS) if not pat.search(text)]
        if missing:
            results.append(
                Result(
                    Result.INFO,
                    f"features/{rel}",
                    f"## Open Questions: {len(missing)} 개 카테고리 누락 — {', '.join(missing)}",
                )
            )

    return results


# ---------------------------------------------------------------------------
# #12 cross-domain transaction contracts schema 검증
# ---------------------------------------------------------------------------

_TX_TYPE_WHITELIST = frozenset([
    "read", "write", "destroy", "create",
    "read·write", "write·destroy", "read·destroy", "read·create",
    "write·create", "read·write·destroy", "read·write·create",
    "write·destroy·create", "read·write·destroy·create",
])


def _parse_md_tables_in_h3_section(text: str, h3_header: str) -> list[list[list[str]]]:
    """마크다운 텍스트에서 특정 H3 섹션 내 표 목록을 반환.

    H3 (`### ...`) 섹션을 대상으로 함. 다음 H2/H3 헤더 또는 EOF 까지를 섹션으로 본다.
    구분선 행 (`| --- |` 형태) 은 제외. 코드블록 안 표는 인식하지 않는다.
    """
    pattern = re.compile(
        rf"^{re.escape(h3_header)}\s*$(.*?)(?=^##\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        return []
    section_text = m.group(1)

    tables: list[list[list[str]]] = []
    current_table: list[list[str]] = []
    in_table = False
    in_code_block = False

    for line in section_text.splitlines():
        stripped = line.strip()
        # H3 이상 헤더 만나면 섹션 종료
        if stripped.startswith("###") and stripped != h3_header.strip():
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
                in_table = False
            break
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
                in_table = False
            continue
        if in_code_block:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
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


def check_domain_transaction_contracts(workspace: Path) -> list[Result]:
    """도메인 산출물의 Cross-domain Transaction Contracts 섹션 schema 검증 (#12).

    MANIFEST ## 도메인 분류 에서 등록된 도메인 별로:
    - ### Cross-domain Transaction Contracts H3 부재 → INFO 1 줄 (단일 DB 정상).
    - 존재 → 4 컬럼 + 헤더 정확 일치 + 변경 type 화이트리스트 검증.
    INFO-only (backward-compat: 기존 v0.2.x 산출물에 섹션 부재해도 INFO 만).
    """
    TX_SECTION_HEADER = "### Cross-domain Transaction Contracts"
    TX_EXPECTED_COLS = 4
    TX_EXPECTED_HEADERS = ["본 도메인 entry", "외부 도메인 영향", "변경 type", "file:line"]

    results: list[Result] = []

    manifest_path = workspace / "context" / "MANIFEST.md"
    if not manifest_path.is_file():
        return results

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except Exception:
        return results

    # MANIFEST 의 ## 도메인 분류 표에서 등록 도메인 + 진입 파일 추출
    domain_tables = _parse_md_tables_in_section(manifest_text, "## 도메인 분류")
    if not domain_tables or not domain_tables[0]:
        return results

    domain_table = domain_tables[0]
    context_dir = workspace / "context"

    for row in domain_table[1:]:  # 헤더 제외
        if not row or len(row) < 2:
            continue
        domain_name = row[0].strip()
        entry_rel = row[1].strip().strip("`")
        if not domain_name or not entry_rel:
            continue

        # 진입 파일 경로로 도메인 산출물 찾기
        entry_path = context_dir / entry_rel
        if not entry_path.is_file():
            # 진입 파일 없음 → skip (다른 검증이 이미 처리)
            continue

        try:
            domain_text = entry_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # ### Cross-domain Transaction Contracts 섹션 lookup
        tx_pattern = re.compile(
            r"^### Cross-domain Transaction Contracts\s*$",
            re.M,
        )
        has_tx_section = bool(tx_pattern.search(domain_text))

        entry_rel_display = entry_path.relative_to(workspace)

        if not has_tx_section:
            results.append(
                Result(
                    Result.INFO,
                    str(entry_rel_display),
                    f"### Cross-domain Transaction Contracts 부재 — 단일 DB 시스템이거나 미작성 (정상)",
                )
            )
            continue

        # 섹션 존재 — 표 파싱 + schema 검증
        tx_tables = _parse_md_tables_in_h3_section(domain_text, TX_SECTION_HEADER)

        if not tx_tables:
            # 섹션은 있지만 표 없음 → INFO (placeholder 허용)
            results.append(
                Result(
                    Result.INFO,
                    str(entry_rel_display),
                    f"### Cross-domain Transaction Contracts: 표 없음 — placeholder 상태 또는 수동 작성 진행 중",
                )
            )
            continue

        tx_table = tx_tables[0]
        if not tx_table:
            continue

        header_row = tx_table[0]
        col_count = len(header_row)

        # 컬럼 수 검증
        if col_count != TX_EXPECTED_COLS:
            results.append(
                Result(
                    Result.ERROR,
                    str(entry_rel_display),
                    (
                        f"### Cross-domain Transaction Contracts 표: "
                        f"컬럼 수 {col_count}개 ({TX_EXPECTED_COLS}개 필요) "
                        f"— 기대 헤더: {', '.join(TX_EXPECTED_HEADERS)}"
                    ),
                    f"표 헤더를 '| 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |' 형태로 수정",
                )
            )
            continue

        # 헤더 정확 일치 검증
        if header_row != TX_EXPECTED_HEADERS:
            results.append(
                Result(
                    Result.ERROR,
                    str(entry_rel_display),
                    (
                        f"### Cross-domain Transaction Contracts 표: "
                        f"헤더 불일치 (받은: {', '.join(header_row)}) "
                        f"— 기대: {', '.join(TX_EXPECTED_HEADERS)}"
                    ),
                    f"헤더를 정확히 '{', '.join(TX_EXPECTED_HEADERS)}' 로 수정",
                )
            )
            continue

        # 변경 type 화이트리스트 검증 (데이터 행)
        for i, data_row in enumerate(tx_table[1:], start=1):
            if not data_row or len(data_row) < TX_EXPECTED_COLS:
                continue
            # placeholder 행은 검증 skip
            if "(자동 detect 실패" in data_row[0] or "(없음)" in data_row[0]:
                continue
            tx_type_raw = data_row[2].strip()
            # (auto) 마커 제거 후 검증
            tx_type = tx_type_raw.replace(" (auto)", "").strip()
            if tx_type and tx_type not in _TX_TYPE_WHITELIST:
                results.append(
                    Result(
                        Result.ERROR,
                        str(entry_rel_display),
                        (
                            f"### Cross-domain Transaction Contracts 표: "
                            f"행 {i} 의 변경 type '{tx_type_raw}' 이 화이트리스트에 없음 "
                            f"— 허용: {', '.join(sorted(_TX_TYPE_WHITELIST))}"
                        ),
                        "변경 type 을 read / write / destroy / create 또는 '·' 구분 조합으로 수정",
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
# M1 자동 마이그레이션: v0.1.0 → v0.2.0
# ---------------------------------------------------------------------------

# v0.1.0 default 표 (backward-compat 주입용)
_V010_DEFAULT_DEPENDENCY_ROWS = """\
| Ruby | `require_relative` · 클래스 참조 (`OrderService`) → `app/**/order_service.rb` Glob |
| Kotlin | `import com.example.X` · `@Autowired`·`val foo: FooService` |
| TypeScript | `import { X } from "../foo"` · 상대 경로 추적 |
| Python | `from foo import X` · `import foo.bar` |
| Go | 동일 패키지 + `import "foo/bar"` |"""

_V010_DEFAULT_ROLE_ROWS = """\
| routes | `config/routes.rb` 도메인 라인·`@RestController` `@RequestMapping`·`*.routes.ts` `router.use` |
| controllers | `*_controller.rb`·`< ApplicationController`·`@RestController` `@Controller`·`*.controller.ts` |
| services | `*_service.rb`·`app/services/**`·`@Service`·`*.service.ts` |
| models | `app/models/**`·`< ApplicationRecord`·`@Entity`·`*.model.ts` `*.entity.ts` |
| helpers | `app/helpers/**`·util/lib 폴더·`*Util.kt` `*Helper.kt`·`*.util.ts` `*.helper.ts` |
| other | 위 어느 것도 아님 |"""


def _is_learn_section_empty(config_path: Path) -> bool:
    """config.md 의 ## learn 언어 패턴 두 표 모두 행이 0 인지 확인."""
    if not config_path.is_file():
        return True
    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception:
        return True
    tables = _parse_md_tables_in_section(text, "## learn 언어 패턴")
    if not tables:
        return True
    # 표 1 행 수 (헤더 제외)
    table1_data = len(tables[0]) - 1 if tables else 0
    # 표 2 행 수
    table2_data = (len(tables[1]) - 1) if len(tables) >= 2 else 0
    return table1_data == 0 and table2_data == 0


def _has_partial_learn_definition(config_path: Path) -> bool:
    """config.md 에 ## learn 언어 패턴 이 존재하지만 행 수 > 0 인지."""
    if not config_path.is_file():
        return False
    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception:
        return False
    tables = _parse_md_tables_in_section(text, "## learn 언어 패턴")
    if not tables:
        return False
    table1_data = len(tables[0]) - 1 if tables else 0
    table2_data = (len(tables[1]) - 1) if len(tables) >= 2 else 0
    return (table1_data > 0) or (table2_data > 0)


def _inject_v010_defaults_into_config(config_path: Path) -> tuple[bool, str]:
    """config.md 의 ## learn 언어 패턴 두 표에 v0.1.0 default 행을 주입."""
    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"read 실패: {e}"

    # 표 1 헤더 다음 줄에 의존성 추적 행 주입
    dep_header = "| 언어 | 의존성 추출 패턴 |"
    role_header = "| 역할 | 식별 패턴 |"

    # 헤더가 다양한 spacing 으로 작성될 수 있으므로 패턴 매칭
    import re as _re

    def _inject_after_header(content: str, header_pattern: str, rows: str) -> str:
        """헤더 행 + 구분선 다음에 rows 를 주입 (이미 행이 있으면 skip)."""
        lines = content.splitlines(keepends=True)
        out = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # 헤더 행 감지 (공백 무시)
            stripped = line.strip()
            cells = [c.strip() for c in stripped.strip("|").split("|")] if stripped.startswith("|") else []
            if len(cells) == 2 and _re.match(header_pattern, stripped):
                out.append(line)
                i += 1
                # 구분선
                if i < len(lines) and lines[i].strip().startswith("|") and all(
                    _re.match(r"^[-:]+$", c.strip()) for c in lines[i].strip().strip("|").split("|")
                ):
                    out.append(lines[i])
                    i += 1
                # 다음 행이 데이터가 아니면 주입 (빈 표)
                if i >= len(lines) or not lines[i].strip().startswith("|"):
                    for row in rows.splitlines():
                        out.append(row + "\n")
            else:
                out.append(line)
                i += 1
        return "".join(out)

    # 의존성 추적 표에 주입
    text = _inject_after_header(
        text,
        r"^\|\s*언어\s*\|\s*의존성 추출 패턴\s*\|$",
        _V010_DEFAULT_DEPENDENCY_ROWS,
    )
    # 역할 분류 표에 주입
    text = _inject_after_header(
        text,
        r"^\|\s*역할\s*\|\s*식별 패턴\s*\|$",
        _V010_DEFAULT_ROLE_ROWS,
    )

    try:
        config_path.write_text(text, encoding="utf-8")
    except Exception as e:
        return False, f"write 실패: {e}"
    return True, "v0.1.0 default 5 언어 표 주입 완료"


def migrate_v0_1_to_v0_2(workspace: Path, project: str) -> list[Result]:
    """M1 자동 마이그레이션: v0.1.0 → v0.2.0 거동.

    감지 조건:
    - .agent-state.yml.plugin_version 이 0.1.x 또는 부재
    - 현재 plugin 이 0.2.0+
    - workspace/context/config.md 의 ## learn 언어 패턴 두 표 모두 빈 행

    `--fix` 가 호출되어야 실행. interactive 환경에서 사용자 확인 (a/b/c),
    non-interactive 환경에서는 자동 미루기 (c 동등).
    """
    results: list[Result] = []

    state_yml = workspace / "projects" / project / ".agent-state.yml"
    config_path = workspace / "context" / "config.md"

    state_data = parse_state_yml(state_yml) or {}
    migration_flag = state_data.get("migration_v0_2_0")

    # 이미 결정된 경우 skip
    if migration_flag in ("accepted", "declined"):
        return results

    state_pv = state_data.get("plugin_version")
    current_pv = read_current_plugin_version()

    # 현재 plugin 버전 확인 — 0.2.0 미만이면 마이그레이션 대상 아님
    if current_pv:
        cv = _parse_semver(current_pv)
        if cv and cv < (0, 2, 0):
            return results

    # plugin_version 이 0.2.0+ 이면 신규 사용자 — skip
    if state_pv:
        sv = _parse_semver(state_pv)
        if sv and sv >= (0, 2, 0):
            return results

    # learn 섹션 확인
    if _has_partial_learn_definition(config_path):
        results.append(
            Result(
                Result.INFO,
                f"{project} migration",
                "config 의 ## learn 언어 패턴 이 부분 정의됨 — 마이그레이션 skip, 사용자 직접 갱신 권장",
            )
        )
        return results

    if not _is_learn_section_empty(config_path):
        return results

    # 마이그레이션 대상 확인됨 — fix callable 생성
    def _do_migrate():
        # interactive 여부 확인
        import sys as _sys
        is_interactive = _sys.stdin.isatty()

        if not is_interactive:
            print(
                f"  [INFO] {project} migration: non-interactive 환경 — "
                "마이그레이션 미루기 (doctor --fix 를 interactive 환경에서 실행하세요)"
            )
            return True, "non-interactive — 미루기 (다음 호출 시 다시 묻기)"

        print(
            f"\n  [UPGRADE] pilot 0.1.x → 0.2.0 — default 표가 SKILL.md 에서 폐지됐습니다.\n"
            f"  backward-compat 을 위해 v0.1.0 default 표를 {config_path} 에 자동 주입할까요?\n\n"
            f"    a) 주입 (권장) — v0.1.0 거동 그대로 유지\n"
            f"    b) 거부 — config 빈 채로 폴더 인접성 fallback 으로 전환 (사용자 자유 정의)\n"
            f"    c) 미루기 — 다음 doctor --fix 호출 시 다시 묻기\n"
        )
        try:
            choice = input("  선택 [a/b/c]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "c"

        # .agent-state.yml 갱신 헬퍼
        def _update_state(migration_val: str):
            try:
                lines = state_yml.read_text(encoding="utf-8").splitlines()
            except Exception:
                lines = []
            new_lines = []
            found_migration = False
            found_pv = False
            for line in lines:
                if line.strip().startswith("migration_v0_2_0:"):
                    new_lines.append(f"migration_v0_2_0: {migration_val}")
                    found_migration = True
                elif line.strip().startswith("plugin_version:"):
                    new_lines.append("plugin_version: 0.2.0")
                    found_pv = True
                else:
                    new_lines.append(line)
            if not found_migration:
                new_lines.append(f"migration_v0_2_0: {migration_val}")
            if not found_pv:
                new_lines.append("plugin_version: 0.2.0")
            content = "\n".join(new_lines)
            if not content.endswith("\n"):
                content += "\n"
            state_yml.write_text(content, encoding="utf-8")

        if choice == "a":
            ok, msg = _inject_v010_defaults_into_config(config_path)
            if ok:
                _update_state("accepted")
                return True, f"v0.1.0 default 표 주입 완료 + plugin_version → 0.2.0"
            return False, f"주입 실패: {msg}"
        elif choice == "b":
            _update_state("declined")
            return True, "거부 — config 빈 채로 유지, plugin_version → 0.2.0"
        else:
            return True, "미루기 — 다음 doctor --fix 호출 시 다시 묻기"

    results.append(
        Result(
            Result.WARN,
            f"{project} migration",
            (
                f"pilot 0.1.x → 0.2.0 업그레이드 감지: ## learn 언어 패턴 이 비어있음. "
                "`doctor --fix` 로 v0.1.0 default 표 주입 또는 거부 선택 가능"
            ),
            "doctor --fix 실행하여 마이그레이션 진행",
            fix=_do_migrate,
        )
    )
    return results


# ---------------------------------------------------------------------------
# #16 Onboarding Health 검사 (OH-1~5)
# ---------------------------------------------------------------------------

def _check_oh1_config_sections(workspace: Path) -> list[Result]:
    """OH-1: workspace/context/config.md 의 3 핵심 섹션 표 본문 행 수 ≥ 1.

    ## learn 언어 패턴 / ## scope 카테고리 / ## Ignore 3 섹션 검증.
    _parse_md_tables_in_section 헬퍼 재사용 (인수인계 line 88).
    """
    config_path = workspace / "context" / "config.md"
    if not config_path.is_file():
        # config.md 부재는 구조 정합성 ERROR 가 사전 처리 — OH-1 진입 안 함
        return []

    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception:
        return []

    SECTIONS = [
        "## learn 언어 패턴",
        "## scope 카테고리",
        "## Ignore",
    ]

    all_filled = True
    results: list[Result] = []

    for section_header in SECTIONS:
        tables = _parse_md_tables_in_section(text, section_header)
        filled = False
        if tables:
            # 첫 번째 표의 헤더 제외 본문 행 수 ≥ 1 이면 채워진 것
            table0 = tables[0]
            data_rows = len(table0) - 1  # 헤더 행 제외
            filled = data_rows >= 1

        if not filled:
            all_filled = False
            results.append(
                Result(
                    Result.WARN,
                    f"OH-1  config 핵심 섹션",
                    f"'{section_header}' 미채움",
                    "수동으로 config.md 편집 (또는 /pilot:init --rewizard v2 — 미구현)",
                )
            )

    if all_filled:
        results.append(
            Result(Result.PASS, "OH-1  config 핵심 섹션", "3 섹션 모두 채워짐")
        )

    return results


def _check_oh2_scope_dir(workspace: Path) -> list[Result]:
    """OH-2: workspace/context/scope/ 디렉터리에 *.md 파일 ≥ 1."""
    scope_dir = workspace / "context" / "scope"
    if not scope_dir.is_dir() or not list(scope_dir.glob("*.md")):
        return [
            Result(
                Result.WARN,
                "OH-2  scope/ 채움",
                "scope/ 미채움 (*.md 파일 없음)",
                "/pilot:learn <진입파일> 호출 권장 (analyze 가 scope 파일 생성)",
            )
        ]
    return [Result(Result.PASS, "OH-2  scope/ 채움", "*.md 파일 존재")]


def _check_oh3_project_registered(workspace: Path) -> list[Result]:
    """OH-3: workspace/STATE.md 의 진행중 또는 대기 프로젝트 ≥ 1.

    STATE.md 부재 시 구조 정합성 ERROR 가 사전 차단 — 여기서는 존재 전제.
    """
    state_md = workspace / "STATE.md"
    if not state_md.is_file():
        # 구조 정합성에서 이미 ERROR — OH-3 진입 안 함
        return []

    try:
        text = state_md.read_text(encoding="utf-8")
    except Exception:
        return []

    count = 0
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3:
            continue
        status = cells[2]
        # 헤더·구분선 제외
        if status in ("상태", "status") or set(status) <= set("-: "):
            continue
        if status in ("진행중", "대기"):
            count += 1

    if count == 0:
        return [
            Result(
                Result.WARN,
                "OH-3  첫 project 등록",
                "등록 프로젝트 없음 (진행중/대기 0건)",
                "/pilot:project {이름} 호출 권장",
            )
        ]
    return [Result(Result.PASS, "OH-3  첫 project 등록", f"진행중/대기 {count}건")]


def _check_oh4_manifest_entry(workspace: Path) -> list[Result]:
    """OH-4: workspace/context/MANIFEST.md 의 ## 도메인 분류 표 본문 행 수 ≥ 1.

    _parse_md_tables_in_section 헬퍼 재사용 (OH-1 과 공유).
    placeholder 행 (|  |  |  |) 은 0 으로 카운트.
    """
    manifest = workspace / "context" / "MANIFEST.md"
    if not manifest.is_file():
        # 구조 정합성에서 ERROR — OH-4 진입 안 함
        return []

    try:
        text = manifest.read_text(encoding="utf-8")
    except Exception:
        return []

    tables = _parse_md_tables_in_section(text, "## 도메인 분류")
    filled = False
    if tables:
        table0 = tables[0]
        # 헤더 제외 본문 행, placeholder 제외
        for row in table0[1:]:
            if row and any(c.strip() for c in row):
                # 모든 셀이 비어있지 않은 경우만 유효 행
                if not all(c.strip() == "" for c in row):
                    filled = True
                    break

    if not filled:
        return [
            Result(
                Result.WARN,
                "OH-4  MANIFEST 진입파일",
                "## 도메인 분류 표 미등록",
                "/pilot:learn <진입파일> 호출 권장",
            )
        ]
    return [Result(Result.PASS, "OH-4  MANIFEST 진입파일", "도메인 분류 표 등록됨")]


def _check_oh5_features_entry(workspace: Path, project: str) -> list[Result]:
    """OH-5: workspace/projects/{project}/features/ 에 *.md 파일 ≥ 1.

    .plan.md 포함, hidden 파일 (. 시작) 제외.
    인수인계 line 115 의 check_features_open_questions 순회 패턴 답습.
    """
    features_dir = workspace / "projects" / project / "features"
    if not features_dir.is_dir():
        return [
            Result(
                Result.WARN,
                "OH-5  features/ 진입 가능",
                "features/ 디렉터리 없음",
                "@pilot-planner 또는 /pilot:create-feature 호출 권장",
            )
        ]

    md_files = [
        p for p in features_dir.glob("*.md")
        if not p.name.startswith(".")
    ]
    if not md_files:
        return [
            Result(
                Result.WARN,
                "OH-5  features/ 진입 가능",
                "features/ 비어있음 (*.md 파일 없음)",
                "@pilot-planner 또는 /pilot:create-feature 호출 권장",
            )
        ]
    return [Result(Result.PASS, "OH-5  features/ 진입 가능", f"*.md {len(md_files)}건")]


def check_onboarding_health(workspace: Path, project: str | None = None) -> list[Result]:
    """OH-1~5 dispatcher.

    OH-1~4 는 항상 실행. OH-5 는 project 인자 지정 시만 실행.
    project 미지정 시 OH-5 = INFO (N/A).
    반환: list[Result] (PASS / WARN / INFO — ERROR 사용 안 함).
    """
    results: list[Result] = []

    # OH-1: config.md 핵심 섹션
    results.extend(_check_oh1_config_sections(workspace))

    # OH-2: scope/ 채움
    results.extend(_check_oh2_scope_dir(workspace))

    # OH-3: 첫 project 등록
    results.extend(_check_oh3_project_registered(workspace))

    # OH-4: MANIFEST 진입파일
    results.extend(_check_oh4_manifest_entry(workspace))

    # OH-5: features/ (프로젝트 인자 지정 시만)
    if project is not None:
        results.extend(_check_oh5_features_entry(workspace, project))
    else:
        results.append(
            Result(
                Result.INFO,
                "OH-5  features/ 진입 가능",
                "N/A — 프로젝트 지정 시 features/ 진입 가능성 검사",
            )
        )

    return results


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

    # domain 산출물 transaction contracts schema 검증 (#12)
    tx_results = check_domain_transaction_contracts(workspace)
    for r in tx_results:
        print(r.render())
    all_results.extend(tx_results)

    # Project
    project = project or determine_active_project(workspace)
    if not project:
        print(
            f"\n{YELLOW}활성 프로젝트 없음 — 프로젝트 체크 건너뜀 "
            f"(--project 인자로 대상 지정 가능){RESET}"
        )
        if fix:
            run_auto_fixes(all_results)

        # 활성 프로젝트 없어도 OH-1~4 는 검사, OH-5 = N/A (spec line 50)
        print(f"\n{BOLD}── Onboarding Health ─────────────────{RESET}")
        if fix:
            print(f"  [{RESET}INFO{RESET}] --fix 모드 — onboarding-health 섹션 skip (사용자 의도 필요)")
        else:
            oh_results = check_onboarding_health(workspace, project=None)
            # WARN 4룰 (OH-1~4) 모두 발화 시 안내 1줄 (OH-5 는 N/A)
            oh_rules_warn = set()
            for r in oh_results:
                if r.level == Result.WARN:
                    for prefix in ("OH-1", "OH-2", "OH-3", "OH-4"):
                        if r.label.startswith(prefix):
                            oh_rules_warn.add(prefix)
                            break
            if len(oh_rules_warn) >= 4:
                print(f"  [{YELLOW}INFO{RESET}] 신규 워크스페이스 감지 — getting-started.md 권장 (pilot/docs/getting-started.md)")
            for r in oh_results:
                print(r.render())
            all_results.extend(oh_results)

        return summarize(all_results)

    print(f"\n{BOLD}Project ({project}):{RESET}")
    proj_results = check_project(workspace, project)
    for r in proj_results:
        print(r.render())
    all_results.extend(proj_results)

    # M1 마이그레이션 감지 (프로젝트 정보 필요)
    migration_results = migrate_v0_1_to_v0_2(workspace, project)
    for r in migration_results:
        print(r.render())
    all_results.extend(migration_results)

    if fix:
        run_auto_fixes(all_results)

    # Onboarding Health 섹션 (--fix 시 skip)
    print(f"\n{BOLD}── Onboarding Health ─────────────────{RESET}")
    if fix:
        print(f"  [{RESET}INFO{RESET}] --fix 모드 — onboarding-health 섹션 skip (사용자 의도 필요)")
    else:
        oh_results = check_onboarding_health(workspace, project)
        # WARN 5건 동시 시 안내 1줄 (OH-1~5 각 룰이 모두 WARN 상태인 경우)
        # OH-1 은 섹션별 복수 WARN 가능 — 룰 단위로 판정 (label prefix 기반)
        oh_rules_warn = set()
        for r in oh_results:
            if r.level == Result.WARN:
                for prefix in ("OH-1", "OH-2", "OH-3", "OH-4", "OH-5"):
                    if r.label.startswith(prefix):
                        oh_rules_warn.add(prefix)
                        break
        # OH-5 는 project 인자 지정 시만 포함 (N/A 이면 4룰 기준으로 제외)
        oh_total_rules = 5 if project is not None else 4
        if len(oh_rules_warn) >= oh_total_rules:
            print(f"  [{YELLOW}INFO{RESET}] 신규 워크스페이스 감지 — getting-started.md 권장 (pilot/docs/getting-started.md)")
        for r in oh_results:
            print(r.render())
        all_results.extend(oh_results)

    return summarize(all_results)
