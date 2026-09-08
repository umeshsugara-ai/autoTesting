# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T01:30 IST (2026-09-08T20:00Z)** (bound to
`D:/autoTesting`). Prior sweep 2026-09-08T19:05Z, ~4h25m and 39 commits ago. Everything the prior
sweep recorded was treated as stale and re-derived from disk.

Docker is down; every command below ran natively under `uv`. Bare `uv run pytest`.

## Concurrency note (AT-101, respected)

No `git stash`, `git checkout` or `git restore` ran in the live tree. All six sabotages ran in a
`git archive HEAD` extract under the session scratchpad, imported via `PYTHONPATH` so the extract's
`src/` and `tests/` win over the editable install (verified: `autotester.__file__` resolves inside
the extract). `docs/MAP.md` was regenerated **in the extract**, not in the live tree —
`git status --porcelain docs/` stayed empty throughout.

**A unit checker on `t133-ensemble-and-issues` was live for this entire sweep.** Its manifest, its
verdict path, `qa/contracts/video-learning.md` (which it is amending with VL2–VL6, I-VL5, I-VL6)
and the nine ledger rows it filed (AT-197…AT-205) were **read but never written**. This sweep wrote
only `qa/issues.jsonl` (its own eight row changes + AT-206), this file, and `qa/.last-sweep`.

---

## Measured state

| | Prior sweep | **Measured now** |
|---|---|---|
| Ledger | 126 verified / 50 open / 0 fixed | **140 verified / 65 open / 0 fixed** (6 high, 24 medium, 35 low open) |
| Manifests / verdicts | 80 / 79 | **84 / 83** |
| Goal tasks | 30/45 done (66.7%) | **30/45 done (66.7%)**, 15 pending — matches disk |
| Test suite | 700 passed, 2 skipped | **797 passed, 2 skipped** (799 collected, 0 `FAILED`) |
| `ruff` / `doctor` | clean | **clean** |
| `docs/MAP.md` | byte-identical | **regenerated in the extract — byte-identical** |
| `docs/SNAPSHOT.md` | byte-identical | **`autotester snapshot --print` diffed against disk — identical** |

**No stale-state drift.** Both generated docs are genuinely fresh rather than merely doctor-green.
The only working-tree modifications are the live t133 checker's (`qa/contracts/video-learning.md`,
`qa/issues.jsonl`) and the `/goal` monitor's timestamp tick (`.goal/*`).

## Bypass detection — clean

All 39 commits since `125cbaf` examined. Every commit touching `src/` or `tests/` carries a
manifest: `81efef9`/`d2d547d`/`befb425`/`c66fafc` (at177 cycles 1–2), `8298020` (at185-at187),
`e2f119f` (at176-at178), `7879af5`/`96128a0`/`bafb390` (t133, `ready-for-check`). Two cosmetic
observations, neither filed: `aa5ad6c` and `b5fde53` carry an identical `chore(docs): regenerate
MAP` message but `b5fde53` touches only `.goal/*`; `d2d547d`'s message is a pasted pytest failure
dump (already AT-188, low, open).

## Handshake integrity — clean

84 manifests, 83 verdicts. The single manifest without a verdict is `t133-ensemble-and-issues` at
`Status: ready-for-check`, `Fix cycle: 1`, under a live unit checker — a dispatch in flight, not a
gap. Every other latest verdict is `PASS` at a `Cycle checked` equal to its manifest's `Fix cycle`;
the one historic exception (`at015-at028-hook-adapter-fix`, `STALLED` with a matching
`qa/debug/at015-at028-hook-adapter-fix-cycle3.md` and a RECOVERY PASS) is unchanged and on record.

Maker liveness: `qa/.last-tick` fresh (01:15 IST, 15 min), `qa/.paused` absent, `qa/.regrill-due`
absent.

## The `fixed` backlog — 6 → 0, cleared by execution

