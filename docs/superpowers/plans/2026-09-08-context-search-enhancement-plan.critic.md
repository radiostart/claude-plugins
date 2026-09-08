# Plan Critic — context-search 고도화 플랜 (2026-09-08) · 적용 커밋 `770cc3e`·`7aaff08`·`b2dfe7b`·`cf5f8b8`·`f2dbdb5`

> 입력 plan: `docs/superpowers/plans/2026-09-08-context-search-enhancement-plan.md` (검토 시각 2026-09-08T08:20:19Z)
> 입력 적용분: `git diff 37ab524..HEAD` — `pilot/tools/context-search.py` (+679/−125) · `pilot/tests/tools/test_context_search.py` · `wrapper-protocol.md` §6 · `ask/SKILL.md` 절차 2 · `orchestrate-load.py:527` · `release-notes.md` 미배포 절
> 페르소나: `personas.planner-critic` (red-team)
> 검증 방법: 기준 커밋 `37ab524` 를 `git worktree` 로 꺼내 head 와 같은 명령을 나란히 실행·`cmp`(fixture 8질의 · 라이브 5질의 · md/json) · `python3 -m unittest discover -s pilot/tests/tools`(base 603 · head 666 통과, Python 3.11.15) · 프로토콜 §6 3단계 명령을 `bash -c` 로 **그대로** 실행 · `score_text`/`parse_frontmatter`/`_source_glob_match`/`_apply_inject`/confluence `search_docs` 직접 호출 프로브 · 1,000섹션 합성 한글 코퍼스 타이밍(중앙값 3회) + cProfile · `docs_build.py --check`(통과) · `doctor.py workspace`(head 4 PASS·3 WARN·1 ERROR = 플랜 §4 G5 기록과 일치, base 5 PASS·0 WARN·1 ERROR). 프로브는 scratch 전용(산출물 아님).
> 실측으로 재현돼 반증하지 못한 플랜 주장(챌린지 아님): §2 A2 표의 base 수치 4건(15·4·0·0) · Q4 14점 1위 · Q5 base 1위 `lifecycle.md /pilot:project` 6점 → head `index.md Cluster 진입` 7점 1위 · Q6 18→20 · 코퍼스 frontmatter 0건 · G1 603→666(context-search 87→150) · Q1~Q4·`select:` md/json 바이트 동일 · 라이브 mtime 전부 6d · 결정성(같은 질의 2회 diff 0).

## 챌린지

