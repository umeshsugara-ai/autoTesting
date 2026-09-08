# Contract — EXPLORE stage (the bounded BFS crawl)

**Covers:** goal tasks T-140 (B1 observation primitives), T-141 (B2 identity + crawl schema),
T-142 (B4 safety layer), T-143 (B3 the crawl stage itself).
**Owner:** /checker. **Criticality:** HIGH — this is the only code in the repo that decides on
its own what to click, and it does so in a real, usually logged-in browser against a production
product. Every other stage replays what a human authored.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B5-B9),
`execute.md` **E5 — explicitly preserved, never amended by this contract** (see X1).
**Authorized by:** D-015 (the stage and its file layout) and D-016 (the safety matrix).

## Purpose

Discover a product's screens without being told they exist: open `base_url`, enumerate the
interactive controls, click the safe ones, fingerprint wherever that lands, and repeat
breadth-first until a bound stops it — producing a screen graph on disk plus the problems noticed
on the way.

`execute.md` E5 says `run_case` "performs exactly the actions in `case.steps` — it never invents
an extra click, submit, or navigation." A crawler is by definition the invention of clicks. Rather
than weaken E5, D-015 puts the invention in one place, under this contract, with brakes. **E5
remains the rule for `run_case`; this contract is the single, bounded exception, and it is an
exception about *clicking*, never about *typing* (X10).**

The prior attempt at this failed five specific ways — URL-only identity (every SPA state
invisible), an LLM-text stop condition that never fired, `beforeunload` dialog traps, analytics
noise reported as product bugs, and "coverage" that only meant the script ran. X3, X12, X8, X9
and the B5 coverage work exist against exactly those.

## Criteria

