# #24 pilot-update.sh 고장 — 경로 stale + 설계 한계

> source: prompt
> created: 2026-07-25T00:00:00Z
> user_prompt: "pilot-update.sh 가 동작하지 않고, 고쳐도 설치 캐시를 갱신하지 못한다는 사실이 v0.10.0 업그레이드 중 드러남 — 도구의 존재 이유를 재검토해 별도 feature 로 등록"

## 요구사항

- **조건**: v0.10.0 릴리스 직후. 2026-07-25 실제 업그레이드 시도 중 발견.
- **트리거**: 문서가 업그레이드 수단으로 안내하는 `pilot/tools/pilot-update.sh` 가 **어떤 환경에서도 즉시 실패**한다. 그리고 실패를 고쳐도 목적을 달성하지 못한다.
- **기대결과**: 아래 두 층위를 구분해 처리한다.

  **(A) 경로 stale — 확정 버그**
  - `pilot/tools/pilot-update.sh:17` 이 `CACHE_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins"` 를 가리킨다.
  - 실제 디렉터리는 `~/.claude/plugins/marketplaces/radiostart-plugins` — 커밋 `19a7ff9` ("마켓플레이스 이름 claude-plugins → radiostart-plugins") 에서 개명됐고 스크립트만 따라가지 않았다.
  - 실측 출력: `✗ 캐시 디렉토리 없음: /Users/.../marketplaces/claude-plugins` 후 즉시 종료.
  - 동일 stale 경로가 문서에도 전파돼 있다: `pilot/README.md:50` (alias 정의) · `pilot/tools/pilot-update.sh:9` (주석 내 alias 예시).

  **(B) 설계 한계 — 고쳐도 목적 미달**
  - 스크립트는 `marketplaces/` **git clone 만** fast-forward 한다 (`:45`·`:66`).
  - 그런데 플러그인이 실제 로드되는 경로는 `~/.claude/plugins/cache/{marketplace}/pilot/{version}/` 이고, `installed_plugins.json` 의 `installPath` 가 이를 가리킨다. **스크립트는 이 경로를 건드리지 않는다.**
  - 실측: 마켓플레이스 클론을 165커밋 fast-forward 해 `plugin.json` 이 `0.10.0` 이 된 뒤에도 `cache/` 에는 `0.1.0`·`0.4.0` 만 존재했고, `0.4.0/tools/` 에 삭제 대상인 `init_detect.py`·`memory-hint.py` 가 그대로 있었다.
  - 사용자가 `/plugin` 으로 업데이트하자 `cache/pilot/0.10.0/` 이 생성되고 레지스트리가 그리로 전환됐다 — **캐시 생성은 `/plugin` 의 몫**임이 확인됐다.
  - 즉 스크립트의 전제("`/plugin` 이 막힌 환경의 대체 수단", `:2`)가 성립하지 않는다. 마켓플레이스 클론만 최신이어도 로드되는 플러그인은 구버전 그대로다.

  **(C) 잘못된 안내 제거**
  - 현재 `pilot-update.sh` 를 업그레이드 수단으로 안내하는 곳: `pilot/README.md:50-55`·`:147` · `pilot/docs/tutorial/getting-started.md:338` · v0.10.0 릴리스 노트.
  - (B) 결론에 따라 안내 문구를 정정하거나 제거해야 한다. 지금은 **사용자가 따라 해도 업그레이드가 되지 않는다.**

## 상태 전환

_(없음)_

## 비즈니스 규칙

- 사용자 전역 설치본(`~/.claude/plugins/`)을 스크립트가 **직접 조작하지 않는다** — `installed_plugins.json` 레지스트리와 어긋난 상태를 만들 수 있다. 캐시 생성·전환은 `/plugin` 에 위임한다.
- (A) 만 고치고 (C) 를 방치하면 "실행은 되지만 업그레이드는 안 되는" 더 나쁜 상태가 된다 — 실패가 조용해진다. (A)·(C) 는 같은 사이클에서 처리한다.
- 문서·주석·릴리스 노트에 남은 stale 경로는 한 번에 정리한다 (마켓플레이스 개명이 이미 한 번 누락된 전례).