### C1 — 프로토콜 3단계 명령이 코퍼스 헤딩의 백틱을 쉘에 넘긴다 → 무음으로 파일 전체가 주입된다
- **severity**: blocking
- **category**: protocol
- **plan 인용**: §3.5 초안 `:211` 「3. 주입: python3 …/context-search.py "select:{file}#{heading},{file}#{heading}" --inject」 · 적용본 `pilot/skills/context/shared/wrapper-protocol.md:42` 「`file` 은 manifest 에 표시된 경로 그대로」 · `pilot/skills/ask/SKILL.md:46` · §4 E8 보강 `:268` 「에이전트가 manifest 줄의 경로를 그대로 붙여 넣을 수 있어야 3단계 흐름이 실제로 돈다」
- **챌린지**: 라이브 코퍼스 H2/H3 33개 중 **21개**, fixture 21개 중 **17개**가 `` ## `/pilot:pilot-doctor` `` 처럼 백틱으로 감싼 헤딩이다(`/pilot:x` 계열 전부 — 이 도구의 주 사용처). 프로토콜은 인자를 큰따옴표로 감싸고 헤딩을 "그대로" 붙이라고 하는데, 큰따옴표 안의 백틱은 bash 명령 치환이다. 실측 `bash -c 'python3 pilot/tools/context-search.py "select:workspace/context/pilot/lifecycle.md#`/pilot:pilot-doctor`" --format manifest'` → stderr `bash: line 1: /pilot:pilot-doctor: No such file or directory`, 헤딩이 빈 문자열로 넘어가 도구는 `select:pilot/lifecycle.md` 로 해석 → 「후보 6건 중 6건 표시」. `--inject` 면 원했던 1섹션(4,962B) 대신 파일 6섹션이 12,000B 예산까지 주입된다. INFO 는 0건 — 도구 쪽도 `select:file#`(빈 헤딩) 을 헤딩 생략과 같게 무음 처리한다(`parse_query` `:206` `heading_part.strip() or None`; 실측 `select:pilot/lifecycle.md#` → `returned 6, info []`). `$` 가 든 헤딩도 같은 경로로 지워진다(`#$ARGUMENTS 처리` → `#처리` → 0건). 작은따옴표·이스케이프면 정상(실측 1건 반환)이지만 어느 지시 문서에도 그 규칙이 없다. 실패가 "틀린 섹션" 이 아니라 "너무 많은 섹션" 으로 나타나므로 에이전트는 성공으로 믿고 진행한다 — 3단계 흐름의 핵심 명령이 코퍼스의 다수 헤딩에서 설계 목적(1~3개 주입)을 스스로 무너뜨린다.
- **제안**: (a) wrapper-protocol §6·ask 절차 2·orchestrate-load 힌트의 예시를 작은따옴표로 바꾸고 「헤딩은 백틱·`$`·`"` 를 뺀 안쪽 텍스트만 쓴다 — 부분 문자열 매칭이라 충분」 1줄 추가. (b) 도구: `_select_result` `:1129` 의 대조에서 양쪽 헤딩의 백틱·`*`·`_` 를 벗겨 비교하고, 원문에 `#` 가 있는데 헤딩이 비면 INFO 「헤딩이 비어 파일 전체 반환 — 쉘 인용 확인」 을 낸다(무음 전체 주입 차단). (c) 선택지로 manifest 줄에 백틱 제거 `select 키` 를 노출하거나 `[#n]` 번호 재지정(`--pick 1,5`, 결정적 순서라 가능)을 검토. (d) 테스트: `select:a.md#` 가 INFO 를 내는 케이스 + 백틱 헤딩 fixture(`lifecycle.md`)로 `#/pilot:doctor` 매칭.

### C2 — `[rules]`·`[boundary]` 예외 규칙은 현재 코퍼스에서 발동 불가이고 rules 는 구조적으로 영구 불가 · 「필수어가 맞으면」 미정의
- **severity**: suggestion
- **category**: protocol
- **plan 인용**: §2 B `:103` 「`rules`·`boundary` 유형은 필수어가 맞으면 버리지 않는 예외가 필요하다. 이 판단에 A1 의 `type` 출력 필드가 쓰인다」 · §2 A1 `:32-33` 「코퍼스 전체 frontmatter 0건 … `rules/{domain}.md` 는 사용자 커스텀 layer 라 frontmatter 강제 대상이 아니다」 · `wrapper-protocol.md:39` · `ask/SKILL.md:46` 「`[rules]`·`[boundary]` 는 질문의 핵심어가 맞으면 유지」
- **챌린지**: 규칙의 키는 manifest 의 `[type]` 태그이고 태그는 frontmatter `type` 이 있을 때만 붙는다(`render_manifest` `:1347`, `_result_entry` `:1082`). 실측: 라이브 8파일·fixture 7파일 모두 frontmatter 0 → 지금은 어떤 후보에도 태그가 없어 규칙이 한 번도 발동하지 않는다. #29 머지 후에도 `rules/{domain}.md` 는 「사용자 커스텀 layer — 이 스킬은 직접 생성하지 않는다」(`pilot/skills/learn/SKILL.md:103`, `29-frontmatter-manifest.md:39`)라 생성기가 `type: rules` 를 쓸 일이 없다 — 플랜 §2 A1 이 스스로 적은 사실이다. 즉 G3(규칙 누락 → 평가 반려) 방지용 예외가 rules 파일에는 영구히 닿지 않고, boundary 도 #29 이후에야 닿는다. 또 「필수어가 맞으면」 의 필수어가 `+필수어` 라면 사전필터를 통과한 후보는 전부 맞으므로 판별력이 0 이고, `+` 를 안 썼으면 정의가 없다. ask 는 같은 규칙을 「질문의 핵심어」 로 다르게 쓴다.
- **제안**: 규칙의 키를 경로로 바꾼다 — 「`rules/`·`boundaries/` 경로 또는 `[rules]`·`[boundary]` 태그」. 도구는 frontmatter 부재 시 `sec.file` 이 `boundaries/`·`rules/` 로 시작하면 `[boundary?]`·`[rules?]` 추정 표기(`_result_entry` 4줄). 「필수어」 는 두 문서 동일 문구로 — 「질의의 핵심 토큰이 `matched` 에 있으면」.

