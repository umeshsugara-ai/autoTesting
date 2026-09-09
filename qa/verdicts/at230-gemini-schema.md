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

- **AT-230** stays `fixed` (not upgraded to `verified`): the defect itself is genuinely closed and
  I proved it independently, but the unit did not PASS, and upgrading a row on a FAIL is the kind
  of claim-outrunning-check the sweep exists to catch.
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
