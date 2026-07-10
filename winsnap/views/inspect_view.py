from collections import Counter

from winsnap.artifacts import ARTIFACTS, matching_items
from winsnap.views.ui import error, info, bold, rule


INSPECT_WIDTH = 60


def process_path(process):
    return process.get("ExecutablePath") or "Unknown"


def parent_pid(process):
    return process.get("ParentProcessId") or "Unknown"


def snapshot_matches(snapshot, query):
    return {
        artifact.key: matching_items(snapshot, artifact, query)
        for artifact in ARTIFACTS
    }


def print_inspect_header(snapshot, query):
    print()
    print(info(rule(INSPECT_WIDTH)))
    print()
    print(bold("Snapshot Inspection"))
    print()
    print(f"Snapshot : {snapshot.get('name')}")
    print(f"Query    : {query}")
    print()
    print(info(rule(INSPECT_WIDTH)))
    print()


def print_snapshot_inspection(snapshot, query, details=False):
    matches = snapshot_matches(snapshot, query)

    print_inspect_header(snapshot, query)

    if not any(matches.values()):
        labels = ", ".join(artifact.label.lower() for artifact in ARTIFACTS)
        print(error(f"No matching {labels} found."))
        print()
        return

    process_artifact = ARTIFACTS[0]
    process_matches = matches[process_artifact.key]
    process_paths = Counter(process_path(process) for process in process_matches)
    parent_pids = Counter(parent_pid(process) for process in process_matches)
    pids = sorted(
        process.get("ProcessId")
        for process in process_matches
        if process.get("ProcessId") is not None
    )

    print(bold("Summary"))
    for artifact in ARTIFACTS:
        print(f"  {artifact.matching_label:<22} {len(matches[artifact.key])}")
    print(f"  {'Unique names':<22} {len(Counter(process_artifact.name(process) for process in process_matches))}")
    print(f"  {'Unique paths':<22} {len(process_paths)}")
    print(f"  {'Parent PIDs':<22} {len(parent_pids)}")
    if pids:
        print(f"  {'PID range':<22} {pids[0]} - {pids[-1]}")
    print()

    print_artifact_summaries(matches)

    if not details:
        labels = ", ".join(artifact.label.lower() for artifact in ARTIFACTS)
        print(bold(f"Use --details to view full entries for {labels}."))
        print()
        return

    print_artifact_details(matches)


def print_artifact_summaries(matches):
    for artifact in ARTIFACTS:
        items = matches[artifact.key]
        if not items:
            continue

        print(bold(artifact.inspect_section_label))
        for name, count in Counter(artifact.name(item) for item in items).most_common():
            print(f"  {name:<50} {count}")
        print()

        if artifact.key == "processes":
            print(bold("Executable Paths"))
            for path, count in Counter(process_path(process) for process in items).most_common():
                print(f"  {count}x {path}")
            print()

            print(bold("Parent Processes"))
            for pid, count in Counter(parent_pid(process) for process in items).most_common():
                print(f"  PID {pid:<10} {count} instance(s)")
            print()

        for title, field_name in artifact.summary_fields:
            print(bold(title))
            for value, count in Counter(summary_value(item.get(field_name)) for item in items).most_common():
                print(f"  {value:<20} {count}")
            print()


def print_artifact_details(matches):
    for artifact in ARTIFACTS:
        items = matches[artifact.key]
        if not items:
            continue

        print(bold(artifact.detail_section_label))
        print()
        for item in items:
            print(info(rule(INSPECT_WIDTH, "─")))
            print()
            artifact.print_item(item)
            print()


def summary_value(value):
    if value is None or value == "":
        return "Unknown"
    return str(value)


def print_process_inspection(snapshot, query, details=False):
    print_snapshot_inspection(snapshot, query, details=details)
