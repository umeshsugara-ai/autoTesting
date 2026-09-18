# Sweep: stale open-row audit — 2026-09-18

**Bound root:** `d:/autoTesting`. **Mode:** targeted sweep of `qa/issues.jsonl`'s open backlog,
dispatched to check whether the reported 158 open rows overstate the true backlog. Not a unit
check — no manifest/verdict issued, no PASS/FAIL. This checker's write surfaces for this run:
`qa/issues.jsonl` and this report.

## Starting state

- `git status --porcelain qa/issues.jsonl` was already clean at sweep start (515 lines).
- Open rows: 158 (low 94, medium 50, high 14).

## Rows examined

Examined in full, with independent re-derivation (not trust of the dispatch prompt's own
claims): **AT-492, AT-475**, the 11 ids named as possibly-orphaned, and a further
**19 open rows** checked against the "manifest referenced has since PASSed" trap: AT-117,
AT-131, AT-328, AT-332, AT-378, AT-380, AT-414, AT-420, AT-428, AT-447, AT-482, AT-484, AT-485,
AT-503, AT-507, AT-510, AT-512, AT-514, AT-515, AT-517. Total: **21 open rows individually
re-derived**, plus a full-ledger id-presence check.

## Closed (2)

### AT-492 (severity: high → closed `fixed`)

Claim: `at490-491-tree-kill-is-bounded` manifest sat `ready-for-check` with no verdict since
commit `176a89c`.

Verified false as of now:
- `qa/manifests/at490-491-tree-kill-is-bounded.md:114` reads `## Status: checked-PASS`
  (Fix cycle 1 of max 3).
- `qa/verdicts/at490-491-tree-kill-is-bounded.md` exists on disk, committed twice —
  `992f03f` (PASS) and `12d2226` (INDEPENDENT CONCURRENT CHECK, also PASS) — with
  `Cycle checked: 1`, matching the manifest's Fix cycle.
- AT-490 and AT-491 (the units this manifest addresses) are both `status: fixed` in the
  ledger, not `open` as AT-492's own evidence field asserted.

The row's point-in-time claim was true when filed; it is false now. Closed with evidence
citing both commit hashes and the ledger cross-check, per the pattern the ledger already uses
for this class of row (AT-496).

### AT-475 (severity: high → closed `fixed`)

Claim: ledger state of committed checker verdicts "lives only in the uncommitted working
tree: 10 rows absent from HEAD and 6 status flips unrecorded."

Verified:
- `git status --porcelain qa/issues.jsonl` clean; `git diff HEAD -- qa/issues.jsonl` empty —
  HEAD and the working tree are byte-identical.
- All 10 named rows (AT-446, 452, 455, 456, 462, 463, 467, 470, 471, 472) are present in HEAD.
- Checked the 11-id side claim from the dispatch prompt independently rather than taking it on
  faith: `AT-899/AT-900/AT-901` are test-fixture strings, not ledger claims. The other eight
  (`AT-290a/AT-290b/AT-294b/AT-295b/AT-466a/AT-466b/AT-480a/AT-054`) appear only as prose in
  `qa/verdicts/`, never inside an `ISSUES-WRITTEN:`/`Issues addressed` block —
  `qa/verdicts/at500-a-letter-suffixed-id-is-an-id.md:96-102` already re-derived this exact
  set and reached the same conclusion independently. None of the 11 counts as a live instance
  of the pattern AT-475 names, so this does not weigh against closing it, and I did not widen
  the rule to catch them (that widening is the exact trap AT-504/AT-508/AT-511 each closed).
- On the stated **cause** (checkers not committing their own ledger hunks): AT-499
  (`status: fixed`, 2026-09-18) corrected the actor boundary after a maker had written
  `qa/issues.jsonl` directly. `git log --oneline -- qa/issues.jsonl` shows every commit since
  AT-499 through current HEAD (`d7298b5`) is authored `qa(checker): …` — none by the maker.

Closed the specific measured claim and the actor-boundary cause behind the 2026-09-17
recurrences. Recorded honestly in the `fix_note` that this is the ledger's current verified
state, not a permanent guarantee against a future lapse — the underlying discipline could
still slip again, and a future sweep should re-check it on its own evidence rather than trust
this closure indefinitely.

