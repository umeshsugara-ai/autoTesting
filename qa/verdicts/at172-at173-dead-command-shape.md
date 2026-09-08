# Verdict — at172-at173-dead-command-shape

**Cycle checked:** 1
**Date:** 2026-09-08
**Commit checked:** 3b765a4
**Contract:** `qa/contracts/video-learning.md` VL1d (generalised), I-VL3 · `qa/contracts/core-invariants.md` C7
**Checker note:** this is a re-dispatch of cycle 1. The previous checker died on an API ENOTFOUND
after one tool call and wrote nothing; a crashed checker is not a verdict and does not consume a
fix cycle.

## VERDICT: PASS

Both shipped defects are fixed and independently reproduced. The structural test is real and
catches five of the six live advice sites. It does **not** catch the sixth — and the sixth is the
one the whole class is named after. That is test strength, not a shipped dead end, so it goes to
the ledger rather than against a criterion; but it is a bigger hole than the manifest represents,
and it is recorded in the contract so the instance test it does not replace cannot be retired as
redundant.

## What I re-ran (host, Docker down, `uv` native, bare `pytest`)

```
uv run pytest                          700 passed, 2 skipped, 1 warning in 80.44s   (0 FAILED lines)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

All three claims reproduce exactly.

## Sabotages (isolated `git worktree` at 3b765a4 — never the live tree, AT-101)

Each asserted **anchor matched exactly once** and **file changed on disk** before its result was
believed (C7). All four of the maker's reproduce:

| # | Sabotage | Result |
|---|---|---|
| S2 | AT-172 message restored (the `ingest analyze` refusal) | anchor once, file changed -> **1** |
| S3 | AT-163 dead group reintroduced elsewhere (`ingest list` -> `media list`) | anchor once, file changed -> **1** |
| S4 | AO — vanished recording not refused (`if not video.is_file()` -> `if False`) | anchor once, file changed -> **2** |
| S5 | AP — the CLI swallows it (typed `except` -> `except NotImplementedError: pass`) | anchor once, file changed -> **1** |

S4 came back **2, not the manifest's 1**. Not a defect: my mutation disables the whole branch and
trips both the stage-level and the CLI-level test, which is the two-level coverage the manifest
claims. Recorded because a manifest number a checker cannot reproduce is worth naming even when
the direction is favourable.

**S1 — the decisive one, which the maker did not run.** `PREP_COMMAND = "autotester ingest prep"`
mutated to `"autotester media prep"`: the original AT-163 dead end, at its own site.

```
S1  tests/test_cli_advice_resolves.py   anchor once, file changed -> 0
S1b whole suite                          anchor once, file changed -> 1
```

The new structural test does not see it. The single failure in the full suite is
`tests/test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists` — the
**pre-existing instance-scoped T-132 test**, i.e. exactly the kind of test this unit was built to
stop relying on. See AT-176 below.

## Attacking the collector (measured, not argued)

I ran the test's own `advice_in_source()` against `src/`. It yields six rows / five distinct
commands: `ingest register`, `ingest list`, `snapshot` (x2), `map`, and the `flowspec approve`
invocation with placeholders. Then I injected a dead command (`autotester bogusgroup deadcmd`) in
one shape at a time into a probe module under `src/` and ran the advice test:

| Shape | Result | Verdict |
|---|---|---|
| plain runtime string (control) | CAUGHT | — |
| `typer.Option(help=...)` | **CAUGHT** | covered; the maker's AST rule handles kwargs correctly |
| dict literal value | **CAUGHT** | covered |
| list literal element | **CAUGHT** | covered |
| module-level bare string statement | MISSED | **correct** — an `ast.Expr` string cannot be printed; this is the rule working |
| f-string with an interpolated part | MISSED | **real hole** — see AT-176 |
| built by implicit/explicit concatenation | MISSED | **real hole** — same root cause |
| no backticks at all | MISSED | **real hole** — live instance, see AT-178 |
| `.md` prompt file under `src/` | not scanned (`rglob("*.py")`) | acceptable scoping — no live instance; prompts address a model, not an operator |
| `ui/` HTML | n/a | the UI is Python-generated; the one `ui/` advice string is a module docstring and correctly excluded |

The two misses that matter share one root cause: **the command name and its backticks live in
different AST nodes.** `media_prep.py:157` builds the advice by implicit concatenation of two
f-string literals, with the opening backtick in the first and the word `autotester` in neither —
it lives in the `PREP_COMMAND` constant, which itself carries no backticks. The `ADVICE` regex
matches nothing in either literal. The docstring discloses the `{}` exclusion and justifies it as
"checked separately by the caller's own test"; S1 shows that justification is true only by the
accident of a surviving instance test, at the one site where it most needs not to be.

## Attacking it the other way — can it FAIL on something legitimate?

No false positives found. Probed against the live CLI:

- a correct command taking **required arguments** (`autotester approve myproj --kind crawl`) — passes;
  `--help` short-circuits click's arity check before parameter validation runs.
- **placeholder arguments** (`ingest prep <slug> <source-id>`, and the live `flowspec approve`
  invocation) — pass.
- a **balanced-quoted Windows path** (`ingest register proj "C:/a b/v.mp4"`) — passes; `shlex.split`
  handles it.
- an **unbalanced quote** fails the test rather than erroring collection — loud, not silent. Note
  `advice_in_source()` runs at import time for `parametrize`, so a `shlex` crash there *would* take
  the module down; it doesn't today, because `shlex.split` is called in the test body, not the
  collector.

So the `{}` exclusion is not needed to prevent false positives — placeholders and quoted paths
already pass without it. It is buying nothing and costing the AT-163 site. That is the shape of the
fix.

## The maker's three-round account — verified

All three rounds are real and the final rule handles all three without over-excluding:

1. **Slicing bug** — confirmed from the code and the comment at the `argv` line: the regex captures
   what follows `autotester`, so the capture *is* the argv; a `[1:]` slice turns `ingest run` into
   `run`. Fixed.
2. **Comments** — `ast.parse` never yields comment text, so comments are structurally invisible.
   Verified: `cli_video.py:109` and `media_prep.py:33` both name dead commands in comments and
   neither is collected.
3. **Variable docstring** — the `ast.Expr`-holding-a-`Constant`-string rule covers the bare string
   under an assignment, which the narrower module/class/function rule missed. Verified by probe
   (module-level bare string MISSED) and by the fact that `PREP_COMMAND`'s docstring, which names
   the dead command, is not collected.

No over-exclusion: `typer.Option(help=)`, dict values and list elements are all still collected.
The rule is where the maker says it is.

## AT-173 — verified at all three points asked

- **`extract_frames` refuses a vanished file** — S4 proves the guard is load-bearing at the stage
  level.
- **The CLI exits 2, no traceback, no green line** — S5 proves the mapping is load-bearing;
  `raise typer.Exit(2) from None` suppresses the chain.
- **A genuine zero-frame result still SUCCEEDS.** This one had no test, so I wrote my own probe:
  file present on disk, analysis with a screen naming no `screenshot_ts`, run through the real CLI.

  ```
  EXIT: 0
  OUT: src_3fb2bbd84fda: 0 frame(s) written
  ```

  Exit code unchanged for that case; only the colour moved to yellow. The maker changed the colour
  and did not change the contract. Confirmed as asked.

## Ruling on the open question — AT-174

**I am taking the offer, and I do not accept the premise that any oracle must encode the answer.**

The maker's search stayed inside the space of *static* oracles — "is this string the right
command?" — and every static answer there is either a restatement of the code or a substring pin.
That space genuinely has no non-circular member, so the conclusion is right about the space and
wrong about the problem.

The escape is to stop asking what the string *is* and test what the message *claims*. A refusal
that names a command makes a causal promise: **"run this and the condition that stopped you will be
gone."** That promise is checkable by execution, and checking it names no command:

> For each refusal that quotes a command, build the state that triggers the refusal, assert it
> fires, then **run the quoted command as the message renders it**, and assert the refusal no
> longer fires.

`ingest prep` passes: it writes `media.json`, so `require_prepared` stops raising.
`ingest frames` — the registered, same-arity sibling that defeated the banner oracle — **fails**,
because running it does not produce `media.json` and the refusal fires again. The test contains no
correct answer; it contains a fixture, an invocation, and the same predicate twice. That is the
same move as the fail-closed predicate from AT-155: replace an oracle that asks *what is written*
with one that asks *what happens*.

Feasibility on this host is not a problem — `ingest prep` writes `media.json` on the ffmpeg-absent
degrade path too (VL1's one-chunk shape), so the fixture needs no ffmpeg.

Scope, stated honestly: this oracle applies to **precondition refusals**, which is where the damage
is. `ingest register`'s "no sources yet" message also round-trips. It does not apply to the new
AT-172 message, which correctly names no command at all — and that is the right answer for that
message, not a gap.

**AT-174 stays open with this design attached.** It is a better unit than this one, as the maker
said; it is not a condition of this verdict.

## Adversarial — advice this test does not cover

I enumerated every `autotester …` reference outside `src/` (`docs/`, `CLAUDE.md`, `qa/`,
`scripts/`, `.claude/`) and resolved each distinct command against the live CLI:

```
ok:   ledger check · ingest run · ingest prep · approve · login · flowspec status ·
      report excel · report html · providers · map · snapshot · ledger relitigation ·
      ledger add · explore · ingest frames
