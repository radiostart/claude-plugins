# context-search fixture

## 목적

`tools/context-search.py` 랭커의 골든 `hit@3` 단위 테스트(`test_context_search.py`
의 `GoldenHitAtThree`)가 소비하는 고정 스냅샷. 라이브 `workspace/context/` 가
`/pilot:learn` 재학습으로 바뀌어도 이 fixture 는 불변이라 단위 테스트가
hermetic 하게 유지된다(D2).

## 스냅샷 정보

- 일자: 2026-09-04
- 출처: `workspace/context/MANIFEST.md` + `workspace/context/pilot/*.md` (7 파일)
- 생성 명령:
  ```bash
  mkdir -p pilot/tests/fixtures/context-search/workspace/context/pilot
  cp workspace/context/MANIFEST.md pilot/tests/fixtures/context-search/workspace/context/
  cp workspace/context/pilot/*.md pilot/tests/fixtures/context-search/workspace/context/pilot/
  ```

## 갱신 규칙

갱신은 선택 사항이다. 갱신할 경우:

1. 위 생성 명령을 그대로 재실행해 스냅샷을 덮어쓴다.
2. `python3 pilot/tools/context-search.py "<질의>" --scope pilot --format json --workspace pilot/tests/fixtures/context-search/workspace` 로 골든 4질의(`test_context_search.py` 의 `GoldenHitAtThree`) `hit@3` 를 재확인한다.
3. 미달 시 랭커를 임의로 조정하지 않는다 — 실측 표를 해당 feature 의 plan.md 에 기록하고 보고한다.

`#22` 재학습 드리프트(예: 스크립트 삭제 서술 등)가 라이브 코퍼스에 남아 있어도
이 fixture 의 랭킹 테스트에는 무관하다 — 섹션 구조·헤딩·경로만 랭킹에 영향을 준다.
