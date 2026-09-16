# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T15:18:00+05:30** — stamp generated from the system clock,
not typed (AT-399). Bound strictly to `D:/autoTesting`. This is the **fourth Mode B sweep of
2026-09-16**, due on the 5th-tick rule after 7 maker ticks since the 14:15 sweep. It supersedes the
14:15 queue.

**Adapter used: `qa/adapter.json` (coding)** — not the DEFAULT. Slot-1 verify re-run by this sweep,
not read: `uv run ruff check src tests scripts` → exit 0 "All checks passed!" · `uv run autotester
doctor` → **clean** · `uv run pytest -q` → see the concurrency disclosure below.

## Concurrency disclosure — read before trusting this sweep's verify line

A second maker session was live in this tree throughout the sweep, building the **AT-399 loop-status
half**. Two transient pytest reds were observed and are **not findings against anyone**:

| Observed | What it was |
|---|---|
| 15:05 — `loop_status.py:71 NameError: name 'field' is not defined` | mid-edit: `dataclasses.field` used before the import landed |
| 15:07 — `tests/test_loop_status.py::test_a_healthy_log_reports_no_anomalies` FAILED | same unit, mid-edit |
| 15:10 — `uv run pytest -q tests/test_loop_status.py` → **exit 0, 15 passed** | the maker settled it |

`git show HEAD:src/autotester/loop_status.py` does not import or use `field`; the working tree does.
So **HEAD was green the whole time** and the red lived entirely in one uncommitted, in-flight file.
This sweep **did not stage, commit, revert or touch** that file, `.goal/*`, `qa/.last-tick`, the
`at379` manifest or evidence, or any untracked `projects/*`.

**Honest limit:** because of that live edit this sweep cannot certify a whole-suite green at a single
instant. Ruff and doctor were green on every run; pytest was green except for the in-flight module,
which was green by 15:10.

## Findings — FINDINGS: 2 new · 1 closed · 1 wontfix · 1 self-dismissed

| Issue | Sev | What |
|---|---|---|
| **AT-420** | **high** | `qa/gates/t162-contract-approval.md`'s **"What is NOT blocked by this — Nothing else in the backlog depends on T-162/T-163"** is **false, and was false the day it was written.** T-164…T-169 all depend on T-163 transitively; all six are `pending`; T-165/T-167/T-169 derive `critical`, T-164/T-166/T-168 `high`. Every one carries `created: 2026-09-10T05:58:09` (commit `4add220`, 2026-09-10) — a full day **before** the gate was raised on 2026-09-11. Not rot: **never true.** |
| **AT-421** | medium | Premise-rot is **not gate-specific** (AT-415 scopes it to gates). **AT-243** asserted "Mode D has NEVER run … zero LIVE-BROWSER lines" for **7 days after that became false**. The sweep has reopen-power (`verified → open`) but no symmetric power to re-derive an **open** row and close it, so a stale open row costs nothing to keep. |

Closed / ruled this sweep: **AT-243 → `verified`** · **AT-413 → `wontfix`** · **AT-422 → `dismissed`
as a duplicate of AT-402, by the sweep that filed it** (recorded, not deleted, so the near-miss is
auditable — the same waste this sweep ruled WONTFIX on AT-413).

## The two gate premises this sweep was sent to re-derive (AT-415)

### `t162-contract-approval.md` — **ROTTEN, and worse than at365's**

| Premise | Re-derived |
|---|---|
| "Umesh already answered `next-unit-scope`: Option C (AT-227) then B (T-163)" | **TRUE** — `next-unit-scope.md` carries `Answered: 2026-09-11 — Option C`. |
| "AT-227 is now closed (`checked-PASS`, verdict `1ad5496`)" | **TRUE** — manifest is `checked-PASS`; `1ad5496` is a real commit, `qa(checker): PASS at227-first-paint-modal cycle 1`. |
| "T-162 has no contract; closest is `ingest.md`" | **TRUE** — grep for `T-162` / `multi-source` / `source.adapter` across all 28 contracts returns nothing. |
| "T-163's own declared dependency is T-162" | **TRUE but incomplete** — deps are `['T-135','T-162']`. T-135 is `done`, so benign. |
| "Blocks two `criticality: critical` tasks" | **TRUE** — T-162 and T-163 both derive `critical`. |
| **"Nothing else in the backlog depends on T-162/T-163"** | **FALSE — see AT-420.** Six more pending tasks sit behind it. |

**Why this is the worse failure.** at365's premise was true when written and went stale, so a
re-derive-on-a-timer would have caught it. This one was **never true**, so no timer would ever have
caught it — only deriving it correctly once. And it is the load-bearing sentence: the gate's own next
line is *"The maker will keep working smaller open issues … rather than idle"*, which is precisely
what has happened for five days. The urgency of the highest-leverage decision in this repo was set by
a sentence that was wrong on arrival.

