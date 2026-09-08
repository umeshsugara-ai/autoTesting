# VERDICT — at140-crawl-cli-coverage

**Cycle checked: 2** · **Date:** 2026-09-08 · **Commit judged:** `f19471e` (+ `8153a46` for AT-142)
**Contract:** `qa/contracts/consent.md` CN1–CN9 · `qa/contracts/explore.md`
**Adapter:** coding · Docker down, `uv` native · bare `uv run pytest` (`-q` twice is `-qq`)
**Isolation:** `git archive HEAD` into a scratchpad, `PYTHONPATH` pinned (AT-101 — the live tree
was never stashed, checked out or restored; `git status` was clean before and after).

Supersedes the cycle-1 FAIL in git history (`1e08fd6`). Cycle-1 failures AT-143, AT-144, AT-146 and
the filed AT-145 are all re-probed below by execution, not by reading the diff.

```
VERDICT: PASS
SCOREBOARD: 9/9 criteria met, 4/4 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-147 (high), AT-148 (medium)
ISSUES-CLOSED: AT-140, AT-142, AT-143, AT-144, AT-145, AT-146 -> verified
EXPLANATION: All four cycle-1 findings are fixed and each fix was proven by re-running my own
probe, not by reading the maker's. The no-trace test now catches 204 entries led by `profiles/`
where the old glob saw 3; all four bound flags are genuinely pinned (I drifted each one
independently, including the two the maker did not claim); the AT-146 docstring correction names
exactly the two tests that fail under the typer drift; and the grant validation refuses expired and
unparseable expiries without breaking a legitimate grant end to end. Two new findings from the
adversarial pass on `_validate_grant` — a one-day boundary hole (AT-147) and a lookalike-host prefix
match (AT-148) — are fresh issues on new code, not unmet criteria: the runtime safety property holds
in both (`require_consent` refuses; CN5 matching is exact). AT-147 must close before T-145's
production grant is issued.
```

## 1. Verification re-run (mine, on the live tree at `f19471e`)

```
uv run pytest                          637 passed, 2 skipped, 1 warning in 70.17s
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

Counted myself; matches the manifest exactly (633 at cycle 1 + 4 new).

## 2. AT-143 — re-probed, and the sabotage claim confirmed literally

My own probe, whole-`AUTOTESTER_ROOT` diff on a refused `explore demo` in the scratch copy:

| State | exit | entries created | led by |
|---|---|---|---|
| `f19471e` as shipped | 2 | **0** | — |
| `_preflight_consent` call removed | 2 | **204** | `profiles/`, `profiles/demo/BrowserMetrics/…` |

The fixed test fails under that sabotage with the message the manifest quotes:

```
E   AssertionError: a refused run created 204 entries, e.g. [.../profiles, .../profiles/demo,
E     .../profiles/demo/BrowserMetrics, .../BrowserMetrics-6A9FD8CB-8848.pma, ...]
```

Where the cycle-1 glob reached 3 of 211, the `set(root.rglob("*"))` diff reaches all of them.
**AT-143 fixed.**

One correction to the manifest's evidence, in the maker's favour: sabotage K fails **two** tests at
this commit, not one — `test_every_bound_flag_reaches_the_crawl_bounds` also fails ("the CLI never
reached the consent pre-flight"), because the new AT-144 test captures at that seam. Stronger than
claimed; noted, not charged.

## 3. AT-144 — all four bounds, drifted independently

Whole-suite run per sabotage, in the scratch copy, anchor-match asserted before each (a sabotage
that does not apply proves nothing — the maker's own cycle-1 lesson, and my first two attempts here
tripped it: `max_actions=max_actions` matches twice in the file because `approve_cmd` has one too):

| Drift in `explore_cmd`'s `CrawlBounds(...)` | result |
|---|---|
| `max_screens` -> 999 | **1 failed**, 636 passed — `test_every_bound_flag_reaches_the_crawl_bounds` |
| `max_depth` -> 77 | **1 failed**, 636 passed — same test |
| `max_actions` -> 11111 | **2 failed** — that test + `test_the_refusal_names_every_bound…` |
| `wall_clock_s` -> 4444.0 | **2 failed** — same two |

All four are genuinely pinned, not only the two the suite already happened to assert. **AT-144
fixed.**

## 4. AT-146 — the attribution verified, not accepted

Typer default `--max-actions` 200 -> 137, whole suite:

```
FAILED tests/test_crawl_real_cli.py::test_the_refusal_names_every_bound_of_the_run_it_refused
FAILED tests/test_crawl_real_cli.py::test_the_refusals_command_grants_the_run_once_a_human_fills_it_in
2 failed, 635 passed, 2 skipped
```

Exactly the two refusal tests the corrected docstring names, and
`test_approve_writes_a_row_that_covers_the_cli_defaults` still passes — which is precisely why the
old docstring was wrong. The correction is accurate. **AT-146 fixed.** The test was corrected in
place, not deleted.

## 5. AT-145 — refusals, the surviving grant, and the adversarial pass

Every case below run through the real CLI at `f19471e` in a scratch root
(project `demo`, `base_url https://demo.test/`):

