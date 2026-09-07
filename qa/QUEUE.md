# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-07T18:40Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-07T18:40+05:30 (= 13:10 UTC); six goal tasks closed in between, so everything the prior
sweep recorded was treated as stale and re-derived from disk. This file was itself stale and is
rewritten, not patched — see "Governance artifacts corrected" below.

No `GRILL:` row this sweep. Check 6 found no goal-drift trigger: `qa/.regrill-due` absent, north
star unchanged, no `missing` requirement that only the human can source, no reopen-power
escalation, and the one `qa/debug/` report on disk matches the one historic STALL.

## What this sweep found

- **Bypass detection** — every code-bearing commit since the prior sweep has a manifest and a
  matching-cycle PASS verdict, with one exception: **`c881767`** (`fix(explorer): AT-093 +
  AT-094/AT-095`) touched `stages/explore_safety.py`, `scripts/explore_proof.py` and two test
  files with **no manifest and no verdict** — a normal-mode fix of three checker-found issues.
  This sweep verified all three itself by re-running (below), so it is closed out here rather
  than filed as an open bypass. Worth naming anyway: a change to the guard that stops the crawler
  logging itself out of a production ERP is not "trivial work" under CLAUDE.md's normal-mode
  carve-out, and the next one like it should carry a manifest.
- **Handshake integrity** — parsed all **59** manifests against their verdicts. Every
  `ready-for-check` manifest has a verdict whose `Cycle checked` equals its `Fix cycle`; every
  PASS verdict has a `checked-PASS` manifest. One historic exception, unchanged and already on
  record: `at015-at028-hook-adapter-fix` ends `STALLED (recovery applied)` against a PASS
  (stall-recovery) verdict. No dispatch gap, no fix gap, no skipped close-out.
- **Maker liveness** — `qa/.last-tick` is fresh, `qa/.paused` absent, and the maker is provably
  working right now: the tree gained the whole T-144 (Track B5) surface *during* this sweep
  (`stages/explore_merge.py`, `stages/crawl_report.py`, `core/excel.py`, `cli_crawl.py`,
  `ui/crawl_view.py`, `ui/routes_crawls.py` + three test modules). Not asleep.
- **`fixed` backlog cleared — the headline item.** The ledger held **32 rows at `fixed`**
  (fix landed, checker verification pending) against 46 `verified`. All 32 were worked through by
  **re-running, never by reading a commit message**. Result: **30 moved to `verified`, 2 back to
  `open`**. The ledger now holds **76 verified / 24 open / 0 fixed** — the claims-outrunning-checks
  gap is gone.
  - `AT-093` (high, gated T-145) — verified by an **independent checker-authored probe**
    (`.work/checker-probe-at093.py`), not the maker's test: `deny_reason()` denies all 12
    separator-joined logout labels under **three** policies including an AT-092 disarm attempt
    (`never_click_patterns=[]`), while 8 innocent lookalikes ("Sign-in", "Backlog-Outline",
    "Re-send code") are untouched. The root-cause fix (`normalise_label` folding `-_./+|`) is real.
  - `AT-095` (low) — verified by **sabotage**: reverting `explore_node.py:94` to the 8000 ms
    default made the test fail naming `[137, 8000]`; restoring made it pass. The test has teeth.
  - `AT-094` (low) → **reopened.** Fixed in half. The row's own scope names `explore_proof.py`
    **and** `bench_trial.py`; only the first was done. `grep -rn "class _NoCacheHandler"` still
    returns two definitions. One import swap remains.
  - `AT-029` (medium) → **reopened.** See the regression below.
