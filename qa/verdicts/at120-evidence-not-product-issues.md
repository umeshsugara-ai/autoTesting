# Verdict — at120-evidence-not-product-issues

**Date:** 2026-09-08
**Unit:** AT-120 — `IssueKind.EVIDENCE` distinct in the artifact but not in any count a human reads
**Commit checked:** `bc29b34` (manifest at `44c6b6b`)
**Contract:** `qa/contracts/explore.md` X16 (with X9's precedent)
**Cycle checked: 1**
**Bound root:** `D:/autoTesting`. Adapter: `qa/adapter.json` (coding).

## VERDICT: PASS

AT-120 was this checker's own finding on the previous unit. It is closed on this checker's own
re-executed probe, not on the maker's transcript.

## 1. The AT-120 probe, re-run at the new HEAD

Same fixture, same sabotage of `page.screenshot`, same measurement as at `6e98487`:

| | `6e98487` (the finding) | `bc29b34` (now) |
|---|---|---|
| `crawl.issues` (headline) | **5** | **1** |
| `crawl.tool_failures` | (did not exist) | **4** |
| issue kinds filed | `{evidence: 4, navigation: 1}` | `{evidence: 4, navigation: 1}` |
| real product issues | 1 | 1 |

The 5-for-1 is gone: `crawl.issues == len(product) == 1` and `crawl.tool_failures == len(tool) == 4`.
The kinds filed are unchanged, so nothing was fixed by suppressing evidence — only by routing the
count. Every surface named in the original finding re-rendered by the checker:

- workbook summary: `Issues found (in the product) = 1`, `Tool failures (the crawler's own) = 4`
- sheetnames: `['Summary','Screens','Edges','Denied & Skipped','Issues','Tool failures','Noise']`
- `Issues` sheet holds exactly the one navigation row; the string `screenshot` appears nowhere in it
- `Tool failures` sheet holds the four, with the screen name and the cause
- crawl-page stat row: a separate `Tool failures` tile reading 4
- crawls table: its own column; `routes_crawls.crawl_page` partitions the two cards by kind

## 2. Verification commands, re-run and counted by the checker

| Command | Manifest claim | Checker's own result |
|---|---|---|
| `uv run pytest -q` | 592 passed, 2 skipped | **594 tests, 0 failures, 0 errors, 2 skipped** (junitxml, counted not read) = 592 passed |
| `uv run ruff check src tests scripts` | All checks passed! | **All checks passed!** |
| `uv run autotester doctor` | doctor: clean | **doctor: clean** |

(The terminal summary line is swallowed in this shell, so the totals were taken from a
`--junitxml` run rather than from a pasted line.)

## 3. Both sabotages reproduced — literally

`git archive HEAD` into a scratchpad, `PYTHONPATH` pinned to the copy (AT-101: the live tree was
never stashed, checked out or restored; `import autotester` confirmed to resolve to the scratch copy
before either run).

- **Sabotage 5** — `add_issue` increments kind-blind again:
  `AssertionError: headline issue count 5 != 1 real product issues` / `assert 5 == 1`, with the
  repr showing `issues=5, tool_failures=0`. The manifest's claim that this reproduces the checker's
  own reported numbers is **true literally**, not from memory — the specific thing AT-117 was filed
  for. Failing test: `test_tool_failures_are_not_counted_into_the_products_issue_total`.
- **Sabotage 6** — the workbook stops partitioning: `assert not True` /
  `"a crawler failure reached the product's Issues sheet"` at
  `tests/test_explore_error_causes.py:175`. Matches the manifest.
- **Restore** — both files re-written from `HEAD`: `6 passed`.

## 4. Hunt for a surface the maker missed

`grep` over `src/`, `scripts/`, `docs/` for `crawl.issues` / `Issues found` / `.issues` returns
exactly five sites. Three gained a `tool_failures` companion in this commit
(`crawl_report.py:42`, `crawl_view.py:48`, `routes_crawls.py:67`), one is the serialiser
(`explore.py:150`), and **one was missed: `cli_crawl.py:96`** — filed as **AT-122** (medium). It
does not inflate; it drops. Cleared, with evidence:

- `stages/coverage.py`, `stages/explore_merge.py` — no reference to issues at all; nothing about a
  crawl's issue count feeds coverage, the FlowSpec merge, or `diff_crawl`.
- `store/project_store.py:253-267` — that `add_issue` is the unrelated test-run `Issue` model, a
  different schema and a different file.
- `docs/` — no doc pins the workbook's sheet list (`docs/MAP.md:114` mentions `NoiseCount` only);
  the sheet list is pinned by the contract, amended below, and by the test in §5.
- `.goal/` dashboard — carries no crawl issue counts.

## 5. The two rulings the manifest put to the checker

**(a) The edited pre-existing test — LEGITIMATE, not a weakening.** `tests/test_crawl_report.py`
line 56 is still `assert load_workbook(out).sheetnames == SHEETS` — an equality against the full
ordered list, never a subset or a membership check. The diff adds exactly one element, in its
correct position between `Issues` and `Noise`; nothing was removed and no assertion was relaxed. A
sheet deleted, renamed, or reordered still fails it. This unit genuinely adds a sheet, and the
contract itself named the old list (X16), so the list is contract in both places and both are now
updated. Flagging it rather than burying it in the diff was the right call and is credited.

**(b) `CrawlIssue.first_party` defaulting to `True` on an EVIDENCE issue — NOISE, no AT id.**
Executed the surface question rather than reasoning about the field: `first_party` is read in
exactly one place in the tree, `crawl_report.py:96`, which renders the "First-party" column of the
**Issues** sheet — and that sheet now receives product kinds only. No filter, no count, no other
render consumes it, so the meaningless `True` on a tool failure is never displayed and can never
reach a number. It is a dormant field on that kind, not a defect. Worth a docstring line if the
field is ever surfaced for EVIDENCE; not worth an issue id today.

## 6. Empty states and the zero case

Rendered on a clean fixture crawl (`issues=1, tool_failures=0`):

- workbook summary row: `Tool failures (the crawler's own) = 0` — an honest zero, not a dash
- `Tool failures` sheet: present with its header row and no data rows — same shape `Noise` has
- crawl-page stat tile: `0`
- empty card: `The crawler recorded everything it tried to.` — reassuring, correct, and not a
  scary empty state; the product's own empty card still reads `No issues found on this crawl.`
- **crawls table: `<td>—</td>`** while the Issues cell beside it prints `0`. In that table `—` is
  the sentinel for unknown (`stop_reason or '—'`, `started_at or '—'`), so a measured zero wears the
  unknown marker. Filed as **AT-121** (low) — exactly the misleading-dash case this check was for.

## 7. Adversarial — can a tool failure still reach a product number, or worse, a product issue be
hidden as a tool failure?

Every `add_issue` call site in the tree was read (9 in `explore_node.py`). `IssueKind.EVIDENCE` has
**exactly one** producer — `explore_node.py:43`, the `except` around `session.screenshot` — and it is
unambiguously a failure of the tool. The other eight file `CONSOLE`, `NETWORK`, `NAVIGATION`,
`DIALOG`, none of which can be routed into the tool bucket. `add_issue` routes on
`kind is IssueKind.EVIDENCE`, an identity test on a `StrEnum` member, with no string comparison and
no caller-supplied override. **No construction exists in which a real product issue is
mis-classified as a tool failure and thereby hidden** — the opposite and worse error was hunted
specifically and is absent. And no path remains where an EVIDENCE issue reaches a product number:
the only unpatched reader, the CLI line (AT-122), reads `crawl.issues`, which is now product-only.

## Contract action

`qa/contracts/explore.md` X16 amended (routine, authorized by D-015): the sheet list gains
`Tool failures`; the AT-120 OPEN-gap paragraph is replaced by the criterion the fix must keep
meeting — the counter, the two summary rows, the sheet, the column, the stat and the card — so a
future kind-blind regression fails the *contract*, not only a test. **X16 is now clean for tool
failures; the amendment log says so and the amendment tightens rather than softens.** AT-121 and
AT-122 recorded inside the criterion as tracked residual gaps.

## Scoreboard

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (X16, incl. its X9 precedent), 4/4 invariants hold
            (X1 untouched, X2 untouched, X10 untouched, X11 artifacts unchanged)
FAILURES: none
ISSUES-WRITTEN: AT-121 (low), AT-122 (medium); AT-120 open -> fixed
EXPLANATION: The checker's own probe, re-run at bc29b34, measures crawl.issues = 1 and
tool_failures = 4 where it measured 5 for 1 at 6e98487, with the same kinds filed — the count was
routed, not suppressed. Both sabotages reproduce literally, including the manifest's claimed
"assert 5 == 1". The edited SHEETS test still pins an exact ordered list and the added sheet is a
legitimate contract change; first_party on an EVIDENCE issue is read by nothing and is noise. Two
display gaps found and filed as follow-ups — the crawls table shows a known zero as the unknown
dash, and the CLI one-liner omits tool failures entirely — neither inflates a product number nor
hides a product issue, so neither is a FAIL of this unit.
```
