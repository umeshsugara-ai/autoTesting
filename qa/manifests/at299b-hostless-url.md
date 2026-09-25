# Manifest — at299b-hostless-url

**Contract:** qa/contracts/core-invariants.md (I7 — `url_template`/`absolute_url` are the ONLY
place a URL is normalised into a screen-identity path)
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-299b

## The bug

`core/urls.py::absolute_url` prepended `https://` to ANY hostless input unconditionally. `urlsplit`
then always reads the first `/`-delimited segment of a scheme-relative-looking string as the host,
so `url_template(..., keep_host=False)` silently DELETED it even when it was genuine path:

- `"erp/trainers"` -> `absolute_url` -> `"https://erp/trainers"` -> templated -> `"/trainers"`
  (lost "erp" — cycle-2 code, without `absolute_url`, produced the correct `"/erp/trainers"`)
- `"students/1"` -> `"/{id}"` (lost "students")
- prose the model returns, e.g. `"Sign in page"` -> `"/"` — a false claim that the site ROOT is
  covered (pre-AT-294 behaviour produced the harmless junk `"/Sign in page"` instead)

## What changed

`src/autotester/core/urls.py:37-79` (`absolute_url`) — added a guard before the unconditional
`https://` prepend: the first `/`-delimited segment is only treated as a host when it carries a
signal an address-bar host actually has — a domain dot (`vidysea.com`) or a port colon
(`localhost:3000`). Otherwise the string is returned unchanged, so `url_template` keeps every
segment as path.

```python
    first_segment = url.split("/", 1)[0].split("?", 1)[0]   # urls.py:76
    if "." not in first_segment and ":" not in first_segment:  # urls.py:77
        return url
    return f"https://{url}"                                   # urls.py:79
```

This is deliberately narrower than the AT-287 whole-string host-shape guessing that was already
rejected as unwinnable (`settings.json` vs `example.com` are the same shape). Here the question is
only "does the first segment of an already-multi-part string carry a host-only signal", and a bare
relative path built from real segments (`erp/trainers`, `students/1`) carries neither. Full
reasoning is in the updated docstring at `urls.py:38-71`.

Callers (`stages/explore_status.py:52`, `stages/ingest.py:137`, `stages/product_map.py:40,61`) are
unchanged — they all call `url_template(absolute_url(x), keep_host=False)`, so fixing
`absolute_url` once fixes all three call sites uniformly.

**Known residual gap, accepted rather than guessed around further** (documented in the docstring):
a bare hostname with no dot and no port (`localhost/students`) or a first path segment that itself
contains a dot (`v1.2/foo`, `settings.json/edit`) still reads as a host. No existing test (direct
or via any of the three callers) exercises that shape through `absolute_url`; `url_template` called
directly (bypassing `absolute_url`) already handles `v1.2/foo`/`settings.json` correctly and is
untouched by this change.

## TDD — red first, in a scratch copy outside the worktree

Per the hard rule, the tracked worktree file was never edited to falsify or red-test. All red-first
and mutation work ran against throwaway copies in
`C:/Users/Lenovo/AppData/Local/Temp/claude/.../scratchpad/at299b_redcheck/` (plain-Python scripts,
no pytest needed — `urls.py` has no third-party deps).

**1. Red against the original (pre-fix) code**, copied verbatim before any edit:

```
$ python3 red_check.py
FAIL  'hostless multi-segment path': absolute_url('erp/trainers') -> url_template -> '/trainers' (expected '/erp/trainers')
FAIL  'hostless path with id segment': absolute_url('students/1') -> url_template -> '/{id}' (expected '/students/{id}')
PASS  'dotted host still stripped': absolute_url('vidysea.com/erp/trainers') -> url_template -> '/erp/trainers' (expected '/erp/trainers')
PASS  'port host still stripped': absolute_url('localhost:3000/students/1') -> url_template -> '/students/{id}' (expected '/students/{id}')
PASS  'scheme-relative host still stripped': absolute_url('//host/x') -> url_template -> '/x' (expected '/x')
PASS  'already-absolute path unchanged': absolute_url('/erp/trainers') -> url_template -> '/erp/trainers' (expected '/erp/trainers')

2 failing / 6 total
```

Confirms the two regression shapes were red and the four already-working shapes were untouched by
the bug, before any fix code was written.

**2. Fix applied to the real worktree file** (`urls.py:76-79` above), plus new pytest tests added
to `tests/test_urls.py` (5 new test functions covering the same shapes, `absolute_url` now imported
directly).

## Capability coverage table

