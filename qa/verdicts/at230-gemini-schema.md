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

---
---

# INDEPENDENT CONCURRENT CHECK — same slug, same cycle (2026-09-09)

**Everything above this line is a prior checker's verdict (`456e32d`, VERDICT: PASS) and is left
byte-intact.** My check ran concurrently, without having seen it, and I initially overwrote it —
restored here, which is the rule (never overwrite; append below and name the disagreement).

**We disagree: I return FAIL.** The disagreement is narrow and testable, so it should be settled on
evidence rather than by seniority:

1. **The prior verdict certifies criterion 5 ("the returned dict is validated on our side") as met
   without saying what pins it. Nothing does.** My sabotage G6 reverts
   `gemini.py:142 schema.model_validate(response.parsed)` to `return response.parsed` and the full
   suite stays green at 910 passed. Per C7 that would be INCONCLUSIVE on its own, so I proved the
   mutation changes behaviour by execution — a stub client returning `{"a":"x","surprise":1}`
   raises `ProviderError` unmutated and returns the raw dict mutated. The behaviour is real; the
   guard is absent. That is AT-256's shape one line below the line AT-256 was about (AT-266).
2. **The prior verdict states the self-reference guard "names its cause".** The depth branch raises
   `$ref expanded 20 deep — is a model self-referential?` while holding and discarding
   `node["$ref"]`; only the *unresolvable* branch names anything (AT-267).
3. **The prior verdict reports "no new issues" after probing "dialect purity across all sent
   models".** I agree on the models sent *today* — I rendered every `BaseModel` under
   `src/autotester/schema/` and the rejected-keyword set came back empty. But the sanitiser is a
   deny-list of four keywords where `google.genai.types.Schema` is an allow-list of 24, verified
   against the installed SDK; `const`, `prefixItems`, `oneOf` and `allOf` pass through untouched
   (AT-265, filed as a hazard, not as a failure of this unit).
4. **`ingest.md`'s own no-fire list** deferred the `google-genai` declaration to "the unit that
   first calls the API for real (A3)". This is that unit; `pyproject.toml` still declares only
   `langchain-google-genai` (AT-268).

**Where we agree, and it is most of it:** the suite numbers, the sanitiser's correctness over
what is sent today, sabotage FF failing exactly one test, the not-UI-touching judgement, and that
the manifest's account of its own bypass is accurate rather than self-serving. The prior verdict
also declines to certify the recall number or to close AT-255/AT-256, and I endorse both.

**Ledger consequence of the disagreement:** the prior verdict moved `AT-230` to `verified`; I
would have left it `fixed` while the unit is FAILing. I have not flipped it back — a checker
should not quietly reverse another checker's ledger write — so it stands at `verified` and this
note is the record that one of us thinks it is premature. AT-265–AT-268 are mine.

The full FAIL verdict follows.

---

# Verdict — at230-gemini-schema

**Date:** 2026-09-09
**Cycle checked:** 1
**Mode:** A (unit check), bound to `d:/autoTesting`
**Contract:** `qa/contracts/ingest.md` (provider seam, **I11–I15 authored by this check**) +
`qa/contracts/core-invariants.md` (C1, C7, C8)
**Manifest:** `qa/manifests/at230-gemini-schema.md`
**Commits judged:** `99ea27d` (the fix, shipped bypassing the pair) + `e6f6818` (the guard)

