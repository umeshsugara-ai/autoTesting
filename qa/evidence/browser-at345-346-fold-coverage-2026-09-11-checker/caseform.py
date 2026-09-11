"""Cycle-3 checker: the case-form door (U8) and the false-positive probe (#3).

Case form fields: title, case_class, step_action, step_target, step_value, step_expected.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8743"
CRED = "ZEBRA_QUILT_APIKEY_31"
RLO = chr(0x202E)


def post(path, fields):
    data = urllib.parse.urlencode(fields, doseq=True).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:160]


_N = [0]


def case(slug, *, title="a case", target=None, value="hello", expect="ok"):
    """Every call gets a UNIQUE target so AT-060's duplicate-content 400 can
    never be mistaken for a credential refusal."""
    _N[0] += 1
    target = target if target is not None else f"#user{_N[0]}"
    return post(f"/projects/{slug}/cases", {
        "title": title, "case_class": "happy", "step_action": ["fill"],
        "step_target": [target], "step_value": [value], "step_expected": [expect],
    })


def say(s):
    sys.stdout.write(s.encode("ascii", "backslashreplace").decode("ascii") + "\n")


def main():
    results = {"attacks": {}, "false_positives": {}}
    post("/onboard", {"slug": "seed", "name": "Seed", "base_url": "https://example.com/app",
                      "allowed_domains": "example.com"})

    reordered = RLO + CRED[::-1]
    stroke = chr(0x0335).join(CRED)
    attacks = {
        "RLO-reordered in title": dict(title=reordered),
        "RLO-reordered in step_value": dict(value=reordered),
        "RLO-reordered in step_expected": dict(expect=reordered),
        "RLO-reordered in step_target": dict(target=reordered),
        "comb-stroke in title": dict(title=stroke),
        "comb-stroke in step_value": dict(value=stroke),
        "NUL in title (AT-353 control)": dict(title=chr(0).join(CRED)),
        "plain credential in title (control)": dict(title=CRED),
    }
    for label, kw in attacks.items():
        code, body = case("seed", **kw)
        verdict = "REFUSED" if code == 400 else "ACCEPTED-to-disk"
        results["attacks"][label] = {"status": code, "verdict": verdict, "body": body}
        say(f"{verdict:18s} {label:38s} HTTP {code}  {body[:90]}")

    say("")
    fps = {
        "expect with a real newline": dict(expect="line one\nline two\nline three"),
        "expect with a real tab": dict(expect="col1\tcol2\tcol3"),
        "expect multi-line + tabs": dict(expect="Given a user\n\tWhen they log in\n\tThen ok"),
        "expect with CRLF": dict(expect="first\r\nsecond"),
        "title with emoji + U+FE0F": dict(title="Checkout ✔️ flow"),
        "title with emoji ZWJ family": dict(title="Team \U0001f468‍\U0001f469‍\U0001f467 case"),
        "title with keycap 1️⃣": dict(title="Step 1️⃣ of onboarding"),
        "title Hindi": dict(title="परीक्षण मामला"),
        "title Arabic with shadda": dict(title="تسجيل الدُّخول"),
        "value with accented Latin": dict(value="Café naïve résumé"),
        "expect with Thai": dict(expect="การทดสอบ"),
    }
    for i, (label, kw) in enumerate(fps.items()):
        kw.setdefault("title", f"fp case {i}")
        code, body = case("seed", **kw)
        ok = code in (200, 303)
        tag = "ACCEPTED" if ok else "REFUSED"
        results["false_positives"][label] = {"status": code, "accepted": ok, "body": body}
        say(f"{tag:10s} {label:34s} HTTP {code}  {body[:110]}")

    out = sys.argv[1] if len(sys.argv) > 1 else "caseform-results.json"
    json.dump(results, open(out, "w"), indent=2)


if __name__ == "__main__":
    main()
