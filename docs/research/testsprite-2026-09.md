# TestSprite teardown — and what it says about our own gaps (2026-09-22)

**Purpose:** how TestSprite actually works, its architecture, and the ordered list of things worth
taking from it — plus the one idea of theirs we should refuse, and the gaps in *our* code this
exercise exposed.
**Open me when:** choosing a mechanism for the oracle, the failure bundle, or the CLI contract; or
about to claim AutoTester does something in the execution model.

Extends `docs/research/market-2026-09.md` (2026-09-03), whose commercial table covers Fume,
Momentic, QA Wolf, Checksum, Meticulous, mabl, testRigor and Autify — **TestSprite is absent from
it**. Nothing in this doc came from running TestSprite: Umesh's constraint was that no Pathlynks
URL, product, account or credential leaves the machine, so this is built from their public docs, CLI
reference and blog. Their CLI documentation is unusually explicit about mechanism, which is enough.

**The finding that matters most is not about them.** Verifying our side to write the comparison
showed that the three capabilities TestSprite ships are the three our own `docs/ARCHITECTURE.md`
claims and does not have. See §7 — those rows are the real output of this document.

---

## 1. What it is

IDE-native AI testing agent, aimed at being driven by a **coding agent** rather than a human.

| | |
|---|---|
| Distribution | CLI (`npm i -g @testsprite/testsprite-cli`, Node ≥20.19) + **MCP server** + installable skill files for Claude, Cursor, Cline, Windsurf, Antigravity, Kiro, Copilot, Codex (`agent install <target>`) |
| Pricing | Free 150 credits/mo · Starter $19 (400) · Standard $69 (1,600) · Enterprise custom; −30% yearly |
| Unit costs | frontend run 0.5 credit · backend run 0.2 · PRD embedding 0.5 · `test plan generate` variable, prints credits used |
| Languages out | Python only — Playwright async (frontend), requests+pytest (backend) |
| Credentials | `~/.testsprite/credentials`, INI, mode `0600`; `TESTSPRITE_API_KEY` overrides |

## 2. Architecture — where each piece runs

```
YOUR MACHINE                              TESTSPRITE CLOUD
──────────────                            ────────────────
testsprite CLI ───── API key ──────►      control plane
  ~/.testsprite/credentials (0600)          projects · envs · tests · testlists · schedules
                                                │
coding agent ──► MCP server ──────►             ├─ exploration + feature map   (PRD + live app)
                                                ├─ proposal staging            (server-side)
                                                ├─ generation → Python          (versioned, etag)
your app ◄──── TLS tunnel ─────────►            └─ execution sandbox: real browsers, parallel
  --local <port>                                       │
  data.tun.testsprite.com:443                          └──► failure bundle (one snapshotId)
  cert verification mandatory
  1 live tunnel per credential
```

**Everything of substance runs in their cloud.** `--local <port>` tunnels your dev server out — the
app stays local, the browser driving it does not. Tunnel details: `tunnel start --ttl 60–28800`,
10s connect/handshake timeouts, `tunnel status|stop`, max 5 live bindings per user, one test per
`--local` invocation, a second `tunnel start` takes over the first (exit 10).

For us the architecture is the point of interest, not the product: **we are local-first by
construction** (headed Playwright against a persistent profile, secrets never leaving the machine).
Their model is the opposite trade — their sandbox is why they can fan out to many parallel browsers,
and why they need `auto-auth` and an OTP field in every environment.

## 3. How it works, end to end

1. **Ingest.** `project docs upload --role prd|api-doc` (md / PDF / text) → extracts features and
   use cases into a flow graph. A PRD is optional but "strongly recommended". Alternatively the MCP
   server infers intent from the codebase.
2. **Explore + plan.** `test plan generate` walks the **live app** feature-by-feature against the
   feature map. For APIs it reads endpoints from the spec *and probes the base URL to confirm actual
   shapes* — spec plus observation, not spec alone.
3. **Human gate.** Proposals **stage server-side**; you select / deselect / edit; `test plan accept
   --only <ids>` converts a chosen subset into real tests. Generation happens *after* approval.
