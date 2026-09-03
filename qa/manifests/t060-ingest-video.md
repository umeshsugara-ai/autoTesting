# Manifest — t060-ingest-video

**Contract:** qa/contracts/ingest.md (I1–I5, new this cycle) + qa/contracts/core-invariants.md
**Goal task:** T-060 (`user_value: high`) — this cycle delivers the video-ingest half only, per
the contract's own no-fire list (doc ingestion and the real golden test are separately deferred)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (advances a previously-blocked task)

## Why this unit, and the honest limit on what it can deliver

Umesh: "you are /maker so do the needful. dont wait for my permission. dont stop until you
achieve the /goal." T-060 was blocked all session on "no Pathlynks demo video exists in this
repo" — that fact hasn't changed; I cannot manufacture a real video. What I *can* do without one:
build and fully test the actual ingest pipeline (the Gemini vision provider, the video→FlowSpec
mapping, provenance tracking) against a `MockProvider` standing in for what a real video-watching
call would answer — exactly the same pattern used for T-050's grading before a working judge
existed, and for every other stage in this codebase. The golden-test acceptance
(">=90% step recall vs a hand-written list on a real demo video", named in T-060's own goal-task
note) stays honestly undeliverable until a real video lands — that limit is named explicitly in
`qa/contracts/ingest.md`'s no-fire list, not smoothed over.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-060 providers/gemini.py + stages/ingest.py: video
ingestion half"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for ingest. Wrote `qa/contracts/ingest.md` (I1–I5) before writing any code,
explicit that this is the video-ingest half of T-060 only.

## Real validation performed before committing to the provider design

Live-tested Gemini's structured-output mechanism against the real `GEMINI_API_KEY` before writing
`GeminiProvider` (same discipline as T-055's live LangChain validation):
```
$ uv run python -c "... genai.Client().models.generate_content(model='gemini-3.6-flash',
  contents='Say result=ok...', config=types.GenerateContentConfig(response_mime_type=
  'application/json', response_schema=Answer))"
result='ok' reason='structured output works'
```
Confirms the `response_schema` + `.parsed` mechanism `GeminiProvider._structured` relies on is
real, not assumed. Did not upload a real video (none exists) — the `client.files.upload` call
path is written per the SDK's documented API but is exercised in tests only via `MockProvider`,
never live, per the contract's no-fire list.

## What changed

- `qa/contracts/ingest.md` (new) — I1 (only-observed content, deterministic ids) · I2 (every
  step's `SourceRef` carries the video timestamp) · I3 (entry_screen resolves to a real screen id
  when it matches) · I4 (a real provider call, video path passed not inlined) · I5 (prompt is a
  file).
- `src/autotester/schema/flowspec.py` — added `ObservedStep`, `ObservedFlow`, `ObservedScreen`,
  `VideoObservation` (the vision model's raw structured answer, mapped into `FlowSpec` by the
  stage — kept separate from `FlowSpec`/`Step`/`Screen`/`Flow` themselves so a model is never
  asked to invent ids, versions, or provenance it doesn't have). No existing class changed.
- `src/autotester/providers/gemini.py` (new, 82 lines) — `GeminiProvider`: `see_video`/`act`/
  `judge` all route through `_structured`, which uploads a video file (only when one is given),
  calls `client.models.generate_content` with `response_schema=<the caller's Pydantic model>`,
  and returns `.parsed`. Lazy `google.genai` import, matching `AnthropicProvider`'s pattern —
  importing this module never requires a live key.
- `src/autotester/providers/__init__.py` — registered `"gemini": GeminiProvider`.
- `src/autotester/prompts/ingest_video_v1.md` (new) — the ingest prompt: only report what was
  actually observed, plain-language targets (never a CSS-selector guess), never write down a
  real-looking credential even as an example.
- `src/autotester/stages/ingest.py` (new, 78 lines) — `ingest_video(source, project_slug,
  provider, docs=None) -> FlowSpec`. Calls `provider.see_video(Path(source.path), prompt,
  VideoObservation)`, maps observed screens/flows into content-addressed `Screen`/`Flow` objects,
  resolves each flow's `entry_screen` name to the matching screen's id when possible, and stamps
  every `Step`'s `source_ref` with the video's timestamps. Always produces a fresh `FlowSpec` —
  merging into an existing one is explicitly out of scope (no-fire list).
- `tests/test_ingest.py` (new, 6 tests) — screens/flows mapped correctly; steps carry the right
  `SourceRef` timestamps; `entry_screen` resolves to the matching screen's id; the same
  `VideoObservation` twice produces identical screen/flow ids (content-addressed, deterministic);
  a source with no path raises `ValueError`; the prompt file exists and interpolates the source
  label.
- `tests/test_providers.py` — 4 new tests for `GeminiProvider` (registry resolution,
  `available()` reflects key presence, `see_video` without a key raises without touching the
  network, missing schema raises) — same shape as the existing `AnthropicProvider` tests in this
  file.
- `docs/ARCHITECTURE.md` — two concept→file rows (`providers/gemini.py`, `stages/ingest.py`);
  Status line updated, naming the real remaining limit (no demo video) instead of implying
  T-060 is simply "blocked" with nothing built. 149 lines (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_ingest.py -v` → 6 passed
- `uv run pytest tests/test_providers.py -v` → 8 passed (4 Anthropic + 4 Gemini)
- `uv run pytest -q` → exit 0, 155 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 149 (≤ 150)
- `grep -rn "GEMINI_API_KEY" tests/` → only in `test_providers.py`, never a literal key value

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ingest.py -v
......                                                                   [100%]
6 passed
$ uv run pytest tests/test_providers.py -v
........                                                                 [100%]
8 passed
$ uv run pytest -q
................................s....................................... [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- Per the no-fire list: doc ingestion, FlowSpec merging, the review gate (T-065), and — most
  importantly — the real golden-test acceptance against actual Pathlynks footage are all
  explicitly NOT delivered by this unit. `.goal/goal.json` T-060's `done_check` is
  `uv run pytest tests/test_ingest.py -q`, which this unit satisfies; the goal task's own note
  about golden-test recall is a further acceptance bar for whenever a real video exists, not
  something this contract (`ingest.md`) claims to close on its own.
- No live Gemini video call anywhere in the default test suite; the one live validation performed
  (shown above) was a text-only structured-output smoke test run directly by the maker before
  committing to the design, not part of the automated suite.
- No secrets touched — `GEMINI_API_KEY` is read only via `os.environ` inside `_structured`, never
  printed or logged; tests use fake keys only.

## Status: checked-PASS

Reconciliation note (2026-09-03): this manifest was never flipped from ready-for-check at the time, even though qa/verdicts/t060-ingest-video.md recorded PASS and the unit shipped (see docs/FEATURES.jsonl / .goal/goal.json). Corrected during a disk-state reconciliation pass -- no re-check performed, no new claim made; the verdict file is the actual evidence, this is only the manifest catching up to it.
