# claude-plugins (pilot)

사내 `dp-skills` 플러그인을 범용 **pilot** 플러그인으로 리팩토링하는 저장소.

- `pilot/` — 플러그인 본체 (agents · skills · hooks · tools · tests · docs)
- `workspace/` — pilot 자신을 개발하는 dogfooding 워크스페이스 (`projects/build-plugin/`)
- `docs/` — 저장소 수준 감사·설계 문서

## 정본 문서

- [HANDOFF.md](HANDOFF.md) — 인수인계: 환경 셋업, 현재 상태, 완료 이력
- [pilot/README.md](pilot/README.md) — 플러그인 설치·부트스트랩
- 매뉴얼 (SSOT): <https://radiostart.github.io/claude-plugins/>

## 테스트

```bash
pytest pilot/tests/ -q --ignore=pilot/tests/tools/test_confluence.py
```

pytest 가 없으면: `for f in pilot/tests/tools/test_*.py; do python3 "$f" || break; done`
(`test_confluence.py` 는 `requests`·`beautifulsoup4` 의존 — HANDOFF.md 셋업 참고.)
