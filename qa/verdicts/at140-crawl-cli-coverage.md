# Verdict — at140-crawl-cli-coverage

**Date:** 2026-09-08 · **Cycle checked: 1** · **Commit judged:** `f564d0d` (manifest `b28e397`)
**Contract:** `qa/contracts/consent.md` CN1–CN9 · `qa/contracts/explore.md`
**Adapter:** coding · Docker down, `uv` native · sabotages run in a `git archive HEAD` scratch
root at `…/scratchpad/at140` with `PYTHONPATH` pinned (AT-101: nothing touched the live tree).

## VERDICT: FAIL

The unit is real work and most of it is exactly what it says it is. Every sabotage count
reproduces to the number, the new tests are non-vacuous, and the two self-corrections are both
accurate — one of them I re-derived the hard way by walking into the identical trap. It fails on
one thing: **the test that carries the unit's headline claim (CN1 no-trace through the CLI) checks
a name pattern inside one subtree, and the artefact AT-111 was actually filed about — the
populated Chromium profile — lives outside that subtree entirely.** And the manifest's "the one
row I would keep" names the wrong test: measured, that row does not pin `explore_cmd`'s typer
defaults at all.

## 1 — Verification, re-run (not read)

```
uv run pytest                          633 passed, 2 skipped, 1 warning in 81.89s
uv run ruff check src tests scripts    All checks passed!   (exit 0)
uv run autotester doctor               doctor: clean
```

All three match the manifest exactly. Bare `pytest` as instructed — `addopts = "-q"` plus a
command-line `-q` is `-qq` and eats the count line.

## 2 — The four sabotages, reproduced

Each patch asserted its anchor matched **exactly once** and `ast.parse`d clean before running —
the maker's own self-correction #1, applied to the checker.

| Sabotage | Claimed | Measured | |
|---|---|---|---|
| K — drop `_preflight_consent` from `explore_cmd` | 1 | **1** — `test_a_refused_crawl_leaves_nothing_on_disk` | ✅ |
| L — `if actions > approval.max_actions:` → `if False:` | 1 | **1** — `test_an_approval_narrower_than_the_run_still_refuses` | ✅ |
| M — a missing `--login-case` ignored | 1 | **1** — `test_a_missing_login_case_is_named_not_ignored` | ✅ |
| N — drop `--max-actions` from the grant command | 2 | **2** — `…names_every_bound…` + `…grants_the_run_once_a_human_fills_it_in` | ✅ |

**K's reasoning verified by execution, not accepted.** With the pre-flight gone,
`test_explore_without_an_approval_exits_two` still **passes** — the seam in `run_crawl` re-raises
and `explore_cmd`'s own `except ApprovalRequired` maps it to exit 2. Confirmed directly: a refused
run with no pre-flight exits **2** and leaves 211 filesystem entries behind. The maker is right
that only the leftover files betray the regression, and right that an exit-code test alone could
never have caught AT-111.

**A checker note on N.** My first cut removed only the `parts.append(...)` line, orphaning
`if actions:` — an `IndentationError`, 7 failures, and a number that looked like a finding.
That is sabotage-anchor discipline failing in the opposite direction from the maker's cut of L,
in the same file, on the same afternoon. The maker's lesson generalises: **verify the sabotage
compiles and the anchor matched before believing any count.**

## 3 — The prior-gap account (verified at `f564d0d^`, not believed)

- **No test invoked `explore` or `approve` through the CLI.** Confirmed by walking every
  `tests/*` blob at `f564d0d^` for `invoke(app` — only `ingest run`, `ingest register`, `login`.
- **Direct `run_crawl` callers:** `git grep` at `f564d0d^` shows **13** call sites in test bodies
  (test_explore 5, test_explore_error_causes 5, test_explore_node_recovery 2, test_explore_live 1)
  plus the `crawl_fake.py` helper. The manifest says twelve. Immaterial, and the substantive claim
  — the shipped commands had zero coverage while the internal entry point had plenty — is exact.

## 4 — Are the tests non-vacuous, and do they cover what matters?

