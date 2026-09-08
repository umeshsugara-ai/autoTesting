# Verdict — at177-cli-surface

**Date:** 2026-09-08 · **Cycle checked: 1** · **Commit:** `81efef9` · **Bound root:** `D:/autoTesting`
**Contract:** `core-invariants.md` C7 (the manifest also cites `qa/contracts/ui.md`, which is the
**web UI** contract and has nothing to do with this unit — a bookkeeping error, not a mismatch of
substance; C7 is the criterion actually in play and is what I judged against).
**Adapter:** coding. Docker down, `uv` native, bare `uv run pytest`.

## VERDICT: FAIL

One item, narrow and reproducible in one command. Everything else the manifest claims reproduced
**exactly**, including both of its self-corrections — those are honest, not decorative.

---

## 1. Verification re-run by me (not read)

```
uv run pytest                          734 passed, 2 skipped, 1 warning in 75.34s
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

Matches the manifest on the counts.

**The walker is not vacuous and the matrix is not collapsed.** Executing `shipped_commands()`
myself returns **22** commands (approve · doctor · explore · flowspec approve/request-edit/status ·
ingest frames/list/prep/register/run · ledger add/check/relitigation/weight · login · map ·
providers · report crawl/excel/html · snapshot). `pytest --collect-only` on the matrix test alone
collects **22 items**, and the file collects **34** — one case per command, not one collapsed case.

## 2. The two self-corrections — reproduced, both honest

Harness: isolated `git worktree` at `81efef9` (AT-101 respected — no `stash`/`checkout`/`restore`
in the live tree), every sabotage asserting **anchor matched exactly once + file changed** before
any result was believed (C7).

**(a) "The matrix would NOT have caught AT-166."** Confirmed. Sabotage = drop
`media_prep.UnreadableRecording` from the `except` clause at `cli_video.py:79` (the AT-166 fix
hunk; the naive anchor matches **twice** in that file — the sibling command carries the same
clause — so I anchored on the clause plus its `# AT-166:` comment):

```
AQ vs tests/test_cli_surface.py    anchor matched once, file changed=True -> FAILED lines = 0   (INCONCLUSIVE)
AQ vs tests/test_media_prep.py     anchor matched once, file changed=True -> FAILED lines = 1
                                   test_the_shipped_prep_command_answers_a_refusal_cleanly
```

Exactly what the manifest says: the matrix is INCONCLUSIVE, the targeted test is the one that
bites. Leaving AQ in the record was right.

**(b) "The repo-level test needed the banner oracle."** Confirmed in both directions. Sabotage AT
= `def doctor() -> None:` to `def doctor(project: str) -> None:`.

```
against the BEFORE version (Usage assertion deleted, traceback-only)  -> FAILED lines = 0   (INCONCLUSIVE)
against the SHIPPED version (banner oracle)                          -> FAILED lines = 1
```

## 3. Sabotages AR, AS, AT — 1 each, as claimed

```
AR  review.py:30  status=APPROVED, by=by -> by=None
      anchor matched once, file changed=True -> 1
      FAILED test_flowspec_approve_records_who_approved_it
AS  review.py:39  ReviewStatus.NEEDS_EDIT -> ReviewStatus.APPROVED
      anchor matched once, file changed=True -> 1
      FAILED test_flowspec_request_edit_takes_approval_back
AT  cli.py:32     def doctor() -> None: -> def doctor(project: str) -> None:
      anchor matched once, file changed=True -> 1
      FAILED test_the_repo_level_commands_run_without_a_project[doctor]
```

## 4. Attacking the matrix — it is much narrower than "all 22 driven"