4. **Plan format.** JSON with a version-pinned `$schema`. `planSteps` = 1–200 entries of
   `{type: "action" | "assertion", description}` in **plain language, explicitly not selectors**.
   `priority: p0|p1|p2|p3`. ≤256 KB single, ≤5 MB / 50 specs batch. `{{...}}` placeholders are *not*
   substituted — credentials live on the project. `test scaffold` and `test lint` run offline with
   no credentials.
5. **Execute.** `test run [--wait --timeout <s>] [--local <port>] [--report junit] [--target-url]`.
   Generated Python is **retrievable (`test code get`) and replaceable (`test code put`)** with an
   etag (`codeVersion`) for concurrency control.
6. **Failure bundle.** `test failure get` returns one directory in which **every artifact shares a
   single `snapshotId`**, and the CLI refuses to stitch a failing step from one run to source from
   another:
   ```
   meta.json        runId · testId · snapshotId · status · failureKind
   result.json      verdict, timestamps, step counts
   test.py          the generated source, as run
   analysis.json    root-cause hypothesis + recommended fix target
   video.json       pointer (URL + duration)
   steps/{n}.json   the failing step AND its neighbours
   steps/{n}-screenshot.png · {n}-dom.html
   .partial         present if the write crashed mid-flight
   ```
   `test failure summary` gives a one-screen triage card with no downloads.
7. **Fix loop.** `create → run → failure get → fix → rerun`, the coding agent consuming the bundle.
8. **Maintenance.** `test rerun` replays **verbatim unless `--auto-heal` engages**.
   `test flaky --runs 1–10 [--until-fail]` measures stability. `test diff <runA> <runB>` exits 0
   when verdicts match, 1 when they differ.
9. **Ops.** Named environments (URL + test account + OTP), `project auto-auth`
   (password / refresh_token / aws_cognito_refresh), `project credential` for static backend auth,
   `project update --test-id-attributes <list>` for **locator priority order**, `testlist`,
   cron `schedule --timezone <IANA>`, `ci init github`, `--output json`, `--dry-run`, `doctor`,
   `usage`, idempotency keys on every mutation.
10. **Exit codes — 15 of them, documented.** 0 pass · 1 test failed · 3 auth/scope · 4 not found ·
    5 validation · 6 precondition · 7 unsupported/timeout · 10 unavailable · 11 rate limited ·
    12 insufficient credits · 13 feature gated · 14 client too old · 130 interrupted.

## 4. What to take, ordered by the gap it closes

Each is a separate future unit. "D-entry" means it changes an approach and so needs an authorizing
`docs/DECISIONS.md` entry first.

| # | Adoption | Closes | Value / effort | Gate |
|---|---|---|---|---|
| A | Persist the generated script and replay it | §7.1 | highest / high | D-entry; ARCHITECTURE.md must be corrected first |
| B | Implement the four dead assertion fields | §7.2 | highest / medium | D-entry (changes what a verdict means) |
| C | Semantic locators + declared attribute priority | §7.3 | high / low | none |
| D | Atomic failure bundle with one id | — | high / low | none |
| E | Differential oracle (base-vs-head replay) | §7.2 alt | high / high | D-entry + likely HUMAN_GATE |
| F | `--output json`, documented exit codes, `--dry-run` | — | medium / low | none |
| G | Stage case proposals for human pruning | — | medium / medium | D-entry (approval flow) |
| H | Case priority `p0..p3` | — | medium / low | D-entry (schema) |

**A — persist and replay the script.** TestSprite keeps generated Python, versions it with an etag,
and replays it verbatim. **That is precisely the script-first design our ARCHITECTURE.md already
promises** (§7.1). Our `Script`, `case.script_ref` and `agent_loop.run_with_fallback` all exist and
are simply unwired — this is wiring, not invention. A funded product shipping it is evidence the
design is sound.

