# Verdict — t120-bench

**Unit:** t120-bench · **Goal task:** T-120 (final task, entire P0–P5 backlog)
**Contract:** qa/contracts/bench.md (K1–K5) · **Rubric:** .goal/rubrics/T-120.md
**Cycle checked:** 1

## Verdict: PASS

This is the final task in the project's entire goal backlog. On this PASS, the whole backlog
closes.

## Evidence per criterion

### K1 / rubric-1 — real seeded corpus with genuine ground truth
`projects/regression-demo/bench/corpus_regression_demo_login.json` (read from disk):
```
"seeded_bugs": [{"id": "bug_login_password",
  "description": "Login rejects the correct password (pass123 -> pass124 typo)",
  "severity": "S1", "location": "/login.html",
  "detect_hint": "Login with correct credentials should succeed but shows an error"}]
```
Verified this is a real, restorable regression, not a placeholder:
- `tests/fixtures/regression_site/login.html` currently reads `password === 'pass123'`
  (`grep "password ===" tests/fixtures/regression_site/login.html`).
- `git status --porcelain tests/fixtures/regression_site/login.html` → empty output — fixture is
  unmodified from tracked state, confirming the trial's copy/restore-in-`finally` (`scripts/
  bench_trial.py:122-144`) genuinely round-tripped the seeded bug rather than leaving it in place.
PASS.

### K2 / rubric-2 — a real AutoTester trial through a real, non-mock judge
`scripts/bench_trial.py::run_and_grade` (lines 94-102) calls the unmodified `stages/execute.py::
run_case` and `stages/grade.py::grade` against a real `BrowserSession` and a real
`LangChainFallbackProvider` instance (`judge = LangChainFallbackProvider()`, line 120).
Read the actual persisted Verdict from the real run:
`projects/regression-demo/runs/run-bench-01M1KEDYFM06WE4JMS941TEB0S/case_63fc83d8ad81.verdict.json`
→ `"result": "FAIL"`, `"grader_provider": "gemini"` (a real vendor, not a mock), with a real
`failures[0].evidence_refs: ["#result text: 'Invalid credentials'"]`. The second case's verdict
(`case_faa8a0dab9d2.verdict.json`) → `"result": "PASS"`, also `"grader_provider": "gemini"`.
`findings_from_verdicts` (`src/autotester/stages/bench.py:15-34`) converts these mechanically:
FAIL → Finding with `matched_bug_id` from `case_bug_map.get(verdict.case_id)`, no hand-adjustment
after the run. The saved AI trial (`trial_ai_01M1KEEBRGA8B4BXCBAG98MDG6.trial.json`) matches the
verdict's own failure text and evidence_refs verbatim. PASS.

### K3 / rubric-3 — scoring only via `BenchTrial.score`, never hand-computed
`stages/bench.py::scorecard` (lines 66-72):
```python
def scorecard(corpus: BenchCorpus, trials: list[BenchTrial]) -> dict[str, dict[str, float]]:
    return {
        trial.participant_label or trial.participant.value: trial.score(corpus)
        for trial in trials
    }
```
This is the only place `.score(` is invoked in `stages/bench.py` or `scripts/bench_trial.py`.
Grepped both files for hand-computed rate arithmetic (`detection_rate`, `false_positive_rate`,
`severity_weighted_recall`, division patterns like `/ len(`, `matched)/`, `/ (len`) — zero matches
in either file; those symbols exist only inside `BenchTrial.score` itself
(`src/autotester/schema/bench.py:58-75`). `scripts/bench_trial.py:171` calls `bench.scorecard(...)`
and only prints the dict — no recomputation. `tests/test_bench.py::
test_scorecard_calls_bench_trial_score_for_every_trial` (lines 77-86) equality-asserts
`card["autotester-real-run"] == ai.score(corpus)` and the same for the human trial — passing.
PASS.

### K4 / rubric-4 — comparative scorecard naming both participants
Manifest's cited run output and the independently re-read persisted trial JSON both show two
entries, one per `Participant`:
- `trial_ai_...trial.json`: `"participant": "autotester"`, `"participant_label":
  "autotester-real-run"`
- `trial_human_...trial.json`: `"participant": "human"`, `"participant_label":
  "human-oracle-baseline"`
`scorecard(corpus, [ai_trial, human_trial])` (bench_trial.py:171) produces both side by side in
one dict, printed together. PASS.

### K5 — persisted as real ProjectStore artifacts
`src/autotester/core/paths.py:84-91` — `bench_dir`, `bench_corpus(id)`, `bench_trial(id)`, all
wired into `ProjectPaths.ensure()` (line 110), matching every other artifact-kind path in the
file. `src/autotester/store/project_store.py:112-129` — `save_bench_corpus`, `load_bench_corpus`,
`save_bench_trial`, `list_bench_trials`, using the file's existing `write_json`/`read_json`
helpers, no new file format. Confirmed on disk (not asserted, actually `ls`'d and `cat`'d):
`projects/regression-demo/bench/corpus_regression_demo_login.json`,
`trial_ai_01M1KEEBRGA8B4BXCBAG98MDG6.trial.json`,
`trial_human_01M1KEEBRGKPSH6V6TTAV41W4K.trial.json` — three real plain-JSON files, all schema-
versioned Pydantic `Artifact` dumps, not throwaway objects. PASS.

### rubric-5 — honest labeling
`participant_label == "human-oracle-baseline"` appears identically in:
`stages/bench.py::oracle_human_trial` (line 62), the saved trial JSON
(`trial_human_...trial.json`), the contract's Purpose section, the manifest, and the script's
docstring (`scripts/bench_trial.py:6-8`: "documented oracle baseline, not a live timed trial").
No file, comment, or print statement anywhere claims a live/timed human run. `duration_s: 300.0`
for the human trial is clearly a placeholder oracle duration, not dressed up as measured timing.
PASS.

## Independent command re-runs (not trusted from the manifest — reproduced myself)

| Command | Result |
|---|---|
| `uv run pytest tests/test_bench.py -v` | `6 passed in 0.08s` — matches expected |
| `uv run pytest -q --no-header -p no:cacheprovider` | exit 0, no failures, no errors (2 skipped, consistent with pre-existing skips elsewhere in the suite) |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `wc -l docs/ARCHITECTURE.md` | `149` (≤150 cap) |
| `git status --porcelain tests/fixtures/regression_site/login.html` | empty — fixture restored |
| grep for hand-computed rate arithmetic in `stages/bench.py` / `scripts/bench_trial.py` | zero matches outside `BenchTrial.score` |

Did not re-run `scripts/bench_trial.py` live (would spend a real Gemini network call + spin up a
real headed browser); the saved RawResult/Verdict/Trial JSON on disk, independently read and
cross-checked field-by-field above, already establishes K1–K5 without re-incurring that cost. This
matches the manifest's own framing of the live re-run as encouraged, not mandatory.

## No-fire items respected

No live timed human trial (correctly out of scope, honestly labeled). No multi-corpus/leaderboard
scope creep. No CI wiring added. All consistent with the contract's no-fire list.

## Overall

All 5 contract criteria (K1–K5) and all 5 rubric criteria are satisfied on cited, independently
verified evidence — real files read from disk, real commands re-run with matching output, real
grep checks for the no-hand-computation requirement. **This unit PASSes.**

**This closes the entire T-120 unit and, per the manifest, the whole P0–P5 goal backlog
(`.goal/goal.json` progress → 20/20).**
