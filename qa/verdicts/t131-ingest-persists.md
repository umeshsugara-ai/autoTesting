# Verdict — t131-ingest-persists

**Unit:** T-131 — Track A2: hardened Gemini vision provider + registered Source + persisted ingest
**Commit checked:** `1c8c8e4`
**Cycle checked: 1**
**Date:** 2026-09-08
**Contract:** `qa/contracts/ingest.md` — I6–I10 **authored by this check** (see Contract authorship below)
**Bound root:** `D:/autoTesting`
**Environment:** host (Docker daemon down; `uv` runs natively). Host shows 2 skips vs the container's 1.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (T-131's done_check + 3 adapter verify commands + goal done_check exit 0),
            10/10 invariants hold (ingest.md I1–I10, I6–I10 newly authored)
FAILURES: none
ISSUES-WRITTEN: AT-125, AT-126, AT-127, AT-128, AT-129, AT-130, AT-131
EXPLANATION: Every claim in the manifest that I could execute, I executed, and all of them held —
the three sabotage transcripts reproduce character-for-character, the prior-state account is
accurate rather than inflated, the determinism claim (seed set on every call, including
options=None) is true, the APPROVED refusal genuinely leaves the reviewed spec intact on disk, and
no test in this unit can reach the network. The seven issues are all follow-on: the largest is that
no shipped caller passes VisionOptions, so the media-resolution half of the config is unreachable
from the CLI — real, but governed by no criterion this unit was built against, and A3's territory.
```

---

## What I re-ran myself

| Command | Result |
|---|---|
| `uv run pytest -q` | **607 passed, 2 skipped** — counted from the progress dots myself (8×72 + 33 = 609 tests, two `s`), not read off the maker's line. Exit 0. |
| `uv run pytest tests/test_providers.py tests/test_ingest.py -q` *(T-131's own `done_check`)* | **exit 0** |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `tests/test_ingest_persist.py` in a `git archive 1c8c8e4` scratch copy, `PYTHONPATH` pinned | 13 passed (baseline for the sabotages) |
| the 29 tests of `test_providers.py` + `test_ingest.py` + `test_ingest_persist.py` with `socket.connect`, `socket.connect_ex`, `socket.create_connection` and `socket.getaddrinfo` all monkeypatched to raise | **29 passed** — see "Honesty of the 'does NOT claim' section" |

No live-tree mutation: every sabotage ran in `git archive HEAD`-extracted scratch copies with
`PYTHONPATH` pinned, per AT-101.

## Sabotage reproduction — all three transcripts are honest (no AT-117 repeat)

| # | What I broke | What I got |
|---|---|---|
| **A** | `persist_ingest`'s APPROVED guard replaced with `if False:` | `E Failed: DID NOT RAISE FlowSpecApproved` · `FAILED tests/test_ingest_persist.py::test_an_approved_flowspec_is_never_silently_overwritten` |
| **B** | `url_pattern=url_template(observed.url)` → `url_pattern=observed.url` | `E AssertionError: assert 'https://demo...ers/123?tab=2' == 'demo.test/trainers/{id}'` · `FAILED …::test_an_observed_url_is_templated_the_same_way_the_crawler_templates_it` |
| **C** | `{{NARRATION}}` → `(narration)` in the prompt template | exactly the three named failures: `test_the_transcript_is_injected_verbatim_into_the_prompt`, `test_a_silent_recording_says_so_instead_of_leaving_a_gap`, `test_the_prompt_template_still_carries_the_placeholder_the_code_replaces` |

Each restored to 13 passed before the next. The manifest's transcripts match my own output
character-for-character, including the truncated repr in B. The maker's point about C is correct
and is now contract text: the third test defends the *template*, and without it a template that
loses the placeholder ships a prompt with no narration while every other test stays green.

## The maker's account of the PRIOR state — checked at `1c8c8e4^`, not believed

| Claim | Verdict |
|---|---|
| `stages/ingest.py` never imported `ProjectStore`; `ingest_video` returned a FlowSpec and no caller persisted it | **TRUE.** `git show 1c8c8e4^:src/autotester/stages/ingest.py` defines four functions (`build_ingest_prompt`, `_to_screen`, `_to_flow`, `ingest_video`); no `ProjectStore`, no `save_flowspec`. `git grep ingest_video 1c8c8e4^ -- src scripts` returns only its own definition — every other hit is `tests/test_ingest.py`. Zero production callers. |
| `providers/gemini.py::see_video` had zero callers | **TRUE in substance, loose in wording.** `GeminiProvider.see_video` was never invoked anywhere outside `tests/test_providers.py:51`; the class appears in `providers/__init__.py`'s registry only. The base-class method *was* called polymorphically at `stages/ingest.py:67` — but by a function that itself had no production caller, so nothing was wired end to end. Not an inflation. |
| `VisionOptions` existed with nobody passing it | **TRUE.** `git grep VisionOptions 1c8c8e4^` hits `schema/observation.py:83`, `tests/test_schema_video.py`, and planning/decision prose. No production caller; `seed` was decorative exactly as claimed. |
| `Source.recorded_on` existed with nothing setting it | **TRUE.** Only the schema field (`schema/project.py:68`) and D-014 prose. |

The "before" is not inflated. This was a wiring unit and the manifest describes it as one.

## Adversarial probes on the new code

**`upload_and_wait`** — stub client, injected `clock`/`sleep`:

- **timeout path** → `ProviderError: v.mp4 was still PROCESSING after 10s — the Files API never made it readable`. Bounded, does not hang.
- **FAILED after polling** and **FAILED returned by `upload` itself** → both raise `ProviderError: the service could not process v.mp4 (state FAILED)`. No infinite poll.
- **handle with no `state` attribute** and **handle whose `state` is a dict** → `_state_of` yields `""` / `"{'weird': 1}"`, neither of which is `ACTIVE`, so the code keeps polling and only returns once a real `ACTIVE` arrives. It fails toward waiting, never toward returning an unreadable handle. Correct direction.
- **corrupt cache file** (`{not json`) → `_load_cache`'s `ValueError` branch swallows it, the upload proceeds, and the cache is rewritten clean. No crash.
- **dead cached handle** (`files.get` raises 404) → upload count 1: it really does degrade to a re-upload, not an error.
- **cached handle still PROCESSING** → also re-uploads. Safe.
- **cache key** — this is the one that fails toward a plausible wrong answer, filed as **AT-128**: `resolve()::st_size` means the same path rewritten with different bytes of identical length is a **HIT** (upload count 0 — measured), so the pipeline would read the old video. `core.ids.file_sha256` is already imported by `stages/ingest.py` in this very unit.

**`_config`** — configs built for six model names:

- **The determinism claim is TRUE and is the important one.** With `options=None` the config still carries `seed=7` and `max_output_tokens=65536` (`opts = options or VisionOptions()` runs before the `if options is not None` guard). The observation cache's premise holds.
- `options=None` correctly leaves `temperature`, `system_instruction` and `media_resolution` unset.
- The `gemini-3` prefix test is **not** correct for all real names: `models/gemini-3.6-flash` — an identifier the SDK accepts, and `--model` passes any string straight through — fails the test and silently loses `media_resolution`. **AT-127.**
- `thinking_level` is in `VisionOptions`, named in `_config`'s own docstring, and never written into the config. **AT-126.**
- No shipped caller passes options at all (measured end to end: `MockProvider.vision_options == [None]` after `autotester ingest run`). **AT-125** — the largest of the seven.

**`_unparsed_reason`** — six response shapes, none crashed: no `candidates` attribute at all, `candidates=None`, `candidates=[]`, `finish_reason=None` → the generic message; `MAX_TOKENS` → `the answer hit max_output_tokens and was truncated (role=vision) — shorten the chunk or raise the ceiling`; `SAFETY` → generic message *with* `finish_reason=SAFETY` appended. The truncation/malformed distinction the manifest claims is real.

**`register_source`** — identical content at two paths gives **ONE** source (count 1), returning the first registration's row and silently not applying the second call's label. I judge that the right answer for a corpus keyed on content, and I have written it into I10 so it is a recorded decision rather than an accident. Missing file raises. Changed bytes at the same path mint a **NEW** source and never mutate the old row — also right, and it exposes the gap filed as **AT-129**: nothing ever re-checks `Source.sha256` at ingest time, so `ingest run <stale-id>` watches the new bytes and stamps every `SourceRef` with the old recording's identity, quietly falsifying I2.

**`persist_ingest`** — over `DRAFT` → overwrites (`'NEW'` on disk); over `NEEDS_EDIT` → overwrites; over `APPROVED` → `FlowSpecApproved`, **and I read the file back: the approved spec is still `'existing-approved'` on disk, untouched, not half-written**; then `replace=True` → `'NEW'`. Exactly as claimed.

**End to end through the real CLI** (typer `CliRunner`, `MockProvider` injected): `ingest register` → id + sha prefix; registering the same file twice → same id, one source; `ingest run` → `demo: 1 screens, 1 flows from demo run (review status draft)`; on disk, `url_pattern='demo.test/x/{id}'` and `source_ref=SourceRef(source_id='src_83ee…', t_start=0.0, t_end=1.0)`. The stage is genuinely reachable by a human now, which is the unit's actual claim.

## Honesty of the "does NOT claim" section

- **"No live model call was made; every test uses MockProvider."** Verified by execution, not by reading: I re-ran the 29 tests of `test_providers.py`, `test_ingest.py` and `test_ingest_persist.py` with `socket.socket.connect`, `socket.socket.connect_ex`, `socket.create_connection` and `socket.getaddrinfo` all replaced by raisers. **29 passed.** Nothing in this unit's test surface can reach the network. (There is no global socket guard in `tests/conftest.py`; the property holds because no test constructs a live client, not because a fixture prevents it. Worth knowing, not worth an issue.)
- **"`screenshot_ts` is requested in the prompt but consumed nowhere."** TRUE. `grep -rn screenshot_ts src/ tests/` returns exactly two source hits: `prompts/ingest_video_v1.md:15` (asks for it) and `schema/observation.py:60` (defines it). No reader. Recorded in the contract's no-fire list as a declared gap.
- The A3/A4 deferrals (media prep, chunking, whisper, ensemble, adjudication) are consistent with the diff — none of them appears.

## Contract authorship (I6–I10) — my words, not the maker's

I folded the inbox's I6–I9 into `qa/contracts/ingest.md`, rewritten and judged against my own
evidence, and added **I10** because `register_source`'s content-identity rule is a real decision
this unit made that the four requested criteria left ungoverned. Two clauses are mine rather than
the maker's: I8 keeps the placeholder rule as a *criterion* (sabotage C proves the template needs
its own defender), and I9 gained a cache-degradation clause after probing — a dead handle, a
`PROCESSING` handle, an expired entry and a corrupt cache file all fall back to a re-upload, and
that behaviour is now required rather than incidental. The inbox entry is marked folded.

## Rulings on the two judgements the maker explicitly asked for

**1. `google-genai` left undeclared in `pyproject.toml`, contrary to plan §4 A2 — a real deviation, filed as AT-130, but not a FAIL of this unit.**
The maker's reasoning is half wrong in a way that matters. `from google import genai` **succeeds**
in this environment today (google-genai 2.22.0 in `.venv`), so the provider is *not* dead code and
the tests are not passing merely by avoiding it. But `uv.lock` shows exactly one package requiring
it — `langchain-google-genai 4.4.0` — so `GeminiProvider` imports by the accident of somebody
else's pin. A langchain-google-genai release that drops or renames that dependency breaks the
vision provider with no `pyproject` change and no failing test, because no test imports
`google.genai` at all. "Nothing exercises it yet" is therefore an argument *for* declaring it, not
against: an undeclared direct import is hazardous precisely while it happens to work. It must be
closed in the A3 unit that first calls the Files API for real; the contract's no-fire list now
names that debt so it cannot go quiet. Not FAIL-worthy: no authored criterion depends on it, the
behaviour is correct today, the fix is one line, and the maker flagged it instead of hiding it.

**2. The `git checkout` hygiene line — upheld in substance, refused in `ingest.md`. Filed as AT-131.**
A feature contract judges the artifact, not how the maker held the tools. AT-101 already records
this exact class against the `living-ledger` feature and covered only committed work; AT-131
extends it to uncommitted files, with the rule stated: while a unit is uncommitted, restore a
sabotage from a file copy taken before the edit, or reproduce it in a `git archive` scratch copy —
never `git checkout`/`restore`/`stash` against the live tree, which cannot tell the sabotage from
the work.
**And nothing was in fact lost.** I checked rather than took the maker's word: the committed
`git diff 1c8c8e4^ 1c8c8e4 -- src/autotester/prompts/ingest_video_v1.md` is a coherent 29-line
addition carrying the whole "What the person said" section — ground truth, align-don't-re-transcribe,
don't paraphrase, and the fabricated-quote-from-a-real-person rationale — plus the url-legibility,
`fields`, `screenshot_ts` and `open_questions` rules. `grep -c '{{NARRATION}}'` = 1, and the three
sabotage-C tests pass against it. That is a full rewrite, not a degraded retype.

## Issues filed

| id | sev | one line |
|---|---|---|
| AT-125 | medium | No shipped caller passes `VisionOptions`; the CLI delivers `options=None`, so `media_resolution` HIGH never applies in production (seed/max_output_tokens do). |
| AT-126 | medium | `thinking_level` is named in `_config`'s docstring and never written into the config. |
| AT-127 | medium | `startswith("gemini-3")` misses the SDK's `models/gemini-3.x` form and silently drops `media_resolution`. |
| AT-128 | medium | Upload cache keyed on `path::st_size`; a same-size in-place edit is a stale HIT serving the old video. |
| AT-129 | medium | `Source.sha256` is never re-validated at ingest time, so a stale Source id stamps SourceRefs into the wrong recording. |
| AT-130 | medium | `google-genai` imported directly, declared nowhere; resolves only transitively via `langchain-google-genai`. |
| AT-131 | low | Extends AT-101: `git checkout` as a sabotage-restore on uncommitted work (maker self-reported; nothing lost, verified). |

None of the seven falsifies I1–I10. Each is a follow-on, and AT-125/AT-129 in particular belong to
the A3 unit that first supplies real options and real media.

## Goal + ledger

- `T-131` closed on this PASS via the goal CLI (`user_value: high`, `criticality: high`).
- **A `docs/FEATURES.jsonl` ledger row IS due** — T-131 is a `user_value: high` goal task closing on
  a checker PASS, which per `CLAUDE.md` requires a row with a prefilled reason shown to Umesh to
  confirm or edit. That is the maker's action on close-out, not the checker's; flagged here so it
  is not skipped. Suggested prefill: *"First working unit of Track A. `ingest_video` previously
  returned a FlowSpec that no caller persisted, so learning from a recording left no trace on disk;
  `GeminiProvider.see_video` and `VisionOptions` had no production callers at all. T-131 wires the
  stage end to end — `register_source` (content-idempotent), `persist_ingest` (refuses to discard
  an APPROVED spec without `--replace`), url_pattern through the crawler's own `url_template`,
  `upload_and_wait` polling the Files API to ACTIVE, typed SDK errors, truncation reported as
  truncation, and `autotester ingest register|list|run`. MockProvider only — no live model call,
  verified with sockets blocked."*

## State left for the maker's close-out (doctor is now RED, by design)

Before this check `uv run autotester doctor` was clean; after closing T-131 it reports two
violations, both of which are the close-out itself and neither of which is checker-owned:

```
ledger-row-missing: T-131 - closed high-value task has no live/updated row
stale-generated: docs/SNAPSHOT.md - differs from regeneration; run `autotester snapshot`
```

The maker closes both: append the `docs/FEATURES.jsonl` row (prefilled reason above, for Umesh to
confirm or edit) and run `autotester snapshot`. I did not touch either -- a generated doc and the
feature ledger are the maker's surfaces, and the verdict must not be the thing that edits them.
