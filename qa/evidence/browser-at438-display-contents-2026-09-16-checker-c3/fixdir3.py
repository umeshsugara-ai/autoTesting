"""Is the AT-453 fix direction sound? NEW vs NEW+pseudo-display conjunct on the A rows (own ground truth)."""
import sys
from pathlib import Path
HERE = Path(__file__).parent
_src = (HERE / "attack3.py").read_text(encoding="utf-8")
exec(_src[: _src.rindex("main2()")])
OLDL = 'window.getComputedStyle(box, "::details-content").contentVisibility === "hidden") return false;'
NEWL = '(p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;'
assert VERS["NEW"].count(OLDL) == 1
cand = VERS["NEW"].replace(OLDL, NEWL)
VERS.clear(); VERS["NEW"] = cand
rows = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for a in [x for x in ATTACKS if x[0][0] in "AB"] + [
        ("F6 dc{display:flow-root} closed", "details::details-content{display:flow-root}", f"<details><summary>s</summary>{C}</details>", None),
        ("G1 closed dc{display:grid}", "details::details-content{display:grid}", f"<details><summary>s</summary>{C}</details>", None)] + [c for c in CASES if "details" in c[0]]:
        r = run_case(b, *a); rows.append(r)
        print(f"{r['case'][:60]:<60} painted={r['painted']!s:<5} CAND={r['NEW']['verdict']} pc={r['NEW']['pos_ctrl']} ce={r['NEW']['console_errors']}")
    b.close()
print("CAND wrong:", [r["case"] for r in rows if r["NEW"]["verdict"] != "ok"])
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1), encoding="utf-8")
