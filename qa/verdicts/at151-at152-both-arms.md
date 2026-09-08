# Verdict — at151-at152-both-arms

**Date:** 2026-09-08 · **Cycle checked:** 1 · **Commit:** 2458b51
**Contract:** `qa/contracts/consent.md` CN4, CN5 · `qa/contracts/core-invariants.md` C2, C3, C7
**Checker:** fresh subagent, bound to `D:/autoTesting`. Docker down; `uv` native; bare `uv run pytest`.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met, 5/5 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-153 (low)
EXPLANATION: Both arms of the grant refusal now name a usable date, and the `..` guard closes the
one silent case in `_is_under` without over-firing on paths that merely contain the characters
`..`. All three claimed sabotages reproduce, and the split lost no test — a full collected-node-id
diff (parametrized ids included) across the whole `tests/` tree shows one renamed test and four
gained, nothing dropped and no parametrization silently removed. The C7 clause the maker built its
harness against turns out to have a hole, demonstrated by my own first sabotage attempt; that is a
defect in the clause I wrote, not in this unit, and it is closed by a routine amendment rather
than charged here.
```

## What I re-ran (my own evidence, not the manifest's)

| Command | Result |
|---|---|
| `uv run pytest` | **650 passed, 2 skipped**, 1 warning, 72s — matches the claim |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |

Collected node ids: 652 at `2458b51` vs 649 at `2458b51^` — 650 passed + 2 skipped = 652, consistent.

## AT-151 — both arms (CN4) · MET

Real CLI, scratch `AUTOTESTER_ROOT`, project `base_url=https://demo.test/`:

```
far-past      2020-01-01  exit 1  "--expires 2020-01-01 is already in the past; ... — use --expires 2026-09-09 or later"
one-day-past  2026-09-07  exit 1  "--expires 2026-09-07 is already in the past; ... — use --expires 2026-09-09 or later"
today         2026-09-08  exit 1  "--expires 2026-09-08 is today, and consent expires at the START of the named day; ... — use --expires 2026-09-09 or later"
tomorrow      2026-09-09  exit 0  appr_09f9ca298704: crawl on https://demo.test/ until 2026-09-09
malformed     09-09-2026  exit 1  "--expires must be YYYY-MM-DD, not '09-09-2026'"
```

Both arms end at the shared sentence, so the class is closed rather than the instance — the
structural point the manifest makes is real, not just rhetoric. **Expiry exactly one day in the
past** (the case asked for explicitly) is correct: it takes the `already in the past` arm and still
names `2026-09-09`. The named date is minimally but genuinely usable — expiry is the START of
2026-09-09, i.e. the end of today, so an operator who pastes it can run today.

