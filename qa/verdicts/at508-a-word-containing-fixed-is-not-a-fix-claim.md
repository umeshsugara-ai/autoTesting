# Verdict — at508-a-word-containing-fixed-is-not-a-fix-claim

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` C10, C7

## What I re-ran myself

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → `38 passed in 0.62s`. Matches manifest.
- `uv run ruff check src tests scripts` → `All checks passed!`. Matches.
- `uv run autotester doctor` → `doctor: clean`. Matches.
- `uv run python scripts/mutation_check.py qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/mutations.json` → `4/4 mutations killed`, exit 0. Every row's "actually failed" set equal to its "claims to kill" set exactly (no over-claim, no under-claim), byte-identical to `mutations.out`.
- `PYTHONUTF8=1 uv run python qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/at508_measure.py` → `distinct notes: 54 | unchanged verdict: 54 | CHANGED: 0`, byte-identical to `note-survey.out`.
- Whole suite: `uv run pytest -q` redirected to a file (`.work/at508_checker_full_suite.log`, 27 lines, resolved to `-qq` as AT-503 warns) and scanned in full: `grep -nE "FAILED|ERROR|^E " ` → **zero matches**, exit 0, `100%` reached, only skips/xfails and one pre-existing deprecation warning.
- `git show --name-only --format= 674bfce` and `94ee1ce` → both are a strict subset of the manifest's "What changed" + this unit's own `qa/evidence/`, `qa/manifests/`, `qa/.last-tick` (C10 satisfied). Full diff of `674bfce` on `checks.py` is additive plus one comment removed; no function/class/test deleted.

## Independent re-derivation (not just running the maker's script)

Ran my own script against the **live shipped functions** (`_claims_a_fix`, `_is_marker_line`, `ISSUE_ID` imported directly from `src/autotester/ledger/checks.py`, not a re-implementation), scanning every manifest myself:
- Marker-line-gated distinct notes: **54**, changed verdict: **0** — matches the manifest exactly, but derived from the real predicate rather than the measurement script's own regex copies, which rules out a divergence between the script and the shipped code.
- An unfiltered whole-file scan (182 notes, no marker gating) surfaces one more apparent change (`including \`fixed_by\`` — a `fixed_by` JSON-field mention in `at496`'s prose, not an Issues-addressed entry). Confirmed it lives outside any `**Issues addressed:**` marker line, so `_is_marker_line` correctly excludes it from the real check. No live consequence; documents that the marker gate is doing real, necessary work (consistent with AT-504's own rationale).
- Directly tested the disclosed edge case: `_claims_a_fix("not, after some deliberation, fixed")` → `True` (a hypothetical false accusation the `{0,15}` bound does not catch) and `_claims_a_fix("not a duplicate, open -> fixed")` → `True` (correctly still a claim). No such long-interposed-clause note exists in the current 54.

## Capability coverage — reproduced in a fresh throwaway copy (never the bound tree)

Copied `src/`, `tests/`, `scripts/`, `pyproject.toml` to a scratch dir outside the repo. Confirmed **GREEN baseline from the copy itself** (`tests/test_ledger_checks.py`: 26 passed) before any edit — proof the copy is real, not an empty extraction. Applied each of the 4 mutation rows as a single-hunk edit to the copy's `checks.py`, one at a time, restoring between:

| row | edit | result |
|---|---|---|
| bare substring restored | `_claims_a_fix` body → old `"fixed" in note.lower() and "not fixed" not in note.lower()` | 4 failed exactly as claimed |
| word boundary dropped from `_FIXED` | `\bfixed\b` → `fixed` | 2 failed exactly as claimed (`unfixed`, `prefixed`) |
| negation dropped | `_claims_a_fix` → `bool(_FIXED.search(note))` | 3 failed exactly as claimed, including the pre-existing `test_an_issue_a_manifest_says_it_did_NOT_fix_stays_open` |
| negation window widened to cross punctuation | `[\w\s-]{0,15}?` → `[\s\S]{0,40}?` | 1 failed exactly as claimed (`not a duplicate, open -> fixed`) |

`CAPABILITY-COVERAGE: 4/4 rows reproduced`. File restored byte-identical after each edit and at the end (`diff` clean). This is stronger than the manifest's own paste because it is a fresh run in a copy I built, not a re-read of the maker's log.

## Judgment calls the brief asked for

