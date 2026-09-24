# Verdict — t123-medium-batch

**Date:** 2026-09-24
**Cycle checked:** 1
**Checker:** claude-sonnet-subagent (fresh context, Mode A unit check)
**Bound root:** D:/autoTesting/.worktrees/t123-medium-batch (branch `wave/t123-medium-batch`, head `d5db88b`)
**Contracts read in full:** `qa/contracts/docker.md` (D2, D4), `qa/contracts/ui.md` (U9 + amendment log),
`qa/contracts/core-invariants.md` (C1-C10), `qa/contracts/browser-and-secrets.md` (B1-B10).
**Manifest:** `qa/manifests/t123-medium-batch.md`, Status `ready-for-check`, Fix cycle 1 of 3.

## What I re-ran myself (never trusted the pasted output)

- `uv run pytest tests/test_ui_healthz.py tests/test_migrate_stamp_legacy_rubrics.py -v` →
  **16 passed** (matches manifest).
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**.
- `uv run pytest` (full suite, no CLI `-q`, PYTHONUTF8=1) → **1601 passed, 0 failed, 5 skipped,
  32 xfailed, 1 warning in 871.72s.** The manifest's own paste showed 1 failure
  (`tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`);
  my independent run did not reproduce it. Cross-checked against the ledger: `ISS-t164-1` already
  documents this exact test as a pre-existing, non-deterministic flake unrelated to any unit's
  diff (confirmed by `git log` on that test file), consistent with either outcome. Either way it
  is outside this unit's diff (`git diff` below touches neither `stages/flake_probe.py` nor its
  test) and is not charged against this unit.

## (a) Do AT-085 and AT-065 meet their issues' expected behaviour + governing criteria

**AT-085** (`docker.md` D4 — presentation-only; `core-invariants.md` C5 — no secret surface).
`src/autotester/ui/routes_live.py` adds `GET /healthz`, freezing `_PROCESS_STARTED_AT` at import
time and scanning `src/autotester/**/*.py` fresh per request for `_newest_source_mtime()`. I drove
this live myself, independently of the maker's evidence:
- Started my own `uv run uvicorn` against the **bound root** on port 8790: `/healthz`, `/live`
  (200) and `/` (200) all answered correctly, no project/secret state touched.
- Started a **second, independent** `uvicorn` against a throwaway copy (never the bound root) on
  port 8791, confirmed `serving_stale_code: false`, then touched a `.py` file **in that copy only**
  and re-hit `/healthz` on the same running process with no restart: `serving_stale_code` flipped
  `false → true` — the exact AT-085 scenario, reproduced against my own server and my own copy, not
  read from the maker's report. Both servers stopped and confirmed down afterward.
- `docker/entrypoint.sh` confirmed to launch uvicorn with no `--reload`, matching AT-085's stated
  root cause.
- **D4 held**: `inspect.getsource(routes_live.healthz)` (test + my own read) shows no `ProjectStore`/
  `SecretStore` call and no project parameter.
**Meets AT-085 and D4.**

**AT-065** (`grade` feature — no contract file per se; governed by `core-invariants.md` C1/C5/C6/C7).
`scripts/migrate_stamp_legacy_rubrics.py` matches AT-065's own recorded fix direction exactly: dry
run by default, `--write`/`--only` for a human-reviewed one-file-at-a-time apply, and `candidate()`
stamps only when a rubric's `criteria`/`no_fire` are byte-identical to what
`run_case_pipeline._rubric_for_claim` would rebuild for the claim embedded in its own text — never a
heuristic guess. Read the full script and full test file: every test exercises `tmp_path`, never
`projects/`, so running the test suite cannot touch real project data (C6 — artifacts stay
human-editable files, no side effect on the real store). **Meets AT-065.**

## (b) Is deferring AT-086/AT-087 legitimate

