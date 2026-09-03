# Manifest — t050-pathlynks-first-run

**Contract:** qa/contracts/pathlynks-first-run.md (F1–F5, new this cycle) + qa/contracts/execute.md
(E1-E5, dependency) + qa/contracts/browser-and-secrets.md (B1-B9, dependency) +
qa/contracts/pathlynks-onboarding.md (O1-O4, dependency, same credential boundary)
**Goal task:** T-050 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly, but resolves the same class as AT-025/O1 (credential
boundary discipline extended to a new script)

## Human gate cleared

Umesh approved this live run explicitly this session (AskUserQuestion: "T-050 needs to run 3
real cases (including a deliberate wrong-password attempt) against the live Pathlynks dev
environment in a headed (visible) browser. Proceed now, or build a different unblocked unit
first?" → "Yes, run it now, headed").

## Grading (F3/F4) is honestly incomplete — read before judging PASS/FAIL

`ANTHROPIC_API_KEY` in `.env` is empty; the only working provider key is `GEMINI_API_KEY`, and no
Gemini provider exists yet (T-060's job). Rather than build a throwaway single-vendor Gemini
judge, Umesh explicitly chose (this session, AskUserQuestion: "should I build a small Gemini
judge provider now... or wait until the LangChain redesign happens properly?" → "Wait — do the
LangChain redesign first") to defer real grading until a proper LangChain-based multi-provider
fallback exists. That architecture direction is recorded in `qa/feedback-inbox.md`
(2026-09-03, "on provider architecture") — unfolded, not yet scoped as its own contract/task.

**What this unit delivers instead**, per the same AskUserQuestion round: the browser-execution
half runs for real (F1/F2/F5, all genuinely met, see below), producing real `RawResult` evidence
persisted exactly as `grade.py`'s contract expects — grading can be added later (the script's
`--grade` flag, currently unused) without re-running the browser part. **F3 (real judge) and F4
(defensible verdicts) cannot be met today** — there is no `Verdict` for any of the 3 cases. This
is a deliberate, human-directed deferral, not an oversight or a build defect; the checker's call
whether that makes this cycle a routine contract amendment (F3/F4 deferred to a follow-on unit
once a real judge exists) or a FAIL naming exactly what's missing.

## What we found (two real bugs, in this script, not the product)

1. **Session-carryover race**: the first attempt ran BEST (login) first, which succeeded and left
   the persistent Chromium profile authenticated for the rest of the process — WORST/EDGE then
   hit an already-logged-in redirect instead of the sign-in form (`Locator.evaluate`/`click`
   timeouts on `input[name="identifier"]`/the submit button). Fixed by running WORST/EDGE first
   (while genuinely logged out) and BEST last; cleared `profiles/pathlynks/` (gitignored local
   Chromium cache, not product data) so the re-run started from a clean logged-out state.
2. **Post-submit timing race**: BEST's own post-submit URL read `[REDACTED]:PATHLYNKS_USER_LOGIN_URL`
   (the login page) instead of `/dashboard` on the corrected-order run, because the site shows an
   async "Logging in..." spinner (confirmed by screenshot) and `page.url` was read before the
   redirect completed. Fixed with a `POST_SUBMIT_WAIT_MS=4000` wait, matching T-030's
   `onboard_pathlynks.py::DASHBOARD_WAIT_MS` precedent exactly.
3. (Not a functional bug, but a data-cleanliness fix) `execute.py::run_case` snapshots
   `session.state.evidence` cumulatively for the whole (reused) `BrowserSession`, not scoped per
   case — so case 2/3's `RawResult.evidence` was also carrying case 1's entries. Fixed in this
   script by slicing `session.state.evidence` to only what each case's own run adds (recorded the
   list length before calling `run_case`), not by changing `execute.py` itself (that's a separate
   contract, already checker-PASSed — flagging this as a note for the checker to judge whether it
   warrants its own issue against `execute.md`, since a future caller reusing one session across
   cases would hit the same thing).

## What changed

- `qa/contracts/pathlynks-first-run.md` (new) — F1 (3 cases, one per kind) · F2 (headed, real
  evidence) · F3 (real judge, not mock) · F4 (defensible verdicts) · F5 (zero secret hits,
  write-policy respected).
- `.goal/rubrics/T-050.md` (new) — authored at this unit's own START, per AT-014's own fix
  direction ("author each rubric when its contract is initialised").
- `scripts/run_pathlynks_first_cases.py` (new, 193 lines) — `build_cases`, `make_rubric`,
  `run_one_case`, `main`. Real login/wrong-password/empty-submit cases against Pathlynks, headed
  browser (`headed=True` in-memory override, `project.json` itself untouched), `--grade` flag
  reserved for when a real judge exists (unused this run).
- `projects/pathlynks/cases.jsonl` — 3 new `Case` rows (best/worst/edge login), via
  `ProjectStore.add_case` (idempotent, content-addressed).
- `projects/pathlynks/runs/run-01M1K3QVCWQESZX05KWCWPH5B3/` — real `Run` + 3 `RawResult` files +
  screenshots from the corrected, working run.
- `tests/test_run_pathlynks_first_cases.py` (new, 6 tests) — case shape (one per kind, correct
  `case_class`), no case step carries a raw secret literal (placeholder check), the deliberately
  wrong password is a literal not a placeholder (there is no such secret key), NAVIGATE steps use
  the real base_url not a template marker, rubric links `case_id`, BEST always sorts last.
- `docs/ARCHITECTURE.md` — concept→file row for the new script; Status line updated. 146 lines
  (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_run_pathlynks_first_cases.py -v` → 6 passed
- `uv run pytest -q` → exit 0, 135 collected (was 129 before this unit: +6)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 146 (≤ 150)
- `uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K3QVCWQESZX05KWCWPH5B3
  scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl` → 1 leak reported
  (`projects/pathlynks/cases.jsonl`), which is the documented AT-004-style false positive
  (`base_url` == undeclared `PATHLYNKS_USER_LOGIN_URL`) — same pattern already accepted for
  `project.json` since T-030, not a real secret.
- Manual: open `projects/pathlynks/runs/run-01M1K3QVCWQESZX05KWCWPH5B3/13-best-final.png` (real
  "Logged in successfully" toast + authenticated dashboard greeting), `05-worst-final.png` (real
  "Invalid credentials" error banner), `08-edge-final.png` (real "required" field validation).

## Actual outputs (from maker's own run)

```
$ uv run python scripts/run_pathlynks_first_cases.py
grading DEFERRED (no --grade flag / no working judge provider yet) -- running the browser part
only, per Umesh's 2026-09-03 decision to wait for the LangChain provider redesign
worst case_a5ea57c0961a  outcome=completed verdict=(deferred)
edge  case_b1cb019ebb56  outcome=completed verdict=(deferred)
best  case_35b17ccece2d  outcome=completed verdict=(deferred)
run: D:\autoTesting\projects\pathlynks\runs\run-01M1K3QVCWQESZX05KWCWPH5B3

$ uv run pytest tests/test_run_pathlynks_first_cases.py -v
......                                                                   [100%]
6 passed

$ uv run pytest -q
................................s....................................... [ 53%]
...............................................................          [100%]

$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean

$ uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K3QVCWQESZX05KWCWPH5B3
  scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl
LEAK: projects\pathlynks\cases.jsonl
scanned 19 file(s); 1 leak(s)
```

## Scope notes for the checker

- BEST's actual RawResult evidence (`case_35b17ccece2d.json` in the cited run) shows
  `post-submit URL: https://pathlynks.vidysea.com/dashboard` — unmasked, since that URL doesn't
  overlap any declared/undeclared `.env` value.
- WORST/EDGE's RawResult evidence shows the post-submit URL still masked as
  `[REDACTED]:PATHLYNKS_USER_LOGIN_URL` — i.e. still on the sign-in page — consistent with a
  rejected wrong-password attempt and a blocked empty submit respectively; confirmed visually via
  the screenshots cited above (an "Invalid credentials" banner and "required" field messages).
- `write_policy=read_only` respected: only login-form submits happened (one deliberately with a
  wrong password, one deliberately empty) — no data was created, edited, or deleted.
- The counsellor role and any screen beyond login are out of scope (contract no-fire list).
- Per the contract's no-fire list, no image/vision content reached any judge (moot this cycle —
  no judge ran at all).
- An earlier attempt at this run (before the two bugs above were found and fixed) exists at
  `projects/pathlynks/runs/run-01M1K3DDACZ1AJ7BJPMX7A5KYF/` — all 3 cases reported `errored` due
  to the session-carryover bug. Left on disk as-is (real evidence of a real debugging process,
  matches this project's own precedent of not deleting run evidence); the corrected run
  (`run-01M1K3QVCWQESZX05KWCWPH5B3`) is the one this manifest's claims are about.

## Status: FAIL — cycle 1, next cycle deferred (not STALLED, not abandoned)

Verdict: `qa/verdicts/t050-pathlynks-first-run.md` (Cycle checked: 1, FAIL, 3/5; commit `1790ba1`,
not pushed per D-007's PASS-only push rule). F1/F2/F5 independently confirmed with real evidence
(headed `headless=False` traced in `session.py`, all 3 screenshots visually verified). F3/F4
correctly FAILed — no `Verdict` exists for any case, since no working non-mock judge exists. New
issue **AT-033** (medium, open) tracks this toward a follow-on.

**Why this does not get a normal fix-cycle 2 right now:** the checker itself named the only two
legitimate paths — (a) a follow-on unit that calls `grade()` against this cycle's already-real
`RawResult` evidence once a working judge exists, or (b) a human-decided contract amendment
splitting execution from grading. Neither is a code fix available to the maker today: (a) is
blocked on the same LangChain provider redesign Umesh explicitly asked to wait for (not a
throwaway fix), and (b) is the checker/human's call to make, not something the maker should
self-apply by softening F3/F4 to get past this cycle ("never soften a criterion to get past it").
Burning fix cycles 2 and 3 with no way to actually resolve F3/F4 would only STALL this unit for
no benefit — this manifest stays at cycle 1/FAIL, explicitly parked pending the provider
redesign, rather than forced through a hollow retry loop. `.goal/goal.json` T-050 stays `pending`
(no false close on a FAIL).