**Non-vacuous: yes, demonstrated in both directions.**
`test_approve_writes_a_row_that_covers_the_cli_defaults` is not a test that can only pass — an
off-by-one probe (`actions > approval.max_actions` → `>=`) fails it, along with 30 others.

**But the manifest attributes its value to the wrong test.** [FAIL-1]
Probe: `explore_cmd`'s `--max-actions` default 200 → 137, whole suite:

```
FAILED tests/test_crawl_real_cli.py::test_the_refusal_names_every_bound_of_the_run_it_refused
FAILED tests/test_crawl_real_cli.py::test_the_refusals_command_grants_the_run_once_a_human_fills_it_in
2 failed, 631 passed, 2 skipped
```

The typer-default drift **is** caught, and — as the manifest claims — it is caught **nowhere else
in the suite**. That half is vindicated. But `test_approve_writes_a_row_that_covers_the_cli_defaults`
**passed** under the drift. It never invokes `explore`; it calls
`require_consent(proj, store, CrawlBounds())`, so what it pins is `CrawlBounds`' schema defaults
against a module constant — not `explore_cmd`'s typer defaults. (Confirmed from the other side:
`CrawlBounds.max_actions` 200 → 137 fails only `…narrower_than_the_run_still_refuses`.) The
manifest's table row "**`explore`'s typer defaults vs `require_consent`**" and its "the one row I
would keep" are therefore misattributed. The protection is real; the named row is not the one
providing it.

## 5 — Adversarial: gaps the manifest admits, and two it does not

Admitted and accepted: `report crawl`, `explore --merge` (needs a completed crawl — correctly
deferred to a browser-backed test), no real crawl run.

**Not admitted — `--max-screens` / `--max-depth` never reach an assertion.** [FAIL-2]
Probe: `max_screens=max_screens` → `max_screens=999` in `explore_cmd`'s `CrawlBounds(...)`:

```
633 passed, 2 skipped   ← the WHOLE suite, unchanged
```

Two of the four bounds `explore_cmd` owns are pinned (actions and wall-clock, via the refusal
text); the other two can be hardcoded to anything and nothing in the repository notices. The
manifest's table lists the bounds row as covered without qualifying which bounds.

**Not admitted — `approve` cheerfully grants approvals that can never work.** [FAIL-3]
Driven through the real CLI in the scratch root:

