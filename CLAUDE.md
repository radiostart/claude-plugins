# claude-plugins (pilot)

Claude Code 플러그인 **pilot** 의 개발·배포 저장소 (마켓플레이스 `radiostart-plugins`).

- `pilot/` — 플러그인 본체 (agents · skills · hooks · tools · tests · docs)
- `workspace/` — pilot 자신을 개발하는 dogfooding 워크스페이스 (`projects/build-plugin/`)
- `docs/` — 저장소 수준 감사·설계 이력 (완료된 plan 포함 — 실행 지시로 읽지 말 것)

## 정본 문서

- 매뉴얼 (사용법 SSOT): <https://radiostart.github.io/claude-plugins/>
- [pilot/README.md](pilot/README.md) — 플러그인 설치·부트스트랩·릴리스 절차
- [HANDOFF.md](HANDOFF.md) — 개발 인계: 환경 셋업, 확정된 설계 결정, 백로그

## 테스트

```bash
pytest pilot/tests/ -q
```

pytest 가 없으면: `python3 -m unittest discover -s pilot/tests/tools`
(외부 의존성 없음 — 표준 라이브러리만 사용.)
