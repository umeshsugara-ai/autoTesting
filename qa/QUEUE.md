# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-08T19:05Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-08T14:40Z, ~4h25m and 15 commits ago. Everything the prior sweep recorded was treated as
stale and re-derived from disk; its closing counts were right at the time and are now wrong
(it reported 98 verified / 42 open / 1 fixed and 71 manifests — actual **126 verified / 50 open /
0 fixed** and **80 manifests / 79 verdicts**).

Docker is down; every command below ran natively under `uv`. Bare `uv run pytest` (not `-q`,
which becomes `-qq` when the harness adds its own and suppresses the count line).

## Concurrency note (AT-101, respected)

No `git stash`, `git checkout` or `git restore` ran in the live tree. All 14 sabotages and every
re-run happened in a `git archive HEAD` extract under the session scratchpad with its own `.venv`.
The `at172-at173-dead-command-shape` manifest — under a live unit checker while this sweep ran —
was **read but never written**, and no verdict file was created for it. Only this checker's four
surfaces (`qa/issues.jsonl`, `qa/QUEUE.md`, `qa/.last-sweep`, and this report) were written.

---

## Measured state

| | Claimed / prior | **Measured now** |
|---|---|---|
| Ledger | 98 verified / 42 open / 1 fixed | **126 verified / 50 open / 0 fixed** (2 high, 21 medium, 27 low open) |
| Manifests / verdicts | 71 / 71 | **80 / 79** |
| Goal tasks | 27/45 done (60%) | **30/45 done (66.7%)**, 15 pending |
| Test suite | 623 passed, 2 skipped | **700 passed, 2 skipped** |
| `ruff` / `doctor` | clean | **clean** |
| `docs/MAP.md` | fresh | **re-derived by running `autotester map` — byte-identical** |
| `docs/SNAPSHOT.md` | — | **re-derived by running `autotester snapshot` — byte-identical** |

No stale-state drift found. Both generated docs are genuinely fresh rather than merely
doctor-green, and `.goal/goal.json`'s progress matches the manifests on disk.

## Bypass detection — clean

All 15 commits since `15d646c` examined. Every commit touching `src/` or `scripts/` carries a
manifest: `f564d0d`/`f19471e` (at140), `4164547` (at147-at148), `da5940e` (at149-at150),
`2458b51` (at151-at152), `b86bf77` (at141-at115), `90e4219` (at154-at157), `62c3e65`
(at158-at160), `8dbc2d5`/`8344137`/`f90fcb3` (t132), `3b765a4` (at172-at173). `8153a46` is a
`qa/gates/` write only — a checker-owned surface, correctly no manifest.

## Handshake integrity — clean

80 manifests, 79 verdicts. The single manifest without a verdict is
`at172-at173-dead-command-shape` at `Status: ready-for-check`, whose checker crashed and wrote
nothing (`c4d42bb` records it, correctly, as not a fix cycle). That is a live dispatch, not a gap.
Every other latest verdict is `PASS` at a `Cycle checked` equal to its manifest's `Fix cycle`;
the one historic exception (`at015-at028-hook-adapter-fix`, STALLED with a matching
`qa/debug/` report) is unchanged and on record.

Maker liveness: `qa/.last-tick` fresh (22:54), `qa/.paused` absent, working tree clean.

## The `fixed` backlog — 11 → 0, cleared by execution

The backlog regrew from 1 to 11 since the prior sweep. All 11 are now `verified`, each by a
sabotage in the scratch extract under a C7-compliant harness (anchor must match **exactly once**,
the file must be re-read and shown changed, and a zero-failure result is reported
**INCONCLUSIVE**, never as "the test is vacuous"):

