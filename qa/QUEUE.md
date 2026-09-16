# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T18:14:52+05:30** — stamp from the system clock (`date`),
not typed (AT-399). Bound strictly to `D:/autoTesting`. Fifth Mode B sweep of 2026-09-16; window
since the previous stamp `2026-09-16T15:15:45+05:30` = 33 commits `e8021f4..0b73aca`. Supersedes the
15:18 queue and the maker's post-at379-stall block (AT-423 is closed checked-PASS; U14 is now folded).

**Adapter:** `qa/adapter.json` (coding). Re-run by this sweep: `uv run ruff check src tests scripts` →
"All checks passed!" · `uv run autotester doctor` → `doctor: clean`. **pytest not run**: another maker
session is mid-edit on `visual_order.js` / `tests/test_browser_visual_order.py` (at438, uncommitted),
so a whole-suite run could not certify a single instant; latest recorded suite is the maker's own
(1312 passed, 12:25Z tick) and is not certified here.

## Findings — FINDINGS: 2 (+ 3 inbox entries folded)

| Issue | Sev | What |
|---|---|---|
| **AT-447** | **high** | **Bypass.** `7d98b64 fix(AT-420)` rewrote `qa/gates/t162-contract-approval.md` with no manifest and no verdict, and AT-420 is still `open` in the ledger. The prose itself is **correct** — re-derived from `.goal/goal.json` deps: T-163…T-169 all pending behind T-162. The defect is the skipped handshake (its twin at400 had a manifest + PASS). |
| **AT-448** | medium | **Fixed backlog 97** (vs 201 verified); 66 rows dated 09-07…09-11 never re-derived since the 09-09 sweep. Not worked by this sweep — disclosed, not rounded. |

**Inbox fold-in (check 2):** three unfolded entries, all folded this sweep —
**U14** added to `qa/contracts/ui.md` (positive rendering detector: scroll-invariance floor, no new
false negative with written tie-break, contract-owned does-not-see list; scoped to later submissions so
the live at438 cycle-1 FAIL is not re-ruled) · **C10** added to `qa/contracts/core-invariants.md`
(`git commit --only`, a unit's commit carries only its paths) · Umesh's "sabb live browser mai
validate" recorded in ui.md's amendment log (already enforced by D-024/Mode D; a session-end pass not
made a criterion — no on-disk session boundary to judge).

## Checks 1–9

1. **Bypass + handshake.** Every source-bearing commit maps to a manifest + verdict (at423, at399, at410,
   at429 c1/c2, at430, at432, at433, at438). One bypass: **AT-447**. Not checked-PASS: `at015-at028`,
   `at345-346` (STALLED, historic), `at379` (STALLED 3/3, diagnosis `qa/debug/at379-…-cycle3.md` present),
   `at438-display-contents` (**another session's live unit, ready-for-check vs cycle-1 FAIL — not a gap**).
   No PASS un-closed-out: at433 PASS (ee7d8c7) is closed out by 0b73aca.
2. **Inbox** — 3 folded (above). Now fully folded.
3. **Contract staleness** — the at438 cycle-1 verdict charged U13 against the detector U13 says it does
   not cover: the moving-acceptance-line pattern, recurring. Remedied by U14, not filed separately.
4. **Enforcement liveness — LIVE.** Commits present; `qa/loop.md` present; **maker alive** (last tick
   12:37:29Z, ~2 min old at sweep start; no `qa/.paused`).
   4b. **Data boundary** — `data_boundary.py` still reports no `data_class`: that is **AT-365**, open gate, not re-filed.
5. **Goal coverage** — 55 tasks, 20 pending; T-162→T-169 (8 tasks, 5 critical) still behind one unanswered gate.
6. **Goal-drift** — none; no `qa/.regrill-due`. **No gate answered off-disk** (all commit bodies in the
   window grepped). GRILL rows carried below.
7. **Silent-failure hunt** over at430/432/433/399 diffs — clean: every new `except` renders a named
   refusal or exits 2. (Pre-existing `routes_sources.py` `except (FileNotFoundError, OSError)` → "Recording
   not found" collapses a permission error into not-found; AT-446 already covers the CLI side.)
9. **Structural erosion (signal, not verdict)** — `visual_order.js` took **4 more commits today** in this
   window (77cba2d, dbe6185, 3259b67, c687b73) plus the live uncommitted at438 edit, and sits at its
   300-line cap. Carried under **AT-402**; reinforces its GRILL row.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), 11th consecutive sweep.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js` — redesign or next patch. Carried, reinforced (4 commits in 3 h).

## HUMAN_GATE — do not build as ordinary units (verified unanswered on disk)

| Gate | Blocks |
|---|---|
| **`t162-contract-approval.md`** | T-162…T-169 (8 pending, 5 critical). Premise now corrected and re-derived TRUE. Highest leverage. |
| `at416-clip-vs-reach-direction.md` | AT-416/417/408 scroll-clip classes (U14 (c) list) |
| `commit-before-verdict.md` | protocol departure (commit before check) — recommendation A |
| `at383-loop-status-consumer.md` | AT-383 → AT-368 |
| `at365-data-class-declaration.md` | AT-365, check 4b |
| `at110-approval-forgery.md`, `erp-credentials.md`, `t135-url-pattern-data-migration.md` | various |
| `at147`, `at218`, `at253` | `Answered:` empty / pending — effectively open |

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-447 — retroactive manifest for 7d98b64 (AT-420)** | **high** and the cheapest in the repo: no new edit, just the handshake — a manifest naming the commit, checked like at400, then AT-420 `open → fixed`. Leaves the highest-leverage gate backed by a checked premise. |
| **2** | **AT-401 — `timeout=` on `scripts/flake_probe.py` `subprocess.run`** | medium, one line + falsifying test; the only behavioural flake_probe defect left. Carried from the 15:18 queue. |
| **3** | **AT-419 — doctor's 300-line cap measures only `*.py`** | medium, and now live: `visual_order.js` is at exactly 300 and still growing under at438; C2 is unenforced on the one file churning hardest. Touches the verify chain — own unit, with a falsifying edit. |

**Explicitly NOT assigned:** **AT-431** (report.html/xlsx 500 with no runs — taken by the maker this
turn) · **at438-display-contents** and AT-442…AT-445 (another session's live unit) · anything under
`.goal/`, `.codex/`, `AGENTS.md`, untracked `projects/*`.

**Terminal state: `FINDINGS: 2`** (AT-447 high, AT-448 medium; 3 inbox entries folded → U14, C10, ui.md log).
