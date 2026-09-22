# Build brief — at119-vocab (issue AT-119, severity low)

## What you are changing
Exactly ONE file: `tests/test_goal_criticality_vocabulary.py` (currently 57 lines).
Do not touch any other file. Do not touch `src/`.

## Current state
That file declares, at line 26:

    CLASSIFIER_VOCABULARY = {"low", "medium", "high", "critical"}

with a comment explaining it deliberately mirrors `_ORDER` in a shared file that lives
*outside* this repository, so the suite does not depend on a path it does not own. That
reasoning stays — do not delete the constant and do not add a hard import at module level.

## The problem to fix
The copy has no drift guard. If the source `_ORDER` ever changes, this test keeps passing
while the data is wrong — the same silent-divergence shape the file was written to prevent.

## What to add
One additional test function in the same file that:
1. Tries to load the source module by path using `importlib.util.spec_from_file_location`
   from: `D:/ai_os/.claude/skills/goal/scripts/criticality.py`
2. Calls `pytest.skip(...)` with a clear reason if that path does not exist or cannot be
   imported — the suite must stay green on a machine without that checkout.
3. Otherwise asserts `CLASSIFIER_VOCABULARY == set(criticality._ORDER)`, with an assertion
   message that names both sets so a divergence is loud and readable.

## House style to match
- Type annotations on the test function (`-> None`), as the existing tests have.
- A short docstring saying why the test exists, in the voice of the existing two tests.
- Imports go at the top of the file with the existing imports.
- The file must stay UNDER 300 lines (a repo lint rule caps file length at 300).

## How this will be verified
`uv run pytest tests/test_goal_criticality_vocabulary.py` must pass, and the new test must
either run and pass or skip with its stated reason.

## Rules
- Work ONLY inside this directory.
- Do NOT run git. Do NOT dispatch other agents.
- Stop as soon as the single file is edited.

---

# CYCLE 2 — one defect to fix, nothing else

A checker reviewed cycle 1 and returned FAIL for exactly one reason. Fix only this.

## The defect (issue AT-538)
`uv run ruff check src tests scripts` fails with **SIM300 (Yoda condition)** on the assertion you
added in `tests/test_goal_criticality_vocabulary.py`. The constant is on the left-hand side.

Current:

    assert CLASSIFIER_VOCABULARY == source_vocabulary, (

Required:

    assert source_vocabulary == CLASSIFIER_VOCABULARY, (

## Rules
- Change ONLY that comparison's operand order. Leave the assertion message exactly as it is.
- Do not touch anything else in the file. Do not touch any other file.
- Do NOT run git. Do not dispatch other agents.
- Everything else about cycle 1 was accepted: the test runs rather than skips, the sabotage proof
  showed it fails for the right reason, and the diff scope was clean. Do not redesign any of it.
