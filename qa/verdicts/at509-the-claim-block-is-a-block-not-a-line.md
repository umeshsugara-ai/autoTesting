# Verdict — at509-the-claim-block-is-a-block-not-a-line

**Cycle checked: 1**
**Date:** 2026-09-18
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`
**Manifest:** `qa/manifests/at509-the-claim-block-is-a-block-not-a-line.md`
**Unit commit:** `9b91085` (tick stamp `0efb8ed` touches only `qa/.last-tick`)
**Contract:** `qa/contracts/core-invariants.md` C10, C7

## What I re-ran myself

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → `43 passed in 0.61s`. Matches.
- `uv run ruff check src tests scripts` → `All checks passed!`. Matches.
- `uv run autotester doctor` → `doctor: clean`. Matches — with 50 more ids in scope than before, and confirmed clean again after this checker's own ledger write.
- `uv run python scripts/mutation_check.py qa/evidence/at509-the-claim-block-is-a-block-not-a-line/mutations.json` → `5/5 mutations killed`, exit 0. Compared each row's `claims to kill` against its `actually failed` set myself: identical in all 5 rows, each isolated to exactly the one test it names — no mutation is caught by a second test covering for it, confirming the manifest's strongest structural claim.
- Whole suite `uv run pytest -q` (via `uv run` wrapper — the AT-503 `-qq` collapse only bites the raw `uv run pytest -q` invocation, and I redirected to a file and scanned it whole regardless): `.work`-independent run redirected to a temp log, 100% reached, `EXIT=0`, zero matches for `FAILED|ERROR|^E `. Only a pre-existing `anyio.abc.BlockingPortal` deprecation warning and a couple of `s`/`x` (skip/xfail) markers, nothing new.
- `git diff 3370a62...9b91085 --stat` and the full diff on `src/autotester/ledger/checks.py`: purely additive (`_NEW_FIELD` + `_marker_lines` added; the two call sites in `check_qa_issue_rows` changed from `body.splitlines()`-filtered to `_marker_lines(...)`). No function, class, test, route, or export deleted or renamed; no file outside the manifest's "What changed" touched (C10 satisfied).

## Independent re-derivation of the 50 (not the maker's script — the shipped function directly)

Called `_marker_lines`/`_is_marker_line` imported straight from `src/autotester/ledger/checks.py` against every file in `qa/manifests` and `qa/verdicts`, comparing ids visible on the marker line alone (old behaviour) against ids visible via `_marker_lines` (new behaviour), with `PYTHONUTF8=1` for the `·`/`→` corpus:

```
manifests  13 artifacts gaining ids | 29 ids newly visible
verdicts    9 artifacts gaining ids | 21 ids newly visible
                                   -> 50 ids across 22 artifacts, exactly as claimed
newly-visible ids WITHOUT a ledger row: []   (all 50 confirmed to have a row)
```

Exact match to the manifest's "measurement first" table and its "every one of the 50 has a row" claim.

## Capability coverage: 5/5 rows reproduced

Re-read the mutation evidence directly rather than trusting the paste: every row's `claims to kill` and `actually failed` test are identical, one test per row, no cross-covering. The three stop conditions (blank line, heading, next `_NEW_FIELD`) are each falsified independently, which is the right structure for a walk with three distinct stop reasons.

## Judgment calls the brief asked for

1. **The disclosed residual-risk trade (continuation prose counted as "named").** Confirmed live: `qa/manifests/at298-migration-host-guard.md` line 10 reads `AT-293 established` inside the "Issues addressed" continuation, and `AT-293` is now swept in as named. It has a row (no violation today). **I agree with the maker's trade as stated**: the direction is a miss→now-visible-but-inert, not an over-accusation, all 50 recovered ids check out against the live ledger, and the proposed alternative (require a list separator before treating a token as a "named" id) would materially complicate the rule for a risk that is currently zero-consequence and only theoretical for the *scope this residual-risk item names*. I do not think this closes the book on over-inclusion in general — see finding AT-511 below, a **different** mechanism producing the same shape, found live rather than reasoned about.
2. **`_NEW_FIELD` heuristic, both directions, checked against the live corpus:**
   - *Does it misfire on real content* (stop too early, a miss)? Scanned every marker-triggered block in both `qa/manifests` and `qa/verdicts`: every line where `_NEW_FIELD` fires is a legitimate field boundary already in use (`EXPLANATION:`, `ISSUES-CLOSED:`) — no spurious early stop found anywhere in the corpus.
   - *Does it fail to fire on a real field label in use* (over-run)? **Yes — found one, live**, not hypothetical: `**ISSUES KEPT OPEN (claimed fixed, not fixed):**` in `qa/verdicts/at097-session-start-hook-regression.md` line 260 does not match `_NEW_FIELD` (the parenthetical before the colon breaks the required unbroken `[A-Z0-9 -]*` run) and is not itself a marker line for `ISSUES-WRITTEN`, so it is swallowed as a continuation of the preceding `**ISSUES-WRITTEN:** AT-106, AT-107` block. Verified by calling `_marker_lines` directly against the real file:
     ```
     '**ISSUES-WRITTEN:** AT-106, AT-107'
     '**ISSUES KEPT OPEN (claimed fixed, not fixed):** AT-097, AT-029'
     '**ISSUES-WRITTEN:** none (no new findings).'
     ```
     AT-097 and AT-029 are now misattributed as named by `ISSUES-WRITTEN` when they are actually named by a distinct field. **Zero live consequence** — both ids are already `status: verified` in the ledger, so `named - set(status_of)` is empty and no `ledger-row-lost` fires; `claimed`/`ledger-row-stale` never runs for a verdict marker at all (that computation is gated to `kind == "manifests"`). I checked the mirror case on the manifest side (a continuation line matching a field-label-with-paren shape right after `**Issues addressed:**`) across every manifest — none found, so today's exposure is verdict-only and inert. Filed **AT-511** (medium) — this is exactly the "next one" the brief asked me to hunt for, and it's the AT-509/AT-504 false-accusation *shape* reproduced by a second, distinct mechanism (field-boundary miss on punctuation, not prose-discussing-an-id) in the very fix meant to close the first mechanism.
   - Also confirmed a smaller, same-root-cause over-run while investigating: when `ISSUES-WRITTEN` is the last field before the closing ` ``` ` of the standard fenced verdict block, the fence delimiter itself matches none of the four stop conditions and gets swept in as one extra harmless line (`qa/verdicts/at147-at148-grant-boundary.md`, `at355`, `at368`, `at386`, both `t135-coverage-merge-expand.md` and `.b.md`). No id has ever landed on a fence line in this corpus, so this is cosmetic today, but it's the same "the stop-condition set doesn't cover every real markdown shape" defect class as AT-511. Folded into AT-511's evidence rather than filed separately.
