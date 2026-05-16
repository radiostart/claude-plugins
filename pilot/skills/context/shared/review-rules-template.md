# 언어별 리뷰 규칙 — 작성 템플릿

이 파일은 **템플릿**이다. `workspace/context/review/{lang}.md` 로 복사해 언어별 리뷰 규칙을 채운다.
`{lang}` 은 `pilot-code-review` 가 파일 확장자로 감지하는 언어명(예: `ruby`, `kotlin`, `typescript`, `python`, `go`).

- 이 파일이 있는 언어 → 아래 규칙 + plugin baseline(`review-principles.md`) 적용.
- 없는 언어 → baseline 만 적용.

복사 후 아래 `---` 밑 내용만 `{lang}.md` 에 남기고 채운다.

---

<!-- 선택: lint 명령을 한 줄 선언하면 에이전트가 해당 언어 변경 파일에 1회 실행한다. 불필요하면 이 줄을 지운다. -->
lint: bundle exec rubocop

# {언어} 리뷰 규칙

## 관용구·패턴
<!-- 이 언어에서 권장/금지하는 관용구. 예: Ruby — guard clause 선호, 명시적 nil 체크 지양 -->

## 자주 나오는 결함
<!-- 체크리스트 형식 권장 -->
- [ ] 예: N+1 쿼리

## blocking 격상 기준 (선택)
<!-- baseline 외에 이 언어에서 blocking 으로 볼 항목 -->
