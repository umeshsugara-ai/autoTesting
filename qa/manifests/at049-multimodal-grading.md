# Manifest — at049-multimodal-grading

**Contract:** qa/contracts/grade.md (unchanged criteria text — a correctness fix, not a
reinterpretation) + qa/contracts/browser-and-secrets.md B7 (screenshots already masked before
capture, unaffected — the judge now sees the same masked image a human would)
**Goal task:** none (`.goal/goal.json` is 20/20 done — discovered while investigating AT-046)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-049 (fixed, critical), AT-046 (fixed — superseded, real root cause)

## Why this unit

Investigating AT-046 (residual grading flakiness for the wrong-password case) led to a much
bigger discovery: `stages/grade.py` has **never** attached real screenshot images to the judge
call. A screenshot pulled and visually inspected (`Read` tool) clearly showed "Invalid
credentials" in red text; the judge still said "no evidence of rejection" — because it had never
seen the image, only its filename. Confirmed by reading `providers/langchain_fallback.py`'s
`_try_tier`: `model.invoke(prompt)` with `prompt` as a bare string, no multimodal content
anywhere. Same gap in `providers/gemini.py` and `providers/anthropic.py`. This affects every
`Verdict` this system has ever produced, not just Pathlynks — asked Umesh how to proceed
(`AskUserQuestion`); chose "fix now."

## What changed

- `src/autotester/providers/base.py` — `Provider.judge()` gains `images: list[Path] | None = None`.
- `src/autotester/providers/mock.py` — `MockProvider.judge()` accepts and records `images` (as
  `judge_images`, a new list attribute) for test introspection.
- `src/autotester/providers/anthropic.py` — `judge()`/`_structured()` attach real images via
  Anthropic's native `{"type": "image", "source": {"type": "base64", ...}}` content block,
  skipping any path that doesn't exist on disk.
- `src/autotester/providers/gemini.py` — `judge()`/`_structured()` attach real images via
  `client.files.upload()`, the same mechanism `see_video` already used for video — reusing a
  proven pattern, not inventing a new one.
- `src/autotester/providers/langchain_fallback.py` — new `_message(prompt, images)` helper:
  returns the plain prompt string when there's nothing to attach (byte-identical behavior for
  every existing caller — `act()`, and any `judge()` call with no images), or a real LangChain
  multimodal `[HumanMessage(content=[...])]` (text block + `image_url` data-URI blocks) when
  there are real files to attach. `.invoke()` requires a str/PromptValue/`list[BaseMessage]` — a
  bare `HumanMessage` is none of those (a real bug this unit's own build hit and fixed, see
  below).
- `src/autotester/stages/grade.py` — new `_screenshot_paths(result, run_dir)`: resolves every
  `SCREENSHOT`-kind evidence entry to a real file path under `run_dir`. `grade()` gains an
  optional `run_dir: Path | None = None` param, passed straight through to
  `judge.judge(prompt, Judgment, images=_screenshot_paths(...))`. `run_dir=None` (any caller not
  yet updated) reproduces today's exact text-only behavior — no crash, no behavior change.
- `src/autotester/stages/run_case_pipeline.py` — `run_and_grade_case` (the one path a UI Run
  button or CLI script calls) now passes `store.paths.run_dir(run_id)` through to `grade()`.
- Tests: `tests/test_grade.py` (+2), `tests/test_langchain_fallback.py` (+3),
  `tests/test_run_case_pipeline.py` (+1) — real image attachment, existence-filtering, and
  end-to-end wiring from `run_and_grade_case` down to the judge call.
- `tests/test_browser_settle.py` (new) — the AT-045/AT-046 `settle()` tests moved out of
  `test_browser.py` to stay under the 300-line design limit once this cycle's cases.jsonl
  investigation and other work landed alongside them (pure file split, no behavior change).
- `projects/pathlynks/cases.jsonl` — populated `expected.visible_text` on the login-submit
  `CLICK` step for all 3 real cases, from live investigation against the actual Pathlynks
  product (not guessed): BEST → `"YOUR PROGRESS"` (the real post-login dashboard panel text),
  WORST → `"Invalid credentials"` (the real rejection message), EDGE → `"is required"` (the real
  client-side validation text). This lets `BrowserSession.settle()` (AT-045/046, already shipped
  this session) poll for the real, specific signal each case expects rather than a generic
  timing guess — a necessary companion to this fix: correct evidence *timing* and a judge that
  actually *sees* the evidence are two different, both-necessary problems.

## A real regression this unit's own build caught and fixed before shipping

