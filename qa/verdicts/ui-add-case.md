# Verdict — ui-add-case

**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-add-case.md
**Cycle checked:** 1
**Date:** 2026-09-07
**Checker:** /checker Mode A, fresh context, bound to `d:/autoTesting`
**Mode:** Mode A unit check. Adapter `qa/adapter.json` (coding) — verify = shell/tests.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (U1-U5 + the new U6 this unit earns), 0 open violations
FAILURES: none
ISSUES-WRITTEN: AT-060 (medium, new) · AT-057 open → fixed
EXPLANATION: Every verify command was re-run by me inside the container and every
one matched the manifest. The add-a-case path was probed hostilely on a scratch
project whose name and base_url carried `<script>`, `'` and `"`; nothing broke out
of any attribute. A case created through the real HTTP form is a genuine
schema.case.Case in projects/<slug>/cases.jsonl with a content-addressed id, a
kind derived from case_class, and rationale None. All five refusal paths return
400/404 and write nothing to disk. The two deferred issues (AT-058, AT-059) are
genuinely outside ui.md U1-U5 and were filed honestly. One new silent-discard gap
found while probing (AT-060) is not a violation of any current criterion.
```

## What I re-ran myself (nothing pasted was trusted)

| Command | My result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | 295 passed, 1 skipped, 0 failed |
| `docker compose exec -T autotester uv run pytest -q tests/test_ui_cases.py` | **9 passed** — matches the manifest's claim exactly |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` |
| Live HTTP against `http://localhost:8010` | see the probes below — all driven by me, not by the maker's script |

Container `autotesting-autotester-1` was up and serving; the repo is bind-mounted at
`/app`, so the code I tested is the code in this working tree.

---

## Criterion-by-criterion

### U1 — Onboarding creates a real, CLI-compatible project — **MET**, and extended

The unit does not change `onboard_submit`; it adds the case-creation half. I verified
the *new* write path meets the same standard U1 sets for projects:

I onboarded a scratch project `xssprobe` over HTTP and posted a case through the real
form, then read it back **through `ProjectStore` inside the container**, not through
the UI:

```
autotester.schema.case Case  isinstance(c, Case) = True
id case_550fbae037d8   recompute case_550fbae037d8   id == compute_id() -> True
kind best   class happy   rationale None   flow_id manual
orders [1, 2]
```

and the raw file on disk (`projects/xssprobe/cases.jsonl`) is one ordinary JSONL row
of exactly the shape `stages/expand.py` writes — same `schema_version`, `created_at`,
`content_id`-shaped id, `preconditions`, `severity`, `status`. **No UI-only
representation and no second store exists:** `routes_cases.py:152` calls
`store.add_case(Case(...))` and nothing else; there is no other write in the module.

**`kind` genuinely cannot be set inconsistently.** It is not a form field. Line 155 is
`kind=KIND_BY_CLASS[parsed_class]`, keyed off the same `parsed_class` the case stores.
I attacked this directly: I posted `kind=worst`, `id=forged` and
`rationale=INJECTED PROVENANCE` alongside `case_class=happy`. The persisted row came
back `kind: "best"`, `id: case_550fbae037d8` (content-addressed, not `forged`) and no
`rationale` key at all. `create_case` reads only `title` and `case_class` from the form
plus the four `getlist` step fields, so extra fields are inert by construction rather
than by filtering.

### U2 — Project detail reflects real state, no caching/duplication — **MET**

`_actions_card` (app.py) is passed the `case_count` `project_detail` already computes
live via `ProjectStore` on every request; it introduces no state of its own. Live:
`/projects/xssprobe` showed the "No cases yet" prompt before the POST and, on the very
next GET after it, the prompt was gone (`grep -c "No cases yet"` → 0) and the Run
control was the real `<button class='btn btn-primary' type='submit'>▶ Run tests</button>`
rather than the disabled span. `GET /projects/definitelynope` → **404**, not an empty
page. `new_case_form` and `create_case` both enter through
`helpers._load_project_or_404`, so an unknown slug 404s on the new routes too — I
confirmed `POST /projects/nosuchproj/cases` → **404** and that no `projects/nosuchproj`
directory was created.

### U3 — The env editor never renders a real secret value — **UNAFFECTED, re-verified**

This unit adds no `SecretStore` or `.env` call — `routes_cases.py` imports neither.
`GET /projects/xssprobe/env` → 200 and the existing credential tests pass in the full
suite. The `+ Add case` action added to the project page is a plain link.

### U4 — Run/report views read real persisted evidence — **UNAFFECTED, re-verified**

No run/report code changed. `GET /projects/xssprobe/report` on a project with no runs
→ **200** with `no runs yet — run a case against this project to see a report here.`,
exactly U4's "reports that plainly, not an error".

### U5 — User-supplied values are HTML-escaped — **MET** (hostile probe, not one payload)