### X1 — E5 stays intact; this is the only stage that invents an action
`stages/explore.py` is the sole module permitted to originate a click or navigation the human did
not author. `run_case` is unchanged in behaviour and its contract is unamended. The explorer calls
`run_case` for exactly one thing: the human-authored login bootstrap case.
**Verify:** `execute.py` and `execute.md` are absent from the unit's diff; `grep -n run_case
src/autotester/stages/explore.py` shows one call site, inside `_bootstrap_login`.

### X2 — Every browser touch goes through `browser/`
No `playwright` import and no `.page.` access anywhere in `src/autotester/` outside `browser/`.
The explorer composes `BrowserSession` methods; it never reaches past them.
**Verify:** `tests/test_actuator_chokepoint.py`, and the grep above returning nothing.

### X3 — Screen identity is structural
A `ScreenNode` id is a pure function of `(templated URL path, structural signature of the visible
non-row interactive elements)` — never URL alone, never a model's free-text description. Two list
pages differing only in row data are ONE screen; two states at one URL offering different controls
are TWO. The same page always yields the same id, whenever it is visited.
**Verify:** `/students/1/` and `/students/2/` collapse to a single `/students/{id}` node, and the
same-URL filter toggle produces a second `/` node — both against a real browser.

### X4 — Bounds fire, and name themselves
`max_screens`, `max_actions`, `wall_clock_s` and `max_depth` each actually end the crawl, and the
one that fired is named in `Crawl.stop_reason`. Bounds are checked before every node and before
every action, so a bound cannot be overshot by a whole node. A crawl always terminates and always
records why.
**Verify:** one test per bound, wall-clock driven by an injected clock rather than real sleeping.

### X5 — `write_policy` is enforced — the D-016 matrix
The first runtime enforcement of `Project.write_policy`, as an INNER guard inside Umesh's outer
boundary (the test account's own permissions):

| policy | destructive-name deny-list | form submits | typing |
|---|---|---|---|
| `READ_ONLY` | ON | never clicked | never |
| `TEST_ACCOUNT` | ON | allowed | never |
| `ALLOW_WRITES` | OFF | allowed | never |

**Verify:** against a real browser, a Delete-labelled control is never clicked under `READ_ONLY`
and IS clicked under `ALLOW_WRITES` — the same fixture, both directions.

### X6 — Session-ending controls are never clicked, at any policy
Logout/sign-out is refused under every `write_policy`, including `ALLOW_WRITES`, and the refusal
is checked against the module-level baseline, not against an overridable policy field — no
configuration can narrow it, only widen it (AT-092). An unnamed non-link control is skipped and
counted, never clicked blind (D-004: a rule decides only where it is certain).

**Known and accepted limitation (D-016, not a defect to re-raise):** the deny-list matches on a
control's *name*. A destructive control the list does not name IS clicked — verified live: a
button relabelled "Obliterate" was clicked and reached the delete sentinel. D-016 accepts this
deliberately, because the real boundary is what the test account is permitted to do. Widening the
pattern set is maintenance, not a contract violation.

**Known OPEN gap against this criterion:** `AT-093` — `Log-Out`, `LOG_OUT`, `Log.Out` and
`Sign-Out` are NOT denied, because the never-click patterns tolerate only `\s`/`\w` between the
two words. Re-verified live at T-143. X6 is therefore **not** clean today for
punctuation-separated labels; this must close before the explorer is pointed at a real product
(T-145).

### X7 — The host is re-checked after EVERY action
Not only on `goto`. A click that navigates off-domain is caught by re-checking
`session.current_url()` after the action completes — the case plain destination-checking on
navigation never saw. A refusal produces an `OFF_DOMAIN_REFUSED` edge plus a `NAVIGATION` issue,
and then recovery (back → the node's own URL → `base_url`), never a silent continue. No node is
ever created from an off-domain page.

### X8 — Dialog circuit breaker
Every JS dialog is recorded. `beforeunload` is accepted; every other dialog is dismissed. More
than `dialog_repeat_limit` dialogs on one node aborts that node — and the crawl continues with the
rest of the frontier rather than hanging. The prior attempt was permanently trapped here.

### X9 — Third-party noise is not a product issue
A failed request becomes a `CrawlIssue` only when the host is first-party. Declared analytics and
tracker hosts are dropped entirely; any other third party is tallied as noise and never reported
as a bug. A first-party 404 IS an issue.

### X10 — Nothing is typed
The explorer never calls `fill`, `select_option`, or `upload`. It does not invent form data, ever.
The only typing that happens on a crawl is the human-authored login case executed through
`run_case`. This is the hard half of X1's exception: the explorer may invent a *click*, never a
*value*.
**Verify:** `grep -n 'fill\|select_option\|upload' src/autotester/stages/explore*.py` returns
nothing.

### X11 — Artifacts are incremental, human-readable, and survive a crash
Nodes, edges and issues are JSONL and the crawl envelope and frontier are JSON, under
`projects/<slug>/crawl/<crawl_id>/`. They are written *as the crawl proceeds*, not assembled at
the end, so a crawl killed partway leaves a graph that still loads (C6). A node's final status
must reach disk — `add_node` is idempotent, so a status transition requires `update_node`;
without it a fully explored graph records every node as `queued` forever.

**Scope of the crash guarantee (honest limit):** append-only writes never rewrite an earlier line
and whole-file writes are atomic (tmp + `os.replace`), so a kill *between* writes is safe and
provably leaves a loadable partial graph. A kill *during* a single line's append is NOT covered:
`read_jsonl` raises on a malformed row rather than skipping it, so a torn final line would make
the file unloadable. Claim only what the ordering supports.

### X12 — The crawl is DOM-driven and deterministic; a model never chooses an action
`run_crawl` takes no provider at all. No stop condition, no action choice, and no safety decision
depends on model output — a crawl completes with `provider=mock`. A model's only permitted role
anywhere in this stage is *naming* an already-discovered screen for human readability. Vision-guided
action choice was explicitly rejected by D-015. This is what keeps the crawl reproducible and its
failures debuggable, and it is why the whole stage can be proven without a credential or an API key.

### X13 — A crawl may propose screens, never approve them
`stages/explore_merge.py::merge_screens` **never rewrites an existing `Screen`** — a human-named
or human-reviewed screen survives a merge byte-identically. When the merge adds anything, the
spec's `Review` is reset to `DRAFT` and `version` is bumped, so a `FlowSpec` can never carry
`approved` over screens no human has seen. When it adds nothing the spec is returned untouched:
re-merging the same crawl produces no version bump, no second review reset and no duplicate
conflict, and the persisted `flowspec.json` is byte-identical.
**Verify (both directions, and the gate must be load-bearing):** set a spec to `APPROVED`, merge a
crawl with one new screen, confirm `DRAFT`; merge the same crawl twice and diff the persisted file
byte-for-byte; **and sabotage the `Review(...)` reset — at least one test must fail.** A reset no
test defends is a decorative human gate.

### X14 — A disagreement between SOURCES is kept, never resolved
When a crawled screen claims a `url_pattern` an already-known screen claims under a different
name, **both screens survive** and a `Conflict` records both claims with both `source_ref`s. The
merge never picks a winner and never overwrites: silently resolving is how a product map stops
matching the product. The same conflict is not recorded twice on a re-merge.

**Deliberate exception, judged and UPHELD by the checker (2026-09-08), and WIDENED from "the same
crawl" to "both claims are structural" (2026-09-08, at103-conflict-scope):** two screens that both
carry a *structural* identity and share a `url_pattern` are **not** a conflict, however many crawls
found them. X3 requires two states at one URL
offering different controls to be TWO screens; a single source correctly modelling an SPA is not
two sources disagreeing, and raising a `Conflict` there would file a false one on every SPA in
every product. Verified live on the fixture site: 7 screens across 6 url patterns, 0 conflicts.
A `Conflict` means *sources disagree*, not *patterns collide* — this criterion pins that meaning.

Only a claim with **no** structural identity — a human's or an ingested video's screen, which
asserts a URL and nothing more — can be contradicted by a crawl. **AT-103 is CLOSED by this
scoping** (`_is_structural` / `_disagreement`, `stages/explore_merge.py`).

**Two residuals of the current rule, tracked rather than written out of it** (neither is a
violation of this criterion as written; both are ledger issues to be closed by a later unit):
**AT-102** — the clash test is `clash.name != incoming.name`, so a re-discovered screen at a known
pattern under the *same* name is added as a silent duplicate with no `Conflict` to explain it;
**AT-109** — the price of scoping on identity: a **genuine product change** (a later crawl finding
a structurally different screen at a pattern an earlier crawl claimed) is now silently two screens
and files no `Conflict`, so the stale screen is kept forever with nothing marking it stale. That
trade is deliberate — at this layer a product change and an SPA re-crawl are the same shape, and
the alternative fires a false conflict on every SPA state on every re-crawl — and it costs no data
(both screens survive, `Review` still resets to DRAFT). The remedy is a *different* mechanism,
last-seen/staleness on `Screen`, not a re-narrowing of the exemption.

### X15 — `Screen.url_pattern` is a host-less path, not the node's browsing template
`ScreenNode.url_template` carries a host (it is a browsing identity); `Screen.url_pattern` is a
path pattern, because that is what `stages/coverage.py` and `stages/ingest.py` compare against.
`screen_from` therefore derives it as `url_template(node.url_example, keep_host=False)` and never
copies `node.url_template`. Copying the template verbatim would make every coverage diff miss.
**Verify:** every merged `url_pattern` starts with `/`, and `/students/1` and `/students/2`
collapse to one `/students/{id}` screen.

### X16 — The crawl report shows what was REFUSED and why it STOPPED
A bounded crawl reported as only what it found reads as full coverage of the product. Both the
crawl page and the workbook therefore give `Crawl.stop_reason` equal billing with the headline
counts, and both list **every** `DENIED_POLICY` / `SKIPPED_UNNAMED` / `OFF_DOMAIN_REFUSED` edge
with its `reason` and the control it names. Third-party noise counted under X9 is recorded in the
workbook's own `Noise` sheet — "we ignored it" stays auditable — and never appears as a
`CrawlIssue`. The workbook is
`Summary / Screens / Edges / Denied & Skipped / Issues / Tool failures / Noise`.
**Known gap, tracked not waived: AT-105** — the noise counts reach the workbook only; the crawl
page does not surface them.

**A failure of the CRAWLER is not a finding about the PRODUCT.** When the tool itself cannot record
something — a screenshot it could not take — it files an `IssueKind.EVIDENCE` issue rather than
inflating the product's issue list, which is X9's principle applied one step closer to home
(AT-114, upheld by /checker 2026-09-08). **The separation must hold in the NUMBERS, not only in
the enum:** `Crawl.tool_failures` counts EVIDENCE issues apart from `Crawl.issues`, and every
surface a human reads keeps them apart — the workbook's `Issues found (in the product)` /
`Tool failures (the crawler's own)` summary rows and its own `Tool failures` sheet, the crawls
table's own column, and the crawl page's own stat and card. They are counted apart and reported,
never dropped: each one is a hole in the evidence the rest of the report is built on, so the same
"we did not report it stays auditable" rule that governs `Noise` governs them.
**AT-120 CLOSED** (unit `at120-evidence-not-product-issues`, commit `bc29b34`, verified by
/checker 2026-09-08 — the same probe that measured `issues = 5` at `6e98487` now measures
`issues = 1, tool_failures = 4`). **X16 is clean for tool failures.** Residual gaps, tracked not
waived: **AT-121** (the crawls table renders a known zero as the `—` it uses for unknown) and
**AT-122** (the `autotester crawl` CLI one-liner reports the product's issues and omits the tool
failures entirely).

## No-fire list (do not raise these as findings)

- Filling forms with synthetic data, and vision-guided action choice — both rejected by D-015/X10.
- Resuming an interrupted crawl, parallel tabs, and CI triggers — not built, not claimed.
- `EvidenceKind.TRACE`.
- Auto-generating cases from crawl screens — that is `expand.py`, after human review.
- Auth bypass or 2FA automation; a wildcard for `allowed_domains`.
- Crawl → FlowSpec merge, coverage from observed screens, and the crawl report (Excel + UI page) —
  that is B5/T-144, explicitly out of T-143's scope.
- The name-based deny-list being incomplete *in principle* (X6's accepted limitation, D-016). A
  specific missing pattern class is a normal issue; the design choice is settled.
- The 8s settle default in `session.settle` being different from the crawl's 2500ms — deliberate
  and documented: a graded case performs a handful of actions, a crawl performs hundreds.
- Auto-generating cases from crawled screens (that is `expand.py`, after human review); naming
  screens with a model (`prompts/explore_name_screen_v1.md` is designed for and deliberately NOT
  built — X12 keeps the crawl provider-free); background/async crawling from the UI (synchronous,
  the same trade-off `routes_runs.py` already makes); resuming an interrupted crawl; merging
  crawl-discovered *flows* (only screens are merged); editing a merged screen from the crawl page.

## Amendment log (append-only; git history is the version)

- 2026-09-07 · init · contract created at T-143 by /checker, from the criteria the maker filed in
  `qa/feedback-inbox.md` (2026-09-07) — the maker never writes a contract. Changes made to the
  maker's proposed X1-X11 while authoring: **added X12** (DOM-driven/deterministic; a model may
  name a screen but never choose an action), which the maker's list omitted although D-015
  authorizes "explore.md X1-X12" and rejects vision-guided crawling by name — restoring the count
  the decision names; **tightened X6** with the live-verified "Obliterate" limitation (accepted
  per D-016) and with AT-093 recorded as an OPEN gap rather than letting the criterion read clean;
  **tightened X11** to state the exact scope of the crash guarantee, since `read_jsonl` raises on
  a torn row and the append-only ordering only supports the between-writes claim; added the
  settle-ms and deny-list-in-principle rows to the no-fire list so neither is re-litigated.
  `execute.md` E5 is untouched and stays the rule for `run_case`.

- 2026-09-08 · routine · **X13-X16 added** at T-144 (Track B5) by /checker, from the criteria the
  maker filed in `qa/feedback-inbox.md` (2026-09-08). Authorized by D-015, whose
  `Changes-authorized` names `qa/contracts/explore.md` and `coverage.md V1 after B5`. Adds
  criteria, softens none; X1-X12 are byte-unchanged and were re-verified in the same check
  (`scripts/explore_proof.py` 10/10; `run_case` still one call site in `_bootstrap_login`; no
  `playwright` import or `.page.` access outside `browser/`; `grep fill|select_option|upload`
  over every module this unit added returns nothing). Changes made to the maker's proposed
  wording while authoring: **X13 gained a mandatory sabotage clause** — the DRAFT reset must be
  defended by a test that fails when the reset is removed, because a human gate no test defends is
  decorative (executed: `status=ReviewStatus.DRAFT` → `status=spec.review.status` fails
  `test_new_screens_are_added_and_review_resets_to_draft`); **X14's exception was judged on its
  merits and UPHELD**, and re-stated as *sources disagree, not patterns collide*, with the two
  residuals of the current implementation (AT-102 same-name silent duplicate, AT-103 cross-crawl
  false conflict) recorded in the criterion rather than left implicit; **X16 was tightened** to say
  where noise is auditable and to record AT-105 (the crawl page omits it) as a tracked gap rather
  than letting the criterion read clean. The maker's offered no-fire list is folded in above.

- 2026-09-08 · routine · **X14's exception re-scoped** from "the same crawl" to "both claims carry
  a structural identity", by /checker at unit `at103-conflict-scope` (commit `ef881b9`, verdict
  `qa/verdicts/at103-conflict-scope.md`). This is what X14's own AT-103 residual paragraph
  prescribed on 2026-09-07 — *"the exemption is right; its scope is one crawl rather than one
  source"* — so it records a change the criterion asked for rather than softening one to pass an
  artifact. Verified by the checker against the pre-fix module (`git show a195fbf:…`) run beside
  HEAD: the same SPA pair merged as crawl 1 then crawl 2 gives `conflicts=1` before and
  `conflicts=0` after, `screens=2` both sides. X14's core is unchanged and re-proven by sabotage —
  suppressing conflicts wholesale (`_is_structural → return True`) fails three tests, including
  `test_a_human_authored_claim_is_still_contradicted_by_a_crawl`. **AT-103 removed from the
  residual list (closed); AT-109 added** — the cost of the new scope, stated inside the criterion
  rather than left implicit. No criterion is removed or weakened; X1-X13, X15, X16 are
  byte-unchanged.

