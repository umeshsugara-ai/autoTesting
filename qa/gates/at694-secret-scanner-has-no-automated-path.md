# GATE — AT-694: the secret scanner that caught two real passwords runs only when someone remembers it

**Filed:** 2026-09-28 (maker, tick wave 33m) · **Severity:** medium · **Ledger:** `AT-694`
**Found by:** the checker's sweep. **Maker's part:** verifying the narrowed claim and declining to
change the gate unilaterally.

## The decision, in one sentence

**Should `scripts/check_no_secrets.py` become a fourth command in `qa/adapter.json`'s verify list?**

## Why it is a decision and not bookkeeping

`qa/adapter.json`'s verify list **is** the pass/fail gate for every unit in this repo — the three
commands there are what `/checker` runs before it may issue PASS. Adding a fourth changes what PASS
means for every future unit, including units already built against the current three. That is a
scope change to the contract, not maker housekeeping, so the maker is putting it here rather than
editing the file. (The maker also may not introduce new commands into the adapter mid-run by its own
skill's security rule.)

## What is true, stated as measured and not as first filed

The sweep's first wording was *"`check_no_secrets.py` appears wired to nothing."* The checker
corrected that itself, and the corrected claim is the one to act on:

- **It is cited in contracts and rubrics:** `qa/contracts/pathlynks-first-run.md:58`,
  `qa/contracts/report-export.md:43`, `.goal/rubrics/T-050.md:23` (rubric item 5), and it is
  hand-run in roughly ten manifests.
- **It has zero automated paths:** not in the adapter's verify list, not in any hook, not in any
  `done_check`.

So it is **wired to memory.** It fires where a contract happens to cite it and where a human thinks
of it — which is exactly the coverage a scanner cannot have, because the commit it needs to stop is
the one nobody was thinking about.

**What it has already caught:** `AT-025` — two real dev passwords in a manifest that was about to be
committed. This is not a hypothetical guard.

## Options

- **A (recommended) — add one line to `qa/adapter.json`'s verify list.** Every unit's check then runs
  it, cost is one fast filesystem scan, and the failure mode is a noisy false positive rather than a
  leaked credential. The residue to state plainly: this catches secrets in files the repo is about to
  keep; it does nothing about a secret already pushed, and nothing about one in a file outside the
  paths it scans.
- **B — leave it manual and cite it in more contracts.** Cheaper to nothing, and it keeps the gate as
  it is, but it scales by adding more places to remember. The checker's own framing applies: a
  discipline that depends on every author remembering a command is many people's attention standing
  in for one validation.
- **C — a pre-commit hook.** Strongest coverage and **the maker is not recommending it**, for the
  checker's reason: a hook that loads `.env` on every commit is a new place a secret gets read. It is
  also an enforcement path (`qa/hooks/*`), so it needs `Approved-by: Umesh` on an authorizing
  DECISIONS entry regardless — which makes it strictly more expensive than A for less certain gain.

## What the maker did not do

Did not edit `qa/adapter.json`. Did not add the hook. Did not re-word the contracts that cite the
scanner. The one-line adapter change is ready to make on an answer of A.
