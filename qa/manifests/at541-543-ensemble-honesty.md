# Manifest — at541-543-ensemble-honesty

**Unit:** Retro-coverage for three defect fixes that landed as BARE commits (df529f2: AT-541
REGRESSION_ANCHOR reachable; AT-542 vision_ensemble wired; a5e5b81: AT-543 bench duration
honest) — all shipped with tests but no manifest/verdict, bypassing the maker-checker pair — plus
the one NEW genuine defect those commits introduced: **AT-550, the silent ensemble shrink**.
**Contract:** `qa/contracts/video-learning.md` VL3 ("an analysis says what it is made of" —
extended here from per-chunk to per-provider coverage) · `qa/contracts/core-invariants.md` C1
(schema-first), C2 (300/50-line caps), C3 (edit in place, no new files for behaviour), C7
(independent verification, mutation-tested new tests).
**Goal task:** none (issue-driven retro-remediation + AT-550 fix).
**Fix cycle:** 1 of max 3.
**Dual check:** no.
**Issues addressed:** AT-541 (retro), AT-542 (retro), AT-543 (retro), AT-550 (new, this cycle).

## AT-550 — the silent ensemble shrink

**The defect.** `ui/routes_sources.py::analyze_source` built the full configured vision ensemble
(`vision_ensemble()`, AT-542 — may name several providers), filtered it down to
`ready = [p for p in ensemble if p.available()]`, and passed **only `ready`** into `analyze()`.
`analyze()` computed `expected = len(providers) * len(PROMPT_NAMES) * len(prep.chunks)` from
that already-shrunk list, so `VideoAnalysis.is_complete` read `True` for a 2-provider config that
lost one provider to a missing credential — a 1-model run was indistinguishable on disk from the
2-model agreement AT-542's own docstring (`schema/project.py:49`) says is "the signal itself." A
downstream reader (an issue row's `models_agreeing`/`model_labels`, a report, an F-039-style
claim) had no way to learn the ensemble had ever been anything but one model.

**The fix — honest degradation, recorded in the data.** `VideoAnalysis` gains
`requested_providers` (who was ASKED for) alongside the existing `provider_labels` (who actually
answered), and a derived `degraded_providers` property (their set difference). The route now
passes the **full** configured ensemble's labels as `requested_providers`, while still only
*calling* `ready` — the "degrade, never die" policy (AT-542) is unchanged; a single credential
still works. What changes is that the shrink is now visible on the persisted artifact instead of
disappearing at the moment `ready` was computed.

## What changed

- `src/autotester/schema/analysis.py:59-68` — `VideoAnalysis.requested_providers: list[str]`
  (new field, `Field(default_factory=list)`), docstring cites AT-550 and the exact failure mode.
- `src/autotester/schema/analysis.py:84-93` — `VideoAnalysis.degraded_providers` (new
  `@property`): `sorted(set(self.requested_providers) - set(self.provider_labels))`.
