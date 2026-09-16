# Verdict — at400-gate-premise-corrected

**Date:** 2026-09-16
**Mode:** A (unit check), fresh context, bound to `d:/autoTesting`
**Manifest:** `qa/manifests/at400-gate-premise-corrected.md`
**Contract:** `qa/contracts/core-invariants.md`
**Cycle checked: 1**
**Dual check:** no

```
VERDICT: PASS
SCOREBOARD: 4/4 applicable criteria met (C2, C3, C4, C7), 5/5 non-engaged criteria hold on the green suite
FAILURES (if any): none
CAPABILITY-COVERAGE: not-applicable (prose gate record; revert_op=none) — the substitute, 4/4 re-derivation commands, reproduced exactly
LIVE-BROWSER: not-applicable (changed path: qa/gates/at365-data-class-declaration.md)
ISSUES-WRITTEN: AT-400 open → fixed · AT-415 (new, medium)
EXPLANATION: Every factual claim the corrected gate section makes was re-derived by me from the
bound tree and every one held. The manifest's refusal to invent a prose-matches-disk guard is
admissible under C7 — the artifact has no executable behaviour to perturb, and the four commands
are a real falsification route, not a narrative substitute for one. The four things the unit
declines to do are all correctly out of scope, and one of them (re-deriving AT-376) is provably
unobtainable in the current tree. The commit-before-manifest ordering is disclosed, narrowly
justified for a live-false gate record, and not charged — but it is bounded to that shape.
```

---

## What I re-ran myself

Every command below was executed by me in `d:/autoTesting`. No pasted output was read as evidence.

### The four re-derivation commands (the unit's substitute for a falsifying edit)

| Command | Manifest expects | My output | Verdict |
|---|---|---|---|
| `grep -c "data_class" qa/adapter.json` | `0` | `0` (exit 1, no match) | ✅ |
| `git status --porcelain qa/adapter.json` | empty | empty | ✅ |
| `git log -S data_class --all -- qa/adapter.json` | empty | empty | ✅ |
| `python D:/ai_os/.../data_boundary.py .` | the VIOLATION line | `[VIOLATION] qa\adapter.json — adapter.json has no "data_class"…` exit 1 | ✅ |

I also read `qa/adapter.json` in full: it carries the `_note` about allowlisted commands and no
`data_class` key of any kind. And I ran the fifth command the sweep used but the manifest did not
list — `git stash list` → empty — closing the last place the reverted edit could have survived.
**The declaration does not exist in the working tree, the index, any commit on any ref, or any
stash.** The corrected section's claim is true in every conjunct.

### Slot-1 verify (`qa/adapter.json`)

```
uv run pytest -q                      -> exit 0 (all dots; 1 skipped; only the known starlette
                                         DeprecationWarning in the warnings summary)
uv run ruff check src tests scripts   -> All checks passed!          exit 0
uv run autotester doctor              -> doctor: clean               exit 0
```

No code changed, so the suite is the regression floor and it is green.

---

## Step 4b — ruling on the refused falsifying edit

**Admissible. The substitution is accepted, and the unit does not ship an unfalsifiable claim.**

The reasoning, because this is the ruling the manifest explicitly asked for:

1. **Slot 2 settles the mechanics.** `qa/adapter.json` declares `artifact.revert_op: "git revert-file"`
   for code; the changed path is a markdown gate record with no executable behaviour. There is no
   branch to mutate, no check to redden, and no assertion that could be attributed to one. C7's
   mutation duty is placed by its own text on *"a unit that ADDS or REWRITES a test"* — this unit
   adds none.
2. **The claim is falsifiable, and I tried to falsify it.** This is the part that matters. C7's
   substance is *"a check that someone else can re-run"*, not *"an edit that reddens something"*.
   The corrected section is a conjunction of four factual assertions about disk state, and each of
   the four commands independently settles exactly one of them — any one disagreeing would have
   failed the unit on the spot. I ran all four plus a fifth the manifest did not claim. That is a
   sharper instrument than a falsifying edit, not a weaker one: a falsifying edit proves a check
   *would* notice a change, whereas these commands prove the claim *is presently true*, which is
   precisely what a gate's premise has to be.
3. **The refusal to add a prose-matches-disk guard is correct, and I want it on record as correct
   rather than merely tolerated.** The manifest names four successive over-claims from that species
   of guard this session (AT-396 → AT-405/406 → AT-413) and declines to add a fifth layer. That
   matches the sweep's own structural-erosion signal and the standing rule that the remedy for a
   guard that over-claims is not another guard. A test asserting that gate prose matches disk would
   also be the exact shape this project keeps getting wrong — a mechanism one notch narrower than
   the sentence describing it — and it would go red permanently the moment any gate legitimately
   records a past tree state.

