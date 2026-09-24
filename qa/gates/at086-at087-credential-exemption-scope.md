# Gate — AT-086 / AT-087 credential-guard exemption scope (qa/contracts/ui.md U9)

**Opened:** 2026-09-24 · **Blocks:** closing T-123 (AT-085 + AT-065 were built in the same unit; these two were deferred by the maker as scope decisions)
**Evidence:** `qa/manifests/t123-medium-batch.md` "Deferred — needs a decision" (branch wave/t123-medium-batch, d5db88b) · `qa/contracts/ui.md` U9 calls both "a scope decision rather than a bug fix"

## Questions
1. **AT-087** — the credential-concatenation check on the project-edit/secrets routes can be hollowed out by the flat exemption list. Make the exemption **per-field** (`exempt: dict[field_label, value]`) and keep exempt fields in the concatenation join as context?
   - (a) Yes, per-field + keep in the join — stricter; risk: new false positives on legitimate no-op resaves.
   - (b) No, accept the current flat exemption as known debt (wontfix, record why).
2. **AT-086** — a project whose `base_url` equals a non-secret value in the shared `.env` cannot be onboarded (the exemption needs stored data a new project doesn't have yet).
   - (a) Let `.env` entries be marked non-secret (e.g. a declared allowlist of public keys like `*_URL`), so they're excluded from the "match every .env value" guard.
   - (b) Keep the guard absolute (AT-083 hardening); operator puts the URL outside the shared `.env`. Record as wontfix.

**Recommendation:** 1(a), 2(a) scoped to an explicit declared list of key names (never inferred) — keeps the boundary strict while removing the onboarding dead-end.

## Answer format
"AT-087 a|b · AT-086 a|b" (+ edits). The maker records `Answered:` here, then builds or closes as wontfix.

Answered: 2026-09-24T16:32:17+05:30 — Umesh: "go with the best" — AT-087 a (per-field exemption, kept in the join) · AT-086 a (explicit declared list of public .env key names, never inferred) — chat 2026-09-24
