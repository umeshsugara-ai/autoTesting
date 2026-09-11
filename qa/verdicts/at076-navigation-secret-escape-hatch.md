# Verdict — at076-navigation-secret-escape-hatch

**Cycle checked:** 1
**Date:** 2026-09-11
**Mode:** A (unit check), extra adversarial rigor — credential boundary (CRITICAL per CLAUDE.md)
**Contract:** qa/contracts/browser-and-secrets.md (B2, B3, B6)
**Checker:** fresh subagent, no builder context, bound to `D:/autoTesting`

## What I re-ran myself (never trusted the pasted outputs)

- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py -q`
  → **49 passed**, exit 0. Matches the manifest's claim.
- `uv run pytest -q` (full suite) → **exit 0**, one `s` (skip — the real-Chromium test, expected
  when browsers aren't installed in this env).
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**
- **Sabotage, independently reproduced** in my OWN isolated `git archive HEAD` extract
  (`C:\...\scratchpad\at076_check`, own `uv sync` venv; confirmed `autotester.__file__`
  resolves inside the extract, not the live tree):
  - Mutation 2 (removed `resolve_for_navigation`'s per-secret domain check): **exactly 2
    failures** — `test_resolve_for_navigation_refuses_a_secret_scoped_to_a_different_domain`
    and `test_goto_refuses_a_secret_scoped_to_a_different_domain_than_it_resolves_to`. Matches
    the manifest.
  - Mutation 3 (removed `goto`'s `check_destination` call): **exactly 3 failures**, including
    the two PRE-EXISTING B6 tests (`test_goto_refuses_before_touching_the_page`,
    `test_real_headless_launch_navigates_a_data_url`) plus the new defense-in-depth test.
    Matches the manifest.
  - Both mutations restored from source before I finished; live tree confirmed untouched
    (`git status --porcelain` clean on the four touched paths throughout).

## Central scrutiny — the credential boundary, character by character

`resolve_for_navigation` (secrets.py:157-196) and `goto` (session.py:133-143) were read in
full. The substitute-then-check ordering is sound, the per-secret domain check is genuine
(mutation 2 proved it live), and `check_destination` genuinely still binds
`project.allowed_domains` independent of a secret's own `domains` (mutation 3 proved it live).
`resolve_for_navigation`'s own `SecretScopeError` for "no usable host" correctly uses the
**original** `value` (still carrying the placeholder) in its message, not `result` — that one
is clean. The two-different-secrets-in-one-URL scenario (checklist item 4) is also sound:
`host_of(result)` computes the one real host the final string actually resolves to, and both
keys are checked against that same real host — there is no way for one key's scope to vouch
for a different key embedded elsewhere in the string, because the check is against the final
navigated host, not per-key.

**But item 3 of the adversarial checklist ("could an exception message anywhere in this chain
leak a raw secret value") is a genuine, reproduced finding, filed as AT-341 (severity:
critical):**

`check_destination` (session.py:61-66) raises
`NavigationRefused(f"'{url}' is outside allowed domains {project.allowed_domains}")`. In
`goto`, it is called as `check_destination(self.project, real)` (session.py:141) where `real`
is the **already-secret-resolved** value from `resolve_for_navigation` — not the placeholder.
This call happens *before* `_record()`/`redactor().scrub()` ever runs (`goto` only reaches
`_record` on the success path, line 143), so this specific message never passes through the
Redactor at all.

I reproduced this standalone in the isolated extract: a secret whose *own* `domains` permit a
host the *project's* `allowed_domains` does not resolves successfully through
`resolve_for_navigation` (correctly — that's not this method's job), and `check_destination`
then raises with the full resolved URL — including the token — verbatim in the exception
message:

```
resolve_for_navigation succeeded, real = https://partner-portal.test/login?token=SUPERSECRETTOKEN123
NavigationRefused message: 'https://partner-portal.test/login?token=SUPERSECRETTOKEN123' is outside allowed domains ['pathlynks.test']
RAW SECRET VALUE LEAKED IN EXCEPTION MESSAGE: True
```

Traced two real, unredacted persistence sinks for that message (both read directly, not
inferred):

1. `stages/execute.py:82-85` — `run_case`'s catch-all `except Exception as exc` (no
   `NavigationRefused`-specific handling) stores `error=f"{type(exc).__name__}: {exc}"` into
   `RawResult`, and `store/project_store.py:150-151 save_result` → `write_json(run_dir/
   <case_id>.json, result)` — no redactor call anywhere in that path.
2. `stages/explore_node.py:119-120` and `:128-130` — both catch `NavigationRefused` and pass
   `str(exc)` straight into `record_edge()`/`add_issue()`, persisted via
   `store/crawl_store.py:66-73 add_edge`/`add_crawl_issue` → `append_jsonl`, again with no
   redaction anywhere in that path.

This is a **regression introduced by this unit**: before AT-076, `goto()` never resolved
secrets at all, so `check_destination` could only ever see a literal (non-secret) URL in its
message. Wiring `resolve_for_navigation` ahead of `check_destination` in the same call chain —
into a function whose own error message embeds the URL verbatim — reopened exactly the
boundary B4 exists to hold ("Redactor... masks every secret value in logs and artifacts"; this
path bypasses the Redactor entirely). The manifest's "evidence is clean" claim (`## Live
browser evidence` / point 2 of its own narrative) verified only that `_record` scrubs the
success-path evidence; it never traced `check_destination`'s own exception message on the
failure path. No test in `test_browser_navigation_secrets.py` or `test_secrets.py` inspects
`str(exc)` — `test_goto_still_refuses_a_resolved_destination_outside_project_domains` only
asserts `pytest.raises(NavigationRefused)`, and its chosen value (`https://evil.test/steal`)
doesn't read like a secret, so even eyeballing the test wouldn't have surfaced this.