Yes. `qa/contracts/ui.md` U9 states, in the criterion text itself (not just the amendment log):
*"Two residuals are deliberately **outside** this criterion and tracked instead, because closing
either is a scope decision rather than a bug fix: **AT-087** ... and **AT-086** .... Both fail
closed."* This is the contract's own text, not the manifest's characterization of it — I read U9 in
full before judging. The manifest's two "Question for Umesh" paragraphs accurately restate the two
genuine trade-offs U9 already flags (widening the concatenation-check's join context vs. a new
false-positive surface; and a `.env`-exempt-value declaration or cross-project trust vs. narrowing
AT-083's boundary). Both fail closed today (no existing project is broken), and neither is a
silently-softened criterion — U9's text is unchanged by this unit. **Legitimate deferral, not a
FAIL.**

**T-123 goal-task scope, checked independently, not taken on the dispatch's word:** `.goal/goal.json`
T-123's title reads *"Medium-issue batch: AT-087 per-field exemption, AT-076/086 config-field rule,
AT-079/080, AT-065, AT-085"* — six issue numbers, not four. I checked `qa/issues.jsonl` for the ones
the manifest doesn't mention: **AT-076, AT-079, AT-080 are already `status: fixed`** from earlier,
unrelated units (at076-navigation-secret-escape-hatch, at079-080-credential-guard-gaps) — so they
are not open work this manifest skipped. **AT-086 and AT-087 remain `status: open`** and are exactly
the two this manifest defers. Net: T-123's title bundles issues resolved across several units: only
AT-086/AT-087 are still open under it. Per dispatch instruction and independently confirmed by the
above: **T-123 stays `pending` in goal.json — not closed by this PASS.** I did not run
`goal_cli.py done` for T-123.

## (c) Security review of `GET /healthz`

- **No auth boundary exists anywhere in this app** — `grep`'d `src/autotester/ui/app.py` for
  middleware/auth: none. `/healthz` sits behind exactly the same (non-)boundary as `/`, `/live`, and
  every other route. `ui.md`'s own no-fire list states *"Authentication/authorization — this is a
  local, single-operator tool for now."* `/healthz` does not narrow or widen that boundary, so this
  is consistent with the contract's declared scope, not a new gap this unit introduces.
- **What it exposes**: an ISO timestamp of process start and of the newest `.py` mtime under
  `src/autotester`, plus a derived boolean. No secret value, no project data, no path contents,
  nothing masked-by-`Redactor` elsewhere in the app is exposed here. Judged against C5 (secrets
  never reach a log/artifact/model) and B1-B10 (credential handling): **not applicable** — this
  route never touches `SecretStore`/`.env`/`ProjectStore`, confirmed by the test asserting no
  `ProjectStore`/`SecretStore` reference in its source and by my own read of the 28-line diff.
  Two source-code mtimes are not a credential or PII leak.
- **DoS-by-scan, at this project's scale**: `_SRC_ROOT.rglob("*.py")` over
  `src/autotester` walks **135 files** (measured: `find src/autotester -name "*.py" | wc -l`). This
  is a local, single-operator dev tool (no auth, no concurrency story, headed browser by design) —
  135 `stat()` calls per request is sub-millisecond and not a meaningful resource-exhaustion vector
  at this project's actual scale and threat model (no-fire list: "Performance of browser startup"
  and "a local, single-operator tool" both already set that bar). Not a finding.

**No security finding on `/healthz`.**

## (d) `scripts/migrate_stamp_legacy_rubrics.py`

