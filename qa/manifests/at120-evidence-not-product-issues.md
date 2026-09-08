# at120-evidence-not-product-issues

**Unit:** AT-120 (high) — `IssueKind.EVIDENCE` was distinct in the artifact but not in any count
or report a human reads
**Commit:** bc29b34
**Fix cycle:** 1
**Contract:** `qa/contracts/explore.md` X16 — the checker amended it on the previous unit to record
this as an OPEN gap: *X16 is not clean until EVIDENCE is counted and displayed apart, the way
`Noise` already is.* This unit closes it.

## Why this unit exists, stated plainly

The previous unit's manifest claimed `IssueKind.EVIDENCE` "keeps a failure of the TOOL out of the
product's issue list". The checker **executed** the claim instead of reading it and found it false
at the only level that matters:

```
crawl.issues (headline) = 5
issue kinds: {'evidence': 4, 'navigation': 1}
```

One real product issue reported as five. `add_issue` incremented `rt.issues` kind-blind, and that
total is what the workbook prints as "Issues found", what the crawls table shows, and what the
crawl page's stat tile reads. The separation was real at the enum and fictional at the number.

**And the inflation was newly introduced by that commit** — before it, a failed screenshot filed no
issue at all. A fix justified by "this will not inflate the product's issue count" shipped having
inflated it. This is the second time in three units that a claim of mine survived my own review and
died on the checker's execution (AT-116 was the first); the pattern is that I check the mechanism I
changed and not the number a reader ends up seeing.

## What changed

| Surface | Before | After |
|---|---|---|
| `schema/crawl.py` | `issues` only | `+ tool_failures`, documented as counted-apart |
| `explore_node.add_issue` | `rt.issues += 1`, kind-blind | routes by kind |
| `crawl_report.crawl_summary` | `("Issues found", …)` | `"Issues found (in the product)"` + `"Tool failures (the crawler's own)"` |
| `crawl_report` sheets | Issues held every kind | Issues = product kinds; new `Tool failures` sheet |
| `routes_crawls` table | one Issues column | `+ Tool failures` column |
| `crawl_view` crawl page | one stat, one Issues card | `+ tool-failures stat`, `+ a second card` |

**The design follows a precedent already in this file rather than inventing one.** `_noise_sheet`
exists because X9 refuses to call third-party failures product issues — and it *reports* them
anyway, "so 'we ignored it' is auditable". Tool failures are the same shape and get the same
treatment. Hiding them would be the other wrong fix: each one is a hole in the evidence the rest of
the report is built on, so the empty state says *"The crawler recorded everything it tried to"*
rather than nothing at all.

## Evidence

```
$ SABOTAGE 5: AT-120 -- add_issue increments kind-blind again (the reported bug)
>       assert crawl.issues == len(product), (
E       assert 5 == 1
FAILED tests/test_explore_error_causes.py::test_tool_failures_are_not_counted_into_the_products_issue_total

$ SABOTAGE 6: the workbook Issues sheet lists every kind again
>       assert not any("screenshot" in str(c) for row in issue_rows for c in row), (
E       assert not True
FAILED tests/test_explore_error_causes.py::test_the_workbook_and_the_crawl_page_keep_them_apart

$ RESTORE
6 passed
```

Sabotage 5 reproduces the checker's reported numbers exactly — `5 == 1` is the same 5-for-1 it
measured at HEAD. That is the point of the test: the regression is now pinned by the number a human
reads, not by the enum.

## A pre-existing test I changed, flagged rather than buried

`tests/test_crawl_report.py::SHEETS` pins the workbook's exact sheet list and failed on this commit.
I updated it because that list is contract and this unit legitimately adds a sheet — but it is a
**maker editing a test that was defending a shape**, so it is named here for the checker to rule on
rather than left in the diff. The assertion still pins an exact ordered list; it was not weakened
to a subset.

## Verification (host; Docker daemon down, `uv` runs natively)

```
uv run pytest -q                       592 passed, 2 skipped   (590 before + 2 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- Still zero live crawls on disk. Every number above is from the fixture site.
- `first_party` on a `CrawlIssue` is a separate axis and is untouched; an EVIDENCE issue is
  currently filed `first_party=True` by default, which is meaningless for a tool failure. Not
  fixed here — flagging it so the checker can decide whether it is a finding or noise.

## Status: ready-for-check