### `at383-loop-status-consumer.md` — **INTACT. No rot. Every premise re-derived TRUE.**

| Premise | Re-derived |
|---|---|
| Mode B sweep check 1 lives outside the bound root | **TRUE** — it is in `C:/Users/Lenovo/.claude/skills/checker/SKILL.md`, and check 1 does read `.last-tick`'s age by hand, exactly as the gate says. |
| `docs/SNAPSHOT.md` is a trap: `doctor.py:119-129` regenerates and compares | **TRUE** — verified at `doctor.py:119-129`; a time-varying line would fire `stale-generated` on every run. |
| No `Changes-authorized:` in DECISIONS covers `qa/hooks/mc-sessionstart.ps1` | **TRUE** — `grep mc-sessionstart docs/DECISIONS.md` returns nothing. |
| "Nothing written. No hook touched, no DECISIONS entry drafted." | **TRUE** — `git status --short qa/hooks/` is empty. |
| `loop-status --strict` exists and has no caller | **TRUE** — `--strict` at `cli_loop.py:22`, consumed at `:36`; the only reference anywhere is the CLI registration `cli.py:287`. |

**Umesh can answer `at383` today on exactly the premise it states.** One caveat, not a rot: the
concurrent AT-399 unit is editing `loop_status.py` right now; if it adds a `--strict` consumer the
gate's fourth candidate changes, so re-read the gate after that unit closes.

## Checks 1–9 — what was re-derived

