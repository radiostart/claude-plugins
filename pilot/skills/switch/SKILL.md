---
name: switch
description: >-
  최근 진행한 project·issue 목록을 조회하고 그중 하나로 전환할 때 사용한다
  — 작업 이름이 기억나지 않을 때의 진입점. 신규 생성은
  `/pilot:project`·`/pilot:issue` 를 직접 사용한다.
---

최근 작업 목록을 조회하고 선택 항목으로 전환한다.

대상 (선택): $ARGUMENTS — 전환할 project·issue 이름 (부분 일치 허용)

**읽기 전용 계약** — 본 스킬은 STATE.md 를 포함한 workspace 의 어떤 파일도 Write/Edit 하지 않는다. 목록은 매 호출 폴더에서 파생하며 (저장 상태 없음 — 이력의 SSOT 는 폴더 자체, preamble P2 원칙), 전환의 쓰기 (STATE.md 갱신·컨텍스트 적재) 는 4단계에서 위임받은 project/issue 스킬 절차가 전부 수행한다.

## 사전 확인

P 절차 비적용 — 사유는 [preamble.md](../context/shared/preamble.md) § 스킬별 P 절차 적용표의 switch 각주 참조 (workspace 존재 확인은 1단계 스캐너가 수행하고, P2/P3 는 위임된 스킬이 수행한다).

## 수행 절차

### 1. 스캔

아래 Bash 명령을 이 턴에 1회 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/switch-scan.py workspace
```

- exit 1 (workspace 부재) 이면 도구 출력을 그대로 표시하고 종료.
- `WARN:` 라인 (STATE corrupt·활성 폴더 부재) 은 가공 없이 그대로 표시하고 **계속 진행**한다 — 본 스킬은 STATE 가 깨진 상황의 복구 진입점이므로 fail-fast 하지 않는다.

### 2. 표 출력

도구가 출력한 표 (+ `외 N건` 문구) 를 그대로 보여준다. 항목이 0건이면 도구의 안내 메시지로 종료.

### 3. 대상 확정

- **`$ARGUMENTS` 있음** — 표의 이름들과 부분 일치 매칭 (대소문자 무시):
  - 단일 매치 → 4단계로.
  - 다중 매치 (동명 project/issue 포함) → 후보만 mode 병기로 재표시하고 어느 것인지 질의.
  - **무매치 → 위임하지 않고 종료.** "목록에 없습니다. 신규 생성은 `/pilot:project {이름}` (프로젝트) 또는 `/pilot:issue {이슈명}` (이슈) 를 직접 호출하세요." 출력 — 오타가 확인 없는 신규 폴더 생성으로 이어지는 것을 막기 위한 의도적 단절이다. 본 스킬은 신규 생성을 대행하지 않는다.
- **`$ARGUMENTS` 없음** — `ToolSearch select:AskUserQuestion` 으로 JIT 로드 후 **1회 질의** (deferred 도구라 선로딩 없이 직접 호출하면 InputValidationError — preamble § 자주 쓰는 deferred 도구):
  - 선택지 = `최근` 상위 3건 (label: 이름, description: mode·요약) + "취소 — 전환하지 않고 명령 목록만 보기" 로 총 4옵션. 표의 나머지 항목은 도구가 자동 제공하는 "Other" 로 이름을 직접 입력받는다.
  - 취소 선택·무응답·질의 실패 (도구 미로드 포함) 시: abort 하지 않고 각 항목의 전환 명령 (`/pilot:project {이름}` / `/pilot:issue {이슈명}`) 목록만 남기고 종료한다.

### 4. 위임

선택 항목의 mode 에 따라 **Skill 도구**로 위임한다:

- `project` → skill `pilot:project`, 인자 = 이름
- `issue` → skill `pilot:issue`, 인자 = 이름

위임받은 스킬의 절차 전체 (P2 STATE 갱신·기존 폴더 Read-only 로드·drift 체크·doctor 검증) 가 그대로 수행된다 — switch 가 그 절차를 요약·생략하지 않는다.

- **폴백**: 하니스가 스킬 실행 중 Skill 도구 호출을 차단하거나 호출이 실패하면, 해당 스킬 본문 (`${CLAUDE_PLUGIN_ROOT}/skills/project/SKILL.md` 또는 `${CLAUDE_PLUGIN_ROOT}/skills/issue/SKILL.md`) 을 Read 하여 그 절차 **전체**를 이 턴에서 그대로 수행한다 (부분 수행 금지).
- 알려진 마찰 1건: issue 위임 시 issue 절차 2 (유사 이슈 "재개할까요?" 질의) 가 방금 고른 항목에 확인 1회를 중복시킬 수 있다 — 정상 동작이며 그대로 답하면 된다.
