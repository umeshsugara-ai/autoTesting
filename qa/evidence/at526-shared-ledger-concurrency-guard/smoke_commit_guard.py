import importlib.util, json, sys

spec = importlib.util.spec_from_file_location(
    "commit_guard", "qa/evidence/at526-shared-ledger-concurrency-guard/commit_guard.proposed.py")
cg = importlib.util.module_from_spec(spec)
# stub out typer so the module imports without the dependency mattering to the pure functions
import types
fake_typer = types.ModuleType("typer")
class _FakeTyper:
    def __init__(self, *a, **k): pass
    def command(self, *a, **k):
        def deco(f): return f
        return deco
fake_typer.Typer = _FakeTyper
fake_typer.Option = lambda *a, **k: None
fake_typer.Argument = lambda *a, **k: None
fake_typer.Exit = Exception
fake_typer.colors = types.SimpleNamespace(RED="red", GREEN="green", YELLOW="yellow")
fake_typer.secho = lambda *a, **k: None
sys.modules["typer"] = fake_typer
spec.loader.exec_module(cg)

def row(id_, **kw):
    d = {"id": id_, "status": "open"}
    d.update(kw)
    return json.dumps(d)

# 1. unchanged -> no diff
text = row("AT-1") + "\n" + row("AT-2") + "\n"
assert cg.diff_ledger_ids(text, text) == {}, "FAIL: unchanged"
print("PASS: unchanged ledger -> no diff")

# 2. reordered rows -> no diff
old = row("AT-1") + "\n" + row("AT-2") + "\n"
new = row("AT-2") + "\n" + row("AT-1") + "\n"
assert cg.diff_ledger_ids(old, new) == {}, "FAIL: reorder"
print("PASS: reordered rows -> no diff")

# 3. reformat (key order + ensure_ascii-style) -> no diff (a8caf58 class)
old = '{"id": "AT-1", "status": "open", "title": "caf\u00e9"}\n'
new = '{"status": "open", "title": "café", "id": "AT-1"}\n'  # literal utf-8 unicode char, reordered keys
assert cg.diff_ledger_ids(old, new) == {}, f"FAIL: reformat -> {cg.diff_ledger_ids(old, new)}"
print("PASS: reformatted-but-same-content row -> no diff")

# 4. added / changed / removed
old = row("AT-1") + "\n" + row("AT-2") + "\n"
new = row("AT-1", status="fixed") + "\n" + row("AT-3") + "\n"
got = cg.diff_ledger_ids(old, new)
assert got == {"AT-1": "changed", "AT-2": "removed", "AT-3": "added"}, got
print("PASS: added/changed/removed classified correctly:", got)

# 5. THE ACTUAL AT-526 SCENARIO: two checkers, one commit
# HEAD (before either checker touches anything)
head = row("AT-520", status="open") + "\n" + row("AT-521", status="open") + "\n"
# at520 checker's uncommitted edit lands in the working tree first (flip + append)
# at521 checker's own working tree ALSO has its own edit (flip AT-521) plus,
# because they share one working copy, at520's edits too:
working_tree_at521_sees = (
    row("AT-520", status="fixed") + "\n" +     # at520 checker's flip (not at521's)
    row("AT-521", status="fixed") + "\n" +     # at521 checker's own flip
    row("AT-525", extra="at520 checker's append") + "\n"  # at520 checker's append
)
unexpected = cg.unexpected_ledger_changes(head, working_tree_at521_sees, {"AT-521", "AT-524"})
assert "AT-520" in unexpected and "AT-525" in unexpected, unexpected
assert "AT-521" not in unexpected, unexpected
print("PASS: reproduces + would have REFUSED the real AT-526 incident:", unexpected)

# 6. clean case: only the declared ids changed -> no refusal
clean_new = row("AT-520", status="open") + "\n" + row("AT-521", status="fixed") + "\n"
assert cg.unexpected_ledger_changes(head, clean_new, {"AT-521"}) == {}
print("PASS: no unexpected ids -> clean, would commit")

# 7. Would this also have caught AT-496's stale-copy drop?
# 9b5cbc5 appended AT-494 and flipped AT-401 to fixed; 1688da3 (30 min later) built its
# commit from a STALE blob that predated both of those changes, silently reverting them.
head_at_1688da3_time = row("AT-401", status="fixed") + "\n" + row("AT-494", status="open") + "\n"
stale_copy_the_checker_actually_read = row("AT-401", status="open") + "\n"  # pre-9b5cbc5 blob
# that checker's own intent: append AT-499 only, nothing about AT-401/AT-494
its_own_new_text = stale_copy_the_checker_actually_read + row("AT-499", status="open") + "\n"
unexpected = cg.unexpected_ledger_changes(head_at_1688da3_time, its_own_new_text, {"AT-499"})
assert "AT-401" in unexpected and "AT-494" in unexpected, unexpected
print("PASS: would ALSO have caught the AT-496 stale-copy drop/revert:", unexpected)
