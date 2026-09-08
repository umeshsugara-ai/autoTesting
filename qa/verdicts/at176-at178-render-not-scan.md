# VERDICT — at176-at178-render-not-scan

**Cycle checked: 1**
**Date:** 2026-09-09
**Commit under check:** `e2f119f` (manifest `6bc9e5c`)
**Contract:** `qa/contracts/video-learning.md` VL1d (generalised) · `core-invariants.md` C4, C7
**Adapter:** coding · slot-1 = `uv run pytest` / `ruff` / `doctor`
**Environment:** Docker down; `uv` native; bare `uv run pytest` (no `-q`, no `-x`); sabotages in a
detached `git worktree` at `e2f119f`, never in the live tree (AT-101).

---

## VERDICT: PASS

**SCOREBOARD: 8/8 criteria met, 3/3 invariants hold**

Every claim in the manifest that I could execute, I executed, and every one held. The findings
below are coverage boundaries of a *test helper*, not shipped defects — filed as issues, not
charged against the criteria, on the same reasoning that governed AT-174/AT-176/AT-178 themselves.

---

## 1. The central claim — sabotage AY, the mutation that returned zero

`PREP_COMMAND = "autotester ingest prep"` → `"autotester media prep"`.

```
anchor `^PREP_COMMAND = "autotester ingest prep"$`  matched exactly once
file on disk changed                                confirmed (grep read back)
uv run pytest -p no:randomly                        4 failed, 740 passed, 2 skipped
```

```
FAILED tests/test_cli_advice_resolves.py::test_the_collector_sees_the_site_the_class_exists_for
FAILED tests/test_cli_advice_resolves.py::test_every_command_the_code_names_is_one_the_cli_exposes[stages_media_prep.py-media prep]
FAILED tests/test_cli_advice_resolves.py::test_the_refusal_names_a_command_that_actually_stops_it
FAILED tests/test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists
```

**Confirmed, and stronger than the manifest states.** The manifest's `failures: 3` is the *delta* —
the three newly-catching tests, correctly named. The full-suite number is **4**: the fourth is the
pre-existing instance test that AT-176's ledger row records as the *only* thing that caught this
mutation at `3b765a4` (`0 failures in the class-level guard, exactly 1 in the full suite`). So the
before/after is exactly: **guard 0 → 3, suite 1 → 4.** The class-level guard now sees the canonical
AT-163 site, which is the whole point of the unit. Reporting the delta rather than the suite total
is a presentational choice, not an overstatement; noted, not charged.

## 2. Sabotage AZ — the registered, same-arity sibling

`PREP_COMMAND` → `"autotester ingest frames"` (registered under `ingest`, same two arguments).

```
anchor matched once · file changed
uv run pytest -p no:randomly     2 failed, 742 passed, 2 skipped
FAILED ...::test_the_collector_sees_the_site_the_class_exists_for
FAILED ...::test_the_refusal_names_a_command_that_actually_stops_it
```

**Exactly 2, as claimed, and the discrimination is real.** Note what did *not* fail:
`test_every_command_the_code_names_is_one_the_cli_exposes` **passed** (the sibling is registered),
and `test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists` **passed**.
Every static oracle in this repo accepts AZ. Only the causal test rejects it. That is precisely the
claim AT-174 was filed to force, and it is now evidenced rather than argued.

## 3. The causal oracle (AT-174) — judged as its designer

**Does it run the command as rendered, or reconstruct it?** It runs it as rendered. It triggers the
real refusal, takes `str(exc)`, lifts the first backticked span out of the *runtime* message, drops
argv[0], and invokes the real `app` through `CliRunner`. Nothing about the correct command is
written into the test — it is a fixture, an invocation, and the same predicate twice, as designed.

**Is the drop-argv[0] safe?** It drops whatever is first without asserting it is `autotester`. I
probed the failure direction: a message reading `ingest prep demo <id>` or
`docker compose exec app autotester ingest prep …` loses its first token and then fails to resolve →
`exit_code != 0` → **test fails**. Fail-safe in the direction that matters. No issue.

**Does it discriminate, or did AZ pass for the wrong reason?** This was the one place I did not take
the result at face value. Under AZ the test failed on the *exit-code* assertion, not on the causal
backstop:

