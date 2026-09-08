# at147-at148-grant-boundary

**Unit:** AT-147 (high) + AT-148 (medium) — the grant and the runtime disagreed for one whole day
**Commit:** 4164547
**Fix cycle:** 1
**Contract:** `qa/contracts/consent.md` CN5–CN7

## Why this jumped the queue

Both came out of the checker's adversarial pass while PASSing `at140` cycle 2 — fresh findings on
new code, not unmet criteria, so they cost no fix cycle. **AT-147 is high and lands on exactly the
date an operator granting same-day production consent for T-145 would type.** Queuing it behind two
other units would mean the one grant that matters most is issued through the defect.

## AT-147 — one comparison, two meanings, one day of disagreement

`_validate_grant` compared `expiry < date.today()`. `RunApproval.is_expired` reads a bare date
through `fromisoformat`, which yields **midnight**, then asks `now > expiry`. So an approval
"expiring today" is already dead at `00:00:01`.

`approve --expires <today>` printed a green **granted** line; the very next `explore` refused it as
`expired`. That is the AT-145 defect one day narrower, on the worst possible day.

**Fixed at the grant, deliberately not by making `is_expired` inclusive.** End-of-day is the more
intuitive reading of `--expires 2026-09-08` — and adopting it would widen **every approval already
on disk by up to 24 hours**. Silently lengthening a consent window is not a change a maker makes to
a security gate on its own judgement. The refusal now names the date to use instead, so the operator
is unblocked rather than merely stopped, and the alternative is put to the checker below.

The rule behind both AT-145 and AT-147, now a test in its own right:

> **any expiry `approve` ACCEPTS must be one `require_consent` will HONOUR.**

Two comparisons implementing one rule is where a day-wide gap comes from.

## AT-148 — a warning that was quiet on the case it exists for

`target.startswith(base_url.rstrip("/"))` reads `https://demo.test.evil.com/` as matching
`https://demo.test/`. Bounded — CN5 matches exactly at run time, so no approval could widen — but a
typo advisory silent on **precisely the shape a typo-squat takes** is not much of an advisory.

Scheme and netloc must be equal before any path prefix is considered. A genuine sub-path of
`base_url` still passes unflagged: a warning that cries wolf on the normal case gets ignored when it
matters.

## Evidence

```
$ SABOTAGE Q: AT-147 -- the boundary goes back to `<` so today is granted then refused
failures: 1
FAILED tests/test_approve_cli.py::test_approve_refuses_an_expiry_of_today

$ SABOTAGE R: AT-148 -- back to the naive prefix match
failures: 1
FAILED tests/test_approve_cli.py::test_a_lookalike_host_is_flagged_not_silently_accepted

$ RESTORE
18 passed
```

## The file split, and why it is worth a line

`tests/test_approve_cli.py` was split out at doctor's 300-line cap **by responsibility**, not by
size: `test_crawl_real_cli.py` is about **refusing** a crawl; this one is about **issuing the
approval that permits one**. That division is the finding restated — the gate's *deny* half was well
guarded and its *grant* half had no test at all until AT-140.

## Put to the checker

**Should `is_expired` treat the named day as inclusive (end of day) instead?** It is what a human
means by "expires on the 8th", and it would let `--expires <today>` work rather than be refused. I
did not take it because it lengthens every existing consent window by up to 24 hours, which is a
widening of a security boundary and belongs to the contract rather than to me. If the checker
prefers it, the conservative refusal I shipped should be replaced rather than layered on.

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          641 passed, 2 skipped   (637 before + 4 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- Still no crawl has ever run against a real product: `find projects -name crawl` and
  `-name flowspec.json` both return nothing.
- `--expires` is still the only expiry control; there is no revoke path (approvals expire, they are
  not withdrawn). That was on T-124's no-fire list and stays there.
- The sweep's remaining queue row — **AT-141 + AT-115**, make C9 mean what it says — is untouched.
  Measured while queuing it: **T-126, T-150 and T-135 all have `done_check`s that exit 0 right now**,
  before any of their work exists. That is the AT-100 shape three times, not the twice AT-115 records.

## Status: ready-for-check
