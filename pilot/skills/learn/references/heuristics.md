# 구조 결정 휴리스틱

`/pilot:learn` P4 단계 — 추출된 정보를 어떤 폴더 구조로 출력할지 결정하는 규칙.

원칙: **코드의 자연스러운 모양을 그대로 미러링한다.** 강제 템플릿(scope/rules 컨벤션) 을 만들려 하지 않는다. 코드가 단순하면 출력도 단순하게, 코드가 sub-domain 으로 나뉘어 있으면 그 분할을 따른다.

---

## 결정 표 (확장판)

| 코드 형태 | 추천 구조 | 예시 |
| --------- | --------- | ---- |
| 단일 파일 진입점 + 의존성 적음 (controller 1 + service 1 + model 1, 총 ≤ 200 줄) | `{domain}.md` 한 파일 | `/pilot:learn app/controllers/<domain>_controller.rb` → `workspace/context/<domain>.md` |
| 단일 도메인이지만 추출량 큼 (총 > 200 줄, 코드 구조는 평면) | `{domain}/` + 카테고리 | `/pilot:learn app/services/<domain>/` (`<domain>` 안에 controllers·services·models 파일이 모두 들어 있음) → `workspace/context/<domain>/` 안에 `routes.md` · `services.md` · `models.md` |
| 명확한 sub-domain 폴더 구조 | 코드 구조 미러 | `app/services/<domain>/{<sub_a>,<sub_b>,<sub_c>}/` → `workspace/context/<domain>/{<sub_a>,<sub_b>,<sub_c>}.md` |
| Routes/Models/Services 가 코드에서 명확 분리 | 카테고리 분할 | Rails 표준 — `config/routes.rb` + `app/models/<entity>.rb` + `app/services/<entity>_service.rb` → `{domain}/routes.md` · `models.md` · `services.md` |
| State machine 풍부 (enum 3 개 이상 또는 상태 전환 규칙 5 개 이상) | `enums/` 추가 | `workspace/context/{domain}/enums/<EntityStatus>.md` |
| Admin / API / 기타 표면이 같은 도메인 안에 공존 | 표면별 분할 | `controllers/admin/<entity>s_controller.rb` + `controllers/api/<entity>s_controller.rb` → `{domain}/admin.md` + `{domain}/api.md` |

---

## 파일 크기 정책

- **진입/index 파일** ≤ **100 줄** — 도메인 한 줄 요약 + 본문 파일 링크 + 핵심 모델·서비스 목록.
- **본문 파일** ≤ **200 줄** — 각 파일이 한 가지 관심사.
- **초과 시 분할 우선순위**:
  1. **sub-domain** 분할 — 코드에 sub-folder 가 있으면 그것을 따라 분할.
  2. **카테고리** 분할 — `services.md` 가 너무 크면 `services/{group}.md` 로 cluster.
  3. **알파벳/번호** 분할 — 마지막 수단. `services-a-m.md` + `services-n-z.md`.

분할은 **자연스러운 경계** 에서 한다. 특히 알파벳 분할은 보존성이 낮으므로 cluster 식별이 가능한 경우 그쪽을 우선.

---

## 진입 파일 결정

MANIFEST.md 의 `## 도메인 분류` 행에 들어갈 "진입 파일" 은 사용자·에이전트가 도메인을 처음 만났을 때 가장 먼저 읽을 파일이다.

| 출력 구조 | 진입 파일 |
| --------- | --------- |
| `{domain}.md` 단일 | `{domain}.md` 자체 |
| `{domain}/` 폴더 + `index.md` 존재 | `{domain}/index.md` |
| `{domain}/` 폴더 + index 없음 (드뭄) | 표 안에서 가장 핵심 본문 (`services.md` 우선) |

`index.md` 권장 — 폴더 구조면 거의 항상 만든다 (분할이 4 개 이상이면 필수).

---

## 예시 — 작은 코드베이스 (controller 1 + service 1 + model 1)

> 중형·대형 코드베이스는 결정 표의 해당 행을 그대로 적용한다 (별도 worked example 불필요 — 파일 크기 정책의 분할 우선순위가 초과분을 처리).

