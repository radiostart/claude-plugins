# 도메인 지식 환류 (knowledge-sync)

feature 사이클의 소스 변경이 `workspace/context/` 의 도메인 지식 문서에 반영할
**신규·변경 지식**을 만들었는지 판정하고, 사용자 승인 후 문서에 기록하는 절차.
[drift-protocol.md](drift-protocol.md) 가 "기존 문서가 코드와 다름 (우연 발견)"
을 다룬다면, 본 프로토콜은 "이번 변경이 만든 지식의 누락 (사이클 종료 시 체계
점검)" 을 다룬다.

---

## 판정 (evaluator — 감지·보고만)

evaluator 가 사이클 검토 완료 후 이번 변경 diff 를 기준으로 판정한다.
**evaluator 는 context/ 파일을 직접 Edit 하지 않는다** — 기록 주체는 사용자
승인을 받은 메인 대화다 (drift-protocol 공통 원칙 1 · 3 과 동일 — 즉시 Edit
금지, 승인 후에만 Edit).

### detected — 다음 중 1개 이상이 diff 에 존재

[`learn`](../../learn/SKILL.md) Phase 3 의 추출 항목 (public interface·라우트·
의존성·state enum·business rule) 을 기반으로 하되, 6 은 본 프로토콜 고유
항목이다:

1. 라우트/엔드포인트 추가·제거·시그니처 변경 (아래 **라우트 선별** 단서)
2. 도메인 모델·테이블·컬럼 추가/변경
3. enum·상태값·도메인 상수 추가/변경/제거
4. 외부 의존 (API·MQ·DB·타 도메인 호출) 추가/제거 — cross-domain 은
   `boundaries/{A}--{B}.md` 대상
5. 비즈니스 용어·개념 신설
6. context 문서에 **이미 기록된** 항목의 동작 변경 (라우트는 아래 **라우트 선별**)

**라우트 선별 (1 · 6 단서).** 도메인 문서에 Routes 표가 있으면 그 표는 전수
목록이 아니라 선별 기재다 ([learn extraction](../../learn/references/extraction.md)
§ Routes 표). 그래서 라우트는 "diff 에 있는가" 가 아니라 **"표에 실릴 것인가"**
로 판정한다 — 아니면 사이클마다 선별로 뺀 행이 되붙어 표가 도로 전수화된다.

- **추가** — 선별 기준 (①~⑤) 통과분만 detected. 목적이 경로·핸들러명 재진술에
  그치는 라우트 신설은 none 이다 (규격이 빼라고 한 행을 여기서 되돌리지 않는다).
- **제거** — 표에 기재된 행이 대상일 때만 detected (미기재 라우트는 지울 행이
  없다).
- **동작 변경** — 6 의 "이미 기록된" 은 라우트에 한해 완화한다. 미기재 라우트라도
  이번 변경으로 선별 기준을 **새로 충족하게 되면** (암묵 필터·권한 분기·경로와
  어긋나는 실제 동작이 생김) detected — 표 크기가 감지 범위를 좁히지 않는다.

### none — 노이즈 가드

내부 리팩터 (공개 표면 불변)·버그 수정 (문서 기록 단위의 동작 불변)·테스트만
변경·스타일/주석. 판단 휴리스틱: **"이 변경을 모르는 다음 planner 가 잘못된
계획을 세울 수 있는가"** — 아니면 none.

### skip

`.agent-state.yml` 의 `domain: null` (판정 기준 도메인 없음). 도메인 진입 문서
부재는 skip 이 아니라 detected — evidence 에 "context 문서 없음 —
`/pilot:learn` 신규 작성 권장" 을 적는다.

## REPORT 표기

VERIFICATION REPORT `metrics` 블록에 기록한다 (**gate 아님** — status 판정
비영향, READY 와 detected 공존이 정상):

```
- metrics:
  - coverage: ...
  - domain_impact: none | detected | skip — {유형}: {요약} → {대상 문서} (항목별 `;` 구분)
```

evidence 예: `enum: 발송상태 CANCELED 추가 → retail.md; 외부 의존: 재고 API 호출 신설 → boundaries/retail--inventory.md` (경로는 `workspace/context/` 기준 상대 표기)

`none` 은 evidence 생략 가능 (노이즈 가드 근거 1줄 선택). `skip` 은 `— domain: null` 을 명시한다.

**감지·REPORT 기록은 status 무관** — `NOT_READY` 라도 `domain_impact` 는 그대로
기록한다. 단 사용자에게 던지는 **질의** (안내 블록) 는 `status: READY`
**한정**이다. `NOT_READY` 는 변경 미확정 — generator 재작업으로 판정이
무효화될 수 있어 질의를 다음 READY 재평가로 미룬다.

## 질의·기록 절차

### 수동 사이클

1. evaluator 는 `status: READY` + `detected` 시 chat 응답 말미 (REPORT 직후) 에 안내 블록을 출력한다:

   ```
   ## 도메인 지식 환류 제안
   이번 변경이 도메인 지식 문서에 반영할 항목을 만들었습니다:
   | # | 유형 | 내용 | 대상 문서 |
   |---|---|---|---|
   | 1 | {유형} | {요약} | {경로} |
   기록할까요? 승인 시 항목별 before/after 미리 보기 후 반영합니다.
   (절차: ${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/knowledge-sync.md § 기록)
   ```

