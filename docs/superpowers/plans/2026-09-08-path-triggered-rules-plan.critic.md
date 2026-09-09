# Plan Critic — 경로 트리거 도메인 규칙 주입 플랜 (#30 C1) · 커밋 `db2c51e` (적용 전)

> 입력 plan: `docs/superpowers/plans/2026-09-08-path-triggered-rules-plan.md` (검토 시각 2026-09-08T09:14:33Z)
> 입력 feature: `workspace/projects/build-plugin/features/30-path-triggered-context.md` · `29-frontmatter-manifest.md` · `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` §0.4 · P3 · § F-C · 부록 B
> 페르소나: `personas.planner-critic` (red-team)
> 검증 방법: (1) **C1 재현** — 임시 규칙 `.claude/rules/zz-critic-probe-{a,b,c,d}.md` 4종을 세션 중 생성해 같은 Claude Code 원격 세션(바이너리 `claude --version` = 2.1.263)에서 발화를 관찰: a `paths: pilot/tools/docs_build.py` 를 Read 도구로 · b `zz-critic-probe-dir/**` 아래 새 파일을 Write → Edit(Read 없이) → Read 순으로 · c `pilot/hooks/slack-notify.sh` 를 Bash `sed` → Read → 규칙 본문 수정 → 재-Read · d 슬래시 없는 `"*.py"`. 서브에이전트 재현은 이 세션에 Agent 도구가 없어 **불가** — 공식 sub-agents 문서로 대체. (2) **§3.2 프로토타입** `scratchpad/paths_proto.py` — `context-search.py` 의 `collect_files`·`parse_frontmatter`·`extract_citations`·`_source_glob_match` 를 importlib 로 재사용(confluence D5 패턴)해 라이브 `workspace/context` 도메인 `pilot`·fixture `pilot/tests/fixtures/context-search/workspace`·미등록 도메인·`source_root` 제한을 실행하고, doctor 의 `_iter_cited_paths`·`_resolve_cited`·`_is_workspace_internal`(#28) 로 같은 도출을 대조, 합성 2도메인 겹침 실험. (3) §3.1 템플릿 4케이스 글자수. (4) `coding-rules.sh` stdin JSON 실행 3회(라이브 config · 규칙 있는 임시 workspace · `session_id` 부재). (5) 공식 문서 memory·hooks·sub-agents·plugins-reference WebFetch 원문 대조. (6) 베이스라인 `python3 -m unittest discover -s pilot/tests/tools` 680 OK · `docs_build.py --check` exit 0 · `doctor.py workspace` 4 PASS·3 WARN·1 ERROR(STATE.md 부재 — 플랜 G5 기록과 일치). 프로브·디렉토리는 전부 삭제, `git status --porcelain` 빈 출력. 프로토타입은 scratch 전용(산출물 아님).
> 실측으로 재현돼 반증하지 못한 플랜 주장(챌린지 아님): C1 메인 세션 발화(Read 직후 `Contents of …/.claude/rules/…:` 블록) · 규칙 파일당 세션 1회(같은 파일 재-Read 시 재주입 없음 — 그 재-Read 에 새 규칙 d 는 발화했으므로 평가는 매번 일어나고 경로 단위로 dedup 된다) · 세션 중 생성한 규칙 파일도 다음 매칭 Read 에 로드 · 따옴표 없는 `dir/**`·정확 경로 파싱 · glob 의미 = gitignore = `_glob_regex`(슬래시 없는 `*.py` 가 중첩 `pilot/tools/docs_build.py` 에 발화 — memory 문서 표의 「`*.md` = 루트만」 과 다르고 플랜 쪽이 맞다) · hooks 문서: command 훅 timeout 기본 600s, PreToolUse·PostToolUse `additionalContext` 선택 · 훅은 서브에이전트 안에서도 실행 · 생성 시간 20~29ms(G3 200ms 대비 여유) · 결정성(프로토타입 3회 동일) · `coding-rules.sh` 81ms·세션 마커 동작.

## 챌린지

### C1 — Write·Edit 는 발화하지 않고, 그 틈을 메운다는 `coding-rules.sh` 는 이 저장소에서 no-op 이며 도메인 포인터도 아니다
- **severity**: blocking
- **category**: premise
- **plan 인용**: §3.1 「발화 조건의 한계」 `:58` 「새 파일 `Write` 만으로는 발화하지 않을 수 있다 — 그 틈은 현행 `coding-rules.sh`(세션 1회 포인터)가 메운다. 두 장치는 중복이 아니라 보완이며, 문서에 그렇게 적는다」 · §2 `:30` 「**`coding-rules.sh` 무변경** — 회귀 테스트만 신설」 · §1 `:21` 「현행 훅 … 세션당 1회 포인터」 · §3.3 `:79` 「문서 주석에 C1 과의 역할 분담 1줄」
- **챌린지**: (1) 발화 조건은 "않을 수 있다" 가 아니라 확정이다 — 같은 규칙(`paths: zz-critic-probe-dir/**`)·같은 파일에 대해 Write → 미발화, Edit(Read 없이) → 미발화, Read → 발화(`CRITIC-MARKER-B3W` 주입). memory 문서도 「Path-scoped rules trigger when Claude reads files matching the pattern, not on every tool use」. (2) 메운다는 훅은 라이브 저장소에서 아무것도 내지 않는다 — `printf '{"tool_input":{"file_path":"…/pilot/tools/x.py"},"session_id":"…"}' | CLAUDE_PROJECT_DIR=… bash pilot/hooks/coding-rules.sh` → exit 0, stdout 빈 문자열. 원인은 `coding-rules.sh:52`·`:75` 의 게이트: `workspace/context/rules/` 부재 + `conventions_doc` 셀이 스켈레톤 예시(`예: \`context/conventions.md\``, doctor 도 「미선언 취급」 INFO) — 즉 `rules/` 를 손으로 만들지 않은 모든 소비 레포에서 no-op 이고, learn 은 `rules/{domain}.md` 를 만들지 않는다(`learn/SKILL.md:103`). (3) 발화하는 경우(임시 workspace 에 `rules/wms.md` 1개, 81ms)에도 메시지(`:79`)는 「pilot 워크스페이스에 코딩 규칙이 정의돼 있습니다 … workspace/context/rules/ (도메인 규칙)」 — 어느 도메인인지, 진입 파일이 어디인지 없는 범용 리마인드이고 세션당 1회라 두 번째 도메인에는 아예 오지 않는다. 따라서 §2 의 「무변경」 판정과 §3.1 의 「보완」 서술은 근거가 없고, 그대로 문서화하면 거짓 진술이 된다. 생성기가 이웃 파일을 Read 하지 않고 새 파일만 만드는 경우(신규 서비스·마이그레이션·테스트 추가)에 포인터가 오지 않는 것은 설계된 공백으로 남는다.
- **제안**: 둘 중 하나를 명시 결정. (A) 최소 — §3.1 을 「Write·Edit 만으로는 발화하지 않는다(실측). 같은 디렉토리 파일 1개를 먼저 Read 하는 관행이 유일한 완화」 로 정정하고 `coding-rules.sh` 를 보완 장치로 부르지 않는다; wrapper-protocol 권장 절에 「도메인 경로에 새 파일을 만들 때는 이웃 파일 1개를 먼저 Read」 1줄(soft). (B) Write 전용 C2 — 이미 PostToolUse `Edit|Write` 에 걸린 `coding-rules.sh` 가 `.claude/rules/pilot-*.md` 의 frontmatter `paths` 를 읽어 `tool_input.file_path` 를 같은 gitignore 의미로 대조하고, 매칭 파일의 본문(≤ 500자)을 세션·도메인당 1회 `additionalContext` 로 내보낸다 — 규칙 파일이 단일 SSOT 라 매처 재구현이 아니고 python 1회 추가로 100ms 예산 안. 어느 쪽이든 §2 표의 근거 열과 §1 「현행 훅」 행을 고친다.

### C2 — §3.2 인용 추정은 라이브 코퍼스에서 catch-all·죽은 glob·무조건 규칙을 만든다
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: §3.2-3 `:64` 「파일 본문 인용(`extract_citations`) 중 workspace 내부 인용 제외 → 디렉토리별 파일 수 집계 → 파일 ≥ 2 인 디렉토리를 `dir/**` 로, 최대 8개, 초과 시 공통 상위로 접기」 · §3.1 `:55` 「`paths` ≤ 8 globs(초과 시 공통 상위 디렉토리로 접기)」 · §3.6 골든 `:104` 「인용 추정 경로 — `pilot/skills/**` 류」 · §3.9-2 `:127`
- **챌린지**: 프로토타입을 라이브 `--domain pilot` 에 돌리면(인용 248건·고유 76): (a) `extract_citations` 는 랭킹용 토큰 추출기(`_CITATION_RE` `:485`)라 `${CLAUDE_PLUGIN_ROOT}/tools/doctor.py` 에서 `/tools/doctor.py` 같은 절대경로 조각 10건, `templates/STATE.md.templ`(확장자 5자 절단)·`.../.focus.histo` 같은 조각을 낸다. (b) 스킬 상대 인용(`references/heuristics.md`·`shared/coding.md`·`templates/config.md.templ`·`tools/doctor.py`)이 저장소 루트에 존재하지 않는데도 집계돼 죽은 glob 4개(`references/**`·`shared/**`·`templates/**`·`tools/**`)가 된다 — 알고리즘에 존재 필터가 없다. (c) `pilot/index.md:35-39` 의 링크 표시문 `[pilot/lifecycle.md](lifecycle.md)` 5건이 `pilot/` 직속 파일로 집계돼 **`pilot/**` catch-all** 이 나온다 — 루트 기준으로 해석하면 파일이 없어 「workspace 내부 인용 제외」 에 걸리지 않는다. 결과 11 globs 중 유효 6, 그것도 전부 `pilot/**` 에 포섭. (d) 11 > 8 → 접기: `os.path.commonpath(['pilot/hooks','references','shared','templates','tools'])` = `''` → 규칙이 `**` 하나가 되고 P3 규칙(「`**` 만이면 무조건」)대로 **모든 세션에 무조건 로드** — 경로 스코프의 정반대. 깊은 쪽만 접어도 결과는 `pilot` + 죽은 4개. (e) §3.9-2 의 `source_root` 제한을 걸어도 7 globs 에 `pilot/**` 가 남아 나머지 6개는 무의미. (f) 골든 기대 「`pilot/skills/**` 류」 는 이 알고리즘의 산출물이 아니다 — `pilot/skills/learn` 등 20개 스킬 디렉토리는 파일 1개씩이라 `≥ 2` 에서 탈락하고 `pilot/skills/**` 는 어디서도 생성되지 않는다(G6 시나리오 `pilot/skills/learn/SKILL.md` 가 매칭되는 것은 오직 (c)(d) 의 catch-all 덕분). fixture 도 같은 구조에 `workspace/context/**`(fixture 가 `workspace/context/pr.md` 를 인용)까지 추가된다 — 지식 문서를 읽을 때마다 자기 포인터가 뜬다.
- **제안**: 추출기를 #28 의 doctor 체인으로 바꾼다 — `_iter_cited_paths`(괄호·백틱 인용만) → `_resolve_cited(repo, source_root)`(실파일 해석, 미해석 탈락) → `_is_workspace_internal` 제외. 같은 코퍼스 실측: 인용 87 → 해석 74 · 내부 3 · 미해석 10 탈락, 조각 0, leaf glob 6(`pilot/.claude-plugin`·`hooks`·`skills/context/{lifecycle,modes,shared}`·`tools`). 그 위에 집계를 leaf 가 아니라 **하위 트리 합산**으로 바꾸고 캡 안에서 커버율로 고른다(루트·`**`·조상-자손 중복·존재하지 않는 디렉토리 금지): 실측 `pilot/skills/**`(53)·`pilot/tools/**`(13)·`pilot/hooks/**`(5) = 71/74(96%) 3 globs — 골든 기대와 일치하고 G6 가 우연이 아니라 알고리즘으로 성립한다. 테스트에 「접기 결과에 `**`·루트 없음」·「존재하지 않는 디렉토리 0」·「`pilot/**` 미생성」 3건.

### C3 — 규칙 파일당 세션 1회는 dedup 이자 stale 이다: 재생성한 내용은 그 세션에 다시 들어오지 않는다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: §2 `:30` 「C1 은 규칙 파일당 세션 1회 로드라 dedup 이 하네스에 내장」 · §3.3 `:76` 「learn Phase 5 … `--write` 실행 … Boundary 모드 … A 도메인 규칙 파일을 재생성」 · §3.5 Phase 3 `:97`
- **챌린지**: 프로브 c — Read 로 발화시킨 뒤 규칙 본문을 `C9K` → `C9K-V2-MODIFIED` 로 바꾸고 같은 파일을 재-Read → 새 내용 미주입(같은 턴에 다른 새 규칙 b 는 발화했으므로 평가는 됐고 경로 dedup 에 막힌 것). 즉 `/pilot:learn` 이 세션 중 `pilot-{domain}.md` 를 재생성하면(초기 학습·`--force`·Boundary 모드 모두) 현재 세션은 이전 포인터(삭제된 경계·옛 index 경로)를 끝까지 들고 간다. memory 문서상 재로드 시점은 「after `/compact` … rules with `paths:` reload as Claude reads files they apply to」 뿐. 새로 뜨는 서브에이전트는 fresh 컨텍스트라 새 파일을 읽으므로 영향 없음 — 문제는 learn 을 돌린 메인 세션 자신과 그 세션이 이어서 하는 직접 편집이다. 플랜은 1회 로드를 장점으로만 적었다.
- **제안**: learn Phase 5 결과 출력(`SKILL.md:82` 항목 5)에 「규칙 파일 갱신 — 이 세션에는 이전 내용이 남아 있음(새 세션 또는 `/compact` 후 재로드)」 1줄, `rules-pointer.py --write` 가 내용이 바뀐 경우 같은 INFO 를 낸다(무변경이면 침묵). workspace-layout 파생물 행에 「세션당 1회 로드」 명시. doctor 검사 대상은 아니다(세션 상태).

### C4 — 규칙 파일 안의 `${CLAUDE_PLUGIN_ROOT}` 는 아무도 치환하지 않는다 — 3단계 진입 줄이 메인 세션에서 죽는다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: §3.1 템플릿 `:52` 「상세 조회: python3 ${CLAUDE_PLUGIN_ROOT}/tools/context-search.py …」 · §3.3 `:70` 「`build_rules_file(workspace, domain, plugin_root)`」 · §3.6 `:102` 「템플릿 정확(마커·`${CLAUDE_PLUGIN_ROOT}` 리터럴)」 · §3.9-1 `:126` 「제안: 커밋」 · §0 `:11` 「본문은 이미 배선된 3단계 … 로 요청 시」
- **챌린지**: plugins-reference 문서 — 플레이스홀더 인라인 치환은 스킬·에이전트 본문·훅 명령·MCP/LSP 설정에서만, 환경변수 export 는 훅·MCP·LSP 프로세스에만. `.claude/rules/*.md` 는 플러그인 컴포넌트가 아니므로 리터럴이 그대로 모델에 닿고, Bash 도구에서 `${CLAUDE_PLUGIN_ROOT}` 는 미설정 → 빈 문자열 → `python3 /tools/context-search.py`(이 세션 env 에도 없음 — `coding-rules.sh:79` 가 훅 시점에 `${CLAUDE_PLUGIN_ROOT:-\$CLAUDE_PLUGIN_ROOT}` 로 실경로를 박아 넣는 이유). 래퍼 안에서는 에이전트 지시문에 치환된 경로가 있어 추론 가능하지만, C1 의 핵심 사용처인 「스킬을 부르지 않고 메인 세션이 직접 도메인 코드를 만지는 경우」(`session-context.sh:6-8` 가 적은 갭)에는 단서가 없다. 반대로 `plugin_root` 를 박으면 `~/.claude/plugins/cache/{marketplace}/pilot/{version}/`(`release-and-upgrade.md:68`) 라 기계·버전 종속 — 커밋 제안(§3.9-1)과 충돌하고 `/plugin update` 때마다 `--check` 불일치 INFO 가 나며 해소 수단이 learn 재실행뿐이다. 시그니처(`plugin_root` 인자)와 테스트(「리터럴」)가 서로 다른 답을 가리킨다.
- **제안**: 상세 조회 줄을 경로 없는 형태로 — 메인 세션용 `/pilot:ask <질문>`(스킬 이름은 하네스가 해석)을 1순위로 적고, 래퍼용 `context-search.py … --scope {d}` 는 「(래퍼 안에서, 지시문의 플러그인 루트 기준)」 로 한정. 또는 `session-context.sh` 가 이미 세션 1회 주입하는 포인터에 「pilot 도구 루트: {실경로}」 1줄을 추가해 규칙 파일이 그것을 참조하게 한다(훅은 env 를 가진다). `plugin_root` 인자는 시그니처에서 뺀다.

### C5 — learn Phase 5 배선 순서·Abort 계약·Boundary 재생성이 서로 맞지 않는다
- **severity**: suggestion
- **category**: protocol
- **plan 인용**: §3.3 `:76` 「MANIFEST 갱신·doctor 직전에 `rules-pointer.py --domain {domain} --write` … Abort cleanup 계약: 규칙 파일 Write 는 Phase 5 batch 안에서」 · `:70` 「도메인 미등록 → `SearchError` 류 exit 2」 · `:76` 「Boundary 모드(`--boundary B --from A`)는 A 도메인 규칙 파일을 재생성」 · §3.1 `:56` 「`boundaries/{domain}--*` ≤ 2」
- **챌린지**: (1) MANIFEST 등록은 Phase 5 항목 1~3(`learn/SKILL.md:78-80`)에서 일어나므로 「MANIFEST 갱신 직전」 실행이면 도메인이 아직 미등록 — 플랜 규칙대로면 exit 2 로 learn 이 매번 실패하고, `collect_files` 를 그대로 재사용하면 미등록 scope 가 예외 없이 코퍼스 전체로 폴백한다(실측 `collect_files(ws, 'nope')` → info 1줄, 파일 8개, 전 도메인 인용으로 12 globs — 오타 도메인이 모든 경로에 발화하는 규칙 파일을 만든다). (2) 「Phase 5 batch」 는 없다 — batch Write 는 Phase 4-6(`SKILL.md:72`)이고 Phase 5 는 MANIFEST Edit + doctor Bash 다(`SKILL.md:35` 의 「Phase 5 batch Write」 문구 자체가 기존 오기이며 플랜이 그대로 물려받았다). 규칙 파일은 batch 밖·MANIFEST 뒤에 Bash 로 써진다고 적어야 Abort 계약(「중단 시 어떤 Write 도 안 함」)과 정합한다. (3) 포인터 선정은 정방향 `boundaries/{domain}--*` 만 보지만 `collect_files`(`context-search.py:909` 이하, `*--{scope}` 포함)와 orchestrate-load(`SKILL.md:96`)는 역방향도 로드한다 — `--boundary wms --from schoice` 는 `schoice` 규칙만 재생성하고 `wms` 규칙은 `schoice--wms.md` 를 영영 모른다.
- **제안**: Phase 5 를 「1~3 MANIFEST → 4 `rules-pointer.py --write`(`parse_manifest_domain_files` 로 등록을 명시 확인, `collect_files` 폴백에 의존하지 않음) → 5 doctor → 6 결과」 로 번호 조정하고 `SKILL.md:35` 의 「Phase 5 batch」 를 「Phase 4 batch」 로 정정. Boundary 모드는 A·B 양쪽 규칙을 재생성(B 는 등록돼 있을 때만), 포인터 후보에 역방향 경계 포함(합계 ≤ 2, 정방향 우선).

### C6 — 「서브에이전트 모두」 는 general-purpose 1종의 관찰이고, 문서는 Explore·Plan 이 프로젝트 규칙을 건너뛴다고 적는다 · 미발화 환경의 감지 수단이 없다
- **severity**: suggestion
- **category**: premise
- **plan 인용**: §0 `:11` 「메인·서브에이전트 모두, git 무시 여부와 무관하게 발화」 · §1 `:18` 「서브에이전트에서도 주입 (#30 Open Q (c) 해소)」 · §3.8 `:122` 「하네스가 C1 을 지원하지 않는 환경이 확인되면 그때 재개」 · §1 표 헤더 `:13`(하네스 버전 미기재)
- **챌린지**: sub-agents 문서: 「CLAUDE.md files: every level of the CLAUDE.md hierarchy … including … project rules … **The built-in Explore and Plan agents skip this**」. pilot 은 Explore 를 명시적으로 쓴다 — `ask/SKILL.md:53`·`context/domain/scope-exploration.md:10` — 그 탐색에는 포인터가 없다(지연 로드되는 path 규칙까지 건너뛰는지는 문서에 없고 이 세션은 Agent 도구가 없어 실측 불가). 환경 게이트도 있다: `--setting-sources` 에서 `project` 제외 시 규칙 skip(v2.1.211 부터 path 규칙 포함), `claudeMdExcludes` 로 `.claude/rules/**` 제외 가능 — 이 경우 C1 은 무음으로 꺼지고 C2 폐기 + `coding-rules.sh` no-op(C1)이라 대체도 감지도 없다. #30 비즈니스 규칙은 실측 기록에 「일자 · Claude Code 버전」 을 요구하는데 §1 은 버전이 없다(이 세션 바이너리 2.1.263; env `CLAUDE_CODE_VERSION` 은 2.1.42 로 달라 바이너리 값을 적어야 한다). 문서상 v2.1.198(심링크 매칭)·2.1.207(잘못된 패턴)·2.1.211·2.1.217(brace 예산)이 거동 경계다.
- **제안**: #30 실측 기록에 버전·세션 종류·재현한 서브에이전트 종류(general-purpose)·**미검증**(Explore/Plan·`--bare`·`--setting-sources`)을 그대로 적는다. G4 에 Explore 프로브 1건 추가(래퍼가 아닌 ask 경로). doctor `check_workspace` 에 `.claude/settings*.json` 의 `claudeMdExcludes` 가 `.claude/rules` 를 가리키면 INFO 1건. `ask/SKILL.md`·`scope-exploration.md` 에 「Explore 결과에는 도메인 포인터가 실리지 않는다 — 결론만 받아 메인에서 도메인 문서를 Read」 1줄.

### C7 — 다중 도메인 겹침을 하네스에 넘기고 생성 측 완화가 없다
- **severity**: suggestion
- **category**: risk
- **plan 인용**: §3.1 「다중 도메인」 `:57` 「런타임 상한은 둘 수 없다 — 파일당 500자 캡이 총량 상한(3도메인 ≈ 1.5K). #30 의 "최대 2 도메인 + 그 외 N" 은 C2 전용 규칙이라 폐기」 · #30 예외 케이스 `:33`(C1/C2 구분 없음)
- **챌린지**: 인용 추정은 도메인마다 공유 디렉토리를 집계한다. learn 산출물 형태의 합성 2도메인(심볼 앵커 인용, 각 7건): `wms` → `app/models/**`·`app/services/wms/**`, `billing` → `app/models/**`·`app/services/billing/**` — `app/models/order.rb` Read 에 두 규칙이 모두 발화. Rails 류에서 `app/models`·`app/controllers/api`·`config`·`spec` 은 거의 모든 도메인이 인용하므로 도메인 N 개면 공유 파일 1개 Read 에 N × ~400자가 순위 없이 쌓이고, 가장 관련 있는 도메인이 무엇인지는 사라진다. fixture 실측의 `workspace/context/**` 처럼 지식 디렉토리 자체를 잡는 glob 도 나온다. #30 의 2도메인 캡은 "C2 전용" 이 아니라 예외 케이스 공통 항목이며, 런타임에 못 두면 생성 시점에 둬야 한다.
- **제안**: 생성 측 배타 규칙 — (a) `workspace/**`·`.claude/**`·config `Ignore`·`test_path_convention` 접두는 항상 제외, (b) 두 도메인 이상이 같은 디렉토리를 요구하면 인용 점유율이 가장 높은 도메인에만 배정(동률이면 둘 다 제외 + INFO 「공유 경로 — index 참조」), (c) doctor: `pilot-*.md` 간 `paths` 겹침 INFO. `rules-pointer.py --domain D` 가 단일 도메인만 보면 (b) 를 못 하므로 전 도메인 인용 집계를 한 번에 하는 `--all`(learn 이 호출)이 필요하다.

### C8 — 게이트가 보증하지 않는 것 — Phase 0 분기 누락·발화 증거의 재현성·골든 fixture 의 자기모순
- **severity**: suggestion
- **category**: test-gap
- **plan 인용**: §3.5 Phase 0 `:91` 「no-op 조건 4종 … 세션 1회 마커 / JSON 형식」 · §3.6 `:101-104` · G4 `:113` · G6 `:115`
- **챌린지**: (1) `coding-rules.sh` 실측 분기 중 테스트 목록에 없는 것: 스켈레톤 `source_root` 셀(`` `app/` · `src/main/` 등 ``)이 sed(`:38`)에 안 잡혀 fail-open 되는 라이브 config 경로(이 저장소가 바로 그 경우), `conventions_doc` 의 `예:` 벗기기 + 3후보 해석(`:63-70`), `session_id` 부재 시 마커 없이 매 Edit 발화(실측 연속 2회 출력), `CLAUDE_PLUGIN_ROOT` 미설정 시 메시지에 리터럴 `$CLAUDE_PLUGIN_ROOT`. (2) G4·G6 는 사람이 대화창에서 본 기록이라 재현·회귀 불가 — memory 문서가 안내하는 `InstructionsLoaded` 훅(「log exactly which instruction files are loaded, when they load, and why」)으로 dogfooding 세션에 로컬 훅 1개를 두면 규칙 파일 로드가 로그로 남는다. (3) 골든 fixture: 기대값 「`pilot/skills/**` 류」 는 C2 대로 산출 불가하고, fixture 코퍼스는 옛 플러그인 배치를 인용한다(`pilot/skills/init/SKILL.md` 8회·`skills/doctor/`·`skills/review/` — 현재 트리에 없음) — 존재 필터를 넣는 순간 fixture 인용 대부분이 탈락하므로 fixture 루트(`workspace.parent`)를 소비 레포로 두고 해석하도록 테스트가 루트를 고정해야 한다. (4) 미검증 케이스: 접기 결과 `**`·루트, 죽은 디렉토리, 도메인 간 겹침, `.claude/rules` 디렉토리 부재 시 `--write` 의 mkdir, 마커 없는 `pilot-*.md` 사용자 파일.
- **제안**: Phase 0 목록에 위 4분기 추가(총 10건). G4·G6 를 `InstructionsLoaded` 로그 라인(규칙 파일 경로 포함) 첨부로 정의. 골든은 fixture 루트를 소비 레포로 두고 기대값을 알고리즘 결과로 재계산해 커밋(JSON, `golden-expected.json` 선례). (4) 의 테스트 4건 추가.

### C9 — #30 을 바꾸는 항목이 변경 목록에 없고, 「#28 선례」 는 import 방향이 반대다
- **severity**: nit
- **category**: doc-drift
- **plan 인용**: §3.3 `:80` 「`features/30-…` § 실측 기록 기입 + C1 확정」 · §3.4 `:86` · §3.1 `:57` 「폐기」 · §3.3 `:78` 「gitignore WARN 은 두지 않는다」 · `:73` 「doctor 가 같은 함수를 import 해 호출 — 판정 1벌 원칙, #28 선례」
- **챌린지**: 플랜이 바꾸는 #30 조항 — 예외 케이스 「최대 2 도메인 + 그 외 N」(`:33`) 폐기, 「gitignore … doctor WARN」(`:36`) 삭제, doctor 검사 3종 → 4종(`--check` 불일치·마커 없음 INFO 추가, `paths↔sources` INFO 를 `--check` 로 흡수), 검증 기준 「frontmatter `paths` 3줄 이내」(`:59`) vs 플랜 ≤ 8 globs, 「공통 디렉토리 접두 glob」 vs `dir/**` 목록, C2 폐기 — 는 「실측 기록 기입」 으로 덮이지 않는다. 「#28 선례」: #28 판정은 `integrity.py` 안의 `check_context_citations_stale`(`:1182`)이고 저장소의 재사용 방향은 도구 → `doctor._common`(orchestrate-load·context-search 모두)이며 doctor 패키지에는 importlib 사용이 없다 — 하이픈 파일 `rules-pointer.py` 를 doctor 가 import 하려면 그 선례가 아니라 새 importlib 경로가 필요하다(테스트도 `sys.path` + 패키지 import 패턴, `test_doctor_citation_drift.py:29-33`).
- **제안**: §3.4 의 #30 항목을 조항별로 열거(요구사항 doctor 줄·예외 2건·검증 기준 1건·C2 상태). 판정 함수는 `pilot/tools/doctor/rules_pointer.py`(패키지 모듈)에 두고 `pilot/tools/rules-pointer.py` 는 CLI 래퍼로 — 방향이 기존과 같아지고 importlib 이 필요 없다.

### C10 — 캡 산정 기준이 없고(주입문에는 frontmatter·주석이 없다), doctor (a) stale WARN 과 (d) 마커 없음 INFO 의 우선순위가 없다
- **severity**: nit
- **category**: edge-case
- **plan 인용**: §3.1 `:55` 「포인터 3~8줄 · 본문(frontmatter 제외) ≤ 500자 · 관리 마커 1줄」 · G4 `:113` 「주입 텍스트 ≤ 500자」 · §3.3 `:78` (a)·(d)
- **챌린지**: 프로브 a 의 주입 블록은 마커 문장 1줄뿐 — frontmatter 와 `<!-- … -->` 는 하네스가 벗긴다(memory 문서 「Block-level HTML comments … are stripped before the content is injected」). 그러므로 관리 마커는 모델에 닿지 않고 캡에도 들어가지 않아야 하는데 플랜은 마커를 줄 수에 넣는다. §3.1 템플릿을 채운 실측: wms 예시 6줄·263자(마커 제외) · `pilot` 라이브 4줄·181자 · 최대 세트(index+rules+본문 2+경계 2+검색, learn 식 이름 `coupon_service`·`coupon_service--order_management`) **9줄·마커 제외 496자·562B, 마커 포함 585자** — 「그 외 N개」 줄이 붙으면 500 초과이고, 검색 줄 하나가 115자(23%). 단위(자/바이트)도 없다. doctor: 사용자가 만든 `.claude/rules/pilot-conventions.md`(마커 없음)는 파일명 도메인 `conventions` 가 MANIFEST 에 없어 (a) 「stale WARN·삭제 제안」 과 (d) 「사용자 관리 INFO」 에 동시에 해당한다.
- **제안**: 캡 = 주입되는 본문(frontmatter·HTML 주석 제외) ≤ 500자(문자 수) · ≤ 8줄, 마커는 별도 1줄로 명시; 검색 줄을 C4 제안대로 줄이면 여유 ~70자. doctor 는 마커 없는 파일을 먼저 걸러 (d) 만 내고 (a)(b)(c) 는 마커 파일에만 적용한다고 1줄.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | v2 §0·§2.3 — Read 만 발화 인정. 최소 보완 훅 `domain-pointer.sh`(PostToolUse Edit\|Write, 규칙 파일 `paths:` 대조, 세션·도메인당 1회, ≤2 도메인, 본문 없음). `coding-rules.sh` 무변경 + 회귀 테스트 10건. "보완" 서술 삭제 |
| C2 | accepted | v2 §2.2 — doctor #28 인용 해석 체인으로 실파일만 집계, 하위 트리 합산 + 탐욕 분할(8개·커버리지 90%), `**`·`workspace/**`·`.claude/**`·Ignore·test_path_convention 제외, 해석 <2 skip |
| C3 | accepted | 마커 주석·learn INFO·doctor 힌트에 "세션당 1회 로드 — 재생성분은 새 세션부터" 명시 |
| C4 | accepted | 상세 조회 줄을 `/pilot:ask (메인) · wrapper-protocol §6 3단계 (래퍼)` 로 — 치환 변수 없음 |
| C5 | accepted | MANIFEST 등록 후·doctor 직전 `--all --write`, 미등록 도메인 exit 2(폴백 없음), Boundary 모드 동일, batch 표현 삭제 |
| C6 | accepted | 실측 기록 종류별 명시(메인·general-purpose ✓, Explore/Plan 문서상 skip, `claudeMdExcludes`·`--setting-sources` 미검증) · doctor `claudeMdExcludes` INFO · ask·scope-exploration 1줄 |
| C7 | accepted | `--all` 전 도메인 집계, 동일 glob 은 하위 트리 최대 도메인에만·동률 제거 + INFO, doctor 규칙 파일 간 동일 glob INFO. 제외 접두 workspace/·.claude/·Ignore·test_path_convention |
| C8 | accepted (부분) | Phase 0 10건(4 분기 추가). G4 는 프로브 절차·주입 원문을 #30 실측 기록으로 — `InstructionsLoaded` 로그는 후속(환경 계측 필요) |
| C9 | accepted | 판정·생성 로직 `doctor/rules_pointer.py`, `tools/rules-pointer.py` 는 CLI 래퍼. #30 조항 변경 v2 §6 열거 |
| C10 | accepted | 캡 = 주입 본문(frontmatter·주석 제외) ≤500자·≤8줄, 마커 별도. doctor 는 마커 없는 파일 INFO 만 먼저 |

> 합의 기입: 2026-09-09 계획 작성 에이전트 — 처리 내역은 `…-plan.r2.md` §0.
