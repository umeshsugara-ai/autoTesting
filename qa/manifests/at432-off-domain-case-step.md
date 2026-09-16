# Manifest — at432-off-domain-case-step

**Unit:** AT-432 — the case form saved a navigate step to a host the project may never visit
**Contract:** `qa/contracts/ui.md`; core-invariants C2, C3, C7; the B6 domain boundary
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-432 (medium)

## What was wrong

On a project whose `allowed_domains` is `['127.0.0.1']`, the case form accepted and **saved**
`navigate https://evil.test/`. Nothing said so. The case could never run: the first time anyone
pressed Run it would die at step 1 with `NavigationRefused`, hours after the mistake and with no hint
that the case form was where it happened.

This is **AT-058's dead-on-arrival class one level down.** `_require_reachable_base_url` already
refuses a *project* whose own base URL is off-domain; nothing did the same for a *case step*.

## What changed

- `src/autotester/ui/helpers.py` — new `_require_reachable_navigate_steps(steps, project)`, next to
  its sibling `_require_reachable_base_url`.
- `src/autotester/ui/routes_cases.py::create_case` — calls it after the steps are built and
  **before** `Case(...)` / `store.add_case`.
- `tests/test_ui_case_navigate_reachability.py` (new) — 7 tests.
- `tests/test_ui_cases.py` — appended to first, then the block moved to its own file when it reached
  318 lines; the file is back to its original 208, byte-identical to HEAD.

### Design: the run-time check decides, the UI only words it

The decision is **`browser.session.check_destination` — the exact function that refuses the step at
run time.** Creation and execution therefore cannot disagree, and there is no second copy of the
domain rule to drift. Three consequences, each checked before building:

- **A relative target (`/login`) is refused.** `check_destination` refuses any target with no
  parseable host, and `BrowserSession.goto` passes the target straight to `page.goto` with no URL
  join — so a relative target never worked at run time. Refusing it now agrees with run time; it is
  not a new restriction.
- **A `{{SECRET:KEY}}` placeholder target is skipped.** `goto` resolves a placeholder *before*
  `check_destination`, and the whole target may be a placeholder with no host to check here (AT-076).
  It stays gated at run time against the secret's own declared domains. Refusing it would break a
  supported feature to close this one.
- **Non-navigate steps are skipped.** A click's target is a locator, not a destination.

**The message is the UI's own, not `check_destination`'s.** That message names the host
unconditionally, and `host_of` returns a *pseudo-host* for garbage — so a credential pasted into a
navigate target would come straight back in the response (AT-088). The host is named only when it
matches `_HOSTNAME_RE`, exactly as `_require_reachable_base_url` already does.

**Import safety checked:** the actuator choke-point test forbids only `.page.` and `playwright`
outside `browser/`; `routes_crawls.py` already imports from `browser.session`; and importing
`session.py` was measured **not** to load Playwright, so the UI still does not pull it in at start-up.

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| An off-domain / relative / credential-shaped navigate target is refused | `test_an_off_domain_navigate_step_is_refused_and_nothing_is_saved` (+ step-2, relative, canary tests) | `routes_cases.py`: delete the `_require_reachable_navigate_steps(...)` call | GREEN before (`7 passed`); after **4 failed, 3 passed** — the four refusal tests; the three acceptance tests stay green, correctly |
| A `{{SECRET:KEY}}` placeholder is not judged at creation | `test_a_secret_placeholder_target_is_not_judged_at_creation` | `helpers.py`: drop `or PLACEHOLDER_RE.search(step.target)` from the skip | GREEN before; after **FAILED exactly 1** |
| Only navigate steps are judged | `test_a_non_navigate_step_with_an_off_domain_looking_target_is_not_refused` | `helpers.py`: skip condition → `if PLACEHOLDER_RE.search(step.target):` (judge every step) | GREEN before; after **FAILED exactly 1** |
| **A pasted credential is never echoed back (AT-088)** | `test_a_pasted_credential_in_a_navigate_target_is_not_echoed_back` | `helpers.py`: `if host and _HOSTNAME_RE.fullmatch(host):` → `if host:` | GREEN before; after **FAILED exactly 1** — without the guard the canary comes back in the response |
| Nothing is saved on refusal — not merely "a 400 is returned" | `...refused_and_nothing_is_saved` + `...offending_step_is_named...` | `routes_cases.py`: `store.add_case(...)` inserted *before* the check | GREEN before; after **5 failed, 2 passed** |

