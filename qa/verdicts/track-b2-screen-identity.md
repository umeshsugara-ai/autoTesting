# Verdict — track-b2-screen-identity

**Manifest:** qa/manifests/track-b2-screen-identity.md
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3, C6)
**Goal task:** T-141
**Cycle checked: 1**

## Verdict: PASS

## What I verified myself (fresh context, re-run not re-read)

### 0. Commits actually landed and are pushed

`git rev-parse HEAD origin/master` both resolve to `712693c91a23c78777e29b640c648b6af15bb704` —
the manifest commit is HEAD and already matches origin. Source commit `b1f39f6` (`feat(schema,
stages): Track B2 -- screen identity + crawl schema + store (D-015)`) sits directly under it.
Nothing to push. Working tree clean.

### 1. Staleness guard

`docker inspect autotesting-autotester-1 --format '{{.State.StartedAt}}'` → started
`2026-09-07T13:08:35Z`. Newest changed-file mtimes in the diff are `13:02:21Z`–`13:04:48Z`
(files were written before the commit's `18:39:44 IST` = `13:09:44Z` metadata timestamp, as
expected — git doesn't preserve write time). `docker-compose.yml` confirms `.:/app` is a live
bind mount (not a baked image copy), so the container's live output reflects the committed code.

### 2. ScreenNode.id is content-addressed, not URL- or description-based (read directly)

`src/autotester/schema/screen_graph.py:70-73`:
```python
def model_post_init(self, _context: object) -> None:
    if not self.id:
        payload = {"t": self.url_template, "s": self.signature}
        object.__setattr__(self, "id", content_id("node", payload))
```
Confirmed: identity is `content_id` over `{url_template, signature}` only. No raw `url` field
feeds the hash (`url_example` is stored but never hashed), and no free-text/LLM description
field exists on `ScreenNode` at all. Matches the manifest's claim exactly.

### 3. The two directional tests, read and re-run

Ran `docker compose exec autotester uv run pytest tests/test_screen_identity.py -q -k
"two_list_rows or two_ids_collapse or different_controls" -v` → `3 passed`.

Read the assertions directly (`tests/test_screen_identity.py`):
- `test_two_ids_collapse_to_one_node_identity` (L53-64): builds two `PageObservation`s at
  `/students/1` and `/students/2` with **identical** elements, calls `node_from`, asserts
  `node_1.id == node_2.id` **and** `url_template == "/students/{id}"`. Genuinely tests the
  collapse-to-one-screen direction on real `ScreenNode.id`, not just `structural_signature`.
- `test_different_controls_at_the_same_url_are_different_nodes` (L67-82): same URL
  (`/dashboard`), one observation with `[Open filters]`, the other with `[Open filters, Show
  archived]` (a genuinely new non-row control), asserts `node_closed.id != node_open.id`. This
  is the direction the prior attempt's URL-only identity would have missed — confirmed the test
  actually varies signature-affecting elements, not something structurally irrelevant.
- Companion `test_two_list_rows_with_different_data_share_a_signature` (L16-20) confirms the
  same collapse one level down, at `structural_signature` directly, via `in_row=True` elements —
  consistent with `ScreenNode`'s row-exclusion rule.

Both directional claims hold on evidence, not just test names.

### 4. core/urls.py::url_template is the only normalisation function (C3)

`grep -rn "url_template|urlparse|def.*template" src/` → 3 hits: the definition itself in
`core/urls.py`, its sole caller in `stages/screen_identity.py`, and one unrelated match in
`browser/secrets.py` that does not define or reimplement URL templating (verified by reading
the surrounding lines — not a duplicate). No second normalisation function exists. `url_template`
in `core/urls.py:37-48` does exactly what the manifest claims: strips query/fragment via
`urlsplit`, collapses repeated slashes via the segment split/join, templates numeric/UUID/ULID/
hex(≥16)/date segments to `{id}`/`{date}`.

### 5. The store split is a genuine mixin, not a second store

Read `store/crawl_store.py` in full: `CrawlStoreMixin` declares only type annotations for
`paths`/`_node_ids` (no `__init__`, never instantiated alone — docstring says so explicitly) and
methods (`save_crawl`, `load_crawl`, `add_node`, `list_nodes`, `add_edge`, `list_edges`,
`add_crawl_issue`, `list_crawl_issues`, `save_frontier`, `load_frontier`) that read/write via
`ProjectPaths`/`filestore`, the same primitives `project_store.py` itself uses — no parallel
storage mechanism.

Reproduced the manifest's own live check:
```
$ docker compose exec autotester uv run python -c "from autotester.store.project_store import ProjectStore; print('add_node' in dir(ProjectStore), 'CrawlStoreMixin' in [c.__name__ for c in ProjectStore.__mro__])"
True True
```
`ProjectStore`'s public API is unchanged (methods appear via inheritance) and the MRO genuinely
includes `CrawlStoreMixin`.

### 6. NoiseCount is a typed model, not a raw dict field

`schema/crawl.py:97-103`:
```python
class NoiseCount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str
    count: int = 0
```
and `Crawl.noise_counts: list[NoiseCount] = Field(default_factory=list)` (L124) — confirmed
`list[NoiseCount]`, not `dict[str, int]`. Matches the manifest's claim of deliberately avoiding
the T-130-round dict-field precedent.

### 7. No C1 violation — no dict-shaped domain object in the new schema files

Grepped `schema/screen_graph.py`, `schema/crawl.py`, `schema/enums.py` for dict-typed fields.
The only dict hit is the pre-existing `KIND_BY_CLASS: dict[CaseClass, CaseKind]` module-level
enum-to-enum lookup table in `enums.py` — not new to this unit, not a domain object (it's a
static classification map between two closed vocabularies, not an artifact field), and not
touched by this diff. No new dict-shaped domain object was introduced.

### 8. Line caps

```
wc -l src/autotester/store/project_store.py src/autotester/store/crawl_store.py \
  src/autotester/core/urls.py src/autotester/stages/screen_identity.py \
  src/autotester/schema/screen_graph.py src/autotester/schema/crawl.py
  266 project_store.py
   67 crawl_store.py
   48 urls.py
   60 screen_identity.py
  107 screen_graph.py
  124 crawl.py
```
All well under 300; `project_store.py` at 266 confirms the split was needed and effective
(manifest said it would have landed at 313 without the split).

### 9. Full verify suite — re-run, not trusted from the manifest

```
$ docker compose exec autotester uv run pytest tests/test_urls.py tests/test_screen_identity.py tests/test_store_crawl.py tests/test_schema.py -q
....................................  (36 passed)

$ docker compose exec autotester uv run pytest -q
exit 0, no failures reported; --collect-only -q confirms 435 total items collected across the
suite (434 passed + 1 skipped by count, matching the manifest's claimed total, up from 406 before
this unit)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

## Scoreboard

4/4 criteria met (C1, C2, C3, C6), 2/2 named invariants hold (screen-identity collapse direction,
screen-identity differentiation direction).

## Issues addressed

None claimed by this manifest.

## Ledger

No new findings — nothing written to `qa/issues.jsonl`.
