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


---

# CYCLE 2 — at673-sessionstart-unclosed-detector

**Date:** 2026-09-29 · **Cycle checked:** 2 · **Checker:** claude-sonnet-5-5 subagent (bound to `d:/autoTesting`)
**Judged against:** `docs/DECISIONS.md` D-056 (ACTIVE, `Approved-by: Umesh`), `qa/gates/at673-round-cap.md`
answer B, `qa/contracts/loop-status.md` LS5/LS6, `core-invariants.md` C12 and the cycle-1 criteria
C1-C8. **Manifest head at check:** cycle-2 fix commit `8ea308ee`; bound tree HEAD moved during the check
(`6c2b2be4` -> `036a5024`, see the suite row). The cycle-1 verdict above is untouched.

```
VERDICT: FAIL
SCOREBOARD: 11/12 criteria met (C1-C8 still hold; D-056 rows AT-713, AT-714, AT-715 all met; the D-056 SCOPE bound is not met), 2/3 invariants hold outright (I1 holds on the measured corpus only, see below)
FAILURES:
- [D-056 scope] sev: medium · the inline-code strip at mc-sessionstart.ps1:77 is a fourth change outside the three waived rows, its stated premise does not reproduce, and it carries a fail-open regression cycle 1 did not have · revert the strip and its test to stay inside three rows, OR Umesh ratifies it (one DECISIONS entry that also decides AT-722) and the checker re-PASSes with no code change · issue: AT-741
CAPABILITY-COVERAGE: 3/3 rows reproduced (each green in its own copy before the edit, red on the named assertion after)
LIVE-BROWSER: not-applicable (changed paths: qa/hooks/mc-sessionstart.ps1, tests/test_mc_sessionstart_unclosed.py, qa/QUEUE.md, the manifest; no UI surface, direct or indirect)
ISSUES-WRITTEN: AT-741 (medium), AT-742 (low), AT-743 (medium); annotated AT-722; AT-713/714/715 -> fixed; AT-719 -> wontfix
EXECUTOR: maker session (claude) (checker: claude-sonnet-subagent)
EXPLANATION: All three waived rows work and I reproduced each. The unit fails on ONE thing, scope: the maker added a fourth change (the inline-code strip) that D-056's Result clause does not authorize, on a seam whose whole cap exists because this fix keeps widening. I do not think the strip is wrong on the corpus, which is why the remedy is a one-line human decision or a revert rather than a rebuild.
```

## What I re-ran myself (nothing taken on report)

| Command | My result |
|---|---|
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `uv run pytest tests/test_mc_sessionstart_unclosed.py -p no:cacheprovider` | `8 passed` (twice; second with `-W error::DeprecationWarning -W error::SyntaxWarning`, still 8 passed, so AT-715 is closed) |
| `uv run pytest tests/test_cli_harness_safety.py` alone | `4 passed in 20.57s` (includes the test the manifest says failed) |
| `uv run pytest tests/test_redact_wrap_perf.py` alone, twice | `18 passed`; the 500 KB bound test took **1.80s** against a 3.0s bound |
| `uv run pytest -p no:cacheprovider` (whole suite, ONCE, redirected to a file, not piped, AT-692) | `1 failed, 2174 passed, 6 skipped, 14 xfailed, 15 warnings in 1602.59s`, `PYTEST_EXIT=1`. The one failure is `tests/test_goal_contract_registration.py::test_revised_goal_contract_is_registered`, see the ruling below |
| `powershell -File qa/hooks/mc-sessionstart.ps1` on the real tree | `Checks pending: 2 [at673-sessionstart-unclosed-detector, at710-decision-citation-resolver] \| PASS not closed out: 0`. at673 is correctly pending (this check is the awaited one) |

## The non-green suite, ruled on evidence

The adapter's verify says `uv run pytest` expects exit 0. Neither the maker's run nor mine returned 0, so
I state the rule I applied: **a non-green suite fails the unit only when a failure is caused by the unit's
diff.** A failure I can attribute elsewhere is a defect in the tree, filed, and not charged to this unit;
it also means exit 0 is not reproducible on HEAD today, which I say plainly rather than dress up.

The unit's diff is `qa/hooks/mc-sessionstart.ps1`, `tests/test_mc_sessionstart_unclosed.py`, the manifest and
one `qa/QUEUE.md` row. `git diff ed26fb16^ HEAD --stat -- src` is empty: no source file changed.

