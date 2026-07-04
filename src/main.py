from datetime import datetime
import getpass
import platform
import socket

from src.collectors import collect_processes
from src.snapshot_store import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
    snapshot_path,
)
from src.differ import diff_processes
from src.diff_view import print_detailed_diff, print_diff_summary
from src.inspect_view import print_process_inspection
from src.search_view import print_process_search
from src.snapshot_view import print_snapshot_list, print_snapshot_summary
from src.ui import success, warning
from src.version import VERSION


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
        "collector": ["processes"],
        "note": note,
        "processes": collect_processes(),
    }

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


def inspect_snapshot(name, query, details=False):
    snapshot = load_snapshot(name)
    print_process_inspection(snapshot, query, details=details)


def search_snapshots(query, details=False):
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]
    print_process_search(snapshots, query, details=details)


def diff_snapshots(before_name, after_name, details=False):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = diff_processes(before, after)

    if details:
        print_detailed_diff(before, after, diff)
        return

    print_diff_summary(before, after, diff)
