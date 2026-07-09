from src.differ import diff_processes, diff_scheduled_tasks, diff_services
from src.snapshot_store import load_snapshot
from src.views.diff_view import print_detailed_diff, print_diff_summary


def diff_snapshots(before_name, after_name, details=False):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = {
        "processes": diff_processes(before, after),
        "services": diff_services(before, after),
        "scheduled_tasks": diff_scheduled_tasks(before, after),
    }

    if details:
        print_detailed_diff(before, after, diff)
        return

    print_diff_summary(before, after, diff)
