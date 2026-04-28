# Lifecycle 문서 인덱스

`skills/context/lifecycle/` 폴더의 진입점. 상황별로 어느 문서를 봐야 할지 라우팅한다.

## 상황별 진입 문서

| 상황 | 시작 문서 | 추가 참조 |
|---|---|---|
| 신규 워크스페이스 setup | [`setup/README.md`](setup/README.md) | [`projects/example/`](projects/example/) (템플릿) |
| 프로젝트 생애주기 이해 (생성·재개·완료) | [`projects/GUIDE.md`](projects/GUIDE.md) | [`projects/example/project.md`](projects/example/project.md) |
| 이슈 모드 (단발성 처리) | [`issues/GUIDE.md`](issues/GUIDE.md) | [`issues/example/issue.md`](issues/example/issue.md) |
| `.agent-state.yml` 스키마·필드 의미 | [`state-schema.md`](state-schema.md) | — |
| 프로젝트 `agents/*.md` 구조 (분석본 vs 템플릿, `[analyze-managed]` 주석) | [`projects/agents-scaffold-notes.md`](projects/agents-scaffold-notes.md) | — |
| Drift 감지·`--regen-agents` 안전 절차 | [`drift-protocol.md`](drift-protocol.md) | `/pilot:doctor`, `/pilot:analyze --regen-agents` |
| Planner 가 작성하는 `.plan.md` 형식 계약 (모드별 필수 섹션·필드) | [`plan-schema.md`](plan-schema.md) | `tools/plan-validate.py` |

## 누가 어떤 문서를 보나

| 청중 | 필수 | 선택 |
|---|---|---|
| **워크스페이스 사용자** (`/pilot:project` 등 사용) | `setup/README.md` (1회) | `projects/GUIDE.md` (재개·문제 발생 시) |
| **플러그인 운영자** | 위 + `state-schema.md`, `agents-scaffold-notes.md`, `drift-protocol.md` | `issues/GUIDE.md` |
| **신규 진입자** | INDEX (본 문서) → `setup/README.md` | 필요 시 위 문서 cherry-pick |
| **에이전트 wrapper** | 직접 로드 — 본 INDEX 미참조 | — |

## 문서 성격

| 분류 | 파일 | 성격 |
|---|---|---|
| **운영 가이드** | `projects/GUIDE.md`, `issues/GUIDE.md`, `setup/README.md`, `drift-protocol.md` | 절차·결정 트리·트러블슈팅 |
| **계약 문서** | `state-schema.md`, `projects/agents-scaffold-notes.md`, `plan-schema.md` | 플러그인이 의존하는 형식·계약 정의 |
| **템플릿** | `projects/example/*`, `issues/example/issue.md` | 신규 프로젝트·이슈 생성 시 복사 기준 |

## 폴더 구조

```
lifecycle/
├── INDEX.md                              # 본 파일 (라우터)
├── drift-protocol.md                     # drift 감지·대응 절차
├── plan-schema.md                        # features/NN-{slug}.plan.md 형식 계약
├── state-schema.md                       # .agent-state.yml v1.2 스키마
├── projects/
│   ├── GUIDE.md                          # 프로젝트 생애주기 운영 가이드
│   ├── agents-scaffold-notes.md          # agents/*.md 구조 메타 노트
│   └── example/                          # 신규 프로젝트 템플릿
│       ├── project.md
│       └── agents/{planner,generator,evaluator}.md
├── issues/
│   ├── GUIDE.md                          # 이슈 모드 운영 가이드
│   └── example/issue.md
└── setup/
    └── README.md                         # 신규 워크스페이스 setup 절차
```

## 변경 시

본 INDEX 는 `lifecycle/` 의 파일 추가·삭제·이동 시 **수동 갱신** 한다. 자동 검증 (doctor) 미연동 — 폴더 구조 변경 빈도가 낮아 수동으로 충분.

신규 문서 추가 시 위 "상황별 진입 문서" 표에 행 추가 + "폴더 구조" 트리 갱신.
