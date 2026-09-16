"""A3/A4 scope: is the FN specific to contentsRenders? Same page shape, non-contents children."""
import sys
from pathlib import Path
HERE = Path(__file__).parent
_src = (HERE / "moded3.py").read_text(encoding="utf-8")
exec(_src[: _src.rindex("main()")])
P = f'<p id="c">{S}</p>'
SP = f'<span id="c">{S}</span>'
CASES2 = [
    ("F1 dc{display:contents} closed, <p> child", "details::details-content{display:contents}", f"<details><summary>s</summary>{P}</details>", None),
    ("F2 dc{display:contents} closed, <span> child", "details::details-content{display:contents}", f"<details><summary>s</summary>{SP}</details>", None),
    ("F3 dc{display:inline} closed, <p> child", "details::details-content{display:inline}", f"<details><summary>s</summary>{P}</details>", None),
    ("F4 grid pattern: details{display:grid} [open]::dc{display:contents}, OPEN, contents child", "details{display:grid}details[open]::details-content{display:contents}", f"<details open><summary>s</summary>{C}</details>", None),
    ("F5 grid pattern: same CSS, CLOSED, contents child", "details{display:grid}details[open]::details-content{display:contents}", f"<details><summary>s</summary>{C}</details>", None),
    ("F6 dc{display:flow-root} closed, contents child", "details::details-content{display:flow-root}", f"<details><summary>s</summary>{C}</details>", None),
]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    rows = [run_case(b, *c) for c in CASES2]
    b.close()
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1), encoding="utf-8")
for c in rows:
    print(f"{c['case'][:70]:<70} painted={c['painted']!s:<5} " + " ".join(f"{t}={c[t]['verdict']}" for t in VERS) + f" pc={all(c[t]['pos_ctrl'] for t in VERS)} ce={[c[t]['console_errors'] for t in VERS]}")
