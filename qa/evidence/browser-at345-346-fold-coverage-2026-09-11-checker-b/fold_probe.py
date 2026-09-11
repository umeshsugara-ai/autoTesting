"""Checker-authored probe: fold-level attack on fold_credential (AT-345/346)."""
import base64, binascii, unicodedata, sys
sys.path.insert(0, "D:/autoTesting/src")
from autotester.core.redact import fold_credential, Redactor

CRED = "ZEBRA_QUILT_APIKEY_31"
r = Redactor({"DEMO_PASSWORD": CRED})
print("folded stored:", r._folded)

def interleave(s, ch):
    return ch.join(s)

cases = {
  "base64": base64.b64encode(CRED.encode()).decode(),
  "base32": base64.b32encode(CRED.encode()).decode(),
  "hex": binascii.hexlify(CRED.encode()).decode(),
  "html-dec-entities": "".join(f"&#{ord(c)};" for c in CRED),
  "html-hex-entities": "".join(f"&#x{ord(c):X};" for c in CRED),
  "double-percent": "".join(f"%25{ord(c):02X}" for c in CRED),
  "rtl-reversed": "\u202e" + CRED[::-1],
  "rtl-reversed-rlm": "\u200f" + CRED[::-1] + "\u200e",
  "plain-reversed": CRED[::-1],
  "cgj-interleaved-U+034F": interleave(CRED, "\u034f"),
  "vs1-interleaved-U+FE00": interleave(CRED, "\ufe00"),
  "vs16-interleaved-U+FE0F": interleave(CRED, "\ufe0f"),
  "mongolian-fvs-U+180B": interleave(CRED, "\u180b"),
  "combining-joiner+zwsp": interleave(CRED, "\u034f\u200b"),
  "math-bold": CRED.translate({c: c - 0x41 + 0x1D400 for c in range(0x41, 0x5B)}),
  "math-sans": CRED.translate({c: c - 0x41 + 0x1D5A0 for c in range(0x41, 0x5B)}),
  "math-monospace": CRED.translate({c: c - 0x41 + 0x1D670 for c in range(0x41, 0x5B)}),
  "armenian-homoglyph": CRED.replace("O","\u0555").replace("Q","\u0562"),
  "cherokee-homoglyph": CRED.replace("A","\u13AA").replace("E","\u13AC").replace("Z","\u13C3"),
  "enclosed-alphanum": CRED.translate({c: c - 0x41 + 0x1F110 for c in range(0x41, 0x5B)}),
  "parenthesized-latin": CRED.translate({c: c - 0x41 + 0x1F110 for c in range(0x41,0x5B)}),
  "fullwidth-again": CRED.translate({c: c - 0x41 + 0xFF21 for c in range(0x41, 0x5B)}),
  "regional-indicator": CRED.translate({c: c - 0x41 + 0x1F1E6 for c in range(0x41, 0x5B)}),
  "combining-dot-below": interleave(CRED, "\u0323"),
  "zwj-U+200D": interleave(CRED, "\u200d"),
  "word-joiner-U+2060": interleave(CRED, "\u2060"),
  "soft-hyphen": interleave(CRED, "\u00ad"),
  "nbsp-interleaved": interleave(CRED, "\u00a0"),
  "hair-space": interleave(CRED, "\u200a"),
  "figure-space": interleave(CRED, "\u2007"),
  "ogham-space-U+1680": interleave(CRED, "\u1680"),
  "braille-blank-U+2800": interleave(CRED, "\u2800"),
  "hangul-filler-U+3164": interleave(CRED, "\u3164"),
  "khmer-viriam-U+17D2": interleave(CRED, "\u17d2"),
  "musical-U+1D173": interleave(CRED, "\U0001D173"),
}
for label, payload in sorted(cases.items()):
    caught = r.contains_folded(payload) or (not r.is_clean(payload))
    rendered_same = "".join(c for c in payload if unicodedata.combining(c) == 0 and unicodedata.category(c) not in ("Cf","Mn"))
    print(f"{'CAUGHT ' if caught else 'BYPASS!'} {label:26s} visible-chars={rendered_same!r}")