The first version of `_message()` returned a bare `HumanMessage(content=[...])`. Live-testing
against Pathlynks immediately 500'd: `ValueError: Invalid input type <class
'langchain_core.messages.human.HumanMessage'>. Must be a PromptValue, str, or list of
BaseMessages.` — LangChain's `.invoke()` does not accept a bare message object. Fixed by wrapping
it in a list (`[HumanMessage(...)]`), confirmed against the real Gemini API, and updated the unit
test's assertions to match the corrected return shape.

## Deliberate scope decision

`scripts/regression_proof.py`, `scripts/bench_trial.py`, and `scripts/run_pathlynks_first_cases.py`
call `grade()` directly and were **not** updated to pass `run_dir` in this cycle —
`run_dir` is optional and defaults to `None` (today's unchanged text-only behavior), matching
this project's established precedent (`run-case-pipeline.md`'s own manifest) of not migrating
those 3 already-checker-PASSed scripts. Each remains exactly as reliable/unreliable as it was
before this fix; only the generic pipeline (`run_and_grade_case`, what the UI Run button and any
future generic caller use) gets the real fix.

## Real verification performed (not simulated)

```
$ uv run pytest -q                        # full suite green, no regressions
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

**Real live Docker verification against the real Pathlynks product — the actual claim this unit
makes, proven by determinism, not a single lucky run:**

```
$ docker compose restart && curl http://localhost:8010/   # 200
$ for i in 1 2 3 4 5; do curl -sX POST http://localhost:8010/projects/pathlynks/run; done
run 1: 303 · run 2: 303 · run 3: 303 · run 4: 303 · run 5: 303
```

| Run | BEST | WORST | EDGE |
|---|---|---|---|
| run-01M1PFH7… | PASS | PASS | PASS |
| run-01M1PFG5… | PASS | PASS | PASS |
| run-01M1PFF1… | PASS | PASS | PASS |
| run-01M1PFDZ… | PASS | PASS | PASS |
| run-01M1PFCS… | PASS | PASS | PASS |

**5/5 runs, all 3 cases, PASS every single time** — versus the pre-fix pattern of
PASS/FAIL/INCONCLUSIVE varying run to run for identical code. Verdict notes now genuinely
describe visual content that matches the real screenshots:
- BEST: *"The user successfully navigated to the login page, entered credentials, and submitted
  the form, resulting in a successful login message and user dashboard."*
- WORST: *"The login attempt with a wrong password was successfully rejected, displaying an
  error message."*
- EDGE: *"Client-side validation displayed errors for required fields and stopped submission."*

Independently visually confirmed one screenshot (`04-step04-click.png` from an earlier
pre-fix run, pulled via `docker cp` and read directly): real red "Invalid credentials" text,
clearly legible — matching WORST's verdict note above almost verbatim.

## How to verify

- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- `uv run pytest tests/test_grade.py tests/test_langchain_fallback.py
  tests/test_run_case_pipeline.py -v` → all pass, including the new image-attachment tests.
- `docker compose restart`, then `POST /projects/pathlynks/run` several times — confirm PASS/
  PASS/PASS every time (not just once), and read a verdict's `note` field — it should describe
  real visual content, not a generic "insufficient evidence" complaint.

## Scope notes for the checker

- This is the single most consequential fix of this session — please verify the actual claim
  (the judge genuinely receives image bytes, not just a longer prompt) by reading
  `providers/langchain_fallback.py::_message` and `providers/anthropic.py`/`gemini.py`'s
  `_structured` yourself, not just trusting the pasted verdict notes.
- Please do your own live reruns (more than once — determinism is the actual claim here) and
  read at least one real screenshot yourself to independently confirm a verdict's reasoning
  genuinely matches what's visible in the image.
- `qa/contracts/grade.md`'s existing criteria text is unchanged by this fix (it was always
  meant to grade against real evidence — this fix makes that literal, not different). Please
  judge whether a new criterion (e.g. "the judge call must attach real evidence, not just
  describe it in text") belongs in the contract's amendment log — this is exactly the kind of
  gap the contract's own spirit already implied but never made explicit.

## Status: checked-PASS — see qa/verdicts/at049-multimodal-grading.md, cycle 1 PASS (checker
independently re-ran 3 fresh live Docker reruns of its own, 9/9 case verdicts PASS; verified the
real screenshot behind one verdict's note matches its reasoning almost verbatim; added a routine
grade.md amendment making G1's evidence-attachment spirit explicit; filed and self-resolved
AT-050, a low-severity premature verified_date stamp)