**Where the line is.** This ruling is scoped to a `qa/gates/` prose record whose entire content is
re-derivable facts. It is not a general licence: a unit touching `src/`, `tests/` or `scripts/`
still owes a falsifying edit per row, and "there's nothing to perturb" is an unreachability claim
under C7's last clause, which costs a mutation run and not a paragraph.

---

## The five independent judgements

### 1. The gate file itself — read by me, not by the maker's description

**(a) No sentence still claims the declaration is in the working tree.** ✅ I read
`qa/gates/at365-data-class-declaration.md` end to end and grepped it for `working tree`,
`uncommitted`, `NOT committed`. One hit, line 64, and it is inside the corrected section's own
quotation of what the file *used to say* (`"It claimed … sat in qa/adapter.json in the working
tree, uncommitted"`), correctly framed as the refuted claim. The narrative in "What happened"
(lines 9-14) is past tense about the moment the gate was opened — `I added "data_class":
"synthetic"` — and is now explicitly reconciled by the corrected section stating the edit was
reverted. No live claim survives.

**(b) The four options and the blocked-consumer analysis are intact and unaltered.** ✅ Verified
mechanically, not by reading: `git show 293bcfb -- qa/gates/…` is a single hunk starting at line 57
that replaces the 4-line `## Current state` section with 33 lines. Options A/B/C/D (lines 45-55),
the "Why I cannot just fix it" analysis of `data_boundary.py` living outside the bound root, the
`real_data_markers`/`PLACEHOLDER_DOMAINS`/`SKIP_DIRS` reasoning, the "both states are red" note,
and the answer-format instruction are all **outside the hunk** and byte-identical. The trailing
empty `Answered:` line is preserved, so the gate remains correctly open.

