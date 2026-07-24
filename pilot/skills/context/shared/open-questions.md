# Open Questions 4 카테고리

`/pilot:analyze` 와 `/pilot:create-feature` 가 공유하는 Open Questions 작성 규칙과 분류 기준. features/NN-*.md 작성 시 `## Open Questions` 섹션의 SSOT.

> **소비 규칙(조건부 인터뷰)** 은 [`interview.md`](interview.md) 가 SSOT — unchecked (`- [ ] `) 행이 여기 작성 규칙대로 만들어지므로, 본 문서의 행 형식을 바꾸면 `interview.md` 의 행 파싱 규칙도 함께 동기화해야 한다.

---

## 작성 규칙

- 4 카테고리 헤더는 항상 모두 포함한다. 카테고리 자체를 생략하지 않는다.
- 한 카테고리에 질문이 없으면 `- (없음)` 으로 표시 (작성자가 "정말 없는지" 의식적 확인 강제).
- 산출물 lookup 시 답할 수 없는 영역이 발견되면 아래 분류 기준에 따라 해당 카테고리에 `- [ ] {질문}: ...` 행 추가.
- A2 runtime fallback: detect 알고리즘 실패 시 → 4 카테고리 헤더 + `- (없음)` placeholder 만 작성. abort 안 함.

---

## 템플릿

```markdown
## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음)
```

---

## 카테고리 분류 기준

- **(a) 같은 도메인 추가 read 필요**: scope/{domain}.md 에서 메서드 시그니처는 캡처됐지만 line-by-line detail 부족한 경우.
- **(b) cross-domain 산출물 부재**: MANIFEST `## 외부 도메인 reference` 표에 매칭되는 미학습 도메인.
- **(c) 외부 시스템 spec 부재**: 코드 외부 시스템 (외부 API, 사내 다른 서비스 등).
- **(d) 비즈니스 결정 영역**: PM/PO 결정 영역 (코드로 결정할 수 없는 비즈니스 판단).

---

## cross-domain 의존성 detect 시 분류 매핑

1. `workspace/context/MANIFEST.md` 를 Read.
2. 사용자 프롬프트 및 작성된 feature spec 에 등장하는 클래스/도메인 키워드를 추출.
3. 키워드를 MANIFEST 의 `## 도메인 분류` 표와 `## 외부 도메인 reference` 표 양쪽에서 lookup:
   - `## 외부 도메인 reference` 표에 매칭되는 도메인이 있으면:
     - `### (b) cross-domain 산출물 부재` 에 `- [ ] {외부 도메인} 산출물 부재 → \`/pilot:learn {추천 경로}\` 권장` 행 추가.
     - INFO 1 줄: `[INFO] {외부 도메인} 의존성 감지 — 먼저 \`/pilot:learn {추천 경로}\` 권장`.
   - 매칭 없음이지만 산출물로 cover 되지 않는 영역 (외부 시스템 API 등) 이 있으면 `### (c) 외부 시스템 spec 부재` 에 `- [ ] {외부 시스템} spec 별도 확보 필요` 행 추가.

> **A2 runtime fallback**: MANIFEST lookup 실패 또는 키워드 추출 실패 시 → spec 진행 (abort 안 함). Open Questions 에는 4 카테고리 헤더 + `- (없음)` placeholder 만 기입. INFO 출력 안 함.
