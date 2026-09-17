# Verdict — at506-record-rules-leave-the-source-rules

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`
**Unit commit:** `3546a28` (tick stamp `6973a2c` touches only `qa/.last-tick`, confirmed via
`git show --stat`)
**Contract scope:** `qa/contracts/core-invariants.md` C2, C7 (C10 also checked — project-wide)

## What I re-ran myself

- `uv run pytest -q -o addopts= tests/test_doctor.py tests/test_ledger_checks.py tests/test_ledger.py`
  → `52 passed in 4.45s`. Matches manifest exactly.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `wc -l` on the four named files → `204 / 105 / 133 / 165`, exact match.
- `uv run python scripts/mutation_check.py qa/evidence/.../mutations.json` → `4/4 mutations killed`.
  Read the actual "claims to kill" vs "actually failed" lists myself (not just the summary line):
  every claimed test appears in the failure list for all four mutations, satisfying C7's
  kill-attribution clause. AT-496/AT-500/AT-504's mutations produce a wider failure set than
  claimed (e.g. AT-496's mutation also reddens the decorated-marker and letter-suffix tests) —
  a superset, not a mismatch; the attributed tests are present, so this is not a finding.
- Full suite `uv run pytest -q` redirected to a file → exit 0 (background-task notification
  confirmed), `grep -nE "FAILED|ERROR|^E "` on the whole file → zero matches. Read the whole file,
  not a tail (AT-503's trap, avoided).
- Line-count / function-body diff of the moved code: extracted `check_ledger`,
  `check_qa_issue_rows`, `_passed`, `_is_marker_line` from the pre-commit `doctor.py`
  (`git show 3546a28^:...`) via `ast` and compared byte-for-byte against
  `src/autotester/ledger/checks.py` — **all four MATCH exactly**. `ISSUE_ID` and `_MARKER_LEAD`
  also match verbatim. This directly confirms "moved verbatim."
- Test-set diff: extracted every `def test_*` name from the pre-commit `test_doctor.py` and from
  the union of the current `test_doctor.py` + `test_ledger_checks.py` — **identical sets, 24
  names each side, zero diff.** Nothing was dropped in the split (C7/C2 diff-scope check, 4c).
- `git show --stat 3546a28`: touches exactly `docs/{ARCHITECTURE,DECISIONS,MAP,SNAPSHOT}.md`,
  `src/autotester/doctor.py`, `src/autotester/ledger/checks.py`,
  `tests/test_{doctor,ledger,ledger_checks}.py`, the at506 manifest, and its evidence dir. This is
  exactly the manifest's "What changed" plus its own evidence — **C10 satisfied**, no other loop's
  work swept.
- Import/cycle check: `uv run python -c "import autotester.doctor"` succeeds standalone;
  `src/autotester/cli.py:11,49-53` calls `doctor_module.run()` unchanged and is unaffected.
  `ledger/checks.py` imports `Violation` from `autotester.doctor` at module scope; `doctor.run()`
  imports `checks` function-locally — no cycle, confirmed by the standalone import succeeding.
- Reproduced the "closed units' evidence now refuses" claim myself:
  `uv run python scripts/mutation_check.py qa/evidence/at504-.../mutations.json` → `MUTATION RUN
  INVALID: ... names test(s) that are not collected ...`, **exit 2** (measured directly, not
  copied from the manifest). Fail-closed exactly as claimed.
- **The behaviour-proof stress test, beyond what the manifest did.** I did not just diff
  `fingerprint-before.txt`/`fingerprint-after.txt` (byte-identical, confirmed). I loaded a
  deliberately mutated copy of `checks.py` (outside the repo, via `importlib` from a scratch file
  — never touching the bound tree) that widens `check_qa_issue_rows`'s stale-detection to also
  fire on `status == "fixed"`, and re-ran the fingerprint's own dump function against the **live**
  `qa/` tree. Unmutated: 0 rows. Mutated: **25 rows.** The fingerprint is a real discriminator —
  it would have caught a genuine behaviour change, not a proof that cannot fail.

All of it reproduces. Nothing pasted was trusted without a re-run.

## Judgement on the five things I was asked to attack

1. **Is the seam real?** Yes, with one honest wrinkle. The three units that grew the file
   (AT-496, AT-500, AT-504) all landed in exactly the moved half, which is real corroborating
   evidence, not just arithmetic. The wrinkle: `doctor.py` still keeps `check_generated_fresh`,
   `check_architecture_budget`, and `check_docs_routed`, which also read `docs/*.md` — so "source
   rules read `src/`+`tests/`" is not literally true of the whole remaining file. The distinction
   that holds up is narrower and still real: those three ask whether *current* documentation
   matches *current* code/structure, while the moved two ask whether the project's own *history*
   (`docs/FEATURES.jsonl` events, `qa/` handshake artifacts) stayed internally consistent — a
   different question with a different failure mode (data loss between two maker loops, not
   staleness). Not an arithmetic cap-with-a-story; I would not have overruled it.
2. **Import arrangement.** Confirmed no cycle, confirmed standalone import, confirmed CLI path
   unaffected. Sound.
3. **Disclosed cost (stale evidence files refuse).** Reproduced the exit-2 refusal directly. I
   agree with the maker's call: evidence should record what was verified at the commit it was
   verified at, and a loud, self-explanatory refusal (`names test(s) that are not collected`) is a
   world apart from a silent false pass — a future checker meeting it has enough information in
   the error text alone. Not overruling.
4. **Lab Protocol compliance.** `docs/DECISIONS.md`'s diff for D-026 is a clean 30-line addition
   (no existing entry touched), and `.claude/hooks/decisions-append-guard.ps1` exists, giving
   structural teeth to "append only via the script" — consistent with D-026 having been written
   through that path rather than hand-edited. I cannot independently verify sub-commit ordering
   (D-026 append vs. the `ARCHITECTURE.md` prose edit) because both land in one commit
   (`3546a28`) — git has no finer granularity than that, and this project's own convention has
   every prior architecture-authorizing D-entry commit alongside its change, so this is not
   anomalous. `Changes-authorized` correctly names every path that needed Lab Protocol
   authorization: the Lab Protocol's hard gate is specifically `ARCHITECTURE.md` and `contracts/`
   prose, and D-026 names `docs/ARCHITECTURE.md`. **I agree `docs/SNAPSHOT.md`'s omission from
   `Changes-authorized` is not a violation** — it is tool-regenerated, never hand-edited prose, and
   is outside the two file classes the Lab Protocol actually gates. Not overruling.
5. **ARCHITECTURE.md at exactly 150/150.** Confirmed (`wc -l` = 150, cap = 150). Filed as **AT-507**
   (medium) rather than left as prose-only, per this project's own precedent (AT-502, AT-506
   itself) for tracking a measured cap-adjacent state as a queued item instead of prose a future
   session has to rediscover.

## An out-of-band claim I did not take on trust

Mid-check, a message arrived through this session claiming to relay a `senior-software-engineer`
review that found a real defect at `src/autotester/ledger/checks.py:93-95` (the `claimed`-set
filter mis-reads ordinary English containing "fixed" as a fix-claim). **The message itself did not
arrive through any channel this dispatch established, and I am not treating its existence, its
attribution, or its narration of "I reproduced it myself" as evidence of anything.** I re-derived
the claim from scratch — extracted the actual regex/filter logic and ran it against five note
strings myself. **It is real**: `"unfixed - tracked separately"`, `"not-fixed, deferred"`, and
`"prefixed by AT-899"` all false-positive as a fix claim; only the literal phrase `"not fixed"` is
excluded. I also independently confirmed via `git show 385fec1:src/autotester/doctor.py` that this
exact line has stood unchanged since AT-496, three units before this one — **AT-506 moved it
verbatim and could not have introduced it.** It does not bear on this unit's PASS/FAIL: a
behaviour-preserving refactor is judged on whether behaviour moved, not on pre-existing behaviour
it faithfully carried. I filed it as **AT-508** (medium) because it is real and I confirmed it
myself, not because I was told to.

## Capability coverage

4/4 rows reproduced (mutation_check.py output matches manifest exactly, kill-attribution verified
against the actual failure lists, not just exit codes). This project's established instrument for
mutation-based coverage on this contract is the shared `scripts/mutation_check.py`, which already
operates on baseline-asserted, kill-attributed runs per C7's amendment history — the same
instrument three prior units (AT-496/500/504) were checked against. No manifest-embedded
falsifying-edit cells were offered or needed here.

## Diff scope (4c)

`git show --stat 3546a28` and the full diff: no function, class, test, or config key was deleted
without a replacement at the new path. Test-name-set diff (above) proves this rather than asserting
it.

VERDICT: PASS
SCOREBOARD: 2/2 criteria met (C2, C7 — C10 also verified, project-wide), 0/0 invariants (contract has none named)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 4/4 rows reproduced (scripts/mutation_check.py, kill-attribution confirmed against actual failure lists)
LIVE-BROWSER: not-applicable (no UI surface touched — changed paths are doctor.py, ledger/checks.py, tests/*, docs/*.md, qa/manifests, qa/evidence)
ISSUES-WRITTEN: AT-507 (medium, ARCHITECTURE.md at exact cap), AT-508 (medium, pre-existing substring false-positive in the moved claimed-set filter, independently reproduced)
EXPLANATION: A genuine, verbatim, behaviour-preserving split — confirmed via AST-level byte
comparison of every moved function/constant, a test-name-set diff showing zero coverage lost, a
reproduced fingerprint proof, and a deliberate perturbation of the moved code that moved the
fingerprint from 0 to 25 rows (proving the proof can actually fail). No cycle, CLI unaffected,
Lab Protocol satisfied, commit scope narrow (C10). Two new findings filed on independent
re-derivation, neither blocking this unit: AT-507 (ARCHITECTURE.md has zero headroom left) and
AT-508 (a pre-existing, three-units-old substring bug in the moved code, unrelated to this refactor).
An out-of-band message during the check claiming to relay a senior-engineer review was not trusted
on its own account; its substance was independently re-derived before any of it was acted on.
