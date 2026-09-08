# Verdict — at149-at150-path-containment

**Cycle checked: 1** · **Date:** 2026-09-08 · **Checker:** fresh Mode A subagent, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at149-at150-path-containment.md` (Fix cycle 1, commit `da5940e`)
**Contract:** `qa/contracts/consent.md` CN4–CN7 · `qa/contracts/core-invariants.md` C2/C3/C7

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (CN4, CN5, CN6, CN7), 3/3 invariants re-run hold (C2, C3, C7)
FAILURES: none
ISSUES-WRITTEN: AT-151 (low), AT-152 (low) — both NEW, neither a defect this unit claimed
EXPLANATION: Both fixes are real and both are guarded by tests that fail when the fix is
removed — I reproduced sabotages S and T myself in a `git archive` scratch copy and got exactly
the 2 failures each the manifest claims, on exactly the named test ids. `_is_under` survived a
harder attack than the maker ran: nine additional adversarial path shapes, and every one it gets
wrong it gets wrong in the SAFE direction (spurious note) except the un-normalised `..` case,
filed as AT-152. The edited assertion is a genuine strengthening, not a sidestep.
```

## What I re-ran (my own evidence, not the maker's paste)

```
uv run pytest                          647 passed, 2 skipped, 1 warning in 69.91s   ✓ matches claim
uv run ruff check src tests scripts    All checks passed!                            ✓
uv run autotester doctor               doctor: clean                                 ✓
```

641 before + 6 new = 647. Confirmed independently: `+3` top-level test functions (590 → 593),
two of them parametrized ×2 and ×3.

## CN4 — the grant refusal now names a date (AT-150)

Driven through the real `CliRunner` against `autotester.cli:app` in a scratch `AUTOTESTER_ROOT`:

```
$ approve demo --kind crawl --target https://demo.test/app --expires 2026-09-08
exit 1
--expires 2026-09-08 is today — consent expires at the START of the named day, so a run
today needs --expires 2026-09-09; this grant would refuse every run it was asked about
```

The literal ISO date `2026-09-09` is present. The overclaim AT-150 named is discharged.

