# Contract — Bench (T-120)

**Covers:** goal task T-120 (final task in the P0-locked backlog). **Owner:** /checker.
**Criticality:** HIGH — T-120's own note: "North star made measurable. Scorecard computed by
`BenchTrial.score`, never by hand." This is the literal implementation of the project's stated
north star: "an expert human tester and AutoTester get the same material and the same build;
AutoTester wins on bugs found, false positives, and time."
**Depends on:** `execute.md`/`grade.md` (the pipeline a trial runs), `regression-proof.md` (the
fixture corpus reused here), `langchain-fallback.md` (the real judge).

## Purpose

Make the north star measurable: given a build with known, seeded defects (`BenchCorpus`), score
one or more participants' attempts (`BenchTrial`) on detection rate, false-positive rate, and
severity-weighted recall — via `BenchTrial.score`, never a hand-typed number. Prove this with a
real trial, not a description of one.

**Honest scope note (same discipline as T-050/T-060/T-110):** a live, timed human tester was not
available in this autonomous session. The AutoTester side of the scorecard is a **real** trial —
the actual execute→grade pipeline run against a genuinely broken build, real `Verdict`s, real
`grader_provider`. The human side is an explicitly labeled **oracle baseline** (perfect precision
and recall against the corpus's own seeded bugs, `participant_label="human-oracle-baseline"`) —
not a fabricated claim of a timed human run. This is documented here and in every manifest/run
output, never presented as a live trial.

## Criteria

### K1 — `BenchCorpus` with real seeded ground truth
A corpus is built from a real, deliberately-broken fixture (the same class of regression as
T-110's `tests/fixtures/regression_site/`), with `seeded_bugs` describing a real, verifiable
defect (`location`, `detect_hint`, `severity`) — not a placeholder.

### K2 — A real AutoTester trial
`run_autotester_trial` (or the calling script) runs the unmodified `stages/execute.py::run_case` +
`stages/grade.py::grade` pipeline, through a real, non-mock judge (`LangChainFallbackProvider`),
against the corpus's broken build, and converts the resulting `Verdict`s into `Finding`s —
`matched_bug_id` set only when the failing case's mapped location is a seeded bug, `None`
(false positive) otherwise. No verdict content is invented or hand-adjusted after the run.

### K3 — Scoring goes through `BenchTrial.score`, never by hand
`stages/bench.py::scorecard(corpus, trials)` calls `trial.score(corpus)` for each trial and
returns exactly that — no parallel hand-computed detection-rate/FP-rate arithmetic anywhere in
the calling script or the manifest.

### K4 — The scorecard is comparative
The final output names both participants (`Participant.AUTOTESTER` and `Participant.HUMAN`) and
their scores side by side — this is the "expert human tester and AutoTester get the same
material" comparison the north star asks for, even though (per the Purpose's honest scope note)
one side is a documented oracle baseline rather than a live run.

### K5 — Persisted as real artifacts
The corpus and each trial save through `ProjectStore` (a new `save_bench_corpus`/
`load_bench_corpus`/`save_bench_trial`/`list_bench_trials`, following the exact pattern of every
other artifact kind in that file) — plain JSON files under `projects/<slug>/bench/`, not
throwaway in-memory objects.

## No-fire list

- A live, timed human trial — explicitly out of scope this cycle (no tester available); the
  oracle-baseline substitution is the documented, honest alternative (see Purpose).
- Multi-corpus benchmarking, leaderboards, or a bench UI page — out of scope; one real corpus,
  one real comparison, is the bar for this unit.
- CI wiring to run bench automatically — future enhancement, not required here.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-120 — no contract existed before this cycle.
