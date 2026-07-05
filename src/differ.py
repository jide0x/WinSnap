from collections import Counter, defaultdict


def process_key(proc):
    return f"{proc.get('Name')}|{proc.get('ExecutablePath')}|{proc.get('CommandLine')}"


def service_key(service):
    return (service.get("Name") or "").lower()


def group_processes(processes):
    grouped = defaultdict(list)
    for process in processes:
        grouped[process_key(process)].append(process)
    return grouped


def diff_processes(before, after):
    before_grouped = group_processes(before.get("processes", []))
    after_grouped = group_processes(after.get("processes", []))
    before_counts = Counter({key: len(items) for key, items in before_grouped.items()})
    after_counts = Counter({key: len(items) for key, items in after_grouped.items()})

    added = []
    removed = []

    for key in sorted(after_counts.keys() | before_counts.keys()):
        added_count = after_counts[key] - before_counts[key]
        removed_count = before_counts[key] - after_counts[key]

        if added_count > 0:
            added.extend(after_grouped[key][:added_count])
        if removed_count > 0:
            removed.extend(before_grouped[key][:removed_count])

    return {
        "added": added,
        "removed": removed,
    }


def diff_services(before, after):
    before_services = {
        service_key(service): service
        for service in before.get("services", [])
        if service_key(service)
    }
    after_services = {
        service_key(service): service
        for service in after.get("services", [])
        if service_key(service)
    }

    added_keys = after_services.keys() - before_services.keys()
    removed_keys = before_services.keys() - after_services.keys()
    common_keys = before_services.keys() & after_services.keys()

    changed = []
    for key in sorted(common_keys):
        before_service = before_services[key]
        after_service = after_services[key]
        changes = service_changes(before_service, after_service)
        if changes:
            changed.append({
                "before": before_service,
                "after": after_service,
                "changes": changes,
            })

    return {
        "added": [after_services[key] for key in sorted(added_keys)],
        "removed": [before_services[key] for key in sorted(removed_keys)],
        "changed": changed,
    }


def service_changes(before_service, after_service):
    fields = ["DisplayName", "State", "Status", "StartMode", "StartName", "PathName", "ProcessId"]
    changes = {}

    for field in fields:
        before_value = before_service.get(field)
        after_value = after_service.get(field)
        if before_value != after_value:
            changes[field] = {
                "before": before_value,
                "after": after_value,
            }

    return changes
