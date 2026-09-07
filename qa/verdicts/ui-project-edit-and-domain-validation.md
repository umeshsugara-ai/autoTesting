# Verdict — ui-project-edit-and-domain-validation

**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-project-edit-and-domain-validation.md
**Date:** 2026-09-07
**Cycle checked:** 1
**Mode:** A (unit check, fresh context — no builder reasoning available to me)
**Bound to:** `d:/autoTesting`

## VERDICT: PASS

**SCOREBOARD:** 7/7 criteria met (U1–U6 re-verified, U7 newly added by this check), 2/2
shared-layout invariants hold.

## What I re-ran myself (nothing below is the maker's paste)

| Command | My result |
|---|---|
| `docker compose exec autotester uv run pytest -q` | 306 passed, 1 skipped, 0 failed |
| `docker compose exec autotester uv run pytest -q tests/test_ui_project_edit.py` | `..........` → 10 passed |
| `docker compose exec autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec autotester uv run autotester doctor` | `doctor: clean` |

I confirmed the running container serves the unit's code before any live probe
(`GET /projects/erp/edit` → 200; `routes_project_edit.py` present in the container), so the HTTP
evidence below is of the new build, not a stale one.

## The central live claim — reproduced verbatim

```
$ curl -s -X POST http://localhost:8010/onboard \
    --data-urlencode "slug=erp-probe" --data-urlencode "name=ERP probe" \
    --data-urlencode "base_url=https://www.vidysea.com/erp" \
    --data-urlencode "allowed_domains=all"
{"detail":"this project could never run: its base URL host 'www.vidysea.com' is not covered by
 allowed domains ['all']. Add 'www.vidysea.com' to the allowed domains."}
HTTP 400

$ docker compose exec autotester sh -c 'ls projects/ | grep erp-probe || echo "nothing created"'
nothing created
```

400, the host named, nothing on disk. Then the other half of the claim — a legitimate onboard still
works end to end: `slug=chk-probe`, `base_url=https://sub.example.com/x`,
`allowed_domains=example.com` → **HTTP 303**, `projects/chk-probe/project.json` written with the
correct `base_url`/`allowed_domains`, and `GET /projects/chk-probe` → 200. That case is also the
over-tightening probe: a **subdomain** of an allowed domain is accepted, as it must be.

## 1. Is the validator stricter than the boundary it guards? — No, and this is provable, not argued

The real boundary is `browser/session.py:57-62`:

```python
def check_destination(project: Project, url: str) -> str:
    host = host_of(url)
    if not host or not project.allows_domain(host):
        raise NavigationRefused(...)
```

`helpers.py::_require_reachable_base_url` composes the **identical pair** — `host_of(base_url)`
then `Project.allows_domain(host)` on a probe `Project` carrying the submitted domains. `grep` over
`src/` confirms `allows_domain` has exactly two call sites (session.py:61 and helpers.py:57) and no
second domain-matching implementation was introduced. This matters more than it looks: `Project.
allows_domain` (schema/project.py:96-99) is **case-sensitive and does not strip a leading dot**,
while `secrets._host_matches` — used for *secret scoping*, a different question — lowercases and
strips. Had the maker reached for `_host_matches`, the validator would have accepted domains the
navigation gate later refuses. It didn't. Same function, same verdict, by construction.

**No existing project is bricked.** I ran the new validator against every project on disk:

```
pathlynks        PASS  https://pathlynks.vidysea.com/signin vs ['vidysea.com']   (subdomain path)
vidysea-erp      PASS  https://www.vidysea.com/erp          vs ['vidysea.com','www.vidysea.com']
regression-demo  PASS  http://127.0.0.1:46661/index.html    vs ['127.0.0.1']     (bare IP + port)
erp              PASS  https://www.vidysea.com/erp          vs ['vidysea.com','www.vidysea.com']
```

All four pass, including the two shapes most likely to trip a naive validator — a subdomain and a
bare IP with a port.

## 2. Is the edit route a back door? — No. Probed hostilely against the live app