3. **The disclosed stale-check parenthetical-split limit** (`AT-900\n(low, open -> fixed)`). The manifest says "the limit is real" without a live citation. **Confirmed it is real, not theoretical**: `qa/manifests/at506-record-rules-leave-the-source-rules.md` line 13 wraps `AT-488` at end-of-line with its parenthetical on the next physical line. Zero consequence (the wrapped text isn't a fix claim), but it's a genuine live instance. Filed **AT-512** (low), tracked per this project's own precedent (AT-502/AT-507/AT-510) for a disclosed-but-inert "Known limits" item.
4. **Hunt for the next one:** the two findings above (AT-511, AT-512) are it. Both are adjacent-but-distinct gaps in the same module rather than a defect in what this unit actually claims to fix, so — consistent with this chain's own precedent (AT-508's checker filing AT-509/AT-510 the same way) — they are filed to the ledger rather than failing the unit.

## Live browser

Not UI-touching. Changed paths: `src/autotester/ledger/checks.py`, `tests/test_ledger_checks.py`, `qa/evidence/at509-the-claim-block-is-a-block-not-a-line/*`. No UI surface, direct or indirect, is affected.

```
VERDICT: PASS
SCOREBOARD: 5/5 mutation rows reproduced, 50/50 newly-visible ids independently re-derived and row-confirmed, 0/0 criteria contradicted, all C10/C7 verify commands re-run and matched
FAILURES (if any): none
CAPABILITY-COVERAGE: 5/5 rows reproduced (compared claims-to-kill vs. actually-failed directly from the evidence file; each isolated to its own test)
LIVE-BROWSER: not-applicable (no UI-touching paths changed: src/autotester/ledger/checks.py, tests/test_ledger_checks.py, qa/evidence/*)
ISSUES-WRITTEN: AT-511 (medium, _NEW_FIELD cannot recognize a field label with a parenthetical before its colon, so the AT-509 fix's own block over-runs into an adjacent field — reproduced live in at097-session-start-hook-regression.md, currently inert), AT-512 (low, confirms the manifest's disclosed stale-check parenthetical-split limit is live, not theoretical, in at506's own manifest); AT-509 open -> fixed
EXPLANATION: Every stated claim holds under independent re-derivation against the shipped functions — the 50 newly-visible ids (13/29, 9/21) match exactly and all have ledger rows, the 5 mutation rows are each isolated to exactly their own test, the diff is purely additive and C10-clean, and the whole suite is green (exit 0, zero FAILED/ERROR). The maker's own disclosed residual-risk trade (continuation prose counted as named) is confirmed live and inert, and I agree with keeping it as-is. I did find a second, distinct over-run mechanism the manifest didn't test for — a field label with an embedded parenthetical bypasses _NEW_FIELD and gets swallowed by the preceding marker's block — reproduced live in the corpus this very unit measured against, but with zero consequence today since both swept-in ids already carry ledger rows. Per this chain's own established practice, that is filed (AT-511, AT-512) rather than failing a unit whose own stated claims are all true.
```