```
app/
  controllers/<domain>_controller.rb    (40 줄)
  services/<domain>_service.rb          (60 줄)
  models/<entity>.rb                    (20 줄)
```

→ 출력:

```
workspace/context/
  <domain>.md    (~120 줄, 단일 파일)
```

내용 구조 (단일 파일):

```markdown
# <domain> 도메인

## 개요
- 진입점: `app/controllers/<domain>_controller.rb`
- 핵심 기능: (도메인 한 줄 요약)

## Routes

> 선별 기재 — 쓰기·상태 변경, 경로로 알 수 없는 동작, 예외 경로·권한 차이만 싣는다.
> 이 표에 없다는 것은 라우트가 없다는 근거가 아니다.
> 전수 조회: {확인된 CLI 또는 정의 파일 경로} ({ISO 날짜} 기준 {N}건)

| Path | Method | Handler |
| ...

## Services
### <Domain>Service (`app/services/<domain>_service.rb`)
- ...

## Models
### <Entity> (`app/models/<entity>.rb`)
- 상태 enum: `<state_a>`·`<state_b>`·`<state_c>` (`app/models/<entity>.rb:8`)
```

---

## Edge Cases

### 모노레포 / 멀티 언어

진입점을 한 번에 여러 언어에 걸치게 주지 않는다. **언어별로 별도 호출**:

```
/pilot:learn backend/app/controllers/<entity>s_controller.rb --domain <domain>-api
/pilot:learn frontend/src/features/<domain>/ --domain <domain>-ui
```

도메인명에 surface 접미사 (`-api`·`-ui`·`-admin`) 를 붙여 충돌을 피한다.

### 진입점이 컨트롤러도 서비스도 아닌 경우 (예: 모델 진입)

`/pilot:learn app/models/<entity>.rb` — 모델 중심 진입은 의존성 추적이 역방향 (이 모델을 사용하는 controller·service 를 찾는다). Grep `<Entity>\.` · `<Entity>::` 로 역참조 수집 후 P2 분류 진행.

### 완전히 자연스러운 분할이 없을 때

코드가 평면적이고 (sub-folder 없음) 카테고리도 명확하지 않으면 (예: util 함수가 한 파일에 다 모임) — 단일 파일로 두고 본문 안에서 H2/H3 로 구분. 200 줄 초과 시에만 알파벳 분할.

### 기존 도메인이 이미 있을 때 (`{domain}.md` 존재)

세 가지 선택지 (SKILL.md P4 의 충돌 처리 참고):

- **overwrite** — 기존 분석이 outdated 일 때.
- **sub-domain 추가** — 기존 도메인의 일부를 정밀화하는 경우. 예: 기존 `<domain>.md` 가 있고 새로 `<sub_a>/` sub-folder 학습 → `<domain>/<sub_a>.md` 로 합병하면서 `<domain>.md` 를 `<domain>/index.md` 로 승격.
- **`{domain}-v2`** — 기존을 보존하면서 새 분석을 별도로 두고 싶을 때 (사용자가 직접 비교하고 통합).

---

## 안티 패턴

다음은 하지 않는다:

- **억지로 `scope/{domain}.md` 만들기** — 코드 구조와 맞지 않으면 컨벤션을 강제하지 않는다. MANIFEST.md 가 색인이라 자유 구조가 정상 동작한다.
- **카테고리 강제** — Rails 가 아닌데 `routes.md`·`models.md`·`services.md` 를 무리하게 만들지 않는다 (예: Go 의 `handler.go`·`store.go` 는 그대로 따른다).
- **추측으로 sub-domain 만들기** — 코드에 sub-folder 가 없는데 "이렇게 나누면 깔끔하겠다" 는 추측으로 분할하지 않는다. 평면 코드는 평면 출력.
- **인용 누락** — 추출된 모든 규칙·메서드는 소스 인용을 단다 (심볼 앵커 우선 — [extraction.md](extraction.md) § 소스 인용 규격). 인용 없는 본문은 추측 의심.
