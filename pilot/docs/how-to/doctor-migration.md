# Doctor 진단·마이그레이션

!!! info "한 줄 요약"
    `workspace/` 정합성 검사 + 자동 마이그레이션. `.agent-state.yml` schema v1.1 → v1.2 같은 업그레이드, STATE/MANIFEST/config 누락, `analyzed`·`tdd` 플래그와 실제 파일 상태의 불일치 (STATE corrupt) 를 조기 감지한다.

## 전제

- `workspace/` 가 존재한다 (`/pilot:init` 이후).
- 다음 중 하나에 해당 — 정기 점검 또는 의심 신호:
    - 새 버전으로 plugin 업그레이드 후 처음 작업.
    - subagent 호출이 *원인 모호한* 에러를 낸다.
    - `.agent-state.yml` 또는 `STATE.md` 를 수동 편집했다.

## 절차

### 1. 진단 (read-only)

```bash
/pilot:doctor
```

검사 항목:

- `STATE.md` 의 활성 프로젝트 수 (1 개만 허용).
- 각 활성 프로젝트의 `.agent-state.yml` schema 버전과 필수 키.
- `MANIFEST.md`·`config.md` 존재와 형식.
- `analyzed` 플래그와 실제 `features/` 폴더 상태의 일치.
- `tdd` 플래그와 `prompts/*.md` 본문의 일치.
- 의존하는 `docs/`·기획서 파일 누락.

출력은 카테고리별 PASS / WARN / FAIL 로 구분된다. 수정 액션 권장이 함께 표시.

### 2. 자동 수정 (`--fix`)

수정 가능한 항목만 자동 적용:

```bash
/pilot:doctor --fix
```

대표 수정 경로:

- **schema 마이그레이션** — v1.0 → v1.1 → v1.2. 누락된 필수 필드 (`plugin_version`·`mode` 등) 를 안전한 default 로 채우고 backup 을 `.agent-state.yml.bak-{version}` 으로 남긴다.
- **MANIFEST 깨진 행 정리** — 형식 어긋난 표 row 를 사용자 확인 후 수정.
- **prompts/ 재생성** — `--regen-agents` 와 동일 효과 (project.md 의 [analyze-managed] 영역만).

자체 판단으로 침묵 수정하는 항목은 *없다* — 모든 수정 전 사용자 확인.

### 3. 변경 검증

수정 후 다시:

```bash
/pilot:doctor
```

모든 항목 PASS 인지 확인. WARN 이 남아도 동작은 가능하지만 다음 작업 전에 정리 권장.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:doctor`](../reference/skills/doctor.md) · [state-schema](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/lifecycle/state-schema.md)
- :material-lightbulb-on: Explanation: schema 진화 정책과 wrapper 계약 호환성은 [릴리스·업그레이드](../explanation/index.md) 에서.