**(c) The AT-376 staleness caveat is present and accurate.** ✅ Present at lines 81-84. Accurate on
three counts I checked rather than assumed: the arithmetic is consistent (335 `.work/` + 2
`profiles/` + 7 tracked = 344, and the AT-376 ledger row's "337 of its 344 are gitignored" agrees);
the attribution is correct (my own run just now, against a tree with no `data_class`, produces
**only** the missing-declaration violation and no file scan at all — so the 344 could only ever
have been measured with the declaration in place, exactly as the caveat says); and the caveat
correctly extends itself to the "~30 benign hits" table higher in the same file, which was measured
the same way. That extension was not required by the ledger row and the maker added it anyway.

### 2. Commit-and-push before the manifest — acceptable here, bounded

**Not charged.** Normal order in this pair is manifest → check → PASS → commit, and D-007 puts the
push in the checker's hands. This unit inverted it. I am ruling it acceptable **for this shape
only**, on four grounds:

- The artifact is a HUMAN_GATE record — the on-disk thing a human decision is made *against*. Its
  falsity was not latent, it was live: Umesh could have answered `A`, `B` or `C` at any minute in
  those hours and acted on a premise that had evaporated. Every minute of delay had a real cost,
  which is not true of a code fix waiting for a check.
- The change is factually verifiable and behaviourally inert. No code, no contract, no enforcement
  path, no schema. Nothing a premature commit could break, and nothing a FAIL would have had to
  unwind beyond one follow-up commit.
- My ability to check was not impaired. I re-derived every claim against the committed state and
  could have FAILed on any of the five commands; the ordering removed no leverage from this role.
- **It was disclosed, in the manifest and in the commit message, rather than discovered.** The
  commit body states the ordering and even credits the sweep (`130c4c1`) rather than the maker for
  finding it. That is the evidence culture C7 exists to enforce.

Confirmed pushed: `293bcfb` is an ancestor of `origin/master`.

**The bound:** this is not precedent for code. A unit touching `src/`/`tests/` that commits before
its check has removed the check's only lever, and the same disclosure would not buy it. Recorded
here rather than folded into the contract — adding a clause for a one-off ordering on a prose
record would be growing the harness to answer a judgement call, which is the move the erosion
signal warns against.

### 3. Severity `high` — agreed, not downgraded

The manifest's argument is the right one and it survives checking: options A, B and C all open with
"land the declaration", so the gate told its only reader that the hard and irreversible-feeling part
was already done when in fact nothing had been done. Two things push it past `medium`:

- The false premise sat on the path to a decision on `AT-365`, itself a `high`, `open`,
  data-boundary issue the sweep ranks #1.
- It propagated. AT-376's 344-violation measurement — the number option B's cost-benefit rests on —
  was taken against the vanished tree state, so the rot had already spread from the sentence into
  the evidence base. My own run demonstrates the propagation is real, not theoretical.

Not `critical`: the human was still in the loop, no data moved, nothing irreversible occurred, and
the worst outcome was a wasted answer that a re-read would have caught.

### 4. The four refusals — all correct scoping, one of them provably forced

- **Does not re-apply the declaration.** ✅ Correct. Landing it is common to A/B/C but each pairs it
  with a *different* second half (purge scratch / fix the shared gate / accept a standing red).
  Landing it alone would pre-empt the choice and, as the manifest says, put MC-003 into a persistent
  red that nobody had authorised. Re-applying remains one line.
- **Does not answer the gate.** ✅ Correct, and structurally required — the maker cannot answer its
  own HUMAN_GATE, and neither can I.
- **Does not re-derive AT-376's 344 violations.** ✅ Correct, and stronger than the manifest claims:
  it is not merely out of scope, it is **unobtainable**. I ran the validator; with no `data_class`
  declared it short-circuits on the missing declaration and never scans a file. Re-deriving 344
  would require re-applying the declaration, which the previous refusal correctly declines.
  Flagging the number stale is the only honest action available, and the manifest took it.
- **Does not touch the other open gates.** ✅ Correct scoping — one unit, one artifact — and the
  manifest names `t162-contract-approval` (open five days) as a suspected same-shape risk instead of
  staying silent. It files nothing, so **I have filed it: AT-415**. That is a checker's job, not a
  reason to hold this unit open.

No under-delivery found in any of the four. The unit does exactly what its title says and says
plainly what it is not doing.

### 5. Naming the command instead of pasting a transcript — adequate here

**Adequate, with a caveat about how the lesson generalises.** C7's Verify clause asks that "the
manifest pastes real output, not a summary". This manifest pastes real output for the four
re-derivation commands and names — rather than pastes — the three slot-1 commands, citing AT-414.

It is adequate because: the unit changed no code, so the suite carries no claim of the unit's own
beyond "the regression floor is intact"; the checker charter is to re-run and never to trust a
paste, so a paste would have contributed nothing I did not produce; and I produced all three
outputs above, green. Nothing is missing from the evidence base.

**The caveat, so the maker does not draw the wrong lesson from AT-414.** AT-414 was filed for an
*elided* paste — `[... all dots ...]` — which strips exactly the pass/skip counts that tell a
current run from a stale one. The honest repair for an elision is a **complete** paste, not the
absence of one. Declining to paste is the right call only when the command carries no claim of the
unit's own, as here. On a unit that touches code, C7's paste duty is live and "the checker will run
it" does not discharge it.

---

## Criteria, judged individually

| Criterion | Engaged? | Evidence |
|---|---|---|
| **C1** schema-first | not engaged | no schema touched; `uv run pytest -q` green |
| **C2** readable / doctor | ✅ met | `doctor: clean` (file-size, docstring, ARCHITECTURE rules) |
| **C3** one concept one place | ✅ met | `doctor: clean`; no new file, single existing file edited in place |
| **C4** repo root clean | ✅ met | `doctor: clean`; changed path is under `qa/gates/` |
| **C5** secrets | not engaged | no `.env`, no `SecretRef`, no prompt touched |
| **C6** artifacts are files | not engaged | no stage output touched |
| **C7** verification independent | ✅ met | every claim re-derived by me from the bound tree; 5/5 commands agreed; mutation duty not triggered (no test added or rewritten); no unreachability claim made — the manifest asserts "no executable behaviour", which is a property of a markdown file and not a claim about the reach of mutation |
| **C8** provider-agnostic | not engaged | no model call touched |
| **C9** declared control value honoured | not engaged | `.goal/` untouched by this unit |

**Invariants:** this contract folds its invariants into the criteria; there is no separate `[I*]`
block, so none is scored separately.

**`Issues addressed` vs the ledger:** the manifest claims AT-400 (high). The ledger row's `expected`
field offers two remedies — *"re-apply AND commit the declaration … or rewrite the gate to say the
declaration is absent"*. The unit took the second, completely. **AT-400 open → fixed.** No other
issue is claimed and none is silently closed.

---

## Ledger changes

- **AT-400** `open` → `fixed`, `fixed_date: 2026-09-16`, with this verdict cited. It moves to
  `verified` only on a later re-check, per the ledger rules.
- **AT-415** (new, medium, `governance`) — the other unanswered gates have never been audited for
  the same premise rot. This unit found it in one gate by accident of a sweep; ~7 gates in
  `qa/gates/` carry no answer and some have been open for days, each stating a tree state nobody has
  re-derived since. Filed as a checker finding, not charged to this unit, which correctly scoped it
  out.

## Not touched by this check

Per the dispatch's concurrency boundary: `.goal/*`, `qa/evidence/at379-*`, `qa/evidence/at358-*`,
`qa/manifests/at379-scrollable-pane-reachability.md`, and the untracked `projects/*`, `.codex/`,
`AGENTS.md` were neither read for judgement, staged, nor modified. No goal task was closed — the
manifest declares `Goal task: none — issue-driven`, and `.goal/` is off limits this session in any
case.

**MC-003** exits 1 on the missing `data_class`. That is AT-365 at HUMAN_GATE — the very gate whose
premise this unit corrects — and is not chargeable here.
