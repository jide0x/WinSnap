from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path_str: str) -> Dict[str, Any]:
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
        meta["exists"] = True
        meta["size"] = stat.st_size
        try:
            meta["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        except Exception:
            meta["modified_at"] = None
        try:
            meta["sha256"] = sha256_file(path)
            meta["hash_status"] = "success"
        except PermissionError:
            meta["hash_status"] = "access_denied"
        except Exception:
            meta["hash_status"] = "error"
    except PermissionError:
        meta["hash_status"] = "access_denied"
    except Exception:
        meta["hash_status"] = "error"
    return meta
