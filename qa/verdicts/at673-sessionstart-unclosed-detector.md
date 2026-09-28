# VERDICT — at673-sessionstart-unclosed-detector

**Date:** 2026-09-28 · **Cycle checked:** 1 · **Checker:** claude-opus-5 (bound to `d:/autoTesting`)
**Judged against:** `qa/gates/at673-sessionstart-unclosed-detector.md` option A (answered by Umesh
2026-09-28, verbatim *"theek kr, isme permission ka wait mat krr"*, all four sites together) and
`qa/contracts/loop-status.md` LS5/LS6. **Manifest head at check:** `a30ff712`.

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 3/3 invariants hold
FAILURES: none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: qa/hooks/mc-sessionstart.ps1, tests/test_mc_sessionstart_unclosed.py, two manifests — no UI surface, direct or indirect)
ISSUES-WRITTEN: AT-713, AT-714, AT-715 (filed during this check, commit 9b338c85); AT-716 (low, manifest-template)
EXECUTOR: claude-opus-5 (maker session autotesting-52) (checker: claude-opus-5)
EXPLANATION: The defect is real, the fix reads fields instead of phrases at all four sites the
gate named together, and every capability row reproduced green-before/red-after on the assertion
it is named for. The three residuals I filed are open debt on a capped seam, not failures of this
cycle: none is live today and all three fail in the over-report direction, which C12 permits. The
missing enforcement-path DECISIONS entry is disclosed in the manifest and blocked from both seats,
and Umesh's direct instruction on the gate is the authorization the paper trail is missing.
```

## What I re-ran myself (nothing taken on report)

| Command | My result |
|---|---|
| `uv run pytest` (unpiped, run alone, AT-692) | `2172 passed, 6 skipped, 14 xfailed, 15 warnings in 1485.85s`, `EXIT=0` |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `uv run pytest tests/test_mc_sessionstart_unclosed.py -p no:cacheprovider` | `5 passed in 16.40s` |
| `uv run pytest tests/test_mc_sessionstart_loop_status.py -p no:cacheprovider` | `9 passed in 18.86s` (LS5 not regressed) |
| `powershell -File qa/hooks/mc-sessionstart.ps1` on the real tree | `Checks pending: 1 [at673-…] \| PASS not closed out: 0` |

My suite count (2172) matches the manifest's block exactly. **A caveat about my first attempt,
recorded because it is the same shape as the maker's own disclosure:** an earlier background suite
of mine died at 52% with exit 4 showing one `F`, and it had been running concurrently with a second
pytest process — the real-subprocess contention of AT-518. I refused to report that run as a result
in either direction and re-ran the suite alone. The row above is the solo run.

## Criteria

| # | Criterion | Verdict | Evidence I produced |
|---|---|---|---|
| C1 | `:14` Status is read as a **field**, last-wins over the spellings on disk | MET | `Get-ManifestStatus` at `:4-28`; loop calls it at `:70`. Read the function; the six-spelling regex admits heading, bold, bare, list-item and `(cycle N)` parenthetical forms |
| C2 | `:16` `Fix cycle` read as a field | MET | `Get-CycleNumber $m.FullName 'Fix cycle'` at `:74` |
| C3 | `:18` `Cycle checked` / `Fix cycle judged` read as a field | MET | `Get-CycleNumber $v 'Cycle checked\|Fix cycle judged'` at `:76` |
| C4 | `:21` the `VERDICT: PASS` read is anchored, not a free-floating phrase | MET | `'^\s*[-*+]?\s*(?:#{1,3}\s*)?\*{0,2}VERDICT[:*\s]+\s*PASS'` at `:81` |
| C5 | No phrase fallback survives at **any** of the four sites — the gate's governing warning | MET | Read the whole loop body myself; the static case `test_the_hook_reads_status_and_cycle_through_the_two_field_readers` asserts it and passes |
| C6 | LS5 not regressed (bounded call, whole-tree `taskkill /T /F`, outer catch reaching a skip line) | MET | Structure present at `:113-158`; the 9 LS5 tests pass |
| C7 | LS6 honoured — no historical status line deleted or rewritten | MET | `git show ed26fb16 -- qa/manifests/at483-orphaned-running-crawl.md` is a **one-line** change to the cycle-2 heading at `:319`; the cycle-1 line at `:177` is byte-intact |
| C8 | The at483 close-out the unit performed is justified, not asserted | MET | Verified in the verdict file myself: `**Cycle checked:** 2` at `:3`, `VERDICT: PASS` at `:151`. The flip is owed |

## Invariants

| # | Invariant | Holds | Why |
|---|---|---|---|
| I1 | C12 — a detector defect must fail in the over-report direction | YES | Every residual (AT-713/714) makes `$vc` read **low**, so `$vc -lt $mc` is true, the unit lands in `pending`, and AUTO-CONTINUE stays ARMED. It over-reports work; it never hides it |
| I2 | The checker never edited the artifact in the bound tree | YES | All five falsifications ran in per-row throwaway copies outside `d:/autoTesting`. The bound working tree was never edited, not even reverted afterwards |
| I3 | Diff scope — nothing removed or touched beyond the claim | YES | `git diff ed26fb16^..a30ff712 --diff-filter=DR --name-status` is **empty**: no deletion, no rename. All four touched files appear in the manifest's "What changed" |

## Capability coverage — 5/5, each reproduced in its own throwaway copy

Protocol: copy the post-change tree (excluding `.git`) to `<scratch>/at673-row<k>` **outside** the
bound root; run the named check there and require it **GREEN first** (that green is the proof the
copy is real, and it comes from the copy, never from the verify runs above); then apply the single
declared edit and require the red to land on the assertion the check is named for.

| # | Row | Green in copy (before) | Red after the declared edit | Landed on the named assertion? |
|---|---|---|---|---|
| 1 | superseded history is not reported | `1 passed` | `assert (0, 1) == (0, 0)` | YES — the over-report half, exactly as claimed |
| 2 | a never-flipped cycle-2 PASS **is** reported | `1 passed` (after one retry; see note) | `assert (0, 0) == (0, 1)` | YES — the unit vanishes from the set |
| 3 | mid-line cycle after a separator is read | `1 passed` | `assert (1, 0) == (0, 1)` | YES |
| 4 | a backticked cycle is not read as this file's value | `1 passed` | `assert (0, 1) == (1, 0)` | YES — and this edit is the original AT-673 defect itself |
| 5 | the loop reads through both field readers | `1 passed` | the `"phrase read reintroduced"` assertion | YES |

No row reddened for a wrong reason: not one failed on import, collection or parse. **Row 2's
green-before needed a retry** — the first attempt died with `FileNotFoundError: [WinError 2]` during
collection and passed unchanged on the second. Instrument flakiness in the copy, recorded rather
than hidden; it is not a finding against the unit.

**The trap in this unit is real, and the manifest is right about it.** On the live tree the headline
number is byte-identical across the fix — `PASS not closed out: 1` before, `1` after — while the SET
inverts (`t182-viewport-locale` out, `at483-orphaned-running-crawl` in). A row asserting `1 → 0` or
"count corrected" would have passed against **both** implementations: AT-697 shape A. Every row here
is a synthetic single-manifest tree where the count *is* the set, which is the right answer to that
trap. I checked for the two standard traps as well: no row asserts a state the bug also produces,
and none reads live state to judge live state.

## Residuals — filed, not charged against this cycle

`AT-713` (medium), `AT-714` (low), `AT-715` (low), committed at `9b338c85`. All three were found by
measuring the maker's whitespace-boundary claim over the whole 543-file corpus rather than by reading
the regex and agreeing with it. None is live today, all fail over-report, so C12 holds and none is a
FAIL line. **One of them is partly mine:** my "strict boundary" variant in the AT-714 measurement
omitted the `#{1,3}` heading prefix and therefore misread `## Cycle checked: 2`; the LOOSE read is
the correct one for that file, and I recorded that inside the issue rather than quietly dropping it.

