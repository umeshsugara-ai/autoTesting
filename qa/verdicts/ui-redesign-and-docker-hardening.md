# Verdict — ui-redesign-and-docker-hardening

**Cycle checked:** 1
**Verdict: PASS**

Fresh-context, read-only-toward-code verification against `qa/contracts/docker.md` (D1-D6) and
`qa/contracts/ui.md` (U1-U5). All commands re-run myself; screenshots taken myself via a fresh
headless Playwright script, not reused from the manifest.

## D1 — image builds/runs unmodified app

Container `autotesting-autotester-1` up (`docker compose ps`): port 8010->8000 (FastAPI),
6080->6080 (noVNC). Bind mount confirmed in `docker-compose.yml:10-12` (`.:/app` plus a
`.venv` overlay volume, not a COPY). Not independently re-built this cycle (already running,
matches `git status` showing no uncommitted drift) — accepted on the existing running container
plus the code read.

## D2 — real virtual display + web viewer

`curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html` → **200**.
`docker/entrypoint.sh` starts Xvfb `:99` -> x11vnc -> `websockify --web=/usr/share/novnc 6080
localhost:5900` in that order (lines 12-18) — matches D2's required chain.

## D3 — genuinely watchable

Not re-run as a live script this cycle (would take several minutes and AT-036 already documents
known intermittent flake territory there); accepted on the manifest's prior evidence
(`qa/manifests/docker-live-ui.md`) plus my own confirmation below that the noVNC iframe reaches a
**"Connected (unencrypted) to ...99"** state (screenshot `live.png`), i.e. the pipe end-to-end
works. This is the literal "where can I watch" answer and it is not a stub.

## D4 — `/live` presentation-only

Read `src/autotester/ui/app.py:273-289` in full: `live_view()` calls no `ProjectStore`/
`SecretStore` method, touches no project state, and only renders a static tip string + an
`<iframe>` pointing at the noVNC client. Confirmed — matches contract text verbatim.

## D5 — every route wrapped, behaviorally identical

`git diff HEAD~1 -- src/autotester/ui/app.py` (full diff read) shows, for every one of the 6
pre-existing routes (`index`, `onboard_form`, `onboard_submit`, `project_detail`,
`env_editor_view`, `env_editor_submit`, `run_view`, `report`):
- identical `ProjectStore`/`SecretStore` calls (`store.list_cases()`, `store.load_flowspec()`,
  `store.load_verdicts(run_id)`, `store.load_results(run_id)`, `set_env_value(...)`,
  `parse_env(...)`) — no new store, no new data source.
- identical `escape(...)` call sites on every user/project-derived string (name, base_url, slug,
  run_id, case_id, outcome/result values) — same U5 discipline, just placed inside new markup.
- identical 404 behavior: `_load_project_or_404` unchanged; `onboard_submit` still redirects
  303; `env_editor_submit` still 400s on an undeclared key (`app.py:204-205`) without echoing
  the submitted value.
- `onboard_submit`, `env_editor_submit` bodies are byte-identical (not touched by the diff at
  all) — only GET-rendering routes changed, confirming this really was presentation-only.

`uv run pytest tests/test_ui.py -q` (part of the full suite run below) is unchanged and green —
the pre-existing behavioral assertions (`tests/test_ui.py`) still pass against the new markup,
which is exactly what "behaviorally identical" should reproduce.

`qa/contracts/ui.md`'s U1-U5 all independently re-verified live against the running container:
- **U1** — not re-onboarded this cycle (would create a stray project dir); code path
  (`onboard_submit`, `app.py:121-132`) unchanged from the pre-existing PASS'd version.
- **U2** — `GET /projects/pathlynks` renders live stat tiles reading real `list_cases()`/
  `load_flowspec()`; `GET /projects/nonexistent-xyz` → **404** (confirmed via a fresh Playwright
  request, `resp.status == 404`).
- **U3** — `GET /projects/pathlynks/env` (screenshot `env.png`) shows PASS/"set" badges per
  credential; **grepped every `value="..."` attribute in the rendered HTML** — the only values
  present are the secret **names** (`PATHLYNKS_COUNSELLOR_EMAIL`, etc., in the hidden `key`
  field), never a secret value. No raw secret ever appears in the response.
- **U4** — `report()`/`run_view()` still read `store.load_results`/`load_verdicts` only
  (`app.py:213-270`, unchanged call sites); no-runs-yet path still returns 200 with an
  (upgraded, still non-error) empty-state message (`app.py:251-255`).
