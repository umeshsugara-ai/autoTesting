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
