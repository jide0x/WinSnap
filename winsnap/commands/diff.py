from winsnap.differ import diff_processes, diff_registry_autoruns, diff_scheduled_tasks, diff_services
from winsnap.snapshot_store import load_snapshot
from winsnap.views.diff_view import print_detailed_diff, print_diff_summary


COLLECTORS = {
    "processes": "Processes",
    "services": "Services",
    "scheduled_tasks": "Scheduled Tasks",
    "registry_autoruns": "Registry Autoruns",
}

EMPTY_DIFF = {"added": [], "removed": [], "changed": []}


def diff_snapshots(before_name, after_name, details=False):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = {
        "processes": diff_if_compatible(before, after, "processes", diff_processes),
        "services": diff_if_compatible(before, after, "services", diff_services),
        "scheduled_tasks": diff_if_compatible(before, after, "scheduled_tasks", diff_scheduled_tasks),
        "registry_autoruns": diff_if_compatible(before, after, "registry_autoruns", diff_registry_autoruns),
        "compatibility": compatibility_report(before, after),
    }

    if details:
        print_detailed_diff(before, after, diff)
        return

    print_diff_summary(before, after, diff)


def diff_if_compatible(before, after, collector, diff_func):
    if collector not in before or collector not in after:
        return dict(EMPTY_DIFF)
    return diff_func(before, after)


def compatibility_report(before, after):
    report = []
    for collector, label in COLLECTORS.items():
        before_has_collector = collector in before
        after_has_collector = collector in after

        if before_has_collector and after_has_collector:
            report.append({"label": label, "status": "compared"})
        elif not before_has_collector and not after_has_collector:
            report.append({"label": label, "status": "skipped", "reason": "not present in either snapshot"})
        elif not before_has_collector:
            report.append({"label": label, "status": "skipped", "reason": "not present in before snapshot"})
        else:
            report.append({"label": label, "status": "skipped", "reason": "not present in after snapshot"})

    return report
