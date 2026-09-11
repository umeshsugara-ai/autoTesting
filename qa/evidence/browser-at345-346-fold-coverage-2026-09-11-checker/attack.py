"""Cycle-3 checker attack: does the guard still let a live credential reach disk?

Bound to d:/autoTesting. Runs against THIS checker's own uvicorn on a scratch
AUTOTESTER_ROOT outside the repo, whose .env holds DEMO_PASSWORD=ZEBRA_QUILT_APIKEY_31.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8743"
CRED = "ZEBRA_QUILT_APIKEY_31"


def post(path, fields):
    data = urllib.parse.urlencode(fields, doseq=True).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode("utf-8", "replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


def ilv(cp):
    return chr(cp).join(CRED)


SPELLINGS = {
    "control-plain-credential": CRED,
    "U+0000 NUL (AT-353)": ilv(0x0000),
    "U+001B ESC": ilv(0x001B),
    "U+200B ZWSP (AT-345)": ilv(0x200B),
    "U+034F CGJ (AT-351)": ilv(0x034F),
    "U+2800 BRAILLE BLANK": ilv(0x2800),
    "U+E000 PUA": ilv(0xE000),
    "U+F8FF PUA end": ilv(0xF8FF),
    "U+100000 PUA plane 16": ilv(0x100000),
    "U+0378 unassigned (Cn)": ilv(0x0378),
    "U+05EB unassigned (Cn)": ilv(0x05EB),
    "U+FDD0 noncharacter": ilv(0xFDD0),
    "U+FFFE noncharacter": ilv(0xFFFE),
    "U+0301 combining acute (visible Mn)": ilv(0x0301),
    "U+0335 combining short stroke": ilv(0x0335),
    "U+20E0 combining enclosing": ilv(0x20E0),
    "U+A4A0 (So)": ilv(0xA4A0),
    "U+1D159 musical null notehead": ilv(0x1D159),
    "U+202E RLO then reversed": chr(0x202E) + CRED[::-1],
    "U+2066 LRI isolate": ilv(0x2066),
}


def main():
    results = {}
    for i, (label, spelled) in enumerate(SPELLINGS.items()):
        slug = f"atk{i}"
        code, _body = post("/onboard", {
            "slug": slug, "name": spelled, "base_url": "https://example.com/app",
            "allowed_domains": "example.com",
        })
        verdict = "REFUSED" if code == 400 else (
            "ACCEPTED-to-disk" if code in (200, 303) else f"unexpected-{code}")
        results[label] = {"slug": slug, "status": code, "verdict": verdict}
        print(f"{verdict:18s} {label:38s} HTTP {code}")
    out = sys.argv[1] if len(sys.argv) > 1 else "attack-results.json"
    json.dump(results, open(out, "w"), indent=2)


if __name__ == "__main__":
    main()
