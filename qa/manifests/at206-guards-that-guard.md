# at206-guards-that-guard

**Unit:** AT-206 + AT-192 + AT-193 + AT-170 — make the class guards guard their class
**Commit:** `9351387`
**Fix cycle:** 2
**Contract:** `qa/contracts/core-invariants.md` C7 (verification is independent) and
`qa/contracts/video-learning.md` VL1. **No new criteria requested** — every claim here is judged
against C7 as written.
**Queue:** this was the sweep's own #1, chosen because the sweep measured the class as
flat-to-rising over nineteen units. This unit is the class, not another instance of it.

## The four issues are one shape: a check that cannot fail is not a check

| Issue | The guard | What it could not see |
|---|---|---|
| **AT-206** (high) | `test_the_collector_sees_the_site_the_class_exists_for` | its own renderer being **deleted whole** |
| **AT-192** (medium) | `advice_scan` constant resolution | AT-176's shape one `import` away — returned *nothing at all* |
| **AT-193** (medium) | `_is_documentation` | a bare f-string or joined documentation statement, scanned as live advice |
| **AT-170** (medium) | *(none existed)* | four ffmpeg behaviours; a checker's four sabotages each failed **zero** tests |

## AT-206, because it is the sharpest one in the repo

`PREP_COMMAND = "autotester ingest prep"` is a plain `ast.Constant`. It yields `ingest prep` **on
its own**, with no rendering at all. Results were deduped to `(file, command)`. So
`assert "ingest prep" in commands` was satisfied by the ingredient, and the f-string that
interpolates it — *the message three fix cycles were spent on, the entire reason the renderer was
written* — contributed nothing the assertion could detect. Disabling the renderer failed nothing.

**The fix is that every result now carries its line.** A composed site and the constant it
interpolates are different lines; dedup is `(file, line, command)`; and the test asserts a site
whose source text *interpolates* `PREP_COMMAND` rather than *defines* it. That site cannot exist
without the renderer.

`len(commands) >= 6` — four sites of slack, which is how AT-178 was unpinned by the same
assertion — is gone. Sites are now pinned individually, by line.

## AT-193 had a second miss inside it

Widening `_is_documentation` to `Expr(JoinedStr | BinOp)` was not enough: a `JoinedStr` holds its
text in **child `Constant` nodes**, and `ast.walk` visits those independently. Excluding the parent
alone left the documentation fully readable through its own children. Every descendant is now
excluded. Found by running the test, not by reading the diff.

## AT-192's fix reports what it still cannot resolve

Cross-file resolution now handles absolute and relative `from … import NAME`. But the honest half
is `unresolved_in_source`: **a hole that returns an empty list looks exactly like a clean scan**,
and that indistinguishability is what let AT-176 and AT-192 each survive a guard written to catch
them. It reports SCREAMING_CASE interpolations it could not value, and deliberately stays quiet on
`{slug}` (a runtime value by design) and on names this module binds to a non-string (a number can
never be a command). Current repo: **11 advice sites, 0 holes.**

## AT-170: the argv is the artifact

`subprocess.run` is intercepted, so no ffmpeg is needed. Asserted: `-ss` after `-i` in **both**
seeking call sites, `ffmpeg_available` as **both** binaries and not either, `probe` returning
`(0.0, 0, 0)` rather than raising, and `plan_chunks(0) == []` so the zero propagates as "nothing to
cut". Note the `-ss` docstrings' own honesty is preserved: the order is kept as the conservative
one across builds, **not** because the failure originally claimed for the other order happens on
ffmpeg 8.1.1 (AT-168 measured both orders byte-identical).

## Verification

- `uv run pytest` → **817 passed, 2 skipped** · ruff clean · `autotester map` · doctor clean, as
  one `&&` chain.
- **Ten sabotages**, each asserting its anchor matched **exactly once** and the file re-read as
  changed, each restored by file copy (never `git checkout` — AT-101, and my own T-131 lesson).
  All ten discriminate: 2, 2, 1, 1, 1, 1 on the collector; 1, 1, 2, 2 on the media boundary.
- The four AT-170 sabotages are the **same four a checker ran to zero failures**. Each now fails.
- `git diff` confirms **zero content change** to the three `src/media` files the sabotages touched.

