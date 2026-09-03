# Verdict — t030-pathlynks-onboarding

**Date:** 2026-09-03
**Cycle checked: 2**
**Contract:** qa/contracts/pathlynks-onboarding.md (O1-O4, O1 amended cycle 1) + qa/contracts/core-invariants.md (C1-C8) +
qa/contracts/browser-and-secrets.md (B1-B9, dependency, already PASSed)

## Note on this check

This is a clean retry of the cycle-2 check. A prior attempt died mid-run to a transient network
error and left no verdict file, but it appears to have partially executed one write: `qa/issues.jsonl`
had AT-025 already flipped `open -> fixed` on disk with no matching verdict backing that claim. Per
protocol ("a pasted output you cannot reproduce = FAIL on that item"; "never trust the maker/a prior
session's claim without re-deriving"), I treated that ledger state as unproven and independently
re-derived AT-025's status from scratch below. Finding: the flip to `fixed` was premature — I have
reverted it back to `open` with a evidence note, because the leak this issue names has NOT actually
been eliminated (it recurred in a different paragraph of the same file). See "AT-025" below.

## What I re-ran myself (not trusted from the manifest's paste or from ledger state)

- `uv run pytest tests/test_onboard_pathlynks.py -q` → 4 passed.
- `uv run pytest -q` (full suite) → 74%+100% dot bands, matches 93 collected (manifest's "94" is
  the pre-existing, already-open low-severity AT-023 discrepancy, not a new finding).
- `uv run ruff check src tests` → All checks passed!
- `uv run autotester doctor` → doctor: clean
- `wc -l docs/ARCHITECTURE.md` → 138 (≤150, C2 holds).
- `git ls-files | grep -E "\.env$"` → no output; `git log --all -- .env` → no output; `git status
  --porcelain` confirms `.env` is untracked, never committed. `.gitignore` covers `**/.env` (with
  a `.env.example` carve-out).
- `.env.example` read in full: template only, every key blank, no real values ever landed there
  (the manifest's own note that they "briefly landed in .env.example by mistake" is consistent
  with this — the mistake was fixed before anything reached git, and the file's *current* content
  is clean, which is what matters).
- Independently (own Python script, not the manifest's pasted grep or the prior dead attempt's
  ledger edit) loaded the real `.env`, extracted the four secret values named in this check's
  brief (`PATHLYNKS_COUNSELLOR_EMAIL/PASSWORD`, `PATHLYNKS_USER_EMAIL/PASSWORD`) plus
  `GEMINI_API_KEY`, and grepped `qa/manifests/t030-pathlynks-onboarding.md`'s **current, full
  content** for each literal value (byte-exact substring match, not the manifest's own regex).
- Searched `git log --all -p -S <value>` for all five values across full history → zero hits;
  nothing was ever committed.
- Re-read `scripts/onboard_pathlynks.py`, `projects/pathlynks/project.json`,
  `projects/pathlynks/knowledge.md`, and every file under
  `projects/pathlynks/runs/onboard-01M1JQDHA8296D4EQ484CPKP1Z/` (3 PNGs, binary-skipped by content
  but filenames checked) fresh — none contain a secret value; all still match what cycle 1 already
  confirmed clean.
- Opened `docs/FEATURES.jsonl` — F-004 row present, `unit: T-030`, real (non-auto-stamp) reason
  quoted below; would be fine to close T-030 on PASS, but this check is a FAIL (see below), so per
  protocol T-030 stays `pending` and is NOT closed.

## O1 — FAIL again (recurrence, different paragraph)

Cycle 1 found two raw passwords quoted in the manifest's "Human gate cleared" narrative. The
maker's cycle-2 fix correctly redacted **that** paragraph to `{{SECRET:PATHLYNKS_COUNSELLOR_
PASSWORD}}` / `{{SECRET:PATHLYNKS_USER_PASSWORD}}` placeholders — confirmed, that specific
instance is gone.

But my independent byte-exact scan of the **entire current manifest** found the real value of
`PATHLYNKS_COUNSELLOR_PASSWORD` still present, verbatim, inside the manifest's own "Evidence sweep
for O1/O3" section — in both `grep -InE` command blocks the manifest presents as its own proof of
cleanliness:

```
grep -InE "[REDACTED-REAL-VALUE]|[REDACTED-REAL-VALUE]|[REDACTED-REAL-VALUE]|[REDACTED-REAL-VALUE]|AIzaSy[A-Za-z0-9_-]{33}" ...
```

`[REDACTED-REAL-VALUE]` in this alternation is byte-for-byte identical to the real `.env` value of
`PATHLYNKS_COUNSELLOR_PASSWORD`. The manifest's cycle-2 narrative claims "the only remaining
occurrences are the grep *patterns* themselves ... as regex, not literals," using
`AIzaSy[A-Za-z0-9_-]{33}` as the justifying example. That example is a genuine regex — it has a
character class and a quantifier, and it matches infinitely many strings, only one of which
happens to be the real key. `[REDACTED-REAL-VALUE]` has no such property: it contains zero regex
metacharacters, it is used in the alternation as a plain literal, and it matches exactly one
string — which is the real secret. The task brief's own distinguishing test ("a documented regex
PATTERN string... is not [a leak]; '[REDACTED-REAL-VALUE]' as a literal in the file body is a leak") applies
directly: this is the literal case, not the pattern case.

I confirmed `[REDACTED-REAL-VALUE]` does not appear anywhere else in the repository (`grep -rn` across the
whole tree, one hit: this manifest) — so it is not a pre-existing generic test fixture the maker
reused by coincidence; it was typed into this file as this unit's real secret value, most likely
because the maker built the "known non-production values to check for" alternation by eye from the
same `.env` it had just been reading, rather than deriving it programmatically the way this check
did. `[REDACTED-REAL-VALUE]`, `[REDACTED-REAL-VALUE]`, `[REDACTED-REAL-VALUE]` do **not** match any of the four real
secret values (confirmed by direct comparison against `.env`) — those three are coincidental/
unrelated strings and are not a leak. Only the `[REDACTED-REAL-VALUE]` token is a real, exact match.

This is the same class of defect O1 (as amended cycle 1) already covers — a raw secret literal in
maker-authored prose, not the script — recurring in a different section of the same file. The
prior (crashed) cycle-2 attempt appears to have flipped `AT-025` to `fixed` in `qa/issues.jsonl`
before it died, with no verdict to back that claim; I reverted that edit back to `open` with a
dated re-check note, since the underlying leak the issue names is not actually resolved — the
manifest, taken as a whole and as it exists right now, still exposes one real secret literal.

**The script itself, project.json, tests, knowledge.md, the run evidence directory, and full git
history remain clean** — confirmed independently, not carried over from cycle 1's verdict.

## O2, O3, O4 — criteria met, but moot under a FAIL (unchanged from cycle 1, independently re-confirmed)

- **O2:** `projects/pathlynks/project.json` — `slug="pathlynks"`, `base_url` on `vidysea.com`,
  `allowed_domains=["vidysea.com"]`, `write_policy="read_only"`, `headed=false` (explicit).
  `secrets[]` declares exactly the 5 required keys, each `domains=["vidysea.com"]`. Would PASS
  alone.
- **O3:** 3 masked screenshots in `projects/pathlynks/runs/onboard-.../`; `03-post-login.png`
  reviewed as an image — genuine "Logged in successfully" toast over a real dashboard, not a
  bounce-back. `fill()` calls in the script pass only `{{SECRET:KEY}}` literals. Independent grep
  of the run directory and `knowledge.md` for all five real values → 0 matches. `write_policy=
  read_only` respected. Would PASS alone.
- **O4:** `projects/pathlynks/knowledge.md` exists with the required template shape; records role,
  login URL context, screens reached, no 2FA observed. Would PASS alone.

## Not evaluated further (moot given the FAIL)

T-030 stays `pending` in `.goal/goal.json` (confirmed still pending, not touched by this check) —
not closed on a non-PASS, per protocol. `docs/FEATURES.jsonl` F-004's presence is noted above for
the record but its "close on PASS" step does not fire this cycle.

## Fix direction for the maker (next cycle, 3 of max 3 — last attempt)

Remove the literal `[REDACTED-REAL-VALUE]` from both `grep -InE` command blocks in the "Evidence sweep for
O1/O3" section (and anywhere else in the manifest). Do not hand-type any `.env` value into a
"known values to check for" list, even inside what looks like a regex — if a value has no
metacharacters, it is not a pattern, it is the secret. Prefer describing the sweep methodology
("grepped the manifest for each of the four declared secret values, loaded from `.env`
programmatically") over pasting the actual alternation string into the manifest at all — that is
what this check's own approach does, and it is the only way to prove a sweep happened without also
becoming a new leak surface. Re-submit with `Fix cycle: 3`; O2/O3/O4 need no further work.

```
VERDICT: FAIL
SCOREBOARD: 3/4 criteria met, 8/8 invariants hold
FAILURES (if any):
- [O1] The manifest's own "Evidence sweep for O1/O3" section contains the literal value "[REDACTED-REAL-VALUE]", which is byte-for-byte the real PATHLYNKS_COUNSELLOR_PASSWORD, presented as a grep alternation entry rather than the (correctly redacted) narrative prose from cycle 1 · fix: remove the raw value from both grep command blocks; describe the sweep methodology instead of pasting the pattern list, or load values from .env programmatically rather than hand-typing them · issue: AT-025 (reopened)
ISSUES-WRITTEN: AT-025 (reopened open->fixed->open; the interim "fixed" state was an unbacked edit from a prior crashed attempt with no verdict, corrected here)
EXPLANATION: Cycle 1's specific leak (two passwords quoted in "Human gate cleared") is genuinely fixed — that paragraph now uses placeholders correctly. But an independent byte-exact scan of the full current manifest found the real counsellor password recurring, verbatim, inside the manifest's own "evidence sweep" grep commands, disguised as one entry in a pattern alternation alongside a genuine regex (the Gemini key pattern) and two unrelated/non-matching strings. A literal with no regex metacharacters that exactly equals a real secret is a leak regardless of the surrounding quotation marks calling it a "pattern." The script, tests, project.json, knowledge.md, run evidence, and git history are all independently confirmed clean. O2/O3/O4 would independently PASS. T-030 stays open; one fix cycle remains (3 of max 3).
```