- 2026-09-08 · routine · **X16 tightened** by /checker at unit `at108-at114-swallowed-causes`
  (commit `6e98487`, verdict `qa/verdicts/at108-at114-swallowed-causes.md`). Records the new
  `IssueKind.EVIDENCE` member and the rule it exists for — a failure of the crawler is not a
  finding about the product — after ruling on the design call the maker put to the checker. The
  ruling: an **additive** enum member that weakens no criterion, reverses no goal direction and
  enables no outward-facing action is a routine amendment under D-015 (which already authorizes
  this stage, its file layout and this contract), not a new DECISIONS entry; the alternative
  (filing screenshot failures as `NAVIGATION`) was rejected on the same grounds X9 rejects calling
  third-party noise a product bug, and the maker's second test fails under that lazy fix — verified
  by the checker's own sabotage run. `capture()` staying non-fatal was also upheld: AT-114's defect
  is the SILENCE, not the survival, and killing a crawl over a missing screenshot trades X11's
  crash-survivable partial graph for no graph at all. **AT-120 added as an OPEN gap** — the
  separation is real in the enum and absent in every count and report a human reads — stated inside
  the criterion rather than left implicit. No criterion is removed or weakened; X1-X15 are
  byte-unchanged.

- 2026-09-08 · routine · **X16's AT-120 gap CLOSED and the criterion restated** by /checker at unit
  `at120-evidence-not-product-issues` (commit `bc29b34`, verdict
  `qa/verdicts/at120-evidence-not-product-issues.md`). The gap this checker opened one unit earlier
  is closed on its own re-executed probe, not on the maker's transcript: the fixture crawl whose
  every screenshot fails reported `crawl.issues = 5` with kinds `{evidence: 4, navigation: 1}` at
  `6e98487` and now reports `issues = 1, tool_failures = 4`, with the workbook's `Issues` sheet
  carrying the one product row and the new `Tool failures` sheet carrying the four. The criterion
  is **tightened, not softened**: it now names the counter, the two summary rows, the sheet, the
  column, the stat and the card, so the next kind-blind regression fails the contract and not only
  a test. The workbook sheet list is amended to add `Tool failures` between `Issues` and `Noise` —
  a legitimate contract change the unit earns, and the pinned exact ordered list in
  `tests/test_crawl_report.py::SHEETS` was checked to still be an `==` on the full list rather than
  a subset. Two residual display gaps (AT-121, AT-122) recorded inside the criterion rather than
  left implicit. Authorized by D-015. No criterion is removed or weakened; X1-X15 are byte-unchanged.