## 예외 케이스

- `/plugin` 이 실제로 막힌 환경(IDE 내장·관리형 세션)이 존재한다면 대체 수단 자체는 여전히 필요하다 — 그 경우 스크립트가 `cache/` 와 레지스트리까지 다뤄야 하는데, 이는 Claude Code 내부 계약에 의존하므로 버전 변화에 취약하다. **존치 여부 자체가 결정 대상.**
- 개명 전 이름(`claude-plugins`)으로 마켓플레이스를 추가해 둔 기존 사용자가 있을 수 있다 — 경로를 하드코딩하지 말고 탐지하는 편이 안전하다.
- `getting-started.md:338` 은 `# 또는: /plugin update pilot@claude-plugins` 주석도 **구 마켓플레이스명**을 쓴다. 이 경로로 실행하면 실패한다.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- [x] `/plugin` 이 캐시를 채우는 정확한 절차와 레지스트리 갱신 규약은 Claude Code 내부 동작이라 공개 spec 이 없다 — 스크립트가 이를 재현하려 할 경우 근거 부재 → **(ii) 확장안 배제 근거로 소화.** 재현 근거가 없으므로 확장하지 않는다

### (d) 비즈니스 결정 영역
- [x] **도구 존치 여부** — (i) 경로만 고쳐 "마켓플레이스 클론 동기화 도구"로 목적을 축소하고 이름·문서를 그에 맞게 정정 (ii) `cache/` + 레지스트리까지 다루도록 확장 (iii) 폐기하고 `/plugin` 안내로 일원화 → **(iii) 폐기.** (i) 은 `/plugin marketplace update` 와 중복이면서 나머지 절반(`/plugin update`)을 못 해 목적 미달, (ii) 는 비즈니스 규칙(전역 설치본 불가침) + (c)1 근거 부재로 배제. `/plugin` 이 없는 환경은 **미지원**으로 명시하는 것이 정확한 서술
- [x] 릴리스 노트(v0.10.0)에 이미 나간 잘못된 안내를 정정할 것인가 → **범위 분리 (2026-07-26).** 저장소 밖 상태 변경이라 본 사이클의 git 게이트가 듣지 않는다. 사용자 명시 승인 시 `gh release edit` 로 별도 처리 (절차는 `.plan.md` 스텝 2 참조 — 백업 → 취득 → 교체 → diff 검증)

## 구현 결과 (2026-07-26)

- `pilot/tools/pilot-update.sh` 삭제 (79줄).
- `pilot/README.md` — `:35` 설치 명령 id 정정 (**신규 설치 실패 버그**) · `:42` 업데이트 명령 정정 + 레포 경로 ↔ 마켓플레이스 id 구분 주석 · `/plugin` 이 막힌 환경 블록을 조건부 서술로 교체 (헬퍼 alias 삭제) · `:146` 업데이트 안내 정정.
- `pilot/docs/tutorial/getting-started.md` — Troubleshooting 5 의 업데이트 블록 정정 + `## 에이전트 간 전달사항` 의 "orchestrate-load 설정" 허구 서술 삭제 (D4).
- `pilot/docs/explanation/release-and-upgrade.md:68` — "수동 `pip` / `git pull`" 제거, `/plugin` 2단계 + 세션 재시작으로 정정.
- 게이트: stale 마켓플레이스 id **0건** (변경 전 9줄/10건) · `pilot-update` 문자열 **0건** (변경 전 10건, `.github/` 0건) · `radiostart/claude-plugins` 레포 슬러그는 보존 (과잉 치환 없음) · `docs_build.py --check` exit 0 · `doctor --schema` 6 PASS · 0 WARN · 0 ERROR.
