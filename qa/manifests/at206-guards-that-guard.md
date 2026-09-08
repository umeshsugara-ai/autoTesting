# at206-guards-that-guard

**Unit:** AT-206 + AT-192 + AT-193 + AT-170 — make the class guards guard their class
**Commit:** `9351387`
**Fix cycle:** 1
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

## Status: ready-for-check