### C3 — 「기존 플래그만 쓰면 바이트 동일」 은 Q1~Q4·`select:` 에 한정된 사실 — G2 와 G4 가 서로 모순, confluence 「무변경」 도 거동 기준으로는 거짓
- **severity**: suggestion
- **category**: doc-drift
- **plan 인용**: §4 G4 `:261` 「신규 플래그 미사용 시 fixture 6질의 · 라이브 3질의(`select:` 포함) md/json 바이트 동일」 · §4 G2 `:259` 「Q6 … 18 → 20점」 · `release-notes.md:50` 「기존 플래그만 쓰면 md/json 출력 바이트 동일 (골든 6질의·라이브 3질의 대조) · `score_text` 시그니처 호환으로 confluence 검색 무변경」 · §3.3 스텝 13 `:177` 「confluence 무변경」
- **챌린지**: 기준 worktree 와 `cmp` 실측(fixture `--scope pilot`, md·json 각각): Q1~Q4·`select:` 동일, **Q5·Q6 상이**(Q6 1위 18→20 + `matched` 에 `정합성검사` 추가, 5위 행이 `index.md 매트릭스 2점` → `lifecycle.md 서문 4점` 으로 교체), 0건 한글 질의(`없는단어입니다 zzqq`)도 guidance 1줄(「붙여쓰기·띄어쓰기 양쪽 자동 대조…」)이 추가돼 상이. 라이브도 `도메인 진입파일 자동 로드`·`도메인을 진입파일로 자동로드`·`정합성검사 상태파일` 가 0건 → 3~5건으로 바뀐다. 같은 표에서 G2 가 Q6 점수 변화를 적고 G4 가 「6질의 동일」 을 적은 것은 자기모순이다. confluence 는 코드는 무변경이지만 `parse_query`→`score_text` 를 공유하므로 거동이 바뀐다 — `search_docs` 실측: 질의 `진입파일` base 0건 → head 2건(`# 진입`·`## 로드 순서`).
- **제안**: G4·release-notes 를 「한글 4자+ 토큰·인접 한글쌍이 없는 질의(Q1~Q4·`select:`·ASCII)에 한해 바이트 동일; 그 외 한글 질의는 E2~E5 로 점수·0건 안내가 바뀐다」 로 정정. 「confluence 무변경」 → 「confluence 코드 무변경 — 한글 결합·역방향 규칙은 `/pilot:confl search` 에도 적용된다」 로 사용자 영향으로 기록.

### C4 — `--include` 로 찾은 후보는 `select:` 로 되짚을 수 없다 — 3단계 흐름이 부속 문서에서 끊긴다
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: `wrapper-protocol.md:37` 「`--include features/ docs/` 부속 문서」(1단계) · `:42` 「`file` 은 manifest 에 표시된 경로 그대로」(3단계) · docstring `:21-23` 「md·manifest 에 표시된 경로(CWD 기준)를 그대로 붙여 넣어도 된다」 · §4 E8 보강 `:268`
- **챌린지**: include 파일의 `Section.file` 은 루트(`workspace/context`) 기준 상대경로라 `../projects/build-plugin/features/27-….md` 형태다. 실측: manifest 표시 경로 `select:workspace/projects/build-plugin/features/27-context-search-tool.md#요구사항 --include features/ --project build-plugin` → 0건(후보로 `../projects/...` 3개 제시), 그 후보 그대로 `select:../projects/...` → 「select: 대상에 절대경로·'..' 사용 불가」 exit 2. 어느 형태로도 도달 불가. 기준 커밋도 같지만 그때의 §6 은 read_hint Read 만 지시했으므로 문제가 없었고, 3단계 프로토콜이 「select 로 주입」 으로 바꾸면서 결함이 됐다.
- **제안**: `_normalize_select_path` `:1088` 가 `_display_path(workspace)` 접두도 인식해 `../…` 로 정규화하고, traversal 판정을 「정규화 결과가 `root` 또는 `workspace` 안」 으로 바꾼다(`collect_files` 봉쇄 검증과 같은 기준 — `sections` 는 이미 수집된 것만 대조하므로 새 파일 접근은 없다). 그때까지 프로토콜 3단계에 「include 후보는 read_hint 로 Read」 예외 1줄. 테스트: include 파일 select 왕복.