**B — make the assertions real.** Their plan steps carry an explicit `type: "assertion"`. Ours has
`Action.ASSERT` as a literal no-op and four fields nothing reads (§7.2). Implementing them does
**not** violate C7 *"the executor never grades itself"* — a deterministic assertion is *evidence*,
and `grade.py` still owns the verdict. It removes the state where an LLM opinion on a screenshot is
the only oracle we have.

**C — semantic locators.** `project update --test-id-attributes <list>` declares locator preference
order. Adopt that *and* Playwright's `get_by_role` / `get_by_label`, so the promise in
`schema/flowspec.py:78` ("semantic locator: role/name/label, not a brittle CSS path") stops being
aspirational. Independent reviewers reported ~8% of TestSprite's *own* generated assertions were
brittle — pixel positions and dynamically generated IDs — so a declared priority list is the cheap
defence, and we have nothing equivalent.

**D — the atomic failure bundle.** The good idea is the integrity rule, not the file layout: one
`snapshotId`, self-contained, the failing step's **neighbours** included, `.partial` when a write
dies mid-flight, and a hard refusal to mix artifacts across runs. Our `qa/evidence/<unit>/` dirs are
human-browsable folders, not an agent-consumable unit. The `.partial` marker is the same fail-closed
instinct `scripts/mutation_check.py` already has, and that harness exists because four vacuous tests
once shipped in one session.

**E — the differential oracle, and why it is strategically interesting.** This is **Meticulous's**
mechanism, not TestSprite's, and `market-2026-09.md` summarises it only as "replay + pixel diff".
The mechanism detail is what matters: on each PR they replay the same recorded sessions **twice —
once against the base commit, once against the head** — screenshot after every dispatched event, and
diff the two. **The baseline is computed at replay time, so there are no golden files to maintain**,
and a human clicks "Approve all Visual Differences" to accept intended change. They also **replay
backend responses recorded at capture time**, so changing data cannot produce a false failure —
which attacks our live flake class (AT-196 / AT-505 / AT-518) at its root rather than its symptom.

> **A differential oracle needs no assertions at all.** Given we currently have zero deterministic
> assertions, this is a genuine *alternative* to **B**, not merely a complement — possibly a cheaper
> route to deterministic regression detection than building an assertion layer.

Honest blocker: it assumes two deployable builds of the app under test. For a hosted product like
Pathlynks we may only ever have "now", which would make this work for products we *build* and not
for products we *observe*. That distinction should be settled before anyone starts it.

**F — the CLI contract.** Their 15 codes separate *test failed* (1) from auth (3), validation (5),
timeout (7), insufficient credits (12) and client-too-old (14), so CI knows what to retry and what
to escalate. We learned the cost of unreadable verify output the hard way in **AT-503** — the pair's
own verify command was `uv run pytest -q`, which doubled against `pyproject.toml`'s `addopts` into
`-qq` and printed no summary line at all, causing two retracted "clean suite" claims. This is the
same lesson one level up. `--dry-run` that exercises code paths offline with no charges is cheap and
genuinely good.

**G — gate the cheap artifact.** They stage *proposals* for human pruning and generate only what
survives. We approve a FlowSpec but not `stages/expand.py`'s case list, so we spend one LLM call per
class (13 of 14) on cases a human would have deleted.

**H — case priority.** `p0..p3` lets a post-dev-cycle regression gate on p0 and run the long tail
nightly.

## 5. Where we are genuinely ahead — with the caveats attached

- **`test flaky --runs N --until-fail` is `scripts/flake_probe.py`.** We built it independently
  (AT-401, AT-495, AT-502), including a proven process-tree kill. Convergent design.
- **Their plan steps are plain language, not selectors** — the same intent as our FlowSpec.
- **Neither TestSprite nor Meticulous has anything like our unknown-screen escalation** (ask the
  human for a video rather than guess) **or our tester-vs-AI scorecard** (`schema/bench.py`).
  *Caveat, and it is a big one:* the escalation has fired exactly once, on a 0-screen fixture, and
  the scorecard has never run against a real human (§7.6). These are design advantages, not yet
  demonstrated ones.
