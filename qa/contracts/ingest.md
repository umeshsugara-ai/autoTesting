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
- Real live calls to Gemini in the default test suite — `tests/test_ingest.py` uses `MockProvider`
  exclusively; `GeminiProvider` itself is exercised only for `available()`/error-path shape.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-060's video-ingest half — no contract existed
  before this cycle.