### C5 — inject dedupe 가 앞→뒤 한 방향뿐 — 키워드+`--inject` 에서 흔한 「H3 가 H2 보다 먼저」 는 그대로 중복 주입
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: §2 A5 `:93` 「부모·자식을 함께 고르면 본문이 중복 주입된다. 라인 범위 포함 관계로 dedupe 해야 한다」 · §4 E9 세부 `:269` 「포함 관계 dedupe 는 **앞선** 결과의 주입 범위가 뒤 섹션 전체를 덮을 때만 적용」 · `_apply_inject` `:1214`
- **챌린지**: H3 헤딩이 질의와 정확 일치하면 H3(+10)가 H2(본문 +2)보다 앞선다 — 키워드 질의에서는 이 순서가 기본이다. 실측(합성 `## Parent zeta / ### Child alpha`): `alpha child` + inject → Child 22점 1위·Parent 4점 2위, 두 `text` 에 `child body` 2회. `select:a.md#Child,a.md#Parent` 도 2회. `test_child_h3_skipped_when_parent_h2_injected_first` `:864` 는 파일 순서(부모 먼저)만 검증한다. 문서(「앞선 결과가 덮는 하위 섹션은 생략」)는 정확하지만 실제 빈도가 높은 쪽이 예외로 남았다.
- **제안**: `_apply_inject` 를 2패스로 — 선택 섹션의 라인 범위를 먼저 모아 포함 관계를 정하고, 뒤에 오는 부모가 이미 주입된 자식을 덮으면 부모 텍스트에서 자식 범위를 `[… L{s}-{e} 는 [#k] 에 주입됨]` 1줄로 접는다(순서 유지·예산 절약). 테스트 2건(키워드 순서·select 역순).

### C6 — 한글 4자+ 질의의 실행 시간이 spec 300ms 를 넘는다 — G3 성능 게이트는 ASCII 질의만 잰다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: G3 `:221`·`:260` 「1,000섹션 성능 테스트 < 1s」 · E4 `:131` 「`compact`(한글 사이 공백 제거) 본문·헤딩에서 좌측 경계 검색」 · `27-context-search-tool.md:43` 「섹션 1,000개 코퍼스에서 300ms 이내」 · `test_1000_sections_…` `:650-669`(`query_raw="keyword2"`)
- **챌린지**: 합성 1,000섹션(섹션당 ~1.3KB 한글 + 인용 6개, base·head 같은 코퍼스) 중앙값: `keyword2` base 144 / head 147ms(게이트가 보는 경로) · 한글 띄어 쓴 5토큰 154 → 229ms · 붙여 쓴 4자+ 3토큰 179 → 289ms · 5토큰 212 → **409ms** — spec 상한 초과이고 게이트(<1s·ASCII)는 이를 못 본다. cProfile: `flex_search` 10,017회 0.18s(프로파일 총 0.82s 의 22%), 그중 `flex_pattern` 문자열 재조립 `:514` 0.077s — 질의 토큰당 1회면 되는 일을 섹션마다 반복한다. E4 가 적은 「compact」 방식은 프로토타입 결과 부적합(공백을 지우면 좌측 경계도 사라져 1,000본문에서 flex 701 히트 vs compact 5 히트) — 구현이 flex 로 바꾼 판단은 옳지만 그 비용과 결정이 플랜 §4 보정에 없다.
- **제안**: (a) `Query` 에 토큰별 컴파일된 flex 패턴을 실어 재사용. (b) 본문 flex 전에 `t[:2] in body_lc` 빠른 거부 — E4 의 대상은 단어 단위 띄어쓰기(`진입 파일`)이지 글자 단위(`진 입 파 일`)가 아니라는 전제를 docstring 에 명시. (c) 성능 테스트에 한글 4자+ 5토큰 질의 1건 추가하고 상한을 spec 의 300ms 또는 명시적으로 완화한 값으로 고정. (d) §4 보정에 「E4 compact → flex 정규식」 결정과 사유 기록.