```
E  AssertionError: the command the refusal named failed: src_… has no analysis.json …
E  assert 2 == 0  +  where 2 = <Result SystemExit(2)>.exit_code
```

So AZ is caught by "the named command errored", which a *different* sibling — one that exits 0 and
still does not prepare — would slip past. I built that case and ran it (probe in the worktree, since
removed): a registered command that exits 0 and writes no `media.json`, invoked exactly as the causal
test invokes it, then the causal test's final line:

```
EXIT0-SIBLING exit_code: 0
BACKSTOP FIRES: require_prepared still raised after an exit-0 sibling
```

**The backstop is real and unconditional.** `media_prep.require_prepared(store, source.id)` after
`exit_code == 0` is the assertion carrying the oracle, and it fires. The oracle discriminates on the
property it claims to (the refusal stops), not merely on the sibling happening to error.

**Can the causal test pass while the message is still wrong?** Yes, in bounded ways worth stating:
it judges the *command*, never the prose around it — VL1d's "says the work must happen on the HOST"
half is not covered by this test (it remains covered by `test_media_prep.py`). And it takes the
**first** backticked span, so a message whose first backtick quotes a path (`` `media.json` ``) would
run that instead — again fail-safe (false positive, not false negative). Neither is a defect; both
are scope, and the manifest's "What this does NOT claim" already concedes the one-refusal limit.

## 4. Attacking the renderer — where it still cannot see

I ran the collector directly against ten constructed shapes. **Detected** (so *not* holes): a
constant defined inside a function or class, a `.format()` template, a dict/enum-lookup value, a
`+`-concatenated module constant, a name rebound later, and a command name **split across the
interpolation boundary** (`f"autotester {GROUP} prep"` → `media prep`, resolved correctly). Note the
first four are caught because the command text sits in a scanned literal, not because rendering
resolved anything — but caught is caught.

**Two real holes, both silent:**

```
K  from …media_prep import PREP_COMMAND
   f"run `{PREP_COMMAND} " f"{slug} {sid}` on the HOST first"      ->  []
L  def f(group): raise RuntimeError(f"run `autotester {group} prep x`")  ->  []
```

**K is AT-176's own shape, one `import` away, and it returns nothing at all.** `_module_constants`
reads only `NAME = "literal"` bindings *in the file being parsed*, so the moment a command constant
is imported rather than defined locally — an ordinary, likely refactor for a name whose whole
purpose is to live in one place — the guard goes blind again in exactly the way this unit exists to
fix. Filed **AT-192 (medium)**, not high: unlike AT-176 there is no live instance (all nine sites
today are same-module), and `test_media_prep.py`'s instance test still stands.

**The `UNRESOLVED` claim, verified rather than accepted.** The manifest says `UNRESOLVED` "**marks**"
what it cannot resolve. Inside `_render` that is true, and it correctly prevents a *wrong* command
being reported. But `advice_in` then filters `UNRESOLVED not in command` and **drops the site
silently** — no count, no warning, nothing a human or a test ever sees. Cases K and L return `[]`,
indistinguishable from "this file contains no advice". So the sentinel is a false-positive guard, not
a marker; "marks it rather than pretending" overstates by one word. The *boundary* is honestly stated
in both the module docstring and the manifest's "What this does NOT claim", so this is imprecision,
not a false claim — filed **AT-195 (low)** with the remedy (return the unresolved sites so the hole
has a number).

