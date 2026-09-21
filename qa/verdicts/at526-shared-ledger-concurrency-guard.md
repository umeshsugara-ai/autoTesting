# Verdict — at526-shared-ledger-concurrency-guard

**Cycle checked:** 1
**Date:** 2026-09-21
**Checked by:** /checker (fresh subagent, bound to `D:/autoTesting`)
**Commit under check:** `290442a` — `qa(maker): land at526 investigation (manifest + gate + evidence)` (unit's own landing commit; `git show --name-only 290442a` = only `qa/manifests/at526-*`, `qa/gates/at526-*`, `qa/evidence/at526-*/*` — exactly its authorized set)
**Unit type:** INVESTIGATION (brief explicitly allowed ending as a proposal)
**Gate status:** `qa/gates/at526-shared-ledger-concurrency-guard.md` carries `Answered: 2026-09-21 — Option 3: Both` (Umesh: orchestration serialization now + commit-guard fast-follow; checker-skill commit-step change authorized). Per the dispatch's context update, this verdict judges whether the measurement and the drafted module are **sound**, not whether a proposal was the right ending.

## VERDICT: PASS

SCOREBOARD: 6/6 capability-coverage rows reproduced; contract criteria C7 + C10 (`qa/contracts/core-invariants.md`) hold for this unit; 0 invariants violated by the unit's own footprint. Verify instruments re-run by me: `uv run autotester doctor` (see "Live-tree note" — one violation, NOT charged to this unit, evidence below), `uv run ruff check src tests scripts` → `All checks passed!`, smoke script → 7/7 PASS exit 0, sparsity script → exact reproduction.

## What I independently re-derived (not trusted from the manifest)

1. **The 7-incident history is real.** Re-ran `git log --format='%h %ad %s' --date=iso -- qa/issues.jsonl` myself: **287 commits**, matching the manifest's count and `qa/evidence/.../ledger_commit_log.txt` byte-for-line (287 lines; all 7 cited hashes present with matching dates/messages). Then read each cited commit's actual diff, not its message:
   - `35b3dcb` (09-09) — real diff renumbering the collision: commit message "resolve AT-269 id collision -- renumber to AT-271", fifth collision that session. Confirmed.
   - `2e0e9c0` (09-11) — closes `at319-issue-id-collision-reconcile` cycle 1 (dedicated reconcile unit exists). Confirmed.
   - `b04d7c9` (09-11) — real diff: `AT-335` row → `AT-337`, "second collision, trivial", with the concurrent-allocation cause in the message. Confirmed.
   - `6566441` (09-17) — real diff (1 line) plus message: the at229-249 verdict commit's ledger was built from a shared copy a concurrent loop had appended to; the checker's own finding was silently overwritten by the other loop's row under the same id (AT-482 collision). **Dropped finding, same-day fix.** Confirmed.
   - `67a61ec` (09-18 01:05, AT-496) — real diff shows exactly the claimed loss shape: the `-` side carries `AT-401` at status `fixed` and the pre-incident `AT-494` row; the `+` side re-adds them. The commit is itself the *restoration* after the stale-write loss (`1688da3` dropped them; independently cross-checked against `qa/manifests/at496-the-ledger-never-loses-a-row.md`, whose Step-1 numbers — `9b5cbc5` appended AT-494 + flipped AT-401, `1688da3`'s stale blob lost both — the smoke script's scenario 7 reconstructs accurately). **Real data loss, ~30 min undetected.** Confirmed.
   - `a8caf58` (09-18 06:52) — real diff: **82 lines changed (41 ins / 41 del)**, pure reformat repair ("fix a self-inflicted ledger reformat from the at511 PASS commit"). Confirmed (same sloppy-shared-write family, as disclosed — not a concurrency collision).
   - `0fe2b6d` (09-18 09:14, this unit's subject) — real diff confirms the mechanism: the at521 checker's PASS commit carries the at520 checker's **flip of AT-520** (`open`→`fixed`, `-`/`+` pair) **and the at521 checker's own new AT-525 row** (`+` only) — content the at521 checker did not author, swept in because `git commit --only <path>` commits the file's on-disk content wholesale. **No damage this time** (both swept edits were correct; AT-520's verdict at `c3bde8d`/`fc2bd50` landed after). Confirmed.
   Tally: 7 distinct incidents across 4 mechanisms (id-collision ×3, stale-copy loss ×2, shared-tree sweep-in ×1, wholesale reformat ×1), 2 with confirmed real data loss — **reproduced exactly.**

2. **Option (d) is a false-accusation machine — measurement reproduced.** Re-ran `uv run python qa/evidence/at526-shared-ledger-concurrency-guard/measure_fixed_by_sparsity.py` myself: `total rows: 523  fixed rows: 150 / fixed rows with NO fixed_by field: 130 / ...NOT present on disk: 0` — identical to the manifest and the evidence log. 130/150 = 86.7% ≈ the claimed 87%. The script's logic is sound (parses every row, filters `status=="fixed"`, counts missing/empty `fixed_by`, checks `fixed_by`-named verdict files against `qa/verdicts/` on disk). The recommendation **not** to build a rule gating on `fixed_by` in its current form is evidenced: the field is populated on only 13% of legitimately-fixed rows. I spot-checked a real populated row's `fixed_by` format for this verdict's own ledger flip (`"fixed_by": "qa/verdicts/at504-....md (cycle 1, PASS) -- ..."`).

3. **The drafted guard is real, working, and correctly unmerged.**
   - **Smoke script re-run by me:** `uv run python qa/evidence/at526-shared-ledger-concurrency-guard/smoke_commit_guard.py` → **7 PASS lines, 0 assertion errors, exit 0** — identical to the manifest, including the two load-bearing rows: `{'AT-520': 'changed', 'AT-525': 'added'}` (the exact AT-526 incident, would have REFUSED) and `{'AT-401': 'changed', 'AT-494': 'removed'}` (the AT-496 stale-copy loss, would ALSO have caught).
   - **The AT-496 scenario's inputs are faithful**, not invented: `qa/manifests/at496-the-ledger-never-loses-a-row.md` itself records `9b5cbc5` appended AT-494 + flipped AT-401 to `fixed`, and `1688da3` built from a stale pre-`9b5cbc5` blob (AT-401 back to `open`, AT-494 gone) — exactly what smoke scenario 7 encodes, with the checker's own intent (`AT-499` only) taken from that same manifest's narrative.
   - **File-budget wall re-verified:** `tests/test_ledger.py` = **226 lines** at today's HEAD (manifest said 294/300 at its writing; the shrink is at523's later split of ledger checks into `tests/test_ledger_checks.py` at `5a88ed4` — a different unit). The *constraint as the manifest stated it* (6 lines of headroom at its writing) was real then, and the manifest's decision not to ship untested code is the correct one either way; the wall itself is now moot because at523 already demonstrated the sibling-file split (`src/autotester/ledger/checks.py` + `tests/test_ledger_checks.py`) the gate's option 1 proposes. `check_file_sizes` and `MAX_FILE_LINES = 300` confirmed at `src/autotester/doctor.py:68` / `:17`.
   - **Code review of `commit_guard.proposed.py` (141 lines) as if adopting it:** read in full. The pure logic is sound — id-keyed diff (position-independent), `json.dumps(sort_keys=True)` canonicalization (a pure reformat/reorder is never a false change), skip-don't-raise on unparseable lines (correct: it is a guard, not a validator — `check_qa_issue_rows` at `src/autotester/ledger/checks.py:141` owns shape validation), fresh `git show HEAD:` read at commit time (not cached), refusal names the exact foreign ids, and it still commits via `git commit --only qa/issues.jsonl` (C10-compliant). Three **fast-follow notes, none blocking this proposal** (all are adoption-time hardening, and the module is explicitly unvetted-until-its-own-unit):
     a. `_read_head_ledger` returns `""` on *any* non-zero `git show` exit — indistinguishable from "no commit yet". Fail-closed in effect (every row reads "added" → refusal), but the error message would misname every id as an unexpected add; the fast-follow should distinguish empty-history from git failure.
     b. `_rows_by_id` is last-wins on a file already containing duplicate ids — a duplicate the id-collision family produced would be invisible to this diff (shape validation is out of its declared scope, and `check_qa_issue_rows` owns that class, so no gap in the guard's own job — but the fast-follow's tests should pin the behavior).
     c. `commit_cmd`'s `subprocess.run(..., check=True)` surfaces a failed commit as a raw `CalledProcessError` traceback rather than a clean message — cosmetic UX only.
   - **Disclosed gap verified honest:** the guard genuinely does NOT address the id-collision family (3 of 7) — two agents independently choosing the same new id both look like legitimate intended adds to a content diff. The gate names this as needing a separate id-allocation remedy, and the gate's Answered line keeps it named. Disclosure accurate, not silently dropped.

