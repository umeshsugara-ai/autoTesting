# Verdict — track-b1-observation-primitives

**Manifest:** qa/manifests/track-b1-observation-primitives.md
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3) + qa/contracts/browser-and-secrets.md
(B5, B7, B9 — no regression) + qa/contracts/execute.md (E2)
**Goal task:** T-140
**Cycle checked: 1**

## Verdict: PASS

## What I verified myself (fresh context, re-run not re-read)

### 0. Commits actually landed and are pushed

`git rev-parse HEAD origin/master` both resolve to `59c837abe5f1abdd83bcb8a3cd20ee4476686404` —
the manifest commit is HEAD and already matches origin; source commit `640cd92` (`feat(browser):
Track B1`) sits directly under it. Nothing to push.

### 1. Staleness guard

`docker inspect autotesting-autotester-1 --format '{{.State.StartedAt}}'` → started
`2026-09-07T12:41:45Z` (epoch 1788785229); newest changed-file mtime among the diff (`observe.py`)
is epoch 1788784796. Container postdates every changed file and the volume is a live bind mount
(`.:/app`), so live-container output below reflects the committed code.

### 2. Full verify suite — re-run, not trusted from the manifest

```
$ docker compose exec autotester uv run pytest tests/test_observe.py tests/test_browser_actions.py \
    tests/test_execute.py tests/test_actuator_chokepoint.py tests/test_browser.py -q
....................................  [100%]   (44 passed)

$ docker compose exec autotester uv run pytest -q
406 passed, 1 skipped  (matches manifest's claimed count, up from 385)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```
One discrepancy found in the manifest's *prose*, not its numbers: it describes the 1 skip as "the
pre-existing real-Chromium test, unrelated." Re-running with `-rA` shows the actual skip is
`tests/test_db.py:93` (`AUTOTESTER_LIVE_MONGO_TEST` opt-in), pre-existing since `af4dfbf` (well
before T-130/T-140) and indeed unrelated to this unit — the count and "pre-existing/unrelated"
claims hold, only the one-line description of *which* test is wrong. Filed as `AT-091` (low,
open) — doesn't touch any C/B/E criterion, no fix cycle burned.

### 3. Actuator choke-point — proved it has teeth on a real planted violation, not just its own
   synthetic test

The shipped `test_the_check_actually_fires_on_a_real_violation` only asserts the regex matches a
string in `tmp_path` — it never runs the real scanner (`_python_files_outside_browser` walks
`_SRC`, not `tmp_path`) against a planted file, so by itself it doesn't prove the choke-point
fires on a real violation. I planted one directly:

```
$ cat > src/autotester/stages/_planted_violation.py <<'EOF'
def bad(session):
    session.page.locator("x").click()
EOF
$ docker compose exec autotester uv run pytest tests/test_actuator_chokepoint.py -q
FAILED tests/test_actuator_chokepoint.py::test_no_direct_page_or_playwright_access_outside_browser_package
AssertionError: raw browser access outside browser/:
  stages/_planted_violation.py:3: session.page.locator("x").click()
```
`test_no_direct_page_or_playwright_access_outside_browser_package` (the real scanner, not the
synthetic teeth-test) caught it and named file:line exactly. Removed the planted file; suite is
green again (`git status` clean of it).

### 4. `launch.py`/`session.py` — byte-identical behavior, every caller intact

- `browser/launch.py::launch_options` read in full: docstring, body, and the `--no-sandbox`/
  `--disable-dev-shm-usage` comment are verbatim what `session.py` used to inline (confirmed
  against `git show ce1b624:.../session.py` — line-for-line match).
