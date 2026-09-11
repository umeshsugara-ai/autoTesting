# HUMAN_GATE — which thread next?

**Raised:** 2026-09-11T07:55+05:30 · maker
**Blocks:** the next unit only. Nothing is half-built; the working tree is clean and every unit this
session closed `checked-PASS`.

## Why this is a gate and not a maker decision

The maker's rule is to keep pulling units while the backlog is non-empty, and the backlog *is*
non-empty. But the remaining items are large, product-shaped, and mutually exclusive in practice —
choosing between them is product direction, which is explicitly the human's call, not the maker's.

The last four units were tooling built on tooling (`mutation_check.py` and its guards). That was
justified — C7 now makes the instrument mandatory, and each round found real defects — but it is
three layers deep, the newest findings all **fail closed**, and it has drifted from the north star.
Continuing it would be the maker choosing comfort over value.

## The options

| | Unit | Why it might be next |
|---|---|---|
| **A** | **T-162** — multi-source adapters (Drive, video, audio, document, email, text into one evidence path) | The largest uncovered slice of the revised goal. T-161 already accepts source *declarations* for sources nothing can ingest, so the UI promises something the pipeline cannot do. |
| **B** | **T-163** — resumable learn-or-explore orchestrator with durable per-stage checkpoints | `criticality: critical`. Its two prerequisites are now done (T-135 closed this session, T-134 earlier). The stages exist separately; nothing coordinates them or survives an interruption. |
| **C** | **AT-227** — first-paint in-page modals during BFS | The oldest open high-severity crawl stopper, and directly on T-165's completeness path. Native-dialog handling does not cover DOM modals. Smallest of the three. |
| **D** | Pause | `/maker pause "<why>"` writes `qa/.paused` and suspends auto-continue until `/maker resume`. |

**Maker's recommendation: C, then B.** AT-227 is bounded, unblocks crawl completeness that several
other units depend on, and is real user-facing behaviour rather than more instrumentation. T-163 is
the higher-value unit but is genuinely large and is the one most worth starting with a human
watching. T-162 is worth doing but its value is gated on B existing.

## Also open, separately

`qa/gates/t135-url-pattern-data-migration.md` — unanswered, and now verified accurate by a checker.
Recommendation there is unchanged: **option B, re-run Analyze on `erp`.**

## Answer

_(unanswered — append `Answered: <ISO date> — <choice> — <where>` below before acting)_