### C7 — `sources` glob 의 `*` 가 `/` 를 넘는다 — #30 의 gitignore 의미와 어긋나 같은 `sources` 가 다른 집합을 가리킨다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: E7 `:134` 「`**` 는 fnmatch `*` 가 `/` 를 포함하므로 그대로 동작. `pathlib.full_match` 는 3.13 전용이라 미사용」 · `_source_glob_match` `:524` · `29-frontmatter-manifest.md` 「`sources` … (glob 허용) — #30 의 paths 로 재사용」 · `2026-09-04-context-retrieval-feature-plan.md:92` 「매칭은 gitignore 스타일(`ignore` 라이브러리)」
- **챌린지**: 실측 `_source_glob_match`: `app/services/*.rb` ↔ `app/services/wms/x/y.rb` **True**, `*.rb` ↔ 아무 경로 True, `app/services/wms/*.rb` ↔ `app/services/wms/x/y.rb` True. gitignore/`.claude/rules paths:` 의미(#30 이 같은 값을 재사용)에서는 셋 다 False 다. 같은 frontmatter 한 줄이 #27 에서는 도메인 밖 소스 경로 질의에 +6 파일 보너스를 주고 #30 에서는 규칙을 로드하지 않는 불일치. `test_nested_suffix_and_directory_forms` 는 `**`·디렉토리 형만 검증하고 단일 `*` 의 경계는 없다.
- **제안**: glob → 정규식 변환 10줄(`**` → `.*`, `*` → `[^/]*`, `?` → `[^/]`, 접두 없는 패턴은 `(^|/)` 앵커)로 gitignore 의미를 맞추고 테스트에 `app/services/*.rb` vs 중첩 경로 False 추가. E7 근거 문장은 「fnmatch 는 `*` 가 `/` 를 넘어 over-match 하므로 쓰지 않는다」 로 뒤집는다.

### C8 — `--max-bytes` 는 `text` 합만 세고 stdout 은 세지 않는다 — 상한 24,000 에서 실제 출력 29.8~39.6KB
- **severity**: suggestion
- **category**: risk
- **plan 인용**: §2 A5 `:95` 「Bash 출력 45.8KB 가 파일로 스왑되고 … 하드 상한 24,000B」 · `INJECT_MAX_BYTES_CAP` `:100` 「Bash 도구 출력이 파일로 스왑되는 크기 아래로 고정」 · docstring 「총 `--max-bytes`」 · `wrapper-protocol.md:42` 「총 12,000B·섹션당 400줄 상한」 · `_apply_inject` `:1230`
- **챌린지**: 예산은 `len(ln.encode())+1` 의 합(`:1230`)이라 헤더·표·manifest 줄·`<context-snippet …>` 래퍼·`[잘림]`·INFO 는 밖이다. 실측(라이브, `pilot skills --limit 20 --inject --max-bytes 24000`): md 29,786B · manifest 32,517B · json **39,591B**(json 은 `snippet` 과 `text` 를 둘 다 실어 1.65×). 기본값에서도 `select:pilot/spec.md,pilot/lifecycle.md --inject` md 는 15,795B 로 「총 12,000B」 를 넘는다. 스왑 임계값은 플랜에 없어(45.8KB 관찰만) 24,000 이 「아래」 인지 검증할 수 없고, json 은 상한 근처에서 이미 그 관찰치에 근접한다.
- **제안**: 예산을 렌더 결과 기준으로 — `_apply_inject` 가 래퍼 2줄과 skip/잘림 줄 바이트도 차감하고, json 은 `--inject` 시 `snippet` 을 생략. 문서는 「`--max-bytes` 는 주입 본문 합」 으로 정확히 쓰고 프로토콜은 md/manifest 만 권장. 실제 스왑 임계값을 1회 실측해 상수 주석에 남긴다.

### C9 — 게이트가 보증하지 않는 것: 골든은 top-3 포함만, 점수·순서 스냅샷은 scratch 에만, 힌트 테스트 부재
- **severity**: suggestion
- **category**: test-gap
- **plan 인용**: G2 `:220` 「Q1~Q4 의 점수·순서가 Phase 0 스냅샷과 동일」 · G4 `:222` · §3.3 스텝 18 `:185` 「orchestrate-load 힌트 문구에 `--format manifest` 추가 + 테스트」 · §3.2 `:148` 「힌트 문구 테스트 있으면 갱신」 · `GoldenHitAtThree` `:1225-1272`
- **챌린지**: (1) 골든 6건은 `(file, heading)` 이 top-3 에 있는지만 본다 — Q5 의 1위 7점 vs 2위 6점(동점이면 `is_entry` 로 index.md 우선) 같은 마진·점수·순서는 어떤 테스트도 고정하지 않는다. G2/G4 의 「스냅샷 동일」 은 scratch 파일 대조라 저장소에 남지 않았고 재현 불가. (2) 스텝 18 의 「+ 테스트」 는 없다 — `pilot/tests/` 전체에서 `manifest --limit`·`[검색]` grep 0건, `cf5f8b8` 의 테스트 추가는 `test_select_accepts_displayed_cwd_relative_path` 1건뿐. 힌트 문구가 `{file}#{heading}` 리터럴을 f-string 밖에 두는 구조(`orchestrate-load.py:527-529`)도 테스트가 없어 f-string 으로 옮기는 순간 `NameError` 가 런타임에만 난다. (3) C1·C4·C5 시나리오(백틱 헤딩·include select·자식 선행)도 미검증. (4) G6 은 미실측이라 §2 B 「점수표 조정 5개보다 이 한 항목의 기대 효과가 크다」 는 근거 0 인 채 배선됐다.
- **제안**: fixture 에 골든 6질의의 기대 결과(`heading·score·matched·line_start·line_end` 상위 5)를 JSON 으로 커밋하고 동등성 테스트 1건(경로는 CWD 의존이라 제외). `test_orchestrate_load.py` 에 힌트 문구 assert 1건(`manifest --limit 8`·`select:{file}#{heading}` 리터럴). C1·C4·C5 테스트. G6 은 다음 feature 사이클 evaluator 증거 항목으로 명시.

### C10 — E4 헤딩 규칙의 문서와 코드 불일치: 2글자 헤딩 토큰도 참여하고, 질의 쪽 조사가 헤딩에서만 흡수된다
- **severity**: nit
- **category**: doc-drift
- **plan 인용**: §4 E4 세부 `:267` 「헤딩의 한글 토큰이 질의 토큰에 포함될 때도 부분 일치(5)로 친다 … 3자 이하·ASCII 토큰은 제외」 · `score_text` `:591` · `build_zero_hit` `:732` C8 항 「조사 제거 재질의」
- **챌린지**: 「3자 이하 제외」 는 코드에서 질의 토큰(`_reverse_candidate`, ≥4)에만 걸리고 헤딩 토큰은 2글자부터 참여한다 — 실측 `진입파일` ↔ 헤딩 `파일 목록` 5점, `설정파일` ↔ 헤딩 `설정` 5점. 부작용으로 조사가 붙은 4자 토큰이 헤딩에서만 흡수된다: `도메인을` ↔ 헤딩 `도메인 분류` base 0 → head 5, 라이브 `도메인을 진입파일로 자동로드` 0건 → 3건(`진입파일로`·`도메인을` 이 헤딩 부분 일치). 본문 쪽(`flex`)은 여전히 조사를 요구하므로 비대칭이고, 0건 안내는 여전히 「조사 제거 재질의」 를 권한다. 유해하진 않다(띄어 쓴 `도메인 분류` 는 헤딩 정확 10 을 받으므로 역방향 5 는 더 보수적) — 문서가 코드를 설명하지 못할 뿐이다.
- **제안**: E4 세부를 「헤딩 토큰은 길이 제한 없음(2글자 포함), 질의 토큰만 ≥4」 로 고치고 docstring 점수표에 「조사 붙은 4자+ 질의 토큰은 헤딩에서 부분 일치 가능」 1줄. 길이 제한을 원하면 `h in t` 에 `len(h) >= 3` 을 걸고 Q5 재실측(정답 헤딩 토큰 `진입` 이 2글자라 Q5 가 깨질 것이므로 현행 유지가 맞다는 결정을 기록).

### C11 — 「붙여 쓴 본문과 띄어 쓴 본문의 점수가 같다」 는 2단어 결합·본문/description 에만 성립
- **severity**: nit
- **category**: premise
- **plan 인용**: §2 A2 `:66` 「지시서 방향(띄어 쓴 질의 → 붙여 쓴 본문)은 헤딩에서 이미 해결돼 있고」 · docstring 「같은 토큰·같은 신호는 한 번만 — 붙여 쓴 본문과 띄어 쓴 본문의 점수가 같다」 · `release-notes.md:47`
- **챌린지**: 실측 `score_text`: 질의 `선발송 접수 상태` ↔ 본문 `선발송접수상태` 4점(`상태` 는 `접수상태` 쌍이 좌측 경계에 막혀 미매칭, `:607`) vs 본문 `선발송 접수 상태` 6점. 헤딩: 질의 `선발송 접수 규칙` ↔ `## 선발송접수 규칙` 20 vs `## 선발송 접수 규칙` 30 — 「이미 해결」 은 hit 기준이지 점수 동등이 아니다. 3어절 붙여쓰기·붙여 쓴 헤딩은 한국어 기술 문서에서 드물지 않다.
- **제안**: docstring·release-notes 문구를 「2단어 결합·본문/description 한정」 으로 좁히거나, 결합어 대조를 「t2 가 t1 매치 직후에 이어지는 위치」 기준으로 바꿔 3어절 연쇄를 허용(6~8줄).

### C12 — 소소한 가장자리 5건(무해하나 문서·테스트에 없음)
- **severity**: nit
- **category**: edge-case
- **plan 인용**: E9 `:136` 「섹션당 400줄」 · E8 `:135` 「헤딩 부분은 substring 이므로 쉼표 앞 접두만 쓰면 된다」 · E10 `:137` · §2 A1 `:49` 「`type`·`domain`·`sources` 는 파싱해 **출력 필드**로 노출한다」 · `_result_entry` `:1082` · `_normalize_select_path` `:1088`
- **챌린지**: (a) 400줄 캡이 복원한 헤딩 줄을 포함해 본문 400줄 섹션(L1-401)이 잘리고 `inject_rest` 가 `offset=401 limit=1` 이 된다(`:1229`). (b) `select:a.md#상태, 전이 규칙` → 두 번째 대상 `전이 규칙` 이 경로로 해석돼 INFO 「select 대상 없음」 + 후보 노이즈 — 코퍼스 헤딩에 쉼표는 0건이라 지금은 무해. (c) manifest 필드 구분자 ` | ` 가 표 본문 snippet 의 `|` 와 충돌(실측 `… | matched: table | | a | b | | --- |`) — 마지막 필드라 앞 5개는 분리 가능하나 문서에 없다. (d) §2 A1 은 `sources` 도 출력 필드로 노출한다고 했으나 JSON 에는 `type`·`domain` 만 붙는다 — E6·스텝 14 와 §2 A1 불일치. (e) `context/` 접두 무조건 제거(기준 커밋부터)로 도메인명이 `context` 면 `select:context/index.md` 가 0건(실측, 후보로 자기 자신 제시).
- **제안**: (a) `lines[:LARGE_SECTION_LINES + (1 if level in (2, 3) else 0)]`. (b) 헤딩에 쉼표가 들어오면 E8 예비안(`--select` 반복)으로 전환하는 조건을 테스트로 남긴다. (c) docstring 에 「snippet 은 마지막 필드 — 앞 5개 ` | ` 로만 분리」 1줄. (d) §2 A1 문장을 `type`·`domain` 으로 정정하거나 `sources` 를 조건부 키로 추가. (e) 접두 제거 후 부재 시 원문으로 1회 재시도.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | 프로토콜 3곳(wrapper-protocol §6·ask 절차 2·orchestrate-load 힌트) 작은따옴표 + "헤딩은 manifest 의 백틱 제거본 일부" · 도구: `_heading_key` 로 백틱·`*`·`_` 무시 대조, `#` 뒤 빈 헤딩은 파일 전체 + INFO(쉘 인용 확인), manifest 헤딩 표시에서 백틱 제거 · 테스트 3건 |
| C2 | accepted | 규칙의 키를 경로로 확장 — wrapper-protocol §6·ask: "`rules/`·`boundaries/` 경로 후보(manifest 태그 `[rules?]`·`[boundary?]`) 또는 frontmatter 태그" + "질의의 핵심 토큰이 `matched` 에 있으면" 으로 두 문서 동일 문구. 도구: manifest 가 frontmatter `type` 부재 시 경로로 추정 태그 표시(JSON `type` 은 frontmatter 사실만) · 테스트 1건 |
| C3 | accepted | G4·release-notes 를 "한글 결합·역방향 규칙에 해당하지 않는 질의(Q1~Q4·select·라이브 3질의)에 한해 바이트 동일, 4자+ 한글 토큰·인접 한글쌍 질의는 점수·순위·0건 안내가 바뀐다(설계 의도)" 로 정정. confluence 는 "코드 무변경 — 같은 랭커라 한글 규칙이 `/pilot:confl search` 에도 적용" 으로 사용자 영향 기록(§3.3 스텝 13 포함) |
| C4 | accepted | `_normalize_select_path` 가 루트 기준·접두·CWD 표시 경로·`../projects/…` 후보를 색인 파일 집합과 대조해 해석, 봉쇄 기준을 collect_files 와 같은 "workspace 안" 으로 변경(`../x` 허용, `../../x` 거부) · 라이브 include 파일 왕복 실측 1건 · 테스트 1건 + 기존 traversal 테스트 2건 기준 조정 |
| C5 | accepted | `_apply_inject` 가 텍스트 줄마다 파일 라인 범위를 들고, 뒤에 오는 H2 가 앞서 주입된 H3 범위를 `[L{s}-{e} 는 [#k] 에 주입됨 — 생략]` 1줄로 접는다(잘림 힌트 offset 은 파일 라인 기준 유지). 앞→뒤 생략 규칙은 그대로 · 테스트 3건(키워드 순서·select 역순·접힌 뒤 잘림) |
| C6 | accepted | 경계·flex 정규식을 `functools.lru_cache` 로 토큰당 1회 컴파일(실행 내 memo), flex 는 첫 글자 부재 시 정규식 없이 거부. 실측(1,000섹션 한글, 전 섹션 일치 최악 케이스): joined 5토큰 314 → 274ms · joined 3토큰 238 → 213ms · ASCII 128 → 127ms. 한글 5토큰 성능 테스트 추가(상한 1.0s, spec 300ms 는 목표) · compact→flex 결정을 flex_pattern docstring 과 §4 에 기록 |
| C7 | accepted | fnmatch 대신 gitignore 의미 정규식(`_glob_regex`, lru_cache): `*`·`?` 는 `/` 를 넘지 않고 `**` 만 가로지름, 슬래시 있는 패턴은 루트 앵커, 없는 패턴은 어느 깊이의 이름과도 일치, 디렉토리는 하위 전부. `wms/**` 는 이제 `app/services/wms/x.rb` 와 불일치(#30 과 동일 집합) · 테스트 hit 10·miss 6 |
| C8 | accepted | 예산을 md/manifest 렌더 총량 근사로 — 예비 600B + 결과별(표/manifest 줄 큰 쪽 + 래퍼·잘림·생략 줄) 오버헤드를 먼저 뗀다. 헤딩 줄만 들어가는 섹션은 생략. json 은 CLI 가 예산 65% 축소 + INFO. 스왑 임계 실측 28,000B 인라인·31,200B 스왑 → 상한 24,000 유지. 실측: 상한에서 md 19.9K·manifest 22.6K·json 21.5K (전: 29.8K/32.5K/39.6K) · 테스트 2건 조정 + 1건 |
| C9 | accepted | (1) `fixtures/context-search/golden-expected.json` 에 골든 6질의 상위 5 의 점수·순서·matched·라인 범위를 커밋하고 `GoldenSnapshotTest` 로 동등성 검증(README 갱신 규칙 4 추가) (2) `test_orchestrate_load` 힌트 테스트에 `--format manifest --limit 8`·`'select:{file}#{heading}'` 리터럴 assert (3) C1·C4·C5 시나리오는 각 라운드에서 테스트 추가 (4) G6 은 §4 남은 일에 evaluator 증거 항목으로 유지 |
| C10 | | |
| C11 | | |
| C12 | | |