Six rows arrived `fixed` since the prior sweep. All six are now `verified`, four by sabotage in the
extract under a C7-compliant harness (anchor matched **exactly once**, file re-read and shown
changed, zero failures reported **INCONCLUSIVE** and never as "the test is vacuous"):

| Sabotage | Result |
|---|---|
| **AT-172 (high)** — restore `autotester ingest analyze` in `cli_video.py`'s refusal | **CAUGHT**, 1 failure (`test_every_command_the_code_names_is_one_the_cli_exposes[cli_video.py-ingest]`) |
| **AT-173 (medium)** — `if not video.is_file():` → `if False:` in `extract_frames` | **CAUGHT**, 2 failures — one at the stage level, one at the shipped CLI level. Fixed at both levels as claimed |
| **AT-174 (medium)** — `PREP_COMMAND` → `autotester ingest frames` (registered, same arity: defeats every static oracle) | **CAUGHT**, 2 failures including `test_the_refusal_names_a_command_that_actually_stops_it`. The causal oracle genuinely discriminates |
| **AT-176 (high)** — kill implicit-concat folding in `advice_scan._render` | **INCONCLUSIVE — 0 failures.** Resolved by execution instead → see AT-206 below |
| **AT-178 (medium)** — re-require a leading backtick in `COMMAND` | **INCONCLUSIVE — 0 failures.** Same → AT-206 |
| **AT-189 (medium)** — no useful mutation exists | Verified by reading: `WATCHED_DIRS = ("docs", "src", "scripts", "projects")`, `qa/` removed. Its purpose is to avoid flakiness, not to detect a regression, so no guard is owed |

AT-176's and AT-178's **fixes are real and were verified by direct execution** — `advice_in_source`
finds 10 sites including the un-backticked `core/consent.py` `approve`, and an AST walk of
`media_prep.py` shows the `JoinedStr` at line 157 rendering to `autotester ingest prep`, which the
old literal scanner could not see. **NO REOPENS.**

**AT-177 (high) closed by measurement, not by assertion.** It was still `open` after the two units
built to close it. Rather than take that at face value either way, I executed
`cli_walk.shipped_commands()` + `invocation_for()` against an empty `AUTOTESTER_ROOT`: **22 shipped
commands, 22 reach application code, 0 stop at click's `Usage:` banner.** Moved `open → verified`;
the residual thinness stays split out as AT-182/AT-183 (both low, open).

## Contract coverage — what is actually pinned

- **`video-learning.md` VL1 / VL1b / VL1d, I-VL3, I-VL4 — genuinely exercised**, unchanged from the
  prior sweep and re-confirmed by this sweep's AT-172/173/174 sabotages. VL1d has gained a **causal**
  oracle (trigger the refusal, run the command it names, assert the refusal stops) that a
  registered same-arity sibling fails — the strongest oracle in the contract.
- **VL1c's measured-placement half still has NO test — second sweep unchanged (AT-170, medium).**
  `test_frames_are_extracted_only_for_the_seconds_the_model_named` monkeypatches `extract_frame`
  and asserts the *arguments passed*, not that the frame is the second the plan named. That is
  form (b) of the recurring class, sitting inside a HIGH-criticality contract, for two sweeps.
- **VL2–VL6, I-VL5, I-VL6 arrived in the working tree during this sweep** (+121 lines, uncommitted,
  written by the live t133 checker). Coverage of the new criteria belongs to that unit's verdict and
  to the next sweep; this sweep neither read them as settled nor touched the file.
- **`core-invariants.md` C4 — now pinned harder than by `doctor` alone.** The repo-fingerprint test
  in `tests/test_cli_harness_safety.py` catches a verify step that mutates the repo (AT-181). Its
  reach is the open residual (AT-187 verified, AT-190/AT-191 open, all low).
- **C7 earned its keep twice more.** Both INCONCLUSIVE results above were reported as INCONCLUSIVE
  rather than as vacuous tests — and following that rule to its conclusion is what produced AT-206,
  this sweep's headline finding. C7 has no on-disk enforcement and cannot have any; it governs the
  checker's harness, not the repo.
