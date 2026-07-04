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
)
from src.differ import diff_processes


BOX_WIDTH = 38
LIST_WIDTH = 60
DIFF_WIDTH = 46


def rule(width=BOX_WIDTH, char="═"):
    return char * width


def process_count(snapshot):
    return len(snapshot.get("processes", []))


def snapshot_collectors(snapshot):
    return snapshot.get("collector") or snapshot.get("collectors", [])


def parse_created_at(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_full_datetime(value):
    created_at = parse_created_at(value)
    if not created_at:
        return value or "Unknown"

    return f"{created_at:%Y-%m-%d} {created_at:%I:%M %p}"


def format_list_datetime(value):
    created_at = parse_created_at(value)
    if not created_at:
        return value or "Unknown"

    return f"{created_at:%b} {created_at.day} {created_at:%I:%M %p}"


def print_snapshot_summary(snapshot):
    print(rule())
    print("WinSnap".center(BOX_WIDTH))
    print(rule())
    print()
    print(f"Snapshot Name : {snapshot.get('name')}")
    print()
    print(f"Created       : {format_full_datetime(snapshot.get('created_at'))}")
    print()
    print(f"Processes     : {process_count(snapshot)}")
    print()
    print("Collector(s)")
    print()
    for collector in snapshot_collectors(snapshot):
        print(f" • {collector.title()}")
    print()
    print(rule())


def print_process(process, marker=""):
    name = process.get("Name") or "Unknown"
    print(name if not marker else f"{marker} {name}")
    print()
    print(f" PID          {process.get('ProcessId')}")
    print(f" Parent PID   {process.get('ParentProcessId')}")
    print(f" Path         {process.get('ExecutablePath') or 'Unknown'}")
    command_line = process.get("CommandLine")
    if command_line:
        print(f" Command      {command_line}")


def create_snapshot(name):
    snapshot = {
        "name": name,
        "version": "0.2",
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "windows_version": platform.platform(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "collector": ["processes"],
        "processes": collect_processes(),
    }

    save_snapshot(snapshot)
    print_snapshot_summary(snapshot)


def show_snapshot(name):
    snapshot = load_snapshot(name)
    print_snapshot_summary(snapshot)


def list_all_snapshots():
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]

    if not snapshots:
        print("No snapshots found.")
        return

    print(rule(LIST_WIDTH))
    print()
    print("Snapshots")
    print()
    print(f"{'Name':<13} {'Created':<22} {'Processes':>9}")
    print()
    print("-" * LIST_WIDTH)
    print()
    for snap in snapshots:
        print(
            f"{snap.get('name', 'Unknown'):<13} "
            f"{format_list_datetime(snap.get('created_at')):<22} "
            f"{process_count(snap):>9}"
        )
    print()
    print(rule(LIST_WIDTH))


def remove_snapshot(name):
    delete_snapshot(name)
    print(f"Deleted snapshot: {name}")


def diff_snapshots(before_name, after_name):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = diff_processes(before, after)

    print(rule(DIFF_WIDTH))
    print()
    print("Difference Report")
    print()
    print(f"Before : {before.get('name')}")
    print(f"After  : {after.get('name')}")
    print()
    print(rule(DIFF_WIDTH))
    print()

    print(f"Added Processes ({len(diff['added'])})")
    print()
    for process in diff["added"]:
        print(rule(DIFF_WIDTH, "─"))
        print()
        print_process(process)
        print()

    print(f"Removed Processes ({len(diff['removed'])})")
    print()
    for process in diff["removed"]:
        print(rule(DIFF_WIDTH, "─"))
        print()
        print_process(process)
        print()