**Non-Python surfaces:** measured, and empty. `grep` for `autotester <cmd>` across `src/**/*.md`,
`*.html`, `*.js` returns nothing; the only `ui/` mention (`ui/routes_crawls.py:5`, "`autotester
explore` wrote a graph…") is a module docstring and correctly excluded. Acceptable scoping — and
AT-178's ledger row already recorded it — though the new module's docstring no longer says so.

## 5. Attacking it for false positives — the docstring exclusion does NOT hold

This is the question the new node types raise, and the answer is no.

```python
def _is_documentation(tree):
    return {id(node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) …}
```

It collects only `Expr` whose value is a **`Constant`**. A bare `JoinedStr` or `BinOp` statement is
an `Expr` too, and is *not* excluded:

```
N  f"""the old name was autotester media prep and it is dead"""   -> ['media prep and it is dead']
O  "the old name was " + "autotester media prep" + " and it is dead"  -> ['media prep', …]
```

N is the sharp one: it is this codebase's **variable-docstring convention**, the one `PREP_COMMAND`'s
own docstring uses to record that `autotester media prep` is dead — written as an f-string, that
documentation would be read as advice and fail the guard. The exclusion's own docstring claims it
"covers real docstrings and this codebase's variable-docstring convention"; it covers the plain form
only. **Latent, not live** — I walked every `.py` under `src/autotester` and found **zero** bare
`JoinedStr`/`BinOp` statements — so the suite is green for a real reason. Filed **AT-193 (medium)**.

**Prose quoting a command the user typed** (`f"you typed \`autotester bogus nine\`, which failed"`)
is flagged. No live instance, and a genuinely runtime echo renders `UNRESOLVED` anyway. Not filed
separately — it is the same surface as AT-193.

**One more false-positive shape**, filed **AT-194 (low)**: the regex takes lowercase words greedily,
so a literal argument is swallowed into the "command" — `"run \`autotester explore demo\`"` yields
`explore demo`, and the CLI oracle then checks a string that is not a command. Harmless across
today's seven, real if advice ever quotes a concrete slug.

## 6. AT-189 — `qa/` out of the fingerprint

```python
WATCHED_DIRS = ("docs", "src", "scripts", "projects")
```

Confirmed: `qa` removed; `docs`, `src`, `scripts`, `projects` all still watched; `.goal` still
excluded. **No real detection lost** — I re-ran the check that produced the finding:
`grep -rn "qa/" src/autotester/ --include=*.py` yields only docstring references, no CLI write path
targets `qa/`, and `repo_root()` is redirected to a temp root during the matrix anyway. The rule
applied to `.goal/` is now applied to `qa/`, which is the whole content of the finding. The narrower
residuals AT-190 and AT-191 are untouched by this unit and stay open.

## 7. Re-run verification (my own, not the manifest's)

```
uv run pytest                          744 passed, 2 skipped, 1 warning in 72.40s   exit 0
uv run ruff check src tests scripts    All checks passed!                            exit 0
uv run autotester doctor               doctor: clean                                 exit 0
```

All three claims reproduced exactly. Collector surface independently counted: **9 sites, 7 distinct
commands** (`ingest register` ×2, `ingest list`, `approve`, `snapshot` ×2, `map`, `ingest prep`,
`flowspec approve`) — the manifest's "5 → 9" is accurate, and `ingest prep` is present.

Live tree after the check: `git status --short` shows only `.goal/` (timer-written). The worktree was
removed and pruned; no sabotage ever touched the live tree.

## 8. The flake — ruling on it, because slot-1 determinism is load-bearing

`test_explore_live.py::test_the_dialog_page_does_not_trap_the_crawl`.

**Genuinely intermittent, not a regression.** Decisive evidence first: `git show --stat e2f119f`
touches `tests/` and `.goal/` only — **no file under `src/autotester/stages/explore*` changed**, so
there is no code for a regression to live in. Then, empirically, seven clean runs since:

```
full suite, baseline            744 passed, 2 skipped
full suite, under sabotage AY   live explore tests passed (only the 4 advice/prep tests failed)
full suite, under sabotage AZ   live explore tests passed
tests/test_explore_live.py ×3   8 passed each time
tests/test_explore_live.py once more, run CONCURRENTLY with a second full suite   8 passed
```

I could not reproduce it, including under deliberate concurrent load. One failure in eight
observations, with no causal change available, is a flake.

**Ruling on the maker's generalisation.** Substantially right, imprecisely stated, and the
imprecision matters:

- *Imprecise:* this test does not assert "one exact terminal `NodeStatus`". It asserts membership in
  a **two**-element set, `("aborted_dialog", "explored")`, guarded by `if dialog_node is not None`.
  The generalisation as written would sweep in tests that are not brittle.
- *Right, and this is the real shape:* the set is defined by **enumerating the outcomes the author
  expected** rather than by the property the test is named for. `NodeStatus` has exactly three
  terminal values, and the excluded third — `ABORTED_ERROR` — is the one a *loaded machine* produces.
  X8's dialog breaker is a race by construction, so the test's pass condition is "the race resolved
  one of the two ways I thought of", which is an environment assertion wearing a product assertion's
  name.
- *And the property it actually names is already fully asserted*: "does not trap the crawl" is
  `crawl.finished_at is not None`, on the line above. Whether the node aborted on the dialog or on a
  load-induced timeout, the crawl was not trapped.

**Accepted as a finding, filed AT-196 (medium)**, with the remedy stated as an invariant rather than
a longer allow-list: assert the node reached *some* terminal status (i.e. is not left `pending`/
`queued`) plus `finished_at`, so the test fails when the crawl hangs — the thing it exists to catch —
and not when a busy host times a navigation out. The correct generalisation for the project is
**"a live test must assert the invariant it is named for, not enumerate the outcomes the author
happened to observe"**; that is narrower than the maker's version and does not condemn every
status assertion.

**On the broader worry — that this undermines every manifest in the project.** It is the right worry
and it is why I am filing rather than shrugging, but it does not undermine the verdicts already
given: the failure mode is a *false FAIL* on a loaded host, not a false PASS, so no manifest was ever
passed by this flake. The exposure is that a maker or checker meets a red suite unrelated to its unit
and either burns a cycle or, worse, learns to re-run until green. Recorded in C7's amendment log
below so the next reader does not have to rediscover it.

**Filing the flake and not fixing it inside a unit about something else was the right call** and is
worth saying plainly — it is the discipline C7 is made of.

---

## Criteria

| | criterion | verdict | evidence |
|---|---|---|---|
| VL1d | refusal names a real, runnable CLI command | **met** | causal test runs the rendered command for real; suite green |
| VL1d-gen | the class-level guard sees the site the class exists for | **met** | AY: guard 0 → 3 failures; `ingest prep` in the collected set |
| AT-176 | the two-AST-node blind spot is closed for same-module constants | **met** | §1, §4 (E resolves) |
| AT-178 | un-backticked advice is collected | **met** | `core/consent.py :: approve` present in the 9 sites |
| AT-174 | a causal oracle exists and discriminates a same-arity sibling | **met** | AZ: only the causal test rejects it; backstop probed independently |
| AT-189 | `qa/` out, `docs`/`src`/`scripts`/`projects` in | **met** | §6 |
| C4 | repo root clean | **holds** | `doctor: clean`; `git status` shows only `.goal/` |
| C7 | independent, re-runnable verification; sabotage asserted | **holds** | anchor-matched-once + file-changed on both AY and AZ; both non-zero, neither INCONCLUSIVE |
| C7 | manifest pastes real output, checker re-runs it | **holds** | all three verify commands reproduced by me |

**FAILURES: none.**

**ISSUES-WRITTEN:** AT-192 (medium), AT-193 (medium), AT-194 (low), AT-195 (low), AT-196 (medium).
**ISSUES CLOSED (open → fixed):** AT-174, AT-176, AT-178, AT-189.

---

## EXPLANATION

This unit was submitted against four findings of mine, and all four are fixed by execution rather
than by argument. The mutation that previously returned **zero** now fails three tests in the guard
and four in the suite; the same-arity sibling that defeats every static oracle in this repo is
rejected by the causal one, and I verified that its discrimination rests on the causal backstop and
not on the sibling incidentally erroring. Verification reproduced exactly (744/2, ruff clean, doctor
clean). The maker also conceded the AT-174 premise it had argued was impossible, and filed a flake it
could have shrugged at — both are the behaviour the pair exists to produce.

The five new issues are boundaries of a test helper, not shipped defects, and the manifest's "What
this does NOT claim" already concedes the general class. Two deserve emphasis anyway: **AT-192**, the
guard is blind again the moment a command constant is *imported* rather than defined locally, which
is AT-176's exact shape one refactor away; and **AT-193**, the documentation exclusion silently does
not cover the new `JoinedStr`/`BinOp` node types, so this codebase's own variable-docstring
convention — the one `PREP_COMMAND` uses to record a dead command — would be read as advice if ever
written as an f-string. Both are latent today (measured: zero live instances of either), which is why
this is a PASS with issues and not a FAIL.