| Sabotage | Result |
|---|---|
| **AT-164 (high)** — `if not plan:` → `if False:` (drop the unreadable-recording refusal) | `test_the_unreadable_recording_refusal_is_not_a_green_success_line` fails |
| AT-166 — narrow the failed-cut wrap to `ZeroDivisionError` | `test_a_failed_cut_writes_no_media_json` fails, raw `CalledProcessError` escapes |
| AT-165 — `is_complete_png(png)` → `png.exists()` in the frame cache | `test_a_zero_byte_leftover_png_is_not_returned_as_evidence` fails |
| AT-165b — drop `out_png.unlink()` on a killed extract | `test_a_killed_extract_leaves_no_half_file_behind` fails |
| AT-167 — remove the negative-overlap guard | `test_a_negative_overlap_is_refused_rather_than_silently_skipping_footage` fails (DID NOT RAISE) |
| AT-163 — `PREP_COMMAND` → `autotester media prep` (the original dead group) | `test_a_stage_needing_prep_is_sent_to_a_command_that_exists` fails |
| AT-171 — `PREP_COMMAND` → `autotester ingest list` (**registered but wrong arity** — the case that came back INCONCLUSIVE for the maker's second oracle) | same test fails. The third oracle genuinely bites where the first two did not |
| AT-158 — restore token-anywhere program matching | `test_the_guard_recognises_the_shapes_it_exists_to_catch` fails on `echo pytest tests/test_x.py` |
| AT-158b — drop `\|` from `SHELL_NEUTERING` | same test fails on `pytest tests/test_x.py \| true` |
| AT-160 — delete `and not waiver_of(r)` from `offenders_in` | `test_a_waived_task_is_exempt_and_an_unwaived_one_is_not` fails |
| AT-159 — drop `"env"` from `RUNNERS` | **INCONCLUSIVE** — applied, file changed, 0 failures. Mutation strengthened per C7 → `program.startswith("python")` → `program == "python"` → **CAUGHT** (`rejected a legitimate check: 'python3 scripts/check_crawl_approval.py erp'`) |
| AT-135 — first mutation hit the `except OSError` handler → **INCONCLUSIVE**; the real fix hunk is `path.is_file()` → sabotaged to `path.exists()` → **CAUGHT** (`test_a_source_pointing_at_a_directory_gets_a_typed_refusal`) |
| AT-168 (low, documentation) — not test-guardable; verified by reading: `chunks.py:83` and `frames.py:30` now carry the corrected measurement ("both orders produced a byte-identical frame") instead of the falsified rationale |

**NO REOPENS — every `fixed` claim held.** Two INCONCLUSIVE results were correctly *not* reported
as vacuous tests; both were the sabotage being wrong, and both were caught on the second mutation.
C7's new clause did real work here.

## Contract coverage — is the new text actually exercised?

- **`video-learning.md` VL1 / VL1b / VL1d, I-VL3, I-VL4 — genuinely exercised**, and proven
  non-vacuous by the sabotages above. VL1's both-binaries clause, VL1b's segment-by-segment
  sidecar comparison, VL1d's "no `Usage:` banner" oracle, I-VL3's not-a-green-success-line and
  I-VL4's whole-PNG gate each have a named test that fails when its fix is reverted.
- **VL1c is exercised in half.** The coverage half (starts at 0, no gap, reaches the duration) has
  five tests. The **measured placement** half — "a chunk's first frame, and a frame `extract_frame`
  pulls at `t`, must be the second the plan named", explicitly written as the criterion *instead of*
  the argument order — has **no test at all**. It was established by one checker probe on ffmpeg
  8.1.1 and can never regress-fail. **AT-170 raised low → medium** for this: it is a criterion in a
  HIGH-criticality contract that decides where every reported second lands, and `explore.md` X13
  already says a gate no test defends is decorative.
- **`core-invariants.md` C9 — two of three fields genuinely pinned.** `tests/test_goal_done_checks.py`
  is real and non-vacuous (four sabotages above), and it asserts the rule on *synthetic rows* as well
  as on disk, which is what makes it bite when no live row exercises a clause. The third field,
  `approved`, is unpinned and **disclosed in the criterion itself** (AT-156, open) — a contract that
  names its own gap rather than reading clean.
- **C7's sabotage clauses have no on-disk enforcement and cannot have any** — they govern the
  checker's harness, not the repo. This sweep honoured them by writing the harness that way
  (anchor-count assertion, re-read after write, INCONCLUSIVE on zero failures), and they earned
  their keep twice. Recorded, not filed: there is nothing in `src/` for a test to hold.

## Enforcement liveness

`.claude/hooks/lab-session-start.ps1` behaviour unchanged since the prior sweep's execution check.
All six hooks registered. `qa/loop.md` carries the seven terminal states with an uncontradicted
`Human gate` line. Repo has commits. No finding.

## Silent-failure hunt (code PASSed since the prior sweep)

Over `media/{chunks,frames,probe,transcribe}.py`, `stages/media_prep.py`, `cli_video.py`,
`cli_crawl.py`, `scripts/check_deliverable.py`: **no new finding.** The three `except Exception`
blocks in `transcribe.py` are the ones VL1 explicitly requires (`whisper_available` probing an
import, a malformed sidecar degrading to `engine="unreadable"`, and the CUDA→CPU fallback inside
the isolated `__main__`). AT-138 already records the one residual (the parse exception is
discarded entirely). Observation, not a finding: `transcribe_subprocess` folds a whisper that
*ran and failed* into `engine="none"` alongside "whisper is not installed" — the contract's
UNVERIFIED section covers this branch explicitly, so it is disclosed rather than hidden.

## Check 6 — gates

**Three gates are open, and all three are accurate on disk. None was answered off-disk.**

| Gate | State | Verified how |
|---|---|---|
| `at110-approval-forgery.md` | correctly **OPEN** | The only place an answer could hide is `qa/verdicts/t124-consent-gates.md`, which restates option 1 as a proposal (`:102`, `:349`), never as a decision. Unchanged since the prior sweep. |
| `erp-credentials.md` | correctly **OPEN** | `projects/erp/` contains no `.env` at all — the credentials genuinely have not been entered, so the gate is not merely unrecorded, it is unanswered. Filed as AT-142 by the prior sweep and written to disk at `8153a46`; the record is accurate. |
| `at147-expiry-end-of-day.md` | correctly **OPEN** (`**Answered:**` present but empty) | Grepped every verdict, manifest, tick stamp, DECISIONS entry and commit body for A/B/C, "end of day", "23:59": the only hits are the checker's and maker's own statements of the *question* (`at147-at148-grant-boundary.md:158-190`, `at149-at150-path-containment.md:76`). No answer anywhere. |

`at052` and `at106` both carry correct `Answered:` lines. **Improvement worth naming:** the latest
tick stamp now lists all three open gates by name — the prior sweep's AT-142 finding (a gate living
only in prose) is closed in behaviour, not just in code.