| Failure | Attribution | Evidence |
|---|---|---|
| `test_cli_harness_safety::..._leaves_the_repository_untouched` (maker's run) | **Not unit-caused; not reproducible.** Fingerprint test that asserts the repo is untouched | Passes alone here (4 passed, 20.57s) **and passed inside my full run**. The tree was being written by other sessions during both runs (`.goal/*`, `qa/.last-tick`, a sweep commit and a D-057 commit all landed mid-run), which is the failure mode the test detects. Consistent with the manifest's account |
| `test_redact_wrap_perf::..._500kb_corpus` (maker's run) | **Not unit-caused.** A wall-clock bound in code this unit never touched | 1.80s alone against 3.0s; it **passed inside my full run**. The maker's 3.43s is a loaded-machine reading (two build subagents were running). `core/redact.py` is unchanged across the whole window. Filed as AT-725 |
| `test_goal_contract_registration::test_revised_goal_contract_is_registered` (my run) | **Not unit-caused.** Deterministic, but from another commit | Fails alone in 0.35s. It pins T-167 deps to `['T-166','T-110']` (test `:50`); commit `ade87168` (D-057, landed during my run) changed `.goal/goal.json` to `[..., 'T-179']`. At `6c2b2be4` and `8ea308ee` the deps match and the test passes. Filed as AT-743 |

So on the unit's own tree the suite is green as far as I can establish: 2174 passed, and the single red test
is a D-057 change made after the unit. I did **not** obtain a clean exit 0 run on `8ea308ee` itself, and I do
not claim one. That gap is why AT-743 exists as a separate row instead of being waved through.

## D-056 rows

| Row | Verdict | Evidence |
|---|---|---|
| AT-713 max over last | MET | `:79-80` `if ($v -gt $n) { $n = $v }`. Row 1 below. Corpus: `at700-setup-vs-subject.md` 1 -> 2 |
| AT-714 boundary no longer admits a bare space | MET | `:78` boundary `(?:^|[^\w\s` + backtick + `])`. Row 2 below. Probe: `see manifest Fix cycle: 5 of 3` reads 5 under the cycle-1 hook, -1 now. Corpus: `sweep-2026-09-22b.md` 3 -> -1 |
| AT-715 raw docstring | MET | Module imports clean under `-W error::DeprecationWarning`; `r"""` at the AT-713/714/715 docstrings and the AT-673 backtick case |

## Capability coverage, 3/3 reproduced

Each row in its own throwaway copy (`scratchpad/at673-row1..3`, outside the bound root; only
`tests/test_mc_sessionstart_unclosed.py` plus `qa/hooks/mc-sessionstart.ps1` and an empty `pytest.ini`, which is
all the named check reads because the test resolves the hook from its own file's parent). Every falsifying
cell was a single-hunk edit to `qa/hooks/mc-sessionstart.ps1`, a file the manifest names, so all were admissible.
The bound tree was never edited.

| Row | Green before, in the copy | Edit applied | Red after, and which assertion |
|---|---|---|---|
| AT-713 highest wins | 8 passed | replaced `$v = ...; if ($v -gt $n) { $n = $v }` with `$n = [int]$mm.Groups[1].Value` | 1 failed, 7 passed: `test_the_highest_cycle_wins_when_a_verdict_lists_its_newest_first`, `assert (1, 0) == (0, 1)`, the signal comparison itself |
| AT-714 bare word is prose | 8 passed | removed `\s` from the negated boundary class (read of "put `\s` back inside": the manifest's wording is ambiguous, since the shipped class is a negation; this is the edit that makes whitespace a legal boundary again) | 1 failed, 7 passed: `test_a_cycle_named_after_a_bare_word_is_prose_about_another_file`, `assert (0, 0) == (1, 0)`, matching the manifest's stated `(0, 0)` |
| Quoted heading | 8 passed | deleted the `[regex]::Replace($line, ...)` strip line | 1 failed, 7 passed: `test_a_quoted_heading_is_not_readable_through_the_heading_allowance`, `assert (0, 1) == (1, 0)` |

None reddened on import or parse; in each case exactly the named test failed on its own `_signals(...)` assertion
and the other seven passed. Row 3 also proves something the manifest does not say: with the strip removed the
AT-713 and AT-714 tests still pass, so the strip is not needed by either waived row.

## The scope ruling, and why this is a FAIL

D-056: scope is "exactly this scope and nothing beyond it": AT-713, AT-714, AT-715. Its Result clause: "Not
authorized by this entry: any other change to `qa/hooks/mc-sessionstart.ps1`". The gate answer says
"Nothing else in `qa/hooks/mc-sessionstart.ps1` is opened by this answer." The manifest itself says "A fourth
change needs a new waiver", then makes one (the per-line inline-code strip) and asks the checker to rule,
adding that if the checker reads it as exceeding D-056 "the correct outcome is a FAIL on scope and a new waiver,
not a quiet acceptance". I read it as exceeding, for three reasons I reproduced rather than reasoned:

1. **The premise does not reproduce.** The manifest says cycle 2 introduced the quoted-heading hole and that
   the strip completes the boundary AT-714 authorizes. I ran the shipped `Get-CycleNumber` from `ed26fb16` (old)
   and `8ea308ee` (new) on the line ``The old read misread `## Cycle checked: 2` here.``: **old reads 2, new
   reads -1.** The hole pre-dates cycle 2 (the old bare-space alternative admitted the heading). The strip fixes a
   pre-existing hole that MAX makes worse. That is a separate fix, not a completion of AT-714, and AT-713/714 pass
   without it.
2. **It carries a fail-open regression cycle 1 did not have.** The odd-backtick shape of AT-722 reads **-1 under
   old and 42 under new.** The leak exists only because of the strip. Fail-open here means an over-read cycle
   hides a pending check, the direction C12 forbids. Not live on the corpus (0 of 547 files), but it is a
   regression on an input cycle 1 handled correctly.
3. **It is an enforcement path.** `qa/hooks/*` needs an `Approved-by` entry for the change under the Lab Protocol,
   and D-056 supplies one only for three rows.

I hold this at above 80% but not at certainty: D-056's `Changes-authorized` names `Get-CycleNumber` only, and the
strip is inside it, so a reasonable reading places it under "boundary tightening". If Umesh reads it that way,
the remedy is one DECISIONS entry ratifying it and the checker re-PASSes with no code change. That is a scope
decision, so it is his. I recommend ratifying, because on the measured corpus the strip is net-positive, but only
together with a decision on AT-722 in the same waiver: ratifying a strip whose regression stays open would be the
"partial fix worse than no fix" this seam has produced four times.

## AT-722 and AT-723 left open: consistent with D-056

Yes. D-056 scopes the cycle to three rows and closes the seam afterwards; a parity guard or fence tracking is a
fourth and fifth change. Declining to widen further is the correct reading of the bound, and I do not demand them.
AT-723 (fenced blocks) is pre-existing and identical in old and new (both read 7). AT-722 is different in kind:
it is a cycle-2 regression and is charged through AT-741, not as a separate demand. Both remain open.

## Diff scope (step 4c)

`git diff ed26fb16^ HEAD --diff-filter=DR --name-status` is empty: nothing deleted or renamed. `8ea308ee` touches
`qa/QUEUE.md`, which the manifest's "What changed" does not list. It is a single table row (the D-056 -> D-057
citation correction the ledger row AT-718 asked for), disclosed in the commit body, no code. I do **not** charge it
as a FAIL and I do not treat it as mechanical either: AT-721 already records it, and I agree with that row's
reasoning while noting the rule is stated without an exception. I am not at 80% that a FAIL is right, so it stays
in this section.

## The 546-file answer set

Re-derived with the hook's own name pairing (manifests read with `Fix cycle`, verdicts with
`Cycle checked|Fix cycle judged`) by loading `Get-CycleNumber` out of the real `.ps1` for both commits, over 547
files: exactly **four** answers change: `at673-...` verdict 2 -> 1 (the strip), `at700-setup-vs-subject` 1 -> 2,
`sweep-2026-09-22b` 3 -> -1, `t162-drive-2b.b` -1 -> 1. That is the manifest's table of three plus its prose
mention of the strip, so **AT-719's claim of a fifth changed file (`at496`) does not reproduce**: it appears only
when a manifest is read with the verdict name set, which the hook never does. Per C12 ("the construction has to be
the one the claim is about") I marked AT-719 `wontfix` with the reasoning. This is a correction to a colleague's
row, made on evidence.

## Other findings (filed, not charged)

- **AT-742 (low):** the comment block at `:39-42` still says the strip was "tried here first and removed" and
  "LAST field wins (LS6)" above code that has the strip and takes the maximum. Documentation only.
- **AT-724 (already open):** the manifest states the post-change hook reading twice with different numbers. I
  confirmed both sentences are in the file.
- **AT-716 (already open):** the manifest carries no `Persona walk:` field; `skip` is the correct substantive
  answer (PowerShell hook and a test, no UI surface).

## Invariants

| # | Invariant | Holds | Why |
|---|---|---|---|
| I1 | C12, a detector defect fails in the over-report direction | **On the corpus only** | The three waived rows narrow the fail-open surface (bare-word prose no longer counts). But MAX plus the strip leave reproducible fail-open shapes (AT-722, a cycle-2 regression; AT-723, pre-existing), 0 live in 547 files. Enumerated debt with ids, charged once through AT-741 |
| I2 | Checker never edited the artifact in the bound tree | YES | All three falsifications ran in throwaway copies under the scratch dir; the bound tree was only written at the ledger and this verdict, after the suite finished |
| I3 | Diff scope: nothing removed or renamed | YES | `--diff-filter=DR` empty; one undeclared doc-only path (`qa/QUEUE.md`) recorded in AT-721 |

## Not done, and why

No push (D-007 applies to PASS only). The manifest is not edited and its Status stays as the maker left it;
the maker answers by either reverting the strip or by Umesh's ratification. `qa/gates/` was not written: the
decision needed is stated in AT-741 and here, and it is Umesh's, so the maker's next tick should raise it as a
HUMAN_GATE citing this verdict.

---

# VERDICT, fix cycle 3 (revert the strip, D-058 point 4)

**Date:** 2026-09-30 · **Cycle checked:** 3 · **Checker:** claude-sonnet-5-5 subagent (bound to `d:/autoTesting/.worktrees/at673-c3`)
**Judged against:** `docs/DECISIONS.md` D-058 point 4 (ACTIVE, `Approved-by: Umesh`, scope: remove ONLY the
per-line inline-code strip and its test), D-056 (the three waived rows), `qa/contracts/loop-status.md` LS5/LS6,
`core-invariants.md` C12, cycle-1 criteria C1-C8. **Head at check:** `d43590ef`, base `9daa5a02`
(`git merge-base master HEAD`). The cycle-1 and cycle-2 sections above are untouched.

```
VERDICT: PASS
SCOREBOARD: 12/12 criteria met (C1-C8 hold; D-056 rows AT-713, AT-714, AT-715 intact; D-056/D-058 scope bound met), 3/3 invariants hold (I1 on the measured corpus, with the fail-open debt enumerated as ISS-at673-1)
FAILURES: none
CAPABILITY-COVERAGE: 3/3 rows reproduced (two committed-test rows green-before/red-after on the named assertion in throwaway copies; the strip re-add row by loading the real function, because no committed test pins it: disclosed debt ISS-at673-1)
LIVE-BROWSER: not-applicable (changed paths: qa/hooks/mc-sessionstart.ps1, tests/test_mc_sessionstart_unclosed.py, the manifest; no UI surface, direct or indirect)
ISSUES-WRITTEN: ISS-at673-1 (medium, open); AT-741, AT-722, AT-742 -> fixed
EXECUTOR: maker session (claude) (checker: claude-sonnet-subagent)
EXPLANATION: The commit removes exactly the strip line, its 10-line rationale comment and the one test that existed only for it, and nothing else: the hook now differs from 8ea308ee by those 11 deleted lines only, so the seam is back to D-056's three rows. The AT-722 odd-backtick line reads -1 again (42 under 8ea308ee, both loaded from the real hook files), and the AT-713, AT-714 and LS5 tests pass. The price D-058 accepted is real and now has its own open id: a balanced quoted heading reads high again, and no committed test pins either behaviour. The full suite was NOT run by me (explicit evidence gap below).
```

## What I re-ran myself (nothing taken on report)

| Command (bound worktree, each redirected to a file and read back, no pipe, no CLI -q) | My result |
|---|---|
| `uv run pytest tests/test_mc_sessionstart_unclosed.py tests/test_mc_sessionstart_loop_status.py` | `16 passed in 51.30s`, rc=0 (7 unclosed + 9 LS5) |
| `uv run ruff check src tests scripts` | `All checks passed!`, rc=0 |
| `uv run autotester doctor` | rc=1, ONE violation: `stale-generated: docs/SNAPSHOT.md differs from regeneration`. See the ruling below |
| `git diff 9daa5a02...HEAD --stat` | 3 files: hook (11 deletions), test (32 deletions), manifest (77 insertions). Nothing else |
| **Full `uv run pytest`** | **NOT RUN, by instruction (RAM about 0.6 GB free; another step runs one full suite after merge). This is an evidence gap, not a claim of green.** Cycle 2's full run had one unrelated failure (`test_goal_contract_registration`, AT-743), which D-058 point 3 addresses on master |

**Doctor ruling.** The single violation is a stale generated snapshot, not a design-rule breach. The identical
violation prints from `D:/autoTesting` (master, whose working tree carries the uncommitted SNAPSHOT/goal edits
that regeneration reads). This unit's diff touches no `src/` file, no `docs/` file and no `.goal/` file, and its only
test-file change is a deletion, so it cannot have caused it. Not charged to the unit; the maker or a sweep
regenerates the snapshot. I did not re-run doctor on a pristine checkout of the base, so "identical on base" rests
on master's dirty tree plus the diff-scope argument, and I say so.

## Requested verifications

**(a) Exactly the strip and its test were removed, nothing else in the hook.** `git diff 9daa5a02...HEAD -- qa/hooks/mc-sessionstart.ps1`
is one hunk, `@@ -61,20 +61,9 @@`, 11 deletions and 0 insertions: the per-line statement that replaced each
backtick-delimited span with a space, and the 10-line comment that explained it ("The inline-code strip is BACK ...").
`git diff 8ea308ee HEAD -- qa/hooks/mc-sessionstart.ps1` is those same 11 deletions and nothing more, so cycle 3 is
precisely cycle 2 minus the strip. The test diff is one hunk, the 32-line
`test_a_quoted_heading_is_not_readable_through_the_heading_allowance` and its `@windows_only` decorator; the seven other
tests are byte-untouched. A grep of `tests/` and `qa/hooks/` for the strip's call finds no other reference. MET.

**(b) The AT-722 shape no longer reads 42.** I wrote my own probe (scratchpad `probe.ps1`) that loads the real
`Get-CycleNumber` out of a hook file by AST, so nothing is reimplemented, and fed it the ledger's exact AT-722
line (three backticks, one odd). Against `git show 8ea308ee:qa/hooks/mc-sessionstart.ps1`: **42**. Against the bound
tree's hook: **-1**. The same run shows the rest of the function behaving as before:

| Line shape | 8ea308ee (strip present) | d43590ef (this cycle) |
|---|---|---|
| AT-722 odd-backtick line | 42 | **-1** |
| balanced quoted heading in a code span | -1 | 2 |
| real field | 3 | 3 |
| two fields, newest first (AT-713) | 2 | 2 |
| field after a bare word (AT-714) | -1 | -1 |

A first attempt of mine with a two-backtick variant of the line read -1 under BOTH hooks; that is not the AT-722
shape (its backticks are balanced), so I discarded it and re-ran with the ledger's exact text. MET.

**(c) AT-713 and AT-714 tests still pass.** Both are in the 16 passed above, and I falsified each in its own
throwaway copy below. MET.

**(d) The D-056 seam is closed again.** Base-to-head touches the hook in that one hunk only; the hook now
contains exactly the AT-713 maximum, the AT-714 boundary and (in the test) the AT-715 raw docstring, nothing
else. No enforcement path other than the one D-058 authorizes (`qa/hooks/mc-sessionstart.ps1`, removal of the
strip only) is touched. MET.

## Capability coverage, reproduced by me outside the worktree

Each row in its own copy under the scratchpad (the hook and the test module copied; `conftest.py` omitted because it
imports a repo helper these tests do not use; the venv of `D:/autoTesting` used). The named test ran GREEN in the
copy before the edit, then the single-hunk single-file edit was applied to the copy's hook.

| Row | Green before (in the copy) | Single-hunk edit to `qa/hooks/mc-sessionstart.ps1` | Red after, assertion that fired |
|---|---|---|---|
| AT-713: max, not last | `1 passed` | `if ($v -gt $n) { $n = $v }` becomes `$n = $v` | `assert (1, 0) == (0, 1)` in `test_the_highest_cycle_wins_when_a_verdict_lists_its_newest_first`. It is the named assertion (a semantic (pending, unclosed) mismatch, not an import or parse error) |
| AT-714: no bare-space boundary | `1 passed` | drop `\s` from the boundary class `[^\w\s<backtick>]` | `assert (0, 0) == (1, 0)` in `test_a_cycle_named_after_a_bare_word_is_prose_about_another_file` |
| Cycle-3 claim: strip absent, AT-722 line reads -1 | probe on the copy: -1 | re-insert the strip statement as the first line of the `foreach ($line ...)` body | probe: 42 |

The third row is not a committed test. The manifest says so plainly ("no committed test asserts the AT-722 shape,
because D-058 scopes this cycle to removals"), D-058 does authorize only removals, and I accept that as enumerated
debt rather than an unenumerated claim, charged once through ISS-at673-1. Consequence to state honestly: re-adding
the strip would keep every committed test green, so the revert is guarded today by this probe and by nothing in the suite.

## Criteria and invariants

| # | Item | Verdict | Evidence I produced |
|---|---|---|---|
| C1-C5 | Status, Fix cycle, cycle-checked read as fields; anchored VERDICT read; no phrase fallback at any of the four sites | MET | Hook read in full at the bound head; the static test `test_the_hook_reads_status_and_cycle_through_the_two_field_readers` passes |
| C6 | LS5 not regressed | MET | `tests/test_mc_sessionstart_loop_status.py`, 9 passed |
| C7 | LS6 honoured | MET | This diff touches no manifest history; the manifest's earlier cycles are byte-intact and Cycle 3 is appended below them |
| C8 | The at483 close-out was justified | MET | Judged at cycle 1 and untouched by this diff |
| D-056 rows | AT-713 max, AT-714 boundary, AT-715 raw docstring | MET | Tests pass; two falsified above; AT-715 unchanged from cycle 2 |
| D-058 scope | Only the strip and its test removed | MET | (a) above |
| I1 (C12) | A detector defect fails over-report, not fail-open | **On the corpus only** | Removing the strip removes the AT-722 fail-open regression. The balanced-quoted-heading over-read returns to its cycle-1 state (reads high, which can hide a pending check). It pre-dates cycle 2, D-058 accepted it, it is 0 live on today's tree, and it is now open as ISS-at673-1, not hidden |
| I2 | Checker never edited the artifact in the bound tree | YES | All three reproductions ran in scratchpad copies; the bound tree was written only at the ledger and this verdict |
| I3 | Diff scope: nothing removed or touched beyond the claim | YES | The only removals are the two D-058 authorizes; the one added path is the manifest, the maker's own file |

## Ledger

- **ISS-at673-1 (medium, open, new):** the balanced quoted heading reads high again (2 here, -1 under the cycle-2
  hook) and no committed test pins the AT-722 or the strip-absence behaviour. Not chargeable to this cycle
  (D-058 bounds it to removals); it needs a new waiver from Umesh for a fix that handles both shapes plus committed tests.
- **AT-741, AT-722, AT-742 -> fixed** (fixed by the revert; verification is by the probe above). Their
  `regression_check` is deliberately left null: no committed command fails with the revert undone, and I will not
  enter an allowlisted command that does not, which is the exact `echo ok` case the ledger rules forbid. ISS-at673-1
  is the row that, when fixed, supplies one. Expect sweep check 1c to name them until then.
- **AT-723 (low)** stays open, untouched. **AT-743** is D-058 point 3's on master, not this unit's.
- The ledger has `merge=union`, and I edited three existing rows in place. The maker should read `qa/issues.jsonl`
  after the merge for duplicated ids.

## Not done, and why

- No merge and no push: the maker merges, and D-007's push-on-PASS is the maker's step after this verdict lands on master.
- No goal task closed: `.goal/goal.json` carries no task for this unit.
- Manifest not edited. Its Status stays at ready-for-check for the maker to flip to `checked-PASS` on close-out.

## Addendum (found after the first commit of this verdict)

Running the real hook on the bound tree after writing the verdict printed `Checks pending: 2 [at673-..., at710-...]`, not the
close-out state I expected. I loaded the real functions (scratchpad `real.ps1`): status `ready-for-check`, manifest Fix cycle
read as **7**, this verdict read as **3**. The 7 comes from manifest line 324 (the AT-723 row, which quotes a fenced example
containing a bold Fix cycle field with 7). Findings, all reproduced against the real function:

- That line reads 7 under **both** 8ea308ee and d43590ef (it is an odd-backtick line, the AT-722 family), so this is not a
  consequence of the revert.
- Separately, a bold field quoted in a code span (backtick, `**Fix cycle:** 7`) reads 7 under d43590ef and -1 under 8ea308ee:
  the first asterisk satisfies the boundary class, the second is eaten by the bold allowance, so the backtick exclusion is
  bypassed for bold fields. That one **is** the balanced-quote hole D-058 accepted, in its bold form. Recorded in ISS-at673-1.
- Direction: over-report on a manifest (pending shown when the check is done), so C12-safe. It does not change the PASS. It
  means **the hook will keep printing this unit as pending until the maker flips its Status to `checked-PASS`**; the maker
  should close out from this verdict file, not re-dispatch a check on the hook's word.
