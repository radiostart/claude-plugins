# doctor — `--fix` v0.1.0 → v0.2.0 마이그레이션

pilot v0.2.0 부터 `## learn 언어 패턴` 의 default 표가 SKILL.md 에서 제거됐다. `--fix` 실행 시 다음 조건을 자동 감지해 사용자에게 마이그레이션을 제안한다.

---

## 감지 조건

- `.agent-state.yml.plugin_version` 이 `0.1.x` 또는 부재 + 현재 plugin 이 `0.2.0+` + `workspace/context/config.md` 의 `## learn 언어 패턴` 두 표 모두 빈 행.

---

## 동작

interactive 환경에서 `a) 주입 / b) 거부 / c) 미루기` 선택. non-interactive 환경에서는 자동 미루기 (hang 방지).

| 선택 | 결과 |
|---|---|
| **a) 주입** | v0.1.0 default 5 언어 표를 `config.md` 에 자동 주입 + `.agent-state.yml.migration_v0_2_0: accepted` + `plugin_version: 0.2.0` |
| **b) 거부** | config 빈 채로 유지 + `migration_v0_2_0: declined` + `plugin_version: 0.2.0` |
| **c) 미루기** | 변경 없음, 다음 `--fix` 호출 시 다시 묻기 |

---

## 예외

- **부분 정의 사용자**: `## learn 언어 패턴` 에 이미 행이 있으면 마이그레이션 skip + INFO.
- **신규 사용자** (`plugin_version: 0.2.0` 부터): 마이그레이션 skip.
