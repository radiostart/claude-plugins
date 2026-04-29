# `--regen-agents` 모드

scope/{domain}.md 가 업데이트됐거나 features 가 여러 개 추가돼 `prompts/*.md` 가 구식일 때 사용한다.

**전제:** `features/*.md` 가 1 개 이상 존재해야 한다. 0 개면 "재생성할 대상 없음. 먼저 `/pilot:analyze` 로 docs 분석이 필요합니다." 안내 후 종료.

**동작:** 메인 분석 프로세스의 1·2·3·4 단계 (docs 읽기·분할·저장) 를 건너뛰고 아래 순서로 실행한다:

1. **백업 (필수)** — 아래 "백업 단계" 참조. 기존 prompts/*.md 를 `.prompts.bak/{timestamp}/` 로 복사.
2. 5 단계 — `project.md` 관련 파일 표 재기입
3. 6-1 / 6-2 / 6-3 — prompts/*.md 재작성
4. 6-4 — `.agent-state.yml` 의 `analyzed_at`, `last_analyzed_features` 갱신
5. **post-regen 검증 (필수)** — 아래 "중복 감지" 참조. doctor 돌려 중복 섹션 WARN 확인
6. 7 단계 — 분석 품질 자가 검증 중 **7-2, 7-3 만** 수행 (7-1 커버리지·7-4 추측 혐의는 docs 재변환이 없으므로 제외)
7. 8 단계 — 결과 출력 (백업 경로 + WARN 여부 포함)

기존 수동 편집 영역 (planner 의 `## 플래닝 프로세스` 하위 등) 은 보존한다. 섹션별 보존 규칙은 [`agents-update.md`](agents-update.md) 의 6-1 / 6-2 / 6-3 참조.

---

## 백업 단계

regen 은 사용자 수동 편집을 의도치 않게 덮어쓸 위험이 있어 항상 백업을 선행한다 (복구·수동 머지 대비). 아래 Bash 로 기존 agents 폴더를 복사한다:

```bash
TS=$(date -u +%Y-%m-%dT%H-%M-%S)
PROJ=workspace/projects/{PROJECT}
mkdir -p ${PROJ}/.agents.bak/${TS}
cp -R ${PROJ}/prompts/. ${PROJ}/.prompts.bak/${TS}/
```

실행 후 사용자에게 백업 경로 (`workspace/projects/{PROJECT}/.agents.bak/{timestamp}/`) 를 알린다. regen 결과가 예상과 다르면 이 경로에서 원본을 복원할 수 있다.

`.agents.bak/` 는 `.gitignore` 권장 (로컬 복구용).

---

## 중복 감지

regen 완료 후 doctor 를 실행해 중복 H2 섹션을 감지한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --project {PROJECT}
```

WARN 에 `duplicate section` 이 포함되면:

- 기존 파일의 비표준 섹션이 regen 으로 인해 **중복 주입** 된 상태.
- 백업 경로와 현재 파일을 비교해 **수동 머지 필요** 를 사용자에게 명시한다.
- 머지 규칙 예시:
  - 동일 헤딩 2 개 → 최신 (analyze-주입) 내용 채택 + 구 버전의 추가 정보는 `## 주의사항` 등 `[analyze-managed]` 없는 섹션으로 이전
  - drift 원인이 도메인 규칙 하드코드면 `rules/{domain}.md` 로 이관