## Check 6 — goal-drift: **no `GRILL:` row**

None of check 6's triggers fires: `qa/.regrill-due` is absent, the north star is unchanged, no
reopen-power escalation occurred (this sweep reopened nothing), and the two `STALLED` tick stamps
both have a matching `qa/debug/` report. The headline finding below is filed as a buildable unit
(AT-177), not as a question only Umesh can answer — so it does not warrant a gate line that would
sit above the TODO rows the maker reads first.

---

# The headline: is the maker's recurring failure mode actually falling?

**Short answer: the rate is not falling. What has fallen is the latency to detection — by roughly
two orders of magnitude — and that is being mistaken for prevention.**

The shape, stated once: *the maker verifies the mechanism it changed, rather than what a production
run or a reader actually sees.* Its three sub-forms are (a) the stage is fixed and the shipped path
is not, (b) the test asserts that the mechanism ran rather than that the property holds, and (c) a
declared value is honoured internally but no shipped caller applies it.

## Instances per unit, in session order

| # | Unit | Instances of the class | Found by |
|---|---|---|---|
| 1 | at113-node-recovery-honesty | 1 (AT-113: status reached the Excel sheet only, never the crawl page or the issue count) | **sweep**, hours later |
| 2 | at116-criticality-vocabulary | 2 (AT-116 every floor inert; AT-119 the test hardcodes a copy of the vocabulary with no link to the real reader) | unit |
| 3 | at108-at114-swallowed-causes | 1 (AT-114) | unit |
| 4 | at120-evidence-not-product-issues | 1 (AT-120: distinct in the artifact, absent from every count a human reads) | unit |
| 5 | at121-at122-crawl-count-surfaces | 4 (AT-121, AT-122, AT-123, AT-124 — four separate reader surfaces) | unit |
| 6 | at125-at132-declared-but-unapplied | 2 (AT-125 no shipped caller passes it; AT-136 the same shape survives in three more places **inside the unit built to close it**) | unit |
| 7 | t131-ingest-persists | 1 (AT-134) | unit |
| 8 | at140-crawl-cli-coverage (cycle 1 FAIL) | 3 (AT-143 the no-trace test globbed the wrong path; AT-144 two bounds reach no assertion; AT-145 `approve` grants approvals that can authorise nothing and prints success) | unit |
| 9 | at147-at148-grant-boundary | 1 (AT-147: green "granted" for a grant the runtime refuses) | unit |
| 10 | at149-at150-path-containment | 2 (AT-149 fixed in the host half, left naive in the path half; AT-150 the refusal names a date it never prints) | unit |
| 11 | at151-at152-both-arms | 2 (AT-151: the *third* occurrence of one-arm-fixed; AT-152) | unit |
| 12 | at141-at115-done-check-can-fail | 2 (AT-154, AT-155 fails open by construction) | unit |
| 13 | at154-at157-fail-closed | 3 (AT-158, AT-159, **AT-160 — a test that does not detect deletion of the clause it is named after**) | unit |
| 14 | at158-at160-program-position | 2 (AT-161, AT-162) | unit |
| 15 | t132-media-prep (3 cycles) | 6 (AT-163, AT-164, AT-165, AT-166, AT-170, AT-171) | unit |
| 16 | at172-at173-dead-command-shape (live) | 4 (AT-172, AT-173, AT-174, AT-175) | unit |

