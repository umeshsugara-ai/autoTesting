# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-08T14:40Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-08T08:35Z, ~6h and 40 commits ago; everything it recorded was treated as stale and
**re-derived from disk**. Its counts were already wrong: it reported 64 manifests and a cleared
`fixed` backlog; actual **71 manifests / 71 verdicts**, and the backlog had regrown to **12**.

No `GRILL:` row this sweep. Check 6 found no goal-drift trigger: `qa/.regrill-due` absent, the
north star unchanged, no reopen-power escalation, and no `STALLED`/`EXHAUSTED` tick without a
matching `qa/debug/` report.

## Concurrency note (AT-101, respected)

No `git stash`, `git checkout` or `git restore` ran in the live tree. Every re-run and all nine
sabotages happened against a `git archive HEAD` extract in a scratch directory with its own
`.venv`. The `at125-at132-declared-but-unapplied` manifest and verdict were left untouched (its
unit checker was live when this sweep started; it PASSed at 14:28, commit `45e9a21`). Only this
checker's four surfaces were written in the live tree.

## What this sweep found

- **Bypass detection — clean.** All 40 commits since the prior sweep examined. Every commit
  touching `src/` or `scripts/` carries a manifest: `ea7e25d` (at113), `1fb89c9` (at116),
  `6e98487` (at108-at114), `bc29b34` (at120), `6c653fd` (at121-at122), `1c8c8e4` (t131),
  `c4c878a` + `d9396d4` (at125-at132). No normal-mode source change slipped through.
- **Handshake integrity — clean across all 71 manifests.** 71 manifests, 71 verdicts, every
  latest verdict `PASS` at a `Cycle checked` equal to its manifest's `Fix cycle`. The one
  exception is historic and on record: `at015-at028-hook-adapter-fix` (`STALLED (recovery
  applied)` against a stall-recovery PASS).
- **Maker liveness — alive.** `qa/.last-tick` fresh (14:26Z), `qa/.paused` absent, tree clean
  except the usual `.goal` timestamp churn.
- **Verify baseline on clean HEAD:** `623 passed, 2 skipped` (up from 581), `ruff: All checks
  passed!`, `doctor: clean`. `docs/MAP.md` re-derived by running `autotester map` in the scratch
  copy — **byte-identical** to the committed file, so it is genuinely fresh, not merely
  doctor-green.
