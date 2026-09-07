# AutoTester — build plan: logged-in testing, learning from recordings, autonomous exploration

**Root:** `d:\autoTesting` · **Date:** 2026-09-07 · **Approver:** Umesh
**Supersedes:** the 2026-09-07 morning version of this file (Track 0 shipped; Tracks A/B were
sketches). This version is the executable plan. **After approval it is copied verbatim to
`d:/autoTesting/plan.md`** (Umesh: *"make its detailed plan and save it in plan.md"*) and every unit
below becomes a `.goal/goal.json` task so the maker can drive it — the plan must not live only
outside the repo again.

---

## 1. Context — why this plan exists

Umesh's critical review (2026-09-07 afternoon) established, verified against disk:

| Done | Not done |
|---|---|
| 53 checker-PASSed units, 32 ledger features | ERP credentials still unset → **0 logged-in ERP runs** |
| Core loop proven on Pathlynks (real login, independent multimodal judge) | Track A (video learning): **not started** — ingest has zero callers, never persists; no upload; no ffmpeg/whisper; Gemini SDK undeclared; corpus not mounted |
| Full UI: dashboard, onboarding, settings, cases CRUD, credentials page, live view, reports, diagrams | Track B (explorer): **not started** — no DOM observation, no back action, 7 actions, `write_policy` read by no code, nothing prevents a Delete click |
| Track 0 release-approved after 6 checker rounds, 38 hostile probes ×2 | Governance out of sync: goal backlog shows 20/20 done and **empty**; the plan's units exist only in this file → the maker would report `BACKLOG_EMPTY` and stop |
| AT-052 gate answered on disk | Housekeeping: `.goal/*` + `goal.md` modified but uncommitted; `projects/erp/` untracked; sweep 20 h overdue; `qa/QUEUE.md` still shows the answered AT-052 grill as blocking |

Umesh's instruction: *"mere bhai ye sabb tho plan krkee build krr properly"* — plan all of it and
build it properly. His scoping answers (already on disk in `qa/gates/at052-bfs-video-corpus-grill.md`):
all three tracks in parallel; explorer bounded by the test account's own permissions; credentials
typed in the platform; outputs = product map, test cases, issues Excel, end-to-end flow. New answers
this session: **test accounts have no 2FA** (only real user accounts such as Karun's and Shubi's do,
and those are never used — CLAUDE.md forbids live-user credentials); **no staging ERP named → assume
production, READ_ONLY**; **commit `projects/erp/`** like the other three projects.

Three corrections found while planning, stated up front so no manifest overclaims:

1. **`erp1/2/3.mp4` are NOT the recordings behind `ERP_Issues_ALL.xlsx`.** They are 30 s / 15 s /
   33 s trainer-module clips; their ground truth is **`ERP_Issues_Trainers.xlsx`** (sheet "Trainer
   module", 7 rows, `Clip` column names them). `ERP_Issues_ALL.xlsx`'s 33 rows belong to ManishSir4
   (22 rows; only two cached chunks exist), Shiv_18Aug_a/b (7), Shiv_17Aug_130019 (2), one mailed
   screenshot, three "verified fixed" rows. Scoring is therefore **per corpus**, and the "32 issues"
   figure in the earlier plan is not achievable from erp1/2/3.
2. **10 of 33 ALL rows are "Feature gap"** (spoken change requests), plus "Wrong model" ×3. The
   prior-art 12-category taxonomy has no home for them; the issue vocabulary must add
   `feature_gap`, `wrong_model`, `data_error` or recall is structurally capped near 50 %.
3. **Adding `Action` members breaks `execute.py:52`** (`_ACTIONS[step.action]` KeyErrors inside a
   run). The enum change and a `.get()` guard must land in the same unit.

Verified environment facts that shape the design: host has `ffmpeg 8.1.1`, `faster_whisper 1.2.1`,
a CUDA GPU and the 9.3 GB corpus; the container has **no ffmpeg, no GPU**, and the repo is
bind-mounted at `/app`. Existing sidecars `erp*.transcript.json` = `{segments:[{start,end,text}],
speech_seconds}`. `session.py` is at 284/300 lines; `app.py` 293; `ARCHITECTURE.md` exactly 150
(its cap); `DECISIONS.md` ends at D-013; goal ids end at T-120; `doctor` caps test files too,
fails on stale `docs/MAP.md`, and `check_root_clean` rejects any root file not in
`ALLOWED_ROOT_ENTRIES` (so `plan.md` needs one line added there).

---

## 2. Id bands, decisions, and order of work

| Band | Track | Units |
|---|---|---|
| T-121..T-123 | G — governance + Track 0 tail | register plan · login case + first logged-in run · medium-issue batch |
| T-130..T-136 | A — learn from recordings | A1..A6 + acceptance |
| T-140..T-145 | B — autonomous explorer | B1, B2, B4, B3, B5 + live demo |

Decisions to append (via `powershell -File scripts/append_decision.ps1 -EntryFile <f>`, in order):
**D-014** Track A schema + shared `Action` additions · **D-015** Track B stage/contract/schema ·
**D-016** `write_policy` runtime matrix. Full text in §7.

**Maker order (one unit per tick, A and B interleaved so both tracks move):**

```
T-121 (governance, same turn as approval)
 └─ T-122 ERP login run  [HUMAN_GATE until ERP_EMAIL/ERP_PASSWORD have values]
D-014 ─► A1 ─► B1 ─► A2 ─► B2 ─► A3 ─► D-016 ─► B4 ─► A4 ─► D-015/explore.md ─► B3 ─► A5 ─► B5 ─► A6 ─► T-136 ─► T-145
T-123 (medium issues) slots in whenever a track is blocked on a checker.
```

Every unit ships through maker-checker: contract criteria requested in `qa/feedback-inbox.md`
(checker writes them) → manifest with **the source diff committed, not paperwork only** (AT-055
recurred five times) → fresh `/checker` → verdict → close-out → `autotester ledger add` for
high-value tasks. Every manifest's live evidence is taken only after the staleness guard
(container `StartedAt` newer than newest `src/**.py` mtime — AT-085).

---

## 3. Track G — governance and the Track 0 tail

### T-121 — register the plan in the repo (normal mode, same turn as approval)
- `src/autotester/doctor.py::ALLOWED_ROOT_ENTRIES` += `"plan.md"`; write `plan.md` (this file).
- `.goal/goal.json`: add tasks T-121..T-123, T-130..T-136, T-140..T-145 in the existing shape
  (`id, title, status:"pending", base_criticality, deps, done_check{type:"cmd",cmd,expect_exit:0},
  note, attempts, created, user_value`); `progress` recomputed; regenerate `.goal/dashboard.html`.
- `qa/QUEUE.md`: replace the stale AT-052 GRILL row with "answered 2026-09-07 — see gates file".
- Append D-014 (Track A can start), D-015 and D-016 (they authorise contracts/ARCHITECTURE prose).
- `git add projects/erp .goal goal.md plan.md` → commit `governance: register Tracks A/B/G (D-014..D-016)`.
- Dispatch the overdue `/checker sweep`.
- Verify: `uv run autotester doctor` clean; `python -c "import json;print(len(json.load(open('.goal/goal.json'))['tasks']))"` → 37.

### T-122 — first logged-in ERP run (HUMAN_GATE: values entered on `/projects/erp/env`)
- Gate check each tick: `SecretStore.has_value("ERP_EMAIL") and has_value("ERP_PASSWORD")`.
- Add via the UI (or `ProjectStore.add_case`) the login case: NAVIGATE base_url → FILL email
  `{{SECRET:ERP_EMAIL}}` → FILL password `{{SECRET:ERP_PASSWORD}}` → CLICK "Sign in" → ASSERT
  expected `url` contains the post-login path. Selectors from a one-off headed inspection.
- Run from the Run button; expected: `Outcome.COMPLETED`, judge `PASS`, password field masked in
  every screenshot (`data-autotester-secret`), zero `.env` values in `projects/erp/runs/**`.
- Verify: `grep -rF "<value>"` is never run by an agent; instead
  `scripts/scan_runs_for_secrets.py`-style check = `Redactor.is_clean` over every run file → clean.
- Also registers the reusable **login bootstrap case id** that B3 needs.

### T-123 — medium-issue batch (one unit, contract `ui.md` U8/U9 amendments)
- AT-087: `exempt` becomes per-field (`dict[label, str]`) in `_refuse_unsafe_submission`.
- AT-076/AT-086: base_url/allowed_domains are config fields — exempt from credential matching
  **only** when the matched `.env` key is not a declared `SecretRef` of any project AND the value
  parses as a URL/host (fails closed otherwise). Onboarding a project whose URL is in `.env` works.
- AT-079/AT-080: pass `slug` and secret `key` through the guard too.
- AT-065: stamp the 4 legacy rubrics with provenance once (`scripts/stamp_legacy_rubrics.py`).
- AT-085: the staleness guard becomes `scripts/live_guard.py` and every manifest cites its output.
- Verify: `uv run pytest tests/test_ui_credential*.py -q`; live probes from the cycle-3 checker list re-run.

---

## 4. Track A — learn from screen recordings

### Decisions baked into Track A
- **Media prep runs on the host** (`autotester media prep`), writing chunks/transcript/frames under
  `projects/<slug>/sources/<source_id>/` which the container sees through the bind mount. The
  container never needs ffmpeg or a GPU, and the 9 GB corpus is never mounted or copied. Existing
  sidecars are loaded byte-for-byte; whisper runs only when no sidecar exists, in an isolated
  subprocess (ctranslate2 teardown crashes parents). *Rejected:* ffmpeg in the Dockerfile + corpus
  mount — fixes chunking, not whisper, and makes a host folder a hidden container dependency.
- **Ensemble = `gemini-3.1-pro-preview` + `gemini-3.8-flash`** (Umesh's own words in `goal.md`:
  "Gemini three point one pro or Gemini three point eight flash… combination"). `gemini-3.6-flash`
  (best in the 18 Aug benchmark) stays one `--models` flag away. Settings from the proven pipeline:
  `seed=7`, `max_output_tokens=65536`, `media_resolution=HIGH`, `thinking_level=high`, `fps=2.0`.
- **Determinism boundary:** raw per-model observations are cached on disk and never re-requested
  without `--force`; everything after (seam merge, interval join, issue derivation, ids, Excel) is
  pure code over sorted inputs → byte-identical on re-run. Tests assert it, including shuffled input.
- **`Issue` is its own artifact**, never a `CaseClass` (D-005's rejection stands).
- Artifact layout (C6, every kind = schema model + `ProjectPaths` property + `ProjectStore` method):

```
projects/<slug>/sources.jsonl                                  Source rows (existing)
projects/<slug>/sources/<sid>/media.json                       MediaPrep (probe + chunk manifest)
projects/<slug>/sources/<sid>/transcript.json                  Transcript
projects/<slug>/sources/<sid>/chunks/chunk_NN_<off>s.mp4       gitignored
projects/<slug>/sources/<sid>/observations/<label>__<prompt>__<NN>.json   raw model cache
projects/<slug>/sources/<sid>/analysis.json                    VideoAnalysis (adjudicated)
projects/<slug>/sources/<sid>/frames/<t_ms>.png                gitignored
projects/<slug>/issues.jsonl · screenmap.json · flowspec.json
```

### A1 — schema + storage foundation (T-130, needs D-014) · ~350 lines
- `schema/enums.py`: `Action` += `BACK, HOVER, PRESS_KEY, SCROLL` (discharges D-005; shared with B1);
  new `IssueCategory` (12 prior-art + `feature_gap, wrong_model, data_error`), `IssueOrigin`
  (spoken/screen/spoken_and_screen/model_detected), `IssueStatus`, `Confidence`.
- **New** `schema/observation.py`: move `ObservedStep/Flow/Screen`, `VideoObservation` out of
  `flowspec.py` (in-place move; flowspec.py is at 202) and extend — `ObservedScreen` += `t_end, url,
  purpose, fields, ui_elements, screenshot_ts`; `ObservedStep` += `on_screen_text, narration`;
  `ObservedFlow` += `exit_screen`; new `ObservedIssue(t_start, t_end, screen, category, severity,
  confidence, title, what_is_wrong, on_screen_text, narration, origin)`; `VideoObservation` +=
  `issues, summary, open_questions`; `VisionOptions(fps, seed, max_output_tokens, media_resolution,
  thinking_level, temperature, system_instruction)`; `ModelObservation(Artifact)`.
- **New** `schema/media.py`: `TranscriptSegment`, `Transcript(Artifact)` with
  `from_sidecar(path, source_id)` (loads the exact sidecar shape) and `slice(offset_s, length_s) -> str`
  (`[MM:SS-MM:SS] text`, clip-relative); `MediaChunk`, `MediaPrep(Artifact)`.
- **New** `schema/analysis.py` (`AnalysedScreen`, `AnalysedIssue`, `JourneyStop`, `VideoAnalysis`),
  `schema/issue.py` (`Issue(Artifact)` — content id over project/source/screen/category/5-s bucket/
  normalised title; fields mirror the 13 Excel columns + `models_agreeing`, `status`, `human_id`),
  `schema/screenmap.py` (`MappedScreen`, `Journey`, `ScreenMap`).
- `flowspec.py`: `Screen` += `source_ref`; `FlowSpec` += `app_overview`. `project.py`: `Source` += `recorded_on`.
- `core/paths.py` (+~35) and `store/project_store.py` (+~70): the properties/methods for every kind above.
- `stages/execute.py`: `_ACTIONS.get(step.action)` → `StepNotExecutable` → `ERRORED` (no traceback).
- `.gitignore`: `projects/*/sources/*/chunks/`, `projects/*/sources/*/frames/`.
- Tests: `tests/test_schema_video.py` (roundtrips, `extra="forbid"`, `from_sidecar` on a copied
  `tests/fixtures/erp1.transcript.json` → 6 segments / 22.0 s, `Issue.id` stable), store tests,
  execute SCROLL → ERRORED.
- Verify: `uv run pytest tests/test_schema*.py tests/test_store.py tests/test_execute.py tests/test_ingest.py -q && uv run autotester map && uv run autotester doctor`

### A2 — hardened vision provider + source registration + ingest that persists (T-131) · ~400 lines
- `providers/base.py`: `see_video(path, prompt, schema, options: VisionOptions | None = None)`;
  `Provider.label` = `id:model`.
- **New** `providers/gemini_files.py`: `upload_and_wait(client, path, cache_path, timeout_s=600)`
  (poll PROCESSING→ACTIVE, FAILED→`ProviderError`, 46 h reuse cache at `.work/gemini_uploads.json`);
  `video_part(file_obj, fps)`. `providers/gemini.py`: `_config(schema, options)` (3.x: HIGH +
  thinking; else temperature+budget; always seed/max tokens), every SDK error → `ProviderError`,
  `MAX_TOKENS` → `ProviderError("truncated — shorten the chunk")`.
- `pyproject.toml`: declare `google-genai>=2.22.0`.
- `stages/ingest.py`: `register_source(store, path, *, label, recorded_on) -> Source` (sha256 via
  `core.ids.file_sha256`, absolute path, idempotent); `ingest_video(..., transcript=None, options=None)`
  keeps `t_start` as `Screen.source_ref`, sets `url_pattern` via **new `core/urls.py::url_template`**
  (shared with B2: `/trainers/123` → `/trainers/{id}`), `fields`, `app_overview`;
  `persist_ingest(store, spec, *, replace=False)` refuses to overwrite an APPROVED spec.
- **New** `cli_video.py` (cli.py is at 223): `ingest register|list|run`; mounted as `autotester ingest`.
- `prompts/ingest_video_v1.md` rewritten in place: `{{NARRATION}}` block ("align, never
  re-transcribe" / "no speech detected — do not invent dialogue"), asks for `url` when the address bar
  is visible, `fields`, `ui_elements`, `screenshot_ts` (2–4 stable frames), keeps the no-credential rule.
- Tests: fake client PROCESSING→ACTIVE (3 gets), FAILED→error, config for a `gemini-3.x` name, sha256
  stability, `ingest run --provider mock` writes `flowspec.json`, approved-spec refusal, url templating.
- Verify: unit tests + live on host: `uv run autotester ingest register erp "…/erp1.mp4" --label "erp1.mp4 (Divya Kamboj, trainer pipeline)" --recorded-on 2026-08-18 && uv run autotester ingest run erp <sid>` → `flowspec.json` with ≥1 screen carrying `source_ref` (manifest pastes the JSON head).

### A3 — host media prep: probe, chunks, transcript reuse/whisper, frames (T-132) · ~350 lines
- **New package** `src/autotester/media/` (subprocess ffmpeg only): `probe.py` (`ffmpeg_available`,
  `probe`), `chunks.py` (`plan_chunks(duration, chunk_s=180, overlap_s=15, min_tail_s=10)` pure;
  `encode_chunks` = accurate-seek re-encode `-c:v libx264 -preset veryfast -crf 22`),
  `transcribe.py` (`find_sidecar`, `transcribe_subprocess` large-v3-turbo CUDA int8_float16 → CPU
  int8 fallback → `False` when not importable; `__main__` for the isolated run), `frames.py`
  (`extract_frame(video, t_s, out_png)`, `frame_name(t_s)` = `00012300.png`).
- `stages/media_prep.py`: `prepare(store, source, *, chunk_minutes=3.0, overlap_s=15.0,
  use_whisper=True) -> MediaPrep` — degrades without ffmpeg to a single chunk on the original path,
  without whisper to `Transcript(engine="none")`; `extract_frames(store, source, analysis)`.
- `cli_video.py`: `media prep|frames`. `pyproject.toml`: `[project.optional-dependencies] media = ["faster-whisper>=1.2.1"]`.
- Tests: `plan_chunks(30)→[(0,30)]`, `(400)→[(0,180),(165,180),(330,70)]`, tail drop; degrade paths
  with `ffmpeg_available` monkeypatched; ffmpeg-dependent tests `skipif` and use a 3 s `lavfi testsrc` clip.
- Verify: unit tests + live `uv run autotester media prep erp <sid>` → `media.json`, `transcript.json`
  identical to `erp1.transcript.json` (manifest pastes a diff), `chunks/chunk_00_0s.mp4`.

### A4 — two-model ensemble, deterministic adjudication, Issue derivation, 13-column Excel, scorer (T-133) · ~400 lines
- **New** `prompts/video_issues_v1.md`: bug sweep with the extended taxonomy, verbatim contract,
  "a tester saying *this should be X / remove this / this is wrong* is `feature_gap`/`wrong_model`
  even when the screen looks fine", `taxonomy_sweep_done`. Two prompts × two models per chunk.
- **New** `stages/analyze_video.py`: `observe_chunk`, `observe_all` (skips cached files; token
  sanity warning when `prompt_tokens < 0.5 × expected`), `analyze(store, source, providers, docs, *,
  overlap_s, force) -> VideoAnalysis`.
- **New** `stages/adjudicate.py` (pure): `shift`, `merge_seams` (same casefold screen across a seam
  → extend `t_end`; steps/issues in the overlap with `|dt| ≤ 10 s` and same action/category → drop
  later), `screen_key`, `join_screens` (same key + overlapping interval → one screen, `models_agreeing`
  = distinct labels), `join_issues` (same screen + category + `|dt| ≤ 10 s` → merge, max severity,
  HIGH confidence when ≥2 agree), `join_journey`, `adjudicate(observations, source, overlap_s=15)`.
- **New** `stages/issues.py`: `derive_issues(analysis, source, project)`, `ISSUE_COLUMNS` = exactly
  `ID, Date, Severity, Type, Title, What is wrong, How we know, Confirm first, Said verbatim,
  Recording, At, Screenshot shows, Evidence`; `export_issues_excel(slug, out)` (sheet "All issues",
  `At` as MM:SS, severity words High/Medium/Low/Fixed); `autosize_columns(ws)` extracted from
  `report_export.export_excel` and shared (one concept, one place).
- `cli_video.py`: `ingest analyze --models --force`, `issues derive|list|export`.
- **New** `scripts/score_video_issues.py`: `--truth <xlsx> --sheet <name> --map <clip>=<sid>…
  --window 20 --threshold 0.30 --bench`; matching = same source, `|At − at_s| ≤ window`, best
  `SequenceMatcher` ratio on title+what-is-wrong, greedy, each truth row once; prints JSON
  `{recall, matched, missed, false_positives, per_row}`; `--bench` persists `BenchCorpus`/`BenchTrial`
  and prints `stages.bench.scorecard` (numbers only from `BenchTrial.score`, K3).
- Tests: byte-identical `adjudicate` on same and shuffled fixtures; seam extension; "Edit Trainer
  drawer"/"edit trainer Drawer" at 3–14 s / 2–15 s → one screen, agreeing=2; issues 8 s/15 s merge,
  8 s/30 s don't; `observe_all` with MockProvider makes 4 calls then 0; Excel header == 13 columns;
  scorer on a 3-row tmp workbook → recall 2/3, 1 FP, `detection_rate == 2/3`.
- Verify: unit tests, then live: analyze erp1/2/3 → derive → `issues export --out .work/erp-issues.xlsx`
  → `score_video_issues.py --truth ".../ERP_Issues_Trainers.xlsx" --sheet "Trainer module" --map erp1.mp4=<id1> …`
  → manifest pastes recall x/7 and FP count, then re-runs analyze without `--force` and shows
  `analysis.json` sha256 unchanged.

### A5 — the four outputs on screen (T-134; split A5.1/A5.2 if > 400 lines)
- **A5.1** `stages/product_map.py::build_screen_map` (folds every analysis by `screen_key`; `frame_ref`
  only when the PNG exists; journeys per recording) + `attach_screenshots(spec, screen_map)`;
  `ui/routes_product_map.py` (`GET /projects/{slug}/product-map` card grid + journeys as linear
  `.flow-tree` chains; `GET …/frames/{sid}/{name}` with `_require_safe_id` and `^\d{8}\.png$`);
  `ui/routes_issues.py` (`GET …/issues` table in `ISSUE_COLUMNS` order, `GET …/issues.xlsx`;
  `_reserved_temp_path` moves from `routes_report.py` to `ui/helpers.py`).
- **A5.2** `ui/routes_sources.py` (`GET/POST …/sources`: register-by-path form + `UploadFile` form,
  label guarded by `_refuse_unsafe_submission`; `POST …/sources/{sid}/analyze` synchronous, refuses
  with "run `autotester media prep` on the host first" when `media.json` is missing;
  `POST …/flowspec/approve|request-edit`); `app.py` moves `live_view` to `ui/routes_live.py` to free
  lines, registers the routers, `_actions_card` gains Sources / Product map / Issues;
  `routes_flow_diagram.py` adds a "Recorded journeys" card per source.
- Tests: two analyses sharing a screen → one `MappedScreen` with two visits; frames route 400 on
  `../x.png`; issues page escapes `<script>`; xlsx has 13 header cells; missing path → 400 without
  echo; approve flips status; analyze without prep → 400 with the host instruction.
- Verify: `uv run pytest tests/test_ui*.py tests/test_product_map.py -q`; live `media frames` ×3 →
  `ingest map erp` → `docker compose up -d --force-recreate` → screenshots of `/product-map`,
  `/issues`, `/flow-diagram` attached to the manifest.

### A6 — reconnect the loops (T-135)
- **New** `stages/merge_flowspec.py::merge(existing, incoming)` — first real constructor of
  `Conflict`; screens keyed by `screen_key`; conflicting url/signals keep existing **and** append a
  `Conflict` with both `source_refs`; flows/source_ids unioned; `version+1`, review back to DRAFT.
  `ingest run --merge` and the UI analyze button use it when a FlowSpec exists.
- `coverage.py`: `_path_of` → `url_template(url, keep_host=False)` on both sides (also B5's seam);
  test proving a real ingested `url_pattern` yields no gap for a matching path and one for an unseen one.
- `autotester expand <project>` CLI + `POST /projects/{slug}/expand` (approved spec only;
  `FlowSpecNotReviewed` message shown verbatim).
- `docs/ARCHITECTURE.md` under D-014: pipeline gains `MEDIA PREP → OBSERVE → ADJUDICATE`; concept
  rows for `media/`, `analyze_video`, `adjudicate`, `issues`, `product_map`, `merge_flowspec`,
  `cli_video`; Storage block extended; the Commands block collapses to a pointer to CLAUDE.md to stay at 150 lines.
- Verify: `uv run pytest -q && uv run ruff check src tests scripts && uv run autotester doctor`; live
  `flowspec approve erp --by umesh && autotester expand erp` grows `cases.jsonl`.

### T-136 — Track A acceptance (numbers, not adjectives)
Score erp1/2/3 vs `ERP_Issues_Trainers.xlsx` (7 rows) **and** Shiv_18Aug_a/b + Shiv_17Aug_130019
vs `ERP_Issues_ALL.xlsx` (9 rows; ManishSir4's 22 only if its two cached chunks are registered as a
source). Manifest reports recall and false positives per corpus, the Excel diffed column-by-column
against the human sheet, and the product map screenshot. done_check = the scorer exits 0.

---

## 5. Track B — the autonomous explorer

### Decisions baked into Track B
- **A new stage with its own contract.** `execute.md` E5 (*run_case never invents an action*) stays
  intact; `stages/explore.py` is the one place that invents clicks. Contract `qa/contracts/explore.md`
  is checker-written from the X-criteria in §7.
- **DOM-driven and deterministic by default** — no model is needed to crawl; the crawl completes
  with `provider=mock`. A model is optional and only *names* screens (B5). *Rejected:* extending
  `Provider.act` with images for vision-guided crawling.
- **Screen identity is structural**, never URL-only (prior attempt: SPAs invisible) and never an
  LLM description (prior attempt: stop condition never fired):
  `ScreenNode.id = content_id("node", {url_template, signature})`, signature = hash of sorted
  `(role, normalised name)` of visible interactive elements **excluding row/list-item data**.
- **B4 (safety) lands before B3 (crawl)** so a crawler never exists in this repo, even for one unit,
  without brakes.
- **Safety inside Umesh's boundary** (his outer bound = the account's permissions; D-016 is the
  inner guard he can loosen): READ_ONLY = deny-list on + no form submits + nothing typed;
  TEST_ACCOUNT = deny-list on, submits allowed, nothing typed; ALLOW_WRITES = deny-list off,
  nothing typed. At every policy: logout/sign-out never clicked; unnamed non-link controls skipped
  (an unnamed icon may be Delete — D-004); `beforeunload` accepted, every other dialog dismissed,
  > N dialogs on one node aborts the node; host re-check after **every** action; failed requests are
  issues only when first-party; GA/GTM/Hotjar/Sentry… dropped, other third parties counted as noise.
  The only typing on a crawl is the human-authored login case run through `run_case`.
- `session.py` has 16 lines of headroom and B1 needs ~25: `launch_options` moves verbatim to
  **new `browser/launch.py`** and is re-imported in `session.py` (test import path unchanged).
- Artifacts under `projects/<slug>/crawl/<crawl_id>/` (`crawl.json`, `nodes.jsonl`, `edges.jsonl`,
  `issues.jsonl`, `frontier.json`, `shots/` gitignored) — appended as discovered so a crash leaves a
  loadable partial graph.

### B1 — observation primitives (T-140, needs D-014/D-015) · ~380 lines
- **New** `browser/launch.py` (`launch_options` moved). `session.py`: `__init__(..., observer=None)`,
  `start()` attaches it; `current_url()`, `go_back()`, `hover()`, `press_key()`, `scroll()` — each
  records evidence via `_record`.
- **New** `browser/enumerate.js` (one `page.evaluate` → `[{role, name, selector, enabled, visible,
  href, is_form_submit, in_row, target_blank, tag}]`; selector priority `data-testid` > stable `#id`
  > `[aria-label]` > `role=…[name=…] >> nth=k` > xpath; `in_row` = ancestor `tr/[role=row]/li` with
  > 3 siblings). **New** `browser/observe.py`: `PageObserver` (installs once: `console` error/warn,
  `requestfailed`, `response ≥ 400`, `dialog`, context `page` for popups; `drain()`),
  `enumerate_elements(page)`, `observe(session) -> PageObservation`.
- Schema (minimal, extended in B2): `schema/screen_graph.py` (`ElementRef`, `PageObservation`),
  `schema/crawl.py` (`DialogEvent`). `execute._ACTIONS` gains BACK/HOVER/PRESS_KEY/SCROLL; BACK
  joins the settle set.
- **Actuator choke-point test** `tests/test_actuator_chokepoint.py`: no `.page.` / `playwright`
  outside `src/autotester/browser/` (baseline is clean today; `scripts/` excluded).
- Tests: FakePage gains `evaluate`/`on`; five listeners installed once; `beforeunload` accepted,
  `confirm` dismissed; new actions record evidence; case with the four new actions runs COMPLETED;
  real-browser (skip without Chromium): every returned selector resolves to exactly one element.
- Verify: `uv run pytest tests/test_observe.py tests/test_browser_actions.py tests/test_execute.py tests/test_actuator_chokepoint.py tests/test_browser.py -q && uv run autotester map && uv run autotester doctor`

### B2 — screen identity + crawl schema + store (T-141) · ~350 lines · pure, can run parallel to B1
- `core/urls.py::url_template(url, *, keep_host=True)` (numeric / uuid / ULID / hex≥16 → `{id}`,
  `YYYY-MM[-DD]` → `{date}`, strip query+fragment, collapse `//`, strip trailing `/`; idempotent).
  Examples pinned in tests: `https://www.vidysea.com/erp/students/123?tab=2#x → www.vidysea.com/erp/students/{id}`;
  `/erp/batch/01J8Z1…/edit → /erp/batch/{id}/edit`; `/erp/p/me` unchanged; `/students/1/ → /students/{id}`.
- `schema/screen_graph.py` += `ScreenNode(Artifact)` (`compute_id`), `ScreenEdge(Artifact)`,
  `CrawlFrontier`; `schema/crawl.py` += `CrawlBounds(max_screens=30, max_actions=200,
  wall_clock_s=600, max_depth=6, per_node_action_cap=25, dialog_repeat_limit=3)`, `SafetyPolicy`
  (`deny_patterns`, `never_click_patterns`, `third_party_ignore`, `click_unnamed=False`),
  `CrawlIssue(Artifact)`, `Crawl(Artifact)`; enums `NodeStatus`, `EdgeOutcome`
  (NAVIGATED/SAME_SCREEN/DENIED_POLICY/SKIPPED_UNNAMED/OFF_DOMAIN_REFUSED/DIALOG/ERRORED),
  `IssueKind`, `CrawlStatus`.
- **New** `stages/screen_identity.py`: `structural_signature(elements)`, `node_from(observation, crawl_id, project, depth)`.
- `core/paths.py` crawl properties; `project_store.py` crawl methods (`add_node` idempotent via cached set).
- Tests: templating table; two element lists differing only in `in_row` names → same signature,
  adding a "Filters" button → different; `compute_id` stable across element order; store round-trips.
- Verify: `uv run pytest tests/test_urls.py tests/test_screen_identity.py tests/test_store_crawl.py tests/test_schema.py -q && uv run autotester map && uv run autotester doctor`

### B4 — safety layer, pure (T-142, needs D-016) · ~300 lines
- **New** `stages/explore_safety.py`: `deny_reason(el, policy) -> str | None` (order: never-click →
  unnamed → deny-list unless ALLOW_WRITES → form-submit under READ_ONLY; default deny regex
  `delete|remove|deactivate|disable|archive|purge|drop|reset|revoke|terminate|cancel subscription|pay|checkout|send|submit|approve|reject|publish|unsubscribe`,
  word-bounded so "Deliverables" does not match), `classify_request(url, project, policy)` →
  first_party / ignored / noise, `DialogBreaker`, `policy_for(project, **overrides)`, `link_is_safe`.
- Tests (`tests/test_explore_safety.py`): table over 3 policies × {Delete, Save submit, Log out,
  unnamed button, unnamed same-domain link, "Deliverables", "Send"}; `evil.test\@vidysea.com` is
  never first-party; breaker trips on the 4th event with limit 3 and resets per node; documented
  limit: Hindi/transliterated names pass through (per-project `deny_patterns` extension).
- Verify: `uv run pytest tests/test_explore_safety.py -q && uv run autotester doctor`

### B3 — bounded BFS crawl + contract + fixture site + CLI (T-143) · ~400 lines + fixture
- **New** `stages/explore.py`: `run_crawl(project, session, store, *, bounds, policy, observer,
  login_case=None, clock=time.monotonic) -> Crawl` — `_bootstrap_login` (via `run_case`; not
  COMPLETED → `LOGIN_FAILED`), `_seed`, `_bfs`, `_stop_reason` (frontier empty / max_screens /
  max_actions / wall_clock / max_depth — named in `Crawl.stop_reason`), `_finish`.
- **New** `stages/explore_node.py`: `visit_node`, `try_action` (safe href → `goto`, else `click`;
  `settle`; `check_destination` on `current_url()` → `OFF_DOMAIN_REFUSED` + issue + recover;
  observe; drain → classified issues + noise; breaker → `ABORTED_DIALOG`; fingerprint → SAME_SCREEN
  / NAVIGATED-to-known / new node + screenshot + enqueue), `_return_to` (go_back → verify
  fingerprint → `goto(url_example)` → `goto(base_url)`); any Playwright exception → `ERRORED` edge,
  crawl continues.
- `cli.py`: `autotester explore <project> --max-screens --max-actions --wall-clock --max-depth
  --login-case --provider mock`.
- **New** `tests/conftest.py` (`serve_dir` factory on `127.0.0.1:0` reusing the no-cache handler
  idea from `scripts/regression_proof.py`; `chromium_or_skip`). **New** `tests/fixtures/crawl_site/`:
  `index.html` (nav, external link, "Open filters" same-URL toggle, login form), `students/` +
  `students/1/`, `students/2/` (must collapse to one `/students/{id}/` node), `settings.html`
  (Delete account / Deactivate / Remove user / Save / Log out → sentinel pages), `dialog.html`
  (`beforeunload` + triple `confirm()`), `reports.html` (`/api/missing` 404, GA fetch, unknown CDN
  fetch, `console.error`), sentinels `deleted.html`, `saved.html`, `logged-out.html`.
- **New** `scripts/explore_proof.py`: headed crawl of the fixture as project `crawl-demo`
  (READ_ONLY); asserts ≥6 nodes, `students/{id}/` once, zero sentinel pages, ≥3 `DENIED_POLICY`
  edges, 1 `OFF_DOMAIN_REFUSED`, dialog node aborted or ≥1 `DialogEvent`, issues contain
  `/api/missing` + the console error, GA absent. Exit 0/1 — the checker's credential-free proof.
- Tests: `tests/test_explore.py` (FakeSite transition table: BFS order + dedupe, `max_actions=3`
  stop reason, injected clock, **Delete never clicked under READ_ONLY and clicked under
  ALLOW_WRITES**, off-domain recovery, dialog storm, login failure, partial artifacts after a
  mid-crawl exception); `tests/test_explore_live.py` (headless, skips without Chromium, X3/X5/X7/X8/X9 end-to-end).
- Verify: `uv run pytest tests/test_explore.py tests/test_explore_live.py tests/test_execute.py -q && uv run python scripts/explore_proof.py && uv run autotester map && uv run autotester doctor && uv run ruff check src tests scripts`

### B5 — crawl → FlowSpec, coverage, report, UI (T-144) · ~400 lines
- **New** `stages/explore_merge.py`: `screen_from(node)` (`url_pattern=url_template`, signals =
  title + top-8 non-row names, `screenshot_ref`, `fields` from textbox/password/combobox) and
  `merge_screens(spec, nodes, project)` (existing ids untouched; name clash → `Conflict`, both kept;
  review → DRAFT; provenance names the crawl). Optional `prompts/explore_name_screen_v1.md` +
  `name_screens(nodes, provider)` — text only (template, title, element names) scrubbed through
  `Redactor` + `assert_no_raw_secrets`; skipped for `mock`.
- `coverage.py` += `diff_crawl(spec, nodes)`, `unreached_screens(spec, nodes)` (template-normalised both sides; V1 amendment).
- **New** `stages/crawl_report.py::export_crawl_excel` (sheets Summary / Screens / Edges / Denied &
  Skipped / Issues / Noise) + `crawl_summary`. **New** `ui/routes_crawls.py`: list, crawl page
  (screen tree by `discovered_by`, thumbnails via `png_base64`, denied/issue tables, stop reason),
  `report.xlsx`, `POST /projects/{slug}/explore` (synchronous like the Run button), `POST …/merge`.
  Sidebar link; `cli.py`: `report crawl`, `explore --merge`.
- Tests: merge idempotent (same fingerprint), clash → one `Conflict`, review reset; coverage with
  `/a/1` vs `/a/{id}` → no gap; workbook sheets; UI empty state, node names, data-URI image, xlsx
  content-type, merge POST updates `flowspec.json`.
- Verify: `uv run pytest tests/test_explore_merge.py tests/test_coverage.py tests/test_crawl_report.py tests/test_ui_crawls.py -q && uv run autotester map && uv run autotester doctor`

### T-145 — live bounded crawl of the ERP (after T-122 and B5)
1. Login bootstrap = the T-122 login case (`--login-case <id>`); fallback `autotester login erp` (hand login into `profiles/erp/`).
2. `AUTOTESTER_SLOW_MO_MS=150 uv run autotester explore erp --max-screens 25 --max-actions 150 --wall-clock 900 --provider mock`
   — READ_ONLY (already in `project.json`): deny-list on, no submits, logout never clicked, nothing typed. Umesh watches the visible browser.
3. Open `/projects/erp/crawls/<id>`, export Excel, `--merge` to seed `flowspec.json` screens → he reviews → `flowspec approve` → `expand`.
4. Manifest evidence: node count, denied list (what the ERP's icon-only buttons were skipped as — tells him which need `aria-label`), issues with GA absent, zero `.env` values in `crawl/**`.

---

## 6. Verification (whole plan)

- Adapter slot 1 on every unit: `uv run pytest -q` · `uv run ruff check src tests scripts` · `uv run autotester doctor` — green, plus a fresh `/checker` verdict; live figures only after the staleness guard.
- **Track 0 tail:** T-122's logged-in ERP run ends in a genuine PASS with the password masked in every screenshot.
- **Track A:** T-136's scorer output — recall and false positives per corpus as numbers; Excel header identical to the human sheet; `analysis.json` byte-identical on re-run.
- **Track B:** `scripts/explore_proof.py` exits 0 (Delete/Deactivate/Remove/Save/Log out never clicked, external link refused, dialog storm survived, GA never an issue) and T-145's real ERP crawl produces a screen graph the human can read.
- **Governance:** `.goal/goal.json` carries every unit; `docs/MAP.md`/`SNAPSHOT.md` regenerated each unit; every high-value PASS gets a `FEATURES.jsonl` row.

---

## 7. Governance texts (append in this order; D-014 before A1/B1, D-016 before B4, D-015 before B3)

### D-014 — Track A schema amendments + shared Action additions
```
## D-014 | 2026-09-07 | type: decision | status: ACTIVE
**What:** Additive schema amendments for Track A (learn from recordings), per the approved plan
(plan.md §4) and the answered AT-052 gate. (1) Discharge D-005 items: `Action` += BACK, HOVER,
PRESS_KEY, SCROLL (execute.py gains a `.get()` guard so an unhandled action is ERRORED, never a
KeyError); `FlowSpec` += app_overview. (2) Move ObservedStep/ObservedFlow/ObservedScreen/
VideoObservation from schema/flowspec.py to new schema/observation.py and extend them (t_end, url,
purpose, fields, ui_elements, screenshot_ts; on_screen_text, narration; exit_screen; issues[],
summary, open_questions) plus VisionOptions and ModelObservation. (3) New artifact kinds, each a
schema model + ProjectPaths property + ProjectStore method, plain JSON/JSONL under projects/<slug>/
(C6): Transcript + MediaPrep (schema/media.py), VideoAnalysis (schema/analysis.py), Issue
(schema/issue.py), ScreenMap (schema/screenmap.py). (4) Screen += source_ref; Source += recorded_on.
(5) New closed vocabularies: IssueCategory (12 prior-art categories + feature_gap, wrong_model,
data_error), IssueOrigin, IssueStatus, Confidence. `CaseClass` stays closed — Issue is a separate
artifact (D-005's rejection stands). Media prep is host-side ffmpeg/faster-whisper via subprocess;
every model call stays behind providers.base.Provider; prompts stay files.
**Why:** Umesh 2026-09-07: "product map, Test cases, issues excel and product flow end to end. like
all maximum learning we can take." VideoObservation cannot carry issues, urls, fields or screenshot
moments, and nothing persists what a video taught the system. Ground truth is dominated by spoken
change requests (10/33 "Feature gap") which the prior taxonomy has no home for. Additive now vs a
re-review of every FlowSpec later (D-005's own reasoning).
**Result:** units T-130..T-136 build on these; A1 is schema-only.
**Changes-authorized:** docs/ARCHITECTURE.md (Pipeline, Concept→file table, Storage, Commands,
Status — A6); qa/contracts/ingest.md (I6-I9); new qa/contracts/video-learning.md (VL1-VL8);
qa/contracts/coverage.md no-fire amendment; qa/contracts/report-export.md scope note; .gitignore;
src/autotester/doctor.py ALLOWED_ROOT_ENTRIES += plan.md.
**Approved-by:** Umesh — plan approved 2026-09-07 (plan.md), gate qa/gates/at052-bfs-video-corpus-grill.md.
**Links:** T-121, T-130..T-136; D-005; ERP_Issues_Trainers.xlsx (erp1/2/3 ground truth — the
"32 rows in ERP_Issues_ALL.xlsx" belong to other recordings)
```

### D-015 — Track B: a new stage with its own contract
```
## D-015 | 2026-09-07 | type: decision | status: ACTIVE
**What:** Build the autonomous explorer as a NEW stage stages/explore.py (+ explore_node.py,
explore_safety.py, explore_merge.py, screen_identity.py) under its own contract
qa/contracts/explore.md; execute.md E5 stays intact — run_case never invents an action, the
explorer is the one place that does. New model families schema/screen_graph.py (ElementRef,
PageObservation, ScreenNode, ScreenEdge, CrawlFrontier, ScreenNaming) and schema/crawl.py
(CrawlBounds, SafetyPolicy, DialogEvent, CrawlIssue, Crawl); enums NodeStatus, EdgeOutcome,
IssueKind, CrawlStatus. New browser modules browser/observe.py (+ enumerate.js) and
browser/launch.py (launch_options moved verbatim out of session.py, at its C2 cap). Screen identity
= content_id over (templated URL path + structural signature of non-row interactive elements),
never URL alone and never an LLM description. Artifacts under projects/<slug>/crawl/<crawl_id>/ as
JSONL; shots/ gitignored. Rejected: extending Provider.act with images for vision-guided crawling —
the crawl is DOM-driven and deterministic; a model is optional and only names screens.
**Why:** Umesh 2026-09-07: "mere bhaai ye sab tho honaa mandatory"; blast radius "jo jo uss account
mai access hoga vo krr lengee". The prior attempt failed on URL-only identity, an LLM-text stop
condition, beforeunload traps, GA noise as issues, and coverage from "did the script run" — each
is designed against in explore.md X1-X12.
**Result:** units T-140..T-145 (B1, B2, B4, B3, B5, live demo).
**Changes-authorized:** docs/ARCHITECTURE.md concept→file row for the explorer (offset by folding
the Pathlynks onboarding row into the scripts row; file stays at 150 lines) and Storage line;
.gitignore projects/*/crawl/*/shots/; qa/contracts/explore.md (new); execute.md E2 and
browser-and-secrets.md routine amendments after B1; coverage.md V1 after B5.
**Approved-by:** Umesh — plan approved 2026-09-07 (plan.md §5).
**Links:** T-140..T-145; qa/gates/at052-bfs-video-corpus-grill.md; D-005; D-014; D-016
```

### D-016 — `write_policy` enforced at runtime, explorer only
```
## D-016 | 2026-09-07 | type: decision | status: ACTIVE
**What:** Project.write_policy is enforced at runtime for the first time, by the explorer only
(stages/explore_safety.py), as an INNER guard inside Umesh's outer boundary (the test account's own
permissions). For crawler-invented actions: READ_ONLY — destructive-name deny-list ON, form-submit
controls never clicked, nothing typed. TEST_ACCOUNT — deny-list ON, submits allowed, nothing typed.
ALLOW_WRITES — deny-list OFF, submits allowed, nothing typed. At every policy: logout/sign-out never
clicked; unnamed non-link controls skipped and counted (D-004: a rule decides only where certain);
the human-authored login case run via run_case is the only pre-crawl form submit; beforeunload is
accepted, every other dialog dismissed, more than dialog_repeat_limit dialogs on one node aborts
the node; host re-check after every action (off-domain → go_back, else goto base_url); failed
requests are issues only when first-party, third_party_ignore hosts dropped, other third parties
counted as noise. No allowed_domains wildcard. Test accounts carry no 2FA (Umesh 2026-09-07);
real user accounts (which do) are never used.
**Why:** write_policy has been declared and defaulted since T-000 and read by zero code. The target
is production (no staging named), so the default is the tightest policy; ALLOW_WRITES is Umesh's
switch. The TEST_ACCOUNT row is the maker's interpretation, shown once in the B4 manifest for
confirm-or-edit.
**Result:** SafetyPolicy defaults in schema/crawl.py; tests/test_explore_safety.py; explore.md X5-X9.
**Links:** T-142; D-014; D-015; D-004
```

### Contract criteria the maker will request (checker-owned, filed via `qa/feedback-inbox.md`)
- **ingest.md I6–I9:** persists via `save_flowspec` and never overwrites APPROVED without
  `--replace/--merge`; every ingested `Screen` carries `source_ref` and templated `url_pattern`
  when a url was observed; narration injected as ground truth, never re-transcribed; upload polled
  to ACTIVE and every SDK failure a `ProviderError`.
- **video-learning.md VL1–VL8:** host prep degrades never crashes (sidecar loaded byte-for-byte);
  chunk plan 3 min / 15 s / drop < 10 s with offsets shifted in code only; raw observations cached
  (second `analyze` = zero provider calls); adjudication deterministic and non-LLM (casefold name +
  overlapping interval; same screen + category + ≤ 10 s; `models_agreeing` a count; byte-identical
  in any input order); `Issue` its own artifact, no new `CaseClass`; Excel exactly the 13 columns
  in order, `At` as MM:SS; scorer reports recall/missed/FPs as numbers with an explicit clip→source
  map and `--bench` numbers only from `BenchTrial.score`; product map derived from analyses on disk,
  `frame_ref` only names a PNG that exists.
- **explore.md X1–X12:** E5 intact; every browser touch through `browser/` (choke-point test);
  structural identity (two list pages with different rows = one node; two SPA states at one URL
  with different controls = two); bounds and stop conditions fire and are named, none depends on
  provider output; `write_policy` enforced per D-016 with the fixture proof (Delete never clicked
  under READ_ONLY, clicked under ALLOW_WRITES); session-ending controls never clicked; host
  re-check after every action with `OFF_DOMAIN_REFUSED` edge + recovery; dialog circuit breaker;
  third-party noise never an issue; nothing typed except the login case; incremental
  human-readable artifacts via `ProjectPaths`/`ProjectStore`; coverage from observed nodes only,
  merge never overwrites, clash → `Conflict`, review → DRAFT.
- **ui.md U8/U9** amendments for T-123 (per-field exemption; config-field rule).

---

## 8. Out of scope / risks stated honestly

- Gemini output is not bit-stable even with `seed=7`; determinism is claimed for the join and
  everything after it, never for the model (VL3/VL4 say so).
- Sync analyze/explore from the UI blocks the request for minutes — same trade-off the Run button
  already makes; a background runner is a later unit.
- Icon-only ERP buttons (empty accessible names) are skipped under READ_ONLY and listed in the
  report so Umesh can add `aria-label`/`data-testid` or flip `click_unnamed` on a staging build.
- Hindi/transliterated control names pass the English deny-list; per-project `deny_patterns` is the
  extension point, documented in B4.
- Not granted: `allowed_domains` wildcard; `CaseClass` expansion; filling forms with synthetic
  data; vision-guided action choice; resuming an interrupted crawl; parallel tabs; 2FA automation.
- Sizing: Track G is hours; Track A and Track B are each multi-week at one checked unit per tick.
  A4/T-136 is the first point where Track A yields something Umesh can compare to his team's sheet;
  B3's `explore_proof.py` is the first visible crawl.
