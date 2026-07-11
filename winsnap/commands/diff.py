from winsnap.artifacts import ARTIFACTS
from winsnap.filtering.engine import apply_filters
from winsnap.schema import validate_snapshot
from winsnap.snapshot_store import load_snapshot
from winsnap.views.diff_view import print_detailed_diff, print_diff_summary


def empty_diff():
    return {"added": [], "removed": [], "changed": []}


def diff_snapshots(before_name, after_name, details=False, show_all=False):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)
    # Basic validation (non-fatal if it raises; show a helpful error)
    validate_snapshot(before)
    validate_snapshot(after)

    diff = {artifact.key: diff_if_compatible(before, after, artifact) for artifact in ARTIFACTS}
    diff["compatibility"] = compatibility_report(before, after)

    # Apply default filtering unless user requested full output
    if not show_all:
        diff = apply_filters(before, after, diff, mode="default")

    if details:
        print_detailed_diff(before, after, diff)
        return

    print_diff_summary(before, after, diff)


def _collector_success(snapshot, key):
    status_map = snapshot.get("collector_status", {}) or {}
    status = status_map.get(key, {})
    return not status or status.get("status") == "success"


def diff_if_compatible(before, after, artifact):
    if artifact.key not in before or artifact.key not in after:
        return empty_diff()
    # Skip comparison if collection failed in either snapshot
    if not _collector_success(before, artifact.key) or not _collector_success(after, artifact.key):
        return empty_diff()
    return artifact.diff(before, after)


def compatibility_report(before, after):
    report = []
    for artifact in ARTIFACTS:
        before_has_collector = artifact.key in before
        after_has_collector = artifact.key in after

        if before_has_collector and after_has_collector:
            # Check collection status; if failed in either, mark skipped with reason
            if _collector_success(before, artifact.key) and _collector_success(after, artifact.key):
                report.append({"label": artifact.label, "status": "compared"})
            else:
                reason = (
                    "collection failed in before snapshot"
                    if not _collector_success(before, artifact.key)
                    else "collection failed in after snapshot"
                )
                report.append({"label": artifact.label, "status": "skipped", "reason": reason})
        elif not before_has_collector and not after_has_collector:
            report.append({"label": artifact.label, "status": "skipped", "reason": "not present in either snapshot"})
        elif not before_has_collector:
            report.append({"label": artifact.label, "status": "skipped", "reason": "not present in before snapshot"})
        else:
            report.append({"label": artifact.label, "status": "skipped", "reason": "not present in after snapshot"})

    return report
