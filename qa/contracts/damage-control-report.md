# Contract — damage-control-report (one honest report, not four files a human must merge)

**Status:** **DRAFT** (authored by /checker 2026-09-28 under **D-054**, `Approved-by: Umesh`).
Goes **ACTIVE** on T-168's first checker PASS.
**Feature:** T-168 — the unified report: regression diff, API failures, workflows and change history
on one surface.
**Code:** does not exist yet (T-168 `pending`; no `damage_control` / `unified_report` module).
Depends on T-164, T-165, T-167.
**Grounding:** AT-638 — and note that **T-168 was named by no decision at all** before D-054, despite
existing in `.goal/goal.json` since 2026-09-10. That is the finding this file closes.
Cross-references: `coverage.md` V7(b)–(c) · `crawl-traversal.md` CR4/CR5 · `network-assertions.md` NA1
(ACTIVE since T-170's PASS) · `report-export.md` RE1/RE5 · `core-invariants.md` C5.

## Why it exists

This is the surface a human actually reads after a run. Every honesty guarantee the pipeline won
upstream — the reason-tagged coverage gaps, the bound-stopped crawl, the `not_visited` screens — can
be quietly destroyed by one rendering step that rounds them to "PASS". This contract exists so the
report cannot become the place where the truth is lost.

## Criteria

### DC1 — Blocked or unvisited is NEVER rendered as pass

`coverage.md` V7(b)–(c) and `crawl-traversal.md` CR5 already require honest, reason-tagged gaps.
That honesty must **survive re-rendering here**. This is a cross-reference, not a second counting
mechanism.

**Verify:** a fixture crawl that stopped on a bound with a sub-100% V7 figure, rendered through the
unified report, shows the **same** figure and the same reason breakdown as the crawl page — never
rounded to "PASS", never omitted. A `not_visited` control or screen never appears as a passed row
anywhere in the report.

### DC2 — It READS existing evidence; it does not recompute

All four data classes come from their existing owners: the regression diff (RR3), API failures
(`network-assertions.md` NA1), workflows (`report-export.md` RE1), and change history
(`crawl-traversal.md` CR4's `PersonaRevision` counts).

The report **never computes a number none of those sources already produced.** A figure invented at
render time has no owner and no test.

**Verify:** every figure on the unified report traces to one of the four named sources. No
number-computing function bypasses all four loaders.

### DC3 — "Unified" means one artifact, not four files stapled together

One invocation produces **one** report artifact — or one coherent, clearly cross-linked pair,
following `report-export.md`'s own video-link exception shape.

This criterion exists because "unified" is half the task's own name and no decision states it. Four
unrelated, unlinked files **fails** this criterion, however complete each one is individually.

**Verify:** one invocation → one artifact (or one cross-linked pair) containing all four data
classes.

### DC4 — No secret reaches the unified report [C5 + `report-export.md` RE5]

Inherited guarantee, restated here only because this is a new artifact and a new artifact is exactly
where an inherited guarantee gets forgotten.

**Verify:** `scripts/check_no_secrets.py` passes clean on the unified report artifact, run against a
project that touches real credentials.

**Known instrument caveat, stated so a unit does not over-trust this Verify:** AT-694 found
`check_no_secrets.py` is wired to *memory* — cited in criteria, rubrics and ~10 manifests — but is
referenced by **no** adapter entry, hook, or `done_check`. A unit satisfying DC4 must run it
explicitly and show the output; "the gate would have caught it" is not evidence here.

## No-fire list

- Building T-168 itself.
- The regression-diff mechanism's internals — `release-regression.md`'s job.
- The network-evidence capture mechanism's internals — `network-assertions.md`'s job, already ACTIVE.
- A PDF exporter or scheduled export — `report-export.md`'s own declined scope, unchanged here.

## Amendment log (append-only; git history is the version)

- 2026-09-28 · init · authored by /checker under D-054 from the criteria filed in
  `qa/feedback-inbox.md` (2026-09-27, `at638-remainder`). Cause: AT-638. T-168 is the starkest of the
  four — it had existed as a goal task since 2026-09-10 with **no authorizing decision and no
  contract**, so nothing could have judged it. DC4 gains a caveat not present in the filed version:
  AT-694 measured that `check_no_secrets.py` is unwired from every automated path, so a unit must run
  it and show the output rather than rely on a gate that will not fire. Additive; no filed criterion
  weakened. DRAFT until T-168's first PASS. **Changes-authorized:** this file (named by D-054). No
  enforcement-path file touched. **Links:** AT-638; AT-694; D-054; T-168.
- 2026-09-30 · routine · Depends-on line (line 8): T-155 removed, now "T-164, T-165, T-167" · why: D-059 dropped T-168's dependency on T-155 (the AI-test section is added when Track C is released) and named this line in its Changes-authorized; the maker filed the ask via `qa/feedback-inbox.md` 2026-09-30. Dependency line only; no criterion touched or weakened. **Changes-authorized:** D-059. No enforcement-path file touched. **Links:** T-168; T-155; D-059.