I read `routes_cases.py` in full and then attacked it, because this is a brand-new
form surface that renders user-controlled values into an attribute.

Scratch project onboarded with:

```
name     = <script>alert(1)</script>&'"X
base_url = https://x.test/a' onmouseover=alert(2) x="><script>alert(3)</script>
```

`GET /projects/xssprobe/cases/new` (20,532 bytes) rendered:

```html
<input name='step_target' value='https://x.test/a&#x27; onmouseover=alert(2) x=&quot;&gt;&lt;script&gt;alert(3)&lt;/script&gt;' …>
```

- `grep -c "<script"` over the whole response → **0**. Not one raw tag.
- The single quote — the character that would end the attribute — came out `&#x27;`,
  the double quote `&quot;`, the angle brackets `&lt;`/`&gt;`. `html.escape` defaults
  to `quote=True`, which escapes both quote characters, and the attribute is
  single-quoted, so **neither** quote style can terminate it.
- The project name rendered escaped in all three places it appears (`<title>`,
  sidebar, breadcrumb).
- `/projects/xssprobe` (the detail page carrying the same name) → `grep -c "<script"` → 0.

Every user-derived string in the module goes through `escape()`: `_options` escapes
both the option `value` and its text; `_step_row` escapes `target`; `new_case_form`
escapes `slug` and `project.name`. The two non-escaped interpolations are
`RedirectResponse(f"/projects/{slug}")` and the `action=` URL — and `slug` has already
passed `helpers._SLUG_RE` (`^[a-z][a-z0-9-]*$`) inside `_load_project_or_404` before
either is built, so no user-controlled string reaches an href/Location.

One thing I checked because it is the usual leak in this pattern: the 400 bodies echo
user input (`unknown action '<script>x</script>'`). FastAPI serves them as
`content-type: application/json`, not HTML, so there is no injection there either —
verified on the wire.

### U6 (new, added by this verdict) — A case is creatable from the UI — **MET**

See the contract amendment below. Evidence is U1's and U2's above: the full loop
onboard → add a case → run is reachable over HTTP with no CLI call.

---

## Point 3 of the dispatch — refusals write NOTHING

I did not trust the status codes. `projects/xssprobe/` contained **only**
`project.json` before the rejection series and **still contained only `project.json`
after all four** — `cases.jsonl` was never created:

| Posted | Status | `cases.jsonl` after |
|---|---|---|
| blank title (`"   "`) | 400 | absent |
| zero surviving steps (all rows blank) | 400 | absent |
| `case_class=bogus` | 400 | absent |
| `step_action=teleport` | 400 | absent |
| unknown project `nosuchproj` | 404 | no project dir created |

The ordering in `create_case` is what makes this true rather than lucky: project lookup,
then title, then class, then `_build_steps` (which raises on an unknown action), then
the empty-steps guard — `store.add_case` is the last statement in the function and is
unreachable from any of the five paths.

## Point 4 of the dispatch — the rationale/rubric causal chain

The manifest's account is **accurate in every link**, verified in the code myself:

1. `stages/run_case_pipeline.py:29` —
   `claim = case.rationale or f"the case '{case.title}' completes as its steps describe"`.
   `case.rationale` is fed to the grader **verbatim as the claim to judge evidence
   against**. So `rationale="added by hand from the UI"` really does produce the claim
   "The evidence is consistent with: added by hand from the UI", which no screenshot of
   a sign-in page can satisfy. The hallucinated `no UI addition step was performed` FAIL
   is the expected output of that rubric, not a model misfire.
2. The fix is real: `routes_cases.py:165` is `rationale=None`, with a comment naming the
   incident. I confirmed the effect end to end — the rubric generated from my own
   form-created case reads
   `The evidence is consistent with: the case '<the title I typed>' completes as its steps describe`.
3. The regression test genuinely prevents recurrence:
   `test_rationale_is_not_provenance_because_it_feeds_the_grading_rubric` asserts both
   the stored value (`case.rationale is None`, `case.flow_id == "manual"`) **and** the
   generated criterion text (`"Sign-in page loads" in claim`, `"from the UI" not in claim`).
   The second assertion is the load-bearing one — it fails if anyone ever puts
   provenance back in `rationale`, because it checks the grader-visible artifact rather
   than the field. That is the right place to pin it.

## Point 5 of the dispatch — honesty of the deferrals, and the `erp` data fix

**AT-058 (onboarding accepts a self-contradictory `allowed_domains`) — legitimate deferral.**
It is a defect in `onboard_submit`, a route this unit does not touch, and no criterion
U1-U5 requires semantic cross-validation of `base_url` against `allowed_domains` (U1 asks
only that a real, CLI-compatible `Project` be persisted, which it is — the schema accepts
it). The maker's refusal to "fix" it by adding a wildcard is correct and matches the
project's own hard boundary: `Project.allows_domain` is the browser's navigation gate.
Deferring it does not make THIS unit incomplete.

