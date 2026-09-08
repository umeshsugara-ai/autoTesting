# at151-at152-both-arms

**Unit:** AT-151 (low) + AT-152 (low) — the checker's follow-ups on `at149-at150`
**Commit:** 2458b51
**Fix cycle:** 1
**Contract:** `qa/contracts/consent.md` CN4–CN5 · `core-invariants.md` C7

## AT-151 — the same one-arm mistake, a third time

The AT-150 fix named a usable date on the `today` branch of a two-arm condition and **not** on the
`past` one. That is AT-149 again — fix one arm, leave its twin — which was itself AT-148 again.

| | The fix | What it missed |
|---|---|---|
| AT-148 | naive `startswith` in the **host** half | the identical line in the **path** half |
| AT-149 | the path half | — |
| AT-150 | name a date on the **today** branch | the **past** branch |
| AT-151 | both branches | — |

**Three iterations of one mistake, each caught by the checker rather than by me.** The shape is
always "I fixed the instance I was looking at." Both arms now end at the same sentence, so there is
no arm left to forget.

## AT-152 — the one silent case

`urlparse` normalises no dot-segments, so `/app/../evil` read as **contained** while *resolving* to
`/evil`. Anything that can climb out is not under anything, so the check refuses to vouch for it
rather than guessing where it lands.

Worth recording from the checker's 28-shape probe: **every other wrong answer errs toward a spurious
warning, never toward silence.** This was the only case that was quiet, which is why it was the only
one worth fixing.

## Evidence — anchors asserted, per the C7 clause the checker just wrote

```
SABOTAGE U (AT-151: the past branch names no usable date)
  anchor matched once, file changed -> failures: 3
    FAILED tests/test_approve_cli.py::test_approve_refuses_an_expiry_of_today
    FAILED tests/test_approve_cli.py::test_the_expiry_refusal_prints_a_usable_date
    FAILED tests/test_approve_cli.py::test_a_past_expiry_also_names_a_usable_date

SABOTAGE V (AT-152: dot-segments read as contained again)
  anchor matched once, file changed -> failures: 1
    FAILED tests/test_approve_target_match.py::test_a_path_that_climbs_out_of_the_base_is_flagged

SABOTAGE S (AT-149: path half back to a bare prefix)
  anchor matched once, file changed -> failures: 2
    FAILED tests/test_approve_target_match.py::test_a_path_that_merely_starts_with_the_base_path_is_flagged[...]

RESTORED
```

Every run printed `anchor matched once, file changed` **before** the result was believed. Sabotage S
is re-run deliberately: those tests changed file in this commit, and a guard that moves house is a
guard worth re-proving.

## The split, and a failure in how I did it

`tests/test_approve_target_match.py` was split at doctor's cap. The division restates the finding:
`test_approve_cli.py` is about **when** an approval is valid (expiry, kind, project); the new file is
about **what** it covers. Those two concerns collected entirely separate bugs — AT-147 was a boundary
date, while AT-148/149/152 were three different ways a string can look like a prefix of a URL without
being underneath it.

**My first attempt was a scripted extraction that dropped a `parametrize` decorator and left an
orphaned test body behind.** Ruff caught it (F821, two undefined names) — I did not. I rewrote both
files explicitly rather than debugging the splitter: a script that silently mis-moves tests is the
same class of problem as a sabotage whose anchor does not match, and I had just written a contract
clause about exactly that.

## This is the END of the consent-hardening chain

Five units now: `t124` → `at147-148` → `at149-150` → this. Each has found progressively smaller
issues in the same two functions, and the last two verdicts produced only `low` findings. The
security-relevant work is done — a forged approval, an expired grant, a lookalike host and a
climbing path are all handled — and continuing would be polishing a function while the sweep's actual
queue row waits.

**Next unit is AT-141 + AT-115 regardless of what this verdict returns**, unless it returns something
`high`. Stating it here so it is a commitment on disk rather than an intention.

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          650 passed, 2 skipped   (647 before + 3 net new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- Still no crawl against a real product.
- `qa/gates/at147-expiry-end-of-day.md` is untouched and remains Umesh's alone.
- **Measured and waiting for the next unit:** `T-126`, `T-150` and `T-135` all have `done_check`s
  that exit **0 right now**, before any of their work exists. That is the AT-100 shape three times,
  not the twice AT-115 records.

## Status: ready-for-check
