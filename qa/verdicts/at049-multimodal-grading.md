# Verdict — at049-multimodal-grading

**Date:** 2026-09-04
**Cycle checked:** 1
**Contract:** qa/contracts/grade.md (+ qa/contracts/browser-and-secrets.md B7, unaffected)
**Manifest:** qa/manifests/at049-multimodal-grading.md
**Project root:** D:/autoTesting

## What I re-ran myself (not trusted from the manifest)

1. `uv run pytest -q` → full suite green (76 passed, 2 skipped), no regressions.
2. `uv run ruff check src tests scripts` → All checks passed!
3. `uv run autotester doctor` → doctor: clean.
4. Read `src/autotester/providers/langchain_fallback.py::_message` in full: confirmed it builds a
   genuine LangChain multimodal message — `content = [{"type":"text",...}] + [{"type":"image_url",
   "image_url":{"url":"data:image/png;base64,<real base64 of path.read_bytes()>"}}]` for each
   existing image path — and returns `[HumanMessage(content=content)]` (a **list**), not a bare
   `HumanMessage`. `_try_tier` calls `model.invoke(_message(prompt, images))`, so `.invoke()`
   genuinely receives a `list[BaseMessage]` when images are given, and the original prompt string
   unchanged when they are not. This is exactly the bug the manifest says its own build hit and
   fixed (bare `HumanMessage` → 500) — confirmed the fix is in place, not just claimed.
5. Read `src/autotester/providers/anthropic.py::_structured`: confirmed real Anthropic native
   image content blocks (`{"type":"image","source":{"type":"base64","media_type":"image/png",
   "data":base64.b64encode(path.read_bytes())...}}`), filtered to `path.exists()`, appended before
   the text block, sent as `messages=[{"role":"user","content":content}]`.
6. Read `src/autotester/providers/gemini.py::_structured`: confirmed real image attachment via
   `client.files.upload(file=str(path))` for each existing image path — same mechanism `see_video`
   already used for video, appended to `contents` before the prompt string.
7. Read `src/autotester/stages/grade.py::_screenshot_paths`: confirmed it resolves every
   `EvidenceKind.SCREENSHOT` entry to `run_dir / ev.path` (a real file path under the given
   `run_dir`), returns `[]` when `run_dir is None` (no crash, old text-only behavior preserved).
   `grade()` passes `judge.judge(prompt, Judgment, images=_screenshot_paths(result, run_dir))`.
8. Read `src/autotester/stages/run_case_pipeline.py::run_and_grade_case`: confirmed it calls
   `grade(rubric, result, run_id, judge, run_dir=store.paths.run_dir(run_id))` — a real, non-None
   run_dir, not a placeholder — this is the one path the UI Run button and any generic caller use.