**AT-059 (stale rubric never invalidated) — legitimate deferral, and this unit closes its
own contribution to it.** I verified the mechanism: `Case.compute_id()` (schema/case.py:38)
hashes only `(project, flow_id, case_class, steps)`; `run_case_pipeline.py:50-54` keys the
rubric `rub_{case.id}` and does `load_rubric` first, `save_rubric` only when absent — so a
stored rubric outlives any change to the claim it was built from. That is a `grade`-feature
bug, not a `ui.md` one. Crucially for this unit, **its own flow can no longer trigger it**:
the form has no rationale input and always writes `None`, so two UI-created cases with the
same steps can never disagree about the claim. The dispatch's concern that "this unit's own
flow can trigger it" was true of the pre-fix version and is no longer true of the shipped
one — I probed for the residual path (same steps, different title) and found it produces a
no-op rather than a divergence (that is AT-060 below, a UX gap, not a grading-correctness one).

**The `erp` data correction is disclosed accurately and is genuinely data.**
`projects/erp/project.json` now reads `allowed_domains: ["vidysea.com", "www.vidysea.com"]`
against `base_url: https://www.vidysea.com/erp` — the change the manifest describes.
`git status --porcelain -- src tests scripts docs` shows the entire code surface of this
unit is exactly `M src/autotester/ui/app.py`, `?? src/autotester/ui/routes_cases.py`,
`?? tests/test_ui_cases.py` (plus `M docs/MAP.md`, `M docs/SNAPSHOT.md`). There is **no
code change hidden anywhere in the diff** that widens or special-cases `allowed_domains`;
`Project.allows_domain` is byte-identical to its committed version. `projects/erp/` is
untracked runtime data and was deliberately left out of the commit.

## New finding — AT-060 (medium), not a criterion violation

Submitting a case whose steps duplicate an existing one is **silently discarded**:
`add_case` is idempotent on the content id and returns without appending, and
`create_case` never compares what came back with what it built, so the user gets a 303
and no case. Reproduced: posting `title=A completely different title` with the same two
steps left `cases.jsonl` at one row still carrying the *original* title. Since `title` is
excluded from `compute_id`, this is also the only way a user could try to correct a
mistyped title — and it fails silently. Filed as AT-060, open. This violates no current
U-criterion (U1 asks that a created case be real and CLI-compatible, which it is), so it
is a finding, not a FAIL.

## Contract amendment applied (routine, auto gate — "add criterion")

`qa/contracts/ui.md` gains **U6 — A test case is creatable from the UI** plus a
2026-09-07 amendment row. The previous amendment row explicitly said AT-057 "needs its
own contract-scoped cycle and a scoping decision before a criterion can be written for
it"; that cycle is this unit, the scoping decision came back "both" (an add-a-case flow
*and* an empty-state prompt), so the criterion is now writable. Adding a criterion is a
routine, non-weakening amendment. This also pre-empts the AT-056/AT-043/AT-048 staleness
pattern of shipping a unit with no contract-side trace.

## Ledger

- **AT-057** — `open` → `fixed` (fixed_date 2026-09-07), with the checker-verified evidence.
- **AT-058, AT-059** — left `open` as filed. Correct.
- **AT-060** — new, medium, open.

## Housekeeping

Scratch project `projects/xssprobe/` created for the hostile probes was deleted
(`projects/` now holds only `erp`, `pathlynks`, `regression-demo`, `vidysea-erp`).
No `.work/` or `projects/erp/` path was committed.

## Per the AT-055 lesson — source commit state

The maker's source changes were **not committed** when I arrived: `routes_cases.py`,
`tests/test_ui_cases.py` and the manifest were untracked, and `app.py`/`docs/MAP.md`
were modified-uncommitted — the exact AT-055 failure mode. **I committed them myself**
with a narrow pathspec covering `src/autotester/ui/routes_cases.py`,
`src/autotester/ui/app.py`, `tests/test_ui_cases.py`, `docs/MAP.md`,
`qa/manifests/ui-add-case.md`, `qa/issues.jsonl`, `qa/contracts/ui.md` and this verdict.
`qa/feedback-inbox.md` had no pending change to commit — it was already clean in the
working tree, so nothing of this unit's was left stranded there.

Commit: **1652de5** — `checker: PASS verdict on ui-add-case (cycle 1) + the unit's
source changes` (8 files: the three source/test files, `docs/MAP.md`, the manifest,
the ledger, the contract amendment, and this verdict). Deliberately excluded and still
uncommitted: `projects/erp/` (untracked runtime data, Umesh's), `docs/SNAPSHOT.md`,
`.goal/*`, `goal.md`, `qa/.last-tick` (hook/maker-owned bookkeeping, not this unit's).
