# Manifest — t050-pathlynks-first-run

**Contract:** qa/contracts/pathlynks-first-run.md (F1–F5, new this cycle) + qa/contracts/execute.md
(E1-E5, dependency) + qa/contracts/browser-and-secrets.md (B1-B9, dependency) +
qa/contracts/pathlynks-onboarding.md (O1-O4, dependency, same credential boundary)
**Goal task:** T-050 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 2 of max 3
**Issues addressed:** AT-033 (this cycle's fix — F3/F4 were undelivered, now genuinely met)

## Cycle 2 — fix for verdict `qa/verdicts/t050-pathlynks-first-run.md` (Cycle checked: 1, FAIL — F3/F4)

Umesh: "you are /maker so do the needful. dont wait for my permission. dont stop until you
achieve the /goal." Built **T-055** (`qa/contracts/langchain-fallback.md`,
`qa/manifests/t055-langchain-fallback.md`) — `LangChainFallbackProvider`, a real,
non-mock, multi-vendor judge (Anthropic → Gemini → Ollama → ChatGPT, falls through to whichever
is actually configured) — then re-ran this unit's real browser cases with grading enabled.

**Result: F3 and F4 are now genuinely met, not deferred.** Cleared `profiles/pathlynks/` again
(gitignored local cache) and re-ran `uv run python scripts/run_pathlynks_first_cases.py` (grading
now the default; `--no-grade` is the opt-out, not the other way around):
```
worst case_a5ea57c0961a  outcome=completed verdict=PASS (gemini)
edge  case_b1cb019ebb56  outcome=completed verdict=PASS (gemini)
best  case_35b17ccece2d  outcome=completed verdict=PASS (gemini)
run: D:\autoTesting\projects\pathlynks\runs\run-01M1K941M7AQ7RWMYPF378TDQT
```
All three `grader_provider` fields say `"gemini"` — the fallback correctly skipped the empty
`ANTHROPIC_API_KEY` tier and landed on the real, working one, exactly as `LangChainFallbackProvider`
is designed to. Each verdict cites real evidence, not a rubber stamp — e.g. the WORST case's
`note`: "The final URL evidence confirms the browser remained on the sign-in page, meeting the
landed criterion for a worst-case scenario." All three `*.verdict.json` files exist under
`projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT/`.

The cycle-1 run (`run-01M1K3QVCWQESZX05KWCWPH5B3`, browser-only, real evidence, no verdicts) and
the earlier debugging run (`run-01M1K3DDACZ1AJ7BJPMX7A5KYF`, the session-carryover bug) are both
left on disk as-is — this manifest's F3/F4 claims are about the cycle-2 run
(`run-01M1K941M7AQ7RWMYPF378TDQT`) specifically.

## Human gate cleared