4. **"Nothing of mine is left in src/" — still true at current HEAD, with the two-units confusion resolved.** `git diff HEAD --stat -- src/` → **empty** (the maker's transient diff was against a pre-`5a88ed4` tree; the at523 files are now committed, so today's diff is clean). Authorship is proven from git, not the diff alone: `290442a` (at526's landing) touches **only** its qa/ files — **zero `src/` files** — while the `src/autotester/doctor.py` / `src/autotester/ledger/checks.py` / `tests/test_ledger_checks.py` changes came in the separate at523 commit `5a88ed4` with its own manifest and evidence. The at526 draft (`commit_guard.proposed.py`) exists only under `qa/evidence/at526-*`, never in `src/` at any commit (verified via the landing commit's name-only list). The manifest's claim, re-read against its own era (`290442a`'s parent `69b852e`), holds: at that point the working-tree src diff was at523's in-flight work, none of it at526's.

5. **Verify commands re-run by me (Mode A step 3):**
   - `uv run ruff check src tests scripts` → `All checks passed!` (matches manifest).
   - `uv run autotester doctor` → **`stale-generated: docs/SNAPSHOT.md` — 1 violation.** See "Live-tree note" below: traced to at523's landed `src/` change (`5a88ed4`, 09-21, after this manifest was written and landed at 12:18:39), not to this unit. Not charged here; recorded for the next maker tick.
   - `git log` over `qa/issues.jsonl` → 287 commits (matches).
   - Smoke + sparsity scripts → reproduced exactly (above).

