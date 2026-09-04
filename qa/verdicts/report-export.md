# Verdict -- report-export

**Manifest:** qa/manifests/report-export.md
**Contract:** qa/contracts/report-export.md (RE1-RE5)
**Cycle checked:** 1

## Verdict: PASS

## Evidence

### RE1 -- reads only existing evidence, never a new source of truth
`src/autotester/stages/report_export.py:42-45,109-113` -- both `export_excel` and `export_html`
construct a `ProjectStore(project_slug, root)` and read exclusively through `store.list_cases()`,
`store.load_results(run_id)`, `store.load_verdicts(run_id)`. `src/autotester/store/project_store.py:81,94,110`
confirms these are the store's own accessors -- no new data model. The one place the exporter
touches the filesystem directly is `_b64_png` (line 74-77) reading a screenshot file at
`store.paths.run_dir(run_id) / shot.path` -- `shot.path` comes from `Evidence` inside an
already-loaded `RawResult`, and `store.paths` is `ProjectStore`'s own path helper (same one
`ui/app.py:253-255` uses to list run dirs). No dedicated `ProjectStore` method exists anywhere in
the codebase for reading screenshot bytes, so this is the only way to embed a screenshot without
duplicating `ProjectPaths`' own logic -- not a second source of truth, not an invented path scheme.

### RE2 -- Excel: one row per case, real fields
Ran the real export against the real Pathlynks run `run-01M1N4HZ83AWWHYJ8QTENKTYBD` myself:

    uv run autotester report excel pathlynks run-01M1N4HZ83AWWHYJ8QTENKTYBD --out /tmp/checker-report.xlsx
    wrote ...\checker-report.xlsx

Loaded it with `openpyxl.load_workbook` and printed every row:

    ('Case', 'Kind', 'Class', 'Outcome', 'Result', 'Criteria met', 'Duration (s)', 'Grader', 'Notes')
    ('Login with correct credentials', 'best', 'happy', 'errored', 'INCONCLUSIVE', '0/1', 30.44, 'rule', 'not judged: execution errored')
    ('Login with correct email, wrong password', 'worst', 'auth_wrong_creds', 'errored', 'INCONCLUSIVE', '0/1', 30.84, 'rule', 'not judged: execution errored')
    ('Submit the login form empty', 'edge', 'input_empty', 'errored', 'INCONCLUSIVE', '0/1', 30.44, 'rule', 'not judged: execution errored')

Real case titles, kinds, classes, outcomes, verdict results, criteria counts, durations, grader,
and the raw error verbatim ("not judged: execution errored" is the real stored verdict scoreboard
text, not a summary) -- matches `report_export.py:50-65` field-by-field.

### RE4 -- defaults to the latest run
Ran `uv run autotester report excel pathlynks --out /tmp/checker-report-latest.xlsx` with no
`run_id`. Compared its rows programmatically against the explicit-run-id export: `match: True`.
`_latest_run_id` (`report_export.py:26-31`) sorts `runs_dir` entries and takes the last, identical
to `ui/app.py:254-255,268`'s own "latest run" convention -- RE4's stated match is real, verified by
reading both sites, not assumed.

### RE3 -- HTML: self-contained, embedded screenshots, one section per case
Read `report_export.py:80-101,104-139`: `_case_section` builds one `<section>` per case with a
result badge and a figure/img element whose src is a base64 data URI per screenshot -- never a
file path. Confirmed on the real export:

- `data:image/png;base64,` count in the file: 6 (matches 2 screenshots x 3 cases)
- regex search for any non-`data:` `<img src=...>` reference: zero matches
- no `<link>` tag anywhere in the file; `<style>` block is inline (`report_export.py:119-129`) and
  does not import/reference `ui/theme.py` or any external stylesheet -- satisfies the no-fire
  list's "no styling parity with the live UI theme" item.
- `scripts/check_no_secrets.py` on both real exported files: `scanned 2 file(s); 0 leak(s)` (RE5).

Visually confirmed by serving the file over a local HTTP server (the sandbox's Playwright blocks
file:// URLs, so I served it over localhost instead) and taking a full-page screenshot, then
viewing it with Read: three sections in run order, each with an INCONCLUSIVE badge, the real raw
Playwright timeout error text, and real embedded screenshots -- the actual Pathlynks landing/
sign-in page and the actual authenticated dashboard, rendered inline with no broken-image icons.
This matches the manifest's claim.

**Minor observation, not blocking:** the generated HTML has no meta-charset tag, so the em dash
in the title/subtitle rendered as mojibake when served without an explicit HTTP charset header.
This is a real gap in a "tester report" meant to be shared/emailed/proxied, not just opened
directly -- but it does not violate any RE1-RE5 criterion as written (the file is still
self-contained, still needs no other file, and modern browsers default local file:// opens to
UTF-8, the contract's stated primary use case). Recommend the maker add a UTF-8 meta-charset tag
to the title/style preamble in `report_export.py:130-136` as a fast-follow, but it does not
warrant a FAIL this cycle.

### CLI (RE4 mechanics)
`src/autotester/cli.py:192-219` -- `report excel`/`report html` both take `run_id: str | None =
typer.Argument(None)`, call straight into `report_export.export_excel/html`, and catch
`ValueError` to print a clean error + exit 1 rather than a traceback -- confirmed by the "no runs"
test below.

### Tests -- genuinely test the claims, not just happy path
`tests/test_report_export.py` -- read in full, ran independently:

    uv run pytest tests/test_report_export.py -v
    5 passed

- `test_export_excel_has_one_row_per_case` -- real row/field assertions.
- `test_export_excel_defaults_to_the_latest_run` -- exercises RE4 with `run_id=None`.
- `test_export_excel_raises_a_clear_error_with_no_runs` -- seeds a project with zero runs and
  asserts `ValueError` with match="no runs" -- genuinely covers the empty-state path, not skipped.
- `test_export_html_embeds_the_screenshot_and_is_self_contained` -- asserts the base64 data-URI
  marker is present, i.e. explicitly checks embedded-not-referenced, per RE3.
- `test_export_html_shows_the_error_for_an_errored_case` -- seeds Outcome.ERRORED +
  Result.INCONCLUSIVE and asserts the raw error text and INCONCLUSIVE badge appear.

All 5 exercise real behavior, including the two edge cases (no runs, errored case) the manifest
claims.

### Full suite / lint / doctor

    uv run pytest -q                       -> all passed (1 pre-existing skip, unrelated)
    uv run ruff check src tests scripts    -> All checks passed!
    uv run autotester doctor               -> doctor: clean

### Docs / dependency claims
- pyproject.toml:17 and uv.lock:1223 confirm openpyxl>=3.1.5 was added for real, not just claimed.
- docs/ARCHITECTURE.md:54 (150 lines total, matches the "at cap" claim) and docs/MAP.md:45 both
  carry the new stages/report_export.py row as claimed.
- src/autotester/stages/report_export.py is 139 lines (manifest says 133 -- a small, harmless
  undercount in the manifest's own self-report; well under the 300-line doctor cap either way).

## Judgment

This genuinely satisfies what Umesh asked for: a real Excel sheet with one row per case (title,
kind, class, outcome, verdict, criteria, duration, grader, verbatim notes) and a real
screen-by-screen HTML walkthrough with every screenshot embedded inline, opened and visually
confirmed against real Pathlynks evidence from this session's actual headed-browser run -- not a
demo/mock. RE1 is true: every read path traced to ProjectStore accessors or the store's own path
helper -- no second source of truth, no recomputed verdict, no hand-typed number. RE2-RE5 are each
backed by independent re-execution and file inspection, not the manifest's say-so.

PASS.