Filed as **AT-341** (severity: critical) in `qa/issues.jsonl` with full evidence and a fix
direction (raise with the already-computed `host` rather than the full `url`, or scrub the
message through `secrets.redactor()` before it leaves `goto`; also scrub `RawResult.error`/
`CrawlIssue.detail`/`ScreenEdge.reason` generically before persistence, since a raw exception
string reaching those sinks is a structural gap this unit exposed, not one it created from
nothing).

## Contract criteria judged (B2, B3, B6)

- **B2** (`resolve`/placeholder discipline) — untouched by this unit, still covered by its own
  tests. Not scoped to `resolve_for_navigation` in the letter of B2, but AT-341 violates the
  same underlying principle B2 exists to state ("never stored, logged, or returned to a caller
  that persists it").
- **B3** (domain scoping enforced, not advisory) — **met** for the resolution path itself
  (mutations 2 and 3 both proved the gates load-bearing), but the exception path this unit
  wired up leaks the very value B3 is scoping.
- **B6** (bounded navigation, refuses outside `allowed_domains`) — **met** functionally
  (`check_destination` still refuses correctly, proven live), but its refusal now carries the
  secret it was refusing, in cleartext, to disk.

Given B4 (evidence is clean) is the depended-on invariant this whole contract exists to
protect (`core-invariants.md` C5, named explicitly in this contract's header), and AT-341 is a
reproduced, on-disk, cleartext-secret-persistence defect introduced by this unit, I am not
crediting B3/B6 as fully evidenced-clean — a criterion "met" in its narrow letter while
actively leaking the thing it protects is not something this unit earns a PASS on.

## Live-browser applicability

Not UI-touching in the route/template sense (browser-session internals + tests only, no
template/route changed). Exercised through the same `FakePage`-backed unit-test pattern the
pre-existing `fill()`/`goto()` tests already use — consistent with this project's own
established instrument for this layer, not a gap. `test_real_headless_launch_navigates_a_data_url`
(real Chromium, skipped when unavailable — it was skipped in my run too) already covers the
real-browser path for `check_destination`, which this unit does not change.

## Verdict block

```
VERDICT: FAIL
SCOREBOARD: 2/3 criteria met, 0/1 invariants hold
FAILURES (if any):
- [B4/core-invariants C5] sev: critical · goto()'s check_destination raises NavigationRefused
  with the fully-resolved (secret-bearing) URL embedded verbatim in its message when a
  secret-bearing navigate target is refused for being outside project.allowed_domains; this
  message is never scrubbed and is persisted unredacted via execute.py's RawResult.error
  (run_dir/<case_id>.json) and via explore_node.py's record_edge/add_issue (crawl_edges/
  crawl_issues jsonl) · fix direction: raise with the already-computed host only (never the
  full url) in check_destination, or scrub every exception string through
  secrets.redactor() before it leaves goto()/reaches these persistence sinks · issue: AT-341
LIVE-BROWSER: not-applicable (src/autotester/browser/secrets.py, src/autotester/browser/session.py,
  tests/test_secrets.py, tests/test_browser_navigation_secrets.py — browser-session internals,
  no route/template changed; FakePage-backed tests are this project's established instrument
  for this layer, matching the pre-existing fill()/goto() test pattern)
ISSUES-WRITTEN: AT-341
EXPLANATION: All four verify commands re-run clean (49/49, full suite exit 0, ruff clean,
  doctor clean), and both sabotage mutations reproduced independently in an isolated extract
  with exactly the predicted failure sets — the resolution-order and domain-scoping logic
  itself is sound and genuinely load-bearing. But the unit wires a newly-secret-aware
  resolution path into an existing, unchanged check_destination whose own exception message
  was never audited for what it now carries — and it carries the raw secret verbatim,
  unredacted, into two on-disk artifact sinks. That is exactly the credential-boundary defect
  this contract's B4/C5 exist to prevent, reproduced with a live token, not merely suspected.
```

## Cycle 2

**Date:** 2026-09-11
**Mode:** A (unit check), cycle 2, EXTRA adversarial rigor — credential boundary (CRITICAL per
CLAUDE.md), cycle 1 already FAILed on exactly this boundary (AT-341). Fresh checker instance, no
access to cycle-1's or the maker's reasoning — this section is built from the manifest, the
ledger, and the code itself, read again from zero.

### AT-341's four named points — each independently confirmed genuine, not just claimed

Read the current source directly, then independently re-derived each:

1. **`check_destination` no longer embeds `url`.** `src/autotester/browser/session.py:61-71` —
   the refusal message is now built only from `host` (already extracted via `host_of`) or the
   literal string `"an unparseable destination"`; `url` itself never appears in the f-string.
   Confirmed by reading the function body, not by trusting the docstring's AT-341 comment.
2. **`execute.py::_result` scrubs `error`/`hitl_prompt`.** `src/autotester/stages/execute.py:98-109`
   — `redactor = session.secrets.redactor()` then `redactor.scrub(error) if error else error` and
   the same for `hitl_prompt`, before either reaches `RawResult`.
3. **`explore_node.py`'s `add_issue`/`record_edge` scrub `detail`/`reason`.**
   `src/autotester/stages/explore_node.py:49-56` (`detail=rt.session.secrets.redactor().scrub(detail)`)
   and `:63-70` (`scrubbed = rt.session.secrets.redactor().scrub(reason) if reason else reason`).
4. **Regression tests genuinely assert the secret's ABSENCE, not merely that an exception was
   raised.** Read all four test bodies in full:
   - `tests/test_browser.py::test_refusal_message_never_embeds_the_raw_destination` — asserts a
     distinctive marker string is `not in str(excinfo.value)` while the host is.
   - `tests/test_browser_navigation_secrets.py::test_goto_still_refuses_a_resolved_destination_outside_project_domains`
     — asserts `"SUPERSECRETTOKEN123" not in str(excinfo.value)` AND not in the evidence path
     string, with a token-bearing value.
   - `tests/test_execute.py::test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting`
     — a non-`NavigationRefused` exception; asserts `"hunter2" not in result.error` and
     `"REDACTED" in result.error`.
   - `tests/test_explore_error_causes.py::test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting`
     / `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting` — assert
     `"zorro-battery-42" not in saved.detail` / `saved.reason` and `"REDACTED" in` each.
   None of these degrades to `pytest.raises(...)` alone. All four genuinely test the property
   named.

### Independent re-run (own isolated extract, never the live tree)

`git archive HEAD | tar -x` into a fresh scratch dir, own `uv sync` venv, confirmed
`autotester.__file__` resolved inside the extract (not `D:\autoTesting`). Baseline first —
asserted green before trusting any mutation (C7): 69 passed, exit 0.

- **Mutation A** — reverted `check_destination` to embed `f"'{url}' is outside allowed domains
  ..."` again (anchor matched exactly once, file changed, confirmed by diff before running).
  Result: **exactly the 2 predicted failures**
  (`test_refusal_message_never_embeds_the_raw_destination`,
  `test_goto_still_refuses_a_resolved_destination_outside_project_domains`), with
  `SUPERSECRETTOKEN123` visible verbatim in the assertion diff.
- **Mutation B** — reverted `execute.py::_result` to store `error=error, hitl_prompt=hitl_prompt`
  unscrubbed. Result: **exactly the 1 predicted failure**
  (`test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting`), `hunter2`
  visible verbatim.
- **Mutation C** (beyond the dispatch's "B or C" minimum, ran both for full coverage of point 3)
  — reverted both `add_issue`'s and `record_edge`'s scrub calls in `explore_node.py`. Result:
  **exactly the 2 predicted failures**
  (`test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting`,
  `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting`), `zorro-battery-42`
  visible verbatim.

All three mutations restored from the untouched live-tree source files immediately after each
was confirmed (diffed byte-identical against the live tree post-restore). `git status
--porcelain` on the live tree's four touched files stayed clean throughout — nothing in
`D:\autoTesting` was ever modified by this check.

### Adversarial fifth-sink hunt — found one, live and reproduced

Traced every remaining caller of `check_destination` and every `session.goto`/`explore.*.goto`
call site, not just the ones AT-341 already named:

- `stages/explore_node.py:110,130-134` (`_perform`, `try_action`'s post-action re-check) — both
  go through `record_edge`/`add_issue`, already scrubbed (point 3 above). Clean.
- `stages/explore_return.py:53,123` (`return_to`, `_recover`) — their generic
  `except Exception as exc: rt.return_error = f"{type(exc).__name__}: {exc}"` is NOT itself
  scrubbed, but `why_lost(rt)` (the only reader of `return_error`) is always folded into an
  `add_issue(...)` call at its call sites in `explore_node.py:214-216,236-239`, and `add_issue`
  scrubs `detail` unconditionally. Clean by construction, one hop later.
- `stages/manual_login.py:42` and `stages/explore_node.py:110`'s link navigation — targets are
  `project.base_url` or a same-page `href`, neither plausibly `{{SECRET:KEY}}`-shaped in normal
  use, and even if one were, `manual_login` reads no `SecretRef` at all (`strict=False`, ML1) so
  `PLACEHOLDER_RE` would never match a resolvable key there. No UI route renders a stack trace or
  raw error to a human screen (checked `ui/` — errors surfaced there go through the same
  `RawResult`/`Crawl` artifacts, not a separate rendering path).
- **`stages/explore.py:125-143` (`_already_past_login`) and `:146-172` (`_seed`) — a live,
  reproduced gap, filed as AT-350 (severity: critical).** `_already_past_login`'s `login_url`
  parameter is `login_step.target` — the human-authored login Case's own NAVIGATE step target,
  which is *exactly* the "a project's own login URL held as one `.env` value" scenario this
  unit's own manifest names as the motivating case for `resolve_for_navigation`. Both functions'
  `except Exception as exc:` clauses (lines 140-141 and 163-164) catch anything `goto()` can
  raise other than `NavigationRefused` — including a real Playwright `TimeoutError`/`net::` error,
  which characteristically embeds the destination URL verbatim in its own message — and store it
  unscrubbed into `rt.login_precheck_error` / `rt.seed_error`. Both fold into `rt.stop_reason`
  (`explore.py:190-197,293,296`), which `_finish` (`explore.py:214-230`) writes straight into
  `Crawl.stop_reason` via `store.save_crawl` → `crawl_store.py:28-29 write_json`, with **zero
  redaction anywhere in that path** — the identical unredacted-persistence shape AT-341 was filed
  for, at a call site neither the cycle-1 nor cycle-2 fix traced.
  **Reproduced** with a standalone script against the live tree (`.work/`, gitignored, not
  committed): a `FakePage.goto()` raising `RuntimeError("net::ERR_CONNECTION_RESET at " + url)` —
  mirroring real Playwright's own message shape — called through
  `explore._already_past_login(rt, "{{SECRET:PATHLYNKS_LOGIN_URL}}")` with the key resolving to
  `https://app.pathlynks.test/login?token=SUPERSECRETTOKEN999` produced
  `rt.login_precheck_error == "RuntimeError: net::ERR_CONNECTION_RESET at
  https://app.pathlynks.test/login?token=SUPERSECRETTOKEN999"` — the token present verbatim.
  This is the same regression class as AT-341 (before AT-076, `goto()` never resolved secrets, so
  a login-precheck exception here could never have carried one), not a pre-existing, unrelated
  gap — it is in scope for this unit's own credential-boundary responsibility, not a "different,
  untraced sink" the manifest's disclaimer can wave off, because it is caused by the exact change
  this unit made. `_seed`'s equivalent path (`rt.project.base_url`) is lower-probability in
  practice (base_url is typically a plain URL, not declared as a `SecretRef` target) but has no
  structural guard against it either, and is named in AT-350 alongside it.

### Contract criteria judged (B2, B3, B6) + core-invariants C5

- **B2** — still untouched by this unit, unaffected either direction.
- **B3** (domain scoping enforced) — met; both the resolution-order logic and
  `check_destination`'s binding are genuinely load-bearing (mutations A/B/C all proved it live).
- **B6** (bounded navigation) — met functionally, and its own refusal message is now clean
  (mutation A proved this).
- **B4/C5 (evidence is clean)** — the three sinks AT-341 named are now genuinely closed. But a
  fourth, sibling sink in the same regression (`explore.py`'s login-precheck/seed) still leaks a
  resolved secret to disk under a realistic failure (a real browser navigation error, not a
  contrived one) that this unit's own manifest scenario — a login URL held as a secret — makes
  directly applicable. The invariant this whole contract exists to hold is not yet fully closed.

### Verdict block

```
VERDICT: FAIL
SCOREBOARD: 3/3 criteria met on their narrow letter (B2 n/a, B3, B6), 0/1 invariants hold (B4/C5)
FAILURES (if any):
- [B4/core-invariants C5] sev: critical · explore.py's _already_past_login (goto(login_step.target))
  and _seed (goto(project.base_url)) catch any non-NavigationRefused exception from goto() into
  rt.login_precheck_error / rt.seed_error without scrubbing; both fold into Crawl.stop_reason
  (explore.py:190-197,293,296) which _finish persists unredacted via store.save_crawl
  (crawl_store.py:28-29) — reproduced live: a Playwright-shaped net:: error on a secret-bearing
  login-case NAVIGATE target leaks the resolved token verbatim into rt.login_precheck_error ·
  fix direction: scrub rt.login_precheck_error/rt.seed_error (or, better, scrub crawl.stop_reason
  once at the single write site in _finish()) through session.secrets.redactor() before
  persistence, with a regression test asserting the secret's absence from the persisted
  Crawl.stop_reason for a non-NavigationRefused goto() failure · issue: AT-350
LIVE-BROWSER: not-applicable (src/autotester/browser/session.py, src/autotester/browser/secrets.py,
  src/autotester/stages/execute.py, src/autotester/stages/explore_node.py — browser-session
  internals and non-UI stage code, no route/template changed; FakePage-backed unit tests and a
  standalone reproduction script are the established instrument for this layer, consistent with
  cycle 1)
ISSUES-WRITTEN: AT-350 (new, critical); AT-341 flipped open -> fixed (its three named sinks are
  genuinely closed, confirmed by source read + 3 independent mutation kills)
EXPLANATION: All four of AT-341's named points are genuinely fixed — read fresh from the current
  source (not trusted from the manifest's narrative) and independently re-broken one at a time in
  an isolated git-archive extract, each producing exactly its predicted failure set with the live
  tree confirmed untouched throughout. All four verify commands re-run clean (69/69, full suite
  exit 0, ruff clean, doctor clean). But an adversarial hunt for a fifth sink — required by this
  dispatch given the credential boundary's criticality and cycle 1's prior FAIL on exactly this
  class — found one: explore.py's login-precheck and seed navigation share goto()'s new
  secret-resolution capability but were never brought into the same scrub discipline, and the
  motivating scenario for AT-076 itself (a login URL held as a secret) makes this call site, not
  a hypothetical one. Reproduced with a live token via a standalone script mimicking a real
  Playwright error message shape. This is the same regression class as AT-341, introduced by the
  same unit, at a call site the fix did not trace — not evidence the fixed sinks are wrong, but
  evidence the credential boundary (B4/C5) is not yet fully closed for this unit.
```

## Cycle 3 — LAST ALLOWED CYCLE, extra adversarial rigor

**Date:** 2026-09-11
**Mode:** A (unit check), cycle 3, EXTRA adversarial rigor — credential boundary CRITICAL,
FAILed twice already (AT-341 cycle 1, AT-350 cycle 2). If this FAILs, the unit goes STALLED.
Fresh checker instance, no access to any prior checker's or the maker's reasoning — cycle 1 and
cycle 2 verdicts and the ledger read fresh from disk, the code re-read from zero.

### AT-350's fix confirmed genuine, not just claimed

Read the current source directly (not trusted from the manifest's narrative):

1. **`src/autotester/browser/secrets.py:226-230`** — new `SecretStore.scrub_optional(text)`:
   `return self.redactor().scrub(text) if text else text`. A shared one-liner, correctly
   passes `None`/empty text through unchanged.
2. **`src/autotester/stages/explore.py::_finish` (line 217)** — `"stop_reason":
   rt.session.secrets.scrub_optional(rt.stop_reason),  # AT-350` — scrubbed at the single write
   site, exactly the "better" structural approach the cycle-2 verdict's `expected` field named
   (covers `login_precheck_error`, `seed_error`, and any future source of `stop_reason` by
   construction, not by enumerating call sites).
3. **`src/autotester/stages/execute.py::_result` (lines 105-106)** and
   **`src/autotester/stages/explore_node.py::add_issue`/`record_edge` (lines 54, 68)** — cycle-2's
   own hand-written scrub calls now route through the same shared `scrub_optional` helper (DRY
   cleanup, no behavior change — confirmed by reading all three call sites).

### Independent re-run, own isolated extract, never the live tree

`git archive HEAD | tar -x` into a fresh scratch dir (`C:\...\scratchpad\at076_check3`), own
`uv sync` venv, confirmed `autotester.__file__` resolves inside the extract (not `D:\autoTesting`).
Confirmed `tests/test_explore_secret_scrubbing.py` is tracked as of HEAD (`git ls-files` — no
manual copy needed, contrary to what the manifest's cycle-3 sabotage section implied might be
necessary; commit `656f7f8` already includes it).

**Baseline asserted green (C7) before trusting any mutation:** the seven touched/relevant test
files (`test_browser.py test_browser_navigation_secrets.py test_secrets.py test_execute.py
test_explore_error_causes.py test_explore_secret_scrubbing.py test_explore.py`) — 89 passed, exit 0.

- **Mutation D — reverted `_finish`'s `scrub_optional` call** (anchor
  `"stop_reason": rt.session.secrets.scrub_optional(rt.stop_reason),  # AT-350` matched exactly
  once; diffed to confirm the file changed before running): **exactly the 1 predicted test
  failed** — `test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl` — with
  `zorro-battery-42` visible verbatim in the assertion diff (`'zorro-battery-42' is contained
  here: pp.test/?t=zorro-battery-42`). Attribution confirmed by test name, not just exit code.
- **Restored from the saved original, re-confirmed green** (`test_explore_secret_scrubbing.py`
  alone, 3 passed) before proceeding — the baseline-before-mutation discipline applied to the
  restore too, not only the first mutation.
- **Mutation E — made the shared `SecretStore.scrub_optional` a no-op** (`return text` in place
  of `return self.redactor().scrub(text) if text else text`; anchor matched exactly once,
  diffed to confirm): **exactly the 4 predicted tests failed across three files** —
  `test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting` (execute.py),
  `test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting` and
  `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting` (explore_node.py), and
  `test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl` (explore.py) —
  proving the DRY refactor genuinely wires every caller through the shared helper, not just the
  ones it was written against.
- Both mutations restored from saved originals; **live tree (`D:\autoTesting`) confirmed
  untouched** — `git status --porcelain` on the four touched paths stayed clean throughout this
  entire check.

**One environment artifact surfaced and set aside, not charged to this unit:** running the FULL
`uv run pytest -q` inside the isolated extract (rather than the targeted file list) produced one
failure — `test_ui_sources.py::test_uploaded_recordings_are_gitignored`, which shells out to
`git check-ignore` and fails with `fatal: not a git repository` because a `git archive` extract
has no `.git` directory. This is a pre-existing property of the isolation methodology itself (the
test existed unchanged at both the cycle-1 and cycle-2 commits), not something cycle 3 touched or
regressed, and has nothing to do with the credential boundary. Re-running the actual required
verify commands in their proper environment — the live tree — settles it cleanly (next section).

### Verify commands re-run myself, in the live tree (the correct environment for ordinary verify,
### per the default coding adapter — the isolated extract is for sabotage/mutation only)

- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_execute.py tests/test_explore_error_causes.py tests/test_explore_secret_scrubbing.py tests/test_explore.py -q`
  → **89 passed**, exit 0.
- `uv run pytest -q` (full suite, live tree) → **exit 0**, one skip (the real-Chromium test,
  expected — browsers not installed in this env).
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**

All match the manifest's claims exactly.

### Adversarial sixth-sink hunt (required by this dispatch — genuinely tried, not just confirmed)

(a) **`manual_login.py`** — read in full (`src/autotester/stages/manual_login.py`). Loads
`SecretStore.load(project, paths.env_file, strict=False)` but never calls `resolve`,
`resolve_for_navigation`, or references any `SecretRef` value — `session.goto(project.base_url)`
navigates to the project's own configured base URL, not a placeholder. No path for a resolved
secret to reach an exception message here. **`cli_video.py`** — grepped the whole `src/` tree for
`goto(` / `.fill(` call sites; `cli_video.py` performs no browser navigation of its own (it drives
video/recording ingestion, not live navigation). No other stage calls `session.goto` outside
`execute.py` (already scrubbed via `_result`), `explore.py` (already scrubbed via `_finish`), and
`explore_node.py`'s `_perform`/`try_action` (already scrubbed via `record_edge`/`add_issue`, and
its `except NavigationRefused`/`except Exception` handlers both route through those, confirmed by
re-reading `explore_node.py:117-139`). No new sink found.

(b) **`scrub_optional`/`Redactor.scrub` correctness on adversarial inputs**, verified directly
against the live-tree source (read-only, no mutation): (i) already-partially-redacted text —
`scrub` is idempotent by construction (replacing a value that isn't present is a no-op), so
calling it twice or on text that already contains `[REDACTED]:KEY` from an earlier pass changes
nothing further; no double-redaction artifact. (ii) two different secrets embedded in one
message — `Redactor.__init__` sorts `self._values` longest-first and `scrub` **loops over every
value**, not just the first match, replacing each independently. Confirmed live:
`Redactor({'K1':'secretone','K2':'secrettwo'}).scrub('boom at secretone and also secrettwo in one
string')` → `'boom at [REDACTED]:K1 and also [REDACTED]:K2 in one string'` — both distinct secrets
masked in a single string. This directly answers checklist item (b): the scrub discipline is
structurally sound for the multi-secret case, not merely untested.

(c) **UI rendering chain re-verified end to end**, not assumed safe because persistence is now
scrubbed: `src/autotester/ui/crawl_view.py:42,51` and `src/autotester/ui/routes_crawls.py:112` and
`src/autotester/cli_crawl.py:107` all render `crawl.stop_reason` — read from the persisted `Crawl`
model, which is scrubbed once at `_finish` before `save_crawl` ever runs, so every reader downstream
is safe by construction. `src/autotester/ui/routes_report.py:146` renders `r.error` (`RawResult.error`)
— scrubbed at `execute.py::_result` before the `RawResult` is ever built or persisted. Both chains
traced from write site to render site; no UI surface reads an unscrubbed field.

### Contract criteria judged (B2, B3, B6) + core-invariants C5

- **B2** — untouched, unaffected either direction, still covered by its own tests.
- **B3** (domain scoping enforced) — met; cycles 1-3's combined mutation evidence (this unit's own
  resolution-order/domain-scope logic, `check_destination`'s message, and now three
  persistence-layer scrub call sites) all independently proven load-bearing.
- **B6** (bounded navigation) — met functionally and its refusal message is clean (unchanged since
  cycle 2, re-confirmed by reading `session.py:61-71` again).
- **B4/core-invariants C5 (evidence is clean)** — **now fully closed for this unit.** All four
  named sinks across three cycles (`check_destination`'s message, `execute.py::_result`,
  `explore_node.py::add_issue`/`record_edge`, `explore.py::_finish`'s `stop_reason`) are genuinely
  scrubbed, independently mutation-tested with exactly the predicted failures each time, and the
  sixth-sink hunt against `manual_login.py`/`cli_video.py`, the multi-secret scrub case, and the
  full UI render chain found nothing further. The manifest's own disclosed-gap scope ("only the
  four sinks two independent checker cycles traced and reproduced") is honestly stated and, as far
  as this cycle's adversarial search can tell, is now the complete set.

### Verdict block

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (B2, B3, B6, B4/core-invariants C5), 1/1 invariant holds
FAILURES (if any): none
LIVE-BROWSER: not-applicable (src/autotester/browser/secrets.py, src/autotester/browser/session.py,
  src/autotester/stages/explore.py, execute.py, explore_node.py — browser-session internals and
  non-UI stage code, no route/template changed; FakePage-backed unit tests and a real run_crawl
  with a monkeypatched goto are this project's established instrument for this layer, consistent
  with cycles 1-2; the UI render chain (crawl_view.py, routes_crawls.py, cli_crawl.py,
  routes_report.py) was traced read-only from write site to render site rather than driven live,
  since none of those templates/routes changed in this unit and the property being checked is
  "does the persisted value ever carry a secret", answered by the persistence-layer proof, not by
  a browser click)
ISSUES-WRITTEN: AT-350 flipped open -> fixed (three independent mutation kills: reverted the
  single-write-site scrub call, and separately neutered the shared helper — both produced exactly
  their predicted failure sets, live tree confirmed untouched throughout)
EXPLANATION: All three cycles' named defects (AT-341's three sinks, AT-350's fourth) are genuinely
  fixed, re-confirmed by reading current source from zero and by independently re-breaking two
  distinct points (the single write-site call, and the shared helper itself) in an isolated
  git-archive extract — each mutation produced exactly its predicted failure set with correct
  attribution, never a bare exit-code read. All four verify commands re-run clean in the live tree
  (89/89 on the targeted files, full suite exit 0 with one expected skip, ruff clean, doctor
  clean); the one red result seen along the way (test_uploaded_recordings_are_gitignored inside
  the isolated extract) is a pre-existing git-check-ignore environment artifact of extracting
  without a .git directory, present since before this unit and unrelated to the credential
  boundary — traced to its root cause and set aside, not charged. A genuine sixth-sink hunt (not a
  restatement of the fifth) checked manual_login.py, cli_video.py, the Redactor's handling of two
  distinct secrets in one string (confirmed both masked independently, live), and the full
  UI-render chain from persisted field to template (both stop_reason and RawResult.error trace
  back to their single scrub-before-persist write site) — and found nothing further. The
  credential boundary this contract's B4/C5 exist to hold is closed for everything this unit
  touches.
```
