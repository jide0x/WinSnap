from datetime import datetime

from winsnap.artifacts import ARTIFACTS, ARTIFACTS_BY_KEY
from winsnap.views.ui import success, warning, info, bold, rule


BOX_WIDTH = 38
LIST_WIDTH = 112
LIST_NAME_WIDTH = 20


def process_count(snapshot):
    return artifact_count(snapshot, "processes")


def service_count(snapshot):
    return artifact_count(snapshot, "services")


def scheduled_task_count(snapshot):
    return artifact_count(snapshot, "scheduled_tasks")


def registry_autorun_count(snapshot):
    return artifact_count(snapshot, "registry_autoruns")


def startup_folder_count(snapshot):
    return artifact_count(snapshot, "startup_folders")


def network_listener_count(snapshot):
    return artifact_count(snapshot, "network_listeners")


def artifact_count(snapshot, key):
    if key not in snapshot:
        return None
    return len(snapshot.get(key, []))


def format_count(value):
    if value is None:
        return "Not collected"
    return str(value)


def format_list_count(value):
    if value is None:
        return "N/C"
    return str(value)


def snapshot_collectors(snapshot):
    return snapshot.get("collector") or snapshot.get("collectors", [])


def snapshot_note(snapshot):
    return snapshot.get("note") or ""


def collector_label(collector):
    if collector in ARTIFACTS_BY_KEY:
        return ARTIFACTS_BY_KEY[collector].label
    return str(collector).replace("_", " ").title()


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
    print()
    print(info(rule(BOX_WIDTH)))
    print(bold("WinSnap".center(BOX_WIDTH)))
    print(info(rule(BOX_WIDTH)))
    print()
    print(f"Snapshot Name : {snapshot.get('name')}")
    print()
    print(f"Created       : {format_full_datetime(snapshot.get('created_at'))}")
    print()
    for artifact in ARTIFACTS:
        print(f"{artifact.label:<14}: {format_count(artifact_count(snapshot, artifact.key))}")
        print()
    if snapshot_note(snapshot):
        print()
        print(f"Note          : {snapshot_note(snapshot)}")
    print()
    print(bold("Collector(s)"))
    print()
    for collector in snapshot_collectors(snapshot):
        print(success(f" • {collector_label(collector)}"))
    print()
    print(info(rule(BOX_WIDTH)))
    print()


def print_snapshot_list(snapshots):
    if not snapshots:
        print(warning("No snapshots found."))
        return

    print()
    print(info(rule(LIST_WIDTH)))
    print()
    print(bold("Snapshots"))
    print()
    print(f"{'Name':<{LIST_NAME_WIDTH}} {'Created':<22} {'Proc':>5} {'Svc':>5} {'Task':>5} {'Run':>5} {'Start':>5} {'Net':>5}  Note")
    print()
    print("-" * LIST_WIDTH)
    print()
    for snap in snapshots:
        print(
            f"{snap.get('name', 'Unknown'):<{LIST_NAME_WIDTH}} "
            f"{format_list_datetime(snap.get('created_at')):<22} "
            f"{format_list_count(process_count(snap)):>5} "
            f"{format_list_count(service_count(snap)):>5} "
            f"{format_list_count(scheduled_task_count(snap)):>5} "
            f"{format_list_count(registry_autorun_count(snap)):>5}  "
            f"{format_list_count(startup_folder_count(snap)):>5}  "
            f"{format_list_count(network_listener_count(snap)):>5}  "
            f"{snapshot_note(snap)}"
        )
    print()
    print(info(rule(LIST_WIDTH)))
    print()
