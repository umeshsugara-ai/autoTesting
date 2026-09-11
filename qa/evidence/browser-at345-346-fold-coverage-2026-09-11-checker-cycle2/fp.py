import sys
sys.path.insert(0, "D:/autoTesting/src")
from autotester.core.redact import Redactor
CRED = "ZEBRA_QUILT_APIKEY_31"
r = Redactor({"DEMO_PASSWORD": CRED, "OTHER": "supersecretlongvalue99"})

legit = {
 "hindi-name": "\u0930\u093e\u091c\u0947\u0936 \u0915\u0941\u092e\u093e\u0930 \u0936\u0930\u094d\u092e\u093e",
 "hindi-zwnj": "\u0915\u094d\u200d\u0937 \u0939\u093f\u0902\u0926\u0940 \u092a\u0930\u0940\u0915\u094d\u0937\u0923",
 "arabic": "\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644 \u0625\u0644\u0649 \u0627\u0644\u0646\u0638\u0627\u0645",
 "arabic-shadda": "\u0645\u064f\u0634\u064e\u062f\u0651\u064e\u062f \u0627\u0644\u0646\u0651\u064e\u0635",
 "arabic-number-sign": "\u0600\u0661\u0662\u0663 \u0627\u062e\u062a\u0628\u0627\u0631",
 "thai": "\u0e17\u0e14\u0e2a\u0e2d\u0e1a\u0e23\u0e30\u0e1a\u0e1a\u0e40\u0e02\u0e49\u0e32\u0e2a\u0e39\u0e48\u0e23\u0e30\u0e1a\u0e1a",
 "hebrew": "\u05d1\u05d3\u05d9\u05e7\u05ea \u05db\u05e0\u05d9\u05e1\u05d4 \u05dc\u05de\u05e2\u05e8\u05db\u05ea",
 "hebrew-niqqud": "\u05d1\u05bc\u05b0\u05d3\u05b4\u05d9\u05e7\u05b8\u05d4",
 "emoji-plain": "Login flow \U0001f680 smoke test",
 "emoji-vs16": "Checkout \u2714\ufe0f works \u2764\ufe0f",
 "emoji-zwj-family": "Team \U0001f468\u200d\U0001f469\u200d\U0001f467 dashboard",
 "emoji-flag": "\U0001f1ee\U0001f1f3 India region case",
 "emoji-keycap": "Step 1\ufe0f\u20e3 then 2\ufe0f\u20e3",
 "korean": "\ub85c\uadf8\uc778 \ud14c\uc2a4\ud2b8",
 "khmer": "\u1780\u17b6\u179a\u1785\u17bc\u179b",
 "mongolian": "\u1826\u1828\u182d\u1820\u1828 \u180b\u1821",
 "accented": "Caf\u00e9 M\u00fcnchner Stra\u00dfe",
 "turkish": "\u0130stanbul I\u015f\u0131k giri\u015f",
 "css-selector": "div.card > ul:nth-child(3) [data-id='x']",
 "xpath": "//div[@class='a']/span[contains(text(),'b')]",
 "url": "https://a.test/p?q=1&r=2#frag",
 "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc-DEF_123",
 "regex": "^[A-Z]{3}-[0-9]{4}$",
 "semver": "v1.2.3-rc.1+build.31",
 "winpath": "C:" + chr(92) + "Users" + chr(92) + "x" + chr(92) + "AppData",
 "sql": "SELECT * FROM t WHERE n LIKE '%zebra%'",
 "zebra-word": "The zebra quilt is in the shop",
}
bad = []
for k, v in legit.items():
    refused = (not r.is_clean(v)) or r.contains_folded(v)
    if refused: bad.append(k)
    print(f"  {'REFUSED*' if refused else 'accepted'}  {k}")
print("\nFALSE POSITIVES:", bad or "none")
