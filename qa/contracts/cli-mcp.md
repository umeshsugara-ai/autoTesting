# Contract — cli-mcp (a CLI and an MCP server a machine can rely on)

**Status:** **DRAFT** (authored by /checker 2026-09-29 under **D-041**, `Approved-by: Umesh` — the
"New checker-authored DRAFT contracts under `qa/contracts/`, as listed in Result" line, which names
this file). Goes **ACTIVE** on T-174's first checker PASS.
**Feature:** T-174 — a documented CLI contract (`--output json`, exit codes that separate what CI
acts on differently, `--dry-run`) plus AutoTester exposed as an MCP server (run tests, get report,
get catalog).
**Serves:** intent O2 (runs a real regression) · spec R25.
**Code:** does not exist yet (T-174 `pending`, depends on T-125 catalog). `src/autotester/cli.py` and
its siblings exit only 0/1 today (`doctor`) and emit human text only.
**Tests:** none yet.
**Grounding:** D-041 §1 (AutoTester exposed as an MCP server) and §6 row T-174 ·
`docs/research/testsprite-2026-09.md` §4 F (a CI must be able to tell *test failed* from *auth*,
*validation* and *timeout*; the cost of unreadable verify output was AT-503) · `consent.md` CN1/CN9
(nothing outward-facing starts without approval) · core-invariants C3, C5, C11, C12.

## Why it exists

A tool a pipeline cannot read is a tool a pipeline cannot gate on. The failure this contract refuses
is a green exit code that hides a refused run, or a JSON blob that a human eyeballed once and no
test ever parsed. AT-503 was the same lesson one level down: a verify command that printed no summary
line produced two retracted "clean suite" claims.

## Criteria

### CM1 — One exit-code table, and every code in it is provoked by a test

Exit codes distinguish at least: **test failed**, **run refused** (no valid `RunApproval`, consent
gate), **usage / validation error**, **infrastructure or timeout**, **internal error**. The table is
defined in ONE place (one enum in one module, mirrored in the CLI's `--help`), not scattered
literals. `doctor`'s existing contract (0 clean, 1 violation) is unchanged.

**Verify:** for each code in the table, a fixture provokes it and asserts `exit_code ==` that code.
A code with no provoking test fails the check. Sabotage: collapse two codes to one value — the
named per-code test goes red on the assertion for the collapsed code, not on an import error.

### CM2 — `--output json` is machine output, schema-typed, and scrubbed

With `--output json` stdout carries **one valid JSON document and nothing else**: no ANSI, no
progress text (those go to stderr). The document is a Pydantic model in `schema/` with
`extra="forbid"` — not an ad-hoc dict — and carries the run id, per-case outcomes, verdict counts
and evidence paths. No secret value appears in it (C5).

**Verify:** parse stdout with `json.loads` and validate against the model; run with a planted secret
value in the fixture project and assert the value appears nowhere in stdout or stderr
(`Redactor.scrub` is the gate). Sabotage: `print()` one human line to stdout — the parse test goes red.

### CM3 — `--dry-run` sends nothing and starts nothing

A dry run launches no browser, makes no provider call, opens no network connection, and creates no
run directory or `RunState`. It reports what **would** run (case ids and count). It is an offline
exercise of the code path, never a weaker run that quietly does real work.

**Verify:** run a fixture project with the browser factory and every provider replaced by fakes that
**raise on use**, and the filestore tree hashed before and after — identical hashes, exit 0, and the
report lists the case ids. The same command **without** `--dry-run` and without an approval still
exits with the "run refused" code (a dry run is not a route around CN1). Sabotage: let the dry-run
branch call the provider — the raising fake turns it red.

### CM4 — The MCP server is a thin adapter over the existing functions, and the approval gate stands

The server exposes exactly **run tests**, **get report**, **get catalog** (D-041 names these). Each
tool calls the function the CLI already calls — no second implementation of a stage (C3). A **run**
tool call goes through the same `RunApproval` gate as every other entry point (CN1, CN9); the MCP
layer can neither grant nor bypass an approval. Tool outputs use the CM2 schema.

**Verify:** list the server's tools — the set equals the three names. Call **run** with no valid
approval: nothing starts (no run directory, no navigation), and the result carries the "run refused"
code. Grep the server module for an import of any stage's internals that the CLI does not also
use — none. Sabotage: skip the approval check inside the run tool — the refusal test goes red.

### CM5 — The MCP dependency is declared in this unit only, and no tool reads a raw secret

`mcp` (or whichever SDK the build picks) is added to `pyproject.toml` only within this unit
(C11) and `autotester doctor`'s `check_dependencies_declared` reports clean. No tool description or
output contains a secret value; **get report** returns the already-redacted report artifact.

**Verify:** `git diff` shows the `pyproject.toml` line arriving in this unit's commit and not
earlier; planted-secret test as CM2, run through the MCP transport.

## Landing note

None of this exists: `grep -rniE "mcp" src pyproject.toml` returns no match (verified 2026-09-29).
A `grep` against a not-yet-existing file exits **2**, not 1, and reading that as "no forbidden thing
found" is the AT-218 vacuous-guard shape — every **Verify** above names a fixture that runs the
built thing, so none of them can pass on an empty tree.

## No-fire list

- Building T-174 itself.
- A hosted or remote MCP deployment, authentication for a network transport — local stdio server only
  until a decision says otherwise.
- The concrete choice of MCP SDK.
- Exit codes for commands that do not exist yet.

## Amendment log (append-only; git history is the version)

- 2026-09-29 · init · authored by /checker under D-041 (`Changes-authorized`: "New checker-authored
  DRAFT contracts under `qa/contracts/`, as listed in Result", and Result names `cli-mcp.md`).
  Cause: T-174 had a `docs/plan.md` row (unit 12) and a goal task but **zero** checkable criteria,
  and the 2026-09-27 sweep and the maker's 2026-09-29 tick both read the absence as a gate
  ("T-176: no authorizing contract"). It was never a gate: the authorization has existed since
  2026-09-24 and the file was simply never written. DRAFT until T-174's first PASS.
  **Changes-authorized:** this file (named by D-041). No enforcement-path file touched.
  **Links:** D-041; T-174; R25; AT-503.