**The trend is real but it is not the trend the countermeasures were adopted for.**

- **Density per unit is flat-to-rising**, not falling: 1–2 per unit for the first seven units, 2–4
  for the middle six, 6 and 4 for the last two. Unit size fell over the same period, so per-unit
  density understates it if anything.
- **No unit since at113 has come back clean of this class.** Sixteen consecutive units.
- **Both countermeasures generated fresh instances of the class inside themselves.** at140 was
  built to close "no test drives the shipped CLI" and its cycle-1 test looked in the wrong place
  (AT-143). at154-at157 was built to make a `done_check` capable of failing and shipped a test that
  could not detect deletion of its own exemption clause (AT-160) — which is C7's INCONCLUSIVE class
  appearing inside the unit written to close C7's INCONCLUSIVE class.
- **What genuinely improved is detection latency and fix radius.** AT-113, AT-115 and AT-140 were
  all found by the *sweep*, hours after the fact. Every instance from unit 4 onward was found by the
  *unit checker*, in the same cycle, minutes later. And the response changed shape at unit 16:
  commit `3b765a4` is titled *"stop fixing instances of the dead-command bug"* and ships
  `tests/test_cli_advice_resolves.py`, which walks the AST of all of `src/` and asks the CLI to
  resolve every command the code names. That is the first fix in this session aimed at the class
  rather than at an instance. The maker also now names the shape in its own commit messages
  (`f90fcb3`: *"the stage was fixed and the shipped path was not"*).

**So: the maker is finding the same class faster and, once, fixing it wider. It is not producing
less of it.** Recognition has improved; prevention has not moved. On the north star's own terms
that is a *time* cost, not a correctness cost — the checker is catching these — but it is fifteen
units of the same lesson, and the mechanism that would convert recognition into prevention (a
class-level guard, written once) exists in exactly one place as of two hours ago.

## Where the blind spot is still unguarded — measured, not asserted

**1. Fifteen of the twenty-two shipped CLI commands still have no test that drives them (AT-177,
high).** AT-140 was filed as *"no test drives the shipped `explore` or `approve`"* and its fix drove
exactly those two. Enumerated from `cli.py`'s registrations and cross-checked against every
`CliRunner().invoke()` in `tests/`:

- **Driven (7):** `explore`, `approve`, `login`, `ingest register`, `ingest prep`, `ingest frames`,
  `ingest run`.
- **Not driven (15):** `doctor`, `providers`, `map`, `snapshot`, `ledger add/weight/check/relitigation`,
  `flowspec status/approve/request-edit`, `report excel/html/crawl`, `ingest list`.