1. **Over-tightening (the dangerous direction):** not found. Both my marker-gated re-derivation (54/54 unchanged) and the maker's are consistent, and I derived mine from the shipped functions directly.
2. **The `{0,15}` bound:** a tuned constant, not a principle, exactly as the manifest says — I confirmed `(not, after some deliberation, fixed)` (26 chars) reads as a claim, which is the residual false-accusation shape the bound doesn't close. I judge the **fix as right and the bound as the correct pragmatic call, not a weak spot**: the proposed structural alternative (require the documented `-> fixed`/`→ fixed` transition) does not survive contact with the corpus — bare `(fixed)`, `(fixed, critical)` and similar arrow-less claims are common and real (AT-044, AT-045, AT-049, AT-057, …), so a structural-only rule would under-detect real claims that exist today. A distance heuristic validated against the full live corpus is the sounder choice available, even though it is not a closed-form guarantee.
3. **Both arrow forms:** confirmed live and handled — `->` and `→` both present in the corpus (e.g. AT-500 vs AT-216/AT-229/AT-249) and both correctly read as claims by `\bfixed\b`, since the arrow character doesn't participate in the boundary. No unicode decode issue in my own re-derivation (ran with `PYTHONUTF8=1`, matched the maker's finding of needing it, no replacement characters).
4. **The disclosed `fix`-vs-`fixed` gap:** real but narrow. I found **3** live marker-scope notes using "fix" not "fixed" (not the manifest's stated "two") — but one of them (AT-027) is on a continuation line and never reaches `_claims_a_fix` at all regardless (see finding AT-509 below), so the manifest's count of notes that actually reach the predicate (2: AT-033, AT-035) is correct. Both are already `status: verified` via other means, so today's impact is zero. I judge leaving it unwidened as **right** (widening to `fix\w*` would readmit `prefix`), and filed it for tracking per this project's own precedent of giving disclosed "Known limits" items a row (AT-502, AT-507) — **AT-510**, low.
5. **Hunt for the next one:** found one. `_is_marker_line`'s single-physical-line gate makes `check_qa_issue_rows` blind to any issue id named on a **continuation line** of a multi-line `**Issues addressed:**` list. Reproduced live against 11 real ids across three manifests (`at011-loop-md.md`, `at357-scope-sandbox-assertions.md`, `at379-scrollable-pane-reachability.md`) — none of them reach `named` or `claimed`. **Direction, checked not assumed: a MISS, never a false accusation** — an invisible id can't trigger `ledger-row-stale` (over-accuse) any more than `ledger-row-lost` (under-protect); it is simply never examined either way. Live, not theoretical, on those three manifests today; only the *consequence* (an actual lost/stale row landing on one of those ids) hasn't happened yet. I also checked and **ruled out** `qa/manifests/at496-the-ledger-never-loses-a-row.md` lines 12–13 as a candidate instance: its wrap does not hide an id — `AT-475` sits on the marker line itself, and the continuation carries no id at all. Pre-dates AT-508 (it is in `_is_marker_line`, not in `_claims_a_fix`) — not a defect of this unit's own claims. Filed as **AT-509**, medium, since it is the same invariant (C10/AT-496) silently unenforced for a whole class of manifest formatting, and this module has now re-acquired a marker-scoping defect on four consecutive units.

## Live browser

Not UI-touching. Changed paths: `src/autotester/ledger/checks.py`, `tests/test_ledger_checks.py`, `qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/*`. No UI surface, direct or indirect (retrieval/ranking), is affected.

```
VERDICT: PASS
SCOREBOARD: 4/4 capability rows reproduced, 0/0 criteria contradicted, all C10/C7 verify commands re-run and matched
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced (fresh throwaway copy, green pre-edit baseline, restored clean)
LIVE-BROWSER: not-applicable (no UI-touching paths changed: src/autotester/ledger/checks.py, tests/test_ledger_checks.py, qa/evidence/*)
ISSUES-WRITTEN: AT-509 (medium, continuation-line blindness in check_qa_issue_rows/_is_marker_line), AT-510 (low, disclosed "fix"-vs-"fixed" gap, tracked per AT-502/AT-507 precedent)
EXPLANATION: The manifest's claims hold up under independent re-derivation against the shipped functions (54/54 marker-gated notes unchanged), the 4 mutation rows reproduce exactly in a fresh throwaway copy with a proven-green baseline, and the diff is narrow and additive (C10 satisfied). Two new findings are pre-existing/adjacent gaps in the same module, neither a defect in what this unit actually claims to fix, so they are filed to the ledger rather than failing the unit. AT-508 closed fixed in qa/issues.jsonl with an evidence-bearing fixed_by.
```