| Grant | exit | outcome |
|---|---|---|
| `--expires 2020-01-01` | **1** | "already in the past — this grant would refuse every run" ✅ |
| `--expires never` | **1** | "--expires must be YYYY-MM-DD" ✅ |
| `--expires 2027-02-29` (bad leap day) | **1** | unparseable ✅ |
| `--expires 2028-02-29` (real leap day) | 0 | granted ✅ |
| `--expires 2999-12-31` | 0 | granted (no far-future rule; not a criterion) |
| `--target https://unrelated.test/` | 0 | warns, proceeds ✅ (CN5 rationale) |
| `--target ""` | 0 | warns, proceeds |
| project with `base_url=""` | 0 | silent, no crash ✅ |
| `--target https://demo.test/evil` (sub-path) | 0 | silent ✅ correct |
| **`--target https://demo.test.evil.com/`** | 0 | **silent — should have warned → AT-148** |
| **`--expires <today>`** | **0** | **granted, then refused at run time → AT-147** |

**The legitimate flow is not broken** — the critical check: `approve … --expires <tomorrow>` exits 0
and `require_consent(proj, store, CrawlBounds())` on that same store then returns without raising.
Confirmed end to end in a fresh root, independent of the suite. **AT-145 fixed** for the cases it
claimed; two residuals filed.

**AT-147 (high).** `_validate_grant` uses `expiry < date.today()`; `RunApproval.is_expired` uses
`datetime.now() > datetime.fromisoformat(expires_at)` — midnight of that day. So `--expires <today>`
prints the green granted line and is then refused: `- appr_cc67c27c603c: expired 2026-09-08`. That
is the AT-145 defect exactly, one day narrower. It matters because T-145's production grant is the
same-day one-shot an operator would most naturally date today.

**AT-148 (medium).** `target.startswith(proj.base_url.rstrip("/"))` accepts
`https://demo.test.evil.com/` against `https://demo.test/`, so the advisory added to catch a
mistyped target is silent on the mistyped shape that looks deliberate. Bounded: CN5 matching is
exact at run time, so no approval is widened and nothing unsafe can run — the defect is the missing
warning, not a hole in the gate. Compare scheme+netloc for equality before any path prefix.

## 6. No weakening (cycle 1 → cycle 2 diff over `tests/`)

Deletions in `git diff f564d0d f19471e -- tests/` are exactly two: the broken glob assertion (which
AT-143 proved could not see the artefact it named — replaced by the whole-root diff **plus** a new
`exit_code == 2` assertion the old version did not have) and the docstring AT-146 disproved. No test
removed, no assertion loosened, no `xfail`/`skip` added. Test count 10 -> 14.

## 7. AT-142 — the ERP credential gate file (`8153a46`), verified separately

`qa/gates/erp-credentials.md` states the question, the answer route, `Status: OPEN`, an `Approver`,
and an `Answered:` stub. Its blocking claims check out against `.goal/goal.json`: **T-122** (`high`,
pending) and **T-145** (`critical`, pending), both correctly characterised; the "nothing else is
blocked" claim is consistent with the session's unblocked-unit picking. Its two factual claims were
re-run, not read: `find projects -name crawl -o -name flowspec.json` returns nothing (the explorer
has indeed never touched a real product), and `scripts/check_crawl_approval.py erp` exits **1**
("no finished crawl on disk for 'erp' (0 crawl dirs)"). **No credential value appears in the file** —
it names only the keys `ERP_EMAIL`/`ERP_PASSWORD`, forbids pasting values into the repo, and gives
the correct reason (the repo is public). A grep for password-assignment, address and long-token
shapes returns nothing. **AT-142 fixed.**

## Criteria

| | |
|---|---|
| CN1 | ✅ proven at the CLI entry point by whole-root diff; 0 entries shipped, 204 caught under sabotage |
| CN2 | ✅ pre-flight is additive; the seam check in `run_crawl` is untouched (sabotage K still exits 2) |
| CN3 | ✅ unchanged by this unit |
| CN4 | ✅ unparseable refused at grant time *and* still treated as expired at run time; AT-147 is a same-day boundary, not an eternal grant |
| CN5 | ✅ exact matching unchanged; the new base_url check is advisory only and never widens a match (AT-148 is the advisory failing silent, not the gate) |
| CN6 | ✅ every bound in the refusal, pinned by two tests; the filled-in command grants exactly the refused run |
| CN7 | ✅ untouched |
| CN8 | ✅ re-run: `check_crawl_approval.py erp` exits 1 |
| CN9 | ✅ tests grant real `RunApproval`s; no localhost bypass introduced |
| I1–I4 (`core-invariants` C1/C2/C3/C6) | ✅ `doctor: clean`, `ruff` clean, no file over cap, no duplicate concept |
