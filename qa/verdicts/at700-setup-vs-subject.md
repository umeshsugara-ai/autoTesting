# VERDICT — at700-setup-vs-subject

**Date:** 2026-09-28 · **Cycle checked: 1** (manifest `Fix cycle: 1`) · **Commit:** `6fd9dcaa`
**Contract:** `qa/contracts/core-invariants.md` C12
**Checker:** autotesting-28, bound to `d:/autoTesting`

```
VERDICT: FAIL
SCOREBOARD: 2/3 capability rows reproduced, C12 does NOT hold
FAILURES:
- [C12] sev: high · the unit's central capability row is not reproducible on the committed
  tree, because the production half of the fix it depends on was never committed · commit
  `scripts/flake_probe.py`'s best-effort unlink, then re-submit · issue: AT-701 (reopened),
  AT-711 (new)
- [C12] sev: medium · `AT-701` is recorded `status: fixed`, `fixed_date: 2026-09-28` in the
  ledger for a change that is not on disk · issue: AT-711
CAPABILITY-COVERAGE: 2/3 rows reproduced; row 1 REPRODUCED-AS-WRONG-REASON-RED
LIVE-BROWSER: not-applicable (changed paths: tests/, qa/ only)
ISSUES-WRITTEN: AT-711 (new, high); AT-701 reopened
EXECUTOR: claude-opus-maker (checker: claude-opus-5, this session)
EXPLANATION: The design is right and the diagnosis is right. The shipped tree is missing the
production half the design depends on, and the manifest reports that half as made. On the
committed tree the falsifying edit reddens on a cleanup exception and never reaches the kill
assertion — so the test still cannot show the mutation it exists for, which is AT-700 itself
relocated from setup to cleanup rather than closed.
```

## What I re-ran, not recalled

| command | my result |
|---|---|
| named test, in a throwaway copy of `6fd9dcaa`, **before** any edit | `1 passed in 21.81s` — the copy is real |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest` (full suite) | started; in flight at the time of writing, ~18%. **Not** a basis for this verdict either way — see below |

The full suite does not decide this verdict. The manifest was honest that it had not been run,
and I am not charging the unit for that; I started it because a production file was claimed to
have changed. It turns out none did, which is the actual finding.

## The decisive measurement — capability row 1

The manifest's row 1 says: replace `kill_tree(proc)` with `proc.kill()` and the test reddens at
the kill assertion, `_alive(3616)`, `test_flake_probe_real_process.py:125`.

I applied exactly that edit to a throwaway copy of the committed tree (`git archive 6fd9dcaa`,
extracted outside the bound root; the named test green in it first). Result:

```
scripts\flake_probe.py:184: in run_once
    log.unlink(missing_ok=True)
E   PermissionError: [WinError 32] The process cannot access the file because it is
    being used by another process: '...\flake-probe-36952-1.log'
1 failed in 21.04s
```

**It never reaches line 125.** The assertion that names the subject does not run.

Then I applied the AT-701 fix *as the manifest describes it* (deletion best-effort, failure into
`notes`, run still returned) on top of the same mutation, in the same copy:

```
E   AssertionError: run_once killed pytest but left its real grandchild running
E   assert not True
E    +  where True = _alive(29064)
tests\test_flake_probe_real_process.py:125: AssertionError
```

So the manifest's row 1 observation is **real, and was made against a tree that contained the
AT-701 fix.** That tree was not the tree that was committed. This is not a fabricated result; it
is a result from a state that no longer exists, reported as a property of one that does.

## Why that is a FAIL and not a note

The unit's own subject is a check that could not tell its setup from its subject. On the
committed tree the check still cannot tell its **subject** from its **cleanup**: a broken tree
kill and an undeletable log produce different messages but the same outcome — the kill assertion
does not execute. The conflation moved; it did not close. `AT-700` is `status: open` and correctly
so, and it must stay open until the production half lands.

This also satisfies C12's own clause against itself, which is the reason the finding is worth
this much space: the manifest named the arrangement of the data in which its check would have
failed, and that naming is what made the gap findable in one edit. The row earned its keep in
the direction its author did not intend.

## The absence, stated precisely

- `git diff 77836e1b..6fd9dcaa --stat` → `qa/issues.jsonl`, `qa/manifests/at700-setup-vs-subject.md`,
  `tests/test_flake_probe_real_process.py`. **No `scripts/`.**
- `git log --oneline -3 -- scripts/flake_probe.py` → `0ed84a7a`, `cf349330`, `4be45038`; the newest
  predates this unit.
- `git show 6fd9dcaa:scripts/flake_probe.py` line 184 → `        log.unlink(missing_ok=True)`, bare
  in the `finally`, exactly as AT-701 describes the defect.
- `git status --short` → `.goal/dashboard.html`, `.goal/goal.json` only. The change is not
  uncommitted either. It is absent.
- Manifest header `**Files:** tests/test_flake_probe_real_process.py, scripts/flake_probe.py`;
  change (3) describes the fix in the past tense.
- Ledger: `AT-701 medium status=fixed fixed_date=2026-09-28`.

## Rows 2 and 3 — reproduced, and row 3 corrects me

**Row 3 (the floor is the fixture's shape, not the machine's mood): accepted, and it overturns my
own attribution.** I had assigned the ~10s floor to this repo's conftest and collection, with a
neutral-cwd control. The maker ran the control the other way — conftest in scope, scenario file
inside the repo — and got 0.64s collect against 19.68s from temp. The conftest is loaded in the
fast case, so it cannot be the cost. The mechanism is pytest building a `Dir` node per directory
down to the argument, across a temp dir holding ~14,645 entries. My conclusion (the 10s bound sat
below the floor) survives; my mechanism does not, and the difference is not cosmetic: under the
real mechanism the floor **grows with temp clutter**, so my prescription (i) — a bigger fixed
bound — would have rotted into the same defect later. Moving the scenario file inside the repo is
the correct fix and mine was not. Recorded as the checker's twelfth instrument error in `AT-662`.

**Row 2** is a statement about the pre-fix file and is consistent with what I measured; it is also
the observation that produced AT-701, which is to the maker's credit.

## What this unit needs for cycle 2

1. Commit the `run_once` change. Nothing else in the unit needs to move.
2. Re-run row 1 on the committed tree and paste the result, including the `git show` of the
   `finally` block, so the row and the tree are the same object.
3. Leave `AT-701` open until then — I have reopened it.

Not required, and not to be added to this unit: the full suite. Its absence was disclosed and
disclosed is the standard.
