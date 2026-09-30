# AT-113 crawl completion — cycle 3 stall diagnosis

Agent Debug Progress:
- [x] Phase 1: Failure capture
- [x] Phase 2: Root-cause diagnosis
- [ ] Phase 3: Contained recovery (recommendation only; not authorized in this diagnosis)
- [ ] Phase 4: Recovery introspection (not performed)

Scope: maker stall diagnosis, Phases 1–2 only. Source and contracts remain unchanged. This report is not a checker verdict or task PASS. The full goal remains active; T-165 remains pending.

## Phase 1 — Failure capture

- Objective: make bounded crawl completion truthful and enforce each fired bound before any further crawl action, including synthetic typing.
- Frozen cycle-3 source: `085537cd549a6aa0ce522aee3d9a6486f2874c83`; read-only `git -C .worktrees/at113-crawl-completion rev-parse HEAD` returned that exact commit.
- Decisive independent headed witness: `.work/check-at113-c3-a/typing_probe.py`; execution session 43797 exited 1 as reported by the owning checker. This diagnosis did not launch or rerun that process.
- Actual persisted artifact independently read: `.work/check-at113-c3-a/typing-data-ff1644b6/report.json`.
- Exact primary failure: `AssertionError: X4: attempted second field after max_depth bound fired`.
- Last successful meaningful step: both BFS and hybrid actually filled the first field at admitted depth 1. Its navigation led to the independently observed valid depth-2 identity `node_cdf745d037b5`; the depth-2 node was refused. Persisted crawl status was `stopped_bound`, reason `max_depth`.
- Failure sequence: after that first `FILL` / `NAVIGATED`, both strategies recorded a second `FILL`, target `#last`, name `Last name`, outcome `same_screen`. Both report flags `second_field_attempted_after_depth_refusal` and `second_field_filled_after_depth_refusal` are true. Both crawl envelopes count 3 actions/3 edges, with 2 admitted screens and 0 tool failures.
- BFS first/second fill timestamps: `2026-09-30T19:25:04.295706Z` then `2026-09-30T19:25:07.924710Z`; hybrid: `2026-09-30T19:25:18.759712Z` then `2026-09-30T19:25:22.428102Z`.
- Environment/source identity: probe asserts each loaded explore, explore_typing and explore_node file equals the frozen Git blob after CRLF-to-LF normalization; report contains their paths and hashes. Loaded typing blob SHA256: `e5ae40e17ab412b77118c527be6ea2795b88ea04302be27bdb0f8c50ec321223`.
- Owned-process cleanup: all 18 `(PID, creation)` rows report `alive: false`; no `cleanup_failure`, `ownership_failure` or `browser_close_failure` key appears. No process kill was performed by this diagnosis.
- Repeated pattern: same semantic failure under both traversal strategies; this is reproducible application behavior rather than evidence of a retry storm or a browser startup failure.

## Phase 2 — Root-cause diagnosis

Classification: **execution / product logic**, specifically incomplete propagation of a fired crawl bound into the synthetic typing loop. Not loop-design, contract ambiguity, verification-command error, transient tool failure or environment failure. Known debugger pattern: tests still failing after a fix → wrong or incomplete hypothesis; isolate the concrete failing behavior.

Evidence chain in the frozen files under `.work/check-at113-c3-a/source/src/autotester/stages/`:

1. `explore_typing.py::_type_one` lines 73–78 records the navigated fill and calls `_enqueue` for its new depth-2 node.
2. `explore_node.py::_enqueue` lines 110–113 refuses `new.depth > max_depth` and sets `rt.stop_reason = explore.stop_reason(rt) or "max_depth"`.
3. `explore.py::stop_reason` lines 48–59 already preserves fired `max_depth` and evaluates screen, action and elapsed-time limits.
4. `explore_typing.py::type_form` lines 106–139 only checks `max_actions` directly and the per-node cap; it never calls that shared stop-reason function. It proceeds through `return_to` and resumes iteration over the original form's elements, allowing the second fill despite the latched depth refusal.
5. `explore_node.py::_click_loop` lines 241–244 does use the shared bound guard. `visit_node` lines 297–299 invokes `type_form` before that click loop, so the click guard is too late to stop a subsequent typed action.

Applicable acceptance rules are explicit: `qa/contracts/explore.md:52–57` X4 says every named bound actually ends the crawl and checks occur before every action. Lines 132–134 say typing is a first-class action and X4 binds typing exactly as clicking. `qa/contracts/core-invariants.md:274–283` requires checks to exercise disagreements between enforcing call sites against the same object. Naming `max_depth` correctly in the final envelope does not satisfy stopping semantics when another fill occurs afterward.

## Smallest contained recovery recommendation — not implemented

Maker should plan an in-place change to the existing `src/autotester/stages/explore_typing.py::type_form` (frozen line 84): apply the existing shared `explore.stop_reason(rt)` guard before every eligible typed action and retain its fired reason. Also inspect the immediate post-typing path so a bound latched by `_enqueue` exits the pre-pass before restoration/replay can issue further actions. Avoid duplicating bound logic or changing X4, schemas, traversal strategies, unrelated code or enforcement paths.

Why contained/reversible: one existing behavioral entry point consumes the same existing runtime and existing bound function; Git can represent the exact narrow diff. This is a proposal, not confirmation that this alone passes all existing acceptance checks.

Required recovery gates: cycle 3 is exhausted, so the maker must record the stall and obtain Umesh's disposition for reopening/authorizing further repair; there is no implicit cycle 4. Independent, unrelated goal work can safely continue while this unit is gated; T-165 and the full goal remain pending. If further repair is authorized, obtain a fresh approved maker plan; independent checker rerun of the headed depth-refusal typing witness for BOTH strategies must show no second-field attempt after the depth refusal while retaining `STOPPED_BOUND/max_depth` and honest refusal evidence; independent wall-clock-before-next-fill coverage with an injected clock; preserve action/per-node cap behavior and existing typing safety checks; required project verification commands run with their actual exit codes. Checker must provide its own verdict before any close-out or PASS. No automatic extra fix cycle, contract weakening, or task closure is authorized by this report.

Result: diagnosis complete; recovery unimplemented. Retrying the unchanged full suite or same browser probe would spend time without changing the failure surface. The next useful action is the bounded in-place maker recovery followed by independent acceptance evidence, subject to the project's cycle/gate rules.
