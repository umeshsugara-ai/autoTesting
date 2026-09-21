# Verdict — x10b-form-typing (cycle 1)

**Checked by:** /checker (Mode A, fresh context, no builder reasoning)
**Date:** 2026-09-21
**Contract:** `qa/contracts/explore.md` (X10 as amended to X10-b, X5 typing column, X12, X6/X5 unchanged-rows, V7b) — amendment text verified against **D-029** (`docs/DECISIONS.md:460-492`): the four-condition rule in the amended X10-b matches D-029's `Result:` line **exactly** (TEST_ACCOUNT/ALLOW_WRITES + synthetic values + dev-environment target + non-destructive; any-one-violation = refusal).
**Manifest:** `qa/manifests/x10b-form-typing.md` — `Status: ready-for-check`, Fix cycle 1. DUAL CHECK: no (contract amendment is the checker's own surface; this check verifies the code against the amended criterion).
**Authorization chain verified from disk:** `qa/gates/post-login-forms.md` carries `Answered: 2026-09-21 — (b)` with the verbatim chat quote D-029 cites; `qa/gates/live-crawl-target.md` carries `Answered: 2026-09-21 — (b) Pathlynks`. D-029's `Changes-authorized` names `qa/contracts/explore.md` (X10 + X5 only) — the actual contract diff (git `e5b3f87..0e225a5`) touches X10, X5's two typing cells + its verify sentence, the no-fire list's first bullet, and appends the amendment-log entry. X1-X9, X11-X18 byte-unchanged. The amendment itself is in order.

**Fix cycle:** 1 of max 3

**Cycle checked: 1**

## What I re-ran myself (all green)

| Command | My result |
|---|---|
| `uv run pytest tests/test_explore_typing.py` | **10 passed** in 47.97s — includes the real-browser proof `test_a_real_browser_types_and_submits_the_filled_form` (real headless Chromium, ~40s of the run; the fixture's GET form carries the synthetic value in `/saved.html?displayname=…`) |
| `uv run pytest tests/test_explore.py tests/test_explore_safety.py tests/test_crawl_coverage.py` | **97 passed** in 5.19s |
| `uv run ruff check src tests scripts` | All checks passed! (exit 0) |
| `uv run autotester doctor` | **doctor: clean** (the manifest's 2 stale-generated violations are gone — MAP/SNAPSHOT were regenerated) |
| extra: `tests/test_actuator_chokepoint.py` `tests/test_browser.py` `tests/test_browser_navigation_secrets.py` | 22 passed |
| extra: `tests/test_explore_live.py` `tests/test_secrets.py` `tests/test_crawl_coverage_bounds.py` `tests/test_crawl_report.py` | 55 passed |
| extra: `tests/test_crawl_inventory_live.py` (V8, real browser) | 2 passed in 285.33s |

The manifest's pasted outputs are reproduced by my own runs; nothing was trusted.

## Code-level greps (contract verbatim)

- `run_case` in `stages/explore.py`: exactly one call site, inside `_bootstrap_login` (explore.py:110). `execute.py`/`execute.md` absent from the unit diff. **X1 intact.**
- No `playwright` import / `.page.` access anywhere in `src/autotester/stages/`. Typing composes `rt.session.fill` / `select_option` / `first_option` — the X2 actuator boundary. `first_option` added to `browser/session.py` (the door), session refactored to 298/300 lines.
- The verify grep's exception is exactly `explore_typing.py`: fill/select_option call sites exist only there (plus `execute.py`'s pre-existing step handlers, outside `explore*`). No other module imports or re-implements typing.
- `synthetic_values.py`: deterministic (sha256 of name+selector+role), no provider, no clock, no randomness; values are obvious fakes (`autotester.invalid`, `AutoTester College N`). Determinism test green.
- Default `SafetyPolicy()` keeps `synthetic_typing=False`; no shipped caller sets it True today — every existing crawl keeps X10 exactly as it was (97 regression tests + 22 chokepoint/browser + 55 live/coverage/report + V8 inventory all green, typing-off behaviour byte-unchanged).

## Per-criterion judgements

| Criterion | Judgement |
|---|---|
| X1 (E5 intact, one `run_case` site) | **MET** |
| X2 (browser/ chokepoint) | **MET** |
| X10 base (nothing typed outside X10-b) | **MET** — probe: READ_ONLY and flag-off crawls produce zero fills/selects |
| X10-b condition 1 (widening policy + explicit per-run flag) | **MET** — `typing_allowed` is the one gate; matrix test + probes |
| X10-b condition 2 (synthetic deterministic values only) | **MET** |
| X10-b condition 3 (non-production target) | **NOT MET in code** — see AT-535. The gate as built is 3-of-4 conditions |
| X10-b condition 4 (non-destructive; X6/X5 guards unchanged) | **MET** — password-named fields refused, uploads never (role filter), Delete + Log out still denied under TEST_ACCOUNT (probe), deny-list ON |
| X10-b "first-class crawl actions … counts toward max_actions **and the per-node cap**" | **HALF MET** — `max_actions` binds (test + my probe); **per-node cap does not** (AT-533) |
| X10-b "click loop still runs after the pre-pass, submit under the same X5 matrix" | **MET** — Save clicked after fill; denials intact |
| X5 matrix (unchanged rows) | **MET** |
| X6 (never-click at every policy) | **MET** |
| X12 (no provider anywhere in the stage) | **MET** |
| X7 (host re-checked after EVERY action) | **NOT MET for typed actions** — see AT-532 |
| V7b (manifest claim 6: refused typing records `DENIED_POLICY`/`policy:typing disabled`) | **NOT MET as claimed** — see AT-534 |

SCOREBOARD: 12/16 criteria met, invariants (E5 intact, X6 never-click) 2/2 hold.

## FAILURES (each defended at >80% confidence; each reproduced by my own probe, not suspected)

- **[X10-b c3] sev: medium · condition 3 (non-production RunApproval target) has no runtime enforcement — `typing_allowed` reads only the policy; nothing in the typing path ever consults the approval's `production` flag; D-029's rule is a four-condition AND and the build enforces 3 of 4 · fix direction: refuse a `synthetic_typing` crawl whose covering RunApproval is `production: true` (in `require_consent`/`run_crawl`), record the covering approval id in `crawl.json`, falsifying test: typing ON + production approval → refused/never typed · issue: AT-535**
- **[X7] sev: high · a fill or select_option that navigates off-domain (a real onchange/auto-submit) creates AND explores an off-domain node with no `OFF_DOMAIN_REFUSED` edge, no `NAVIGATION` issue, no recovery — X7 says the host is re-checked after EVERY action; `try_action` does this (explore_node.py:142-146), `_type_one` never does (no `check_destination` in explore_typing.py) — reproduced: fill→`https://evil.test/` yields a visited off-domain node, crawl reads `completed` · fix direction: re-check the host after settle in `_type_one`, refuse + recover exactly as `try_action` does; pin with a test · issue: AT-532**
- **[X10-b first-class-actions] sev: medium · typed actions ignore `per_node_action_cap` — reproduced: `per_node_action_cap=2`, typing ON → the settings node performs 4 actions (2 typed + 2 clicked); the amended sentence "counts toward max_actions and the per-node cap" is false as built (global `max_actions` does bind) · fix direction: make `type_form` consume the same per-node budget; falsifying test at cap=2 · issue: AT-533**
- **[V7b/manifest claim] sev: medium · manifest claim 6 ("a refused typing action records DENIED_POLICY with `policy:typing disabled`") does not happen: typing-refused fields are silently CLICKED by the click loop and counted as exercised by coverage; `TYPING_DISABLED` (explore_safety.py:30) has zero call sites — dead code · fix direction: either record the skip as a `policy:typing disabled` coverage reason (new closed-set member, folded into coverage.md by the checker) or correct the manifest claim and pin the click-instead behaviour with a test — maker's choice, but the claim as written is not backed · issue: AT-534**

Not charged this cycle (questions, not failures): the settings node in probe A shows a **second, unrelated click edge on `input.displayname`** after the Save navigation — an artefact of `return_to`'s back-chain on the fake (the saved page's go_back), not evidence of a second fill; worth a glance when fixing AT-533's counter sharing. Whether "search" fields should type under `READ_ONLY` (gate option (c), not chosen) remains settled — not re-litigated.

## Mode D (live browser) disposition

The unit touched `src/autotester/{schema,stages,browser}` — not a UI surface of our own app under the `qa/contracts/ui-*` definitions, so a driven check of our own UI is **not-applicable**. The maker's live-browser proof is a REAL-browser test inside `tests/test_explore_typing.py`, which I **re-ran myself** (green, real Chromium, ~48s); the V8 inventory live tests (real browser, full crawl + depth bound) also re-ran green. Independent browser evidence: `qa/evidence/browser-x18a-login-both-directions-2026-09-17-checker/` and `qa/evidence/browser-at480-489-wall-bound-and-fill-fallback-2026-09-17-checker/` cover the unchanged surfaces this unit composes with; no new UI surface was added.

LIVE-BROWSER: not-applicable (changed paths: src/autotester/schema/crawl.py, src/autotester/stages/{explore_typing,explore_safety,explore_node,synthetic_values}.py, src/autotester/browser/session.py — no UI surface; real-browser proof re-run by checker inside tests/test_explore_typing.py)

## Issues

ISSUES-WRITTEN: AT-532, AT-533, AT-534, AT-535 (all `open`, `found_by: checker-unit`)

Issues addressed per the manifest: none claimed; ledger reconciled — nothing to close.

## EXPLANATION

The four verify commands pass on my own re-run, the D-029 authorization chain is real on disk, the amendment diff touches exactly its authorized surface, and the core X10-b mechanism (gate boolean, deterministic generator, password/upload refusal, bounds-on-max_actions, click loop intact, default OFF) is genuinely built and pinned — including a real-browser proof. But the unit does not yet earn PASS: X10-b's contract sentence makes all four conditions a refusal, and condition 3 exists in no code path; X7's "re-checked after EVERY action" is false for the new action type the unit introduced, and my probe shows an off-domain node created and explored from a typed action; the per-node cap sentence is measurably false; and the manifest's V7b claim describes code that does not exist. These are fixable in one cycle — the gate seam (`require_consent`), one host re-check in `_type_one`, one shared counter, and either the missing denial record or a corrected claim. X10's hard half (nothing typed without all four conditions) held in every probe I ran; the failures are in the completeness of the guards around the new capability, not in the ban itself.

VERDICT: FAIL