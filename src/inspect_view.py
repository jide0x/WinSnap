from collections import Counter

from src.process_view import print_process
from src.ui import error, info, bold, rule


INSPECT_WIDTH = 60


def process_matches(process, query):
    query = query.lower()
    fields = [
        process.get("Name"),
        process.get("ExecutablePath"),
        process.get("CommandLine"),
    ]
    return any(query in str(field).lower() for field in fields if field)


def process_name(process):
    return process.get("Name") or "Unknown"


def process_path(process):
    return process.get("ExecutablePath") or "Unknown"


def parent_pid(process):
    return process.get("ParentProcessId") or "Unknown"


def matching_processes(snapshot, query):
    return [
        process
        for process in snapshot.get("processes", [])
        if process_matches(process, query)
    ]


def print_inspect_header(snapshot, query):
    print()
    print(info(rule(INSPECT_WIDTH)))
    print()
    print(bold("Process Inspection"))
    print()
    print(f"Snapshot : {snapshot.get('name')}")
    print(f"Query    : {query}")
    print()
    print(info(rule(INSPECT_WIDTH)))
    print()


def print_process_inspection(snapshot, query, details=False):
    matches = matching_processes(snapshot, query)

    print_inspect_header(snapshot, query)

    if not matches:
        print(error("No matching processes found."))
        print()
        return

    names = Counter(process_name(process) for process in matches)
    paths = Counter(process_path(process) for process in matches)
    parent_pids = Counter(parent_pid(process) for process in matches)
    pids = sorted(
        process.get("ProcessId")
        for process in matches
        if process.get("ProcessId") is not None
    )

    print(bold("Summary"))
    print(f"  {'Matching instances':<22} {len(matches)}")
    print(f"  {'Unique names':<22} {len(names)}")
    print(f"  {'Unique paths':<22} {len(paths)}")
    print(f"  {'Parent PIDs':<22} {len(parent_pids)}")
    if pids:
        print(f"  {'PID range':<22} {pids[0]} - {pids[-1]}")
    print()

    print(bold("Names"))
    for name, count in names.most_common():
        print(f"  {name:<30} {count}")
    print()

    print(bold("Executable Paths"))
    for path, count in paths.most_common():
        print(f"  {count}x {path}")
    print()

    print(bold("Parent Processes"))
    for pid, count in parent_pids.most_common():
        print(f"  PID {pid:<10} {count} instance(s)")
    print()

    if not details:
        print(bold("Use --details to view full process entries."))
        print()
        return

    print(bold("Instances"))
    print()
    for process in matches:
        print(info(rule(INSPECT_WIDTH, "─")))
        print()
        print_process(process)
        print()