This is not the harmless half. **`flowspec approve` is the command that records a human's review of
a FlowSpec** — the gate `ingest.md` I6 exists to protect. **`report crawl`, `report excel` and
`report html` are the reader surfaces** that AT-120, AT-121, AT-122 and AT-123 were every one of them
filed against. `ledger check` is what `doctor`'s governance gate calls. The class was named, and one
instance was closed — the same instance-not-shape response the maker itself diagnosed one directory
over, in the same session.

**2. The one class-level guard cannot see the message the class was created for (AT-176, medium).**
Executing `test_cli_advice_resolves.py`'s own collector: it yields **5** distinct commands
(`ingest register`, `ingest list`, `snapshot`, `map`, `flowspec approve <project> --by <name>`). It
does **not** yield `autotester ingest prep`. `require_prepared`'s advice is built as
``f"… run `{PREP_COMMAND} " f"{slug} {source_id}` …"`` — two `ast.Constant` nodes with the backtick
opening in the first, and the literal word `autotester` never adjacent to a backtick at all, because
it lives inside the `PREP_COMMAND` constant. The regex matches nothing in either literal. The
docstring discloses one exclusion (`{}` templates) but not this one. No live dead end today —
`media_prep`'s own dedicated test still covers it, and both remaining `DEAD` hits in a raw scan
(`media prep`, `ingest analyze`) are historical *comments*, correctly skipped by the AST walk. The
defect is that the guard is advertised as closing the class and would let a future `PREP_COMMAND`-style
constant ship green. **This is the class's own signature applied to the countermeasure: the mechanism
was verified, the collector's reach was not.** Note: this file belongs to the unit currently under
check, so if that unit's checker files the same thing, AT-176 is the duplicate.

**3. VL1c's measured placement property has no test (AT-170, raised to medium).** See contract
coverage above.

---

## Top-3 recommended next units

1. **AT-177 (high) — finish what AT-140 started: drive the remaining shipped commands.** Highest
   leverage on the board, and it converts the session's most expensive lesson into a standing gate
   instead of a fifteenth diagnosis. Order by what a human or a gate reads: **`flowspec approve` and
   `flowspec request-edit` first** (the human review gate, protected by I6), then **`report crawl` /
   `report excel` / `report html`** (the four reader-surface issues AT-120–AT-123 all landed here),
   then `ledger check` and `doctor`. Model it on `tests/test_ingest_real_cli.py`, which is already
   proven non-vacuous. Do this **before T-133** — Track A4 will add more reader surfaces to an
   already-unguarded set.

2. **AT-176 (medium) + AT-170 (medium) as one unit — make the two class guards actually cover their
   class.** Both are the same defect in two places: a guard whose *reach* was never measured.
   (i) Teach `advice_in_source()` to fold implicit string concatenation and resolve module-level
   `str` constants, then assert the collector finds `ingest prep` specifically — the vacuity guard
   should pin a known member, not just a count. (ii) Give VL1c's placement half a real test:
   `extract_frame` at a known `t` on a fixture with sparse keyframes, asserting the frame is the one
   the plan named. **Wait for the `at172-at173` verdict first** — that unit owns
   `test_cli_advice_resolves.py` and is under check now.

3. **AT-161 (medium) + AT-162 (low) — close the fail-open still live in the `done_check` predicate.**
   `is_capable_of_failing` scores segments with `any()`, so the `|| true` neutering family still
   reaches through `;` and `&&`; and `offenders_in` silently skips a row whose `cmd` is `""` or
   `null`. This is the governance predicate that decides whether anything is finished, it fails
   **open** in both cases, and the file is already under test — cheap, and it is the fourth cycle on
   one predicate, so closing it properly ends that thread.

**Three HUMAN_GATES open, none of which may idle the three units above:**
`at110-approval-forgery.md` · `erp-credentials.md` · `at147-expiry-end-of-day.md`. AT-110 and
at147 should both be answered before T-145 runs against the live ERP — they decide what the consent
gate is allowed to claim and how long a grant lasts. The ERP credentials gate caps what the loop can
ultimately demonstrate but blocks nothing on this queue.

**Cheap and worth folding in:** AT-099 (low) — `ui-flow-diagram.md` and `ui-sidebar.md` are still the
only two of 28 contracts with no Amendment log. Unchanged for three sweeps.
