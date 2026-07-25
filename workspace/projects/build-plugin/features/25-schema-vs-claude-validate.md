# #25 `doctor --schema` ↔ `claude plugin validate` 중복 검토

> source: prompt
> created: 2026-07-25T00:00:00Z
> user_prompt: "#20 에서 유지·CI 신설한 schema.py 가 하는 일이 Claude Code 자체 `claude plugin validate` 와 겹친다 — 자체 구현 유지 이유를 재검토"

## 요구사항

- **조건**: #20 완료 상태 (`schema.py` 410줄 유지 + `.github/workflows/validate.yml` 신설).
- **트리거**: Claude Code CLI 에 `claude plugin validate <path>` 가 존재하며 우리 `doctor --schema` 와 검사 범위가 상당 부분 겹친다. 정비의 목적이 "자체 구현 축소" 였으므로 유지 근거를 재확인해야 한다.
- **기대결과**: 아래 실측 대조를 근거로 (a) `schema.py` 축소·폐기 후 CLI 위임 (b) 현행 유지 (c) 역할 분담 재정의 중 하나를 확정하고 반영한다.

### 실측 대조 (2026-07-25, 손상본 주입 실험)

`pilot/` 사본에 결함 3종을 심고 양쪽을 실행한 결과:

| 결함 | `claude plugin validate` | `doctor --schema` |
|---|---|---|
| `SKILL.md` frontmatter 블록 없음 | ⚠ WARNING — 통과 | ❌ ERROR — 차단 |
| `hooks.json` 에 없는 이벤트명 (`BogusEvent`) | ✘ ERROR | ❌ ERROR |
| `hooks.json` JSON 문법 파손 | ✘ ERROR (+ "At runtime this breaks the entire plugin load" 안내) | (문법 파손은 미검증) |
| `plugin.json` 미지 키 (`bogus_key`) | ⚠ WARNING — "Claude Code ignores it at load time" | ✅ PASS (금지 키 목록 방식이라 미탐) |
| `plugin.json` version ↔ git tag 불일치 | 미검사 | ⚠ WARN |

정상 상태 실행: `claude plugin validate ./pilot` → `✔ Validation passed` (exit 0) · `doctor --schema` → `6 PASS · 0 WARN · 0 ERROR`.

### 대조에서 드러난 것

- **완전 포함 관계가 아니다.** CLI 는 JSON 문법 파손·미지 키를 잡고, 우리 것은 version↔tag 정합을 잡는다. 어느 쪽도 상위 집합이 아니다.
- **심각도 정책이 다르다.** frontmatter 부재를 CLI 는 WARNING(통과), 우리는 ERROR(CI 차단)로 본다. **CLI 로 단순 교체하면 CI 게이트가 느슨해진다** — `validate.yml` 이 지금 막고 있는 것을 통과시키게 된다.
- **관련 CLI 도 있다.** `claude plugin tag` 는 "plugin.json 과 마켓플레이스 엔트리가 일치하는지 검증" 한다고 기술돼 있어 version 계열 검사와 겹칠 여지가 있다 — 실측 미확인.

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **CI 게이트 강도를 낮추지 않는다.** 위임하더라도 frontmatter 부재가 ERROR 로 남아야 한다 (CLI 가 WARNING 이면 exit code 로 막을 수 없으므로 별도 처리 필요).
- 외부 CLI 에 의존하면 **Claude Code 버전에 따라 거동이 변한다** — CI 에서 CLI 버전을 고정하거나, 변화가 게이트를 무력화하지 않도록 방어할 것.
- 자체 구현을 남기는 부분은 **"CLI 가 못 하는 것" 으로 근거를 명시**할 것. 근거 없이 중복 유지하지 않는다.

## 예외 케이스

- CI 환경(GitHub Actions runner)에 `claude` CLI 가 설치·인증돼 있어야 한다 — 현재 `validate.yml` 은 `python3` 만 요구한다. 위임 시 CI 전제가 무거워진다.
- `claude plugin validate` 의 출력 형식·exit code 계약은 공개 spec 이 없다 — 파싱해 게이트로 쓰면 취약하다.
- `schema.py` 는 `--schema` 외 다른 호출처가 없는지 확인할 것 (있으면 폐기 범위가 달라진다).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- [ ] `claude plugin validate` 의 exit code·출력 형식 계약이 문서화돼 있지 않다 — CI 게이트로 쓸 근거 부족
- [ ] `claude plugin tag` 가 실제로 검증하는 범위 미확인 (version↔marketplace 정합 중복 여부)

### (d) 비즈니스 결정 영역
- [ ] 처리 방향 — (i) `schema.py` 를 CLI 미커버 항목(version↔tag)만 남기고 축소 + CI 는 양쪽 병행 (ii) 현행 유지하고 중복을 감수 (iii) CLI 로 전면 위임. (iii) 은 CI 전제가 무거워지고 심각도 정책이 느슨해져 권장하지 않음
- [ ] CI 에서 `claude plugin validate` 를 병행 실행할 것인가 — 러너에 CLI 설치·인증 비용 대비 이득 판단