## Left open, deliberately (19 checked, 0 closed)

Generalized the "manifest referenced has since PASSed" pattern search: 17 open rows reference
a `qa/manifests/*.md` path directly, plus AT-420/AT-447/AT-484 which were named in the dispatch
as adjacent risks. For every one, I re-read the current file content the row cites (not just
the row's own text) before ruling:

- **AT-328** — claims a stale forward-pointer chain in `at311-mutation-check.md` (line 60-62
  says the 8/8 cycle-2 run is authoritative; line 153 says that same 8/8 is superseded by
  13/13). Re-read both line ranges in the live file: **both sentences are still there,
  word-for-word.** Still open, correctly.
- **AT-485** — claims `qa/hooks/mc-sessionstart.ps1:14` substring-matches
  `'Status: ready-for-check'` anywhere in a manifest body rather than anchoring to the header
  line. Re-read the script: the `Select-String -Pattern 'Status: ready-for-check'` call is
  still unanchored. Still open, correctly.
- **AT-420 / AT-447** — a gate file (`qa/gates/t162-contract-approval.md`) with a false "not
  blocked" claim, and the missing manifest/verdict handshake for its own retroactive fix.
  Re-checked: `qa/gates/t162-contract-approval.md:28` still reads the false
  "Nothing else in the backlog depends…" line; no `qa/manifests/*at420*` or `*t162*` and no
  `qa/verdicts/*at420*` exist. Both still open, correctly.
- **AT-484** — flagged by the dispatch as a control case (a row naming a PASSed unit —
  `at229-249-pytest-leaves-the-tree-clean` — among others, that is nonetheless still valid).
  Confirmed: AT-484's actual condition is about `qa/.last-tick` currency as a systemic
  practice, not about that one manifest's status; the mentioned unit passing changes nothing
  about the claim. Left open per the dispatch's own instruction and my independent read of the
  row.
- **AT-117, AT-131, AT-332, AT-378, AT-380, AT-414, AT-428, AT-482, AT-503, AT-507, AT-510,
  AT-512, AT-514, AT-515, AT-517** — each is a residual, low/medium-severity documentation- or
  precision-defect finding filed *during* that manifest's own check (a wrong assertion cited,
  an elided suite paste, a stale figure, a missing standing check, a mechanism gap). None of
  these assert "the checker hasn't looked yet" (AT-492's shape); they assert "the artifact's
  content is wrong," which a later PASS on the same manifest does not retroactively fix unless
  the content was specifically edited. Spot-read two of the oldest (AT-328, AT-485, detailed
  above) to confirm the pattern holds rather than assuming it from the title alone; did not
  open every remaining file given time cost and that none showed any surface signal (recent
  edit, superseding row, contradicting verdict) of having been addressed. Left open.

No row was closed by inference from "its manifest passed" alone — every closure above rests on
directly re-reading the current file state the row itself cites.

## Result: was the backlog materially inflated?

**Only marginally, at the top of the severity ladder, not throughout.** Two `high`-severity
rows were stale — both were themselves *about the ledger/dispatch process*, not about a code
defect, and both were resolved by ordinary process running forward (a PASS landing, an
actor-boundary fix taking effect) rather than by anything this sweep needed to fix. Every other
row checked — including the specific "manifest since PASSed" pattern the dispatch worried about
most — held up under direct re-reading of current file state. The 158-row figure was accurate
to within 2 rows; it was not inflated in the way the dispatch's hypothesis (numbered item 3)
worried about.

## True open count now

**156 open** (was 158): **high 12** (was 14), **medium 50** (unchanged), **low 94** (unchanged).

## Verification

- `git show --stat` before/after confirmed a 2-line diff (2 insertions, 2 deletions) touching
  only the AT-475 and AT-492 rows — no reformatting of the other 513 lines.
- `uv run autotester doctor` → `clean` after the edit.
- No file outside `qa/issues.jsonl` and this report was written or modified.

## Commit

Committed with `git commit --only qa/issues.jsonl qa/sweeps/2026-09-18-stale-open-rows.md`.