- **We publish coverage we do not like.** `crawl_coverage.py` reports 45 of 677 controls (6%) rather
  than "20 screens found". No vendor dashboard tells you that. This is the most defensible thing in
  the repo and it should be treated as a feature, not an embarrassment.

## 6. The idea to refuse

**Do not adopt "regenerate the test instead of maintaining it."**

TestSprite's anti-flake position, verbatim: *"it doesn't maintain tests at all. It regenerates
them"*, and *"there are no stale selectors because the selectors are generated at test time."* Their
blog explicitly **rejects** the self-healing framing as guessing at a broken locator.

Nowhere do they explain how a regenerated test distinguishes an **intentional UI change** from a
**regression**. The answer offered is *"the agent reads your codebase and product requirements,
understands the current state."* That is an assertion, not a mechanism.

> **If the oracle is regenerated from the current app state, the oracle moves with the bug.**

There is no acknowledgement anywhere in their material that regeneration could mask a real defect.
This is the deepest problem in the category, and it is exactly what our reviewed FlowSpec plus
ask-for-a-video-on-unknown-screen exists to solve. Recorded here so nobody re-proposes it in six
months; anything that revives it owes a `**Supersedes:**` entry arguing against this section.

Stated fairly: **their approach is wrong in a way ours is right in design and unproven in
practice.** Our review gate works. Our escalation has fired once, on a fixture.

## 7. What this exercise found in our own code

Verified directly on 2026-09-22, not taken on report. These are the real output of this document.

**7.1 Script-first execution and token amortization do not exist.** `docs/ARCHITECTURE.md`
"Execution model" states: *"script-first (run the durable Playwright script if one exists) → agent
fallback … on success the agent emits a script. So a stable suite costs ~zero tokens to re-run."*
In fact `Script` (`schema/case.py:87`) is never instantiated in `src/`; `case.script_ref`
(`schema/case.py:31`) appears only as its own declaration and a copy-through
(`schema/case.py:60`), never read for behaviour; `run_with_fallback` (`stages/agent_loop.py:67`)
appears nowhere else in `src/` — `run_case_pipeline.py:95`, `explore.py:109` and the UI all call
`execute.run_case` directly. **Every re-run is a fresh vision call.** Under the Lab Protocol this
section of ARCHITECTURE.md is currently false, which makes correcting it a prerequisite for
adoption **A**, not a follow-up.

**7.2 There is no deterministic assertion layer.** `ExpectedState`
(`schema/flowspec.py:54-68`) declares six fields. `absent_text` (:65), `dom_asserts` (:66),
`visual_signal` (:67) and `network` (:68) have **zero read sites in `src/`** — grep returns only
their declarations. `url` and `visible_text` are read only in `browser/session.py:230,245` inside
`_poll_for_expected`, which is a *settle hint*: it polls until the condition holds **or the timeout
expires, then returns either way**, recording no failure. `Action.ASSERT` is
`lambda session, step: None` (`stages/execute.py:43`, commented "evidence only"). `run_case`
therefore returns only COMPLETED / ERRORED / BLOCKED_HITL. **100% of pass/fail judgement is an LLM
reading a screenshot** (`stages/grade.py:123`). Against a product that ships real assertions, "we
have `dom_asserts` and `network`" is not a claim we can make — they are unimplemented schema.

**7.3 No semantic locators and no reachable healing.** Raw selector strings go straight to
`page.locator(...)` (`browser/session.py:146-204`). `schema/flowspec.py:78` documents `target` as a
semantic locator, while every Pathlynks case on disk is brittle CSS (`input[name="identifier"]`).
The repair loop in `agent_loop.py` fires only on `Outcome.ERRORED`, so it cannot catch a locator
that resolves to the *wrong* element — and nothing in production calls it anyway (7.1).

