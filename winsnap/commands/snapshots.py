from datetime import datetime
import getpass
import platform
import socket

from winsnap.artifacts import ARTIFACTS
from winsnap.snapshot_store import delete_snapshot, list_snapshots, load_snapshot, save_snapshot, snapshot_path
from winsnap.version import VERSION
from winsnap.views.snapshot_view import print_snapshot_list, print_snapshot_summary
from winsnap.views.ui import success, warning


def create_snapshot(name, note=""):
    if snapshot_path(name).exists():
        print(warning(f'Snapshot "{name}" already exists.'))
        print()
        print("Overwrite?")
        print()
        response = input("[y/N] ").strip().lower()
        if response != "y":
            print(warning("Snapshot not overwritten."))
            return

    snapshot = {
        "name": name,
        "version": VERSION,
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "windows_version": platform.platform(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "collector": [artifact.key for artifact in ARTIFACTS],
        "note": note,
    }
    for artifact in ARTIFACTS:
        snapshot[artifact.key] = artifact.collect()

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