- **NEW FINDING — `AT-097` (high) — an authorized enforcement-path fix was silently reverted, and
  `AT-029` regressed with it.** `docs/DECISIONS.md` D-010 (ACTIVE, `Approved-by: Umesh`) records
  raising the session-start hook's ARCHITECTURE cap to 150 lines. **The disk says 100.** Bisecting
  the file's whole history: `5f83bdb`=100 → `f9e3456`=150 (the authorized fix) → **`051303e`=100**.
  `051303e` is D-013, a *"byte-identical to the AIOS template"* sync claiming *"behaviour otherwise
  unchanged"*. It was not: it reverted D-010's cap **and** AT-015's broadened section filter, with
  no `Supersedes:` line. The filter is back to matching **numbered** headings
  (`^## (1|2|3|6)[\.\s]`) while `docs/ARCHITECTURE.md` uses **unnumbered** ones. I executed the
  filter block from the file on disk against the real `ARCHITECTURE.md`: **it keeps 1 line** — the
  title — and stops. **Every session since 2026-09-05 has been injected an effectively empty
  ARCHITECTURE ground-truth block. AT-015's original bug is fully regressed, in the hook that is
  supposed to make the Lab Protocol survive forgetting.** The generalisable risk: any future
  "sync to the AIOS template" can silently revert any locally authorized change.
- **NEW FINDING — `AT-098` (medium), silent-failure hunt.** Over the code PASSed since the prior
  sweep (`explore.py`, `explore_node.py`, `explore_safety.py`, `crawl_store.py`, `crawl.py`,
  `explore_proof.py`): `stages/explore.py:93-98` `_seed` does `except Exception: return None`
  without binding the exception, so a crawl that cannot start collapses every cause into the one
  string `"could not open base_url"`. Detection is not lost (the crawl aborts and says so) but the
  diagnosis is — and a `NavigationRefused`, the **X7 security refusal**, is indistinguishable from
  a DNS failure. That lands squarely on T-145, the live logged-in ERP crawl. Deliberately **not**
  flagged: `explore_node.capture`'s swallow, which the contract documents as B7 "never fatal".
- **NEW FINDING — `AT-100` (medium) — a `done_check` that cannot fail.** `.goal/goal.json` T-145
  (live logged-in ERP crawl, `user_value: high`) carries `done_check: {"cmd": "true"}`. That is
  check 4's third loop-design question ("can it run a wrong answer to completion") answering
  **yes**. Recorded as already-being-addressed — **D-018 authorising its replacement is being
  appended this turn**, so no duplicate work is queued. One thing D-018 does *not* cover, left open
  on the row: T-145 is `criticality: low` while T-122 and T-144 are `critical`, yet T-145 is the
  task that drives a real browser against a real logged-in production ERP.
- **NEW FINDING — `AT-099` (low)** — `qa/contracts/ui-flow-diagram.md` and `ui-sidebar.md` still
  lack the mandated Amendment log heading (0 of 27 contracts vs ≥1 for the other 25). AT-043 fixed
  only the three contracts it happened to name.
- **NEW FINDING — `AT-101` (low), filed against this sweep itself.** To bisect a red `doctor`
  I ran `git stash -u` + `git checkout` six times **in a live shared working tree while the maker
  was mid-flight on T-144**. Everything was recovered (`git stash list` empty, HEAD back on
  `bfd1a34`, all T-144 files present; `docs/SNAPSHOT.md` is regenerable via
  `autotester snapshot`), and the red `doctor` turned out to be the maker's *normal* WIP state
  (new untracked modules make generated `docs/MAP.md` stale) — no defect, so the bisect was
  unnecessary as well as unsafe. A Mode B sweep must not mutate the working tree; `git show
  <commit>:<path>` answers the same question with no checkout, as the AT-097 bisect then did.
  Filed on disk rather than left in a transcript.
- **Ledger gap (raised in the dispatch) — investigated, no gap.** T-130/T-140/T-141 closed
  `checked-PASS` with no `docs/FEATURES.jsonl` row while T-142/T-143 produced F-033/F-034.
  `uv run autotester ledger check` reports **"ledger: every closed high-value task has a row"**,
  and it is right: the rule (`ledger/store.py:115`, L3) is scoped to `user_value: high`.
  T-130/T-140/T-141 are all `user_value: normal`; T-142/T-143 are `high`. Correct behaviour, not a
  gap. Residual worth one line: CLAUDE.md says `normal` tasks "auto-stamp `update`", and nothing
  enforces or verifies that half — it is not checked by `ledger check`.