9. **Live Docker verification, independently executed, not reused from the manifest's pasted
   output:** restarted the container (`docker compose restart`), polled `curl
   http://localhost:8010/` until 200 (2 attempts), then issued **my own 3 fresh
   `POST /projects/pathlynks/run` calls** (all `303`, none reused from the manifest's 5 runs).
   Result directories: `run-01M1PFRS3G6QR3Q3SSD3Q8469G`, `run-01M1PFSSQCNK5ES2XBWWT33AMK`,
   `run-01M1PFTW67V1E82RR1EDS150HA` — **9/9 case verdicts PASS** (3 cases × 3 runs), all
   `grader_provider: "gemini"`.
10. Read one real verdict (`case_a5ea57c0961a` / WORST, run `...TW67V1E82RR1EDS150HA`) in full:
    `note: "The login attempt was successfully rejected as evidenced by the error state shown in
    04-step04-click.png."` — a specific claim about visible content, not a generic
    "insufficient evidence" hedge. Then **read the actual screenshot file
    `04-step04-click.png` from that same run directory directly** (not docker cp — the project
    mount is directly visible) — it genuinely shows red "Invalid credentials" text on the
    Pathlynks sign-in form. The verdict's reasoning matches the image's real content precisely.
    A second case in the same run (`case_b1cb019ebb56` / EDGE) noted "Validation messages
    appeared and blocked the empty form submission" — also a specific, plausible visual claim.
11. Confirmed the 3 untouched scripts (`scripts/regression_proof.py`, `scripts/bench_trial.py`,
    `scripts/run_pathlynks_first_cases.py`) still call `grade(rubric, result, run_id, judge)` with
    no `run_dir` argument — `grade()`'s `run_dir: Path | None = None` default means
    `_screenshot_paths` returns `[]` for them, `judge.judge(prompt, Judgment, images=[])` behaves
    identically to the pre-fix call. This is a deliberate, documented, backward-compatible scope
    decision, correctly not flagged as a gap.
12. Grepped the new tests directly (not just trusted the manifest's bullet list):
    `tests/test_grade.py` asserts `judge.judge_images == [[run_dir / "01-login.png", ...]]` and a
    separate test asserts `judge.judge_images == [[]]` when `run_dir` is not given;
    `tests/test_langchain_fallback.py` asserts the sent message's `content[1]["type"] ==
    "image_url"` and its `image_url.url` starts with `"data:image/png;base64,"`, plus a
    plain-string-when-no-images test and a missing-file-is-filtered test;
    `tests/test_run_case_pipeline.py` asserts `judge.judge_images == [[run_dir /
    "01-step01-navigate.png"]]`. These genuinely exercise the real attachment path, not just the
    plumbing around it.

## Criteria (qa/contracts/grade.md)

- **G1** (stateless, evidence-only judge) — MET. `grade()` still takes only `Rubric`, `RawResult`,
  `run_id`, `Provider` (+ optional `run_dir`); `build_grade_prompt` still builds from rubric +
  evidence only. Attaching real image bytes for evidence the judge was already told about (by
  filename) is not new case/script leakage — verified no `Case`/`Script` import was added to
  `grade.py`.
- **G2** (deterministic outcomes never reach the judge) — MET, unchanged code path verified by
  reading `grade()`: `BLOCKED_HITL`/`ERRORED` still short-circuit before `judge.judge(...)` is
  ever called.
- **G3** (PASS requires cited evidence; inconsistency downgrades to INCONCLUSIVE) — MET, unchanged
  `_inconsistency` logic verified by reading it in full; not touched by this fix.
- **G4** (Verdict complete and persisted) — MET. All 9 live verdicts from my own reruns have
  `run_id`, `case_id`, `result`, `grader_provider`, `rubric_hash` populated; `.verdict.json` is a
  distinct file per case, separate from `.json` (RawResult), confirmed by directory listing.
- **G5** (prompt is a file, not inline) — MET, unchanged: `build_grade_prompt` still reads
  `prompts/grade_v1.md`; no prompt text was inlined by this fix.

**Contract amendment:** added a routine amendment to `qa/contracts/grade.md`'s log (2026-09-04)
making G1's "the judge sees real evidence, not just its label" spirit explicit — per the manifest's
own invitation and the checker's sole-writer role over contracts. Routine gate (clarifies, does
not weaken); no criticality escalation needed.

## Issues

- Verified AT-049 (critical) genuinely fixed — closing the loop the manifest opened. Real image
  bytes are attached in all three providers; `run_dir` threads through the one generic pipeline;
  9/9 live PASS across my own independent reruns; one verdict's note independently confirmed
  against the real screenshot pixel-for-pixel.
- AT-046 (medium, residual grading flakiness) — manifest and ledger both mark it superseded by
  AT-049's real root cause, not by further settle()-tuning. Consistent with the evidence: 9/9 PASS
  this check, versus the pre-fix flaky pattern documented in AT-046's own ledger row.
- **New finding (low, self-resolved same cycle):** `qa/issues.jsonl`'s AT-049 row was stamped
  `verified_date: "2026-09-04"` by the maker before any checker verdict existed for this unit —
  only `/checker` should set `verified_date`. No behavior/code impact, and the stamp is now
  genuinely correct (this verdict is the actual verification), but the sequencing violated
  segregation of duties. Filed as **AT-050** (low, status: fixed — the sequencing gap closes with
  this verdict landing; no further action needed unless it recurs).

## Scope decision confirmed

`scripts/regression_proof.py`, `scripts/bench_trial.py`, `scripts/run_pathlynks_first_cases.py`
deliberately not migrated — confirmed genuinely backward-compatible (default `run_dir=None` →
empty images list → identical pre-fix behavior), not an oversight.

---

VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 5/5 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-050
EXPLANATION: Read every changed provider/stage function myself and confirmed each genuinely
attaches real image bytes (LangChain multimodal message as a list, Anthropic base64 image block,
Gemini file upload) rather than only describing screenshots in text. Independently ran 3 fresh
live Docker reruns against Pathlynks (9/9 case verdicts PASS, not reused from the manifest's own
evidence), and independently read a real screenshot file that matches its verdict's note almost
verbatim. The 3 untouched scripts remain correctly backward-compatible. Added one low-severity
ledger-hygiene issue (AT-050) for a premature `verified_date` stamp, self-resolved by this verdict
landing, and one routine contract amendment making G1's evidence-attachment spirit explicit.
