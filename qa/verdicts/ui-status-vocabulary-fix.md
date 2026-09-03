# Verdict — ui-status-vocabulary-fix

**Manifest:** qa/manifests/ui-status-vocabulary-fix.md
**Contract:** qa/contracts/ui.md (U1-U5) + qa/contracts/docker.md D5
**Cycle checked: 1**

## Verdict: PASS

## What I verified myself (fresh context, re-run not re-read)

### 1. Code inspection

- `src/autotester/ui/theme.py:163-181` — `badge()` (test-result colors, unchanged
  `_BADGE_CLASS` map) and the new `pill(text, tone="neutral")` are two distinct
  functions with distinct docstrings. `badge()`'s docstring (line 164-167) now
  explicitly says "Never reuse this for a non-test-result status ... that's what
  `pill()` is for." `pill()` (line 177-181) maps tone -> `_PILL_CLASS`
  (`positive`/`warning`/`neutral`) and is documented as "anything that ISN'T a
  test result."
- `src/autotester/ui/app.py:170-203` (`env_editor_view`) — `_status_cell` (line
  181-183) now calls `theme.pill("● Set", "positive")` /
  `theme.pill("○ Not set", "neutral")` instead of `badge('PASS')`/
  `badge('INCONCLUSIVE')`. The underlying data source (`parse_env(paths.env_file
  .read_text(...))`, `present.get(key)`) is untouched — same `ProjectPaths`/env
  parsing as before, only the rendering function changed.
- `src/autotester/ui/app.py:136-166` (`project_detail`) — review status
  (`spec.review.status.value if spec is not None else "no flowspec yet"`, line
  139, unchanged logic) is now rendered via `theme.pill(escape(review),
  review_tone)` inline in the subtitle paragraph (line 162-163), not via
  `theme.stat(...)`. The stat row (line 144-149) now holds only `len(store
  .list_cases())` and `len(project.allowed_domains)` — real counts, same
  `ProjectStore`/`Project` reads as before.
- `run_view` (line 219-242) and `report` (line 245-275) still call `theme.badge`
  exclusively (lines 226, 266) — confirmed `badge()`'s `_BADGE_CLASS` map and
  call sites are byte-for-byte unchanged from before this unit; `pill()` is
  additive, no existing caller was touched.
- No `ProjectStore`/`SecretStore` call signature, no `html.escape` call, changed
  in either modified route — verified by reading both functions in full (U5
  requires whole-file verification, done here for `app.py`'s modified sections
  plus a scan of every other route, all still calling `escape(...)` on
  user/project-derived strings exactly as before).

### 2. Tests — re-run, not trusted from the manifest

```
$ uv run pytest tests/test_ui.py -v
tests\test_ui.py .........s.......                                       [100%]
16 passed, 1 skipped, 1 warning in 0.72s
```
Matches the manifest's claim exactly. Confirmed why the two substring
assertions still hold against the new markup (not just "still pass by luck"):
- `test_env_editor_never_renders_the_real_value` (line 121-136) asserts
  `"set" in response.text` — this matches the still-present static subtitle
  "Values are never shown once saved — only whether one **is set**." (`app.py`
  line 200), independent of the `pill()` label text ("● Set" is capitalized so
  wouldn't itself satisfy a lowercase substring check — the page still passes
  because of that subtitle sentence, not by accident of the pill markup).
- `test_project_detail_...` (line 78) asserts `"no flowspec yet" in
  response.text` — still literally present, now inside a `pill()` span instead
  of a `stat()` div; substring search doesn't care which wrapper element holds
  the text.

```
$ uv run pytest -q            -> 34%/69%/100%, 2 skipped total, all green
$ uv run ruff check src tests scripts   -> All checks passed!
$ uv run autotester doctor    -> doctor: clean
```

### 3. Live container — re-driven myself

