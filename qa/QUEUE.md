# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T06:22Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-09T04:50Z, ~1.5h and 11 commits ago.

## Concurrency note (AT-101, respected)

No `git stash`/`checkout`/`restore` in the live tree. My own C5 re-sabotage ran in a `git archive
HEAD` extract with its **own `uv sync` venv**, `__file__` verified before trusting the result. A
maker session was actively fixing `providers/gemini_schema.py`, `tests/test_gemini_schema.py`,
`pyproject.toml`, `uv.lock` for the peer checker's AT-265..268 findings throughout this sweep —
those paths were read but never written.

**This sweep's own headline is a same-day double verdict-file overwrite, disclosed in full and
corrected twice — see `qa/.last-sweep`'s newest entry and `qa/verdicts/at230-gemini-schema.md`.**

---

## TOP-3 RECOMMENDED NEXT UNITS (this sweep)

1. **AT-266 (high, filed by the peer, independently confirmed by me) — pin `gemini.py:142`'s
   response-dict validation.** Removing `schema.model_validate(response.parsed)` entirely produces
   **zero test failures** (910 passed, twice, in two independent isolated extracts). One stub-client
   test asserting an extra/missing/wrong-typed key raises `ProviderError` closes it — no network,
   no key, the exact pattern `tests/test_gemini_schema.py` already uses for the request side.
2. **AT-264 (high, this sweep) — give `generate_cases` an error boundary.** A `ProviderError`
   mid-generation reaches the operator as a raw `text/plain` 500, not the themed page every sibling
   refusal in the same function (`routes_learn.py:169-213`) returns. Reproduced live; not
   hypothetical — `providers/gemini.py` genuinely raises this, and the scorer's own measured recall
   today is 1/7, i.e. the model is already observed to misbehave on this exact path. Wrap the
   `expand()` loop, return the same `_refusal()` the no-provider case uses.
3. **AT-215 / AT-156 (fifth consecutive sweep, unchanged) — either build the test or downgrade the
   claim.** VL1c's measured-placement half and C9's `approved` field remain unpinned by anything.
   Five sweeps naming the same gap without movement is itself worth a line in the next tick: either
   this is queued and built, or the criterion should say plainly that it is unverified.

Also open from this sweep: **AT-265** (the sanitiser is a 4-keyword deny-list against a 24-key
allow-list in the installed SDK — latent, not yet a failure) · **AT-267** (the self-reference refusal
drops the `$ref` it is holding rather than naming it) · **AT-268** (`ingest.md`'s own no-fire list
says `google-genai` gets declared "when the unit that first calls the API for real" lands — that
unit landed, `pyproject.toml` still doesn't declare it).

---

## TOP-3 RECOMMENDED NEXT UNITS

1. **AT-255 + AT-256 (both high) — recommit and actually pin the AT-230 fix.** `99ea27d` put the
   change that unblocked every real Gemini call on master with no manifest, no verdict, and its only
   guard (`tests/test_gemini_schema.py`) untracked. Reverting the single wiring line
   `providers/gemini.py:79` in a HEAD extract leaves **867 passed, 2 skipped, zero failures**. The
   unit is not "commit the test" — the test as written cannot catch it either: all 12 assertions call
   `gemini_schema()` directly and never construct `GeminiProvider`. The pin has to watch the
   `response_schema` kwarg the provider actually hands the client.

2. **AT-231 (high) — merge the duplicate pair in `adjudicate`.** Now that a real number exists
   (recall 1/7, 5 false positives, at least 3 of the 5 being duplicates of each other), this single
   defect accounts for the majority of the FP count. It is the highest-leverage open scorer issue and
   the cheapest movement available on the headline number. AT-232 (the 0.30 `SequenceMatcher`
   threshold, `stages/score.py:214,254`) is the matching lever on the recall side and is correctly
   ranked `high` alongside it.

3. **AT-226 (high) + AT-227 (raised medium → high this sweep) — the crawler's two real-world
   stoppers.** The first real crawl learned ONE screen. An already-authenticated session aborting the
   whole crawl as `login_failed`, and a first-paint modal nothing dismisses, are both first-order
   causes of that, on the critical path of every downstream stage. Neither has any fix in code:
   grep for `modal|dismiss|already_authenticated` across `stages/explore*.py` and `stages/login*.py`
   returns nothing.

Below the top-3, unchanged and still owed: **AT-215** (VL1c's measured-placement half has no test —
**fourth** consecutive sweep unchanged, in a HIGH-criticality contract) and **AT-156** (C9's
`approved` field pinned by nothing — **fourth** consecutive sweep).

## Gate lines (read before the TODO rows)

- GRILL: the recurring vacuous-guard class (AT-218) — **still open, and this sweep is the fourth
  consecutive report of it unchanged**. See the headline in `qa/.last-sweep`.
- HUMAN_GATE: `qa/gates/at110-approval-forgery.md` — open, not answered off-disk.
- HUMAN_GATE: `qa/gates/erp-credentials.md` — open, no `Answered:` line at all; `projects/erp/` still
  has no `.env`.
- HUMAN_GATE: `qa/gates/at147-expiry-end-of-day.md` — its `**Answered:**` line is still an empty
  template stub, not an answer.
- `qa/gates/t136-model-credentials.md` is correctly **answered** (2026-09-09, "THE GATE WAS WRONG —
  Umesh had already provided the credentials").