Each row: claim -> single-hunk falsifying mutation (applied only to a throwaway copy in the scratch
dir, `mutants/*.py`) -> the check that goes red on the mutant and stays green on the fixed copy.
Full harness + output: `capability_check.py` in the scratch dir.

| Claim | Falsifying single-hunk edit | Check that goes red |
|---|---|---|
| Hostless multi-segment path is not eaten (`erp/trainers`, `students/1`) | Delete the `first_segment` guard entirely (revert to unconditional `https://` prepend — the original bug) | `test_absolute_url_leaves_a_genuine_hostless_relative_path_alone` |
| Dotted host (`vidysea.com`) is still recognised & stripped | Narrow the guard to check only `:` (drop the `.` check) | `test_absolute_url_still_restores_scheme_for_a_dotted_or_ported_host` |
| Ported host (`localhost:3000`) is still recognised & stripped | Narrow the guard to check only `.` (drop the `:` check) | `test_absolute_url_still_restores_scheme_for_a_dotted_or_ported_host` |
| Scheme-ful / scheme-relative / absolute-path input passes through unchanged | Remove the leading `"//" in url.split("?", 1)[0][:8]` early-return | `test_absolute_url_passes_through_scheme_ful_and_absolute_path_input` |
| Prose input no longer falsely claims the site root | Same as row 1 (revert to unconditional prepend reproduces `"Sign in page"` -> `"/"`) | `test_a_non_url_transcription_no_longer_falsely_claims_the_site_root` |

Actual run of the harness (fixed copy green, each mutant red):

```
$ python3 capability_check.py
Claim 1: hostless multi-segment path not eaten (erp/trainers, students/1)
  fixed module  -> PASS (expected)
  mutant mutant_no_guard        -> FAIL/red (expected)
Claim 2: dotted host (vidysea.com) still recognised & stripped
  fixed module  -> PASS (expected)
  mutant mutant_dot_only        -> FAIL/red (expected)
Claim 3: ported host (localhost:3000) still recognised & stripped
  fixed module  -> PASS (expected)
  mutant mutant_colon_only      -> FAIL/red (expected)
Claim 4: scheme-ful / scheme-relative / absolute-path input passthrough
  fixed module  -> PASS (expected)
  mutant mutant_no_scheme_guard -> FAIL/red (expected)
Claim 5: prose input no longer falsely claims the site root
  fixed module  -> PASS (expected)
  mutant mutant_no_guard        -> FAIL/red (expected)

ALL CAPABILITY ROWS OK
```

## How to verify (targeted — see Gaps for why not the full adapter command)

- `uv run pytest tests/test_urls.py tests/test_ingest_persist.py tests/test_product_map.py tests/test_ui_product_map.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_crawl_liveness.py tests/test_crawl_status_surfaces.py`
- `uv run ruff check src tests scripts`
- `uv run autotester doctor`

## Actual outputs (from maker's own run, this worktree)

```
$ uv run pytest tests/test_urls.py tests/test_ingest_persist.py tests/test_product_map.py tests/test_ui_product_map.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_crawl_liveness.py tests/test_crawl_status_surfaces.py
........................................................................ [ 94%]
....                                                                     [100%]
76 passed, 1 warning in 8.22s
(warning is a pre-existing starlette/anyio DeprecationWarning, unrelated to this change)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

LIVE-BROWSER: not-applicable (no browser/network code touched — pure string templating).

## Gaps

- **Full suite not run.** Free RAM measured ~416 MB (`Get-CimInstance Win32_OperatingSystem` ->
  FreePhysicalMemory 426072 KB) at the start of this unit, well under the 3.5 GB floor for
  `uv run pytest` (full). Ran the targeted set above instead: `tests/test_urls.py` (the function's
  own tests, both old and new) plus every test file that references `url_pattern` /
  `absolute_url` / `url_template` through the three real callers (`ingest`, `product_map`,
  `explore_status` via its login-wall/crawl-status consumers) — 76 tests, all green. Not run:
  test files with no textual reference to these symbols (unlikely to exercise this path, but not
  independently confirmed).
- **Residual host/path ambiguity**, documented in the new docstring and above: a bare hostname
  with no dot/port, or a path segment that itself contains a dot, is still misread as a host. No
  caller currently exercises this shape through `absolute_url` (confirmed by grep across
  `tests/`), so it is a known limitation rather than a regression, and not asserted against.
- "Optionally reject an observed url containing whitespace" (issue's suggested extra guard) was
  NOT implemented — out of scope for the segment-eating bug this unit targets; the prose case is
  already improved (no longer claims root) without it.

Status: ready-for-check
