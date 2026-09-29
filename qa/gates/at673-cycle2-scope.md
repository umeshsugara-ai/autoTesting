# GATE — at673 cycle 2 carries a fourth change D-056 did not authorize

**Filed:** 2026-09-29 (maker) · **Decider:** Umesh · **Blocks:** at673-sessionstart-unclosed-detector
closing (cycle 2 verdict FAIL on scope only, `qa/verdicts/at673-sessionstart-unclosed-detector.md`,
AT-741). Every functional check is green: AT-713/714/715 met, 3/3 capability rows reproduced.

## The question in one line

The cycle-2 fix added a per-line inline-code strip at `qa/hooks/mc-sessionstart.ps1:77`. D-056 waived
exactly three rows and said "any other change … not authorized". Do we revert the strip or ratify it?

## What the checker measured

- The strip's stated premise does not reproduce. The quoted-heading misread it claims to fix
  pre-dates cycle 2: it read 2 under cycle 1 and reads -1 now.
- The strip adds a fail-open regression. The AT-722 odd-backtick line read -1 under cycle 1 and
  reads 42 now.
- Neither shape occurs in any of the repo's 547 files today.
- With the strip deleted, the AT-713/714 tests still pass. The waived rows do not need it.

## Options

- **A — Revert the strip and its test** (maker's recommendation). The unit returns to exactly the
  D-056 scope and loses the fail-open regression. It is a removal, not a new change, and it still
  needs a one-line D-entry authorizing cycle 3 on this closed seam.
- **B — Ratify the strip** (the checker's lean). One DECISIONS entry authorizes it and decides
  AT-722. The checker re-PASSes with no code change. It keeps the AT-722 regression unless that
  entry also demands its fix.
- **C — Leave at673 FAILed on scope.** Cycle 1 already fixed the real bug (on master since the
  cycle-1 PASS), and cycle 2's code stays with a FAIL on file. This is not recommended because it
  leaves a handshake open forever.

## Answer format

Answered: <ISO date> — <A|B|C> — <where/verbatim>

Answered: 2026-09-29 — A — "A: Revert it (Recommended)", Umesh via AskUserQuestion in the maker session; recorded as D-058
