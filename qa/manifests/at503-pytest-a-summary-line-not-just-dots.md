# Manifest — at503-pytest-a-summary-line-not-just-dots

**Unit:** AT-503 — `qa/adapter.json`'s slot-1 verify command (`uv run pytest -q`) combines with
`pyproject.toml:62`'s `addopts = "-q"` into an effective `-qq`, which prints **no `N passed` /
`N failed` summary line at all** — only progress dots and `[100%]`. Two people have already judged
a suite "clean" from a `tail` of a log with no summary in it and had to retract (a checker at
AT-505, and the maker). Filed as `qa/issues.jsonl` AT-503 by the at500 cycle-1 checker.
**Contract:** `qa/contracts/core-invariants.md` C7 (verification is judged on real, re-runnable
output — a manifest pasting a summary line has to be a summary line pytest actually printed).
**Goal task:** none named directly (tooling/config fix, same shape as AT-507 and AT-513).
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-503 (low, open → fixed here; not closed by me — `qa/issues.jsonl` is the
checker's write surface, AT-499).

## Measure first (three invocation shapes, on a small subset — never the full suite twice)

`uv run pytest --collect-only -q`, then the same subset (`tests/test_ledger_checks.py`, 19 tests)
run three ways, each redirected to a file and judged on the whole file, never a `tail`:

```
$ uv run pytest --collect-only -q > .work/at503/collect.log 2>&1; echo "exit=$?" >> .work/at503/collect.log
$ uv run pytest tests/test_ledger_checks.py > .work/at503/bare.log 2>&1; echo "exit=$?" >> .work/at503/bare.log
$ uv run pytest -q tests/test_ledger_checks.py > .work/at503/single_q.log 2>&1; echo "exit=$?" >> .work/at503/single_q.log
$ uv run pytest -qq tests/test_ledger_checks.py > .work/at503/double_q.log 2>&1; echo "exit=$?" >> .work/at503/double_q.log
```

Copied verbatim into `qa/evidence/at503-pytest-a-summary-line-not-just-dots/{collect,bare,single_q,double_q}.log`.

**Results (grep -c "passed" over the whole file, not a tail):**

| invocation | CLI flag | + config's `addopts=-q` | summary line? | grep -c "passed" |
|---|---|---|---|---|
| `uv run pytest --collect-only -q` | `-q` | `-qq` (collection, N/A) | N/A (no run) | 0 |
| `uv run pytest tests/test_ledger_checks.py` | none | **`-q`** | **`19 passed in 0.61s`** | 1 |
| `uv run pytest -q tests/test_ledger_checks.py` | `-q` | **`-qq`** | none — dots + `[100%]` only | 0 |
| `uv run pytest -qq tests/test_ledger_checks.py` | `-qq` | `-qqq` | none — identical to the row above | 0 |

This confirms the mechanism exactly: pytest's `-q` is an additive count (argparse `action="count"`);
the config's `addopts = "-q"` already contributes one, so typing `-q` again on the CLI reaches the
`-qq` threshold that suppresses the summary, and typing `-qq` explicitly lands on the same behaviour
by a different route. The **bare** invocation — no `-q` on the CLI at all — is the only one of the
three that prints the summary line, because it is the only one that leaves the config's single `-q`
un-doubled.

## Decision

**Option (a): change `qa/adapter.json`'s verify command from `uv run pytest -q` to `uv run pytest`.**
Not (b) touching `pyproject.toml`'s `addopts` — that constant is what makes the bare form's output
readable at all (a fully un-quieted `pytest` prints one line per test, which is worse for a CI-style
log), and changing it would reach every other invocation in the tree, including other units' and
other loops' ad-hoc runs, not just this one adapter command. Not (c) leave both undocumented — the
retractions already happened twice; a documented, unfixed footgun is not the same as a fixed one.
The measurement above is exactly what the unit brief predicted, so (a) is both the narrowest change
and the one the evidence supports.

## What changed

- `qa/adapter.json:9` — verify command `"uv run pytest -q"` → `"uv run pytest"` (the `expect: "exit
  0"` line is unchanged; only the command string moved).
- `d:/autoTesting/CLAUDE.md` — Commands block only: `uv run pytest -q` → `uv run pytest`, with an
  inline comment stating why (no `-q` here because the config already applies one, and stacking a
  second doubles to `-qq`).
- `qa/feedback-inbox.md` — appended a PATTERN/EVIDENCE/APPLIES NEXT entry (2026-09-18) listing every
  other place in the repo the identical `-q`-on-`-q` doubling appears that this unit's file set does
  not cover: `AGENTS.md` (mirrors `CLAUDE.md`'s three lines), `CLAUDE.md`'s own two prose mentions
  outside the Commands block, `qa/contracts/core-invariants.md` (C7's Verify clause + its amendment
  log), `qa/contracts/ui.md`, `qa/contracts/explore.md`, `qa/loop.md`, and — the broader latent
  finding — roughly 45 per-file `cmd` rows in `.goal/goal.json` that also type `-q` on the CLI and
  therefore also print no summary. None of those files are edited here; they are out of this unit's
  declared file set (`qa/adapter.json`, `CLAUDE.md`'s Commands block, `qa/manifests/at503-*.md`,
  `qa/evidence/at503-*/`, `qa/feedback-inbox.md`) and `qa/contracts/` is checker-owned regardless.
- No `src/` or `tests/` file changed. No behaviour of any stage changed — this is a verify-command
  and documentation fix.

## How to verify (commands + expected)

```
git show HEAD:qa/adapter.json | grep '"cmd"' | head -1     # (pre-change) "uv run pytest -q"
grep '"cmd"' qa/adapter.json | head -1                       # (post-change) "uv run pytest"
uv run ruff check src tests scripts                          # expect: All checks passed!
uv run autotester doctor                                     # expect: doctor: clean
uv run pytest tests/test_ledger_checks.py                    # expect: dots + `N passed in …s` line
                                                              # (bare — this is now literally what
                                                              # qa/adapter.json's verify command runs
                                                              # against the whole tree)
```

**Full suite is deliberately NOT re-run here.** It takes ~12–15 minutes and has already run clean on
this tree multiple times today under the coordinator's own measurement (most recently 1484 passed,
2 skipped, 32 xfailed, exit 0). This unit's change touches no `src/` or `tests/` file and has no
mechanism to move that number — the change is entirely in which flag gets passed to the same test
run, never in the tests themselves. The subset runs above are the maker's own, real, captured
evidence for the mechanism that motivated the change; the full-suite figure is cited, not re-derived,
and attributed as such rather than presented as this unit's own run.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ grep -n '"cmd"' qa/adapter.json
      { "cmd": "uv run pytest", "expect": "exit 0" },
```

Subset logs (full contents, not excerpted — each is under 6 lines):

```
--- qa/evidence/at503-pytest-a-summary-line-not-just-dots/bare.log ---
...................                                                      [100%]
19 passed in 0.61s
exit=0

--- qa/evidence/at503-pytest-a-summary-line-not-just-dots/single_q.log ---
...................                                                      [100%]
exit=0

--- qa/evidence/at503-pytest-a-summary-line-not-just-dots/double_q.log ---
...................                                                      [100%]
exit=0
```

(`collect.log` is the `--collect-only` run — 5057 bytes of collection listing plus a deprecation
warning and `exit=0`; no summary line applies to a collection-only run.)

## Capability coverage (each claim → its isolating check)

This unit's only behavioural claim is about **pytest's own flag-combination semantics**, not about
this repo's source code — there is no `src/` function to mutate, and the four-log table above already
*is* the falsification: each row is a different input (flag combination) producing a different,
independently observed output (summary present/absent), which is exactly the green-before/red-after
shape the mutation-coverage table exists to capture, just applied to a config change instead of a code
branch.

| capability | check | falsifying condition | observed |
|---|---|---|---|
| The adapter's verify command now prints a readable summary line | `uv run pytest tests/test_ledger_checks.py` (bare, matching the new adapter command's flag shape) | put `-q` back on the CLI (the pre-fix command) | fixed: `19 passed in 0.61s` printed; pre-fix (`single_q.log`, same command with `-q` added): no summary, dots only |
| `doctor` and `ruff` are unaffected by this change (it is config/doc only) | `uv run autotester doctor`, `uv run ruff check src tests scripts` | n/a — no code path exists that could regress from a JSON string + a markdown comment | both green after the edit (pasted above) |

**NO ISOLATING FALSIFICATION beyond the above for the CLAUDE.md wording change** — it is pure prose
(a comment explaining why no `-q`), `revert_op: none`: reverting it changes nothing pytest does,
only whether a future reader understands why the command looks the way it does. The adapter.json
row above is the one claim with real behaviour behind it, and it is covered.

## Live browser evidence

Not UI-touching — no `src/` file, no `ui/` route, no browser surface changed. Changed paths:
`qa/adapter.json`, `d:/autoTesting/CLAUDE.md` (Commands block), `qa/feedback-inbox.md`,
`qa/manifests/at503-pytest-a-summary-line-not-just-dots.md`,
`qa/evidence/at503-pytest-a-summary-line-not-just-dots/*`.

## Known limits (disclosed, not claimed)

- **No test is added or changed by this unit, and none would be meaningful here.** The property
  under test is pytest's own `-q`/`addopts` interaction, not code this repo owns — asserting "pytest
  prints a summary at verbosity N" in `tests/` would be a test of a third-party library's CLI
  parsing, not of `autotester`. The four captured logs are the evidence instead, in the same spirit
  as a config-only PR: the proof is the observed output at each candidate setting, not a new
  assertion. Per the maker skill's own capability-coverage guidance, the table above stands in place
  of a mutation run.
- **This change touches the CHECKER's verify command too, not only the maker's.** `qa/adapter.json`
  slot-1 is the single verify instrument both halves of the maker-checker pair run against — the
  checker's Mode A re-run of "verify commands" will now also invoke bare `uv run pytest` instead of
  `uv run pytest -q`. That is the intended effect (a shared, readable command), but it means the
  checker's own full-suite re-run for this unit (if any) inherits the same "don't run it twice today"
  constraint the maker is under, since the tree's test content is unchanged from the coordinator's
  most recent full run.
- **The fix is necessarily partial** — this unit's declared file set is narrow
  (`qa/adapter.json`, `CLAUDE.md`'s Commands block, and this manifest/evidence/feedback-inbox), and
  the identical `-q`-on-`-q` doubling exists in `AGENTS.md`, two other prose spots in `CLAUDE.md`
  itself, four `qa/contracts/*.md` files, `qa/loop.md`, and roughly 45 per-file `cmd` rows in
  `.goal/goal.json`. All of these are named with locations in `qa/feedback-inbox.md`'s new entry
  for the checker to fold or route as it judges fit; none are edited here because contracts are
  checker-owned and the rest are outside this unit's file set.
- **`AGENTS.md` is untracked in git status** (`?? AGENTS.md` at session start) and was not
  inspected for whether it is a symlink/copy of `CLAUDE.md` or an independent file — flagged in the
  feedback-inbox entry as carrying the same stale lines, but its exact relationship to `CLAUDE.md`
  is unconfirmed.
- **`qa/issues.jsonl`'s AT-503 row is not flipped by this manifest.** That ledger is the checker's
  write surface (AT-499); this manifest is the fix for the checker to verify and close.

## Status: checked-PASS

Cycle 1, `qa/verdicts/at503-pytest-a-summary-line-not-just-dots.md` (commit `e5b3f87`), pushed per
D-007. PASS. The checker re-derived the doubling on its own subset rather than reading this
manifest's logs, and confirmed `pyproject.toml:62` is the repo's only `-q` source.

**It did the part this unit could not do, on its own surface.** The contract files are the
checker's, never the maker's, so the stale `uv run pytest -q` in their Verify clauses was routed to
`qa/feedback-inbox.md` rather than edited here. The checker folded all of it in: `core-invariants.md`
(C7, plus a new append-only amendment-log entry), `ui.md`, `explore.md`, `living-ledger.md`,
`browser-and-secrets.md` (two clauses) and `pathlynks-onboarding.md` — **six contracts, no criterion
weakened**. That is the hand-off working exactly as designed: the maker reports what it cannot
touch, and the owner of the surface fixes it.

**Three residual rows filed, and one of them is a correction to this manifest's own reasoning:**

- **AT-523** — this manifest justified leaving `pyproject.toml`'s `addopts` alone partly on the
  grounds that *"a fully un-quieted pytest prints one line per test."* **That is false, and I
  verified it myself rather than take the checker's word:** `uv run pytest -o addopts= tests/test_marker_blocks.py`
  prints `............... [100%]` — dots, exactly like the quiet mode it was being contrasted with.
  One line per test requires `-v`. The unit's *conclusion* is unaffected, because its other reason —
  changing `addopts` reaches every pytest invocation in the tree, including other loops' — is
  independently sufficient. But a decision recorded with a wrong reason is a trap for whoever
  revisits it, which is why this is a filed row and not a footnote.
- **AT-521** — `CLAUDE.md`'s two prose mentions outside the Commands block, `AGENTS.md` and
  `qa/loop.md` still name the doubled command.
- **AT-522** — **43 of 50** per-file `cmd` rows in `.goal/goal.json` carry the same doubling. The
  checker recounted independently and matched the number I measured from the orchestrator side
  exactly. This is the largest remaining surface and it means most per-file verify commands in the
  backlog still produce summary-less output.

The checker also proposed, rather than imposed, a narrow guard: assert that `qa/adapter.json`'s
verify `cmd` never stacks a CLI `-q` on top of `pyproject.toml`'s `addopts`. That tests this repo's
own config consistency rather than pytest's semantics, which is the distinction this manifest used
to argue no test was warranted — so the proposal is well aimed. It is carried on AT-523, not
silently adopted here.

