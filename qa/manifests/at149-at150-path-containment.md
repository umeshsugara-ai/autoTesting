# at149-at150-path-containment

**Unit:** AT-149 (medium) + AT-150 (low) — the checker's two follow-ups on `at147-at148`
**Commit:** da5940e
**Fix cycle:** 1
**Contract:** `qa/contracts/consent.md` CN4–CN7

## AT-149 — I fixed a defect and reintroduced it in the same function, in the same commit

AT-148 replaced a naive `startswith` in the **host** half of `_warn_on_target_mismatch`. The
identical bug survived **one line below it**, in the **path** half:

```python
if same_host and base.path.startswith(want.path.rstrip("/")):   # <- AT-149
```

Against `base_url = https://demo.test/app`, both `/apple-secrets` and `/appliance/admin` were
silently accepted as being under `/app`.

*A prefix is only a containment if it ends at a separator* is the exact sentence AT-148 was about.
I wrote it in a docstring and did not apply it to the next line. `_is_under` now states it once, in
one place, so there is no second copy to forget.

## AT-150 — my overclaim, and a test that protected the wrong thing

The manifest said the refusal *"names the date to use instead"*. It said the **word** "tomorrow" and
printed no date. Worse: **my own test asserted only that the word appeared**, so a refusal naming no
usable date would have passed it. That is a test written against the message I meant rather than the
message a reader gets — a small instance of the exact failure this whole session keeps circling.

It now prints the ISO date, and the test asserts the date.

## Evidence

```
$ SABOTAGE S: AT-149 -- the path half goes back to a bare prefix
failures: 2
FAILED tests/test_approve_cli.py::test_a_path_that_merely_starts_with_the_base_path_is_flagged[https://demo.test/apple-secrets]
FAILED tests/test_approve_cli.py::test_a_path_that_merely_starts_with_the_base_path_is_flagged[https://demo.test/appliance/admin]

$ SABOTAGE T: AT-150 -- the refusal says the word instead of the date
failures: 2
FAILED tests/test_approve_cli.py::test_approve_refuses_an_expiry_of_today
FAILED tests/test_approve_cli.py::test_the_expiry_refusal_prints_a_usable_date

$ RESTORE
17 passed
```

## Method note — sabotage T first reported ZERO failures

Its anchor string did not match (heredoc quoting mangled it), so the patch applied **nothing** and
the suite was green. That is the third appearance of one trap in two days:

- AT-140 cycle 1 — my no-op sabotage read as *"my test is vacuous"*; I nearly rewrote a correct test.
- The `at140` checker hit it from its own side (`max_actions=max_actions` matches twice in the file).
- Here.

So the harness itself now asserts: **the anchor is present, and the file actually changed**, before
any result is believed. A sabotage needs its own assertion, not just its own patch. Offered as a
contract line if the checker agrees — it is a property of how evidence is produced, not of the
artifact, which is where the last such proposal (AT-131) was correctly ruled out of a *feature*
contract.

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          647 passed, 2 skipped   (641 before + 6 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## Related: a HUMAN_GATE the checker raised rather than deciding

`qa/gates/at147-expiry-end-of-day.md` — should a bare `--expires <date>` mean the **end** of that
day? The checker prefers end-of-day on the merits and **may not adopt it either**, because it widens
a safety boundary retroactively. It proposes a third option neither of us considered: store new
grants as `<date>T23:59:59` — intuitive meaning, **zero** retroactive widening, one line in
`approve_cmd`. That is Umesh's call and is untouched here.

It also names a sharp edge I missed: a grant issued at 23:50 with `--expires <tomorrow>` dies ten
minutes later.

## What this does NOT claim

- Still no crawl against a real product; `find projects -name crawl` returns nothing.
- The checker verified something I had assumed rather than checked: `store.add_approval` has exactly
  **one** production caller and the UI has **no** grant surface, so `_validate_grant` covers 100% of
  the shipped grant path. My dispatch had wondered whether the UI bypassed it — it does not exist.
- **AT-141 + AT-115** (make C9 mean what it says) remains the sweep's outstanding queue row.

## Status: checked-PASS
