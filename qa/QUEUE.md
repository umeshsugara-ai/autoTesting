# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-08T08:35Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-07T18:40Z, ~8h and 28 commits ago; everything it recorded was treated as stale and
**re-derived from disk**. Its counts were wrong by the time this sweep started (it reported
59 manifests and a cleared `fixed` backlog; actual 64 manifests, backlog had regrown to 7).

No `GRILL:` row this sweep. Check 6 found no goal-drift trigger: `qa/.regrill-due` absent, the
north star unchanged, no `missing` requirement only the human can source, no reopen-power
escalation, and no `STALLED`/`EXHAUSTED` tick without a matching `qa/debug/` report.

## Concurrency note (AT-101, respected)

The maker is building **t124-consent-gates fix cycle 2** in this same working tree. This sweep
**never ran `git stash`, `git checkout` or `git restore`** — the mistake that made a prior sweep
file AT-101 against itself. Every re-run happened against a `git archive HEAD` extract in a
scratch directory, with `PYTHONPATH` pinned so imports resolved to the copy (verified explicitly).
No file in the live tree was written except this checker's own four surfaces.

## What this sweep found

- **Bypass detection — clean.** All 28 commits since the prior sweep examined. Every commit
  touching `src/`, `scripts/` or `.claude/` carries a manifest: `f731983` (T-144), `b9fa94b` +
  `5d99520` (hook, D-019/D-020), `afddb87` (AT-107), `ef881b9` (AT-103), `fb261c5` (T-124). No
  normal-mode source change slipped through this time — the prior sweep's `c881767` complaint has
  not recurred.
- **Handshake integrity — clean across all 64 manifests.** Every `ready-for-check` manifest has a
  verdict whose `Cycle checked` equals its `Fix cycle`; every PASS verdict has a `checked-PASS`
  manifest. Two expected exceptions, neither a defect: `t124-consent-gates` sits at
  `ready-for-check` / `Fix cycle 1` against a **FAIL** verdict and the maker is mid-cycle-2 on it
  right now; `at015-at028-hook-adapter-fix` ends `STALLED (recovery applied)` against a
  stall-recovery PASS, historic and already on record.
- **Maker liveness — alive.** `qa/.last-tick` fresh (2026-09-08T03:05Z, later than the newest
  commit), `qa/.paused` absent, seven uncommitted source files under active edit.
- **Enforcement liveness — VERIFIED BY EXECUTION, and this is the first sweep that could say so.**
  Ran `.claude/hooks/lab-session-start.ps1` directly. It emits **no `[WARN]`** and injects the
  real ground truth: all 10 named ARCHITECTURE sections through `## Status`, the full 21-entry
  decision index, and D-018/D-019/D-020 in full. The empty-block regression (AT-015 → AT-097 →
  AT-106) is genuinely closed. The repo has commits; the loop spec `qa/loop.md` carries all seven
  terminal states and an uncontradicted `Human gate` line.
- **The guard tests are NOT vacuous — proven by three sabotages** in a scratch copy of the hook +
  tests (never the live `.ps1`). Reverting the filter to the template's numbered allowlist → 4 of
  7 fail; reverting the cap 150 → 100 → 3 fail; reverting `$archPath` back to the repo root → the
  path test fails. Each of the three historical regressions is independently caught. The tests
  parse the pattern, the cap **and** the path out of the live `.ps1`, so they cannot drift into
  simulating a fiction — the AT-107 lesson held.
- **The `fixed` backlog had regrown 0 → 7, and all 7 are now `verified` by re-running, not by
  reading commit messages.** AT-029/AT-097/AT-106/AT-107 verified by executing the real hook plus
  the three sabotages above. AT-098, AT-103 and AT-104 verified by sabotaging the fix in the
  scratch extract and confirming named tests fail: AT-103 both directions (the *lazy* fix —
  suppress all conflicts — fails 3 tests; the *pre-fix* rule fails the SPA test); AT-098 (collapsing
  both excepts to one blind handler fails 2 tests); AT-104 (removing `crawl_view.review_line` fails
  3, including the "not falsely warned" direction). **Nothing was reopened** — every claim held.
- **Verify baseline on clean HEAD:** `581 passed, 2 skipped`, `ruff: All checks passed!`,
  `doctor: clean`.
- **Silent-failure hunt — 2 findings** (AT-113 high, AT-114 medium), over the code PASSed since the
  prior sweep. Details below.
- **Loop-design check — 1 finding** (AT-115 medium): the AT-100 "done_check that cannot fail" shape
  recurs on two more goal tasks.
- **Contract staleness:** AT-099 still true and still open — `ui-flow-diagram.md` and `ui-sidebar.md`
  are the only two of 28 contracts with no Amendment log. No new staleness; `consent.md` was
  authored by the T-124 checker and the inbox entry is marked folded.
- **Known, tracked, not re-filed:** `qa/adapter.json`'s verify allowlist is still the original 3
  commands, though D-018 authorized widening it — that is T-126, already registered. It does mean
  this sweep, like every recent verdict, ran commands outside the allowlist.

## Top-3 recommended next units

1. **`t124-consent-gates` fix cycle 2 — AT-111 (high) + AT-112 (medium).** Already in flight; this
   is the right unit. AT-111 is the sharper one: the "a refused run leaves no trace" invariant is
   proven only on the direct `run_crawl` call that no operator uses, while both *shipped* entry
   points still create `crawl/<id>/shots/` and launch Chromium before refusing.
   **AT-110 (high) is HUMAN_GATE** — `qa/gates/at110-approval-forgery.md`, unanswered, and it is a
   security-posture call (sign approvals with a secret vs. accept tamper-evidence-not-proofing).
   Per the standing rule, **the gate must not idle the rest**: AT-111/AT-112 are buildable now and
   the maker should not wait on Umesh to proceed with them.

2. **AT-113 (high, new) — an unexplored screen is reported as a successful crawl.** This gates
   **T-145** the way AT-093 did. A screen the crawler could not return to is marked
   `ABORTED_ERROR`, files no issue, and the crawl still ends `completed` / `frontier empty` /
   `issues=0`; the status reaches the Excel sheet only, never the crawl page or the issue count,
   and the screen still enters the FlowSpec via `merge_screens` as a real screen with no actions —
   indistinguishable from a genuine leaf. Proven by probe against the real `run_crawl`. Pointing
   the explorer at the live production ERP while a partial crawl looks complete is the failure
   mode T-145 can least afford.

3. **AT-108 + AT-114 as ONE sweep of every `except` in `stages/explore*.py`** — the maker's own
   stated plan, and the right shape. AT-114 is the strongest instance: `explore_node.capture()`'s
   blind `except Exception: return None` **defeats a deliberate design decision** in
   `session.py::screenshot`, which re-raises a second consecutive failure precisely because it is
   real (AT-036). `_recover()`'s `except Exception: pass` is the third site. "The cause was
   swallowed" is a shape, not a location — patch it once, at the principle.

**Cheap and worth folding in:** AT-115 (medium) belongs to T-126, which is itself one of the two
tasks it indicts — `uv run autotester doctor` checks none of T-126's or T-150's deliverables, so
both can close green with the work undone. AT-099 (low) is two missing Amendment log headings.
