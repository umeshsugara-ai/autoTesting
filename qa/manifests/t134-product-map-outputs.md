# Manifest — t134-product-map-outputs

**Unit:** T-134 / Track A5 — Product Map, recorded journeys, Sources and Issues outputs
**Commit:** `4de3321`
**Fix cycle:** 3 of 3
**Dual check:** yes — senior-software-engineer + data-engineer before checker
**Contract:** `plan.md` A5.1/A5.2; `qa/contracts/video-learning.md`
**Goal task:** T-134

## User-visible claim

An operator can register or upload a recording, run its configured vision analysis, and inspect
the persisted result through Product Map, recorded journeys and a 13-column Issues view/Excel
download. Product Map folds every persisted analysis by the canonical
`adjudicate.screen_key`, publishes only complete PNG frame references, and templates learned
URLs. Re-analysis projects current complete findings without erasing human review history;
partial analysis is monotonic and cannot delete or degrade a stable issue.

## What changed

- `stages/product_map.py::build_screen_map` folds analysed sightings, visits and journeys and
  `attach_screenshots` returns a copy of the FlowSpec.
- `ui/routes_product_map.py` renders learned screens, frames and recorded journeys; frame paths
  reject malformed names, missing files and traversal.
- `ui/routes_issues.py` renders escaped issue rows and exports the exact 13-column XLSX shape.
- `ui/routes_sources.py` supports canonical register-by-path, content-addressed uploads and
  per-source Analyze. Uploaded originals are gitignored and extension allowlisted.
- `stages/issues.py::sync_source_issues` makes a complete reading authoritative per source while
  partial readings only add genuinely new IDs. Stable complete refreshes preserve `created_at`,
  status, human id, confirmation note and evidence refs.
- Approved FlowSpecs remain byte-identical; non-approved FlowSpecs may receive screenshot refs.
- `cli_video.py` exposes `autotester ingest map <project>` and follows the same approved-FlowSpec
  boundary. `routes_live.py` is the extracted existing live-view owner.
- `docs/MAP.md` was regenerated; tests pin persistence, security, idempotence and rendered output.

## Verification reproduced by maker

```text
.\.venv\Scripts\python.exe -m pytest tests/test_issues.py tests/test_ui_sources.py
tests/test_product_map.py tests/test_ui_product_map.py tests/test_ui_issues.py
--basetemp .work\pytest-t134-finalfix -p no:cacheprovider -q
41 passed, 1 third-party deprecation warning

.\.venv\Scripts\python.exe -m pytest --basetemp .work\pytest-t134-release
-p no:cacheprovider -q
100% passed, 2 skipped, 1 third-party deprecation warning

.\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!

.\.venv\Scripts\autotester.exe doctor
doctor: clean

git diff --check
passed; Windows line-ending notices only
```

Independent release reviews on the final diff:

- senior-software-engineer: **APPROVE**, no findings; focused 41 passed.
- data-engineer: **APPROVE / PASS**; exact 8/8 screen-key fold, 3/3 sources and journeys,
  3/3 issue projection, 7/7 complete frame refs, zero URL/frame/projection violations.

## Live browser evidence — exact maker commit

Served commit `4de3321` on `http://127.0.0.1:8767` and drove the visible in-app browser:

1. `/projects/erp/product-map` rendered **8 learned screens across 3 recordings**, seven real
   screenshot thumbnails and all three ordered recorded journeys.
2. `/projects/erp/issues` rendered **3 findings** and the exact 13 headers from ID through
   Evidence. The three rows correspond to the three analysed ERP recordings.
3. `/projects/erp/sources` rendered both registration forms, three persisted sources and an
   Analyze control for each source.
4. Product Map, Issues, Flow Diagram and Sources returned HTTP 200. XLSX returned HTTP 200,
   5,822 bytes and the workbook media type. A real frame returned HTTP 200, 280,472 bytes and
   `image/png`; malformed frame name returned HTTP 400.

## Review attacks and fixes

1. Initial reviewers found upload privacy/suffix risk, stale append-only issues, approved
   FlowSpec mutation, raw URLs and weak frame validation. All were fixed and regression-tested.
2. The fresh data review found partial refresh deletion and unstable `created_at`. Both were
   fixed; partial absence is non-authoritative and stable reruns are byte-identical.
3. The fresh code review found same-ID partial degradation and missing-path echo. Partial stable
   rows are now untouched and missing-path errors use a fixed message. Final independent code
   and data reviews both approved the exact diff.

## What this unit does not claim

- It does not claim the full reusable AutoTester north star is complete. Generic credential-led
  portal exploration, exhaustive live BFS acceptance, Drive/docs/audio ingestion, durable portal
  persona generation and release-triggered regression orchestration remain broader goal work.
- It does not claim two differently named screens are semantically identical. The approved A5
  contract folds by `adjudicate.screen_key`; the ERP corpus currently contains eight distinct
  keys, while a unit fixture proves duplicate-key folding.
- It does not commit recordings, extracted frames or live ERP artifacts.
- This is pre-push local evidence. Post-push live validation remains gated on explicit push
  authorization for the named GitHub remote and branch.

## Status: checked-PASS — see `qa/verdicts/t134-product-map-outputs.md`, cycle 3 PASS