- **Enforcement liveness** — Lab Protocol wiring present, D-000 `Approved-by: Umesh` covers it,
  repo has a real commit history, `.claude/settings.json` hook commands still use the D-012 `-File`
  form. `qa/loop.md`'s Stop line lists the seven terminal states and is not contradicted by
  `qa/adapter.json`. **But** the AT-097 finding is exactly a dead-gate-that-looks-alive: the hook
  is wired, fires, and injects nothing.
- **Goal coverage** — 36 tasks, **26 done / 10 pending**. North star unchanged. Track A/B tasks map
  onto D-014/D-015/D-016. No requirement `missing` beyond what those decisions already scope.
- **Verify commands re-run by this sweep** — `uv run pytest -q` (exit 0), `uv run ruff check src
  tests scripts`, `uv run autotester doctor`, `uv run autotester ledger check`. The doctor/ruff
  violations currently showing are the maker's in-flight T-144 files, not defects.

## Governance artifacts corrected

The prior `qa/QUEUE.md` was materially wrong on three counts, all re-derived from disk this sweep
and fixed by this rewrite:

| Claimed | Actual |
|---|---|
| 20 done / 16 pending | **26 done / 10 pending** |
| "All 29 manifests" | **59 manifests** (and 59 verdicts) |
| `qa/contracts/explore.md` "correctly does not exist yet" | **It exists** — authored by the checker in `53a828c` alongside the T-143 PASS |

## Top-3 recommended next units

1. **AT-097 + AT-029 (high) — restore the session-start ARCHITECTURE injection.** The highest-value
   item on the board: the protocol's own memory hook has been injecting one line since 2026-09-05.
   **No new human gate is needed** — D-008 already authorizes the broadened filter and D-010 the
   150-line cap, both `Approved-by: Umesh`, so this is check 4's case (ii) ("the entry exists but
   the wiring is absent"), an ordinary buildable unit. Restore **both** halves: the cap *and* a
   filter that matches this repo's **unnumbered** headings — raising the cap alone changes nothing
   while the filter matches no heading. Then append a DECISIONS entry recording why the repo copy
   legitimately diverges from the AIOS template, so the next template sync does not revert it a
   second time. Verify by executing the filter against `docs/ARCHITECTURE.md` and asserting all ten
   headings survive (the check D-010's own Result claims and that nothing re-runs today).
2. **AT-098 (medium) — propagate the seed failure's cause, before T-145 runs.** Bind the exception
   in `stages/explore.py::_seed` and put the type and message into `stop_reason`, recording
   `NavigationRefused` distinctly from a transport error. Small, well-scoped, and it is the
   difference between a diagnosable and an undiagnosable first live ERP crawl. Sweep up
   `_recover`'s bare `except: pass` (`explore_node.py:145-150`) in the same unit.
3. **Finish T-144 (Track B5), then the cheap sweep-ups.** T-144 is mid-flight in the working tree
   right now and is the last Track B unit (crawl → FlowSpec merge, coverage, report/UI); it should
   land and reach a checker before new work starts. Behind it, three low-cost closers:
   **AT-094** (one import swap in `scripts/bench_trial.py`), **AT-099** (two contracts need their
   Amendment log — checker-owned), and the `criticality: low` half of **AT-100** once D-018 lands.

T-122 and T-145 remain correctly HUMAN_GATE on Umesh entering `ERP_EMAIL`/`ERP_PASSWORD` at
`/projects/erp/env`. The backlog is not empty and not blocked: item 1 is buildable now.

Terminal state: **FINDINGS: 5** (AT-097 high · AT-098 medium · AT-100 medium · AT-099 low ·
AT-101 low), plus 2 reopens (AT-029, AT-094) and 30 `fixed` rows verified to `verified`.
