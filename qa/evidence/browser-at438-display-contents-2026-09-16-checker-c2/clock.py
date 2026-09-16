import json, subprocess, os, sys, shutil
from pathlib import Path
S = Path(sys.argv[1]); C = S / "copy"
js = C / "src/autotester/browser/visual_order.js"; tf = C / "tests/test_browser_visual_order.py"
ojs, otf = js.read_bytes(), tf.read_bytes()
spec = json.loads((C / "qa/evidence/at438-display-contents/mutations.json").read_text(encoding="utf-8"))
env = dict(os.environ, PYTHONPATH=f"{C/'src'};{S/'plug'}")
ID = "tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor"
def run():
    r = subprocess.run([r"D:\autoTesting\.venv\Scripts\python.exe","-m","pytest","-p","pathproof","-p","no:cacheprovider","-o","addopts=","-s","--tb=short",ID],cwd=C,env=env,capture_output=True,text=True)
    o=r.stdout+r.stderr; return [l for l in o.splitlines() if l.startswith(("PATHPROOF","CLOCK","E ")) or " passed" in l or " failed" in l]
t = otf.decode().replace("\r\n","\n")
anchor = '    assert before and all('
assert t.count(anchor)==1
t2 = t.replace(anchor, '    print("CLOCK", before, after)\n'+anchor, 1)
t3 = t2.replace('"CONTENTS_ANIMATED_S6", "LASTCHILD_SIBLING_S7"):', '"CONTENTS_ANIMATED_S6"):', 1)
assert t3 != t2
tf.write_text(t2, encoding="utf-8", newline="\n"); print("A unmutated + print:", run())
tf.write_text(t3, encoding="utf-8", newline="\n")
m = spec["mutations"][4]; j = ojs.decode().replace("\r\n","\n"); assert j.count(m["old"])==1
js.write_text(j.replace(m["old"], m["new"],1), encoding="utf-8", newline="\n")
print("B row5 mutation, S7 assertion removed:", run())
m = spec["mutations"][3]
js.write_text(j.replace(m["old"], m["new"],1), encoding="utf-8", newline="\n")
print("C row4 mutation (span probe), S7 removed:", run())
js.write_bytes(ojs); tf.write_bytes(otf)