Umesh approved this live run explicitly this session (AskUserQuestion: "T-050 needs to run 3
real cases (including a deliberate wrong-password attempt) against the live Pathlynks dev
environment in a headed (visible) browser. Proceed now, or build a different unblocked unit
first?" → "Yes, run it now, headed").

## Grading history (F3/F4) — cycle 1 deferred, cycle 2 delivers for real

Cycle 1: `ANTHROPIC_API_KEY` was empty and no Gemini provider existed, so grading was honestly
deferred rather than shipping a throwaway single-vendor shortcut — checker correctly FAILed 3/5
(AT-033). Cycle 2 (this one): built `LangChainFallbackProvider` (T-055) and re-ran with grading
on. F3/F4 are now genuinely met — see the "Cycle 2" section above for the real run and verdicts.

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
- `scripts/run_pathlynks_first_cases.py` (cycle 1: new, 193 lines; cycle 2: updated) —
  `build_cases`, `make_rubric`, `run_one_case`, `main`. Real login/wrong-password/empty-submit
  cases against Pathlynks, headed browser (`headed=True` in-memory override, `project.json`
  itself untouched for `headed`). Cycle 2: judge switched from a disabled placeholder to
  `LangChainFallbackProvider`; grading is now the default (`--no-grade` opts out).
- `projects/pathlynks/cases.jsonl` — 3 new `Case` rows (best/worst/edge login), via
  `ProjectStore.add_case` (idempotent, content-addressed).
- `projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT/` (cycle 2, current) — real `Run` + 3
  `RawResult` + 3 `*.verdict.json` files + screenshots. Cycle 1's browser-only run
  (`run-01M1K3QVCWQESZX05KWCWPH5B3`) and the earlier debug run
  (`run-01M1K3DDACZ1AJ7BJPMX7A5KYF`) remain on disk as history.
- `tests/test_run_pathlynks_first_cases.py` (new, 6 tests) — case shape (one per kind, correct
  `case_class`), no case step carries a raw secret literal (placeholder check), the deliberately
  wrong password is a literal not a placeholder (there is no such secret key), NAVIGATE steps use
  the real base_url not a template marker, rubric links `case_id`, BEST always sorts last.
- `docs/ARCHITECTURE.md` — concept→file row for the new script; Status line updated. 146 lines
  (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_run_pathlynks_first_cases.py -v` → 6 passed
- `uv run pytest -q` → exit 0, 145 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 147 (≤ 150)
- `uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT
  scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl
  src/autotester/providers/langchain_fallback.py` → 1 leak reported
  (`projects/pathlynks/cases.jsonl`), the documented AT-004-style false positive (`base_url` ==
  undeclared `PATHLYNKS_USER_LOGIN_URL`), not a real secret.
- Manual: open each `*.verdict.json` under `projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT/`
  — all `result: "PASS"`, `grader_provider: "gemini"`, each with a `note` citing the specific URL
  evidence that justified it.
- Screenshots (from the cycle-1 browser-only run, still the visual evidence — the login flow
  itself was unchanged in cycle 2): `run-01M1K3QVCWQESZX05KWCWPH5B3/13-best-final.png` (real
  "Logged in successfully" toast + dashboard), `05-worst-final.png` (real "Invalid credentials"),
  `08-edge-final.png` (real required-field validation).

## Actual outputs (from maker's own run, cycle 2)

```
$ rm -rf profiles/pathlynks   # local Chromium cache only, not product data
$ uv run python scripts/run_pathlynks_first_cases.py
worst case_a5ea57c0961a  outcome=completed verdict=PASS (gemini)
edge  case_b1cb019ebb56  outcome=completed verdict=PASS (gemini)
best  case_35b17ccece2d  outcome=completed verdict=PASS (gemini)
run: D:\autoTesting\projects\pathlynks\runs\run-01M1K941M7AQ7RWMYPF378TDQT

$ uv run pytest -q
................................s....................................... [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT
  scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl
LEAK: projects\pathlynks\cases.jsonl
scanned 23 file(s); 1 leak(s)
```

## Scope notes for the checker

- BEST's actual RawResult evidence (`case_35b17ccece2d.json` in the cited run) shows
  `post-submit URL: https://pathlynks.vidysea.com/dashboard` — unmasked, since that URL doesn't
  overlap any declared/undeclared `.env` value.
- WORST/EDGE's RawResult evidence shows the post-submit URL still masked as
  `[REDACTED]:PATHLYNKS_USER_LOGIN_URL` — i.e. still on the sign-in page — consistent with a
  rejected wrong-password attempt and a blocked empty submit respectively; confirmed visually via
  the cycle-1 screenshots (an "Invalid credentials" banner and "required" field messages) and
  re-confirmed by the identical post-submit URLs in the cycle-2 run
  (`run-01M1K941M7AQ7RWMYPF378TDQT`'s `case_a5ea57c0961a.json`/`case_b1cb019ebb56.json`).
- `write_policy=read_only` respected in both runs: only login-form submits happened (one
  deliberately with a wrong password, one deliberately empty) — no data was created, edited, or
  deleted.
- The counsellor role and any screen beyond login are out of scope (contract no-fire list).
- Per the contract's no-fire list, no image/vision content reached the judge —
  `LangChainFallbackProvider` sends text-only prompts; the grader reasoned from the evidence list
  (the post-submit URL string), not screenshot pixels, exactly as `grade_v1.md`'s prompt intends.
- Two earlier runs remain on disk as real debugging history, not deleted:
  `run-01M1K3DDACZ1AJ7BJPMX7A5KYF` (the session-carryover bug, all 3 `errored`) and
  `run-01M1K3QVCWQESZX05KWCWPH5B3` (cycle 1, browser-only, correct behavior but no verdicts). The
  current cycle's F1–F5 claims are about `run-01M1K941M7AQ7RWMYPF378TDQT`.

## Status: checked-PASS (cycle 2)

Reconciliation note (2026-09-03): never flipped at the time, even though qa/verdicts/t050-pathlynks-first-run.md records Cycle checked: 2, VERDICT: PASS, and goal task T-050 shows status done (.goal/goal.json). Corrected during a disk-state reconciliation pass -- the verdict file is the actual evidence.

Cycle 1 verdict: `qa/verdicts/t050-pathlynks-first-run.md` (Cycle checked: 1, FAIL, 3/5; commit
`1790ba1`). F1/F2/F5 confirmed with real evidence; F3/F4 correctly FAILed (no working judge).
AT-033 tracked the gap. Cycle 2 (this submission) closes AT-033 for real: `LangChainFallbackProvider`
(T-055, see its own manifest) is a genuine non-mock judge, and re-running this unit's real cases
with grading on produced 3 real, evidence-cited `PASS` verdicts via Gemini (the fallback chain's
actual working tier). Dispatching for re-check.