1. **Bypass + handshake — CLEAN.** 16 commits in the window `130c4c1..ed4107d`; every source-bearing one maps to a manifest (`at396`, `at405`, `at400`, and the live `at379`). `b177076` (untrack) and `5e9ae80` (re-track) are index-only on `tests/test_flake_probe.py`, content unchanged, both mapped to AT-407. Of 130 manifests exactly **two** are not `checked-PASS`: `at345-346-fold-coverage` (`Fix cycle 3 of 3 — exhausted; STALLED`, known) and `at379-scrollable-pane-reachability` (**live, another session's — not a gap, not reported as one**). No PASS un-closed-out, no FAIL unanswered.
2. **Inbox — CLEAN.** Every entry in `qa/feedback-inbox.md` carries a `FOLDED:` line with date and target contract. Nothing unfolded.
3. **Contract staleness — CLEAN.** 28 contracts; last amended today, `13:15:29`.
4. **Enforcement liveness — LIVE.** Repo has commits; `qa/hooks/` intact; `qa/loop.md` present and its `Stop` line lists the seven terminal states (`BACKLOG_EMPTY`, `BLOCKED`, `EXHAUSTED`, `PAUSED`, …) with a `Human gate` line that `qa/adapter.json` does not contradict (no `improve` block to conflict with). **Maker live:** last tick `15:02:03`, 9 min old at sweep time — not asleep, no `qa/.paused`.
4b. **Data boundary — VIOLATION, carried, not new.** `data_boundary.py` exits 1: `qa/adapter.json` has no `data_class`. This **is** AT-365, an open HUMAN_GATE whose own premise was corrected by AT-400 this morning. Not re-filed.
5. **Goal coverage.** 55 tasks, 35 `done` / 20 `pending`. The multi-source + orchestrator half of the north star (T-162 → T-163 → T-164…T-169, 8 pending tasks) is **entirely behind one unanswered gate** — that is AT-420's real cost.
6. **Goal-drift — none.** North star last edited `2026-09-03`; contracts amended `2026-09-16` — the contract is ahead of the goal, not behind. No `qa/.regrill-due`. Three GRILL rows carried (below). No gate answered off-disk: all seven open gates verified unanswered **on disk**.
7. **Silent-failure hunt** over code PASSed since 14:15. One standing hit, already filed: **AT-401** — `scripts/flake_probe.py:137` `subprocess.run(` with **no `timeout=`** (re-derived today, still true), and `probe()` loops it N times. Nothing new in `at396`/`at405`/`at400` (two are test-prose-only, one is a prose gate record).
9. **Structural erosion — signal already on the books.** `visual_order.js` is the only file in `src/`+`scripts/` touched by more than one commit since 2026-09-14 (**5**, against 1 for everything else). That is **AT-402**, already filed with a larger window and already carrying its GRILL row. Reported as a signal, never a verdict, and **not** a finding against the live unit.

## The prose-guard churn ruling — the maker was RIGHT to stop

Four units have now touched `scripts/flake_probe.py` and its tests (at335, at386, at396, at405) and
AT-413 would be a fifth. **Measured, not asserted:**

- `scripts/flake_probe.py` has **exactly one commit in its entire history** (`4be4503`, AT-335, 186
  lines) and **has never been modified since.**
- at386 added tests. **at396 and at405 changed no production code at all** — their own verdicts
  record changed paths as `tests/test_flake_probe.py` and `tests/test_flake_probe_runner.py`.
- The chain is a **prose-correction loop over a guard's own self-description**, each link correcting
  the previous link at a smaller scope: at335's docstring → at396 · at396's residual assertion
  messages → at405 · at405's docstring → AT-413. Severity has been at the floor (`low`) since at396.

**AT-413 → `wontfix`.** The accurate statement **already exists on disk** — the at405 manifest's
"What this does not claim" section scopes the guard correctly — so only the docstring lags, and
nothing reads it. And sweep check 9's own cited authority forbids answering an erosion signal by
growing the harness (Schmid: *"if your harness is getting more complex as the model improves, you are
most likely over-engineering"*). A fifth unit on a test guard's docstring is that.

**AT-401 is NOT the same thing and should NOT be closed with it.** It is a real behavioural defect in
production script code — an unbounded `subprocess.run` in a function designed to be looped
unattended — and it is sweep check 7's own named class ("a side effect with no timeout or rollback").
Keep it, build it small.

## AT-243 — re-derived and CLOSED

The dispatch brief said at366 made this stale. It is far staler than that. Measured today:
**76 verdict files carry a `LIVE-BROWSER:` field**, of which **19 name a real checker-owned evidence
directory** (at079-080, at227, at241, at264, at277, at339, at345-346, at355, at358, at366, at379,
business-truth, live-ui-b361a16, t100-ui-reclose, t134, t135 ×2, t160, t161), and **20
`browser-*-checker*` directories** exist under `qa/evidence/`. Mode D has run dual-checker (t135 A/B)
and three-cycle (at379 c1/c2/c3). The row's remedy — *"either those PASSes carry independent
live-browser evidence, or they are not PASSes"* — is now standing practice. **AT-243 → `verified`.**
The generalisation is filed separately as **AT-421**.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), **10th consecutive sweep**.
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js` — redesign or sixth patch. Carried, and **reinforced** by this sweep's check 9.

## HUMAN_GATE — do not build as ordinary units

| Gate | Blocks | State |
|---|---|---|
| **`t162-contract-approval.md`** | T-162, T-163 (both critical) **+ T-164…T-169** | **5 days.** Unanswered on disk. **Premise corrupt — fix AT-420 before Umesh reads it.** Highest-leverage decision in the repo. |
| **`at383-loop-status-consumer.md`** | AT-383 → AT-368 | Unanswered on disk. **Premise fully intact — answerable today, as written.** |
| `at365-data-class-declaration.md` | AT-365, and check 4b | Unanswered. Premise corrected this morning by AT-400. |
| `at110`, `at355`, `t135`, `erp-credentials` | various | Unanswered on disk. |
| `at218`, `at253`, `t136`, `at147` | various | `Answered:` present but `(pending)` / `(not yet)` — effectively open. |

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

| # | Unit | Why this one |
|---|---|---|
| **1** | **AT-420 — correct `t162-contract-approval.md`'s "What is NOT blocked" section** | **high**, and the cheapest high in the backlog: a prose correction to one gate file, no code, no verify risk. It is the only thing standing between Umesh and an informed answer on the decision that gates 8 pending tasks including 3 critical. Name the six blocked tasks and their criticality; **do not re-scope the options** — Option A's four design questions are still right. Precedent: at400 did exactly this shape for at365 and PASSed cycle 1. |
| **2** | **AT-401 — bound `flake_probe.run_once`'s subprocess with a `timeout=`** | **medium**, one-line change at `scripts/flake_probe.py:137` plus its falsifying test. The **only** remaining flake_probe item with behavioural teeth now that AT-413 is `wontfix` — and the distinction is the point: this sweep closed the prose loop and kept the real defect. Check 7's own named class. |
| **3** | **AT-419 — make doctor measure the cap that C2 actually states** | **medium**, filed by the at379 checker: `core-invariants` C2 says "no file in `src/` or `tests/`" exceeds 300 lines, but `doctor` measures a narrower set — `scripts/mutation_check.py` sits at **319** and doctor exits 0. A design rule nobody enforces is AT-218's vacuous-guard class in the enforcement layer itself. Touches the verify chain, so build it as its own unit with a falsifying edit. |

**Explicitly NOT assigned:** the AT-399 loop-status half (live in another session this turn) ·
`at379-scrollable-pane-reachability` and its issues AT-416/417/418 (live unit, another session) ·
anything under `.goal/`, `projects/`, `.codex/`, `AGENTS.md`.

**Terminal state: `FINDINGS: 2`** (2 new — AT-420 high, AT-421 medium; AT-243 closed `verified`,
AT-413 ruled `wontfix`, AT-422 self-dismissed as a duplicate of AT-402).