**Grant↔runtime agreement (CN4's other clause) still holds** —
`test_the_grant_and_the_runtime_agree_on_every_expiry_they_accept` is in the 17 green tests of
`tests/test_approve_cli.py` and was not touched by this commit.

**But the sibling branch was left behind → AT-151 (low).** The past-date branch of the *same*
`when` expression says only `already in the past` and names no date:

```
$ approve demo ... --expires 2026-09-05
exit 1
--expires 2026-09-05 is already in the past; this grant would refuse every run it was asked about
```

CN4's clause is unqualified — *"A refusal at the grant must also name what the operator should
type instead"* — and this branch does not. It is the same class of defect as AT-150, one branch
over, and the maker fixed only the instance I named. That is the AT-149 pattern in miniature and
I am recording it as such. Filed, not FAILed: it predates this unit, the unit never claimed it,
and burning a fix cycle on a defect outside the submitted claim is the thing the checker rules
warn against.

## CN5 / AT-149 — I attacked `_is_under` harder than the maker did

`_warn_on_target_mismatch` driven directly, 28 cases. All against `base_url` unless noted.

| # | base_url | target | warns? | right? |
|---|---|---|---|---|
| 1 | `/app` | `/apple-secrets` | **yes** | ✅ the AT-149 defect, fixed |
| 2 | `/app` | `/appliance/admin` | **yes** | ✅ |
| 3 | `/app` | `/app` | no | ✅ the base itself |
| 4 | `/app` | `/app/` | no | ✅ |
| 5 | `/app` | `/app/admin` | no | ✅ genuine child |
| 6 | **`/app/`** (trailing slash) | `/app/admin` | no | ✅ `rstrip` handles it |
| 7 | **`/app/`** | `/app` | no | ✅ `path in (stem, base)` — the `stem` arm carries this |
| 8 | **`/app/`** | `/apple` | **yes** | ✅ no trailing-slash escape hatch |
| 9 | **empty base path** (`https://demo.test`) | `/anything` | no | ✅ `stem=""`, `startswith("/")` — everything on the host is under it, which is correct |
| 10 | empty base path | `/` | no | ✅ |
| 11 | `/app` | **`/app/../evil`** | no | ⚠️ **AT-152** — lexically under `/app`, actually resolves to `/evil` |
| 12 | `/app` | `/../evil` | **yes** | ✅ |
| 13 | `/app` | **`/app%2Fevil`** | **yes** | ✅ safe direction — it decodes to `/app/evil` which *is* under the base, so this is a spurious note, never a missed one |
| 14 | `/app` | **`/%61pp/admin`** | **yes** | ✅ same: spurious, decodes to `/app/admin` |
| 15 | `/app` | `/%61pp` | **yes** | ✅ spurious |
| 16 | `/app` | **`/app//admin`** | no | ✅ empty segment, still genuinely beneath `/app` |
| 17 | `/app` | **`/APP/admin`** | **yes** | ✅ URL paths are case-SENSITIVE |
| 18 | `/app` | **`https://DEMO.TEST/app`** | **yes** | ✅ over-warns (DNS is case-insensitive) but **consistent with CN5**, which names host case a deliberately distinct target |
| 19 | **base `/`** | `/anything` | no | ✅ everything is under root |
| 20 | base `/` | `/` | no | ✅ |
| 21 | `/app?x=1` | `/app` | no | ✅ `urlparse` splits the query off the path |
| 22 | `/app` | `/app?x=1` | no | ✅ a query'd endpoint under the base is a legitimate target |
| 23 | `/app#f` | `/app` | no | ✅ fragment likewise |
| 24 | `/app` | `/app` (**identical strings**) | no | ✅ |
| 25 | `/` | `/` (identical) | no | ✅ |
| 26 | `münchen.test/a` | `xn--mnchen-3ya.test/a` | **yes** | ⚠️ IDN and its own punycode read as different hosts — over-warning, and consistent with CN5's exactness; not a defect |
| 27 | `xn--mnchen-3ya.test/a` | same | no | ✅ |
| 28 | `/app` | `https://demo.test.evil.com/app` | **yes** | ✅ AT-148 still holds |

**The asymmetry is the right one.** `urlparse` normalises neither `..` nor percent-encoding, and
in seven of the eight cases where that matters the function errs toward *warning when it need
not* — noise, never silence. The single exception is row 11 (`AT-152`): a `..` target escapes the
base and gets no note. Bounded exactly as AT-149 and AT-148 were — CN5 matches the target string
EXACTLY at run time, so no approval widens; only the advisory goes quiet.

## The warning cannot become a refusal

Confirmed by execution, not by reading: a mismatched target with a valid expiry exits **0**, emits
the note, **and writes the approval row** (`approvals.jsonl`: 1 row). `_warn_on_target_mismatch`
contains a single `typer.secho` and no `raise`/`Exit`, and `_validate_grant` calls it *after* every
refusal branch has already returned. A legitimate grant is never blocked by it.

## Sabotages S and T — reproduced, in my own harness

`git archive HEAD` into a scratchpad (AT-101; no `stash`/`checkout`/`restore` in the live tree).
My harness asserts the anchor matches **exactly once** and that the on-disk file actually changed
before believing any result:

```
BASELINE: 17 passed

SABOTAGE S (path half back to a bare prefix): 2 failed, 15 passed
    FAILED tests/test_approve_cli.py::test_a_path_that_merely_starts_with_the_base_path_is_flagged[https://demo.test/apple-secrets]
    FAILED tests/test_approve_cli.py::test_a_path_that_merely_starts_with_the_base_path_is_flagged[https://demo.test/appliance/admin]

SABOTAGE T (refusal back to the word "tomorrow"): 2 failed, 15 passed
    FAILED tests/test_approve_cli.py::test_approve_refuses_an_expiry_of_today
    FAILED tests/test_approve_cli.py::test_the_expiry_refusal_prints_a_usable_date

RESTORE: 17 passed
```

Exactly the counts and exactly the test ids the manifest claims. Both guards are non-vacuous.

Note what sabotage T proves about the AT-150 fix specifically: reverting the message to the word
fails **both** the new test *and* the maker's edited older one. Under the OLD assertion
(`"tomorrow" in output`) the sabotaged message would have passed. That is the strengthening,
demonstrated rather than argued.

## No regression: the test set only grew, and the one edit is a strengthening

The commit touches exactly one test file. Across all of `tests/`, the diff contains **exactly one
non-addition line**:

```
-    assert "tomorrow" in result.output, "the refusal must say what date to use instead"
+    assert TOMORROW in result.output, "the refusal must name the date to use instead"
```

`TOMORROW` is `(date.today() + timedelta(days=1)).isoformat()` (`tests/test_approve_cli.py:26`) —
a literal ISO date. The new predicate is **strictly stronger**: every output satisfying it also
contains a date, while the old one was satisfied by the bare word. Nothing was deleted, no test
was renamed out of collection, no `skip`/`xfail` was added, assertions in the file went 20 → 26,
top-level test functions 590 → 593. **Strengthening, not a sidestep.**

## Ruling on the method note (the manifest asked for one)

**It belongs in `qa/contracts/core-invariants.md` C7 — and only there. Amended, this verdict.**

The maker is right that AT-131 was correctly refused a home in a *feature* contract: `consent.md`
judges the artifact, not how the maker held the tools. But `core-invariants.md` is the
project-wide contract, and **C7 is already entirely about how verification is done** — "the
executor never grades itself", "the manifest pastes real output, not a summary". A sabotage that
silently applied nothing is a manifest pasting real output from an experiment that never
happened. That is C7's subject exactly, and it is the only place in the project where a rule about
evidence-production is enforceable against every unit.

The evidence is now overwhelming, and this check added two occurrences the maker could not have
counted:

1. AT-140 cycle 1 — maker's no-op sabotage read as "my test is vacuous"; nearly rewrote a correct test.
2. The `at140` checker — `max_actions=max_actions` matched twice in the file.
3. This unit's sabotage T — heredoc mangled the anchor quoting.
4. **This check, attempt 1** — my own T anchor had the wrong indentation. My assertion caught it and said so: `AssertionError: SABOTAGE T: ANCHOR NOT PRESENT -- harness is lying`.
5. **This check, attempt 2** — my repair of the anchor silently did not apply. The same assertion caught it again.

Five occurrences in two days, across three independent agents. Without the assertion, occurrences
4 and 5 would have been reported to you as *"sabotage T: 0 failures — the maker's test is
vacuous"*, and this verdict would have been a FAIL on a correct fix. The rule earned its place by
firing on the checker that was ruling on it.

`qa/loop.md` is the wrong home: it describes the loop's steps and terminal states and is the
maker's own file — a rule the maker writes for itself is not a gate. "Nowhere" is not defensible
at five occurrences.

Amendment applied under the **routine** gate: it adds a criterion clause and weakens none.

## Issues

| id | sev | status |
|---|---|---|
| AT-149 | medium | **fixed** — `_is_under` states the rule once, guarded by sabotage S |
| AT-150 | low | **fixed** — refusal prints the ISO date, guarded by sabotage T |
| AT-151 | low | **new, open** — the past-date branch of the same refusal still names no usable date (CN4) |
| AT-152 | low | **new, open** — `_is_under` compares un-normalised paths; `/app/../evil` escapes the base with no note |

Neither new issue blocks this unit. Both are the *next* instance of a class the unit closed —
which is how AT-149 itself was found, and is the healthy outcome, not a failure of the fix.

## Standing, unchanged by this check

- `qa/gates/at147-expiry-end-of-day.md` remains **Umesh's call**. The maker correctly did not
  adopt it. The third option (store new grants as `<date>T23:59:59`) is on that gate file; so is
  the 23:50-grant-dies-in-ten-minutes edge. Neither maker nor checker may decide it.
- Still no crawl against a real product. This unit does not change that and does not claim to.
- AT-141 + AT-115 remain the sweep's outstanding queue row.
