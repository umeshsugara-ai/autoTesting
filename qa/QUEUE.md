# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T08:26Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-09T06:22Z, ~2h and 20 commits ago.

## Concurrency note (AT-101, respected)

No `git stash`/`checkout`/`restore` in the live tree. My own C5 re-sabotage ran in a `git archive
HEAD` extract with its **own `uv sync` venv**, `__file__` verified before trusting the result. A
maker session was actively fixing `providers/gemini_schema.py`, `tests/test_gemini_schema.py`,
`pyproject.toml`, `uv.lock` for the peer checker's AT-265..268 findings throughout this sweep —
those paths were read but never written.

**This sweep's own headline is a same-day double verdict-file overwrite, disclosed in full and
corrected twice — see `qa/.last-sweep`'s newest entry and `qa/verdicts/at230-gemini-schema.md`.**

---

## TOP-3 RECOMMENDED NEXT UNITS (refreshed 2026-09-09T08:26Z sweep)

AT-266/AT-267/AT-268 named below as of the last refresh are **already verified** — do not re-queue
them; ledger confirms `verified` for all three as of this sweep.

1. **AT-273 (high, filed this sweep) — give `_already_past_login` (explore.py:115-123, AT-226's own
   precheck) the same disciplined exception handling as its sibling `_seed` 15 lines below.** The
   bare `except Exception: return False` swallows a transient nav failure during the precheck and
   silently reclassifies it as ordinary not-yet-authenticated, so the crawl can still fall through to
   `run_case`'s own `goto` and hit the exact step-timeout AT-226 exists to prevent — with no signal
   the precheck itself failed. Freshest code in the repo, sitting next to the pattern it should have
   copied; cheap to fix (name the exception, store it on `rt` the way `_seed`/`rt.seed_error` does).
2. **AT-227 (high) — the first-paint modal that nothing dismisses.** Still the other real-world crawl
   stopper alongside AT-226 (which has its own fix in flight, checker already dispatched this turn —
   do not race it). Grep for `modal|dismiss` across `stages/explore*.py` still returns nothing; the
   first real crawl learned one screen and this is on the critical path of every downstream stage.
3. **AT-215 / AT-156 (sixth consecutive sweep, unchanged) — either build the test or downgrade the
   claim.** VL1c's measured-placement half and C9's `approved` field remain unpinned by anything.
   Six sweeps naming the same gap without movement: either queue and build it, or the criterion
   should say plainly that it is unverified.

In flight, not queued: **AT-226** (already-authenticated-crawl fix built, manifest ready-for-check,
checker dispatched concurrently this turn — see concurrency note above). Fixed-backlog carried,
unworked again this sweep: **AT-207/208/219-223/228/230** (15 rows) — next sweep's first job.

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
