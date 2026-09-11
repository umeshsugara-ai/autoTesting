"""One question: does the credential guard see through UNICODE spelling?

Separate from `test_ui_credential_transforms.py`, which asks the same thing
about ASCII-shaped substitutions, because these fail for a different reason and
are fixed in different lines of `fold_credential`: normalisation, not
punctuation.

Every case here was live-reproduced by a checker against its own server before
the fix (AT-345). The zero-width one is the worst thing found in this whole
credential thread: U+200B has no width, so a project name interleaved with it
RENDERS as the exact credential on the home index -- a human reading the page
sees the secret, while every byte-comparison in the system says it is a
different string.

The last test is the cost side. Normalising harder and stripping format
characters makes the guard match MORE strings, so ordinary non-ASCII input must
still get through.

Contract: qa/contracts/ui.md U8/U9.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.ui.app import app

UPPER_CREDENTIAL = "ZEBRA_QUILT_APIKEY_31"
ZERO_WIDTH = "\u200b"

UNICODE_TRANSFORMS = {
    "zero-width-interleaved": ZERO_WIDTH.join(UPPER_CREDENTIAL),
    "full-width-latin": UPPER_CREDENTIAL.translate(
        {c: c - 0x41 + 0xFF21 for c in range(0x41, 0x5B)}),
    "turkish-dotless-i": UPPER_CREDENTIAL.replace("I", "\u0131"),
}

@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

def _project_with_credential(client: TestClient, scratch_root: Path, *, value: str = "") -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/demo/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })
    if value:
        env_line = "DEMO_PASSWORD=" + value + chr(10)
        (scratch_root / ".env").write_text(env_line, encoding="utf-8")

def _seed(client: TestClient, scratch_root: Path, slug: str) -> None:
    (scratch_root / ".env").write_text(
        f"DEMO_PASSWORD={UPPER_CREDENTIAL}\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": slug, "name": slug.title(), "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    client.post(f"/projects/{slug}/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })

@pytest.mark.parametrize("label", sorted(UNICODE_TRANSFORMS))
def test_a_unicode_spelling_of_a_credential_is_refused(
    client: TestClient, scratch_root: Path, label: str
) -> None:
    _seed(client, scratch_root, "seedu1")

    response = client.post("/onboard", data={
        "slug": "leaky-" + label, "name": UNICODE_TRANSFORMS[label],
        "base_url": "https://demo.test", "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 400, f"{label} was accepted"
    assert not (scratch_root / "projects" / ("leaky-" + label)).exists()

def test_the_kelvin_sign_stays_caught(client: TestClient, scratch_root: Path) -> None:
    """A regression pin, not a new catch: U+212A already folded correctly via
    `casefold` before AT-345. Adding NFKC could plausibly have reordered the
    steps and lost it."""
    _seed(client, scratch_root, "seedk")

    response = client.post("/onboard", data={
        "slug": "leaky-kelvin", "name": UPPER_CREDENTIAL.replace("K", "\u212a"),
        "base_url": "https://demo.test", "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 400

def test_ordinary_unicode_text_is_still_accepted(
    client: TestClient, scratch_root: Path
) -> None:
    """The cost side of widening: an accented name, a CJK title, a Greek letter
    next to a `+` must all still get through."""
    _seed(client, scratch_root, "seedu2")

    for index, name in enumerate(("Caf\u00e9 M\u00fcnchner Stra\u00dfe",
                                  "\u65e5\u672c\u8a9e\u306e\u30d7\u30ed\u30b8\u30a7\u30af\u30c8",
                                  "\u03a9mega + Sigma")):
        response = client.post("/onboard", data={
            "slug": f"ok-{index}", "name": name,
            "base_url": "https://demo.test", "allowed_domains": "demo.test",
        }, follow_redirects=False)
        assert response.status_code in (200, 303), f"{name!r}: {response.text[:200]}"

def test_format_characters_are_stripped_before_normalising(
    client: TestClient, scratch_root: Path
) -> None:
    """The ORDER inside `fold_credential`, pinned rather than asserted in prose.

    A zero-width space between a base letter and its combining mark blocks NFKC
    from composing them. Measured: for `e` + U+200B + U+0301, strip-then-NFKC
    yields U+00E9, while NFKC-then-strip leaves `e` followed by a bare
    combining acute -- a different string, which then fails to match the stored
    credential. So a credential containing an accented character can be spelled
    past the guard by anyone who gets the order wrong."""
    accented = "CAF\u00c9_QUILT_APIKEY_31"
    (scratch_root / ".env").write_text(
        f"DEMO_PASSWORD={accented}\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "seedord", "name": "Seedord", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/seedord/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })

    # the same value, with E + ZWSP + combining acute in place of the composed E-acute
    spelled = accented.replace("\u00c9", "E\u200b\u0301")
    response = client.post("/onboard", data={
        "slug": "leaky-order", "name": spelled,
        "base_url": "https://demo.test", "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 400
    assert not (scratch_root / "projects" / "leaky-order").exists()