```
VERDICT: FAIL
SCOREBOARD: 3/5 criteria met, 7/7 invariants hold
FAILURES:
- [I15] sev: high · the AT-230 response-path validation is guarded by nothing — reverting
  `schema.model_validate(response.parsed)` to `return response.parsed` passes all 910 tests,
  while direct execution proves the mutation changes behaviour · add one stub-client test
  asserting an extra key raises ProviderError; no network, no key · issue: AT-266
- [ingest.md no-fire] sev: medium · this contract deferred the `google-genai` declaration to
  "the unit that first calls the API for real (A3)"; this is that unit and pyproject.toml still
  declares only `langchain-google-genai` · declare `google-genai>=2.22.0`, close AT-130 ·
  issue: AT-268
- [I14] sev: low · the `$ref` depth refusal drops the reference it is holding and asserts
  self-reference for a condition that does not imply it · name the ref, as the sibling
  unresolvable branch already does · issue: AT-267
LIVE-BROWSER: not-applicable (changed paths: src/autotester/providers/gemini.py,
src/autotester/providers/gemini_schema.py, tests/test_gemini_schema.py, docs/DECISIONS.md,
docs/MAP.md, docs/SNAPSHOT.md, qa/issues.jsonl) — see "Mode D" below; this is a judgement, not
an omission
ISSUES-WRITTEN: AT-265, AT-266, AT-267, AT-268
EXPLANATION: The sanitiser is correct — genuinely, not narrowly — for every schema this repo
sends today, and six independent sabotages in my own extract prove its behaviours are pinned
rather than merely present. It FAILs on the one thing this unit exists to be about: the sibling
line from the same commit, the returned-dict validation the manifest itself asked to have
checked, is unguarded, so AT-256's shape recurs one line below the line AT-256 was about. The
manifest's account of its own bypass is accurate and understates rather than overstates it.
```

---

## What I re-ran (all of it myself; nothing read from the manifest)

| Command | Where | Result |
|---|---|---|
| `uv run pytest` | live tree | **910 passed, 2 skipped** (99.8s) — matches the manifest exactly |
| `uv run ruff check src tests scripts` | live tree | `All checks passed!` |
| `uv run autotester doctor` | live tree | `doctor: clean` |
| `uv run autotester providers` | live tree | `available providers: gemini, langchain-fallback, mock` |
| `uv run pytest` | `git archive HEAD` extract | **910 passed, 2 skipped** — clean baseline |

`uv run autotester map` was **not** run: it regenerates `docs/MAP.md`, and the checker is
read-only toward artifacts. `doctor` passing is the criterion `map` feeds.

**Deliberately not run: `autotester ingest analyze` and `scripts/score_video_issues.py`.** Both
make paid provider calls, `projects/erp/` has no cached observations to short-circuit them, and
this unit's criteria are about the schema seam, not about the recall number. So the manifest's
`3 screens, 2 issues (2/2 model calls)` and `recall 1/7 | FP 5` are **not independently
reproduced by me** — stated plainly rather than glossed. They are corroborated by artifacts that
could only exist if a real call succeeded: `projects/erp/issues.jsonl` carries six model-produced
rows with `"model_labels":["gemini"]`, `"how_we_know":"spoken_and_screen"` and verbatim narration
(`"said_verbatim":"Remove not getting this error"`) timestamped `2026-09-09T04:03Z`, against
`src_a6d5d1b66aa0` (erp1.mp4, sha256-keyed). The unit does not claim the number is good and
neither do I.

## The sabotage harness

`git archive HEAD` extract with **its own `uv sync` venv**, not a `PYTHONPATH` pin. The sibling
checker's warning was worth taking seriously — a `.pth`-installed editable package registers a
meta-path finder that runs *before* `sys.path`, so a `PYTHONPATH` pin can silently lose to the
live tree. Verified before believing a single result:

```
>>> autotester.providers.gemini.__file__
...\scratchpad\ext\src\autotester\providers\gemini.py
>>> autotester.providers.gemini_schema.__file__
...\scratchpad\ext\src\autotester\providers\gemini_schema.py
```

Every sabotage asserts **anchor matched exactly once** and **file re-read as changed** before the
suite runs, and restores by writing the saved bytes back (never `git checkout`, AT-101). Full
suite each time, so counts are comparable with the 910-test baseline.

