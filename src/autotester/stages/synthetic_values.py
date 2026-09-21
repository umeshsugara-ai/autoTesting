"""The synthetic value generator (X10-b, D-029): what the crawler types.

One job: produce a fixed, non-PII, deterministic value for a form field, so a
crawl's typed runs are reproducible and never carry a real person's data. The
VALUE is derived only from what the DOM already told the crawler (the element's
own name/label/selector) — X12's determinism extends to what is typed: no
provider, no randomness, no clock.

Non-PII by construction: every value is an obvious fake ("autotester-…",
"Example College"), never a real-looking person's name, address or phone.
"""

from __future__ import annotations

import hashlib

_FAKE_DOMAIN = "autotester.invalid"
_WORD = "AutoTester"


def _seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def synthetic_value(el_name: str, el_selector: str, role: str) -> str:
    """One deterministic fake value for one element.

    The field's own identity (name, selector, role) is the whole input, so the
    same field always yields the same value within a run and across runs —
    a typed crawl can be replayed and diffed (X12's determinism extends here).
    """
    label = f"{el_name} {el_selector}".lower()
    n = _seed(el_name, el_selector, role)
    if role == "combobox":
        # The caller selects a real option; this value is only a fallback.
        return ""
    if any(k in label for k in ("email", "mail")):
        return f"autotester-{n}@{_FAKE_DOMAIN}"
    if any(k in label for k in ("search", "query", "filter", "find", "keyword")):
        return f"{_WORD} search {n % 1000}"
    if any(k in label for k in ("date", "day", "dob", "birth")):
        return "2026-01-01"
    if any(k in label for k in ("number", "num", "count", "age", "phone",
                                "mobile", "phone_no", "pin", "zip")):
        return str(1000 + n % 9000)
    if any(k in label for k in ("url", "link", "website", "site")):
        return f"https://{_FAKE_DOMAIN}/{n % 1000}"
    if any(k in label for k in ("name", "title", "college", "university", "school",
                                "institute", "organization", "company")):
        return f"{_WORD} College {n % 1000}"
    if any(k in label for k in ("city", "town", "state", "country", "location",
                                "address")):
        return f"{_WORD} City"
    if any(k in label for k in ("comment", "message", "note", "feedback", "description",
                                "remark", "reason")):
        return f"{_WORD} automated check {n % 1000}."
    return f"{_WORD}-{n % 100000}"