# at176-at178-render-not-scan

**Unit:** AT-176 (high) + AT-178 (medium) + AT-174 (medium) + AT-189 (medium)
**Commit:** e2f119f
**Fix cycle:** 1
**Contract:** `qa/contracts/video-learning.md` VL1d generalised · `core-invariants.md` C4 · C7

## The guard could not see the message the class exists for

A checker pointed `PREP_COMMAND` back at the dead `autotester media prep` — the canonical AT-163
site — and this test returned **zero failures**. `media_prep.py` builds that advice as

```python
f"... run `{PREP_COMMAND} " f"{slug} {source_id}` on the HOST first"
```

The backtick lives in one f-string part; the command name in a module constant. **Two AST nodes, no
single literal holding both** — invisible to any regex over constants. My claim that it "finds every
backtick-quoted `autotester` string in `src/`" was overstated, and the guard built to end the class
carried the class's own signature.

## Render, do not scan

`tests/advice_scan.py` renders each string the way Python will — joining adjacent parts,
substituting module constants, following implicit concatenation — and reads commands out of the
**result**, backticked or not.

| | before | after |
|---|---|---|
| distinct advice sites | 5 | **9** |
| `ingest prep` (the class's own message) | invisible | seen |
| un-backticked advice (`core/consent.py`, AT-178) | invisible | seen |

Still static — no import, no execution — so a value that only exists at runtime remains a hole, and
`UNRESOLVED` **marks** it rather than pretending. That boundary is stated in the module rather than
discovered by the next checker.

## AT-174 — the oracle I said could not exist

I argued no test could tell a correct command from a plausible sibling without encoding the answer
in itself. **True of static oracles only.** The checker designed the causal one: *trigger the
refusal, run the command it names, assert the refusal stops firing.*

A registered same-arity sibling defeats every static check and fails this one, because it does not
make the refusal go away. Both halves are tested — the command that keeps the promise, and the
sibling that does not.

## AT-189 — one rule, applied to one place and not the other

I excluded `.goal/` from the repo fingerprint because a timer rewrites it, then added **`qa/` in the
same commit** — which the maker-checker pair's own automation rewrites on the same kind of timer.
207 of 1258 watched files, **no CLI code writes there**, so it bought nil detection and a real chance
of the suite failing because a maker tick landed mid-run.

## Evidence

```
SABOTAGE AY (PREP_COMMAND back to the dead `media prep` -- returned 0 before this unit)
  anchor matched once, file changed -> failures: 3
    test_the_collector_sees_the_site_the_class_exists_for
    test_every_command_the_code_names_is_one_the_cli_exposes[...]
    test_the_refusal_names_a_command_that_actually_stops_it

SABOTAGE AZ (the refusal renamed to `ingest frames` -- REGISTERED and same-arity)
  anchor matched once, file changed -> failures: 2
    test_the_collector_sees_the_site_the_class_exists_for
    test_the_refusal_names_a_command_that_actually_stops_it
```

**AZ is the unit.** That sibling passes every static oracle in this repo, and the causal test is the
only thing that catches it.

## A flake found and filed rather than shrugged at

`test_explore_live.py::test_the_dialog_page_does_not_trap_the_crawl` failed **once** under
full-suite load — `assert 'aborted_error' in ('aborted_dialog', 'explored')` — and passed on the
next full run and in isolation (8 passed). Nothing in `stages/explore*.py` was touched.

It matters because `uv run pytest` is the adapter's **slot-1 verify**, cited by every manifest in
this project: a flaky test turns *"the suite is green"* from a fact into a probability. Recorded in
`qa/feedback-inbox.md` with the shape it generalises to — X8's dialog breaker is a race by
construction, so asserting one exact terminal status is asserting the race resolved a particular
way — rather than fixed inside a unit about something else.

## Verification (host; Docker down, `uv` native; bare `pytest`)

```
uv run pytest                          744 passed, 2 skipped
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- **Runtime-only values remain invisible.** A command assembled from a function return or a
  non-constant name renders as `UNRESOLVED` and is skipped. Static analysis buys what it buys.
- The causal oracle covers **one** refusal (`require_prepared`). Every other refusal in the codebase
  still has only the static check, and generalising it needs a way to trigger each one cheaply.
- **AT-188** stands: a commit message carries a pasted pytest dump in a public repo, and rewriting
  pushed history to tidy it would erase the record of the mistake.

## Status: ready-for-check
