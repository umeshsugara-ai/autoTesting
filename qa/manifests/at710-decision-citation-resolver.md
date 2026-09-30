# Manifest — at710-decision-citation-resolver

**Unit:** AT-710's general remedy — a `D-NNN` decision-citation resolver in
`autotester doctor` (`qa/QUEUE.md` block, item 3). `qa/contracts/living-ledger.md`
L9 is the checker-owned criterion this implements verbatim; it was already written
and twice-amended (2026-09-28) by an earlier maker cycle on this same unit that
built, validated and then **held** its implementation on a file-budget gate. This
cycle independently re-derives the same implementation from L9's text (not copied
from the earlier session's `.work/`, which is gitignored scratch and not present in
this worktree), re-measures the file budget from scratch on the current tree, and
reaches the **same HUMAN_GATE**.

**Date:** 2026-09-28
**Fix cycle:** 1
**Status:** HUMAN_GATE: new module (see below) — **not** ready-for-check. Nothing
under `src/` or `tests/` changed; there is nothing yet for a checker to verify
against a contract, only a validated candidate held in gitignored scratch.

## HUMAN_GATE: new module

**Gate record:** `qa/gates/new-module-authorization.md` (filed by the maker orchestrator
2026-09-28). The four options and the recommendation live there; this section is the unit's
own statement of the wall it hit. The maker independently re-measured every line count below
before writing that gate -- `doctor.py` 279, `ledger/checks.py` 288, `ledger/evidence_specs.py`
156, `ledger/render.py` 300, `tests/test_doctor.py` 300 -- and all five matched exactly.

Per this project's hard rule ("a new module is a human gate in this repo") and this
unit's own instruction ("this check should fit inside `doctor.py`; if that file is
near the 300-line cap and genuinely cannot take it, do NOT create a new module —
report HUMAN_GATE with the measured line count and what you considered"):

**Measured, on the current tree (`b3060667`):**

| file | lines | cap | headroom | role |
|---|---|---|---|---|
| `src/autotester/doctor.py` | 279 | 300 | 21 | the check registry `run()` imports into |
| `src/autotester/ledger/checks.py` | 288 | 300 | 12 | the conceptual home — "records" checks that read `docs/`/`qa/` against ground truth, exactly this check's shape (it already hosts `check_qa_issue_rows`, the closest sibling: a citation vs. a ledger row) |
| `src/autotester/ledger/evidence_specs.py` | 156 | 300 | 144 | considered and **rejected** — plenty of headroom, but its module docstring states one job ("does a unit's evidence spec stay runnable"), unrelated to decision citations; adding this there would violate "one concept, one place" and "module docstring states its one job" for headroom alone |
| `src/autotester/ledger/render.py` | 300 | 300 | 0 | the other lazy-import target `doctor.py` already uses; at its own cap |
| `tests/test_doctor.py` | 300 | 300 | 0 | where `doctor.py`-registered checks are tested |
| `tests/test_ledger_checks.py` | 274 | 300 | 26 | where `ledger/checks.py` checks are tested |

The validated implementation (`.work/at710/citations.py`, see below) is **131
lines** of module (regex/glob constants, an 11-row allow-list, four functions), plus
**110 lines** of test (`.work/at710/test_citations.py`, 9 tests). Neither fits in
the 21 lines free in `doctor.py`, nor the 12 free in `checks.py` — the file the
implementation's own doc-comments identify as the conceptual home, matching the
prior cycle's independent conclusion ("checks.py 288/300 is the concept-home,
doctor.py 21 headroom... needs a new module"). Trimming the logic to fit 12–21
lines was not attempted as a serious option: L9 requires (a) two-source header
resolution (`docs/DECISIONS.md` + `docs/archive/*.md`, two different line shapes),
(b) five-glob citation scanning, (c) entry-scoped foreign-id-space exemption with
its own line-grouping pass over `docs/DECISIONS.md`, and (d) a hand-curated,
per-occurrence non-claiming allow-list with reasons — none of that compresses to
single digits of code without becoming unreadable, which is the exact failure mode
C2's caps exist to prevent.