6. **Diff scope (step 4c).** `git show --name-only 290442a`: 7 files, all under `qa/manifests/at526-*`, `qa/gates/at526-*`, `qa/evidence/at526-*` — the manifest's declared changed-paths set exactly. Nothing deleted or renamed anywhere by this unit; `qa/contracts/core-invariants.md` untouched by it (confirmed: the at526-era contract edits in `0fe2b6d` belong to the at521 unit; at526's own landing commit contains no contract file). No scope violation.

7. **Issues addressed:** AT-526 is this unit's own subject; the manifest correctly did NOT flip it (checker's write surface per AT-499) and correctly left the ledger untouched — `git show 290442a --name-only` confirms `qa/issues.jsonl` is not in the unit's commit. **I flipped it: `open → fixed` with `fixed_by` naming this verdict** (row 523, single-line edit, every other byte preserved — `git diff` = 1 insertion, 1 deletion). This matches the AT-499 row-schema convention (`"fixed_by": "qa/verdicts/....md (cycle N, PASS) -- ..."`).

## Live-tree note (not a failure of this unit)

At check time `uv run autotester doctor` reports `stale-generated: docs/SNAPSHOT.md`. Trace: `docs/SNAPSHOT.md` was last regenerated at `d7298b5` (09-18); the src/ changes between then and HEAD are **at523's** `5a88ed4` (doctor.py +10/-2, checks.py +95, render.py +25 — landed 2026-09-21 12:18:40, one second after at526's own landing commit, by the separate at523 unit with its own manifest). `290442a` (at526) touched no `src/` file, and `docs/` is generated from `src/` by `autotester map`/`snapshot` — so the drift is at523's residual, not at526's. Per the dispatch's context update (record, do not penalize), this is not charged here. **Handoff:** the next maker tick should run `uv run autotester snapshot` (or map) to regenerate `docs/SNAPSHOT.md`; flagging in the verdict so it is not silently lost. It does not block this PASS: C2's instrument is clean on everything this unit produced or touched.

## Capability coverage (checker reproduction of the manifest's table)

| capability | my reproduction | result |
|---|---|---|
| the AT-526 incident is not a one-off | re-ran the git log; grepped + read all 7 cited diffs in full | 7 incidents / 4 mechanisms / 2 real data losses — confirmed |
| no damage currently sitting in the ledger | re-ran `autotester doctor`; `check_qa_issue_rows` at `checks.py:141` present (AT-496's detector) | no `ledger-row-lost`/`ledger-row-stale` fires (SNAPSHOT note above is a different rule, attributed to at523) |
| option (d) is a false-accusation machine | re-ran `measure_fixed_by_sparsity.py` | 523/150/130/0 — exact match, 87% claim accurate |
| the guard would have refused the real incident | re-ran `smoke_commit_guard.py` | `{'AT-520': 'changed', 'AT-525': 'added'}` — matches `0fe2b6d`'s actual diff |
| the guard generalizes to AT-496's mechanism | re-ran `smoke_commit_guard.py` + cross-checked scenario inputs against `qa/manifests/at496-*.md` | `{'AT-401': 'changed', 'AT-494': 'removed'}` — matches AT-496's manifest numbers |
| nothing of mine is left in `src/` | `git diff HEAD --stat -- src/` (empty at HEAD) + `git show --name-only 290442a` (no src files) + authorship attribution to 5a88ed4 | confirmed |

No falsifying-edit rows apply: this is an investigation unit (`revert_op: none` in the manifest, correctly declared) — the claims are historical git facts and a proposed module, both re-derived above rather than re-falsified. No UI surface touched (changed paths are qa/ markdown + evidence only) → `LIVE-BROWSER: not-applicable`.

## Close-out

- Ledger: AT-526 flipped `open → fixed`, `fixed_by` names this verdict (cycle 1, PASS). No new issues filed by this check (the three commit_guard adoption notes above ride inside the verdict for the fast-follow unit; filing them as ledger rows now would pre-judge a module that is not yet adopted).
- Context updates recorded, not penalized: gate answered 2026-09-21 (option 3); HEAD moved past the manifest's step-1 citations (append-only history preserved all 7 cited commits).

VERDICT: PASS