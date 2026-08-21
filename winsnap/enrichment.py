from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from winsnap.files import file_metadata, verify_signatures_bulk
from winsnap.files.cache import cache_key
from winsnap.files.resolve import (
    resolve_executable_from_autorun,
    resolve_executable_from_firewall_rule,
    resolve_executable_from_process,
    resolve_executable_from_service,
    resolve_executable_from_startup_item,
    resolve_executable_from_task,
)


# Map artifact key -> resolver that extracts the referenced executable path from one item
RESOLVERS: Dict[str, Any] = {
    "processes": resolve_executable_from_process,
    "services": resolve_executable_from_service,
    "scheduled_tasks": resolve_executable_from_task,
    "registry_autoruns": resolve_executable_from_autorun,
    "startup_folders": resolve_executable_from_startup_item,
    "firewall_rules": resolve_executable_from_firewall_rule,
}


def discover_referenced_paths(snapshot: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], str]]:
    """Extract (artifact_key, item, path) for every resolvable executable reference."""
    discovered: List[Tuple[str, Dict[str, Any], str]] = []
    for key, resolver in RESOLVERS.items():
        for item in snapshot.get(key, []) or []:
            try:
                path = resolver(item)
            except Exception:
                path = None
            if path:
                discovered.append((key, item, str(path)))
    return discovered


def dedupe_paths(discovered: List[Tuple[str, Dict[str, Any], str]]) -> List[str]:
    """Return ordered unique paths in first-seen order."""
    seen = set()
    unique: List[str] = []
    for _, _, path in discovered:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def enrich_unique_paths(
    paths: List[str],
    no_hash: bool = False,
    no_signature: bool = False,
    workers: int = 0,
    cache: Dict[str, Any] = None,
    timings: Dict[str, Any] = None,
) -> Dict[str, Dict[str, Any]]:
    """Hash, verify signature, and collect metadata for each unique path.

    Returns a mapping {path: metadata}; paths skipped under no_hash are omitted.
    Hashing runs in parallel; signatures are verified in a single native call.
    When `cache` is provided, unchanged files reuse cached hashes/signatures.
    When `timings` is provided, it is populated with `hash_ms` and `signature_ms`.
    """
    if not paths:
        if timings is not None:
            timings["hash_ms"] = 0
            timings["signature_ms"] = 0
        return {}

    max_workers = workers if isinstance(workers, int) and workers > 0 else min(4, len(paths) or 1)

    # Phase 1: hash + metadata for each unique path (Python, I/O bound)
    hash_start = time.perf_counter()
    hashed: Dict[str, Dict[str, Any]] = {}
    if not no_hash:
        if max_workers == 1:
            for path in paths:
                meta = file_metadata(path, cache)
                hashed[meta["path"]] = meta
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(file_metadata, path, cache) for path in paths]
                for future in as_completed(futures):
                    meta = future.result()
                    hashed[meta["path"]] = meta
    if timings is not None:
        timings["hash_ms"] = int((time.perf_counter() - hash_start) * 1000)

    # Phase 2: signature verification via native WinVerifyTrust. Only
    # successfully hashed files are checked, deduplicated by sha256 (identical
    # content via different paths is verified once). WinVerifyTrust is I/O
    # bound and releases the GIL, so the unique paths are split into chunks
    # verified concurrently. Cached signatures are reused without re-verifying.
    sig_start = time.perf_counter()
    signatures_by_sha: Dict[str, Dict[str, Any]] = {}
    if not no_signature:
        sha_to_path: Dict[str, str] = {}
        for path, meta in hashed.items():
            sha = meta.get("sha256")
            if sha and sha not in sha_to_path:
                sha_to_path[sha] = path

        to_verify: List[str] = []
        for sha, path in sha_to_path.items():
            cached_sig = _cached_signature(cache, path)
            if cached_sig is not None:
                signatures_by_sha[sha] = cached_sig
            else:
                to_verify.append(path)

        if to_verify:
            bulk = _verify_signatures(to_verify, max_workers)
            for sha, path in sha_to_path.items():
                if sha in signatures_by_sha:
                    continue
                sig = bulk.get(path)
                signatures_by_sha[sha] = sig
                if cache is not None and sig is not None:
                    cache.setdefault(cache_key(path), {})["signature"] = sig

    if timings is not None:
        timings["signature_ms"] = int((time.perf_counter() - sig_start) * 1000)

    enriched: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        meta = hashed.get(path)
        if meta is None:
            continue
        meta_with_sig = dict(meta)
        meta_with_sig["signature"] = signatures_by_sha.get(meta.get("sha256"))
        enriched[path] = meta_with_sig
    return enriched


def _cached_signature(cache, path: str):
    if cache is None:
        return None
    entry = cache.get(cache_key(path))
    if isinstance(entry, dict):
        sig = entry.get("signature")
        if isinstance(sig, dict):
            return sig
    return None


def _verify_signatures(paths: List[str], workers: int) -> Dict[str, Dict[str, Any]]:
    """Verify signatures for `paths`, chunked across parallel workers.

    Each call to verify_signatures_bulk is a native WinVerifyTrust loop that
    releases the GIL while reading/verifying files, so splitting across threads
    hides disk latency.
    """
    if not paths:
        return {}
    if workers <= 1 or len(paths) <= 1:
        return verify_signatures_bulk(paths)

    chunk_size = max(1, (len(paths) + workers - 1) // workers)
    chunks = [paths[i:i + chunk_size] for i in range(0, len(paths), chunk_size)]
    merged: Dict[str, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(verify_signatures_bulk, chunk) for chunk in chunks]
        for future in as_completed(futures):
            merged.update(future.result())
    return merged


def attach_file_metadata(
    discovered: List[Tuple[str, Dict[str, Any], str]],
    enriched: Dict[str, Dict[str, Any]],
) -> None:
    """Attach each item's file metadata in-place."""
    for _, item, path in discovered:
        meta = enriched.get(path)
        if meta is not None:
            item["file"] = meta


def enrich_snapshot(
    snapshot: Dict[str, Any],
    no_hash: bool = False,
    no_signature: bool = False,
    workers: int = 0,
    cache: Dict[str, Any] = None,
    timings: Dict[str, Any] = None,
) -> None:
    """Full pipeline: discover referenced paths, dedupe, enrich, attach back.

    When `timings` is provided, it is populated with `path_resolution_ms`,
    `hash_ms`, and `signature_ms`.
    """
    resolve_start = time.perf_counter()
    discovered = discover_referenced_paths(snapshot)
    unique_paths = dedupe_paths(discovered)
    if timings is not None:
        timings["path_resolution_ms"] = int((time.perf_counter() - resolve_start) * 1000)
    enriched = enrich_unique_paths(
        unique_paths,
        no_hash=no_hash,
        no_signature=no_signature,
        workers=workers,
        cache=cache,
        timings=timings,
    )
    attach_file_metadata(discovered, enriched)
