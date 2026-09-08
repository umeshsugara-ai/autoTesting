# Contract — INGEST stage (T-060, video half)

**Covers:** goal task T-060 (video-ingest portion only — see no-fire list for what's deferred).
**Owner:** /checker. **Criticality:** HIGH — the entry point of the whole pipeline; everything
from T-065 onward depends on a `FlowSpec` existing.
**Depends on:** `core-invariants.md` (all).

## Purpose

Turn a demo video (a `Source`) into a `FlowSpec` — screens and flows, every step provenance-
tracked to the exact second it was observed — using a vision-capable provider (`GeminiProvider`,
the `see_video` role). This is the "video/docs → FlowSpec with SourceRefs" half of T-060's title;
the "docs" half and the full golden-test acceptance (">=90% step recall vs a hand-written list on
a real demo video") are explicitly out of scope for this contract — see the no-fire list.

## Criteria

### I1 — Screens and flows only from what was actually observed
`stages/ingest.py::ingest_video` maps a provider's `VideoObservation` (screens[], flows[]) into a
`FlowSpec` — it invents no screen, flow, or step beyond what the `VideoObservation` contains. The
mapping is deterministic: the same `VideoObservation` always produces the same screen/flow ids
(content-addressed via `content_id`, same discipline as `Case`/`Script`).

### I2 — Every step carries provenance to the second
Each `Step` the stage produces has a `SourceRef` naming the source video's id and the
`t_start`/`t_end` the vision model reported for that action — a human reviewing the resulting
`FlowSpec` can jump straight to the moment the system learned a given step.

### I3 — Flow entry_screen resolves to a real screen id when possible
When an `ObservedFlow.entry_screen` name matches one of the same observation's screen names, the
produced `Flow.entry_screen` is that screen's minted id, not the raw name — so
`FlowSpec.screen(flow.entry_screen)` actually resolves.

### I4 — The vision call is a real provider call, not text-only
`ingest_video` calls `provider.see_video(path, prompt, VideoObservation)` — the video file path is
passed to the provider, never inlined into the prompt text; `GeminiProvider.see_video` genuinely
uploads the file (`client.files.upload`) before calling `generate_content`.

### I5 — Prompt is a file, not an inline string
The ingest prompt lives at `prompts/ingest_video_v1.md`, following the project's "prompts are
files" rule; the prompt itself instructs the model not to invent unobserved content and never to
write down a real-looking credential even as an example.

### I6 - Learning is persisted, and a human's review is never discarded by accident
`stages/ingest.py::persist_ingest` writes the produced `FlowSpec` through
`ProjectStore.save_flowspec`. Before T-131 `ingest_video` returned a spec and no caller saved it,
so a recording could be watched and leave no trace on disk; producing a spec is not the
deliverable, persisting it is. Persisting blindly is the opposite defect: an existing spec at
`ReviewStatus.APPROVED` is **refused** (`FlowSpecApproved`) unless the caller passes an explicit
`replace=True` / `--replace`, because overwriting an approved spec throws away a human's
judgement and not merely data. A `DRAFT` or `NEEDS_EDIT` spec carries no such judgement and is
overwritten freely. The refusal must be genuinely non-destructive - the approved spec is still
intact on disk after the refusal, not half-written.

### I7 - Every screen names where it came from, and the video/crawl seam uses ONE templater
Each `Screen` produced from a recording carries a `SourceRef` (`source_id`, `t_start`, `t_end`)
back to the second it was read from. `url_pattern` is produced by `core.urls.url_template` - the
crawler's own function, not a lookalike - so a screen learned from a video and the same screen
found by a crawl collapse to one row instead of two. It is set **only when a url was actually
observed**; a screen with no visible address bar gets `None`, because inventing a pattern would
report coverage of something nothing has seen. Asserting the literal templated string is not
sufficient on its own: the defending test must assert against `url_template`'s own output, so the
two sides of the seam cannot drift apart silently.

### I8 - Narration is ground truth, injected, and never re-transcribed
When a `Transcript` exists it is injected into the prompt verbatim, and the prompt instructs the
model to **align** it to what is on screen rather than re-transcribe or paraphrase it: a
paraphrased complaint is a fabricated quote attributed to a real person, and this system treats a
tester's own words as evidence. When no speech exists, the prompt says so explicitly rather than
leaving a gap the model may fill.
**The template must carry the placeholder the code replaces.** `str.replace` on a missing needle
does not raise, so a template that loses `{{NARRATION}}` ships a prompt that runs blind with
nothing failing anywhere. A test defending the *template* - not only the code - is therefore part
of this criterion, not an extra.

### I9 - The upload is readable before it is used, and every SDK failure is typed
`providers/gemini_files.py::upload_and_wait` polls the Files API to `ACTIVE` before any
`generate_content` call. `files.upload` returns while the file is still `PROCESSING`, and passing
that handle onward fails sometimes loudly and sometimes as an **empty reading**, which is the
worse outcome because it is indistinguishable from a bad prompt. `FAILED` raises rather than
polling forever; a bounded timeout raises rather than hanging; every SDK exception (upload, poll,
generate) is re-raised as `ProviderError` **with its cause chained**. Truncation is reported AS
truncation: a `MAX_TOKENS` finish reason says the answer hit the output ceiling, not "structured
output did not parse", which sent the reader to their schema instead of to the chunk length.
An upload cache is permitted and must **degrade to a re-upload, never to an error**: a dead,
expired, non-`ACTIVE`, or corrupt-on-disk cache entry is a miss, not a failure.

### I10 - Sources are identified by content, and re-registering is not re-recording
`register_source` keys on the file's sha256, not its path: the same bytes registered twice return
the existing row. A shell command gets re-run by habit, and a doubled corpus would quietly skew
every recall number scored against a human's sheet. A missing file raises rather than registering
a phantom. Two different paths holding identical bytes are ONE source (the first registration's
path wins, and the second call's `label` is not applied) - the intended answer for a corpus keyed
on content, recorded here so it is a decision rather than an accident. Changed bytes at the same
path are a NEW source; the old row is never mutated, because a `SourceRef` that already points
into it must keep meaning what it meant.

## No-fire list

- **The golden test itself** (">=90% step recall vs a hand-written list on a real demo video") —
  there is no Pathlynks demo video in this repo yet (a separate, standing blocker, tracked
  outside this contract). This contract is satisfiable with `MockProvider`-seeded tests only; the
  real-video acceptance is a follow-on once a video exists.
- **Doc ingestion** (the "docs" half of T-060's title) — this contract covers video only.
- **Merging into an existing `FlowSpec`** — `ingest_video` always produces a fresh `FlowSpec`;
  conflict detection (`Conflict` model) and merge logic are a later unit's job.
- **The review gate** (`FlowSpec.review.status` draft→approved) — that is T-065, a separate task
  the plan already names.
- **Live model calls.** No criterion above requires one; the whole stage is satisfiable against
  `MockProvider`, and `upload_and_wait` is judged on its state machine and error shape rather than
  against the real Files API. Exercising the real Files API is A3/A4 territory, and that is where
  the `google-genai` declaration (AT-130, see the amendment log) must be closed.
- **`ObservedScreen.screenshot_ts`** - requested in the prompt, defined in the schema, consumed by
  nothing. It lands with frames in A3. Verified as an honest, declared gap.
- **`VisionOptions.fps` and `thinking_level`** - carried in the schema and not applied by
  `_config` today (AT-126). Out of scope for I9, which governs upload and error shape only.
- **Media prep, chunking, whisper, the ensemble and adjudication** (A3/A4), and **merging into an
  existing FlowSpec** (A6).
- Real live calls to Gemini in the default test suite — `tests/test_ingest.py` uses `MockProvider`
  exclusively; `GeminiProvider` itself is exercised only for `available()`/error-path shape.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-060's video-ingest half — no contract existed
  before this cycle.
- 2026-09-08 - routine - added I6-I10 for T-131 (Track A2) - why: folded from
  `qa/feedback-inbox.md`, where the maker filed I6-I9 and the checker authored them. Each was
  judged on the checker's own execution rather than on the maker's framing, and I10 was added
  because `register_source`'s content-identity rule is a real decision this unit made that the
  four requested criteria left ungoverned. I8's placeholder clause is kept as a *criterion* and
  not a note: sabotage C reproduces three failures, one of which exists solely to defend the
  template, and that test is the only thing standing between the system and a prompt that ships
  without narration while every other test stays green. I9 gained the cache-degradation clause
  after probing - a dead handle, a `PROCESSING` handle, an expired entry and a corrupt cache file
  all fall back to a re-upload, and that is now required rather than incidental.
  **Ruling on the maker's first offered judgement (`google-genai` left undeclared in
  `pyproject.toml`, contrary to plan section 4 A2):** the omission is a real deviation from an
  approved plan, filed as AT-130, but it does not fail this unit. The maker's stated reason is
  partly wrong - `google.genai` IS importable in this environment today (verified), so the
  provider is not dead code - and that is the actual hazard: it resolves only as a transitive
  dependency of `langchain-google-genai`, so `GeminiProvider` works by the accident of somebody
  else's pin, which is exactly what a direct declaration exists to prevent. It must be closed in
  the unit that first calls the API for real (A3), and the no-fire list now names that so the debt
  cannot go quiet.
  **Ruling on the second (a hygiene line banning `git checkout` as a sabotage-restore while work
  is uncommitted):** upheld in substance, refused in this location. A feature contract judges the
  artifact, not how the maker held the tools; AT-101 already records this class against the
  `living-ledger` feature, and the extension belongs there - filed as AT-131. Verified
  independently that nothing was in fact lost to the accident: the committed prompt diff is a
  coherent 29-line rewrite carrying the full "align, never re-transcribe" section and exactly one
  `{{NARRATION}}` placeholder, not a degraded retype.