- **C9's `approved` field remains unpinned and disclosed in the criterion itself** (AT-156, open).
  Unchanged for three sweeps — a contract that names its own gap rather than reading clean.

## Enforcement liveness

All hooks registered (`SessionStart` ×2, `PreToolUse` ×2, `SessionEnd` ×1); the three
`.claude/hooks/*.ps1` files present; repo has 423 commits. `qa/loop.md` carries all seven terminal
states with an uncontradicted `Human gate` line. No finding.

**The three loop-design questions.** *Can it spin?* No — `ADVANCED` requires "one unit moved on
evidence". *Can it Goodhart the verifier?* **Partially yes, and this sweep measured it:** the
adapter's slot-1 is `uv run pytest`, and two of this session's guards pass while their fix is
removed (AT-206) — a green suite is a weaker signal than the loop treats it as. Filed as AT-206
rather than as a loop-spec defect, because the fix is in the tests, not in the spec.
*Can it run a wrong answer to completion?* The `done_check` predicate still fails **open**
(AT-161/AT-162, open, fourth cycle on one predicate).

## Silent-failure hunt (code PASSed since the prior sweep)

Over `cli_video.py` and `stages/media_prep.py`: **no new finding.** The one broad
`except Exception` (`media_prep.py:81`) re-raises as `UnreadableRecording` naming the original type
and chaining `from exc` — that is AT-166's required behaviour, not a swallow. T-133's new modules
are under a live unit check and are that checker's to scan.

## Gates — three open, all accurate, none answered off-disk

| Gate | State | Verified how |
|---|---|---|
| `at110-approval-forgery.md` | correctly **OPEN** | Grepped `qa/verdicts/`, `qa/manifests/` and `docs/DECISIONS.md` for `hmac`/`keyed hash`/`approval forgery`: one hit, `qa/verdicts/t124-consent-gates.md`, which restates an option as a proposal. No decision anywhere |
| `erp-credentials.md` | correctly **OPEN** | `projects/erp/` contains `cases.jsonl`, `project.json`, `rubrics/`, `runs/` and **no `.env` at all** — the credentials genuinely have not been entered |
| `at147-expiry-end-of-day.md` | correctly **OPEN** (`**Answered:**` present but empty) | Grepped every verdict, manifest, tick stamp, DECISIONS entry and the 39 commit bodies for `end of day`, `23:59`, `expiry`, `expires`, `option [123]`. Every hit is technical discussion of the defect (`at140`, `at147-at148` verdicts); none is a policy decision |

`at052` and `at106` both carry correct `Answered:` lines. The maker's tick stamp still names all
three open gates by name.

## Check 6 — goal-drift: **no `GRILL:` row**

`qa/.regrill-due` absent, north star unchanged, no reopen-power escalation (this sweep reopened
nothing), no `STALLED`/`EXHAUSTED` stamp without a matching `qa/debug/` report. AT-206 is buildable
by the next tick, not a question only Umesh can answer.

---

# The headline, re-measured: did anything actually change?

**Two things changed, and one of them is real. The production rate of the class did not move.**

The shape, restated once: *the maker verifies the mechanism it changed, rather than what a
production run or a reader actually sees.* Sub-forms: (a) the stage is fixed and the shipped path
is not, (b) the test asserts that the mechanism ran rather than that the property holds, (c) a
declared value is honoured internally but no shipped caller applies it.

## The four units since the last sweep