## The one that came back INCONCLUSIVE, and what it was

Sabotage BF made the hole reporter return `[]` unconditionally. **Zero failures.** The repo has no
holes today, so a detector that can *never* report is indistinguishable from one that finds
nothing — which is AT-206's own shape, arriving inside AT-206's fix, in the same hour.

Reported as INCONCLUSIVE per C7 rather than as a vacuous guard, then closed with a constructed
source carrying a known hole. BF now fails. **That C7 clause is the thing that caught it**; without
it the honest-looking reading is "the sabotage proved nothing was wrong."

## What this unit does not claim

It does not claim the class is fixed. It fixes four instances and one meta-instance. The sweep's
measurement — self-caught 0 of 16, rate flat-to-rising — is not answered by a unit; it is answered
or not by the next several units, and the next sweep should say so plainly either way.

## Status: superseded by cycle 2

---

# Cycle 2 — the guard had its own slack, which is this unit's own subject

Cycle 1: **FAIL, 8/11.** Every failure came from the pressure probes, and the first one is this
unit's thesis landing on this unit.

## AT-210 — I claimed the sites were pinned. They were not.

The manifest said *"sites are now pinned individually, by line"*. The resolve check is
**parametrized over whatever the collector returns**, so deleting a site removes a **case**, not a
test. The checker deleted `core/consent.py`'s advice — *the exact site AT-178 exists for* — and the
run went from 26 tests to 25 with **zero failures**. Nine of the eleven sites were freely deletable.

And removing `len(commands) >= 6` was a **net loss**. It was crude and it left four sites of slack,
which is why AT-178 was unpinned by it — but it bit at six, and I replaced it with nothing.

`EXPECTED_SITES` now freezes the inventory: a vanished site fails a test instead of shortening the
run, and adding one is a deliberate edit. Both deletions the checker used now fail.

## AT-211 — the AT-206 guard survived its own sabotage by coincidence

`test_the_collector_sees_the_COMPOSED_site_not_just_the_constant` gathered line numbers from
**every file** and indexed them into `media_prep.py`'s source. So a decoy `"autotester ingest prep"`
at line 157 of any new module satisfied it — with the renderer deleted. Only a sibling test on
synthetic source caught the deletion at all.

Now scoped to `stages/media_prep.py`. **The checker's exact attack, replayed here** (renderer
folded away + a decoy constant at line 157 of a fresh module), fails 3 tests including that one.

## AT-212 — the hole report had an exemption wide enough to hide a command

`_module_level_names` exempted a name for **being bound**, while `_module_constants` resolves
literals only. So

```python
PREP_COMMAND = os.environ.get("CMD", "autotester ingest prep")
```

was invisible to the collector **and** exempt from the hole report, in one move —
`unresolved_in_source(SRC) == []` still held. A call can return anything, so a call is no longer an
exemption; only a non-string literal or a literal container (`NEVER_A_COMMAND`) is. Measured after
the change: still **11 sites, 0 holes** — the tightening added no noise.

## AT-213 — the ordering was asserted and the program was not

`argv[0]` was never checked, so renaming the binary to `ffmpeg-x` failed nothing. A perfectly
ordered argv handed to a program that does not exist is not a working call. Both ffmpeg call sites
and the ffprobe one now assert the program.

## Verification

- `uv run pytest` → **818 passed, 2 skipped** · ruff clean · `autotester map` · doctor clean, one
  `&&` chain.
- **Six sabotages plus a replay of the checker's own AT-211 attack**, each anchor-matched-once and
  file-verified-changed, restored by file copy (AT-101). All seven discriminate: 1, 1, 3, 3, 1, 1,
  and 3 on the replay.
- The two site-deletions from AT-210 and the `os.environ.get` binding from AT-212 are the
  checker's own constructions, re-run here.

## Worth recording about cycle 1

The checker's C7 zero-failure clause fired **on its own harness**: its first dedup sabotage changed
two of three lines, so the check key and the add key never matched — dedup was *disabled*, not
reverted, and the suite returned **823 passed**, six *more* cases than baseline. It caught that
from the count going up, called it INCONCLUSIVE, and re-ran a true revert. That is the clause
working on the person applying it, which is the only real test of it.

## Status: ready-for-check
