# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-03T12:30+05:30 (terminal state CLEAN — 0 new findings; 7
pre-existing open issues re-verified, all still accurate, none critical/high). North star
unchanged since 458304a, `.regrill-due` absent, no reopen escalation. Bypass check clean: only
`.goal/goal.json` + `.goal/dashboard.html` + `goal.md` + `qa/.last-tick` (state files) touched
since the 10:55 sweep; every code commit (T-040, T-041, T-045, T-080) paired with a manifest and
a matching-cycle PASS verdict, all pushed. `uv run pytest -q` / `ruff check` / `autotester doctor`
all green. T-050 and T-060 remain the only pending goal tasks and both are genuinely human-gated
(T-050: needs Umesh's explicit go-ahead for a live headed Pathlynks run incl. a deliberate
wrong-password attempt; T-060: needs a Pathlynks demo video not yet supplied) — everything
downstream of them (T-065, T-070, T-090, T-100, T-110, T-120) is transitively blocked. This
refresh's top-3 are the only genuinely buildable work right now.

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| 1 | TODO | Author `qa/loop.md` (re-run `/maker init` step 3b — Stop line with the maker's seven terminal states, Human gate line agreeing with `qa/adapter.json`) | AT-011 | Loop-Doctor-lite has had nothing to check since the first sweep (2026-09-03T08:40); still absent on disk, confirmed this sweep (`ls qa/loop.md` → no such file); low effort, closes a standing liveness gap; no HUMAN_GATE needed |
| 2 | TODO | Fix `lab-session-start.ps1`'s ARCHITECTURE-section injection filter (matches "sections 1-3 + 6" against headings that are `## What it does` / `## Pipeline` / etc — zero matches, so every session gets an empty ground-truth block) | AT-015 | Re-verified this sweep: `grep "^#" docs/ARCHITECTURE.md` shows no numbered headings; the filter has matched nothing since it was written. **This is an enforcement-path file (`.claude/hooks/*`)** — per D-000 it needs a DECISIONS entry with `Approved-by: Umesh` before edit; either fix the filter or rename ARCHITECTURE.md's sections to match it. Author the D-entry first, then the fix is a same-tick build. |
| 3 | TODO | Scope + build literal Script-artifact generation for the agent fallback loop (construct a `Script` under `projects/<slug>/scripts/`, set `Case.script_ref`, once `agent_loop.run_with_fallback` gets a fix stable) | AT-026 | T-080's checker (cycle 1, 2026-09-03 12:01) filed this as its own finding: the pre-existing `Script`/`script_ref` schema surface (design-lock commit a5ffcec) was built for exactly this and T-080 doesn't use it — a defensible narrow PASS but not a full "durable script" delivery per the contract's own escape valve. Medium severity, no HUMAN_GATE required to scope it; if literal script generation is ever ruled permanently out of scope, retiring `Script`/`script_ref` from the schema would itself need human sign-off (schema removal), noted for whoever picks this up. |

Also open (lower, unchanged this sweep): AT-012 `.last-tick` timezone mix (historical lines only;
current writes already use `+0530`, cosmetic) · AT-014 `.goal/rubrics/T-050.md`, `T-110.md`,
`T-120.md` don't exist yet — per AT-014's own fix direction these are authored at each task's own
contract START, and none of the three has started, so this is not yet actionable (not promoted to
top-3) · AT-023 t020 manifest test-count off-by-one (low, cosmetic) · AT-024 `ProjectStore` O(n)
re-read on every add (low, perf, revisit at T-070 scale).

Sweep note: no reopen-power triggered — no ledger row's `fixed`/`verified` status was found
unbacked by evidence on re-derivation. Goal-coverage: all 19 `.goal/goal.json` tasks map to an
existing contract or an acknowledged HUMAN_GATE; no missing requirement surfaced. `qa/adapter.json`
unchanged (no `improve` block; evolutionary-mode checks stay inactive, as before).