| # | Mutation | Failures | Which |
|---|---|---|---|
| **FF** | `gemini.py:79` `gemini_schema(schema)` → `schema` (restore AT-230 exactly) | **1** | `test_the_PROVIDER_actually_sends_the_sanitised_schema` |
| G1 | drop `"additionalProperties"` from `DROPPED_KEYS` | 3 | `…_is_gone_everywhere`, `…renders_clean`, `…PROVIDER_actually_sends…` |
| G2 | stop inlining `$ref` (return the node as-is) | **5** | `…refs_are_inlined…`, `…renders_clean`, `…self_referential…`, `…unresolvable_ref…`, `…PROVIDER…` |
| G3 | strip keywords in property position too | 2 | `test_a_FIELD_named_title_survives`, `test_every_required_name_exists_in_properties` |
| G4 | stop collapsing `anyOf: [X, null]` | 1 | `test_an_optional_becomes_nullable_not_a_union` |
| G5 | `MAX_REF_DEPTH = 10**9` (disable the cycle guard) | 1 | `test_a_self_referential_model_is_refused_not_expanded_forever` |
| **G6** | `return schema.model_validate(response.parsed)` → `return response.parsed` | **0** | — see below |

**FF reproduces the manifest's central claim exactly: one failure, the wiring test.** The manifest
says the other sanitiser sabotages "each fail 1–3 tests"; I measured 1–5, G2 being 5. That is a
delta note, not a discrepancy — the manifest's direction is right and C7's "pastes real output" is
met (the same courtesy the `at176-at178` amendment recorded).

**Not one sanitiser sabotage came back at zero.** Answering the vacuity question directly: none of
the ten `gemini_schema`-facing tests is satisfied by an inert implementation. Six distinct
behaviours, six distinct mutations, six non-empty failure sets, each naming the test whose title
describes that behaviour. This file is the opposite of vacuous.

### G6 is not a C7 INCONCLUSIVE, and the distinction is the whole finding

C7 says a zero-failure sabotage is evidence about the *sabotage* until the mutation is shown to
change behaviour. So I showed it, by execution rather than by argument — driving `_structured`
with a stub client (no network, no key) on the **unmutated live tree**:

```
EXTRA KEY  -> ProviderError: gemini returned JSON that does not fit Small (role=agent):
              1 validation error for Small / surprise / Extra inputs are not permitted
MISSING    -> ProviderError: ... a / Field required
WRONGTYPE  -> ProviderError: ... a / Input should be a valid string
VALID      -> a='x'
```

`extra="forbid"` **is** enforced on the response path; it surfaces as `ProviderError`, not as a
bare `ValidationError` and not as a silent pass; the manifest's "stricter than Gemini's dialect
can express" claim is true. With the mutation, the same payload returns the raw dict. The
mutation therefore changes behaviour and **still fails nothing** — which is a statement about the
tests, made on exactly the evidence C7 demands before making it. `grep` across `tests/` confirms
the cause: nothing in the repo constructs a Gemini response or reaches `_structured` at all;
`tests/test_providers.py:42–65` stops at registry / `available()` / api-key plumbing.

That is AT-256's shape, in the unit written to answer AT-256, one line below the line that was
pinned. `e6f6818` pinned the call site and left its sibling — the other half of the same AT-230
comment block, `gemini.py:135–147` — exactly as unpinned as the call site had been. **AT-266,
high.** The fix is small; the reason it is a FAIL rather than a note is that "the code contains
the behaviour" is precisely the evidence this project has now been burned by three times.

## Is the sanitiser correct for the dialect, or only for the cases the maker hit?

I looked for a fourth defect by construction, and grounded the dialect rather than guessing it.
`google-genai` 2.22.0's `types.Schema` has exactly 24 fields:

```
any_of default defs description enum example format items max_items max_length max_properties
maximum min_items min_length min_properties minimum nullable pattern properties
property_ordering ref required title type
```

and `types.GenerateContentConfig(response_schema=<dict>)` performs **no local validation** — I
fed it `const`, `prefixItems`, `oneOf` and `additionalProperties` dicts and each came back
byte-for-byte unchanged. So anything outside those 24 reaches Google and 400s there, by the same
mechanism as the original `Unknown name "additional_properties"`.

Probed against the live sanitiser:

| Shape | Output | Dialect |
|---|---|---|
| `enum` / multi-value `Literal` | `{"enum":[…],"type":"string"}` | ✅ `enum` is in the set |
| field named `type`/`format`/`items`/`properties`/`required`/`enum` | each kept verbatim with its own subschema | ✅ the keyword-position fix **generalises**, it is not a special case for `title` |
| two fields → same nested model | both fully inlined, no ref-counter leakage (`refs+1` is per-path, correctly) | ✅ |
| `$ref` **with siblings** (`Field(description=…)`, a default) | `{**defs[name], **siblings}` — sibling wins, `default` dropped | ✅ correct merge order |
| numeric/string constraints, `dict[str,int]` | `exclusiveMinimum/Maximum` dropped (constraint lost, but never a 400) | ✅ safe |
| **single-value `Literal["only"]`** | `{"type":"string","const":"only"}` | ❌ `const` is not in the set |
| **`tuple[int,str]`** | `{"prefixItems":[…],"maxItems":2}`, no `items` | ❌ `prefixItems` is not in the set |
| **discriminated union** | `{"oneOf":[…]}` with `const` tags inside | ❌ `oneOf` is not in the set — and note the sanitiser drops the `discriminator` keyword while keeping the `oneOf` it belongs to |
| **`int \| str \| None`** | 3-member `anyOf` still containing `{"type":"null"}` — the collapse is guarded by `len(options)==2` | ⚠️ `NULL` is in the `Type` enum, so borderline; the `nullable` intent is lost either way |
| `int \| str` (a real union) | untouched `anyOf` | ✅ `any_of` is in the set |

**Answer: the sanitiser is a deny-list against the four keywords that have already drawn blood,
where the dialect is an allow-list of 24.** But I then rendered **every** `BaseModel` under
`src/autotester/schema/` through `gemini_schema` and swept for rejected keywords — the set came
back **empty**. So this is latent, not live: nothing sent today is affected, and it does not fail
the unit. It is filed as **AT-265, medium**, because one single-value `Literal` — the natural way
to write a discriminator tag — re-creates AT-230 with a fresh keyword and an identical 400. I
wrote **I11 as an allow-list criterion** for that reason: a deny-list contract is a record of past
injuries, not a rule.

## Criteria (I11–I15, authored by this check — see the contract's amendment log for the reasoning)

| | Criterion | Verdict |
|---|---|---|
| **I11** | dialect conformance for what is actually sent | **MET** — `additionalProperties`/`$defs`/`$ref` absent, optionals `nullable`; sabotages G1/G2/G4 pin all three. Allow-list gap is latent (AT-265) |
| **I12** | a keyword is only a keyword in keyword position; `required` never names a missing property | **MET** — G3 = 2 failures; the M3 probe shows it generalises beyond `title` |
| **I13** | the provider sends the sanitised dict, pinned without a network call | **MET** — FF = exactly 1 failure, in an extract with `__file__` verified |
| **I14** | unrenderable schema refused locally, **naming the reference** | **NOT MET** — refusal is local and typed (G5 pins it), but the depth branch names nothing (AT-267, low) |
| **I15** | returned dict validated on our side, `ProviderError` not a bare `ValidationError` | **NOT MET as a criterion** — behaviour correct and proven, guarded by nothing (AT-266, high) |

Core invariants: **C1** ✅ (this whole unit exists *because* of `extra="forbid"`, and it is now
enforced on both directions of the wire) · **C2** ✅ (103/164/184 lines; `doctor: clean`) ·
**C3** ✅ (new module `gemini_schema.py` — C3 requires a stated reason in the manifest, and this
late manifest supplies it) · **C4** ✅ · **C7** ✅ (the manifest's sabotage claim reproduced in my
own harness; the anchor/change assertions were honoured) · **C8** ✅
(`grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` → nothing; the vendor SDK
stays behind the provider seam, and `gemini_schema.py` is inside it) · **C9** n/a.

## Mode D — why its absence is a judgement

The changed paths across both commits are `providers/gemini.py`, `providers/gemini_schema.py`,
`tests/test_gemini_schema.py`, `docs/{DECISIONS,MAP,SNAPSHOT}.md` and `qa/issues.jsonl`. No route,
template, component or page. I also checked the indirect case D-024 exists for — a retrieval or
ranking change that alters what an answer page renders — and it does not apply: the sanitiser
decides whether a provider call succeeds *at all*, and every UI surface reads stored artifacts
under `projects/<slug>/`, which this change does not touch. There is additionally no browser
assertion that could distinguish a sanitised schema from a raw one without spending money on a
live call. **I agree with the manifest's not-UI-touching claim; Mode D is inapplicable, not
skipped.**

