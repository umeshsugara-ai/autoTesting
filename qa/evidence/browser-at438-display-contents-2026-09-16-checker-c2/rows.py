import json, subprocess, os, sys, re
from pathlib import Path
S = Path(sys.argv[1]); C = S / "copy"
tgt = C / "src/autotester/browser/visual_order.js"
orig = tgt.read_bytes()
spec = json.loads((C / "qa/evidence/at438-display-contents/mutations.json").read_text(encoding="utf-8"))
env = dict(os.environ, PYTHONPATH=f"{C/'src'};{S/'plug'}")
T = "tests/test_browser_visual_order.py::"
def run(ids):
    r = subprocess.run([r"D:\autoTesting\.venv\Scripts\python.exe", "-m", "pytest", "-p", "pathproof", "-p", "no:cacheprovider",
                        "-o", "addopts=", "-rf", "-s", "--tb=short", *ids], cwd=C, env=env, capture_output=True, text=True)
    out = r.stdout + r.stderr
    proof = [l for l in out.splitlines() if l.startswith("PATHPROOF")]
    summ = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)][-1:]
    asserts = [l.strip() for l in out.splitlines() if l.strip().startswith("E ")][:6]
    return {"exit": r.returncode, "proof": proof, "summary": summ, "E": asserts}
res = []
for i, m in enumerate(spec["mutations"], 1):
    ids = [T + k.split("::")[1] for k in m["kills"]]
    tgt.write_bytes(orig)
    before = run(ids)
    text = orig.decode("utf-8")
    crlf = "\r\n" in text
    t = text.replace("\r\n", "\n")
    n = t.count(m["old"])
    new = t.replace(m["old"], m["new"], 1)
    tgt.write_text(new, encoding="utf-8", newline="\n")
    changed = tgt.read_bytes() != orig
    after = run(ids)
    tgt.write_bytes(orig)
    res.append({"row": i, "name": m["name"], "anchor_count": n, "file_changed": changed, "before": before, "after": after})
    print(json.dumps(res[-1], indent=1))
(S / "rows.json").write_text(json.dumps(res, indent=1))
