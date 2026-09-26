# Verdict — at299b-hostless-url

**Date:** 2026-09-26 · **Cycle checked:** 1 · **Checker:** claude-sonnet-subagent + orchestrator re-run

```
VERDICT: FAIL
SCOREBOARD: hostless multi-segment paths fixed (core target met); AT-299b's expected clause NOT met for a bare dotted token: the ingest result is still '/' for a raw url that is not root-shaped
FAILURES:
- [AT-299b] sev: medium · Through the composition every caller uses, url_template(absolute_url(x), keep_host=False) (stages/ingest.py:137, stages/explore_status.py:52, stages/product_map.py:40,61), a bare dotted token with no slash still collapses to '/': 'file.html', 'sitemap.xml', 'report.pdf', 'robots.txt', 'a.b' → '/'. That is the false site-root claim AT-299b exists to kill. The expected clause's own mechanism ("after templating, if the result is '/' while the raw observed url was not root-shaped, store url_pattern=None") is not implemented, and the new tests cover only dot-free prose ('Sign in page'). · Fix: implement the clause at the ingest boundary. A slash-free token is ambiguous ('example.com' vs 'file.html' cannot be told apart by shape, AT-287), so when templating gives '/' and the raw string had no '/' after its host (no path and no trailing slash), store url_pattern=None. Keep '/' only for an explicit root ('example.com/', 'https://x.y', '/'). Do NOT stop promoting slash-free tokens to hosts: that turns a real bare host 'example.com' into the pattern '/example.com'. Add tests for 'file.html', 'example.com' → None and 'example.com/' → '/'. · issue: AT-299b
CAPABILITY-COVERAGE: 5/5 declared rows reproduced (copy c299-1: mutant_no_guard, mutant_dot_only, mutant_colon_only, mutant_no_scheme_guard each red on the named test; fixed module 19 passed); the "prose no longer claims root" row holds for its input only (see FAILURES)
LIVE-BROWSER: not-applicable (core/urls.py, tests/test_urls.py)
ISSUES-WRITTEN: none new (AT-299b stays open)
EXECUTOR: maker (checker: claude-sonnet-subagent; FAILURE re-run by the orchestrator in the worktree)
EXPLANATION: The guard correctly stops a hostless path such as 'erp/trainers' losing its first segment, and it keeps stripping dotted and ported hosts. But a filename-shaped observation still claims the site root, and the ingest-boundary None guard the issue asked for was replaced by a shape guard that cannot resolve the single-token case. Also, low: the docstring (urls.py:65-69) says 'localhost/students' "still reads as a host", but the guard leaves it unchanged (a path, '/localhost/students'); correct that sentence.
```

Orchestrator re-run in the worktree (`uv run python`): 'file.html' → '/', 'example.com' → '/', 'www.example.com' → '/', 'Sign in page' → '/Sign in page'. Base absolute_url (merge-base) prepended https:// unconditionally, so 'file.html' → '/' is not new, but it is exactly what AT-299b's expected clause asks this unit to stop.
Subagent evidence: targeted 8 files 76 passed · ruff clean · doctor clean · diff = urls.py, test_urls.py, manifest only.