## Is the manifest's account of its own bypass honest?

Checked against `git`, not against its own narrative. **It is accurate, and it understates rather
than overstates.**

- *"the test never landed"* — **confirmed.** `git show --stat e6f6818` is
  `tests/test_gemini_schema.py | 184 ++++++++…`, `1 file changed, 184 insertions(+)`. The file is
  created whole in `e6f6818`; it is absent from `99ea27d`, whose stat is docs ×3, `qa/issues.jsonl`,
  `providers/gemini.py`, `providers/gemini_schema.py` and nothing else. (The sweep's 867-test count
  at the bypassed HEAD versus my 910 today is *not* evidence for this — several later units added
  tests in between — so the diff, not the delta, is what carries it: `+184/-0`, file created.)
- *"I reported the result of a run I had not confirmed"* — **confirmed**, and it is the correct
  characterisation. AT-256's own evidence line cites the eleven direct `gemini_schema(...)` call
  sites in the then-untracked file and records that it never constructs `GeminiProvider`.
- **Understated, twice.** (i) The Sabotage section reads *"Before `e6f6818`: 0 failures. The
  sanitiser had 12 assertions…"*, which describes a guard that existed **on disk but not in git**;
  at HEAD there were no assertions at all, and a `git clean` would have taken the lot. The header
  does say "its only guard file untracked", so it is on the record — but the sabotage narrative
  reads as if a 12-assertion guard were in the tree. (ii) More substantively, *"After: exactly 1
  failure"* reads as the wiring debt being settled, when the same commit's other AT-230 line is
  still unpinned today (AT-266). The manifest lists that behaviour among the criteria it wants
  checked and does not note that nothing guards it.
- **Nothing overstated.** No claim I could test was inflated, and the two "does not claim"
  disclaimers (the recall number is bad; a late manifest does not repair the bypass) are both
  correct. The manifest does not ask for credit it has not earned.
- **One thing the manifest does not mention and should be on the record:** `99ea27d` carries a
  DECISIONS entry, **D-022 — and D-022 is about T-135, `expand`/`coverage` reconnection.** Its
  `Changes-authorized` names `ui/routes_learn.py`, `stages/coverage.py`, `ARCHITECTURE.md` and
  `goal.json`. Nothing in it names `providers/`. So the AT-230 fix rode into master inside a
  commit whose recorded decision describes different work — which is a large part of why the
  bypass was invisible to everything except a sweep that reads `git show --stat`. No Lab Protocol
  rule is strictly broken (`ARCHITECTURE.md` prose was untouched, `MAP.md` is generated), but a
  decision log that describes the wrong change is a weaker instrument than an absent one.

## Ledger notes

- **AT-230**: I would have left it `fixed` rather than upgrading it on a FAILing unit — the defect
  itself is genuinely closed and I proved it independently, but upgrading a row while the unit is
  FAILing is the claim-outrunning-check shape the sweep exists to catch. The concurrent checker
  moved it to `verified` and I have not reversed another checker's ledger write; see the
  INDEPENDENT CONCURRENT CHECK section at the top of this file.
- **AT-255** (BYPASS) stays **open**, by the maker's own statement and mine: a late manifest is not
  having gone through the pair.
- **AT-256** stays **open**. The specific line it names is now pinned — FF proves it — but the
  class it names recurs untouched at `gemini.py:142` (AT-266). Closing it while its own shape
  survives one line below would be the fifth generation of the pattern, not the end of it.

## For cycle 2 — the shortest path to PASS

1. **AT-266 / I15** — one test: stub client, payload with an extra key, assert `ProviderError`.
   Then re-run sabotage G6 and show it fails.
2. **AT-268** — declare `google-genai>=2.22.0` in `pyproject.toml`; close AT-130.
3. **AT-267 / I14** — put `node["$ref"]` into the depth message and tighten the test's `match=`.
4. **AT-265** is medium and latent; it may be queued as its own unit rather than fixed here, but
   say which in the manifest.