- `docker compose ps` — `autotesting-autotester-1` already Up, ports
  8010->8000 and 6080->6080 mapped.
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/` -> `200`.
- Took my own headless-Playwright screenshots (not reused from the manifest) of
  `http://localhost:8010/projects/pathlynks/env` and
  `http://localhost:8010/projects/pathlynks`, plus
  `http://localhost:8010/projects/regression-demo/report` for a side-by-side
  comparison of `badge()` vs `pill()`.
  - **Credentials page:** every declared secret (`PATHLYNKS_COUNSELLOR_EMAIL`,
    `_PASSWORD`, `_USER_EMAIL`, `_USER_PASSWORD`, `_MONGO_URI`) shows a small
    green "● Set" pill under a "STATUS" column, distinct label and icon (a
    filled dot) from a test-result badge.
  - **Report page (regression-demo):** the actual test-result badge for
    comparison reads "✓ PASS" with a checkmark icon, same green family. Visual
    judgment: the two are same color family (green = "good/present", a
    reasonable and disclosed design choice per the manifest) but carry
    different icons (● vs ✓) and different words ("Set" vs "PASS") — a user
    reading either label sees unambiguous, different words. This resolves the
    literal bug reported (the OLD code called `badge('PASS')` next to a
    credential, i.e. the word "PASS" itself appeared for a credential, which
    really could read as "this test passed"). The new pill never says "PASS"
    for a credential. Net: genuine clarity improvement over the prior state,
    even though the CSS class underneath (`badge-pass`) is shared — that
    class name is invisible to the user; only the rendered text/icon matters
    for the confusion this fix targets.
  - **Project detail page:** review status ("no flowspec yet") is now a small
    gray pill inline next to the base URL/subtitle line, not a stat tile. The
    stat row holds only "3 / Cases" and "1 / Allowed domain(s)" — both real
    numbers. This directly fixes the second reported bug (a sentence sitting
    in a big-number tile).
- `docker compose restart` then `docker compose exec autotester bash -c "ps aux
  | grep -E 'x11vnc|Xvfb|websockify' | grep -v grep"` -> all three present
  (`Xvfb :99`, `x11vnc -display :99 ...`, `websockify --web=/usr/share/novnc
  6080 localhost:5900`). Confirms the earlier entrypoint restart-safety fix
  (docker.md D2) still holds after this presentation-only change.

## Contract check

- **ui.md U1** — untouched, `/onboard` code not modified by this unit.
- **ui.md U2** — `project_detail` still reads `store.load_flowspec()` and
  `store.list_cases()` live per request (line 138, 146); only presentation of
  the already-live `review` string moved. Holds.
- **ui.md U3** — `env_editor_view`/`env_editor_submit` unchanged except the
  status cell's rendering function; the real secret value is still never
  placed in the response (confirmed by the still-passing
  `test_env_editor_never_renders_the_real_value`, and by reading the modified
  function body — `present.get(key)` only ever yields a bool used to pick
  which pill, never the value itself). Holds.
- **ui.md U4** — `run_view`/`report` are unmodified by this unit (only
  `project_detail`/`env_editor_view` and `theme.py` changed); still reads real
  persisted `RawResult`/`Verdict` files. Holds.
- **ui.md U5** — every string touched by this unit (`review`, `ref.key`, pill
  label literals which are hardcoded, not user input) is still passed through
  `escape(...)` where it originates from user/project data, exactly as before.
  Holds.
- **docker.md D5** — diffed the pre-existing 6 routes' escaped-data content
  conceptually against this change: `pill()`, like `stat()`, only changes the
  chrome/wrapper around already-escaped data; no route's escaped payload
  content changed, only which theme helper wraps it. Holds — this unit is a
  same-shaped, more-scoped repeat of the D5 pattern (chrome-only change).

## Judgment

Genuinely a clarity improvement, backed by my own screenshots: the credential
page no longer displays the literal word "PASS" (a test-verdict word) next to
a credential, and the review-status sentence no longer sits inside a
big-number stat tile. `badge()` is byte-identical to before and its two
existing call sites (`run_view`, `report`) are untouched — confirmed by
re-running the full test suite and by screenshotting the report page's real
"✓ PASS" badge alongside the credential page's "● Set" pill. All of ui.md's
U1-U5 hold, none of the underlying `ProjectStore`/`SecretStore` logic or
escaping discipline changed — this was presentation-only, as claimed.

PASS.
