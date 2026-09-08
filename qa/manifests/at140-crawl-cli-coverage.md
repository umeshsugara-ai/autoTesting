# at140-crawl-cli-coverage

**Unit:** AT-140 (high) — no test drove the shipped `autotester explore` or `autotester approve`
**Commit:** f564d0d
**Fix cycle:** 1
**Contract:** `qa/contracts/consent.md` CN1–CN9 · `qa/contracts/explore.md`
**Queue:** top row of the 2026-09-08T14:40Z sweep, taken as written.

## Why this unit, and why now rather than after T-145

The sweep was asked to judge whether my countermeasure for a five-unit blind spot was real. Its
answer was the useful kind — **yes, and it is scoped too narrowly to help where it matters most.**

Measured, not asserted: across the whole suite the only CLI commands any test invoked were
`ingest run`, `ingest register` and `login`. Twelve tests called `run_crawl` **directly** — the
entry point AT-111's own checker called *"the one no operator uses"*. And `approve`, **the command
that grants consent**, had no test at all, while the refusal path around it was well defended.

**T-145 is CRITICAL and points that untested path at a live production ERP.** Testing it afterwards
would be testing it after the only run that mattered.

## What made this cheap — and it is AT-111's dividend

These tests need **no browser**. Consent is pre-flighted before `paths.ensure()` and before
`BrowserSession`, which was the whole point of the AT-111 fix, so every refusal path is reachable
from a plain `CliRunner`. The success path deliberately stops at the consent seam; a real crawl
belongs to `scripts/explore_proof.py`, not to a unit test.

## What is covered for the first time

| Surface | Why it matters |
|---|---|
| `explore` refusal exit code + **no-trace** through the CLI | CN1 was proven only by the proof script and by calling `run_crawl` directly |
| The refusal's grant command carries **the bounds of the run it refused** | CN6 — the original bug printed a command that produced a second refusal |
| Both exit-1 paths in `_resolve_crawl_target` | a missing `--login-case` silently ignored would crawl logged-OUT and call the login wall the product |
| `approve` unknown-kind / unknown-project | the grant command had zero coverage |
| **`explore`'s typer defaults vs `require_consent`** | 200 actions / 600 s are the exact numbers production is judged against: an approval for precisely those must pass, one action short must refuse |

That last row is the one I would keep if I could keep only one. A default that drifts out of step
with what the consent gate checks would fail **nowhere else in the suite**.

## Evidence

```
$ SABOTAGE K: the explore CLI stops pre-flighting consent (the AT-111 regression)
failures: 1
FAILED tests/test_crawl_real_cli.py::test_a_refused_crawl_leaves_nothing_on_disk

$ SABOTAGE L: consent stops checking the ACTION budget
failures: 1
FAILED tests/test_crawl_real_cli.py::test_an_approval_narrower_than_the_run_still_refuses

$ SABOTAGE M: a missing --login-case is ignored instead of named
failures: 1
FAILED tests/test_crawl_real_cli.py::test_a_missing_login_case_is_named_not_ignored

$ SABOTAGE N: the refusal drops the action bound from its grant command (the original CN6 bug)
failures: 2
FAILED tests/test_crawl_real_cli.py::test_the_refusal_names_every_bound_of_the_run_it_refused
FAILED tests/test_crawl_real_cli.py::test_the_refusals_command_grants_the_run_once_a_human_fills_it_in

$ RESTORE
10 passed
```

**K failing only ONE test is correct and worth stating explicitly.** `run_crawl` checks consent
again at the seam, so removing the pre-flight still exits 2 — only the **leftover files** betray it.
That is precisely the AT-111 bug, and it means the exit-code test alone could never have caught it.

## Two self-corrections

1. **My first cut of sabotage L applied nothing.** I wrote the condition as
   `approval.max_actions < actions`; the real code is `actions > approval.max_actions`. The string
   never matched, the sabotage was a no-op, and it reported **zero failures** — which I initially
   read as *"my test is vacuous"* and was about to act on by rewriting a correct test. **A sabotage
   that does not apply proves nothing in either direction.** Verify the anchor matched before
   believing the result. This is the inverse of AT-117: there I fabricated a failure, here I nearly
   believed a fabricated pass.
2. **I dropped a claim I could not support.** My first test asserted the refusal's grant command
   "works verbatim". It does not, *by design*: it leaves placeholders for what only a human can
   supply — who authorised the run, until when, what it may touch. A test asserting verbatim
   execution would be asserting a design mistake. It now substitutes the placeholders and checks the
   filled-in command grants exactly the run that was refused, not a narrower one.

## Verification (host; Docker down, `uv` runs natively; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          633 passed, 2 skipped   (623 before + 10 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- **No crawl was actually run.** These tests stop at the consent seam by design; the live-browser
  behaviour is still `scripts/explore_proof.py`'s job and T-145's.
- `report crawl` and `explore --merge` remain uncovered by the CLI — `--merge` needs a completed
  crawl, so it belongs with a browser-backed test rather than here. Naming it so the gap is on
  record instead of implied closed.
- The sweep's other two queue rows (**AT-141 + AT-115** — make C9 mean what it says; **AT-142** —
  the ERP credential gate has no file on disk at all) are untouched and remain queued.

## Status: ready-for-check
