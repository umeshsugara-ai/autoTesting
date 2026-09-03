"""Pure-logic pieces of scripts/regression_proof.py. Contract:
qa/contracts/regression-proof.md. The actual proof (a real headed browser
against a real local fixture server, a real judge, a real regression injected
and reverted) is not a live-network-independent unit test by nature -- see
qa/manifests/t110-regression-proof.md for that real run's cited evidence.
These tests cover the parts that don't need a browser or a live judge call.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import regression_proof as rp

from autotester.schema.enums import Action, CaseKind

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "regression_site"


def test_fixture_files_exist() -> None:
    assert (FIXTURE_DIR / "index.html").exists()
    assert (FIXTURE_DIR / "login.html").exists()
    assert (FIXTURE_DIR / "login.broken.html").exists()


def test_good_fixture_checks_the_real_password() -> None:
    text = (FIXTURE_DIR / "login.html").read_text(encoding="utf-8")
    assert "pass123" in text


def test_broken_fixture_checks_a_different_password() -> None:
    good = (FIXTURE_DIR / "login.html").read_text(encoding="utf-8")
    broken = (FIXTURE_DIR / "login.broken.html").read_text(encoding="utf-8")
    assert "password === 'pass123'" in good
    assert "password === 'pass124'" in broken
    assert "password === 'pass123'" not in broken


def test_build_cases_returns_login_and_homepage() -> None:
    cases = rp.build_cases("regression-demo", "http://127.0.0.1:9")
    assert len(cases) == 2
    assert cases[0].kind is CaseKind.BEST
    assert cases[1].kind is CaseKind.BEST
    login_targets = [s.target for s in cases[0].steps]
    assert any("login.html" in t for t in login_targets)
    assert any(s.action is Action.FILL for s in cases[0].steps)


def test_make_rubric_uses_a_stable_short_criterion_id() -> None:
    """A prior real run showed the judge sometimes invents a criterion id
    (e.g. "login_success_text") instead of using a generic one like "text" --
    grade.py's self-consistency check correctly downgraded that to
    INCONCLUSIVE. A short, explicitly-pinned id ("c1") with an instruction to
    use it exactly reduced this to zero across repeated real runs."""
    case = rp.build_cases("regression-demo", "http://127.0.0.1:9")[0]
    rubric = rp.make_rubric(case, "Login successful")
    assert rubric.criteria[0].id == "c1"
    assert "c1" in rubric.criteria[0].text


def test_no_cache_handler_overrides_end_headers() -> None:
    """A prior real run showed the persistent browser profile served a stale,
    cached login.html on the AFTER run even after the file changed on disk --
    a plain http.server sends no cache-control headers at all. This handler
    exists specifically to defeat that."""
    import http.server

    assert issubclass(rp._NoCacheHandler, http.server.SimpleHTTPRequestHandler)
    assert rp._NoCacheHandler.end_headers is not http.server.SimpleHTTPRequestHandler.end_headers