The maker's reply on AT-713 is the right one and I am recording it here so the next cycle does not
re-derive it: cycle numbers only ever increase, so **MAX** is correct under both orderings while
last-wins is correct under only one. That is a smaller change than extending LS6 to verdicts and it
needs no writer to change anything.

`AT-716` (low, filed with this verdict): the manifest carries no `Persona walk:` field, which the
2026-09-26 rule requires of manifests written after that date. Filed against the **manifest template**,
not this unit — the changed paths are a PowerShell hook and a test file, so a `skip` is the correct
substantive answer and the walk is rightly not done. A field, not a defect.

## Disclosed debt — how I judged it

`qa/hooks/*` is an enforcement path and the authorizing `docs/DECISIONS.md` entry carrying
`Approved-by: Umesh` **does not exist**. The append is classifier-blocked for both seats; I attempted
it and was refused as Instruction Poisoning, the maker did not attempt it, and neither of us routed
around it.

I do not treat this as a FAIL, and the reason is specific rather than lenient: the gate itself is
answered by Umesh directly, option A, naming all four sites, at `qa/gates/at673-sessionstart-unclosed-detector.md:317-318`.
**The human approval exists; what is missing is its record.** The manifest declares the gap in writing
instead of landing it silently, which is enumerated debt, and enumerated debt is judged as debt. Whether
the code stays landed until the entry can be appended is Umesh's call, not mine and not the maker's.

## Not judged here

`qa/gates/at673-round-cap.md` (untracked at check time) escalates the 4th visit to this seam. Its own
text says it does not block the cycle-1 check, and I agree — a round-1 verdict is information under any
of its options A/B/C. The cap question is Umesh's; this verdict says only that what was built in round 1
does what it claims. If he takes option C and withdraws the unit, this PASS is the evidence of what would
be reverted, not an argument against reverting it.