2. 사용자 승인 시 **메인 대화**가 아래 § 기록 을 수행한다. 거부 시 기록하지
   않고 종료 — 미기록 지식은 이후 사이클에서 drift 로 발견될 수 있다 (의도된
   안전망).

3. `NOT_READY` + `detected` 면 안내 블록을 띄우지 않는다 — REPORT
   `metrics.domain_impact` 에 기록만 하고, 재작업 후 `READY` 가 되는 재평가에서
   1·2 를 수행한다.

### /pilot:autopilot

단일 feature 자동 진행이라 누적·일괄 질의가 없다. evaluator READY
(`kind=done`) 로 끝나면 메인 대화가 완료 보고에 evaluator 의 안내 블록을 그대로
포함시킨다 — 이후 절차는 수동 사이클과 동일 (autopilot 은 질의 없이 기록하지
않는다 — [`interview.md`](../shared/interview.md) 의 "질의는 메인 대화에서만"
과 같은 원칙). STOP (NOT_READY 계열) 으로 끝나면 질의가 발생하지 않으며, 재개
후 READY 재평가에서 질의한다. 안내 블록을 미처리한 채 세션을 닫았어도 판정은
diff 기준이라 소실되지 않는다 — 다음 READY 재평가 또는 재검토에서 재감지할 수
있고, `metrics.domain_impact` 가 남은 REPORT 가 있으면 그것으로 복원한다.

## 기록

수행 주체: 사용자 승인을 받은 메인 대화.

1. 항목별 대상 문서의 before/after 를 제시하고 최종 승인을 받는다
   (drift-protocol 공통 원칙 2 와 동일 형식).
2. Edit 으로 반영. 대상은 MANIFEST 가 가리키는 도메인 진입 파일·하위 파일이다
   (구조 자유 — learn § 제약). 파일 크기 정책 (진입/index ≤100줄·본문 ≤200줄)
   은 [`learn`](../../learn/SKILL.md) § Phase 4, MANIFEST 갱신 (기존 정의
   우선·`## 도메인 분류` H2 정확 매칭) 은 learn § Phase 5 를 따른다. 기록
   문안에 feature ID (`F9`)·티켓 키 등 프로젝트 생애주기 토큰을 남기지 않는다
   — 이번 feature 로 발견한 사실이라도 도메인 표현으로 쓴다 (공유 context 는
   프로젝트-무관).
   - **Routes 표에 행을 더할 때**는 표 위 **고지 3 줄**
     ([learn extraction](../../learn/references/extraction.md) § Routes 표 고지
     의무) 이 같이 있는지 확인하고, 없으면 이때 넣는다 — 고지 없는 선별 표는
     다음 사용자에게 전수 목록으로 읽힌다.
   - **환류 문안도 L1·L2 까지다** (extraction § 기재 층위). 이번 변경으로 알게
     된 계산식·조건 분기 순서·반환 키 전수는 도메인 문서에 적지 않고 심볼
     앵커로 위치만 남긴다 — 환류는 learn 과 같은 기재 규격을 쓴다 (사람이
     문안을 쓰는 경로라 미리보기 가드가 없으므로 여기서 한 번 더 확인한다).
3. **항목 5건 이상 또는 섹션 구조 개편**이면 개별 Edit 대신
   `/pilot:learn {진입점} --force` 재실행을 권장한다 (learn 산출 문서는 diff
   모드 없는 덮어쓰기 갱신이라 재실행이 더 안전. 사용자 커스텀 layer 인
   `scope/`·`rules/` 는 learn 이 건드리지 않아 그대로 보존된다).
4. `rules/{domain}.md` 등 사용자 커스텀 layer 는 환류 대상이 아니다 — 정책은
   코드에서 추론 불가. 구현과 rules 의 상충 발견은
   [drift-protocol § A](drift-protocol.md) 경로.
5. **기본 브랜치 조기 합류.** `workspace/context/` 는 git tracked 공유 자산이다
   ([workspace-layout](../../../docs/explanation/workspace-layout.md) § 영구
   파일 vs 일시 파일). 기록 커밋을 feature 브랜치에 남겨두면 다른 브랜치·
   체크아웃에서 그 도메인 지식이 보이지 않는다. context/ 변경 커밋은 feature
   머지를 기다리지 말고 기본 브랜치에 조기 합류시킨다 (cherry-pick 또는
   context 단독 커밋 분리).

## 경계

| 축 | drift (drift-protocol) | domain_impact (본 문서) |
| --- | --- | --- |
| 무엇 | 기존 문서가 실제와 다름 | 이번 변경이 만든 신규·변경 지식의 미반영 |
| 발견 | 사이클 중 우연 (읽다가) | 사이클 종료 시 체계 점검 (diff 기준) |
| REPORT | `gates.drift` (READY 와 모순) | `metrics.domain_impact` (READY 와 공존) |

`project.md` 의 "에이전트 간 전달사항" (evaluator step 6) 은 **프로젝트 내부**
feature 간 전달용 — 공유 도메인 지식과 별개 축이다.