I ran the matrix's own invocation (`<cmd> nonexistent-project nonexistent-id`) against all 22
commands under an empty `AUTOTESTER_ROOT` and recorded the exit code and first line of output.
**18 of 22 never leave click's argument parser** — exit 2 with a `Usage:` banner, because the two
extra positionals are themselves rejected (options-only commands: `doctor`, `providers`, `map`,
`snapshot`, `ledger check`; wrong-arity: `approve`, `explore`, `login`, all three `flowspec`, all
three `report`, `ingest list`, `ledger add/relitigation/weight`). Only **4** reach application
code and produce a real refusal: `ingest frames`, `ingest prep`, `ingest register`, `ingest run`.

So for 18 of the 22 the assertion `"Traceback" not in result.output` is an assertion about click,
not about autotester. The docstring's "narrower than it looks" is honest in direction, but does
not state the measured **4/22**, and the manifest headline ("a smoke matrix over all 22 commands")
and the commit subject ("drive the 15 shipped commands nothing was driving") overstate it.
Filed **AT-180** (medium).

**"Could a command silently succeed on a nonexistent project?" — yes, and I found one.** With the
*correct* arity, `autotester ingest list nonexistent-project` exits **0** and prints
`nope has no sources yet — 'autotester ingest register' adds one.` — indistinguishable from a
real project that has no sources. Every sibling refuses properly (`explore nope` / `login nope` →
exit 1 `no project 'nope' yet`; `flowspec status nope` → exit 1). The matrix cannot notice: it
asserts no exit code at all, and for this command it never even reaches the code. Filed **AT-179**
(high) — a shipped product defect, and precisely the hole the matrix's weak assertion leaves open.

## 5. Attacking the focused gate tests

Behaviour is **correct** everywhere I probed — the gaps here are test strength, not defects:

- `flowspec approve` on a project with **no FlowSpec at all** → exit 1, `no flowspec for 'bare' yet`.
  On a wholly unknown project → the same. Correct, and **untested**.
- `request-edit` on a **DRAFT** spec → exit 0, status moves DRAFT to `needs_edit`, `by` recorded.
  Sane.
- The shipped `test_flowspec_request_edit_takes_approval_back` asserts only
  `status is not APPROVED` — it would pass on any wrong status, and checks neither `by` nor `note`.
- `test_flowspec_status_on_an_unknown_project_is_clean` asserts **only** the absence of a
  traceback: no exit code, no message. `status` is covered barely beyond that.

Filed **AT-183** (low).

## 6. The reports

Refusal-only is **thin, not wrong** — but it does not deliver what this unit's own argument
demands. `tests/test_report_export.py` and `tests/test_crawl_report.py` cover the export functions
well, including positive cases, but contain **zero** `CliRunner` invocations (`grep -c` returns 0
and 0). So after this unit the three `report` commands are driven only through a refusal; the
success path of the shipped command — does it write the file where it says, exit 0, name the path
— is still proven only at the function level. That is exactly the "a test that calls a function
proves the function works; only a test that runs the command proves the product does" distinction
this file's own docstring opens with. A seeded-run positive case is cheap (the fixtures already
exist in `test_report_export.py`) and worth having. Filed **AT-182** (low).

## 7. The AT-176 account — accurate, and nothing was quietly weakened

Reproduced in the worktree: `PREP_COMMAND = "autotester ingest prep"` to `"autotester media prep"`
(anchor matched once, file changed) yields **0 failures** in `tests/test_cli_advice_resolves.py`
and **1** in `tests/test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists`.
The manifest's account is correct and matches the AT-176 ledger row (severity `high`, open).

