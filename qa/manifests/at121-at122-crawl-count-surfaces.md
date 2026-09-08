# at121-at122-crawl-count-surfaces

**Unit:** AT-122 (medium) + AT-121 (low) — the two crawl-count surfaces the AT-120 sweep missed
**Commit:** 6c653fd
**Fix cycle:** 1
**Contract:** `qa/contracts/explore.md` X16 (the checker declared it clean for tool failures on the
AT-120 verdict; these are the same criterion at two surfaces that verdict's fix did not reach) +
`qa/contracts/ui.md`.

## Why these are one unit

Both were found by the checker in the same pass, and both are the same shape as AT-120 itself: **a
surface that reports a crawl's counts.** Splitting them would repeat the mistake that made AT-108
and AT-114 two issues instead of one sweep.

## AT-122 — the CLI

`cli_crawl` was the one `crawl.issues` reader the AT-120 commit did not touch. After that fix it no
longer *inflated* the count — it silently **dropped** tool failures instead. For a CI or headless
run, that single line is the entire report, so it was told nothing about holes in its own evidence.
Under-reporting replaced over-reporting; both are dishonest, and the second is arguably worse
because nothing looks wrong.

The line is extracted as `echo_crawl_summary` so it is testable at all — a helper the fix needed,
not a refactor bundled in.

## AT-121 — the zero case

The crawls table rendered a tool-failure count of `0` with `or '—'`, the same glyph the table uses
for an **unknown** `stop_reason`, while the Issues cell beside it printed `0`. Two meanings, one
glyph, adjacent columns.

## Evidence

```
$ SABOTAGE 7: AT-122 -- the CLI line drops tool failures again
>       assert "4 tool failures" in line, "a headless run gets this line and nothing else"
E       assert '4 tool failures' in 'crawl_x: completed (frontier empty) — 3 screens, 4 edges, 9 actions, 1 denied, 1 issues\n'
FAILED tests/test_explore_error_causes.py::test_the_cli_line_reports_tool_failures_too

$ SABOTAGE 8: AT-121 -- a measured zero renders as the unknown sentinel
>       assert row.count("<td>0</td>") == 2, (
E       assert 1 == 2
FAILED tests/test_explore_error_causes.py::test_a_known_zero_is_printed_as_zero_not_as_unknown

$ RESTORE
8 passed
```

Sabotage 7's failure shows the **actual emitted line**, not a description of it.

## Two self-corrections, kept because they are the interesting part

1. **My first pass tested both fixes by grepping the SOURCE** for the string `tool_failures`. That
   test passes on a comment. It is precisely the fiction-testing failure AT-107 was filed for, one
   axis over, and I wrote it immediately after having been caught doing it. Replaced with the real
   `echo_crawl_summary` output and a real rendered page through `TestClient`.
2. **My second pass then asserted no em dash anywhere in the row** — and it failed on *correct*
   behaviour. `started_at` on a crawl that never started is a genuine unknown, and telling that
   apart from a measured zero is the entire point of AT-121. A test that cannot make that
   distinction cannot defend it. The assertion now matches the two count cells only, with the
   reasoning recorded beside it so the next person does not "tighten" it back.

## Verification (host; Docker daemon down, `uv` runs natively)

```
uv run pytest -q                       594 passed, 2 skipped   (592 before + 2 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- Still zero live crawls on disk; every number is from the fixture site or a constructed `Crawl`.
- `echo_crawl_summary` takes `crawl: Any` to match the file's existing convention for its other
  helpers, not because the type is unknown. Flagged rather than quietly changed.

## Status: checked-PASS