Confirmed by full read: `--write` is required to persist anything (default is report-only,
`main()`'s `args.write` gate wraps the only call to `apply()`), and `candidate()` returns a claim
only when `rubric.provenance is None` **and** the embedded claim, rebuilt via `_rubric_for_claim`,
produces byte-identical `criteria`/`no_fire`. Every test path uses `tmp_path`, confirming this
cannot touch real `projects/` rubric files during the test suite. **Confirmed as described.**

## Diff scope (step 4c) — `git diff 087ab84 d5db88b`

```
 docs/MAP.md                                |   3 +-
 qa/manifests/t123-medium-batch.md          | 165 +++++++++++++++
 scripts/migrate_stamp_legacy_rubrics.py    | 147 +++++++++++++++
 src/autotester/ui/routes_live.py           |  43 +++++++-
 tests/test_migrate_stamp_legacy_rubrics.py | 157 +++++++++++++++
 tests/test_ui_healthz.py                   |  79 +++++++++
 6 files changed, 592 insertions(+), 2 deletions(-)
```

`routes_live.py`'s only deletions are the 2-line docstring it replaced (with a longer one) — no
function, route, test, export or config key was removed or renamed. No file outside the manifest's
"What changed" (+ `docs/MAP.md`, regenerated via `uv run autotester map` and named in the manifest)
was touched. **Clean — nothing removed or out-of-scope.**

## Capability coverage — re-derived myself, in throwaway copies, never the bound tree

Per protocol: copied the bound tree (excluding `.git`, `.venv`) to two **separate** throwaway
copies outside the bound root (`C:/Users/Lenovo/AppData/Local/Temp/claude/checker-t123/row1`,
`.../row2`). Verified each copy's `autotester` package resolves to the **copy's own** `src/`
(the repo's `.venv` carries an absolute-path `.pth` to the bound root, so I forced
`PYTHONPATH=<copy>/src` and confirmed via `python -c "import autotester...; print(__file__)"`
that it printed the copy's path, not the bound root's, before trusting any result).

| capability | check | GREEN (before, in copy) | edit applied (single-hunk, single-file, as named) | RED (after, in copy) |
|---|---|---|---|---|
| AT-085: `serving_stale_code=true` when a source file is newer than process start | `tests/test_ui_healthz.py::test_healthz_detects_a_source_edit_after_process_start` | `1 passed` | `routes_live.py`: `newest > _PROCESS_STARTED_AT` → `newest < _PROCESS_STARTED_AT` | `FAILED ... assert False is True` — the exact `serving_stale_code` assertion |
| AT-065: `candidate()` refuses a rubric edited since generation, even with `provenance` stripped | `tests/test_migrate_stamp_legacy_rubrics.py::test_a_rubric_edited_since_generation_is_never_a_candidate` | `1 passed` | `migrate_stamp_legacy_rubrics.py`: deleted the `if rubric.criteria != rebuilt.criteria or rubric.no_fire != rebuilt.no_fire: return None` guard | `FAILED ... AssertionError: assert 'the login page is shown' is None` — the exact `candidate(edited) is None` assertion |

**CAPABILITY-COVERAGE: 2/2 rows reproduced.** Both edits matched the manifest's cells exactly
(single-hunk, single-file, named in "What changed") — no cell required `CONTRACT_MISMATCH` handling.

## Live-browser (Mode D)

`/healthz` is a JSON API route with no template/DOM/interaction target (confirmed by reading the
full diff — `theme.page()` is never called by `healthz()`), so a Playwright click-through has no
surface to exercise; this matches the manifest's own stated reasoning, independently verified true
by reading the code, not accepted on assertion. I drove it with my own real HTTP client against my
own two independently-started `uvicorn` processes (bound root + a throwaway copy, ports 8790/8791,
never reusing the maker's port 8765 or its evidence) — see (a) above for the exact steps and the
observed `false → true` flip. `migrate_stamp_legacy_rubrics.py` is a CLI script with no UI surface.
Evidence: `qa/evidence/browser-t123-medium-batch-2026-09-24-checker/report.json` (written below).

## Issues ledger

- **AT-085**: `open → fixed` (`qa/issues.jsonl`, `fixed_date: 2026-09-24`, checker_note added).
- **AT-065**: `open → fixed` (same).
- **AT-086, AT-087**: left `open` — legitimately deferred, not fixed by this unit (see (b)).
- No new issues filed; nothing found at >80% confidence that isn't already covered above.

## VERDICT block

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (AT-085 vs D4/core-invariants C5, AT-065 vs core-invariants C1/C5/C6/C7), 0/0 invariants violated
CAPABILITY-COVERAGE: 2/2 rows reproduced
LIVE-BROWSER: qa/evidence/browser-t123-medium-batch-2026-09-24-checker/report.json (JSON-API route, no DOM surface -- driven via independent HTTP clients against two checker-started uvicorn processes, not the maker's evidence)
ISSUES-WRITTEN: none (AT-085, AT-065 flipped open->fixed in qa/issues.jsonl; AT-086, AT-087 correctly left open)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: AT-085's /healthz correctly detects post-start source staleness, verified live against two independently-started servers (bound root + a throwaway copy), touches no project/secret state, and sits behind the same (declared, no-fire-listed) no-auth boundary as every other route -- no security or DoS finding at this project's scale. AT-065's migration script matches its own recorded fix direction: dry-run default, byte-identical-shape-only candidacy, tested exclusively against tmp_path. Both capability-coverage rows independently reproduced in isolated throwaway copies. AT-086/AT-087 deferral is legitimate per ui.md U9's own criterion text, not just the manifest's assertion -- so per dispatch instruction, T-123 (whose title also names AT-076/079/080, all already fixed by earlier units) stays pending in goal.json; only AT-085/AT-065 are flipped to fixed in the ledger.
```
