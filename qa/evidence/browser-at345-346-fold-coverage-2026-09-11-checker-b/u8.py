import json, sys, urllib.parse, urllib.request, pathlib, unicodedata
BASE="http://127.0.0.1:8791"; ROOT=pathlib.Path(sys.argv[1]); CRED="ZEBRA_QUILT_APIKEY_31"
def post(p,d):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE+p,data=urllib.parse.urlencode(d).encode(),method="POST")) as r: return r.status,r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code,e.read().decode("utf-8","replace")
post("/onboard",{"slug":"u8","name":"U8","base_url":"https://demo.test","allowed_domains":"demo.test"})
post("/projects/u8/secrets",{"key":"DEMO_PASSWORD","domains":"demo.test","mask_in_screenshot":"on"})
jsonl = ROOT/"projects"/"u8"/"cases.jsonl"
FORMS={"ZWSP-U+200B (unit claims closed)":"\u200b".join(CRED),
       "CGJ-U+034F":"\u034f".join(CRED),
       "VS1-U+FE00":"\ufe00".join(CRED),
       "VS16-U+FE0F":"\ufe0f".join(CRED)}
for i,(label,payload) in enumerate(FORMS.items()):
    for field in ("title","step_value","step_expected","split-across-two-values"):
        if field=="split-across-two-values":
            half=len(payload)//2
            d={"title":f"t{i}{field}","case_class":"happy","step_action":["fill","fill"],
               "step_target":[f"#a{i}",f"#b{i}"],"step_value":[payload[:half],payload[half:]],
               "step_expected":["ok","ok"]}
        else:
            d={"title":payload if field=="title" else f"t{i}{field}","case_class":"happy",
               "step_action":"fill","step_target":f"#s{i}{field}",
               "step_value":payload if field=="step_value" else "x",
               "step_expected":payload if field=="step_expected" else "ok"}
        code,body=post("/projects/u8/cases",urllib.parse.urlencode(d,doseq=True) and d)
        print(f"  {'REFUSED ' if code==400 else 'ACCEPTED'} {label:32s} via {field:26s} ({code})")
raw = jsonl.read_text(encoding="utf-8") if jsonl.exists() else ""
visible="".join(c for c in raw if unicodedata.category(c) not in ("Cf","Mn"))
print("\ncases.jsonl (git-tracked) contains a string that RENDERS as the credential:", CRED in visible)
print("cases.jsonl contains the credential byte-for-byte:", CRED in raw)
