# #11 feature spec Open Questions 템플릿

> source: V1-Full Step D 시나리오 C 제안 B — feature spec 작성 시 산출물에서 답할 수 없는 영역을 명시적으로 분류해 추측 회피

## 요구사항

- **조건**: V1 시나리오 C 결과, 산출물만으로 spec 작성 시 막히는 영역이 4 카테고리로 분류 가능. 현재 features 명세 템플릿 (`features/00~05`) 에는 명시적 "Open Questions" 섹션 부재 → 작성자가 막힌 부분을 임의 추측으로 메우는 회귀 위험.
- **트리거**: `/pilot:create-feature` 또는 `/pilot:analyze` 5-2 단계의 features/ 산출.
- **기대결과**: 모든 신규 features/NN-{slug}.md 가 "Open Questions" 섹션 강제. 산출물에 부재한 영역을 4 카테고리로 분류 명시.

## 비즈니스 규칙

- **4 카테고리 강제** (V1 시나리오 C 결과 기반):
  - **(a) 같은 도메인 안 추가 read 필요**: 산출물이 메서드 시그니처는 캡처했지만 line-by-line detail 부족 (예: cancel_after_completion 71-91 정확한 step). 해결 = 추가 `/pilot:learn {domain}` 정밀 호출 또는 코드 직접 read.
  - **(b) cross-domain 산출물 부재**: 다른 도메인 학습 안 됨. 해결 = `/pilot:learn {외부 도메인}` 후속 호출 (MANIFEST 의 "외부 도메인 reference" 섹션 참조 — `#10` 과 짝).
  - **(c) 외부 시스템 spec 부재**: 코드 외부 (예: PG API spec, DHL API spec, 사내 다른 서비스 API). 해결 = pilot 책임 외 — 사용자가 별도 spec 확보.
  - **(d) 비즈니스 결정 영역**: 도메인 PO 결정 영역 (예: 박스 손상 보고가 일반 보류와 다른 워크플로 가져야 하는지). 해결 = PM/PO 와 협의.
- **템플릿 형식**:
  ```markdown
  ## Open Questions

  ### (a) 같은 도메인 추가 read 필요
  - [ ] {질문}: {산출물 부족한 영역} → {추가 read 위치}
  
  ### (b) cross-domain 산출물 부재
  - [ ] {질문}: {외부 도메인} 산출물 부재 → `/pilot:learn {외부 도메인}` 권장
  
  ### (c) 외부 시스템 spec 부재
  - [ ] {질문}: {외부 시스템} spec 별도 확보 필요
  
  ### (d) 비즈니스 결정 영역
  - [ ] {질문}: PM/PO 협의 필요
  ```
- **빈 카테고리 처리**: 한 카테고리에 질문이 없으면 카테고리 헤더 + "(없음)" 표시. 카테고리 자체 생략 안 함 — 작성자가 "정말 없는지" 의식적 확인하도록 강제.
- **`/pilot:create-feature` 의 자동 detect**: 산출물 lookup 시 답할 수 없는 영역 발견 → Open Questions 의 적절한 카테고리에 자동 추가. 사용자가 spec review 시 추가/수정 가능.
- **A2 runtime fallback**: detect 알고리즘 실패 시 → Open Questions 섹션 4 카테고리 헤더 + "(작성자 직접 채움)" placeholder 만 자동 작성. abort 안 함.
- **doctor 검증**: features/NN-*.md 파일에 Open Questions 섹션 부재 → INFO 1 줄 (`[INFO] features/{path} 에 Open Questions 섹션 부재 — 추측 회피 위해 권장`).

## 예외 케이스

- **모든 카테고리 비어있음** (산출물 100% cover): 4 카테고리 모두 "(없음)" 표시. 정상 — 단순 feature 시나리오.
- **다단계 cross-domain (A → B → C)**: 카테고리 (b) 에 첫 단계 (B) 만 명시. 후속 learn 후 다시 detect → C 추가.
- **사용자가 직접 작성한 features/ 파일**: 자동 detect 안 함. 사용자가 수동 작성. doctor 가 INFO 만.
- **`/pilot:analyze` 의 5-2 결과**: 5-2 가 features/ 갱신 시 기존 Open Questions 섹션 보존. 자동 detect 결과는 신규 카테고리 (a)~(d) 행으로 추가.

## 관련 파일 범위

- **변경**: `pilot/skills/create-feature/SKILL.md`
  - feature spec 산출 단계에 "Open Questions 섹션 작성" 단계 추가
  - 자동 detect 알고리즘 명시 (산출물 lookup 실패 영역 → 카테고리 분류)
- **변경**: `pilot/skills/analyze/SKILL.md`
  - 5-2 단계의 features/ 갱신 절차에 Open Questions 섹션 보존 + 자동 추가
- **변경**: `pilot/skills/context/lifecycle/projects/example/features/{template}.md` (만약 있으면)
  - 신규 4 카테고리 섹션 포함된 template
- **변경**: `pilot/tools/doctor/integrity.py`
  - features/NN-*.md 의 Open Questions 섹션 부재 시 INFO 1 줄
- **단위 테스트**: `pilot/tests/tools/test_doctor_open_questions.py` — Open Questions 섹션 detect 케이스
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/expected/features/` 에 Open Questions 섹션 포함된 sample
- **사용자 영향**: 사용자가 spec 의 막힌 영역을 의식적 분류 → 추측 임시 메우기 회피 → 후속 작업 (cross-domain learn / PM 협의 등) 우선순위 명료.
