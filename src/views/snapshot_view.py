from datetime import datetime

from src.views.ui import success, warning, info, bold, rule


BOX_WIDTH = 38
LIST_WIDTH = 88
LIST_NAME_WIDTH = 20


def process_count(snapshot):
    return len(snapshot.get("processes", []))


def service_count(snapshot):
    if "services" not in snapshot:
        return None
    return len(snapshot.get("services", []))


def scheduled_task_count(snapshot):
    if "scheduled_tasks" not in snapshot:
        return None
    return len(snapshot.get("scheduled_tasks", []))


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
    print(f"Processes     : {format_count(process_count(snapshot))}")
    print()
    print(f"Services      : {format_count(service_count(snapshot))}")
    print()
    print(f"Tasks         : {format_count(scheduled_task_count(snapshot))}")
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
    print(f"{'Name':<{LIST_NAME_WIDTH}} {'Created':<22} {'Proc':>5} {'Svc':>5} {'Task':>5}  Note")
    print()
    print("-" * LIST_WIDTH)
    print()
    for snap in snapshots:
        print(
            f"{snap.get('name', 'Unknown'):<{LIST_NAME_WIDTH}} "
            f"{format_list_datetime(snap.get('created_at')):<22} "
            f"{format_list_count(process_count(snap)):>5} "
            f"{format_list_count(service_count(snap)):>5} "
            f"{format_list_count(scheduled_task_count(snap)):>5}  "
            f"{snapshot_note(snap)}"
        )
    print()
    print(info(rule(LIST_WIDTH)))
    print()
