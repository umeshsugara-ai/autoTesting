# Manifest — t170-network-assertions
**Contract:** qa/contracts/network-assertions.md
**Goal task:** T-170
**Date:** 2026-09-24
**Fix cycle:** 1 of 3
**Dual check:** no  ← T-170's goal-task criticality is `high`, not `critical` (7b applies only to `critical`)
**Issues addressed:** none
**Executor:** claude-sonnet-subagent
**Executor rationale:** schema/security/auth-adjacent (secrets boundary, NA5) and a `high`-criticality goal task — kept on a Claude subagent per the "never delegate" list, no `record` row needed.

## What changed

- `src/autotester/browser/observe.py` — `PageObserver` gains a `responses` buffer (method, url,
  status) populated for EVERY response (not only failures) in the existing `_on_response` handler,
  plus `drain_responses()` to read+clear it. No second `page.on` listener (NA6).
- `src/autotester/stages/network_capture.py` (new) — `first_party_evidence(responses, project,
  policy, redactor, *, step_order=None) -> list[Evidence]`: turns buffered responses into
  `EvidenceKind.NETWORK` evidence, first-party only (reuses `explore_safety.classify_request`, X9/C3),
  scrubbed through the caller's `Redactor` (NA5). Pure data transform, no browser, no provider (NA4),
  no import of `grade` (NA2). Shared by both the run and the crawl path (NA6/C3 — one conversion).
- `src/autotester/stages/execute.py` — `_drain_network_evidence(session)` folds first-party NETWORK
  evidence into `session.state.evidence` after every step (before that step's own `assert_expected`
  call, so a same-step declared `network` pattern already sees it). `_declares_expectation` now
  includes `expected.network`. `_assertions_unmet` now also recognises `EvidenceKind.NETWORK`
  `assert `-prefixed items (previously `dom` only), so an unmet declared network pattern makes the
  outcome `ASSERTION_FAILED` the same way url/visible_text/absent_text/dom_asserts already do.
- `src/autotester/browser/assertions.py` — `met()` and `assert_expected()` now evaluate
  `expected.network`: one `assert network: met|unmet (<pattern>)` `EvidenceKind.NETWORK` item per
  declared pattern, via a new `_network_met(session, pattern)` helper that reads already-captured
  NETWORK evidence on `session.state.evidence` (a pure read of the observed stream, NA4). Module +
  method docstrings updated to state `network` is now handled here, discharging D-032's deferral
  (NA3).
- `src/autotester/browser/session.py` — `assert_expected`'s docstring updated in place (line-neutral
  edit; the file was already at the 300-line cap) to say `network` is now a deterministic field here
  too.
- `src/autotester/stages/explore.py` — new `_fold_network_evidence(rt)`, called once from `_finish`
  before the crawl envelope is saved: drains the observer's buffer and persists first-party NETWORK
  evidence via the new store method (crawl side of NA1 — a crawl has no per-step `RawResult` to fold
  into progressively the way a run does).
- `src/autotester/core/paths.py` — `ProjectPaths.crawl_network(crawl_id)` — `crawl/<id>/network.jsonl`.
- `src/autotester/store/crawl_store.py` — `add_crawl_network` / `list_crawl_network`, mirroring the
  existing `add_crawl_issue` / `list_crawl_issues` pattern exactly.
- `docs/MAP.md` — regenerated via `autotester map` (generated section only, per C2/ARCHITECTURE.md;
  no hand edits).
- `tests/test_network_assertions.py` (new) — NA1-NA6 coverage, TDD (written before the
  implementation), local fakes only (no real browser, no external site).

**Deliberately NOT changed:** `docs/ARCHITECTURE.md` prose — D-040's `Changes-authorized` scopes the
ARCHITECTURE.md edit to T-165's traversal-strategy line only, not T-170; this unit adds no
authorized ARCHITECTURE.md change and none was made. `qa/contracts/network-assertions.md` — maker
reads only.

## How to verify (commands + expected)

- `uv run pytest tests/test_network_assertions.py` (bare, no `-q`, AT-503) → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0
- `uv run pytest` (full suite, bare) → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_network_assertions.py
............                                                             [100%]
12 passed in 0.33s
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest        (full suite, bare, no -q — AT-503; run before the mutation cycles below;
                         the tree since then is identical, confirmed by `git status`/`grep` after
                         every sabotage was reverted, so this run stands for the current tree)
2 failed, 1616 passed, 5 skipped, 32 xfailed, 1 warning in 852.78s (0:14:12)

FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
  — known pre-existing flake, not this unit's (ISS-t164-1), named in the dispatch brief.
