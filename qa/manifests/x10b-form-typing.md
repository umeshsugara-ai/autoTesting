# Manifest - x10b-form-typing (Pathlynks campaign, stage-2 precondition)

**Unit:** X10-b amendment (D-029) made real: the explorer may type SYNTHETIC,
non-PII, deterministic values into post-login form fields under TEST_ACCOUNT /
ALLOW_WRITES, on a non-production target, non-destructive - and never at any
other policy. Encoding in code (SafetyPolicy + a typing pre-pass in
explore_node) and amending qa/contracts/explore.md X10 + X5 exactly as D-029's
Changes-authorized line permits.
**Contract:** qa/contracts/explore.md X10 (amended to X10-b), X5 (typing column),
X12 (unchanged: the fill CHOICE is DOM-driven, the VALUE comes from a fixed
deterministic generator, no provider), X6/X5 (never-click + deny-list unchanged),
V7b (fills become exercised controls; refusals get policy: reasons).
**Goal task:** enables stage-2 of the Pathlynks live-crawl gate answer
(qa/gates/live-crawl-target.md + qa/gates/post-login-forms.md, both answered
2026-09-21); authorized by D-029 (Changes-authorized: explore.md X10 + X5).
**Date:** 2026-09-21
**Fix cycle:** 1 of max 3
**Dual check:** no (contract amendment is the checker's own surface; checker
verifies the code against the amended criterion in cycle 1)
**Issues addressed:** none (new capability, not a defect fix); unblocks
live-crawl stage 2.

## What was built

1. `src/autotester/schema/crawl.py::SafetyPolicy.synthetic_typing: bool = False`
   - the deliberate, explicit switch a run sets only when D-029's four
     conditions are met; default OFF means X10 stays as-was for every existing
     caller and every existing test.
2. `src/autotester/stages/explore_safety.py::typing_allowed(policy)` - the ONE
   boolean the crawler consults; False unless write_policy in
   {TEST_ACCOUNT, ALLOW_WRITES} AND policy.synthetic_typing.
3. `src/autotester/stages/synthetic_values.py` (new module, one job: the value
   generator) - deterministic, seeded by the field's own name/role; email,
   text, number, date, search; password-named fields are never typed (a
   "change password" form must not be exercised by the crawler; D-029
   non-destructive); uploads never typed.
4. `src/autotester/browser/session.py::first_option(locator)` - browser/ door
   for combobox option reading (X2: the explorer composes session methods).
5. `src/autotester/stages/explore_node.py::type_form(rt, node)` - typing
   pre-pass before the click loop: textbox/textarea get FILL, combobox gets
   SELECT; each records an edge (SAME_SCREEN or NAVIGATED), counts toward the
   per-node cap and max_actions (X4 bounds apply to typing too).
6. Coverage: fills count as exercised (SAME_SCREEN/NAVIGATED already in
   PERFORMED); a refused typing action records DENIED_POLICY with
   `policy:typing disabled` (V7 reason set unchanged).
7. `qa/contracts/explore.md`: X10 reworded to the X10-b rule (4 conditions,
   each violation = refusal), X5's typing column amended, no-fire row updated,
   amendment-log entry appended (D-029 cited as authorization).

## How to verify (commands + expected)

```
uv run pytest tests/test_explore_typing.py   # new; expect all pass
uv run pytest tests/test_explore.py tests/test_explore_safety.py tests/test_crawl_coverage.py  # regression: typing-off behaviour byte-unchanged
uv run ruff check src tests scripts          # expect: All checks passed!
uv run autotester doctor                     # expect: doctor: clean
```

## Capability coverage (each claim -> its isolating check)

| capability | check | falsifying condition |
|---|---|---|
| typing happens under TEST_ACCOUNT when enabled | typing test | typed values absent from page.fills |
| typing NEVER happens under READ_ONLY | typing test | a fill leaks through at READ_ONLY |
| typing NEVER happens with synthetic_typing=False | typing test | a fill leaks through at TEST_ACCOUNT with the flag off |
| password fields never typed | typing test | a password field receives a value |
| values are synthetic + deterministic | typing test | same field yields a different value across runs |
| destructive submit still denied under TEST_ACCOUNT | typing test | Delete-labelled control clicked |
| combobox selects a real option | typing test | select_option called with a value not among options |

## Actual outputs (my own run, 2026-09-21)

```
$ uv run pytest tests/test_explore_typing.py
10 passed in 60.30s        # 9 fake-site/gate tests + 1 REAL-browser proof (~55s)
$ uv run pytest tests/test_explore.py tests/test_explore_safety.py tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_explore_live.py tests/test_browser.py tests/test_secrets.py tests/test_actuator_chokepoint.py
84 passed in 128.96s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
2 violations -- BOTH stale-generated (docs/MAP.md, docs/SNAPSHOT.md); regenerated with
`autotester map` + `autotester snapshot` at close-out before ready-for-check
```

Build notes (deviations from the plan above, all improvements):
- The typing pre-pass lives in its own module `src/autotester/stages/explore_typing.py`
  (79 lines) instead of inside `explore_node.py` — the 300-line cap forced the split
  (explore_node was 323 with it inline); `visit_node` calls it through a lazy import
  because `explore_typing` imports `explore_node`'s edge/issue/return helpers (one
  concept, one place: node bookkeeping stays in explore_node, typing in explore_typing).
- `browser/session.py` was refactored OVER the cap by first_option; compacted
  `_record`/`__init__`/`close` signatures to land at 298/300 lines — behaviour-identical
  (test_browser.py + test_browser_navigation_secrets.py green).
- Live proof detail: the fixture's settings form is a GET form (`action="/saved.html"`),
  so the submitted value is visible in the reached node's url_example
  (`/saved.html?displayname=AutoTester+College+N`) — the assertion reads the persisted
  graph, not the page's live DOM.
- `crawl_fake.py` gained additive pieces only: FakeOption/FakeLocator.all/select_option/
  locator, a `selects` list on FakeSitePage, and two X10-b elements on the settings page.
  All 19 pre-existing test_explore tests pass byte-unchanged.

## Status: ready-for-check
