## D-039 | 2026-09-24 | type: decision | status: ACTIVE

**What:** Authorize building T-125, the test catalog, exactly as `plan.md` §5A specifies. It adds a
pure stage `stages/catalog.py::catalog(project, spec, store) -> Catalog`, a schema
`schema/catalog.py` (`CatalogEntry`, `Catalog`, enum `BlockedReason` with the closed vocabulary
`no_flowspec`, `flowspec_not_approved`, `missing_credential`, `no_ground_truth`, `needs_write_policy`,
`no_live_endpoint`), and a `tier` for each `CaseClass` (`static` -> `behavioural` -> `adversarial`) so runs go
cheap-to-expensive. It also adds a read-only page `GET /projects/{slug}/catalog`. Add a new contract
`qa/contracts/catalog.md` (criteria CT1-CTn). /checker authors it from §5A as DRAFT, and it goes
DRAFT->ACTIVE on this unit's checker PASS.

**Why:** `stages/expand.py` generates cases without saying which ones can actually run. A tester then
sees a case count that silently includes cases blocked on a missing credential, an unapproved
FlowSpec or a write policy. The catalog makes "what is runnable now, what is blocked, and the one
action that unblocks it" explicit. T-152 (Track C check registry) and T-166 (traceable eval compiler)
both depend on T-125 and must reuse this one Catalog, never a second one. T-125 has been ready since
D-023 registered it, but no contract existed, so no maker could build it.

**Result:** Pending build. On checker PASS: the catalog stage, schema and page land, and
`qa/contracts/catalog.md` goes ACTIVE. `tests/test_catalog.py` and `tests/test_ui_catalog.py` are
the registered done_check. No ARCHITECTURE.md prose change: the catalog is a derived view over
existing artifacts, reflected in the generated MAP/SNAPSHOT, not a new pipeline stage.

**Changes-authorized:** qa/contracts/catalog.md (new, authored by /checker as DRAFT, DRAFT->ACTIVE on
this unit's checker PASS). No ARCHITECTURE.md prose change.

**Links:** T-125; plan.md §5A; D-023 (registered T-125, Approved-by Umesh 2026-09-09); T-152; T-166;
qa/gates/t165-d039-traversal-scope.md (that proposal is renumbered D-040, since this entry takes D-039)