- **The `fixed` backlog had regrown 0 → 12, and 11 are now `verified` by execution, not by
  reading commit messages.** Nine sabotages, each in the scratch extract, each breaking a
  *different named* test — none of these guard tests is vacuous:
  | Sabotage | Result |
  |---|---|
  | AT-113 drop the pre-loop `add_issue` | `test_a_node_the_crawl_cannot_return_to_files_an_issue_and_is_marked_aborted` fails |
  | AT-113 let the mid-loop failure fall through | `test_a_node_lost_mid_exploration_is_marked_aborted_not_explored` fails |
  | AT-120 make `add_issue` kind-blind again | `test_tool_failures_are_not_counted_into_the_products_issue_total` fails |
  | AT-114 restore `capture()`'s blind `except: return None` | 3 tests fail |
  | AT-122 drop `tool_failures` from the CLI line | `test_the_cli_line_reports_tool_failures_too` fails |
  | AT-121 restore `tool_failures or '—'` | `test_a_known_zero_is_printed_as_zero_not_as_unknown` fails |
  | AT-108 make `_why()` a constant | `test_a_lost_screen_reports_why_it_was_lost` fails |
  | AT-116 re-uppercase every criticality in `.goal/goal.json` (89 fields) | 2 tests in `test_goal_criticality_vocabulary.py` fail |
  | AT-133/AT-134 narrow `load_sidecar` back to `(OSError, ValueError)` + `return None` | 4 tests in `test_ingest_real_cli.py` fail |
  AT-100 verified by **executing** T-145's new `done_check`: `uv run python
  scripts/check_crawl_approval.py erp` → `FAIL no finished crawl on disk for 'erp'`, exit 1 — a
  check that can genuinely fail, unlike the `{"cmd":"true"}` it replaced.
  **NO REOPENS — every `fixed` claim held.** Ledger now **98 verified / 42 open / 1 fixed**
  (AT-135, from the unit that PASSed 12 minutes ago, left `fixed`: not independently re-run).
- **Enforcement liveness — verified by execution.** `.claude/hooks/lab-session-start.ps1` run
  directly: no `[WARN]`, full ARCHITECTURE ground truth and the decision index injected. Both
  hook families registered in `.claude/settings.json` (`SessionStart` ×2, `PreToolUse` ×3,
  `SessionEnd`). `qa/loop.md` carries the seven terminal states and an uncontradicted `Human
  gate` line. Repo has commits.
- **Gates — both open gates are accurate on disk, neither answered off-disk.**
  `at110-approval-forgery.md` is correctly `OPEN`: the only place an answer could have hidden is
  the T-124 cycle-2 verdict, and `qa/verdicts/t124-consent-gates.md:194` merely restates option 1
  as a proposal. `at052` and `at106` both carry correct `Answered:` lines. But the **second** open
  gate has no file at all → **AT-142**.
- **Contract coverage.** `ingest.md` I6–I10 are genuinely exercised (`test_ingest_persist.py`
  I6–I9 incl. the I8 *template* placeholder assertion, `test_ingest_real_cli.py` I7–I10 through
  the real CLI). `core-invariants.md` C9 is only one-third exercised → **AT-141**.
- **Contract staleness:** unchanged — `ui-flow-diagram.md` and `ui-sidebar.md` are still the only
  two of 28 contracts with no Amendment log (AT-099, open, low).
- **Silent-failure hunt** over everything PASSed since the prior sweep: no new finding. The
  remaining blind `except`s in `ingest.py:156` and `gemini_files.py:39/85` are the ones the
  contract explicitly asks for (I9 "degrade to a re-upload, never to an error"), and
  `routes_crawls.py`'s `if crawl is None: continue` cannot hide a crashed crawl because
  `run_crawl` writes the manifest *before* the browser opens (`explore.py:213`).

## The pattern this sweep was asked to judge (AT-116 → AT-120 → AT-122 → AT-125 → AT-133)

**The countermeasure is real, and the blind spot it was built for is still wide open one directory
over.** `tests/test_ingest_real_cli.py` genuinely drives the shipped entry point — `CliRunner`
against the real `autotester.cli:app`, monkeypatching only the provider factory — and it is not
vacuous (sabotage 9 above). But it is scoped to `ingest`.

Measured across the whole test suite, the *only* CLI commands any test drives are `ingest run`,
`ingest register` and `login`. **`autotester explore` and `autotester approve` — the two commands
T-145 will actually run against the live production ERP — have no test at all**, while twelve
tests call `run_crawl` directly, which is the exact entry point AT-111's checker already said "no
operator uses". `approve_cmd` is the sharper half: the *refusal* path is defended and the *grant*
path is not. Same shape as every one of the five units above. Filed as **AT-140 (high)**.

## Top-3 recommended next units

1. **AT-140 (high) — drive the shipped `explore` + `approve` commands from a test.** The single
   highest-leverage unit on the board, and it is the maker's own recurring root cause pointed at
   the one task that runs against production. A `tests/test_crawl_real_cli.py` modelled exactly on
   `test_ingest_real_cli.py`: `approve` grants a real row through the CLI; `explore` with no
   approval exits 2 and leaves no trace; `explore` with a covering approval runs against the
   `tests/crawl_fake` fixture; `--max-actions` above the grant is refused; `--merge` sends the
   FlowSpec back to DRAFT. This sweep confirmed by hand that the seam works today — so this is
   cheap to write and it converts a probe nobody will repeat into a regression gate.
   **Do this before T-145, not after.**

2. **AT-141 (medium) + AT-115 (medium) as one unit — make C9 mean what it says.** C9 forbids a
   declared control value being silently ignored, and its own Verify clause tests one of the three
   fields it governs; `grep -rn done_check tests/ src/` returns nothing. T-126 and T-150 still
   close green on `uv run autotester doctor`, which checks none of their deliverables. One test
   that asserts every task's `done_check` names something the task actually delivers closes both.

3. **AT-142 (medium) — write the ERP credential gate to disk.** Every tick stamp for three days
   has ended "HUMAN_GATES OPEN: … ERP_EMAIL/ERP_PASSWORD for T-122/T-145", and there is no
   `qa/gates/` file for it — the one gate this sweep could not check for an off-disk answer. It
   blocks a `high` and a `critical` task. Ask it once, on disk, with options.

**HUMAN_GATE, unchanged and still not to be picked by the maker:** `at110-approval-forgery.md`
(sign approvals with a secret, or accept tamper-evidence-not-proofing). It blocks nothing today
and **must not idle AT-140/141/142** — but it should be answered before T-145 runs against the
live ERP, because it decides what the consent gate is allowed to claim.

**Cheap and worth folding in:** AT-099 (low) — two missing Amendment log headings.