One refinement to its stated cause: the manifest says the name and its backticks are "different AST
nodes", which is true but is not the whole mechanism — the `ADVICE` regex also excludes any string
carrying `{}` by design, and the surviving literal is ``run `{PREP_COMMAND} ``. Either exclusion
alone hides it. This does not change the finding.

**`git show --stat 81efef9` = 2 files:** `tests/test_cli_surface.py` (+201) and a Status flip on
`qa/manifests/at172-at173-dead-command-shape.md`. `tests/test_cli_advice_resolves.py` is
byte-untouched. Nothing was weakened.

## 8. Adversarial — and this is the FAIL

**Two of the 22 shipped commands overwrite git-tracked files: `map` writes `docs/MAP.md`,
`snapshot` writes `docs/SNAPSHOT.md`** (`cli.py:51-68`). The smoke matrix itself is safe — both are
arity-rejected before any write, and I confirmed the temp root was empty after all 22 invocations.

But `test_the_repo_level_commands_run_without_a_project` **takes no `root` fixture**, so it invokes
`map` and `snapshot` for real against the **live repo**. Proved, not inferred:

```
$ printf '\nZZZ-CHECKER-PROBE\n' >> docs/SNAPSHOT.md
$ git status --short docs/          ->  M docs/SNAPSHOT.md
$ uv run pytest "tests/test_cli_surface.py::test_the_repo_level_commands_run_without_a_project" -q
....                                                                     [100%]
$ grep -c ZZZ-CHECKER-PROBE docs/SNAPSHOT.md   ->  0   (the test erased it)
$ git status --short docs/                     ->  (clean)
```

This is **new with this commit** — `grep -rn '"map"|"snapshot"' tests/*.py` matches no other test.
It means `uv run pytest`, the adapter's own verify command and the one every checker re-runs, now
silently rewrites two git-tracked files in whatever tree it is run in. It is invisible when the
docs happen to be current (as they were in my run) and destroys uncommitted doc edits when they are
not — and this session began with `M docs/SNAPSHOT.md` in exactly that state.

**Why this is a FAIL and not just an issue:** C7's first line is *"a unit is complete only when a
check that someone else can re-run passes."* A verify command that mutates the repository it
verifies is not independently re-runnable in the live tree — it is the failure mode C7 exists for,
introduced inside the unit whose whole subject is C7 discipline.

**Fix direction (cheap):** give that test the same `root` fixture the rest of the file uses, or
drop `map`/`snapshot` from it and assert their no-argument shape via
`runner.invoke(app, ["snapshot", "--print"])` and an equivalent for `map` that writes nothing.
Keep the banner oracle — it is the part that works.

---

## Ledger

- **AT-177** stays `open`. The unit closes most of it (the 15 undriven commands now have a test
  that invokes them) but section 4 shows the drive is shallow for 18 of 22, and it introduced
  AT-181.
- **AT-176** unchanged (`high`, open) — correctly named as the next unit, not deferred.

ISSUES-WRITTEN: AT-179, AT-180, AT-181, AT-182, AT-183.

```
VERDICT: FAIL
SCOREBOARD: C7 — 5/6 sub-clauses met (independent re-run · sabotage assertion · zero-failure
            INCONCLUSIVE reporting · real pasted output · executor-does-not-grade-itself all hold;
            "a check someone else can re-run" fails on AT-181)
FAILURES:
- [C7] sev: high · `uv run pytest` now rewrites git-tracked docs/MAP.md and docs/SNAPSHOT.md,
  because test_the_repo_level_commands_run_without_a_project invokes `map` and `snapshot` against
  the live repo with no tmp root — proved by an injected marker being erased · give that test the
  `root` fixture (or use `snapshot --print` and drop `map`) · issue: AT-181
ISSUES-WRITTEN: AT-179, AT-180, AT-181, AT-182, AT-183
EXPLANATION: Every claim in the manifest reproduced exactly — 734/2, ruff and doctor clean, the
walker's 22 commands and 22 parametrized cases, sabotages AR/AS/AT at 1 each, and both
self-corrections honest in both directions (AQ: 0 against the matrix, 1 against test_media_prep;
the banner oracle: 0 before, 1 after). The AT-176 account is accurate and nothing was weakened.
The unit fails on one thing it introduced: the new repo-level test runs two write-commands against
the live repo, so the project's own verify command mutates the repository it verifies. Separately,
attacking the matrix found a real shipped defect it cannot see — `ingest list <nonexistent>` exits
0 and reports "no sources yet" (AT-179) — and measured that only 4 of the 22 invocations reach
application code at all (AT-180).
```
