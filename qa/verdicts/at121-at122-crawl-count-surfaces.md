# Verdict — at121-at122-crawl-count-surfaces

**Date:** 2026-09-08
**Unit:** AT-122 (medium) + AT-121 (low) — the two crawl-count surfaces the AT-120 sweep missed
**Commit checked:** `6c653fd` (manifest `2433ab9`)
**Cycle checked: 1**
**Contract:** `qa/contracts/explore.md` X16 (+ its AT-121/AT-122 residual paragraph), `qa/contracts/ui.md`
**Bound root:** `D:/autoTesting`. Adapter: `qa/adapter.json` (coding).

## VERDICT: PASS

Both issues are closed on evidence I produced myself. Both fixes are defended by tests that
exercise the real code path, and both sabotages reproduce exactly as the manifest claims.

## What I re-ran

Host (Docker daemon down; `uv` runs natively — not a blocker):

```
uv run pytest -q                      596 selected: 594 passed, 2 skipped
uv run ruff check src tests scripts   All checks passed!
uv run autotester doctor              doctor: clean
```

The host's 2 skips (vs the container's 1) are the documented environment difference, not a
regression of this unit.

## AT-122 — the CLI line (behavioural, not source-inspection)

I called the real helper and read captured stdout — no grep of the source anywhere:

```
normal          -> 'crawl_x: completed (frontier empty) — 3 screens, 4 edges, 9 actions, 1 denied, 1 issues, 4 tool failures\n'
zeros           -> '... 1 denied, 0 issues, 0 tool failures\n'
never-finished  -> 'crawl_x: running (None) — ... 1 denied, 1 issues, 123456 tool failures\n'
```

The count is emitted verbatim at every magnitude, including a six-digit value and a zero. **AT-122
closed.**

## AT-121 — the crawls table (real page through TestClient)

I rendered `/projects/demo/crawls` against a temp `AUTOTESTER_ROOT` and read the actual row bytes:

```
crawl_zero (issues=0, tool_failures=0, started_at=None)
  ...<td>frontier empty</td><td>3</td><td>1</td><td>0</td><td>0</td><td>—</td>
  em dashes in row: 1 (started_at, a genuine unknown)   <td>0</td>: 2
crawl_big  (tool_failures=1234567, stop_reason=None)
  ...<td>—</td><td>0</td><td>0</td><td>0</td><td>1234567</td><td>—</td>
```

A measured zero now reads `0`, the same as the Issues cell beside it, while the two genuine
unknowns (`stop_reason`, `started_at`) keep the `—`. That is exactly the distinction the issue was
filed for. **AT-121 closed.**

I also swept every remaining `or '—'` in `src/autotester/` — `crawl_report.py:36,44,45,55,69,111`
and `routes_crawls.py:66,69`. All are on genuinely optional *string* fields. **No numeric field
anywhere still renders through the unknown sentinel.**

## Sabotage reproduction (git archive HEAD → scratchpad, `PYTHONPATH` pinned; live tree never touched)

**Sabotage 7** — drop the tool-failures clause from `echo_crawl_summary`:

```
>       assert "4 tool failures" in line, "a headless run gets this line and nothing else"
E       assert '4 tool failures' in 'crawl_x: completed (frontier empty) — 3 screens, 4 edges, 9 actions, 1 denied, 1 issues\n'
```

This matches the manifest's transcript **character for character** (the only difference is my
console codepage rendering the em dash as `?`). The AT-117 concern — a paraphrased transcript
presented as an emitted line — does not apply here; the maker pasted the real assertion output.

**Sabotage 8** — restore `crawl.tool_failures or '—'` in `routes_crawls.py`:

```
E       assert 1 == 2
E        +  where 1 = ...'<td>frontier empty</td><td>3</td><td>1</td><td>0</td><td>—</td><td>—</td>'.count('<td>0</td>')
```

**RESTORE → `8 passed`.** Both fixes are load-bearing.

## The two self-corrections — judged

1. **Source-grep → behavioural.** Verified, not taken on trust. `test_the_cli_line_reports_tool_failures_too`
   imports and *calls* `echo_crawl_summary` and asserts on `capsys` output;
   `test_a_known_zero_is_printed_as_zero_not_as_unknown` boots the FastAPI app through `TestClient`
   and asserts on rendered HTML. Neither test opens a source file, and neither would survive the
   behaviour being removed (proven above). The correction is real, not cosmetic.