**Rows 2, 3 and 4 each break exactly one test**, which is the evidence that each of the three
exemptions in this unit is load-bearing rather than decorative. **Row 4 is the security-relevant
one:** remove the hostname-shape guard and a password pasted into a target is returned to the
browser.

**Row 5 is broader than I intended, and I am saying so rather than presenting it as isolating.** It
did break the two refusal tests on `nothing may be saved`, which is its point — but it also broke
three acceptance tests, because saving early makes the route's own `_refuse_duplicate` fire on the
normal save that follows. It proves the state assertions are load-bearing; it does not isolate them.

Every anchor asserted to match exactly once and to produce a real change; none broke import or
collection (7 collected every run).

## Two of my own test mistakes, caught before they could mislead

1. **Wrong API.** I wrote `ProjectStore.load_cases()`; the method is `list_cases()`. Five tests
   failed on `AttributeError`. The first test's 400 and message assertions had **already passed**
   before reaching that line, so the fix was fine — the tests were wrong.
2. **The placeholder test was measuring a different guard.** It used an *undeclared* credential key,
   and the 400 came from a pre-existing guard ("this project has not declared a credential called
   ..."), not from this unit. As an acceptance test it failed for an unrelated reason; **written as
   a refusal test it would have passed for the wrong one.** Fixed by declaring the credential first,
   and row 2 above proves the test now exercises this unit's code path.

## Live browser evidence

**`qa/evidence/browser-at432-off-domain-case-step-2026-09-16/report.json`** — a **maker smoke**, not
the validation. Real Chromium, isolated root with the Vidysea projects deleted, `regression-demo`
(allowed domain `127.0.0.1`).

- **Off-domain step through the real form and the real "Add case" button:** HTTP 400 —
  *"this case could never run: step 1 navigates to 'evil.test', which is not covered by allowed
  domains ['127.0.0.1']."* Case count **44 before, 44 after**; the probe was not saved.
- **In-domain step through the same button:** redirected to the cases page, count **44 → 45**, the
  in-domain probe listed, the off-domain probe still absent, **0 console errors**.
- **1 console error in the whole session**, attributed: the deliberate 400.

## What this does not claim

- **The refusal still renders as raw JSON** replacing the page, with typed steps lost. Pre-existing,
  already filed as **AT-439**; not introduced or fixed here.
- It checks only **user-entered cases**. Cases produced by `/cases/generate` or by FlowSpec expansion
  are not gated by this helper; they still fail safely at run time via `check_destination`, but they
  are not refused up front. Worth a separate look, not silently in scope.
- It does not re-validate **existing** cases already on disk.
- **`src/autotester/ui/helpers.py` is now at 299 lines** — at the doctor's budget. I trimmed my own
  docstring to land there rather than splitting a module for line count, but the next validator
  added to that file will force a real split. AT-403 already flagged modules sitting at 290–300.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_case_navigate_reachability.py tests/test_ui_cases.py tests/test_ui_case_management.py -q` → exit 0
- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean` (RED twice mid-build — `helpers.py` 315, then 301 — resolved, not suppressed)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_cases.py tests/test_ui_case_navigate_reachability.py tests/test_ui_case_management.py -p no:cacheprovider -o addopts= -q
26 passed, 1 warning in 1.70s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest -q
........................................................................ [  5%]
..................................xx....xx..xxxxxx....xx..xxxxxx..xxxxxx [ 10%]
xxxxxxxx...................................................x............ [ 16%]
........................................................................ [ 21%]
..................................................................s..... [ 27%]
........................................................................ [ 32%]
........................................................................ [ 37%]
........................................................................ [ 43%]
........................................................................ [ 48%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 65%]
........................................................................ [ 70%]
........................................................................ [ 75%]
.........................................................s.............. [ 81%]
........................................................................ [ 86%]
........................................................................ [ 92%]
........................................................................ [ 97%]
.................................                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  D:\autoTesting\.venv\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
EXIT: 0
```

The command's entire output, redirected to a fresh file: exactly one `EXIT` line and zero `FAILED` lines. **The 33 `x` marks are expected failures, none this unit's** — `pytest -o addopts= -q -rx` attributes 32 to `tests/test_browser_scroll_invariance.py` and 1 to `tests/test_browser_visual_order.py` (a deliberate `xfail(strict=True, reason="AT-438")`), both the concurrent session's files.

**A first capture is NOT cited, and why matters.** I backgrounded a run with a shell `&`, assumed it had died with its shell, and relaunched. It had not: both wrote into the same file, which ended holding two runs — one `EXIT: 1` with `FAILED tests/test_browser_visual_order.py::test_content_visibility_hidden_is_reported_exactly_where_it_paints[ruby]` on `net::ERR_NO_BUFFER_SPACE`, and one `EXIT: 0`. A process check then showed the other session was simultaneously running its own browser suites, so up to three browser suites shared the host's socket buffers. That failure did **not** recur in this single clean run and lies in a file this unit does not touch — consistent with host resource contention (AT-391's class), not a defect. Recorded because a capture assembled from two concurrent runs is not evidence of either.

**Sabotage confirmation (C7):** `git archive HEAD` extract with its own `uv sync`;
`autotester.ui.helpers.__file__` confirmed inside the extract; baseline 7 passed; five mutations from
pristine backups with exactly-once anchors. Extract deleted; **then** the suite.

## Data-boundary gate (MC-003)

Exits 1 on the missing `data_class` — AT-365, open, at HUMAN_GATE. Not introduced here.

## Checker ruling (2026-09-16, verdict 3ca11d1) — PASS, 4/4 criteria, 4/4 invariants, 5/5 rows

**Validated in the checker's own live browser** — own server on port 8022, own isolated copy with this
unit's files layered on, Vidysea projects deleted, no `.env`. It did not read my evidence first.
Ten scenarios through the real case form, case counts checked on disk:

- **Refused, nothing saved:** off-domain target; step-2 off-domain (step named); relative `/login`; a
  canary pasted as a target — absent from the response, the page, **the server log and `cases.jsonl`**;
  and `regression-demo` off-domain, count held at 44.
- **Saved:** in-domain; subdomain; a declared `{{SECRET:KEY}}` target, **stored as the placeholder with
  the real value not on disk**; a click whose selector contains an off-domain URL; `regression-demo`
  in-domain, 44 → 45.
- **5 console errors = exactly the 5 deliberate 400 refusals.** None unexplained.

**The claims I asked it to test, independently:**
1. **No regression on relative targets** — `execute.py:27` hands the target straight to `session.goto`,
   which calls `check_destination` then `page.goto` with no URL join; `host_of("/login")` returns `""`
   and is refused. A relative target never ran.
2. **Rows 2/3/4 each break exactly one test.** With the hostname guard removed, the lowercased canary
   genuinely comes back.
3. **The corrected placeholder test reaches this unit's code** — under mutation 2 a declared
   placeholder gets this unit's own message (`"step 1 needs a full URL"`); an undeclared key gets the
   other guard's.
4. **Row 5 adequately disclosed** as broad.
5. **Suite contention attribution accepted** — the error was in a file this unit does not touch, did not
   recur in its own clean run, and the mixed capture was not cited.

### The scope gap is wider than I disclosed — AT-441 (low)

I named `/cases/generate` and FlowSpec expansion as ungated paths. **The checker found two more:**
`cli.py:238` and the cases `stages/agent_loop.py` saves after correcting them. All four still **fail
safely at run time** — `execute.py:82` catches `NavigationRefused` and marks the case ERRORED — so none
is a silent pass, but none is refused up front either.

### One discrepancy I found at close-out, and fixed

I had written, and the checker had confirmed, that `tests/test_ui_cases.py` was "back to its original
208 lines, byte-identical to HEAD". **It was not byte-identical.** Its content matched exactly (208 lines,
an empty diff once line endings are ignored), but my `sed -i` had rewritten its CRLF line endings as LF,
so git reported the file modified. Restored from HEAD with `git checkout` before committing, so this unit
does not touch that file; the case tests re-run green afterwards (16 passed). "Same content" and
"byte-identical" are different claims, and I made the stronger one.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at432-off-domain-case-step.md`, commit 3ca11d1; ledger AT-432 open → fixed; AT-441 filed)