**qa/QUEUE.md's own framing of this item ("pure filesystem code, buildable today,
no human gate") is not correct once actually implemented** — recorded here rather
than quietly overridden, since the queue is not maker-owned ground truth but it is
read by whoever picks the next unit.

**What I am not proposing:** trimming `checks.py` or `evidence_specs.py` by moving
existing code elsewhere just to manufacture room for this unit — that is a separate
refactor with its own blast radius, out of scope for a unit framed as "build the
detector," and exactly the kind of scope-creep a single work unit should not
absorb silently.

**Left for Umesh:** which file hosts `check_decision_citations` — a new
`ledger/citations.py` (mirroring the `checks.py`/`evidence_specs.py` split
precedent, AT-506) is the option I'd take if authorized, since the logic is
self-contained (depends only on `autotester.doctor.Violation` and the stdlib) the
same way `evidence_specs.py` and `checks.py` are. Alternatively, splitting
`checks.py` itself (moving its pytest-`-q` guard functions, which are already the
largest independent cluster in that file, out to make room) is possible but is the
scope-creep case above.

## What was measured and validated (held in `.work/at710/`, gitignored, not committed)

`.work/at710/citations.py` implements `check_decision_citations(root) ->
list[Violation]`, exactly to `qa/contracts/living-ledger.md` L9:

- **Scope (citation sources):** `qa/gates/*.md`, `qa/contracts/*.md`,
  `qa/manifests/*.md`, `qa/verdicts/*.md`, `docs/*.md` — the five globs L9 names,
  non-recursive (so `docs/archive/*.md` and `docs/research/*.md` are resolution
  targets/other docs, not citation sources, per L9's literal text).
- **Citation pattern:** `\bD-\d+\b`. Word-boundaried on both sides so `SD-3`,
  `MD-3` (real strings, `docs/research/crawl-reuse-2026-09.md:11`,
  `qa/manifests/at015-at028-hook-adapter-fix.md:145`) and `ID-040`-shaped tokens
  never match (the digit-adjacent letter kills the left boundary); a range shape
  like `D-008-D-011` or `D-039/D-040/D-041/D-042` (both real, live in
  `qa/gates/at638-...md`) correctly yields each id as its own citation.
- **Resolution:** `docs/DECISIONS.md` `## D-NNN |` headers, union
  `docs/archive/*.md` `D-NNN |` one-line index entries (archiving is not
  deletion — currently an empty set on this tree, since no quarterly archive has
  run yet; covered by a synthetic test, not the live tree).
- **Foreign id-space exemption**, entry-scoped per L9 exactly: `docs/DECISIONS.md`
  is split into `## D-NNN` entries; within an entry, any id that co-occurs on some
  line with a path matching `decisions[/\\]log\.md` (case-insensitive — matches
  the one real instance, `D:/ai_os/umesh/decisions/log.md`, generically enough to
  also cover the shared `D:/ai_os/decisions/log.md`) is exempt everywhere in that
  same entry, not just on the qualifying line.
- **Non-claiming allow-list:** an explicit `(file, line): reason` dict, 11 rows,
  each a real line measured on this tree that quotes or discusses a phantom/foreign
  id without claiming it as a live authorization — never a per-file exemption.

### Measured on the real tree (`b3060667`; 643 files across the 5 globs, ~1406 `D-NNN` occurrences)

**7 real dangling citations — all fire, matching L9's own fixture (c) exactly:**

```
qa/gates/at654-d029-dev-only-vs-production-pathlynks.md:8   D-056
qa/gates/at654-d029-dev-only-vs-production-pathlynks.md:18  D-056
qa/gates/at654-d029-dev-only-vs-production-pathlynks.md:63  D-056
qa/gates/pathlynks-user-account-first.md:31                 D-056
qa/gates/pathlynks-user-account-first.md:35                 D-056
qa/gates/pathlynks-user-account-first.md:38                 D-056
qa/gates/pathlynks-user-account-first.md:67                 D-056
```

**A fourth non-claiming line beyond L9's named fixtures, found by measuring rather
than assuming the fixture list was complete:** `qa/gates/write-policy-tier.md:103`
— *"NOTE: the "D-056" cited elsewhere as authorizing this DID NOT EXIST on disk --
highest decision id was D-055... Filed as a finding."* — a negative statement of
absence, not a claim; added to the allow-list with that reason.

**12 lines correctly exempted** (11 `_NON_CLAIMING` rows in `qa/contracts/living-
ledger.md` and `qa/gates/write-policy-tier.md:103` quoting/discussing `D-056`
and `D-088`, plus `docs/DECISIONS.md:623` and `:638` citing `D-088`, exempted by
the entry-scoped foreign-log rule, not the allow-list).

**Result: exactly 7 violations, 0 false positives, 0 false negatives** against
every occurrence in scope on the live tree — confirmed by
`test_no_false_positive_on_real_decisions` (`len(v) == 7`).

## Capability table (falsifying edit -> observed result, each in `.work/at710/citations.py`, restored after)

Falsified directly in the gitignored scratch copy (nothing tracked was ever
touched — `git status --short` stayed empty for the whole session, confirmed
before and after every mutation). Each mutation: `cp citations.py
citations.py.goodcopy`, edit the one line, run
`uv run pytest .work/at710/test_citations.py -v`, restore with `cp
citations.py.goodcopy citations.py` (never `git checkout --`, since the file
isn't tracked to begin with).

| # | capability | falsifying edit | before | after |
|---|---|---|---|---|
| 1 | detects a real dangling `D-NNN` and reports it | `if cid in headers: continue` → `if True: continue` | 9 passed | **3 failed**: `test_real_d056_citations_all_fire`, `test_no_false_positive_on_real_decisions` (7→0), `test_dangling_id_in_synthetic_repo_fires` |
| 2 | citation regex is word-boundaried, not substring | `_DECISION_ID = re.compile(r"\bD-\d+\b")` → `re.compile(r"D-\d+")` | 9 passed | **2 failed**: `test_id_boundary_does_not_over_match` (SD-3/MD-3/ID-040 now match), `test_no_false_positive_on_real_decisions` (7→11, `SD-` inside other text starts matching) |
| 3 | foreign id-space exemption is entry-scoped, not a no-op | the `is_decisions and any(...)` skip → `if False: continue` | 9 passed | **2 failed**: `test_cross_log_d088_does_not_fire`, `test_no_false_positive_on_real_decisions` (7→9, `docs/DECISIONS.md:623` and `:638` now fire) |
| 4 | non-claiming allow-list actually exempts, not a no-op | `if (rel, lineno) in _NON_CLAIMING: continue` → `if False: continue` | 9 passed | **4 failed**: `test_self_reference_does_not_fire`, `test_cross_log_d088_does_not_fire`, `test_write_policy_tier_absence_line_does_not_fire`, `test_no_false_positive_on_real_decisions` (7→19, all 11 allow-listed + write-policy-tier line now fire) |
| 5 | `docs/archive/*.md` entries resolve (archiving ≠ deletion) | the archive-glob loop → `if False:` (loop body never runs) | 9 passed (this synthetic test isolated) | **1 failed**: `test_archive_entry_resolves` |

Every mutation reproduced exactly, was reverted, and re-verified green (9 passed)
before the next ran; final state confirmed identical to the pre-falsification copy
(no `SABOTAGE` marker left, `git status --short` empty throughout since the whole
exercise lives outside the tracked tree).

## How to verify (commands + actual outputs)

```
$ uv run pytest .work/at710/test_citations.py -v
============================= test session starts =============================
collected 9 items
.work\at710\test_citations.py .........                                  [100%]
============================== 9 passed in 5.53s ==============================

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest
[first run, PIPED to `tail -20` while measuring background-task mechanics — its
reported wrapper exit code is unreliable (AT-692: piping pytest loses its real
exit status to the last pipe stage), so a second, unpiped run followed]
3 failed, 2170 passed, 5 skipped, 14 xfailed, 16 warnings in 2115.16s (0:35:15)
FAILED tests/test_redact_wrap_perf.py::test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus
FAILED tests/test_redact_wrap_perf.py::test_redact_scan_time_roughly_doubles_not_quadruples_with_input_size
FAILED tests/test_ui_runs_serial_entry_mix_live.py::test_a_serial_run_mixing_an_entry_case_with_ordinary_cases_does_not_500

$ uv run pytest > .work/at710/pytest_full.log 2>&1; echo "EXIT_CODE=$?"
[second run, unpiped, authoritative]
1 failed, 2171 passed, 6 skipped, 14 xfailed, 15 warnings in 2362.59s (0:39:22)
FAILED tests/test_redact_wrap_perf.py::test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus
EXIT_CODE=1
```

**Only `test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus` fails on
both runs; the other two (a second perf-timing assertion and a live UI serial-run
test) failed once and passed once** — consistent with timing/environment flakes on
a loaded machine, not a real regression: this cycle touched no file under `src/`
or `tests/` (`git status --short` stayed clean except this manifest for the whole
session). Confirmed unrelated by inspection: none of the three failing test files
import or reference `doctor`, `ledger/checks`, `ledger/render`, or
`ledger/evidence_specs` (`grep -l "doctor\|ledger" tests/test_redact_wrap_perf.py
tests/test_ui_runs_serial_entry_mix_live.py` → no match). The one
consistently-failing test is a wall-clock performance bound
(`test_redact_wrap_perf.py`), pre-existing and orthogonal to this unit's scope.

`.work/at710/*` is gitignored (`.gitignore:10`, `.work/`) and outside `src/`/
`tests/`, so it is invisible to `check_file_sizes`/`check_function_sizes` and to
the tracked-suite `uv run pytest` — both confirmed clean above with no code from
this unit landed anywhere `doctor` or the tracked suite would see it.

`uv run autotester map` not run: no module was added or removed in the tracked
tree (nothing landed there this cycle) — `doctor: clean` already confirms
`check_generated_fresh` sees no drift.

## Known limits / gaps (disclosed, not claimed)

- **Nothing is wired into `doctor.py` or `checks.py`.** This manifest documents a
  validated candidate and a HUMAN_GATE, not a shipped check. `autotester doctor`
  today still does not catch a dangling `D-NNN` citation — AT-710's underlying gap
  is unchanged until the module-placement question is answered and the candidate
  (or a rewrite of it) is actually wired in and its tests moved to a tracked file.
- **Scope is literally the five globs L9 names**, non-recursive. A `D-NNN` cited
  inside `docs/research/*.md`, `qa/issues.jsonl`, `qa/feedback-inbox.md`,
  `qa/QUEUE.md`, `qa/.last-tick`, `CLAUDE.md`, or any `src/`/`tests/` file is
  never scanned — measured false "hits" during design (e.g. `D-056` mentioned in
  `qa/.last-tick`, `qa/feedback-inbox.md`) are correctly out of scope under L9's
  own text, not a gap in the implementation.
- The `decisions[/\\]log\.md` foreign-log pattern is measured against the one real
  instance on disk. It is a generic-enough structural signal (any decisions-log
  path ending `log.md`), not a hardcode of the literal AIOS path, but it has not
  been proven against a second, differently-named foreign log because none exists
  in this repo yet.
- The specific missing `D-056` append (the concrete instance AT-710 names) is a
  separate, classifier-blocked item per `qa/QUEUE.md` and is explicitly **not**
  touched here — no entry was appended to `docs/DECISIONS.md`, consistent with the
  brief ("You are building the detector, not appending any decision entry").
- `qa/contracts/living-ledger.md` was read but not edited (checker-owned); no
  feedback filed to `qa/feedback-inbox.md` this cycle — L9 as written already
  matches the measured shapes exactly (it was itself the product of the earlier
  cycle's feedback and the checker's amendment), so there is nothing new to raise
  against the criterion itself. The one new fact for the checker is the
  `write-policy-tier.md:103` non-claiming line, recorded above, which is a
  measurement not a request to change L9.

## Links

AT-710; `qa/contracts/living-ledger.md` L9 (+ Amendment log entries 2026-09-28
×2); `qa/QUEUE.md` item 3; `qa/gates/at654-d029-dev-only-vs-production-pathlynks.md`;
`qa/gates/pathlynks-user-account-first.md`; `qa/gates/write-policy-tier.md`.

---

## Status: ready-for-check

**Fix cycle:** 1
**Authorization:** `docs/DECISIONS.md` D-058 point 1 (restating D-057; Approved-by: Umesh) lifts the
HUMAN_GATE above: a NEW `src/autotester/ledger/citations.py` and its own test module, for AT-710 only.
The earlier cycle never reached check, so this is cycle 1 of the check loop.
**Persona walk:** skip (doctor check, no UI)
**Live browser:** Not UI-touching.

### What changed (additions only; nothing deleted or renamed)

| file | change | lines |
|---|---|---|
| `src/autotester/ledger/citations.py` | NEW: `appended_ids`, `foreign_ids_by_line`, `check_decision_citations` (+ `_scan`, `_declared`, `NON_CLAIMING`) | 101 / 300 |
| `src/autotester/doctor.py` | `run()`: one import line + one name added to the check tuple | 280 / 300 |
| `tests/test_citations.py` | NEW: 11 tests | 110 |
| `docs/MAP.md`, `docs/SNAPSHOT.md` | regenerated by `autotester map` / `autotester snapshot` (new module) | generated |

One concept, one place: `grep` finds `check_decision_citations` defined only in `citations.py`; the
`.work/at710/citations.py` scratch and the 81-line heuristic there are NOT copied. That draft matched
absence phrases by regex, which L9 forbids ("declared, not inferred"); this module declares every
exemption instead. `tests/test_doctor.py` is untouched (still 300).

Design, all to L9's current text: five citation globs, non-recursive; pattern `\bD-\d+\b`;
resolution by header only (`## D-NNN` in `docs/DECISIONS.md`, `D-NNN |` lines in `docs/archive/*.md`);
foreign id space exempt at ENTRY granularity inside `docs/DECISIONS.md` only, keyed on a
`decisions/log.md` path anywhere in the same entry; non-claiming occurrences are `NON_CLAIMING` rows
`(file, distinctive line text, id) -> reason`, per occurrence, keyed by text rather than line number so
an appended amendment cannot silently un-declare one. No whole-file exemption anywhere.

### Current-tree finding (re-run over the tree at 9daa5a02 + this change)

Raw resolver with an empty allow-list found exactly one id that does not resolve: the AIOS-log id
cited in `docs/DECISIONS.md:623` and `:638` (foreign-log entry rule), `qa/contracts/living-ledger.md`
`:137`/`:229` and this manifest (quotations, 3 declared `NON_CLAIMING` rows). All seven write-policy
citations of the earlier cycle are gone: `D-056` and `D-057` now exist as headers, and 9daa5a02
repointed those gate lines to a `WP-DECISION (NOT YET WRITTEN ...)` placeholder. **Real dangling
citations in the tree: 0. `autotester doctor` is clean.**

### Known gap, disclosed not claimed

L9's added bullet "resolution is necessary and not sufficient" (wrong-subject: compare a citation's
stated authorization against the entry's **What:**) is NOT implemented. Free-text authorization claims
have no machine-readable shape in this tree, and implementing it inferentially is exactly what L9
forbids elsewhere. The Verify clause's three fixtures and the header/archive/foreign/allow-list rules
are implemented; the wrong-subject bullet needs a checker decision on a declarable shape (for example a
`cites-for:` marker) before a maker can build it. Fixture (c) is built with its precondition asserted
at run time (id absent from `appended_ids`) per the 2026-09-29 amendment, not tied to a real id.

### Capability coverage (falsified in a throwaway copy outside the repo, restored, re-run green)

Copy at `<scratchpad>/fz` with `PYTHONPATH=<copy>/src` (import path confirmed to be the copy);
each row is one single-hunk replace in a file listed above; baseline 11 passed.

| # | Capability | Single-hunk edit | PASS before | FAIL after |
|---|---|---|---|---|
| 1 | dangling id reported | `if cid in appended or` -> `if True or` | 11 passed | 6 failed (dangling, header, boundary, foreign, per-file, seven-fire) |
| 2 | word-bounded pattern | `\bD-\d+\b` -> `D-\d+` | 11 passed | 2 failed: `test_the_citation_pattern_is_word_bounded`, `test_the_real_tree_has_no_dangling_citation` |
| 3 | header, not substring | `^##\s+(D-\d+)\b` -> `(D-\d+)\b` | 11 passed | 2 failed: `test_matching_is_by_header_not_by_substring`, `test_a_foreign_id_is_exempt_across_its_whole_entry_only` |
| 4 | archive resolves | `glob("*.md")` -> `glob("*.nomatch")` | 11 passed | 1 failed: `test_an_archived_entry_resolves` |
| 5 | foreign id, entry-scoped | `or (line_no, cid) in foreign or` -> `or False or` | 11 passed | 2 failed: `test_a_foreign_id_is_exempt_across_its_whole_entry_only`, real tree |
| 6 | declared non-claiming exempts | `or _declared(...)` -> `or False` | 11 passed | 2 failed: `test_a_non_claiming_row_is_per_occurrence_never_per_file`, real tree |
| 7 | non-claiming is per occurrence | `and snippet in line for` -> `and True for` | 11 passed | 1 failed: `test_a_non_claiming_row_is_per_occurrence_never_per_file` |
| 8 | exactly the five globs | add `"qa/*.md"` to `CITING_GLOBS` | 11 passed | 2 failed: `test_only_the_five_named_globs_are_citation_sources`, real tree |
| 9 | wired into `autotester doctor` | drop the name from the `run()` tuple in `doctor.py` | 11 passed | 1 failed: `test_doctor_run_includes_the_citation_check` |

Restored copy: 11 passed. Full script and output: scratchpad `fz.py` / `fz.out` (outside the repo).

### How to verify (real outputs, redirected to files, no CLI -q)

```
uv run pytest tests/test_citations.py     -> 11 passed in 0.38s   (EXIT 0)
uv run ruff check src tests scripts       -> All checks passed!   (EXIT 0)
uv run autotester doctor                  -> doctor: clean        (EXIT 0)
```

Before `autotester map` / `snapshot` the doctor reported two `stale-generated` violations (MAP.md,
SNAPSHOT.md) caused only by the new module; both regenerated, then clean.

**Full suite deliberately NOT run** by this maker (RAM ~2.5 GB budget); deferred to the checker.
No senior-software-engineer review dispatched by this seat (instructed not to dispatch a checker).

**Links:** AT-710; D-058; D-057; D-056; `qa/contracts/living-ledger.md` L9; `qa/gates/new-module-authorization.md`.

---

# Cycle 2 — re-check against L9 as narrowed by D-060

## Status: ready-for-check

**Fix cycle:** 2

**Authorized by:** `docs/DECISIONS.md` D-060 (checker, commit `38930b1f`): the wrong-subject bullet moved verbatim out of L9 into new criterion L10 ("not yet buildable: needs a declarable form; own unit"). L9's Verify no longer includes subject match.

**What changed:** no code change. `citations.py`, `tests/test_citations.py` and the 3 `doctor.py` lines are exactly as the cycle-1 checker verified (9/9 capability rows reproduced, 11 passed, ruff clean, doctor clean). The only failure in `qa/verdicts/at710-decision-citation-resolver.md` (ISS-at710-1) was the wrong-subject bullet, which is no longer part of L9. Master merged into this branch so the checker sees the amended `qa/contracts/living-ledger.md`.

**Known gap, now owned elsewhere:** L10 (subject match) is a separate unit with its own task; it is not claimed here.

**Suite:** the full suite is run once by the maker after merge (RAM). Last master full run: 4 failed / 2170 passed, the 4 under isolated re-run.
