from datetime import datetime

from src.collectors import collect_processes
from src.snapshot_store import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
)
from src.differ import diff_processes


def create_snapshot(name):
    snapshot = {
        "name": name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "version": "0.1",
        "collectors": ["processes"],
        "processes": collect_processes(),
    }

    path = save_snapshot(snapshot)
    print(f"[+] Snapshot saved: {path}")


def show_snapshot(name):
    snapshot = load_snapshot(name)

    print(f"Snapshot : {snapshot.get('name')}")
    print(f"Created  : {snapshot.get('created_at')}")
    print(f"Version  : {snapshot.get('version')}")
    print(f"Collectors: {', '.join(snapshot.get('collectors', []))}")
    print(f"Processes: {len(snapshot.get('processes', []))}")


def list_all_snapshots():
    snapshots = list_snapshots()

    if not snapshots:
        print("No snapshots found.")
        return

    print("Snapshots:")
    for snap in snapshots:
        print(f"  - {snap.stem}")


def remove_snapshot(name):
    delete_snapshot(name)
    print(f"Deleted snapshot: {name}")


def diff_snapshots(before_name, after_name):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = diff_processes(before, after)

    print("\n=== WinSnap Diff ===")
    print(f"Before: {before.get('name')} at {before.get('created_at')}")
    print(f"After : {after.get('name')} at {after.get('created_at')}")

    print(f"\n[+] Added Processes: {len(diff['added'])}")
    for p in diff["added"]:
        print(f"  + {p.get('Name')} PID={p.get('ProcessId')}")
        print(f"    Path: {p.get('ExecutablePath')}")
        print(f"    Cmd : {p.get('CommandLine')}")

    print(f"\n[-] Removed Processes: {len(diff['removed'])}")
    for p in diff["removed"]:
        print(f"  - {p.get('Name')} PID={p.get('ProcessId')}")
        print(f"    Path: {p.get('ExecutablePath')}")
        print(f"    Cmd : {p.get('CommandLine')}")