| Unit | Instances of the class | Self-caught | Checker-caught |
|---|---|---|---|
| at177-cli-surface (cycle 1 **FAIL** → cycle 2 PASS) | **4** — AT-180 (the matrix asserted a property of *click's argument parser* for 18 of 22 commands, not of autotester), AT-185 (an exclusion whose stated reason was measurably wrong), AT-186 (a guard that fires only when the regenerated file differs from disk), AT-187 (the fingerprint's reach never measured) | **0** | 8 rows (AT-179…AT-188) |
| at185-at187-write-not-change (PASS c1) | **3** — AT-189 (the rule applied to `.goal/` and not to `qa/`, inside one commit), AT-190 (files-only walk: a new *directory* is invisible), AT-191 (mtime granularity: an idempotent write in the same tick is undetectable) | **0** | 3 rows |
| at176-at178-render-not-scan (PASS c1) | **4** — AT-192 (the renderer resolves only *same-file* constants, so AT-176's own shape one `import` away is invisible again), AT-193, AT-195 ("marks it rather than pretending" overstated), AT-196 (a test enumerating the two statuses its author observed instead of asserting the invariant it is named for) | **0** | 5 rows |
| **+ this sweep** | **1 more in that same unit** — AT-206, below | — | sweep |
| t133-ensemble-and-issues (live, cycle 1) | **1 self-caught pre-ship** — a determinism test that compared whole JSON including `Artifact.created_at`, so `adjudicate-twice` had been passing *only because both calls landed in the same microsecond* | **3** (this one, an inverted `max()` on descending severity, and a field that does not exist) | 9 rows filed so far (AT-197…AT-205, **four of them high**) |

**Self-caught across the three units that have closed: 0 of 16. Checker-caught: 16 of 16.**

## So: is the rate falling?

**No. Nineteen consecutive units since at113 have come back carrying this class, and the three that
closed in this window produced 4, 3 and 4 instances — the same band as the 6 and 4 the prior sweep
reported, on units that got smaller.** Density per unit is flat. Self-catch rate on shipped units
is still zero.

**AT-206 is the sharpest single piece of evidence this session has produced, and it is a
third-generation instance.** The chain: AT-163/AT-172 was the dead-command bug → the countermeasure
was a class-level guard (`test_cli_advice_resolves.py`) → that guard could not see the one message
the class exists for (AT-176) → the countermeasure to *that* was the renderer in `advice_scan.py`,
shipped with an assertion written expressly to pin it: `assert "ingest prep" in commands`.
**That assertion passes with the renderer entirely disabled.**
`PREP_COMMAND = "autotester ingest prep"` is itself an `ast.Constant`, which the *old naive scanner
already saw*, and `advice_in_source` dedups by `(file, command)` — so the guard cannot tell the site
it was written for from the constant's own definition sitting 127 lines above it. The companion
clause, `len(commands) >= 6`, has four sites of slack against the ten present, so AT-178's fix is
unpinned by the same assertion. **The vacuity guard is itself vacuous.** Mechanism verified; what it
would catch, never measured. That is the class's own signature, three levels deep, on the
countermeasure to the countermeasure to the countermeasure.

## What *did* change — two things, stated precisely

1. **The `&&` verify chain is a real countermeasure, adopted after a real cost.** The maker pushed
   `doctor`-red three times this session; the third time it *read* the red output and committed
   anyway, because its own chain used `;` instead of `&&`. Its own diagnosis is exact and is the
   general form of the class: *"the check ran, the result was right there, and the thing I did next
   did not depend on it. A verify step whose failure does not stop the next action is decoration."*
   The sequence is now one `pytest && ruff && doctor && commit` chain. This is the first
   countermeasure this session that removes the maker's *discretion* rather than adding another
   thing for it to remember — and it is the only one that has not yet produced an instance of the
   class inside itself.

2. **The first self-catch of the class, before shipping.** T-133's determinism test was passing only
   because two calls landed in the same microsecond — a test asserting that the mechanism ran, not
   that the property held, caught by the maker *by running rather than reading* and fixed before the
   commit. One instance is not a trend, and the same unit still arrived with nine checker findings
   (four high). But it is the first time in nineteen units that this class was stopped on the
   maker's side of the handshake, and it should be named as such rather than rounded off.

**Verdict, unsoftened: recognition and reaction have improved again; production has not moved.
Zero of sixteen instances in the three closed units were self-caught. The countermeasure adopted
two sweeps ago now has a third-generation instance of the class living inside it. The one change
that has structural teeth is the `&&` chain, because it is the only one that does not rely on the
maker remembering to look.**

---

## Top-3 recommended next units

**Standing handshake obligation above this list:** `t133-ensemble-and-issues` cycle 1 is under a
live checker that has already filed **four high** issues (AT-197 order-dependent merge in the
shipped two-prompt ensemble · AT-198 an analysis built from 1 of 24 calls is indistinguishable from
a complete one · AT-199 a truncated cache entry that `--force` cannot get past · AT-200 a cache key
that is the prompt's *name*, so editing a prompt silently reuses stale answers). Its verdict decides
the next unit; the list below is what to pick from once that cycle is answered.

1. **AT-206 (high) + AT-192 (medium) + AT-170 (medium) as one unit — make the class guards guard
   their class, and measure the reach this time.** All three are the same defect: a guard whose
   *reach* was asserted rather than measured. (i) AT-206: make the assertion name the *site*, not
   the command — dedup by `(file, lineno, command)` or assert that the `JoinedStr` at
   `media_prep.py:157` specifically resolves, and pin `core/consent.py`'s un-backticked `approve` by
   name instead of by a `>= 6` count with four sites of slack. **The acceptance test for this unit is
   the sabotage, not the suite: disabling `_render`'s implicit-concat folding must make it fail.**
   (ii) AT-192: resolve imported constants, or fail loudly on an unresolvable `Name` rather than
   returning `UNRESOLVED` silently. (iii) AT-170: give VL1c's placement half a real test —
   `extract_frame` at a known `t` on a fixture with sparse keyframes, asserting the frame is the
   second the plan named, with `extract_frame` **not** monkeypatched. Highest leverage on the board:
   it is the only item that converts nineteen units of the same lesson into a gate that can fail.

2. **AT-161 (medium) + AT-162 (low) — close the fail-open in the `done_check` predicate.** Unchanged
   across two sweeps and now the fourth cycle on one predicate. `is_capable_of_failing` scores
   segments with `any()`, so the `|| true` neutering family still reaches through `;` and `&&`; and
   `offenders_in` silently skips a row whose `cmd` is `""` or `null`. This is the governance
   predicate that decides whether anything is finished and it fails **open** in both cases. Note the
   `;`-vs-`&&` shape here is the *same shape* the maker just diagnosed in its own verify chain —
   closing it in code as well as in habit is cheap and ends the thread.

3. **T-136 (the scorer and the first real recall numbers) — but read
   `.work/track-a-corpus-facts.md` into the manifest BEFORE building.** It is the natural next unit
   after T-133 closes and the first that produces a number Umesh can judge the north star by. Four
   measured facts in that file each silently produce a **recall of zero** if the plan is followed
   instead: (a) the corpus is under `C:/Users/Lenovo/Videos/Screen Recordings/`, **not** the `D:`
   paths T-136 and A3 give; (b) `faster_whisper` is **not importable in the project venv**, so
   `engine="none"` is the default path on this host, not a fallback — the erp1/2/3 sidecars are what
   make the run possible at all; (c) `ERP_Issues_ALL.xlsx` holds **32** rows, not the plan's 33, so a
   denominator taken from the plan is wrong before the first comparison; (d) two ground-truth sheets
   the plan never enumerated (19 Aug, 24 Aug) exist with no matching registered recordings — the
   Trainers(7) + ALL scope is still right, but the plan's claim to have enumerated the ground truth
   is not. A scorer that reports 0.0 because it read an empty directory is the recurring class
   applied to the north star's own metric.

**Three HUMAN_GATES open, none of which may idle the three units above:**
`at110-approval-forgery.md` · `erp-credentials.md` · `at147-expiry-end-of-day.md`. AT-110 and at147
should both be answered before T-145 runs against the live ERP. The ERP credentials gate caps what
the loop can ultimately demonstrate but blocks nothing on this queue.

**Cheap and worth folding in:** AT-099 (low) — `ui-flow-diagram.md` and `ui-sidebar.md` are still
the only two of 28 contracts with no Amendment log. Unchanged for four sweeps.
