import sys, urllib.parse, urllib.request
BASE="http://127.0.0.1:8791"
def post(p,d):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE+p,data=urllib.parse.urlencode(d).encode(),method="POST")) as r: return r.status,r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code,e.read().decode("utf-8","replace")
post("/onboard",{"slug":"fp2","name":"FP2","base_url":"https://demo.test","allowed_domains":"demo.test"})
post("/projects/fp2/secrets",{"key":"DEMO_PASSWORD","domains":"demo.test","mask_in_screenshot":"on"})
BS=chr(92)
LEGIT=[("url-with-query","Open https://demo.test/search?q=a+b&sort=desc#top"),
 ("json-body",'Submit {"user":"alice","role":"admin","n":31}'),
 ("css-selector","Click div.card > ul li:nth-child(2)[data-id='x']"),
 ("xpath","//div[@id='main']//a[contains(@href,'/logout')]"),
 ("code-snippet","assert (a + b) == c; # zebra quilt"),
 ("french-name","Nom d'utilisateur: Ayse Gulsen Ozturk"),
 ("turkish-name","Kullanici: AYSE GULSEN OZTURK IZMIR"),
 ("hindi-name","\u0909\u092e\u0947\u0936 \u0938\u0941\u0917\u0930\u093e"),
 ("cyrillic-name","\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0421\u0435\u0440\u0433\u0435\u0439 \u041f\u0440\u043e\u0445\u043e\u0440\u043e\u0432"),
 ("regex","^[A-Z]{3}-[0-9]{4}$ must match"),
 ("bcrypt-ish","Hash starts with $2b$12$ and is 60 chars"),
 ("markdown-table","| col | col2 | --- | a | b |"),
 ("emoji-title","Login works then logout \U0001F6AA"),
 ("sql","SELECT * FROM users WHERE id=31 AND name LIKE '%zebra%'"),
 ("semver","Upgrade from v1.2.3-rc.1+build.31 to v2.0.0"),
 ("file-path","Check C:"+BS+"Users"+BS+"test"+BS+"AppData"+BS+"Local"+BS+"app.log exists"),
 ("greek-word","\u0391\u03bb\u03c6\u03ac \u03b2\u03ae\u03c4\u03b1 \u03b3\u03ac\u03bc\u03bc\u03b1 quilt"),
 ("base64-ish-token","Paste eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc into the box"),
]
bad=[]
for i,(label,text) in enumerate(LEGIT):
    for where,payload in (("title",{"title":text,"case_class":"happy","step_action":"click","step_target":f"#go{i}","step_value":"","step_expected":"ok"}),
                          ("target+expected",{"title":f"case {label}","case_class":"happy","step_action":"fill","step_target":text,"step_value":f"x{i}","step_expected":text})):
        code,body=post("/projects/fp2/cases",payload)
        ok = code in (200,303) or "already has a case" in body
        flag = "OK      " if ok else "REFUSED!"
        guard = "looks like it contains a real credential" in body or "credential appears to be split" in body
        if not ok: bad.append((label,where,code,"GUARD" if guard else "other",body[:110]))
        print(f"  {flag} {label:18s} [{where:15s}] ({code}) {'<-- CREDENTIAL GUARD' if guard else ''}")
print("GUARD FALSE POSITIVES:", sum(1 for b in bad if b[3]=="GUARD"), "/ other refusals:", sum(1 for b in bad if b[3]!="GUARD"))
for b in bad: print("   ",b)