- `session.py` re-imports it (`from autotester.browser.launch import launch_options`) and
  re-exports it in `__all__`, so `from autotester.browser.session import launch_options`
  (`tests/test_browser.py`'s existing import) still resolves.
- `tests/test_browser_actions.py::test_launch_options_still_importable_from_session_after_the_move`
  asserts `launch_options(...) == moved(...)` (dict equality on real output, not a text diff) —
  re-ran it, passes; also ran `tests/test_browser.py` (unmodified) end-to-end, all green — no
  caller broke.

### 5. Four new `BrowserSession` methods route through `self._record`

Read `session.py:160-179` directly: `go_back`, `hover`, `press_key`, `scroll` each mutate the page
then `return self._record(...)` — same shape as every pre-existing action (`click`, `fill`,
`select_option`). `_record` (line 278-289) is the sole path to `self.secrets.redactor().scrub()`
before an `Evidence` is appended, so none of the four bypasses redaction. Confirmed by test
behavior too (`test_go_back_calls_the_page_and_records_url_evidence` etc. all assert on the
returned `Evidence`'s kind/label/step_order, which only `_record` populates).

### 6. `PageObserver` dialog policy — live probe against real Chromium, not fakes

```python
# real headless Chromium, page.on('dialog', ...) via PageObserver.attach
page.click('text=alert'); page.click('text=confirm'); page.click('text=prompt')
# -> dialogs: alert False, confirm False, prompt False   (all dismissed)

page.evaluate('window.addEventListener("beforeunload", e => { e.preventDefault(); e.returnValue=""; })')
page.goto('about:blank')
# -> dialogs: [('beforeunload', True)]                    (accepted)
```
Matches D-016 exactly: `beforeunload` accepted, everything else dismissed by default.

### 7. `enumerate.js` real-Chromium probe — reproduced myself

Ran the manifest's exact command (button `#go` + link with `href="/x"`, no test framework) inside
the container:
```
[{'role': 'button', 'name': 'Click me', 'selector': '#go', ..., 'tag': 'button'},
 {'role': 'link', 'name': 'Link', 'selector': 'role=link[name="Link"] >> nth=0', 'href': '/x', ..., 'tag': 'a'}]
```
Matches the manifest's claimed shape and selector priority exactly (stable `#id` for the button,
`role=...>>nth=k` for the link).

### 8. `execute.py` — BACK joins the settle-before-screenshot set, no E-criteria regression

`stages/execute.py:70` — `if step.action in (Action.CLICK, Action.NAVIGATE, Action.BACK): session.settle(...)`,
confirmed BACK was added alongside the two pre-existing entries. `settle()` itself is unchanged
(passive, exception-suppressed) so this doesn't add a step (E5 still holds) and doesn't introduce
judgement (E1 still holds — `run_case` still only returns COMPLETED/ERRORED/BLOCKED_HITL). All
four new actions dispatch through `_ACTIONS` to real `BrowserSession` methods, never touching
`session.page` directly (E2). Full `tests/test_execute.py` + `tests/test_execute_new_actions.py`
green, including the rewritten `StepNotExecutable` guard test (verified it now monkeypatches
`_ACTIONS` to remove a real handler rather than relying on an always-missing SCROLL handler —
correct fix for the regression the manifest describes).

### 9. Doctor's duplicate-concept scan actually covers `browser/launch.py` + `browser/session.py`

Planted a genuine top-level duplicate (`def check_destination(project, url): return url` appended
to `launch.py`, colliding with the existing top-level `check_destination` in `session.py`):
```
$ docker compose exec autotester uv run autotester doctor
duplicate-concept: src/autotester/browser/session.py:61 — 'check_destination' also defined in src/autotester/browser/launch.py
1 violation(s)
```
Caught it correctly, both directions. Reverted; `doctor: clean` again.

### 10. C1/C2/C3 spot-check

- New `schema/screen_graph.py` (42 lines) / `schema/crawl.py` (18 lines): `ElementRef`,
  `PageObservation`, `DialogEvent` all carry `ConfigDict(extra="forbid")`. None inherits
  `schema.base.Artifact` — correct precedent-match: they're nested value objects embedded in a
  future persisted artifact, the same pattern as the pre-existing `Evidence` (embedded in
  `RawResult`, which *does* inherit `Artifact`), not top-level persisted artifacts themselves.
- File sizes: `session.py` 289, `launch.py` 43, `observe.py` 98, `execute.py` 105 — all ≤ 300;
  `doctor` (which enforces the 50-line function cap too) is clean.
- No `*_v2`/`*_new` filenames; `launch.py` is a genuinely new module with a stated reason
  (`session.py` was at its 300-line cap) — matches C3's "new module requires a stated reason."

## Contract check

- **core-invariants C1** — holds (schema shapes above, `extra="forbid"` present, precedent-correct
  non-inheritance of `Artifact` for nested value objects).
- **core-invariants C2** — holds (`doctor: clean`, all touched files ≤ 300 lines).
- **core-invariants C3** — holds (doctor's duplicate scan proven live to cover the moved file;
  `launch_options` move is edit-in-place with a stated reason, not a duplicate).
- **browser-and-secrets B5/B7/B9** — no regression: `start()`/`close()` untouched by this diff
  (`session.py:95-118` identical logic to before, only `observer.attach` added at the end of
  `start()`); `tests/test_browser.py` (headed-default, masking, cleanup-scope tests) reruns green
  unmodified.
- **execute E2** — holds: verified directly (§8) that every new action dispatches through a
  `BrowserSession` method, never `session.page` directly, and follows the existing
  action→`_record` pattern.

## Judgment

Every claim in the manifest reproduces against evidence I generated myself: the choke-point test
genuinely catches a planted violation (its own bundled "teeth" test didn't actually prove that —
I proved it directly), the `launch_options` move is behavior-identical with every caller intact,
all four new session methods route through `_record`, the dialog policy matches D-016 against
real Chromium dialogs (not just fakes), the `enumerate.js` probe reproduces exactly, `execute.py`'s
BACK/settle wiring introduces no E-criteria regression, and doctor's duplicate scan demonstrably
covers the moved file both directions. The one issue found — a wrong one-line description of which
test the suite's single skip is — is cosmetic, filed as `AT-091` (low), and does not cost this unit
a criterion.

PASS.