**Timezone.** No confusion is reachable: the grant compares `date.today()` (local) and the runtime
`require_consent` uses `datetime.now()` (local naive, `core/consent.py:99`) against
`datetime.fromisoformat` of the same bare date. One clock, one convention, both halves — the CN4
grant↔runtime agreement holds across the boundary rather than only at it. There is no UTC/local
split anywhere on this path (`explore.py:38`'s `datetime.now(UTC)` is a stamp, not a comparison).

## AT-152 — the `..` guard (CN5) · MET, and NOT over-broad

`_is_under` driven directly over 24 shapes against base `/app`:

```
contained (True):   /app  /app/  /app/x  /app/./x  /app//x
                    /app/v..1/x   /app/report..pdf   /app/..x   /app/x..   /app/....//evil
refused  (False):   /app/../evil  /app/a/../b  /app/x/..  /app/..  /../app  /..  ..
                    /apple  /appliance/admin  /APP/x  //app/x  /  ""  /app%2f../evil
```

The over-broad question is answered NO: `path.split("/")` with an exact `..` segment lets
`/app/v..1/x`, `/app/report..pdf`, `/app/..x`, `/app/x..` and even `/app/....//evil` through
(`....` is a literal directory name, not a climb) while refusing every real climb. The maker's
reasoning was right and the implementation matches it.

**AT-153 (low, filed, not charged).** The guard is literal-segment only, so the encoded forms of
the same escape stay silent: `/app/%2e%2e/evil`, `/app/%2E%2E/evil`, `/app/.%2e/evil` and
`/app/..;/evil` all read as contained. Same bounded blast radius as AT-148/149/152 — CN5 matches
exactly at run time, so no approval widens and only the grant-time advisory goes quiet. Queued, not
fixed now (see the stop-decision ruling below).

One spurious warning worth naming and not filing: `https://demo.test:443/app` warns against
`https://demo.test/app` because netloc equality is literal. That errs toward noise, which is the
direction CN5 deliberately chooses, and CN5 already records case/slash/query brittleness as
intended. Not a finding.

## Sabotage reproduction — my harness, my anchors

Every run asserted `count(anchor) == 1` and byte-level file change before believing anything;
tree is `git archive 2458b51` into the scratchpad with `PYTHONPATH` pinned (AT-101), live tree
untouched.

| Sabotage | anchor | file changed | failures | maker claimed |
|---|---|---|---|---|
| **U** — the AT-151 hunk reverted to the pre-fix one-arm `when` expression | 1 | yes | **1** — `test_a_past_expiry_also_names_a_usable_date` | 3 |
| **V** — `if ".." in path.split("/")` → `if False` | 1 | yes | **1** — `test_a_path_that_climbs_out_of_the_base_is_flagged` | 1 ✔ |
| **S** — containment back to a bare `startswith(stem)` | 1 | yes | **2** — `test_a_path_that_merely_starts_with_the_base_path_is_flagged[apple-secrets]`, `[appliance/admin]` | 2 ✔ |

Restored byte-identical; baseline on the restored tree 20 passed.

**U reproduces at 1, not 3, and that is not a discrepancy against the maker.** My mutation is the
tightest possible one — the exact AT-151 diff hunk reverted — and it kills exactly the one test
that guards AT-151. The maker's broader mutation additionally disturbed the shared trailing
sentence, taking two `today`-branch tests with it. A guard that dies on the minimal revert is the
stronger result, so U is credited.

## C7 compliance — the point of this check, and the clause has a hole

The maker's harness satisfies C7 **as written**: anchor asserted exactly once, file change
asserted, both printed before any result was believed, on all three sabotages. Judged against the
clause in force at 2458b51, this is compliant. **PASS on C7.**

But the clause is insufficient, and I proved it on myself rather than by argument. My *first*
sabotage U mutated `"already in the past"` → `"already in the past XXX"`. Anchor matched exactly
once. File changed. Result: **0 failures** — because that string is on a line no assertion reads.
Under the clause as written that is a clean, fully-asserted sabotage reporting a green suite, which
is precisely the "the guard test is vacuous" misreading the clause exists to prevent. The hole is
the one this check was asked to look for, and it is wider than the comment/docstring case: any
mutation on a line no assertion exercises produces it.

`count == 1` and `file changed` prove the patch *landed*; they do not prove the mutation *matters*.
The missing third leg is that a zero-failure sabotage must be reported as **INCONCLUSIVE about the
tests** until the mutation is shown to change behaviour. Amended into C7 today (routine gate,
tightening only, amendment log entry cites this verdict). It is a defect in the clause I wrote a
day ago, not in this unit, so it is not charged against the maker and burns no fix cycle.

## The split lost nothing (C2, C3)

Full collected-node-id comparison across the whole `tests/` tree, `2458b51^` → `2458b51`
(parametrized ids included, so a decorator lost anywhere in the suite would show as vanished `[…]`
cases):

```
649 -> 652 collected
lost:    test_approve_warns_when_the_target_is_not_the_projects_base_url
gained:  test_a_past_expiry_also_names_a_usable_date
         test_a_path_that_climbs_out_of_the_base_is_flagged
         test_a_wholly_unrelated_target_is_flagged
         test_the_exact_base_url_is_not_flagged
```

The single "lost" name is a rename-and-split, and it is a **strengthening**: the old test asserted
`"base_url" in output or "does not match" in output`; `test_a_wholly_unrelated_target_is_flagged`
asserts `"does not match"` outright, and `test_the_exact_base_url_is_not_flagged` adds the negative
control the old single test never had. **No orphan** (ruff clean, collection clean, and an orphaned
body would have surfaced as an F821 exactly as it did on the maker's first attempt). **No
parametrization silently dropped** — every `[…]` id present before is present after. The maker's
disclosure of its failed scripted extraction is accurate and the recovery is sound.

## Ruling on the stop decision — I agree, and I agree the AT-153 style stays queued

Stop. The chain `t124` → `at147-148` → `at149-150` → this has monotonically decreasing severity
(high → medium → low → low), and everything left in this area is **advisory-only**: `_is_under`
feeds one grant-time `note:` line, while the actual consent gate is CN5's exact string match, which
no finding in three passes has dented. AT-153 is real but is the fourth member of a family whose
worst case is a missing warning about a typo the operator would then have to paste verbatim into a
run that matches exactly anyway. Fixing it now would be polishing a warning while
`qa/QUEUE.md`'s actual row waits.

**Explicitly, as asked:** I filed one low finding and I agree it should be **queued, not fixed
now**. It carries a stated fix direction so whoever picks it up does not re-derive the analysis.

I additionally endorse AT-141 + AT-115 as the right next unit, and note the manifest's own
"measured and waiting" line is the strongest argument for it: `T-126`, `T-150` and `T-135` all have
`done_check`s that exit 0 today, before any of their work exists. That is the AT-100 shape three
times over, in the machinery that decides whether *anything* is done — strictly more valuable than
a fourth pass at a `note:` line, and it is C9 territory, where the invariant already exists and is
being violated by live data.

## Contract changes made by this check

- `qa/contracts/core-invariants.md` **C7** — added the zero-failure/INCONCLUSIVE clause + amendment
  log entry. Routine (tightening; adds a reporting duty, weakens nothing).
- `qa/issues.jsonl` — AT-151, AT-152 → `verified` (fixes reproduced by sabotage, not read);
  AT-153 filed `open`.
- `qa/gates/at147-expiry-end-of-day.md` untouched, as the manifest states. Confirmed: it remains
  Umesh's alone and no code in this commit anticipates either answer.