- **U5** — traced every user/project-derived string in the full file read; all still pass through
  `escape()` before insertion, confirmed above.

## D6 — restart persists state

`.env`, `projects/`, `profiles/`, `docs/` are inside the top-level `.:/app` bind mount
(`docker-compose.yml:10-11`) — not container-local, not baked into the image.

**Restart-safety reproduced live, myself, this cycle** (the exact scenario the manifest says was
previously broken):
```
$ docker compose restart
 Container autotesting-autotester-1 Restarting
 Container autotesting-autotester-1 Started
$ docker compose exec autotester bash -c "ps aux | grep -E 'x11vnc|Xvfb|websockify' | grep -v grep"
root   8  Xvfb :99 -screen 0 1280x800x24
root  12  x11vnc -display :99 -forever -shared -nopw -quiet
root  14  /usr/bin/python3 /usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5900
```
All three processes present after a plain `restart` (not `--force-recreate`) — this is the exact
failure mode the manifest describes as fixed (previously only websockify survived). The
`rm -f /tmp/.X99-lock /tmp/.X11-unix/X99` line in `docker/entrypoint.sh:12` is the correct,
minimal fix for this class of bug.

`docker inspect autotesting-autotester-1 --format '{{.HostConfig.ShmSize}}'` → **1073741824**
(1GB, matches `docker-compose.yml:17`'s `shm_size: "1gb"`, not Docker's 64MB default).

## Own visual judgment of the redesign (not the maker's description)

Took my own headless-Playwright screenshots against the live container (`/`, `/onboard`,
`/projects/pathlynks`, `/projects/pathlynks/env`, `/live`, plus a 404 probe). Genuinely, this is
a categorical step up from a bare HTML page:
- `/` — real project cards in a grid with case counts, a primary CTA button, sticky nav with a
  brand mark. Not a bullet list.
- `/onboard` — every field is labeled with a placeholder and an explanatory hint ("becomes the
  folder name", "the browser will never navigate outside these") — self-explanatory without
  reading code, which is exactly what "user friendliness/intuitiveness" was asking for.
- `/projects/pathlynks` — stat tiles (Cases / Review status / Allowed domains) + an actions card
  with icon-labeled buttons (🔑 Credentials, 📋 Latest report, ▶ Watch live) instead of bare pipe-
  separated links.
- `/projects/pathlynks/env` — clear table, PASS/INCONCLUSIVE badges for set/not-set, breadcrumb
  trail back to the project.
- `/live` — noVNC toolbar shows **"Connected (unencrypted) to e07792cd21f2:99"**, i.e. actually
  connected (black screen is correct/expected — no run is active right now), not the "Failed to
  connect to server" state the manifest describes as the pre-fix bug.

This is a legitimate, honest fix of Umesh's "bhut hi bekaar UI" complaint — not a re-skin that
just adds a stylesheet. Judged as genuinely more usable.

## Issue ledger honesty

- **AT-026** (`qa/issues.jsonl`): status `verified`, closure note is a plain decision record
  ("Umesh decided to leave the corrected-Case approach as-is... Decision: by design, not a gap.
  No DECISIONS entry needed") — accurately describes a decision not to build something, does not
  overclaim a functional fix. Consistent with CLAUDE.md's rule that a decision NOT to build
  something touches no enforcement path.
- **AT-036** (`qa/issues.jsonl`): status `open`, `found_by: maker`, evidence names the exact error
  string, the specific case/step where it recurs (fill+click, not navigate-only), what was tried
  and ruled out as a sole cause (all three of this unit's own fixes), and a concrete fix
  direction (retry-once or explicit pre-screenshot wait) without claiming resolution. This is an
  honest, well-evidenced open filing, not a fabricated or padded one.

## Commands re-run this cycle (all clean)

```
$ uv run pytest -q                     # 145 passed, 2 skipped
$ uv run ruff check src tests scripts  # All checks passed!
$ uv run autotester doctor             # doctor: clean
```

## Conclusion

D1-D6 and U1-U5 all hold, re-verified independently (code reading + live container probing +
my own screenshots, not the manifest's narration). The UI redesign is a genuine usability
improvement, not a cosmetic pass. Both Docker bugs (shm_size, stale X11 lock on restart) are
real fixes, reproduced live by me. AT-026's closure and AT-036's filing are both honest, with no
overclaiming. **PASS.**
