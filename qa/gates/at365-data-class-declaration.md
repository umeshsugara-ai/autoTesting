# Gate — AT-365: declaring `data_class` makes the boundary gate fire, and it fires on benign files

**Opened:** 2026-09-16T11:50+05:30
**Blocks:** AT-365 (high, data-boundary) — the sweep's #1 recommended unit
**Raised by:** maker, mid-build

## What happened

AT-365 looked like a one-line fix: `qa/adapter.json` declared no `data_class`, so MC-003's
`data_boundary.py` could not fire at all and the synthetic-only posture existed only as prose in a
`_note`. I added `"data_class": "synthetic"` — the declaration is **correct**, this repo genuinely
holds no V3.3, Pathlynks, student-applicant or production data.

Then I ran the gate. It reports **~30 violations**. I checked every distinct address it flagged:

| Address | What it actually is |
|---|---|
| `noreply@anthropic.com` | the `Co-Authored-By:` attribution line, in commit-message scratch files |
| `pathlynks.test`, `evil.test`, `a.test@evil.test`, `pw@pathlynks.test` | deliberately fake fixtures in the security tests — RFC 2606 reserved `.test` TLD |
| `umeshsugara@vidysea.com` | the repo author's own address in `pyproject.toml` `[project] authors`, already public in git history |

**Zero real third-party personal data.** Every hit is attribution, an RFC 2606 test domain, or the
project's own package metadata. And **every violating path is under `.work/`** — the gitignored
scratch directory this project's own CLAUDE.md designates for scratch, logs and evidence — mostly
inside stale whole-repo copies left by checkers of closed units (t160, t161, t136, at241, at339,
ui-cred).

## Why I cannot just fix it

`data_boundary.py` lives at `D:/ai_os/.claude/skills/_shared_validation/` — **outside this bound
root.** The maker's project-binding rule forbids writing there, and it is shared by every
maker-checker project, so a change is a cross-project decision, not this unit's.

The adapter offers no knob that helps: its only field is `real_data_markers`, which *adds* markers.
There is no domain allowlist, no path exclusion, and both `PLACEHOLDER_DOMAINS` (which covers
`example.com`/`test.com` but not the `.test` TLD) and `SKIP_DIRS` (which omits `.work`) are
hardcoded.

Note this is not a reason to leave `data_class` undeclared — undeclared is *also* a blocking
violation by design ("deleting the field is not a way out of the gate"). Both states are red. The
question is only which red, and what closes it.

## The decision — Umesh picks one

- **A — Purge the stale `.work/` scratch** (the closed-unit checker copies and `*msg*.txt` files),
  then land the declaration. Cheapest, and `.work/` is gitignored scratch by design. Destructive
  and irreversible, which is why I have not done it: some of it may still be cited evidence.
- **B — Land the declaration and fix the shared gate** so attribution addresses, RFC 2606 `.test`
  domains and the project's own `pyproject.toml` authors stop counting, and gitignored paths are
  skipped. Correct and benefits every project, but it edits a shared enforcement path outside this
  root and needs its own authorization.
- **C — Land the declaration and accept a standing red**, with the sweep re-filing this finding
  every run. Honest but noisy, and a gate nobody can ever get to green is the failure mode AT-218
  is about.
- **D — Something else.**

**Answer format:** reply `A`, `B`, `C` or `D` with one line of reasoning, or append an
`Answered:` line to this file directly.

## Current state — CORRECTED 2026-09-16T14:20+05:30 (AT-400, high)

**What this section said was false, and had been since shortly after the gate was opened.** It
claimed `"data_class": "synthetic"` plus a `_data_class_note` sat in `qa/adapter.json` in the
working tree, uncommitted, awaiting the decision.

**The truth on disk:**

```
$ grep -c "data_class" qa/adapter.json        -> 0
$ git status --porcelain qa/adapter.json      -> (clean)
$ git log -S data_class --all -- qa/adapter.json -> (no commit has ever carried it)
```

I wrote the declaration, then **reverted it myself** an hour later
(`git checkout -- qa/adapter.json`) so the AT-366 unit would ship against a clean tree — and never
came back to update this file. The edit is gone with no trace, and this gate sat advertising a
tree state that no longer existed. A sweep caught it, not me.

**Why this matters more than a stale sentence.** Options A, B and C all begin *"land the
declaration"*, so a reader answering today would have been told the hard part was already done.
And **AT-376's measurement is stale with it**: its 344 violations (335 under `.work/`, 2 under
`profiles/`, 7 tracked) were counted against a tree that had the declaration in place. Those
numbers need re-deriving before they are used to justify an option — the ~30 benign hits described
higher up this file were measured the same way and carry the same caveat.

**Nothing about the decision itself changes.** The four options stand, the analysis of *why* every
consumer is blocked stands, and re-applying the one-line declaration is trivial whenever an answer
arrives. What changed is that this section now describes the repository as it is.

A gate's premise rotting while it waits is a failure mode this project had not seen before. It is
also an argument for answering the older gates sooner: `t162-contract-approval` has been open five
days, and nothing guarantees its stated premise has aged any better than this one did.

Answered:

Answered: 2026-09-24T16:32:17+05:30 — Umesh declined option a: "ye dependecy user ne jo testing account diya hai usse depend krti hai, ye tho account dene wale tester ki galti hai hum concerned nhi hongee" — no shared data_boundary.py change; AT-365 to be closed as accepted/wontfix by the checker with this reason — chat 2026-09-24
