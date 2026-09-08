# at185-at187-write-not-change

**Unit:** AT-186 (medium) + AT-185 (medium) + AT-187 (low)
**Commit:** 8298020
**Fix cycle:** 1
**Contract:** `qa/contracts/core-invariants.md` C4 · C7

## AT-186 — the finding, and it is about the guard I had just shipped

The checker sabotaged the **product** rather than the test: it removed the early `return` so
`snapshot --print` echoes **and** writes. **The whole suite came back green.**

Cause: `render_snapshot` reproduces the committed bytes exactly, so a **content hash sees nothing**.

The property I care about is *"nothing was **written**"*. What I actually asserted was *"nothing
**changed**"* — a weaker claim that coincides with it most days and fails exactly when the write is
idempotent, which is the common case for a regenerator.

The fingerprint now carries `mtime_ns` and `size` beside the hash, so a write is visible regardless
of what was written. **Sabotage AX — the checker's own mutation — now fails 1 where it previously
left the suite green.**

## AT-185 — an honest number with a wrong reason is still a wrong claim

I stopped the matrix at 20/22 and justified it: *"valid arguments would make those two write, which
is AT-181 again."*

**Measurably wrong.** `repo_root()` honours `AUTOTESTER_ROOT`, so with the temp root in place those
writes land in the temp root and the repo stays clean — the checker proved it by running
`ledger add` and diffing. The enum value now comes from click and **all 22 reach application code**.

Fixing that broke the placeholder test on enum values, which are not paths and cannot become one.
**Refined rather than loosened:** closed-vocabulary values are exempt; everything else must still be
inside the temp root, because the property is that no placeholder a command might treat as a
**destination** can point at the repository.

## AT-187

The fingerprint watched `docs/` and the repo root only, while `projects/<slug>/` is **where the CLI
actually writes**. Now watches `docs`, `qa`, `src`, `scripts`, `projects`. `.goal/` is deliberately
excluded — the goal monitor rewrites its timestamp every few minutes, so including it would make
this test fail on the clock rather than on a command.

## Evidence

```
SABOTAGE AX (the PRODUCT: --print echoes AND writes -- the checker's own mutation)
  anchor matched once, file changed
  -> failures: 1
     FAILED tests/test_cli_harness_safety.py::test_snapshot_print_is_what_makes_the_repo_level_test_safe
```

That single line is the unit: the same mutation, against the same test, went from **green** to
**failing**.

## The extraction, and the smell it removes

`tests/cli_walk.py` — both test files now import the walker from a helper module instead of one test
module importing another. The checker called that *acceptable but a smell*, and it existed only
because the two files were split at a line cap. Same pattern as `tests/crawl_fake.py`.

It also brought `test_cli_surface.py` back under doctor's cap, **which it had crossed again by 9
lines** — the second time in two commits. I read the doctor output in full this time, which is how I
know.

## Verification (host; Docker down, `uv` native; bare `pytest`)

```
uv run pytest                          739 passed, 2 skipped
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean      <- read in full
```

## Not fixed, and not fixable

**AT-188** — commit `d2d547d`'s message is a pasted pytest failure dump, in a public repo, on the
very commit I flagged for pushing doctor-red. Rewriting pushed history to tidy it would erase the
record of the mistake. That is the same reasoning applied twice already this session, and it applies
here for the same reason.

## Still queued, and it is the next unit

**AT-176** — the dead-command guard does not see `ingest prep`, because the command name and its
backticks live in different AST nodes. **AT-178** — un-backticked advice at `core/consent.py:35`.
**AT-174** — the checker *designed* the causal oracle I said could not exist: trigger the refusal,
run the quoted command as rendered, assert it stops firing. Those three are one unit, and it is next.

## Status: checked-PASS