**7.4 `EXPAND`, the stated differentiator, has never run on a real product.** The ceiling is
structurally exactly 14 (1 + 3 + 2 + 8, `stages/expand.py:39-50`), not a heuristic. The only
FlowSpec in the repo is `projects/checkerdemo/flowspec.json` — 0 screens, `review.status:
needs_edit`. All three Pathlynks cases are hand-written by a human. Separately, a plain bug:
**`CaseClass.REGRESSION_ANCHOR` appears only in its own declaration and `KIND_BY_CLASS`
(`schema/enums.py:69,87`)** — absent from `CLASS_DESCRIPTIONS` and `applicable_classes`, so it can
never be generated.

**7.5 Video → issue-list works on real input; video → FlowSpec does not.** `projects/erp/` holds
real `media.json`, `transcript.json`, chunks, frames, Gemini observations and three derived issues
with verbatim Hinglish quotes and timestamps. But **no `flowspec.json` exists for erp or
pathlynks** — so the north-star path (video → FlowSpec → review → expand → executable cases) is
unproven on real input. Also one chunk per source and **one model**, despite F-039 claiming a
two-model ensemble; the rows say `"models_agreeing": 1`, so the adjudicator has never had a second
opinion to arbitrate.

**7.6 The flagship unknown-screen behaviour has fired once, on a fixture, and the benchmark has no
human in it.** The only `requests.jsonl` in the repo is `projects/checkerdemo/` — one row asking for
a video of `/`, trivially generated because that flowspec has 0 screens. `stages/coverage.py:103`
says so candidly in its own comment. And `stages/bench.py:51 oracle_human_trial` is a
perfect-recall, perfect-precision synthetic with `duration_s: 300.0` **passed in as a literal**, so
"AutoTester wins on time" currently reduces to 13.6s against a hardcoded 300, over **one seeded typo
in one static HTML file**. The real scorer (`stages/score.py`) is careful code with **no truth
data** — no `ERP_Issues_Trainers.xlsx` in the repo, T-136 still open. **We cannot state a recall or
false-positive number against a human tester.**

**7.7 Provenance drift.** The feature ledger stops at F-043 / 2026-09-10 while roughly twelve days
of crawler work shipped through 2026-09-21 unledgered, so `docs/SNAPSHOT.md` understates the crawler
and overstates the case pipeline.

## 8. Evidence hygiene

- **"42% → 93% pass rate after one iteration"** is TestSprite's own benchmark against GPT/Sonnet/
  DeepSeek-generated code. Unverifiable. A claim, never a finding.
- **dev.to carries a cluster of near-identical "honest review" posts, none carrying a disclosure** —
  the signature of a paid campaign. One was read closely and does contain falsifiable specifics
  (8–12s sandbox spin-up; ~45s for a 10-test batch; ~10% false positives traced to locale/currency
  handling; ~8% of generated assertions brittle) and real criticism (English-only dashboard; RTL
  unsupported and undocumented). Treat as weak-to-moderate evidence with the caveat attached.
- **Almost all pricing and comparison material is TestSprite's own blog**, including its competitor
  comparisons; the one third-party pricing knowledge base belongs to a competitor. Neutral sources
  are effectively absent.
- **Video→test is not unclaimed territory** — `market-2026-09.md` already recorded Fume, Meticulous,
  Checksum and testRigor doing session-or-video→test back on 2026-09-03; Replay.build and AclipA
  also do. **Our differentiator is narrower than "video ingest":** it is the reviewed oracle, the
  unknown-screen escalation and the tester-vs-AI scorecard — two of which are unproven (§7.6).

## Sources

- https://www.testsprite.com/ · https://docs.testsprite.com/
- https://github.com/TestSprite/testsprite-cli (+ its `DOCUMENTATION.md` — the most substantive source)
- https://www.testsprite.com/blog/software-testing-agents-and-the-death-of-the-flaky-test (§6)
- https://www.meticulous.ai/ · https://www.meticulous.ai/how-it-works (§4E)
- https://bug0.com/knowledge-base/testsprite-pricing (competitor-authored; pricing cross-check)
- https://dev.to/panturlo/testsprite-review-autonomous-testing-for-ai-native-development-a-developers-honest-take-3ahp (§8 caveat applies)