DEAD: ingest analyze · media prep
```

**No live dead end anywhere.** Both dead names survive only in narration about the bugs themselves
(`docs/DECISIONS.md`, manifests, ledger rows, the `PREP_COMMAND` docstring), which is the correct
place for them. `CLAUDE.md`'s Commands block is uncovered by any test but is currently correct.
Folded into AT-178 rather than filed separately: the collector's `src/`-only scope is a deliberate
boundary, but nothing tests the documents a human opens first.

## Criteria

| Item | Verdict | Evidence |
|---|---|---|
| VL1d — the refusal names a command the operator can actually run | **MET** | every command named in a shipped `src/` message resolves against the live CLI; the AT-172 message now names none, correctly |
| VL1d generalised to every refusal quoting a command | **MET for the artifact** | all 15 live commands resolve; residual is test strength (AT-176), not a shipped defect |
| I-VL3 — never assert a fact it did not observe | **MET** | a vanished recording is refused at both levels (S4, S5); a real zero-frame result still succeeds, verified by execution |
| C7 — sabotage asserts it was applied | **MET** | five sabotages, each anchor-matched-once + file-changed before its result was read |
| C7 — verification is independent | **MET** | every number in the manifest re-derived here; S1 and the zero-frame probe are the checker's own |
| Manifest claim: "finds **every** backtick-quoted `autotester …` string in `src/`" | **NOT MET** | S1 -> 0. Overstated, not false-in-effect; the missed site is still covered by its own instance test. Ledger, not a criterion failure |

## Issues

- **AT-172 -> fixed** (verified: S2 reproduces; the shipped message names no command).
- **AT-173 -> fixed** (verified: S4, S5, and the zero-frame probe).
- **AT-176 -> severity raised medium -> high**, with the sweep's finding confirmed by sabotage.
  The sweep filed it from a read of the collector and flagged itself as a possible duplicate of
  this check; it is the same finding, so this verdict confirms rather than duplicates it. Raised
  because the sweep reasoned it and I proved it: the class-level guard returns **0 failures** on the
  canonical AT-163 regression, and the only thing between that regression and a green suite is the
  instance test the commit message argues is no longer the strategy.
- **AT-178 (new, medium)** — un-backticked advice, and advice outside `src/*.py`, is uncollected.
  Live instance: `core/consent.py:35`.
- **AT-174 stays open** with the round-trip oracle design above.

## Contract amendment (routine — records a measurement, tightens nothing)

`video-learning.md` VL1d gains a recorded edge case naming the interpolation blind spot and stating
that `tests/test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists` is
**not** made redundant by the class-level guard and may not be retired on that basis. That is the
concrete near-term regression path: a future maker reading commit 3b765a4 would reasonably delete
it.
