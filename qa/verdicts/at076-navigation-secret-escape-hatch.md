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
