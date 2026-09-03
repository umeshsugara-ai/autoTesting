# Verdict — t070-expand

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker mode:** A (unit check, fresh context, re-ran everything myself)

## What I re-ran

- `uv run pytest tests/test_expand.py -v` → `8 passed` (matches manifest)
- `uv run pytest` → `170 passed, 1 skipped in 1.64s` (171 collected — matches manifest's "171 collected")
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `wc -l docs/ARCHITECTURE.md` → `150` (≤ 150, at the cap not over)

## Criteria

- **X1 — refuses unreviewed FlowSpec, before any provider call.** Read `expand()` in
  `src/autotester/stages/expand.py:120-128`: `require_reviewed(spec)` is the literal first
  statement, before the `for flow in spec.flows` loop that is the only place `expand_flow` (and
  therefore `provider.act`) is ever called. `require_reviewed` (`stages/review.py:43-50`) raises
  `FlowSpecNotReviewed` unless `status is APPROVED`. `tests/test_expand.py::test_expand_refuses_an_unreviewed_flowspec`
  confirms this against a live `DRAFT` spec. MET.
- **X2 — happy case is the flow's own steps, zero provider calls.** `_happy_case`
  (`expand.py:82-87`) builds a `Case` directly from `flow`/`project` args with
  `steps=list(flow.steps)` — the same `Step` objects from the input flow, not a re-derived copy.
  `expand_flow` (`expand.py:102-117`) appends this case before entering the provider-calling loop,
  and the loop explicitly `continue`s past `CaseClass.HAPPY` so it is never sent to
  `provider.act`. `test_happy_case_uses_the_flows_own_steps_verbatim` asserts step-target equality
  against `LOGIN_FLOW.steps` directly while every other class is forced to decline (`not_applicable()
  * 20`), which would fail if HAPPY ever depended on the mock queue. MET.
- **X3 — deterministic input/auth detection, all 8 universal classes always included.**
  `_has_fill`/`_has_auth_field` (`expand.py:46-51`) are pure step-shape predicates — no provider
  call inside `applicable_classes` at all (confirmed by reading the whole function,
  `expand.py:54-65`). `_has_auth_field` checks `"SECRET" in s.value` on a `FILL` step, which
  matches this codebase's `{{SECRET:KEY}}` convention — cross-checked against
  `core/redact.py::PLACEHOLDER_RE = re.compile(r"\{\{SECRET:([A-Z0-9_]+)\}\}")`, whose matched
  span always contains the literal substring `SECRET`. `UNIVERSAL_CLASSES` (8 entries, matching
  X3's named list exactly) is unconditionally appended (`expand.py:64`) regardless of `_has_fill`/
  `_has_auth_field`. `test_no_fill_flow_skips_input_and_auth_classes` confirms `DOUBLE_SUBMIT`
  (a universal class) is present even when `INPUT_EMPTY`/`AUTH_WRONG_CREDS` are absent. MET.
- **X4 — a decline produces no Case, not an empty/broken one.** `_expanded_case`
  (`expand.py:90-99`): `if not expanded.steps: return None` is the first line: no `Case` object is
  constructed at all when steps is empty. `expand_flow` only appends `if case is not None`
  (`expand.py:114-116`) — never a placeholder, never a logged-but-skipped entry.
  `test_model_declining_a_class_produces_no_case_for_it` confirms `len(cases) == 1` (HAPPY only)
  when every class declines. MET.
- **X5 — prompt-level instruction against fake-real credentials, honestly scoped.**
  `prompts/expand_case_v1.md` line 12-15 explicitly instructs: never write a real-looking
  credential, invent an obviously-fake one for a wrong-password scenario, and leave a
  legitimately-needed field's `{{SECRET:KEY}}` placeholder unchanged. This is prompt text only —
  `expand.py` has no code path that inspects `ExpandedSteps.steps` values for
  credential-shaped strings, and the manifest says so plainly rather than overclaiming
  enforcement. Judged as an honest, acceptable scope boundary: any case this stage produces still
  has to pass through `execute.py`'s existing `{{SECRET:KEY}}`-resolution/domain-scoping boundary
  (`core/redact.py::assert_no_raw_secrets`) before it could ever touch a real browser, so the
  actual security boundary is unweakened even though this stage itself doesn't re-verify the
  model's output. MET (as a documented prompt-level claim, not a code-enforced one — matches its
  own no-fire list).

## Goal task's own acceptance bar (>=12 cases, >=1 per applicable class)

Verified independently, not by trusting the test: `applicable_classes(LOGIN_FLOW)` = HAPPY + 3
input classes (`_has_fill` true — LOGIN_FLOW has FILL steps) + 2 auth classes (`_has_auth_field`
true — both FILL steps carry `{{SECRET:...}}` values) + 8 universal classes = **14 classes**,
13 non-HAPPY. `test_login_flow_produces_at_least_twelve_cases` builds
`responses = [make_steps(...) for c in non_happy]` — one non-empty `ExpandedSteps` per non-happy
class, via `MockProvider(responses={"agent": responses})`, i.e. every one of the 13 non-happy
classes is answered with a real (non-declining) case. `expand_flow` therefore returns
1 (HAPPY, no provider call) + 13 (one per queued non-declining response) = **14 cases,
deterministically** — not a coincidence of how many responses happened to be queued, since the
queue length is itself derived from `applicable_classes(LOGIN_FLOW)` and every entry in it is
constructed to answer non-empty. 14 >= 12 holds by construction, and every applicable class
(all 14) is represented by exactly one case. MET.

## Scope / no-fire list

- Confirmed `expand()`/`expand_flow` never call `ProjectStore.add_case` — grepped `expand.py`,
  no `ProjectStore` import or reference.
- `Case.rubric_ref`/`script_ref` left `None` in both `_happy_case` and `_expanded_case` — confirmed
  by reading both constructors; neither field is set.
- `tests/test_expand.py` uses `MockProvider` exclusively (import at top, no other provider
  imported/used) — no live model call in the default suite.
- No merge/dedup logic added in `expand.py` beyond what `Case.compute_id` already provides —
  confirmed, `expand.py` contains no dedup/merge code.

## SCOREBOARD

5/5 criteria met (X1-X5), all invariants hold. Goal task's own >=12-cases / >=1-per-class bar
independently reverified and confirmed mathematically guaranteed by the test's own mock queue
construction, not coincidence.

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 5/5 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All five contract criteria (X1-X5) verified directly against
src/autotester/stages/expand.py, src/autotester/schema/case.py, and
src/autotester/prompts/expand_case_v1.md by tracing call order and reading the actual logic
(not trusting the manifest's characterization). The goal task's own ">=12 cases, >=1 per
applicable class" bar for the login flow was independently recomputed (14 applicable classes,
14 cases guaranteed by the test's own non-declining mock queue) rather than taken on faith.
pytest, ruff, and doctor were all re-run fresh and match the manifest's pasted output exactly.
```
