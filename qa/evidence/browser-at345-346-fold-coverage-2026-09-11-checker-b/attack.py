"""Checker-authored live on-disk attack against the AT-345/346 fold."""
import json, sys, urllib.parse, urllib.request, pathlib
BASE="http://127.0.0.1:8791"
ROOT=pathlib.Path(sys.argv[1])
CRED="ZEBRA_QUILT_APIKEY_31"

def post(path, data):
    body=urllib.parse.urlencode(data).encode()
    req=urllib.request.Request(BASE+path, data=body, method="POST")
    try:
        with urllib.request.urlopen(req) as r: return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")

# seed a project declaring the secret
post("/onboard", {"slug":"seed","name":"Seed","base_url":"https://demo.test","allowed_domains":"demo.test"})
post("/projects/seed/secrets", {"key":"DEMO_PASSWORD","domains":"demo.test","mask_in_screenshot":"on"})

def il(ch): return ch.join(CRED)
ATT = {
 "cgj":            il("\u034f"),
 "vs1":            il("\ufe00"),
 "vs16":           il("\ufe0f"),
 "mongolian-fvs":  il("\u180b"),
 "khmer-viriam":   il("\u17d2"),
 "hangul-filler":  il("\u3164"),
 "braille-blank":  il("\u2800"),
 "rtl-reversed":   "\u202e"+CRED[::-1],
 "base64":         __import__("base64").b64encode(CRED.encode()).decode(),
 "html-entities":  "".join(f"&#{ord(c)};" for c in CRED),
 "regional-ind":   CRED.translate({c:c-0x41+0x1F1E6 for c in range(0x41,0x5B)}),
 "armenian":       CRED.replace("O","\u0555").replace("Q","\u0562"),
 "cherokee":       CRED.replace("A","\u13AA").replace("E","\u13AC").replace("Z","\u13C3"),
}
results={}
for label,payload in ATT.items():
    slug=f"atk-{label}"
    code,text=post("/onboard",{"slug":slug,"name":payload,"base_url":"https://demo.test","allowed_domains":"demo.test"})
    cfg=ROOT/"projects"/slug/"project.json"
    on_disk = cfg.exists()
    stored = json.loads(cfg.read_text(encoding="utf-8"))["name"] if on_disk else None
    visible = "".join(c for c in (stored or "") if __import__("unicodedata").category(c) not in ("Cf","Mn"))
    results[label]={"status":code,"written":on_disk,"renders_as_credential":visible==CRED}
    print(f"{label:16s} status={code} written={on_disk} renders_exactly_as_credential={visible==CRED}")
json.dump(results, open(sys.argv[2],"w"), indent=2)