- `src/autotester/stages/adjudicate.py:253-296` (`adjudicate`) — gains keyword-only
  `requested_providers: list[str] | None = None`; the `VideoAnalysis(...)` construction now sets
  `requested_providers=sorted(set(requested_providers)) if requested_providers else labels`
  (`labels` is the existing `provider_labels` computation, captured via walrus at
  `adjudicate.py:290` to avoid a second statement under the 50-line function cap). Omitted, it
  defaults to the observed labels — every pre-existing caller's output is byte-identical.
  **Line budget:** the file sat at exactly 300 lines pre-existing (the design-rule ceiling, zero
  headroom); three existing docstrings (module header, `SEAM_WINDOW_S`, `adjudicate`'s own) were
  tightened by a combined 4 lines to pay for the new parameter/field/logic — no prose's citation
  (VL3/VL4/AT-208/AT-550) or code behaviour was removed, only reworded tighter. File is 300 lines
  after the change (`uv run autotester doctor` confirms clean).
- `src/autotester/stages/analyze_video.py:141-188` (`analyze`) — gains keyword-only
  `requested_providers: list[str] | None = None`, forwarded to `adjudicate()` as
  `requested_providers or [p.label for p in providers]` (`analyze_video.py:186-187`). A caller
  that passes the FULL requested set as `providers` itself (the CLI, `cli_video.py:250`, which
  never pre-filters by availability) needs to pass nothing new and sees no behaviour change.
- `src/autotester/ui/routes_sources.py:239-252` (`analyze_source`) — one added keyword argument:
  `requested_providers=[p.label for p in ensemble]` (line 252), `ensemble` being the FULL
  configured list computed one line above `ready`'s filter (unchanged). Comment block above it
  (`routes_sources.py:239-244`) extended with the AT-550 rationale.
- `tests/test_ensemble_honesty.py` (new file, 6 tests) — isolating coverage for the new field,
  property, and both threading points (see Capability coverage below).

## How to verify (commands + expected)

```
uv run pytest tests/test_expand.py tests/test_schema.py tests/test_analyze_video.py tests/test_adjudicate.py tests/test_ensemble_honesty.py
uv run ruff check src tests scripts
uv run autotester doctor
```
Expected: all tests pass, ruff clean, doctor clean.

## Actual outputs (real, pasted)

```
$ uv run pytest tests/test_expand.py tests/test_schema.py tests/test_analyze_video.py tests/test_adjudicate.py tests/test_ensemble_honesty.py
.............................................................            [100%]
61 passed, 1 warning in 1.60s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

Wider confirmation — the same four required files plus every other file touching this code path
(`test_adjudicate_determinism.py`, `test_analyze_cache.py`, `test_ui_sources.py`) and the new
file together:

```
$ uv run pytest tests/test_expand.py tests/test_schema.py tests/test_analyze_video.py tests/test_adjudicate.py tests/test_adjudicate_determinism.py tests/test_analyze_cache.py tests/test_ui_sources.py tests/test_ensemble_honesty.py
........................................................................ [ 87%]
..........                                                               [100%]
82 passed, 1 warning in 2.89s
```

Full repo suite, run once before the doctor/ruff line-budget trims (functional code identical
before/after those trims — only docstring wording changed in `adjudicate.py` afterward, reverified
directly above):

```
$ uv run pytest
........................................................................ [  4%]
...(elided: skip/xfail markers for browser- and credential-gated tests, as usual)...
1534 passed, 5 skipped, 32 xfailed, 1 warning in 719.14s (0:11:59)
```

## Retro-coverage — AT-541/AT-542/AT-543 (already landed, re-verified against this worktree)

These three shipped in bare commits df529f2/a5e5b81 with tests but no manifest. Re-run here as
Mode A evidence for the checker; no code changed for these three (AT-541/542/543 code is
untouched this cycle — only AT-550 above is new work).

- **AT-541 — `REGRESSION_ANCHOR` reachable.** `src/autotester/stages/expand.py:33`
  (`CLASS_DESCRIPTIONS`) and `expand.py:76` (`classes.append(CaseClass.REGRESSION_ANCHOR)` in
  `applicable_classes`) — it used to sit in `KIND_BY_CLASS` but never appear as an applicable
  class, so nothing could ever generate one. Tests: `tests/test_expand.py:70-90`
  (`test_...` asserting `REGRESSION_ANCHOR in classes`, that every anchor case has that class,
  and that `not_applicable()`/`make_steps` route correctly for it).
- **AT-542 — `vision_ensemble` wired.** `src/autotester/schema/project.py:42-70`
  (`ProviderConfig.vision_ensemble()` — splits/dedupes the comma-separated `vision` config) wired
  into both call sites: `ui/routes_sources.py:239` and `cli_video.py:248-250`. Tests:
  `tests/test_schema.py:91-107` (`test_vision_ensemble_splits_the_config_and_deduplicates`,
  `test_vision_ensemble_empty_config_falls_back_to_gemini`).
- **AT-543 — bench `oracle_human_trial` duration honest.** `src/autotester/stages/bench.py:52-72`
  — `duration_s` defaults to `None` and scores `0.0` (unmeasured), never a hardcoded literal.
  Tests: `tests/test_bench.py:67-87` (`test_oracle_human_trial_is_labeled_a_baseline_not_a_live_run`,
  `test_oracle_human_trial_never_carries_a_hardcoded_duration`).

Re-run above (`tests/test_expand.py tests/test_schema.py` in the combined command) confirms all
three still pass against this worktree's HEAD (6b0e744) plus the AT-550 change layered on top.

## Capability coverage (each new claim -> its isolating falsification)

All three mutations below were applied directly to the live worktree files (single hunk each,
confirmed unique via the editor's exact-match requirement — a no-op if the anchor were not
exactly one occurrence), `tests/test_ensemble_honesty.py` run against the mutated code, then the
exact original text restored and re-verified byte-identical (`git diff` empty for that hunk)
before the next row. Final state re-confirmed clean by the "Actual outputs" runs above, which ran
*after* all three restores.

| capability | check | falsifying edit (single hunk) | observed |
|---|---|---|---|
| `VideoAnalysis.degraded_providers` is the real set-difference, not a stub | `test_adjudicate_records_the_requested_ensemble_separately_from_who_answered` + 2 more | `schema/analysis.py:93`: `return sorted(set(self.requested_providers) - set(self.provider_labels))` → `return []` | GREEN before: `6 passed in 0.78s`. RED after: `3 failed, 3 passed` — `assert [] == ['anthropic']` |
| `adjudicate()` actually threads the caller's `requested_providers` into the artifact, not a default that ignores it | same 3 tests | `adjudicate.py:291`: `requested_providers=sorted(set(requested_providers)) if requested_providers else labels,` → `requested_providers=labels,` | GREEN before (after restore of row 1): `6 passed`. RED after: `3 failed, 3 passed` — `assert ['gemini'] == ['anthropic', 'gemini']` |
| **THE AT-550 regression itself**: the route must forward the FULL configured ensemble (`ensemble`), not just the credentialed subset (`ready`), as `requested_providers` | `test_analyze_route_records_the_shrink_when_one_configured_provider_has_no_credential` | `routes_sources.py:252`: `requested_providers=[p.label for p in ensemble]` → `requested_providers=[p.label for p in ready]` | GREEN before (after restore of row 2): `6 passed`. RED after: `1 failed, 5 passed` — `assert ['gemini'] == ['anthropic', 'gemini']` (the exact silent-shrink shape the fix exists to prevent) |

The third row is the load-bearing one: it is a route-level integration test (real `TestClient`
POST through `analyze_source`, two fake providers keyed by name with independent `.available()`)
that fails ONLY when the route itself regresses to pre-AT-550 behaviour — the other two rows
pin the schema/adjudicate plumbing the route depends on. `test_analyze_default_matches_pre_at550_behaviour_for_callers_that_say_nothing`
and `test_adjudicate_without_requested_providers_reports_no_degradation` (the other 2 of the 6)
are non-regression controls (no mutation needed — they pin the *default*, unmutated path already
exercised by every pre-existing caller and covered by the full-suite run above).

## Live browser evidence

**Not UI-touching — the change is in the analyze/record layer; the route is an unchanged thin
pass-through.** `routes_sources.py:239-252` (`analyze_source`) still returns exactly the same
responses it did before (`303` to `/product-map` on success, the same `_refusal` HTML on the same
exception types) — the only route-level change is one added keyword argument on an existing
internal call (`requested_providers=[p.label for p in ensemble]`, line 252). No new HTML, no new
response shape, no new user-visible control. The actual behaviour change — a persisted
`VideoAnalysis` that now distinguishes "requested" from "ran" — lives entirely in
`schema/analysis.py` (new field + property) and `stages/adjudicate.py` (new parameter, pure
function, no I/O). `test_analyze_route_records_the_shrink_when_one_configured_provider_has_no_credential`
and its mirror-case sibling (`test_analyze_route_records_no_degradation_when_the_full_ensemble_has_credentials`)
already exercise the route end-to-end via FastAPI's `TestClient` (a real ASGI request/response
cycle, not a bare function call) and assert on the persisted artifact — the honest substitute for
opening a browser against a route whose HTML is provably unchanged.

## Known limits (disclosed, not claimed)

- `requested_providers` is opt-in per caller. A future caller that pre-filters providers (like
  the route did) and forgets to pass it will silently get the pre-AT-550 behaviour again (no
  degradation recorded) rather than an error — this mirrors `expected`'s own existing opt-in
  shape (AT-208) and was not tightened further to avoid changing every other caller's contract
  in this cycle.
- `degraded_providers` cannot distinguish "the caller never said" from "everyone answered" — both
  read as `[]`. This is stated in the property's own docstring
  (`schema/analysis.py:84-92`) rather than fixed, because `requested_providers` itself (non-empty
  vs empty) already carries that distinction for a reader who checks both fields, and collapsing
  it into one boolean would lose it.

## Status: ready-for-check
