"""Checker step 4b, at438 cycle 3: every mutation row reproduced in a THROWAWAY copy (argv[1]/copy).
Before = the named test green IN THE COPY; after = the same test with one row applied.
PATHPROOF proves pytest imported the copy's src. Also evaluates each mutated detector on the
fixture directly and lists EVERY sentinel it gets wrong, so row isolation is measured, not inferred."""
import json, os, re, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

S = Path(sys.argv[1]); C = S / "copy"
tgt = C / "src/autotester/browser/visual_order.js"
orig = tgt.read_bytes()
spec = json.loads((C / "qa/evidence/at438-display-contents/mutations.json").read_text(encoding="utf-8"))
env = dict(os.environ, PYTHONPATH=f"{C / 'src'};{S / 'plug'}")
T = "tests/test_browser_visual_order.py::"
SHOWN = ["CONTENTS_PLAIN_S1", "CONTENTS_OPENDETAILS_S2", "CONTENTS_ANIMATED_S6", "LASTCHILD_SIBLING_S7", "CONTENTS_ACCORDION_S10"]
HIDDEN = ["CONTENTS_CLOSEDDETAILS_S3", "CONTENTS_CVHIDDEN_S4", "CONTENTS_DISPLAYNONE_S5", "CONTENTS_UNSLOTTED_S8",
          "CONTENTS_INSELECT_S9", "CONTENTS_SECONDSUMMARY_S11", "CONTENTS_DETAILSCONTENTS_S12", "CONTENTS_SLOTINCLOSED_S13"]
FIX = (C / "tests/fixtures/bidi_site/cvcontents.html").as_uri()


def run(ids):
    r = subprocess.run([r"D:\autoTesting\.venv\Scripts\python.exe", "-m", "pytest", "-p", "pathproof", "-p", "no:cacheprovider",
                        "-o", "addopts=", "-rf", "-s", "--tb=short", *ids], cwd=C, env=env, capture_output=True, text=True, timeout=900)
    out = r.stdout + r.stderr
    return {"exit": r.returncode, "proof": [l for l in out.splitlines() if l.startswith("PATHPROOF")],
            "summary": [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)][-1:],
            "E": [l.strip()[:300] for l in out.splitlines() if l.strip().startswith("E ")][:4]}


def wrong(browser, js):
    page = browser.new_page(viewport={"width": 900, "height": 600})
    page.goto(FIX); page.wait_for_timeout(400)
    seen = page.evaluate(js); page.close()
    return {"missing": [s for s in SHOWN if s not in seen], "leaked": [s for s in HIDDEN if s in seen]}


res = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    res.append({"row": 0, "name": "UNMUTATED copy", "fixture_wrong": wrong(b, orig.decode("utf-8"))})
    print(json.dumps(res[-1]))
    for i, m in enumerate(spec["mutations"], 1):
        ids = [T + k.split("::")[1] for k in m["kills"]]
        tgt.write_bytes(orig)
        before = run(ids)
        t = orig.decode("utf-8").replace("\r\n", "\n")
        n = t.count(m["old"])
        new = t.replace(m["old"], m["new"], 1)
        tgt.write_text(new, encoding="utf-8", newline="\n")
        changed = tgt.read_bytes() != orig
        after = run(ids)
        fw = wrong(b, new)
        tgt.write_bytes(orig)
        res.append({"row": i, "name": m["name"], "anchor_count": n, "file_changed": changed,
                    "before": before, "after": after, "fixture_wrong": fw})
        print(json.dumps(res[-1], indent=1))
    b.close()
assert tgt.read_bytes() == orig
(Path(__file__).parent / "rows3.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