2. **The surviving assertion `row.count("<td>0</td>") == 2`.** It is load-bearing today — sabotage 8
   drops it to 1. It is *positionally blind*, though: I rendered a row where `screens=0, denied=0,
   issues=0` and counted **three** `<td>0</td>` cells from unrelated columns. In the test's own
   fixture (`screens=3, edges=4, actions=9, denied=1`) no unrelated column is zero, so today the
   count pins exactly the two cells it names. The brittleness is that a future fixture edit could
   make it pass by coincidence. This is a note, not a failure — the maker's own comment beside the
   assertion already explains why matching the glyph anywhere in the row is wrong, which is the
   harder half to get right.

## Surface hunt, re-run including this commit

Every reader of a crawl's counts in `src/`: `cli_crawl.echo_crawl_summary` (fixed here),
`ui/routes_crawls.py:67-68` (fixed here), `ui/crawl_view.py:47-49` (separate stat tile, AT-120),
`stages/crawl_report.py:41-43` + its `Tool failures` sheet (AT-120), and `stages/explore.py:141-152`
`_finish`, the serialiser, which writes `tool_failures` into `crawl.json`. **No surface is left
where a crawl's counts are reported without tool failures, and nothing new was introduced.**
`cli.py` only mounts the commands; `routes_report.py` is about run verdicts and reads no crawl
counts; `coverage.py`, `explore_merge.py` and `project_store` were re-checked and contain no
crawl-count reporting (cleared again at this commit).

## Extraction safety

`echo_crawl_summary` is a pure move. The emitted string's prefix is byte-identical to the pre-fix
inline `typer.secho` (same f-string, same `fg=GREEN`); the only change is the appended
`, {crawl.tool_failures} tool failures`. Call ordering is preserved exactly: summary → `if merge:
_merge_into_flowspec` → `typer.echo(crawl_dir)`, the same three statements in the same order as
before. Both refusal paths still return before the summary is ever reached — `_preflight_consent`
raises `typer.Exit(2)`, and the `ApprovalRequired` handler around `run_crawl` raises `Exit(2)` from
the `except` block that sits *above* the call. So when and whether the line prints is unchanged.

## Adversarial probes

- Large count (1234567), zero, `stop_reason=None`, a never-started crawl (`started_at=None`) — all
  render honestly on both surfaces; no truncation, no falsy collapse.
- **Backward compatibility, executed.** I hand-wrote a pre-`tool_failures` `crawl.json` (the exact
  key set from before `bc29b34`) and loaded it: `store.load_crawl("crawl_old")` succeeds and the
  Pydantic default holds (`tool_failures = 0`). The old artifact renders in the table without
  error. Filed as AT-124 (low): that unmeasured legacy crawl now displays a confident `0`. This is
  what AT-121's own fix direction asked for, and `issues`/`denied` have always had the identical
  property, so it is a residual to record, not a regression of this unit.
- One inconsistency found and filed as AT-123 (low): the CLI line is the only crawl-count surface
  that does not guard `stop_reason`, printing the literal `None`. Unreachable through `explore_cmd`
  today (`_finish` always sets `stop_reason or "frontier empty"`), which is why it is low and not a
  failure of this unit.

## SCOREBOARD

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 6/6 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-123 (low), AT-124 (low) — both residuals, neither a failure of this unit.
                AT-121 open → fixed. AT-122 open → fixed.
EXPLANATION: Both surfaces were re-verified by execution, not by diff — the real CLI helper's
captured stdout and a real rendered page through TestClient. Both sabotages reproduce, sabotage 7
character-for-character as the manifest claims, and RESTORE gives 8 passed. The two
self-corrections are genuine: the final tests are behavioural, and the surviving
`row.count("<td>0</td>") == 2` is load-bearing today though positionally blind — I rendered a row
with three zero cells to establish that, and record it as brittleness rather than a defect. The
AT-120 surface hunt re-run at this commit finds no remaining crawl-count surface without tool
failures and nothing newly introduced; the `echo_crawl_summary` extraction is byte-identical apart
from the added clause and preserves both refusal paths and the `--merge` ordering.
```

Criteria judged: (1) the CLI reports tool failures apart from product issues at every magnitude;
(2) the crawls table renders a measured zero as `0` while genuine unknowns keep `—`; (3) no other
crawl-count surface regressed or was newly introduced; (4) the extraction is behaviour-preserving
on every path; (5) both fixes are defended by behavioural tests proven load-bearing by sabotage.
Invariants: X1/X2/X10 untouched (no explore-stage behaviour changed) · X16's counted-apart rule
now holds on every surface · `ui.md` U5 (the two changed cells are ints, no unescaped user text
added) · doctor clean (file/function caps) · ruff clean · no `*_v2`/duplicate module.
