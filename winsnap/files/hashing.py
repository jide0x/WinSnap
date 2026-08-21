from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from winsnap.files.cache import cache_key


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path_str: str, cache: Dict[str, Any] = None) -> Dict[str, Any]:
    """Collect file metadata (size, mtime, sha256).

    When `cache` is provided, a file whose size and mtime are unchanged from the
    cached entry reuses the cached hash instead of re-reading the file.
    """
    meta: Dict[str, Any] = {
        "path": path_str,
        "exists": False,
        "sha256": None,
        "size": None,
        "modified_at": None,
        "hash_status": None,
    }
    try:
        path = Path(path_str)
    except Exception:
        meta["hash_status"] = "unsupported_path"
        return meta

    try:
        if not path.exists():
            meta["hash_status"] = "missing"
            return meta
        if not path.is_file():
            meta["hash_status"] = "not_a_file"
            return meta
        stat = path.stat()
        size = stat.st_size
        mtime_ns = stat.st_mtime_ns
        try:
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        except Exception:
            modified_at = None

        key = cache_key(path_str)

        # Cache hit: reuse the previous hash if size and mtime are unchanged.
        if cache is not None:
            entry = cache.get(key)
            if (
                isinstance(entry, dict)
                and entry.get("size") == size
                and entry.get("mtime_ns") == mtime_ns
                and entry.get("sha256")
            ):
                meta["exists"] = True
                meta["size"] = entry.get("size")
                meta["modified_at"] = entry.get("modified_at")
                meta["sha256"] = entry.get("sha256")
                meta["hash_status"] = entry.get("hash_status") or "success"
                return meta

        meta["exists"] = True
        meta["size"] = size
        meta["modified_at"] = modified_at
        try:
            meta["sha256"] = sha256_file(path)
            meta["hash_status"] = "success"
        except PermissionError:
            meta["hash_status"] = "access_denied"
        except Exception:
            meta["hash_status"] = "error"

        if cache is not None:
            entry = cache.get(key)
            if not isinstance(entry, dict):
                entry = {}
            entry["size"] = size
            entry["mtime_ns"] = mtime_ns
            entry["sha256"] = meta["sha256"]
            entry["modified_at"] = modified_at
            entry["hash_status"] = meta["hash_status"]
            entry["signature"] = None
            cache[key] = entry
    except PermissionError:
        meta["hash_status"] = "access_denied"
    except Exception:
        meta["hash_status"] = "error"
    return meta
