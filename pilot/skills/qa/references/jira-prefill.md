# Jira fetch 결과 → qa/{KEY}.md prefill 규칙

신규 생성 절차 5-2 (fetch 출력 형식) 와 5-3 (템플릿 주입 규칙) 의 상세. fetch 명령·성공/실패 분기·회신 섹션 금지는 SKILL.md 본문이 SSOT.

## 5-2. `jira.py fetch` stdout 형식

`jira.py fetch` 의 stdout 은 다음 섹션을 포함한다:

- `# {KEY} — {summary}` 헤더
- `> status: ...` · `> reporter: ...` 메타
- `## 현상` — description (ADF → markdown)
- `## 재현 경로` — description 의 헤딩 또는 customfield 추출 결과
- `## 첨부 파일` — attachment 파일명 목록

## 5-3. 템플릿 주입 규칙

| 템플릿 토큰·섹션 | 채우는 값 |
| --- | --- |
| `{JIRA-KEY}` | 실제 KEY 로 치환 |
| `{요약}` | fetch 의 `summary` |
| `{URL}` | `${ATLASSIAN_BASE_URL}/browse/{KEY}` (또는 `${JIRA_BASE_URL}` — backcompat; env 부재 시 placeholder 유지) |
| `{YYYY-MM-DD}` (`reported`) | 오늘 날짜 (`date +%Y-%m-%d`) — Jira created 가 fetch 결과에 없으므로 진입일 기록 |
| `{QA 담당}` (`reporter`) | fetch 의 `reporter` displayName |
| `## 현상` 본문 | fetch 의 `## 현상` 섹션 본문 그대로 삽입 |
| `## 재현 경로` 본문 | fetch 의 `## 재현 경로` 섹션 본문. 본문이 placeholder (`_(본문에서 추출 불가 ...)_`) 면 템플릿의 placeholder (`_(Jira 본문에서 추출 또는 사용자 보강)_`) 유지 |
| `## 연관 feature` | 템플릿 placeholder 유지 (`_(연관 features — features/NN-*.md grep 결과 또는 사용자 명시)_`) |
| `## 원인` · `## 조치` · `## 회귀영향` | 템플릿 placeholder 유지 |

fetch 출력 중 다음은 폐기 (템플릿에 슬롯 없음):

- `> status:` 행
- `## 첨부 파일` 섹션

`> jira:` 와 `> reported:` 행은 SKILL.md 가 보강한다 (jira.py 출력에는 없음).
