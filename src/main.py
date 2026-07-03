import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


SNAPSHOT_DIR = Path("snapshots")


def collect_processes():
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    data = json.loads(result.stdout)

    if isinstance(data, dict):
        data = [data]

    return data


def take_snapshot(name):
    SNAPSHOT_DIR.mkdir(exist_ok=True)

    snapshot = {
        "name": name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "processes": collect_processes()
    }

    path = SNAPSHOT_DIR / f"{name}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"[+] Snapshot saved: {path}")


def load_snapshot(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_key(proc):
    return f"{proc.get('Name')}|{proc.get('ExecutablePath')}|{proc.get('CommandLine')}"


def diff_snapshots(before_path, after_path):
    before = load_snapshot(before_path)
    after = load_snapshot(after_path)

    before_processes = {process_key(p): p for p in before["processes"]}
    after_processes = {process_key(p): p for p in after["processes"]}

    added = after_processes.keys() - before_processes.keys()
    removed = before_processes.keys() - after_processes.keys()

    print("\n=== WinSnap Process Diff ===")
    print(f"Before: {before['name']} at {before['created_at']}")
    print(f"After : {after['name']} at {after['created_at']}")

    print(f"\n[+] Added Processes: {len(added)}")
    for key in added:
        p = after_processes[key]
        print(f"  + {p.get('Name')} PID={p.get('ProcessId')}")
        print(f"    Path: {p.get('ExecutablePath')}")
        print(f"    Cmd : {p.get('CommandLine')}")

    print(f"\n[-] Removed Processes: {len(removed)}")
    for key in removed:
        p = before_processes[key]
        print(f"  - {p.get('Name')} PID={p.get('ProcessId')}")
        print(f"    Path: {p.get('ExecutablePath')}")
        print(f"    Cmd : {p.get('CommandLine')}")


def main():
    parser = argparse.ArgumentParser(description="WinSnap: simple Windows process snapshot diff tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("name")

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("before")
    diff_parser.add_argument("after")

    args = parser.parse_args()

    if args.command == "snapshot":
        take_snapshot(args.name)

    elif args.command == "diff":
        diff_snapshots(args.before, args.after)


if __name__ == "__main__":
    main()