| Probe | Result |
|---|---|
| `allowed_domains=all` via edit (what onboarding refuses) | **400**, same message, on-disk value unchanged |
| `allowed_domains=" , , "` (empty after split) | **400** "a project needs at least one allowed domain" |
| `name="   "` | **400** "a project needs a name" |
| `base_url=https://evil.test@sub.example.com/x` (userinfo) | **400** "is not a URL the browser can open" |
| `base_url=https://evil.test\@sub.example.com` (backslash) | **400** (refused; `host_of` fails closed on `\` — verified directly: returns `''`) |
| **`slug=hijacked` passed as an extra form field** | 303, and on disk `"slug": "chk-probe"` — unchanged, no new directory created |
| `GET`/`POST /projects/nosuch/edit` | **404** both |
| `GET /projects/BAD..slug/edit` | **400** (`_require_slug` regex) |

The slug cannot move: it is a path parameter fed through `_require_slug`, and the write is a
`model_copy(update={...})` over exactly three keys. There is no submitted state the edit route
accepts that onboarding would refuse.

**The recovery journey actually works** — the half of AT-058 that only a live test can prove. I
seeded a scratch project in the exact broken state (`allowed_domains: ['all']` against
`base_url: https://www.vidysea.com/erp`), then:

```
GET  /projects/chk-broken/edit  -> 200   (a broken project is still reachable/editable)
POST /projects/chk-broken/edit  -> 303   (allowed_domains=www.vidysea.com)
check_destination(project, project.base_url) -> 'www.vidysea.com'   (no NavigationRefused)
```

The repaired project passes the **real** navigation gate, not merely the validator.

## 3. U5 escaping on the new edit form — clean

Onboarded a project named `<script>alert(1)</script>&'" onmouseover=x` with
`base_url=https://sub.example.com/x?a='"><script>alert(2)</script>` and
`allowed_domains=example.com,ev'"il.com`, then read the raw `GET .../edit` HTML:

```
raw "<script>" occurrences: 0
value='&lt;script&gt;alert(1)&lt;/script&gt;&amp;&#x27;&quot; onmouseover=x'
value='https://sub.example.com/x?a=&#x27;&quot;&gt;&lt;script&gt;alert(2)&lt;/script&gt;'
value='example.com, ev&#x27;&quot;il.com'
```

The load-bearing detail: the attributes are **single-quoted** and `html.escape` escapes `'` to
`&#x27;` by default, so attribute breakout is closed — the exact failure a `quote=False` or an
f-string would have opened. I also read `routes_project_edit.py` in full (U5 requires reading, not
one payload): every interpolation is `escape()`d; `safe_slug` is `escape(slug)` over an
already-regex-validated slug; the POST's `Location: /projects/{slug}` header takes the same
validated slug, so no header injection either. `theme.page` and `theme.breadcrumb` are used as the
amendment log requires, and add no unescaping.

## 4. U3 credential boundary — intact

`routes_project_edit.py` imports only `theme` and two helpers; it references `SecretStore`,
`env_editor`, and `.env` **nowhere** (the sole match for "env" in the file is a docstring sentence).
Verified the write preserves what the form does not offer, against a real project read-only:

```
secrets preserved: True ['PATHLYNKS_COUNSELLOR_EMAIL', 'PATHLYNKS_COUNSELLOR_PASSWORD',
                         'PATHLYNKS_USER_EMAIL', 'PATHLYNKS_USER_PASSWORD']
write_policy preserved: True read_only     slug preserved: True
```

No secret-shaped string appears anywhere in the rendered edit form. `SecretRef` handling is
untouched by this unit's diff.

## 5. The deliberate non-fix — judged SOUND

The manifest refuses to teach `allowed_domains` a wildcard, calling it a security-model decision.
I agree, and not merely on deference:

- `allowed_domains` is the *only* thing standing between a driven browser and the open web; it is
  also the scope within which secrets may be typed. A literal `*` would be a boundary widening with
  a blast radius well beyond the usability bug being fixed, and CLAUDE.md reserves exactly that
  class of change for Umesh.
- **The user is not left stuck**, which is the test that matters. Umesh's actual intent was "test my
  ERP", not "let this browser go anywhere" — and that intent is now fully expressible, with the
  refusal naming the exact host to add (`Add 'www.vidysea.com' to the allowed domains.`) and the
  form saying where the user looks: *"There is no wildcard: name every host you mean."* The old
  failure was a `NavigationRefused` hours later, phrased in terms the user could not act on; the new
  one is a sentence that tells him what to type.
- Refusing the wildcard here is also the right *shape* of decision: a maker widening a documented
  security boundary while fixing a usability bug is precisely the drift the pair exists to catch.

If Umesh does want an allow-anything mode, that is a separate decision (and, in a Lab-Protocol repo,
a `docs/DECISIONS.md` entry) — not a residue of AT-058, which I am closing as fixed.

## Findings filed (neither is a FAIL — no criterion covers them)

- **AT-061** (low) — the "browser can open it" half of the validator is weaker than it reads:
  `host_of` returns a pseudo-host for garbage, so `base_url=all, allowed_domains=all` (303) and a
  schemeless `base_url=vidysea.com` (303) both still onboard. Self-consistent, so the AT-058 half
  correctly passes them; they would die at `page.goto`. The manifest's claim is literally
  "`host_of` returns empty", and that is exactly what the code checks — so this is a new gap, not a
  broken promise. Fix belongs in the UI layer, **not** in `host_of`, which must keep failing closed
  on exactly the cases it names.
- **AT-062** (low) — onboarding stores `name`/`base_url` verbatim while the edit form `.strip()`s
  them; `POST /onboard` with `base_url="  https://sub.example.com/x  "` persisted the padding.
  Harmless today (`host_of` tolerates it), filed so the divergence is queued rather than folklore.

## Ledger + contract

- **AT-058 → `fixed`** (`fixed_date: 2026-09-07`), with the evidence above recorded on the row.
  Both halves verified; `verified` awaits a later re-check, per protocol.
- **AT-061, AT-062** written to `qa/issues.jsonl` as new open low-severity rows.
- `qa/contracts/ui.md`: **U7 added** plus an append-only amendment-log entry. Routine,
  non-weakening. U7 pins the *composition* (`host_of` + `allows_domain`) rather than the behaviour,
  so a future unit cannot quietly let the validator drift stricter than the gate it mirrors.
- No goal task exists for this unit (manifest: "Goal task: none"), so nothing to close in `.goal/`.

## Housekeeping

All scratch projects I created while probing (`chk-probe`, `chk-xss`, `chk-broken`, `chk-garbage`,
`chk-noscheme`, `chk-ws`) were removed; `projects/` is back to its four real entries. No production
data was touched, and every read of `pathlynks` was read-only.

## EXPLANATION

The unit does what it claims, and the part most likely to have gone wrong — a validator that
over-tightens and bricks legitimate projects — is right by construction rather than by luck: it
composes the same two functions the navigation gate itself uses, and all four projects on disk still
pass. The edit route is not a back door (probed hostilely: same validator, slug immovable, unknown
project 404, blank/stranding input refused), U5 escaping holds against quotes and `<script>` in both
the project name and the base URL, and the `.env`/`SecretRef` boundary is untouched. The refusal to
add a wildcard is sound and leaves the user's real intent expressible with the host named in the
error. Two low-severity gaps filed; neither violates a criterion.
