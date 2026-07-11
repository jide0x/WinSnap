from datetime import datetime
import getpass
import platform
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from winsnap.artifacts import ARTIFACTS
from winsnap.snapshot_store import delete_snapshot, list_snapshots, load_snapshot, save_snapshot, snapshot_path
from winsnap.version import VERSION
from winsnap.views.snapshot_view import print_snapshot_list, print_snapshot_summary
from winsnap.views.ui import success, warning


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


def create_snapshot(name, note="", profile="full"):
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
    selected_keys = PROFILE_KEYS.get(profile, PROFILE_KEYS["full"]) if PROFILE_KEYS else [a.key for a in ARTIFACTS]
    selected = [a for a in ARTIFACTS if a.key in selected_keys]

    snapshot = {
        "name": name,
        "version": VERSION,
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "windows_version": platform.platform(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "collector": [artifact.key for artifact in selected],
        "note": note,
    }

    # Collect in parallel to reduce wall-clock time. On error, store empty list.
    def run_collect(artifact):
        try:
            return artifact.key, artifact.collect()
        except Exception as e:  # keep snapshot creation resilient
            print(warning(f"Collector failed: {artifact.label}: {e}"))
            return artifact.key, []

    with ThreadPoolExecutor(max_workers=min(4, len(selected)) or 1) as executor:
        futures = {executor.submit(run_collect, artifact): artifact for artifact in selected}
        for future in as_completed(futures):
            key, result = future.result()
            snapshot[key] = result

    save_snapshot(snapshot)
    print_snapshot_summary(snapshot)


def show_snapshot(name):
    snapshot = load_snapshot(name)
    print_snapshot_summary(snapshot)


def list_all_snapshots():
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]
    print_snapshot_list(snapshots)


def remove_snapshot(name):
    delete_snapshot(name)
    print(success(f"Deleted snapshot: {name}"))