FAILED tests/test_goal_criticality_vocabulary.py::test_every_base_criticality_is_a_value_the_classifier_recognises
  — pre-existing, unrelated to T-170: T-175's `base_criticality: "normal"` (registered by D-041,
    already on the base commit before this branch) is outside CLASSIFIER_VOCABULARY. Confirmed via
    `git diff ea6b7c3 -- .goal/goal.json` (empty) and `git status --porcelain -- .goal/goal.json`
    (empty) — this unit never touches `.goal/goal.json`.
```

## Capability coverage (each new claim -> its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| NA1: first-party responses captured as NETWORK evidence, every crawl+run, independent of status, third-party excluded | `test_na1_first_party_responses_are_captured_third_party_are_not` | `network_capture.py`: inverted the first-party filter (`!=` → `==` "first_party") | before: `1 passed in 0.07s`. after: `FAILED ... AssertionError: assert 'app.pathlynks.test/api/students' in 'GET https://cdn.unrelated-third.test/px.gif -> 200'` — the filter now kept the third-party call and dropped the first-party one, exactly the inverted condition. revert: `1 passed in 0.07s` |
| NA2: capture path never imports the grader (observation only) | `test_na2_no_grade_import_in_the_capture_path` | `network_capture.py` module docstring: added a line reading `from autotester.stages import grade` | before: `1 passed in 0.05s`. after: `FAILED ... assert 'grade' not in ...` (matched `es import grade`). revert: `2 passed in 0.06s` |
| NA3: a declared `network` pattern gets a real met/unmet check, recorded not raised | `test_na3_an_unmatched_network_pattern_is_unmet_and_fails_the_assertion` | `assertions.py`: `assert_expected`'s network block hardcoded the label to `"met"` regardless of `found` | before: `1 passed in 0.07s`. after: `FAILED ... AssertionError: assert <Outcome.COMPLETED> is <Outcome.ASSERTION_FAILED>` — an unmet pattern was mislabeled met, so the run never flipped to ASSERTION_FAILED. revert: `3 passed in 0.10s` |
| NA4: deterministic, no provider import anywhere in the capture module | `test_na4_no_provider_import_anywhere_in_the_capture_module` | `network_capture.py` module docstring: added a line reading `import anthropic` | before: `1 passed in 0.04s`. after: `FAILED ... AssertionError: assert not <re.Match ... match='import anthropic'>`. revert: `1 passed in 0.09s` |
| NA5: a captured URL is scrubbed through `Redactor` before it becomes evidence | `test_na5_a_secret_value_in_a_captured_url_is_scrubbed` | `network_capture.py`: dropped `redactor.scrub(...)`, used the raw f-string as `path` | before: `1 passed in ...`. after: `FAILED ... AssertionError: assert 'hunter2' not in 'GET https:/...nter2 -> 200'` — the raw secret value leaked into the evidence path. revert: `1 passed in 0.06s` |
| NA6: exactly one `page.on("response", ...)` listener in `src/autotester/browser/`, no second capture mechanism | `test_na6_exactly_one_response_listener_exists_in_browser` | `observe.py`: added a second `page.on("response", self._on_response)` line in `attach()` | before: (part of the full-file run above). after: `FAILED ... AssertionError: ['observe.py:53', 'observe.py:54'] ... assert 2 == 1`. revert: confirmed via `git status`/`grep sabotage` clean + full `test_network_assertions.py` re-run: `12 passed in 0.33s` |

Every sabotage was a single-hunk edit to exactly the file/line named, reverted immediately after
the red run was captured, and the tree's final `git status --porcelain` / `grep -rn sabotage` (no
hits) confirm no residue. Each failure is attributed to the specific assertion the named test makes
for the capability it covers, not a generic collection or import error (core-invariants C7's
kill-attribution clause).

## Live browser evidence

Not UI-touching — no surface changed. This unit touches only `src/autotester/browser/observe.py`,
`src/autotester/browser/assertions.py`, `src/autotester/browser/session.py` (docstring only),
`src/autotester/stages/execute.py`, `src/autotester/stages/explore.py`,
`src/autotester/stages/network_capture.py` (new), `src/autotester/core/paths.py`,
`src/autotester/store/crawl_store.py`, `docs/MAP.md` (generated), and
`tests/test_network_assertions.py`. None of these are `*.tsx|jsx|vue|svelte|html|css`,
`apps/web/**`, `**/routes/**`, `**/pages/**`, or `**/components/**`, and no `ui/` file changed
(`git status --porcelain` confirms). No `qa/ui-surfaces.json` narrowing was needed.

## Status: ready-for-check
