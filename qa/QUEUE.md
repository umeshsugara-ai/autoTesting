# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T04:50Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-09T02:15Z, ~2.5h and 4 commits ago. Everything the prior sweep recorded was treated as
stale and re-derived from disk.

Baseline was **bare `uv run pytest`** (`addopts = "-q"` is set, so a command-line `-q` gives `-qq`
and hides the summary; `FAILED` lines were counted). Host reports 2 skips.

## Concurrency note (AT-101, respected)

No `git stash`, `git checkout` or `git restore` ran in the live tree. The one sabotage ran in a
`git archive HEAD` extract under the session scratchpad with `PYTHONPATH` pinned to the extract's
`src/`. A maker session was building `src/autotester/ui/routes_learn.py`, `src/autotester/ui/*` and
`tests/test_ui_learn.py` (the AT-241 unit) for this entire sweep: those paths and any
`qa/manifests/at241-*` / `qa/verdicts/at241-*` were **read but never written**. This sweep wrote only
`qa/issues.jsonl`, this file, `qa/.last-sweep`, and `.goal/goal.json`'s T-100 status (authorized by
D-022's own `Changes-authorized` line).

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
