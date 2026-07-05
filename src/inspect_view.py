from collections import Counter

from src.diff_view import print_service, service_name
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


def service_matches(service, query):
    query = query.lower()
    fields = [
        service.get("Name"),
        service.get("DisplayName"),
        service.get("State"),
        service.get("Status"),
        service.get("StartMode"),
        service.get("StartName"),
        service.get("PathName"),
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


def matching_services(snapshot, query):
    return [
        service
        for service in snapshot.get("services", [])
        if service_matches(service, query)
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
    process_matches = matching_processes(snapshot, query)
    service_matches = matching_services(snapshot, query)

    print_inspect_header(snapshot, query)

    if not process_matches and not service_matches:
        print(error("No matching processes or services found."))
        print()
        return

    names = Counter(process_name(process) for process in process_matches)
    paths = Counter(process_path(process) for process in process_matches)
    parent_pids = Counter(parent_pid(process) for process in process_matches)
    pids = sorted(
        process.get("ProcessId")
        for process in process_matches
        if process.get("ProcessId") is not None
    )
    service_names = Counter(service_name(service) for service in service_matches)
    service_states = Counter(service.get("State") or "Unknown" for service in service_matches)
    service_start_modes = Counter(service.get("StartMode") or "Unknown" for service in service_matches)

    print(bold("Summary"))
    print(f"  {'Matching processes':<22} {len(process_matches)}")
    print(f"  {'Matching services':<22} {len(service_matches)}")
    print(f"  {'Unique names':<22} {len(names)}")
    print(f"  {'Unique paths':<22} {len(paths)}")
    print(f"  {'Parent PIDs':<22} {len(parent_pids)}")
    if pids:
        print(f"  {'PID range':<22} {pids[0]} - {pids[-1]}")
    print()

    if process_matches:
        print(bold("Process Names"))
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

    if service_matches:
        print(bold("Services"))
        for name, count in service_names.most_common():
            print(f"  {name:<50} {count}")
        print()

        print(bold("Service States"))
        for state, count in service_states.most_common():
            print(f"  {state:<20} {count}")
        print()

        print(bold("Service Start Modes"))
        for start_mode, count in service_start_modes.most_common():
            print(f"  {start_mode:<20} {count}")
        print()

    if not details:
        print(bold("Use --details to view full process and service entries."))
        print()
        return

    if process_matches:
        print(bold("Process Instances"))
        print()
        for process in process_matches:
            print(info(rule(INSPECT_WIDTH, "─")))
            print()
            print_process(process)
            print()

    if service_matches:
        print(bold("Service Entries"))
        print()
        for service in service_matches:
            print(info(rule(INSPECT_WIDTH, "─")))
            print()
            print_service(service)
            print()