| `approve demo --kind crawl …` | exit | output |
|---|---|---|
| `--expires 2020-01-01` (already expired) | **0** | `appr_304e…: crawl on https://demo.test/ until 2020-01-01` |
| `--expires never` (unparseable) | **0** | `appr_3846…: … until never` |
| `--target https://evil.example/` (not the project's `base_url`) | **0** | `appr_92e8…: crawl on https://evil.example/` |

The safety property holds — `require_consent` refused all three at run time, and CN4's
"unparseable expiry is treated as expired" is intact. This is a **feedback** defect, not a hole:
the human granting consent for T-145's live production ERP crawl is told "granted" in green and
finds out only when the crawl refuses. AT-140 did not introduce it, and it is out of the unit's
stated scope, so it is a filed issue rather than a FAIL line.

**Reachability note (not a finding).** `explore_cmd`'s own `except ApprovalRequired → Exit(2)`
around `run_crawl` (cli_crawl.py:88-90) is reached by no test — with the pre-flight in place it
can only fire if consent changes between pre-flight and seam. Sabotage K proves it is live code.
Recorded as an observation.

## 6 — The two self-corrections: both accurate

**(a) The no-op sabotage.** Accurate, and independently confirmed: `core/consent.py:55` reads
`if actions > approval.max_actions:`; the string the maker first tried
(`approval.max_actions < actions`) appears nowhere in the file. Reading zero failures as "my test
is vacuous" would have led to rewriting a test that is, in fact, correct — L kills it cleanly.

**(b) The dropped "works verbatim" claim.** Accurate, verified by reading the refusal builder
(`core/consent.py:34-38`) rather than the manifest. The command literally contains
`--scope "<what this run may touch>"` and `--granted-by <name> --expires <YYYY-MM-DD>` — three
human-only placeholders. A test asserting verbatim execution would be asserting that the tool
should invent who authorised a production crawl and until when. Dropping the claim was right, and
the replacement (substitute the placeholders, then require that the filled-in command grants
*exactly* the refused run and not a narrower one) is the stronger property.

## 7 — The no-trace test's glob is not strong enough [FAIL-4 — the reason this is a FAIL]

`test_a_refused_crawl_leaves_nothing_on_disk` globs `root/projects/demo` for names containing
`"crawl"` or `"profile"`. I ran the refused CLI run with the pre-flight removed and diffed the
**whole** `AUTOTESTER_ROOT` before and after. 211 entries were created. The test's glob sees
**3** of them:

```
caught: ['profiles', 'projects/demo/crawl', 'projects/demo/crawl/crawl_01M2…']
missed: 208 — the entire  root/profiles/demo/  Chromium tree (Default/Network/Cookies,
        Default/Login Data, Default/History, Local Storage, Sessions, Cache, …)
        plus projects/demo/crawl/<id>/shots
        and projects/demo/{bench,rubrics,runs,scripts,sources}
```

`profiles/` sits at the **root**, a sibling of `projects/` — outside `project_dir` entirely, so
the test cannot reach it whatever it globs for. The `'profiles'` hit above is from my root-wide
diff, not from the test's scope.

This matters because it is precisely the artefact the test's own docstring names: *"a refused run
still left `crawl/<id>/shots/` **and a populated Chromium profile**"*. The profile half is
unchecked. CN1's tightened clause says the refused entry point "must leave the project directory
exactly as they found it"; a name-filtered glob over one subtree is a weaker statement than that,
and it would pass a future regression that leaves a populated browser profile without a
`crawl/` directory — a cookie jar and a `Login Data` file from a production ERP, left behind by a
run consent refused.

The fix is small and the test already has the fixture for it: snapshot `set(root.rglob("*"))`
before the invoke and assert the set is unchanged after. That is CN1 stated literally, it needs
no new machinery, and it is strictly stronger than the current two substrings.

## Ledger

- **AT-143** (high) — the no-trace test cannot see the browser profile [FAIL-4]
- **AT-144** (medium) — `--max-screens` / `--max-depth` reach no assertion [FAIL-2]
- **AT-145** (medium) — `approve` grants expired / unparseable / off-target approvals with exit 0
- **AT-146** (low) — the manifest's "the one row I would keep" names a test that does not do it [FAIL-1]

**AT-140 stays `open`.** It is substantially addressed and it is not finished: the criterion it
was filed to close (CN1 at the shipped entry point) is the one still under-evidenced.

## Scoreboard

```
VERDICT: FAIL
SCOREBOARD: 6/8 unit claims evidenced, 3/4 contract criteria hold (CN1 partial; CN2, CN6, CN9 hold)
FAILURES:
- [CN1] sev: high · the no-trace test globs projects/<slug> for "crawl"/"profile", but the Chromium
  profile it names in its own docstring lives at root/profiles/ — 208 of 211 artefacts a refused run
  creates are invisible to it · snapshot set(root.rglob("*")) before/after the invoke instead ·
  issue: AT-143
- [X-bounds] sev: medium · explore_cmd's --max-screens/--max-depth can be hardcoded to 999 with the
  whole 633-test suite still green · assert all four bounds reach CrawlBounds · issue: AT-144
- [C-manifest] sev: low · "the one row I would keep" names
  test_approve_writes_a_row_that_covers_the_cli_defaults, which passes when explore_cmd's
  --max-actions default drifts 200→137; the two refusal tests are what catch it · correct the
  manifest row to name them · issue: AT-146
ISSUES-WRITTEN: AT-143, AT-144, AT-145, AT-146
EXPLANATION: Verification and all four sabotage counts (K→1, L→1, M→1, N→2) reproduce exactly in an
isolated archive, the tests are non-vacuous in both directions, and both self-corrections check out —
including K's subtle claim that exit 2 survives the missing pre-flight, which I confirmed by running
it. It fails on the claim it leads with: the CN1 no-trace test sees 3 of the 211 files a refused run
leaves, and the populated Chromium profile that AT-111 was actually filed about is outside the
directory it globs. The fix is one before/after set comparison. Landing it before T-145 points this
path at a live production ERP is the whole reason this unit was taken first.
```
