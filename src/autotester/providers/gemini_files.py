"""Upload a video to the Files API and wait until the service can actually read it.

The SDK's `files.upload` returns as soon as the bytes are accepted, while the
file is still `PROCESSING`. Passing that handle straight to `generate_content`
fails — sometimes immediately, sometimes as an empty reading that looks like the
model simply saw nothing, which is the worse outcome because it is
indistinguishable from a bad prompt. So the wait is not an optimisation; it is
the difference between an error and a plausible wrong answer.

Uploads are cached: the Files API keeps a file for ~48h, and re-uploading a 200MB
recording for every prompt in an ensemble is the single most expensive avoidable
thing this pipeline can do.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from autotester.core.ids import file_sha256
from autotester.providers.base import ProviderError

ACTIVE = "ACTIVE"
FAILED = "FAILED"
CACHE_TTL_S = 46 * 3600
"""Below the service's ~48h retention, so a cache hit is never a dead handle."""


def _state_of(file_obj: Any) -> str:
    state = getattr(file_obj, "state", None)
    return str(getattr(state, "name", state) or "")


def _load_cache(cache_path: Path) -> dict[str, Any]:
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _remember(cache_path: Path, key: str, name: str) -> None:
    cache = _load_cache(cache_path)
    cache[key] = {"name": name, "at": time.time()}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cached_name(cache_path: Path, key: str) -> str | None:
    entry = _load_cache(cache_path).get(key)
    if not isinstance(entry, dict):
        return None
    if time.time() - float(entry.get("at", 0)) > CACHE_TTL_S:
        return None
    name = entry.get("name")
    return str(name) if name else None


def _cache_key(path: Path) -> str:
    """Content, not size (AT-128).

    The first version keyed on `resolve()::st_size`, which makes a recording
    re-exported in place at the same byte size a cache HIT — serving the OLD
    video under the new file's name, and producing a confident reading of
    footage nobody asked about. `core.ids.file_sha256` was two modules away."""
    return f"{path.resolve()}::{file_sha256(path)}"


def upload_and_wait(client: Any, path: Path, *, cache_path: Path | None = None,
                    timeout_s: float = 600.0, poll_s: float = 2.0,
                    clock: Any = time.monotonic, sleep: Any = time.sleep) -> Any:
    """Upload `path`, poll until ACTIVE, and return the file handle.

    `clock` and `sleep` are injected so the timeout is testable without one."""
    key = _cache_key(path)
    if cache_path is not None and (name := _cached_name(cache_path, key)):
        try:
            cached = client.files.get(name=name)
            if _state_of(cached) == ACTIVE:
                return cached
        except Exception:  # a dead handle is a cache miss, not an error
            pass

    try:
        file_obj = client.files.upload(file=str(path))
    except Exception as exc:  # every SDK failure is a ProviderError (I9)
        raise ProviderError(f"upload of {path.name} failed: {type(exc).__name__}: {exc}") from exc

    started = clock()
    while _state_of(file_obj) not in (ACTIVE, FAILED):
        if clock() - started > timeout_s:
            raise ProviderError(
                f"{path.name} was still {_state_of(file_obj) or 'PROCESSING'} after "
                f"{timeout_s:.0f}s — the Files API never made it readable")
        sleep(poll_s)
        try:
            file_obj = client.files.get(name=file_obj.name)
        except Exception as exc:
            raise ProviderError(
                f"polling {path.name} failed: {type(exc).__name__}: {exc}") from exc

    if _state_of(file_obj) == FAILED:
        raise ProviderError(f"the service could not process {path.name} (state FAILED)")

    if cache_path is not None:
        _remember(cache_path, key, str(file_obj.name))
    return file_obj
