"""Shared pytest fixtures. First conftest in this repo — added at Track B3,
which needs a real local site to crawl (a fake page cannot exercise
navigation, dialogs, or network failures).

`_NoCacheHandler` is imported from `scripts/regression_proof.py` rather than
redefined, following the import pattern `tests/test_regression_proof.py`
already uses — one no-cache handler in the repo, not two.
"""

from __future__ import annotations

import functools
import http.server
import sys
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from regression_proof import _NoCacheHandler


@pytest.fixture(scope="session")
def serve_dir() -> Iterator[Callable[[Path], str]]:
    """Serve a directory over HTTP on an ephemeral localhost port.

    Yields a factory: `base_url = serve_dir(some_directory)`. Every server
    started through it is shut down at teardown, so a test never leaks a
    thread or a port.
    """
    servers: list[http.server.ThreadingHTTPServer] = []

    def _serve(directory: Path) -> str:
        handler = functools.partial(_NoCacheHandler, directory=str(directory))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield _serve

    for server in servers:
        server.shutdown()
        server.server_close()

# -- the mutation instrument's synthetic project (C7) ------------------------
#
# Registered here rather than imported: importing a fixture shadows the test's
# own parameter name, which ruff flags as F811 on every use. Named
# `mutation_repo` rather than `repo` because conftest fixtures are visible to
# the whole suite and a bare `repo` is too generic to own globally.

from tests_mutation_fixtures import MODULE, TESTS  # noqa: E402


@pytest.fixture
def mutation_repo(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "mod.py").write_text(MODULE, encoding="utf-8")
    (tmp_path / "tests" / "test_mod.py").write_text(TESTS, encoding="utf-8")
    return tmp_path


def spec(**overrides) -> dict:
    mutation = {
        "name": "threshold broken", "file": "scripts/mod.py",
        "old": 'if value > 10:', "new": 'if value > 0:',
        "kills": ["test_small_values_are_small"],
    }
    mutation.update(overrides.pop("mutation", {}))
    return {"tests": "tests/test_mod.py", "mutations": [mutation], **overrides}
