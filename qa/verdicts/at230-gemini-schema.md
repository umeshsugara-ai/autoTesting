# Verdict — at230-gemini-schema

**Date:** 2026-09-09 · **Cycle checked:** 1 · **Bound to:** `d:/autoTesting`
**Commits checked:** `99ea27d` (the fix, shipped bypassing the pair) + `e6f6818` (the guard)
**Contract:** `qa/contracts/ingest.md` (provider seam) · core-invariants **C8**

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, C8 holds
FAILURES: none at >80% confidence
LIVE-BROWSER: not-applicable (changed paths: providers/gemini.py, providers/gemini_schema.py,
              tests/test_gemini_schema.py, generated docs — no route, page, component or template)
ISSUES-WRITTEN: none new
EXPLANATION: Every criterion was re-derived against the real code, not against the manifest. The
sanitiser is correct over all four schema models the project actually sends, not just the one that
motivated it; the field/keyword collision is genuinely fixed; the self-reference guard fires and
names its cause; and the provider wire is pinned by a guard that I proved can fail. The unit's
own honesty about the bypass is accurate and its scope claims are not overstated.
```

---

## What I re-ran myself

| Command | My result |
|---|---|
| `uv run pytest` | **910 passed, 2 skipped** |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run autotester providers` | `gemini, langchain-fallback, mock` |

## Criteria — each re-derived, not read

I did not test only the model that produced the original 400. The manifest's own stated lesson is
that a seam talking to someone else's API cannot be proven by a double that agrees with us, so I
rendered **every schema model this project sends** and walked the output tree myself
(`.work/checker-at230-probe.py`).

| | Criterion | Result | How I know |
|---|---|---|---|
| C1 | schemas are in Gemini's dialect — no `additionalProperties`, `$defs`/`$ref`, `anyOf` union | **PASS** | Walked the rendered tree of `FlowSpec`, `ExpandedSteps`, `Verdict`, `VideoAnalysis`, distinguishing keyword position from `properties` (field-name) position. Zero banned keys; zero literal `$defs`/`$ref` in the serialised JSON. |
| C2 | a field colliding with a JSON-Schema keyword survives; `required` never names a missing property | **PASS** | `ObservedIssue.title` present in `properties`. `required ⊆ properties` checked recursively across all five models — no mismatch anywhere, not just at the top level. |
| C3 | the provider sends the **sanitised** schema, pinned without a network call | **PASS** | **Sabotage, my own:** reverted `gemini.py:79` to `kwargs["response_schema"] = schema` in a `git archive HEAD` extract → **exactly 1 failure**, `test_the_PROVIDER_actually_sends_the_sanitised_schema`, asserting *"the raw Pydantic class was sent (AT-230)"*. No network involved. |
| C4 | a self-referential model is refused locally, naming the reference | **PASS** | Built a `SelfRef` model with `child: Optional[SelfRef]`; `gemini_schema` raised `SchemaTooDeep: $ref expanded 20 deep — is a model self-referential?` — refused locally and the message points at the cause. |
| C5 | the returned dict is validated against the model on our side | **PASS** | `gemini.py:140-146` — `schema.model_validate(response.parsed)`, `ValidationError` converted to a `ProviderError` naming the schema and role. Stricter than the wire, since `extra="forbid"` cannot be expressed in Gemini's dialect at all. |

**AT-101 respected:** the sabotage ran in a scratchpad extract with `PYTHONPATH` pinned to it. The
live tree's `gemini.py:79` still reads `gemini_schema(schema)` and `git diff -- providers/` is empty.

## On the guard that was the real finding

The manifest says the T-131 provider unit was PASSed against *"a fake client that accepted any
config, so the one thing that could only fail against Google's endpoint was the one thing never
exercised."* That is correct and it is the same class as AT-218 — a guard that cannot fail. What
matters here is that the replacement guard **can**: I broke the wire and exactly one test went red,
with a message that names the issue. That is the standard, and this unit meets it.

## What I am not certifying

- **Not the recall number.** `recall 1/7 = 0.1429, FP 5` is a bad result and the manifest says so
  itself. AT-231 and AT-232 are open against it and this verdict does not touch them.
- **Not the bypass.** `99ea27d` reached master with no manifest, no verdict and its guard file
  untracked. A late manifest gets the *change* checked; it does not make the process have happened.
  **AT-255 stands as filed**, and this PASS is not a reason to close it.
- **AT-256 (reporting a run that was not confirmed) is a separate process finding** and is likewise
  untouched by this verdict.

## Ledger

`AT-230` → **verified**. No new issues: the two things I probed hardest for beyond the manifest's
own list — dialect purity across *all* sent models, and `required`/`properties` consistency at every
nesting level, not just the root — both held.
