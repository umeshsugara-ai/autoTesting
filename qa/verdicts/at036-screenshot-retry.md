# Verdict — at036-screenshot-retry

**Manifest:** qa/manifests/at036-screenshot-retry.md
**Contract:** qa/contracts/browser-and-secrets.md (B7 — screenshot masking / evidence capture)
**Cycle checked:** 1
**Verdict: PASS**

## What was checked

### 1. Scope of the fix — `src/autotester/browser/session.py::BrowserSession.screenshot` (lines 187-208)

```
201:        try:
202:            self.page.screenshot(path=path, full_page=False)
203:        except Exception as exc:
204:            if "captureScreenshot" not in str(exc):
205:                raise
206:            self.page.wait_for_timeout(250)
207:            self.page.screenshot(path=path, full_page=False)
208:        return self._record(EvidenceKind.SCREENSHOT, name, step_order=step_order, label=label)
```

- Matches on the exact substring `"captureScreenshot"` only — any other exception message hits
  `raise` immediately at line 205, unmodified. No broad `except Exception: pass`, no retry loop,
  no backoff beyond the single documented 250ms wait.
- Exactly one retry: the second `self.page.screenshot(...)` call at line 207 is not itself wrapped
  in another try/except, so a second consecutive failure of the same error propagates unchanged
  (nothing catches it a second time).
- No change to masking: `add_style_tag(content=MASK_CSS)` (line 197) still runs before every
  capture attempt, both the first and the retried one, since it happens once before the try block
  — B7's masking-before-capture guarantee is preserved on the retried path too.
- No changes to `execute.py`, `_record`, redaction, or any other evidence path — confirmed by
  reading the full diff scope named in the manifest; the only touched function is `screenshot()`.

**Judgment: narrow.** This cannot mask a real failure — it only absorbs one specific, named
transient string, exactly once, and every other failure mode (including a second occurrence of
the same error) surfaces exactly as before.

### 2. Tests — `tests/test_browser.py`

Fake class `_FlakyCaptureScreenshotPage(FakePage)` (lines 152-170) takes a `fail_times` counter,
raises the real CDP error string that many times then delegates to the real `FakePage.screenshot`
(which writes the file), and records each `wait_for_timeout` call in `waited_ms`. This is a
genuine fake that fails N times then succeeds — not a stub that trivially passes regardless of
implementation.

- `test_screenshot_retries_once_on_the_known_transient_protocol_error` (line 173): `fail_times=1`
  — asserts the file actually exists on disk after the call and `waited_ms == [250]` (exactly one
  wait, exactly 250ms). This would fail if the retry didn't happen, waited a different amount, or
  waited more than once.
- `test_screenshot_gives_up_after_a_second_consecutive_failure` (line 181): `fail_times=2` —
  asserts the exception propagates with `match="captureScreenshot"`. This would fail if the code
  looped/retried more than once or silently swallowed the second failure.
- `test_screenshot_does_not_retry_a_different_error` (line 188): a fresh `_OtherErrorPage`
  raising `"Target page, context or browser has been closed"` — asserts the error propagates
  immediately with no retry (no `wait_for_timeout` call is possible since `FakePage` doesn't
  define one, so a wrongful retry attempt would itself raise `AttributeError` rather than pass).

**Judgment:** all three tests exercise the actual retry-once-then-give-up state machine via a
call-counting fake, not a happy-path-only fixture.

### 3. Independent re-run of all verification commands

```
$ uv run pytest tests/test_browser.py -v
collected 14 items
tests\test_browser.py ..............                                     [100%]
14 passed in 0.97s
```

```
$ uv run pytest -q
............................................s........................... [ 34%]
........................................................................ [ 69%]
........................................................s.......         [100%]
(all green, 2 pre-existing skips unrelated to this change)
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

All match the manifest's claims exactly.

### 4. Real Docker repro (the actual bug environment)

Container was already up (`docker compose ps` showed `autotesting-autotester-1` healthy, port
8010 responding `200`). Ran the exact repro command 5 times (manifest ran 3; I ran 5 for more
margin):

```
$ for i in 1 2 3 4 5; do docker compose exec autotester bash -c \
    "cd /app && rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py"; done
=== run 1 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 2 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 3 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 4 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 5 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
```

Every run shows the login case correctly judged `FAIL (observed: 'Invalid credentials')` — a
real, non-empty observation — and the homepage case `PASS`. No `Protocol error
(Page.captureScreenshot)`, no `ERRORED`, no empty/INCONCLUSIVE observation in any of the 5 runs.
This is the exact failure mode AT-036 described, and it did not recur across 5 consecutive runs
(previously flaking roughly every other run per the manifest and issue).

## Conclusion

- Retry is genuinely narrow: one exact error string, one retry, everything else (including a
  repeated failure of the same kind) propagates unchanged. Cannot mask an unrelated real failure.
- Tests exercise the actual retry-once/give-up/no-false-retry behavior via a fail-counting fake,
  not happy-path-only stubs.
- Real Docker repro (5 runs, exceeding the 3-5 asked for) shows the flake did not recur, with the
  login case correctly reaching a real FAIL judgment rather than an empty/ERRORED observation.
- All stated commands (`pytest tests/test_browser.py -v`, `pytest -q`, `ruff check`,
  `autotester doctor`) reproduced exactly as claimed in the manifest.

**PASS.**
