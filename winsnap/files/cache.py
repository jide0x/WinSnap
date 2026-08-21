from __future__ import annotations

import json
import os
from typing import Any, Dict

from winsnap.snapshot_store import SNAPSHOT_DIR, ensure_snapshot_dir


CACHE_VERSION = 1
CACHE_FILENAME = ".hashcache.json"


def cache_key(path: str) -> str:
    """Canonical key for a path: normalised case and separators."""
    return os.path.normcase(os.path.normpath(path))


def cache_path():
    return SNAPSHOT_DIR / CACHE_FILENAME


def load_cache() -> Dict[str, Dict[str, Any]]:
    """Load the on-disk hash cache, or {} if missing/corrupt/version-mismatched."""
    path = cache_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return {}
    entries = data.get("entries")
    return entries if isinstance(entries, dict) else {}


def save_cache(entries: Dict[str, Dict[str, Any]]) -> None:
    """Persist the cache atomically (write temp, then replace)."""
    ensure_snapshot_dir()
    payload = {"version": CACHE_VERSION, "entries": entries}
    path = cache_path()
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)
