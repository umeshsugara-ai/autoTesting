# at108-at114-swallowed-causes

**Unit:** AT-108 + AT-114 as ONE sweep of every swallowed exception in `stages/explore*.py`
**Commit:** 6e98487
**Fix cycle:** 1
**Contract:** `qa/contracts/explore.md` X11 (incremental crash-survivable artifacts), X16 (refusal
reporting). Also `core-invariants.md` C9 in spirit: a failure is honoured or reported, never
silently replaced by a weaker outcome.

## Why this is one unit and not three patches

AT-108 and AT-114 were filed separately, against different functions, by different checks. They are
the same defect. When AT-108 was filed the lesson recorded was *"'the cause was swallowed' is a
shape, not a location"* -- so this unit sweeps every `except` in the explore stages rather than
patching the one that was reported most recently. Three sites had it; a fourth (`try_action`) was
already correct and is left alone.

## What changed

| Site | Before | After |
|---|---|---|
| `explore_node.capture()` | `except Exception: return None` | files an `EVIDENCE` issue naming the cause; still non-fatal |
| `explore_node.return_to()` | `except Exception: _recover(); return False` | binds cause to `rt.return_error`, then recovers |
| `explore_node._recover()` | `except Exception: pass` | appends its cause to the original, never replacing it |
| `explore.ExploreRuntime` | -- | new `return_error` scratch field, same pattern as the existing `seed_error` |
| `schema/enums.py IssueKind` | 4 members | `+ EVIDENCE` |

Both AT-113 issue texts now carry `_why(rt)`, which returns the recorded cause or the explicit
string `"cause not recorded"` -- worse than a cause, but honest, and it tells a reader the gap is in
this crawler rather than in the product it was looking at.

## The design call the checker should rule on

**`IssueKind.EVIDENCE` is a new member of a closed vocabulary.** The alternative was to file
screenshot failures as `NAVIGATION`. I rejected it: a `CrawlIssue` is read as a finding about the
product under test, and inflating that list with the crawler's own failures is the same dishonesty
X9 already forbids when it refuses to count third-party noise as a product issue. The second test
exists specifically to pin that, and the lazy fix fails it. If the checker disagrees, the argument
belongs in the contract rather than left implicit.

**Second call: `capture()` stays non-fatal.** AT-114's text can be read as "stop swallowing, let it
raise". I did not, because X11 wants a crash-survivable partial graph and killing a crawl over a
missing screenshot is worse than a graph with a documented hole. The defect was the *silence*, not
the survival.

## Evidence

```
$ SABOTAGE 1: capture() -- blind except, cause discarded
E       assert []
FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_recorded_with_its_cause

$ SABOTAGE 2: return_to() -- cause discarded
E       assert False
FAILED tests/test_explore_error_causes.py::test_a_lost_screen_reports_why_it_was_lost

$ SABOTAGE 3: _recover() -- bare pass
E       AssertionError: assert 'browser gone' in (('back failed'))
FAILED tests/test_explore_error_causes.py::test_a_failed_recovery_says_so_instead_of_passing_silently

$ SABOTAGE 4: the LAZY fix -- file the tool failure as a product NAVIGATION issue
E       assert []
E       AssertionError: assert [CrawlIssue(s...t_party=True)] == []
FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_recorded_with_its_cause
FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_not_reported_as_a_product_bug

$ RESTORE
4 passed
```

Sabotages 1-3 each fail exactly one test -- the one defending that site -- which is stronger than
"they all fail", because it proves the three tests are not redundant. Sabotage 4 fails two, which is
the entire reason the second test exists: it defends against the wrong fix, not the missing one.

## Verification (host; Docker daemon down, `uv` runs natively -- not a blocker)

```
uv run pytest -q                       590 passed, 2 skipped   (586 before + 4 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

The 2 skips are the live-Mongo opt-in (`tests/test_db.py:93`) and the POSIX-only permissions test
(`tests/test_ui.py:163`); the container reports 1 because the latter runs there.

## What this does NOT claim

- No live crawl was run. There are still **zero** `crawl/` dirs on disk; this is unit-level only.
- `try_action`'s `except Exception as exc` was already binding its cause into the edge detail and
  is unchanged -- named here so the sweep's scope is auditable rather than assumed complete.
- `stages/explore_safety.py`, `explore_merge.py` and `screen_identity.py` contain no `except` at
  all (`grep -n except` -> no matches). The sweep covered the whole surface it claimed to.

## Status: checked-PASS
