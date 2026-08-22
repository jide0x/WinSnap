from datetime import datetime
import getpass
import platform
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from winsnap.artifacts import ARTIFACTS, SUPPORTED_COLLECTORS
from winsnap.enrichment import EnrichStats, enrich_snapshot
from winsnap.files.cache import load_cache, save_cache
from winsnap.snapshot_store import delete_snapshot, list_snapshots, load_snapshot, save_snapshot, snapshot_path
from winsnap.version import VERSION
from winsnap.views.snapshot_view import print_snapshot_list, print_snapshot_summary
from winsnap.views.ui import success, warning, bold
import time


# Profiles define which artifacts to collect (in stable order defined by ARTIFACTS)
PROFILE_KEYS = {
    "full": [a.key for a in ARTIFACTS],
    "core": [
        "processes",
        "services",
        "scheduled_tasks",
        "registry_autoruns",
        "startup_folders",
        "local_users",
        "local_groups",
    ],
}


def create_snapshot(name, note="", profile="full", no_hash=False, no_signature=False, workers=0, timings=False, retries=1, timeout_factor=1.0, cache=False):
    if snapshot_path(name).exists():
        print(warning(f'Snapshot "{name}" already exists.'))
        print()
        print("Overwrite?")
        print()
        response = input("[y/N] ").strip().lower()
        if response != "y":
            print(warning("Snapshot not overwritten."))
            return

    # Select artifacts according to profile, preserving ARTIFACTS order
    total_start = time.perf_counter()
    selected_keys = PROFILE_KEYS.get(profile, PROFILE_KEYS["full"]) if PROFILE_KEYS else [a.key for a in ARTIFACTS]
    selected = [a for a in ARTIFACTS if a.key in selected_keys]

    snapshot = {
        "schema_version": 1,
        "winsnap_version": VERSION,
        "snapshot_id": str(uuid.uuid4()),
        "name": name,
        "version": VERSION,
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "windows_version": platform.platform(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        # Write the new plural key going forward; views/readers tolerate older 'collector'
        "collectors": [artifact.key for artifact in selected],
        "note": note,
    }

    # Collect in parallel to reduce wall-clock time. On error, store empty list.
    def run_collect(artifact):
        start = time.perf_counter()
        attempt = 0
        last_exc = None
        while attempt < max(1, retries):
            try:
                items = artifact.collect()
                duration = int((time.perf_counter() - start) * 1000)
                status = {
                    "status": "success",
                    "count": len(items) if isinstance(items, list) else 0,
                    "duration_ms": duration,
                }
                return artifact.key, items, status
            except Exception as e:
                last_exc = e
                attempt += 1
        duration = int((time.perf_counter() - start) * 1000)
        print(warning(f"Collector failed after {attempt} attempt(s): {artifact.label}: {last_exc}"))
        status = {
            "status": "failed",
            "count": 0,
            "duration_ms": duration,
            "error": str(last_exc),
        }
        return artifact.key, [], status

    collector_status = {}
    max_workers = workers if isinstance(workers, int) and workers > 0 else (min(4, len(selected)) or 1)
    # Propagate timeout factor to PowerShell runner via env var
    import os as _os
    _os.environ["WINSNAP_TIMEOUT_FACTOR"] = str(timeout_factor)

    collect_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_collect, artifact): artifact for artifact in selected}
        for future in as_completed(futures):
            key, items, status = future.result()
            snapshot[key] = items
            collector_status[key] = status
    collection_wall_ms = int((time.perf_counter() - collect_start) * 1000)

    snapshot["collector_status"] = collector_status

    # Enrichment pipeline: discover referenced executables, dedupe paths,
    # then hash/verify signatures on the unique set (in parallel) and attach back.
    # Caching only applies when hashing is enabled (nothing to cache otherwise).
    cache_entries = None
    cache_load_ms = 0
    if cache and not no_hash:
        load_start = time.perf_counter()
        cache_entries = load_cache()
        cache_load_ms = int((time.perf_counter() - load_start) * 1000)

    stats = EnrichStats() if timings else None
    enrich_snapshot(snapshot, no_hash=no_hash, no_signature=no_signature, workers=workers, cache=cache_entries, stats=stats)

    cache_save_ms = 0
    if cache_entries is not None:
        save_start = time.perf_counter()
        save_cache(cache_entries)
        cache_save_ms = int((time.perf_counter() - save_start) * 1000)

    # Record legacy singular key for backward compatibility if someone inspects raw JSON with old tools
    snapshot["collector"] = snapshot.get("collectors", [])

    output_timings = {} if timings else None
    output_start = time.perf_counter()
    save_snapshot(snapshot, timings=output_timings)
    output_wall_ms = int((time.perf_counter() - output_start) * 1000)
    print_snapshot_summary(snapshot)

    # Optional timings summary
    if timings:
        def _ms(key):
            return stats.timings.get(key, 0)

        def _cnt(key):
            return stats.counters.get(key, 0)

        print(bold("Collection"))
        for a in selected:
            st = collector_status.get(a.key, {})
            status_text = st.get("status", "unknown")
            dur = st.get("duration_ms", 0)
            cnt = st.get("count", 0)
            line = f"  {a.label:<22} {status_text:<8} {cnt:>5} items  {dur:>6} ms"
            print(line)
        print(f"  {'Collection wall clock':<22} {collection_wall_ms:>8} ms")

        print()
        print(bold("Enrichment"))
        print(f"  {'Cache load':<22} {cache_load_ms:>8} ms")
        print(f"  {'Path resolution':<22} {_ms('path_resolution_ms'):>8} ms")
        print(f"  {'Cache lookup':<22} {_ms('cache_lookup_ms'):>8} ms")
        print(f"  {'SHA-256 hashing':<22} {_ms('hash_ms'):>8} ms")
        print(f"  {'Signature checks':<22} {_ms('signature_ms'):>8} ms")
        print(f"  {'Enrichment wall clock':<22} {_ms('enrichment_wall_ms'):>8} ms")
        print()
        print(f"  {'Refs discovered':<22} {_cnt('refs_discovered'):>8}")
        print(f"  {'Unique paths':<22} {_cnt('unique_paths'):>8}")
        print(f"  {'Hash cache hits':<22} {_cnt('hash_cache_hits'):>8}")
        print(f"  {'Hash cache misses':<22} {_cnt('hash_cache_misses'):>8}")
        print(f"  {'Files hashed':<22} {_cnt('files_hashed'):>8}")
        print(f"  {'Signature cache hits':<22} {_cnt('sig_cache_hits'):>8}")
        print(f"  {'Signature cache misses':<22} {_cnt('sig_cache_misses'):>8}")
        print(f"  {'Files verified':<22} {_cnt('files_verified'):>8}")

        print()
        print(bold("Output"))
        print(f"  {'Cache save':<22} {cache_save_ms:>8} ms")
        print(f"  {'JSON encoding':<22} {output_timings.get('json_encode_ms', 0):>8} ms")
        print(f"  {'File save':<22} {output_timings.get('file_write_ms', 0):>8} ms")
        print(f"  {'Output wall clock':<22} {output_wall_ms:>8} ms")

        print()
        print(bold("Total"))
        total_ms = int((time.perf_counter() - total_start) * 1000)
        print(f"  {'Total':<22} {total_ms:>8} ms")


def show_snapshot(name):
    snapshot = load_snapshot(name)
    print_snapshot_summary(snapshot)


def list_all_snapshots():
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]
    print_snapshot_list(snapshots)


def remove_snapshot(name):
    delete_snapshot(name)
    print(success(f"Deleted snapshot: {name}"))
