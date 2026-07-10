from collections import Counter, defaultdict


def process_key(proc):
    return f"{proc.get('Name')}|{proc.get('ExecutablePath')}|{proc.get('CommandLine')}"


def service_key(service):
    return (service.get("Name") or "").lower()


def scheduled_task_key(task):
    return f"{task.get('TaskPath') or ''}|{task.get('TaskName') or ''}".lower()


def registry_autorun_key(autorun):
    return f"{autorun.get('Hive') or ''}|{autorun.get('KeyPath') or ''}|{autorun.get('ValueName') or ''}".lower()


def startup_folder_key(item):
    return f"{item.get('Scope') or ''}|{item.get('FullName') or ''}".lower()


def network_listener_key(listener):
    return f"{listener.get('Protocol') or ''}|{listener.get('LocalAddress') or ''}|{listener.get('LocalPort') or ''}|{listener.get('OwningProcess') or ''}".lower()


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


def diff_scheduled_tasks(before, after):
    before_tasks = {
        scheduled_task_key(task): task
        for task in before.get("scheduled_tasks", [])
        if scheduled_task_key(task)
    }
    after_tasks = {
        scheduled_task_key(task): task
        for task in after.get("scheduled_tasks", [])
        if scheduled_task_key(task)
    }

    added_keys = after_tasks.keys() - before_tasks.keys()
    removed_keys = before_tasks.keys() - after_tasks.keys()
    common_keys = before_tasks.keys() & after_tasks.keys()

    changed = []
    for key in sorted(common_keys):
        before_task = before_tasks[key]
        after_task = after_tasks[key]
        changes = scheduled_task_changes(before_task, after_task)
        if changes:
            changed.append({
                "before": before_task,
                "after": after_task,
                "changes": changes,
            })

    return {
        "added": [after_tasks[key] for key in sorted(added_keys)],
        "removed": [before_tasks[key] for key in sorted(removed_keys)],
        "changed": changed,
    }


def scheduled_task_changes(before_task, after_task):
    fields = ["State", "Author", "RunAsUser", "Triggers", "Actions"]
    changes = {}

    for field in fields:
        before_value = before_task.get(field)
        after_value = after_task.get(field)
        if before_value != after_value:
            changes[field] = {
                "before": before_value,
                "after": after_value,
            }

    return changes


def diff_registry_autoruns(before, after):
    before_autoruns = {
        registry_autorun_key(autorun): autorun
        for autorun in before.get("registry_autoruns", [])
        if registry_autorun_key(autorun)
    }
    after_autoruns = {
        registry_autorun_key(autorun): autorun
        for autorun in after.get("registry_autoruns", [])
        if registry_autorun_key(autorun)
    }

    added_keys = after_autoruns.keys() - before_autoruns.keys()
    removed_keys = before_autoruns.keys() - after_autoruns.keys()
    common_keys = before_autoruns.keys() & after_autoruns.keys()

    changed = []
    for key in sorted(common_keys):
        before_autorun = before_autoruns[key]
        after_autorun = after_autoruns[key]
        changes = registry_autorun_changes(before_autorun, after_autorun)
        if changes:
            changed.append({
                "before": before_autorun,
                "after": after_autorun,
                "changes": changes,
            })

    return {
        "added": [after_autoruns[key] for key in sorted(added_keys)],
        "removed": [before_autoruns[key] for key in sorted(removed_keys)],
        "changed": changed,
    }


def registry_autorun_changes(before_autorun, after_autorun):
    changes = {}

    before_value = before_autorun.get("Value")
    after_value = after_autorun.get("Value")
    if before_value != after_value:
        changes["Value"] = {
            "before": before_value,
            "after": after_value,
        }

    return changes


def diff_startup_folders(before, after):
    before_items = {
        startup_folder_key(item): item
        for item in before.get("startup_folders", [])
        if startup_folder_key(item)
    }
    after_items = {
        startup_folder_key(item): item
        for item in after.get("startup_folders", [])
        if startup_folder_key(item)
    }

    added_keys = after_items.keys() - before_items.keys()
    removed_keys = before_items.keys() - after_items.keys()
    common_keys = before_items.keys() & after_items.keys()

    changed = []
    for key in sorted(common_keys):
        before_item = before_items[key]
        after_item = after_items[key]
        changes = startup_folder_changes(before_item, after_item)
        if changes:
            changed.append({
                "before": before_item,
                "after": after_item,
                "changes": changes,
            })

    return {
        "added": [after_items[key] for key in sorted(added_keys)],
        "removed": [before_items[key] for key in sorted(removed_keys)],
        "changed": changed,
    }


def startup_folder_changes(before_item, after_item):
    fields = ["Name", "FullName", "Extension", "Length", "LastWriteTimeUtc", "TargetPath", "Arguments", "WorkingDirectory"]
    changes = {}

    for field in fields:
        before_value = before_item.get(field)
        after_value = after_item.get(field)
        if before_value != after_value:
            changes[field] = {
                "before": before_value,
                "after": after_value,
            }

    return changes


def diff_network_listeners(before, after):
    before_listeners = {
        network_listener_key(listener): listener
        for listener in before.get("network_listeners", [])
        if network_listener_key(listener)
    }
    after_listeners = {
        network_listener_key(listener): listener
        for listener in after.get("network_listeners", [])
        if network_listener_key(listener)
    }

    added_keys = after_listeners.keys() - before_listeners.keys()
    removed_keys = before_listeners.keys() - after_listeners.keys()
    common_keys = before_listeners.keys() & after_listeners.keys()

    changed = []
    for key in sorted(common_keys):
        before_listener = before_listeners[key]
        after_listener = after_listeners[key]
        changes = network_listener_changes(before_listener, after_listener)
        if changes:
            changed.append({
                "before": before_listener,
                "after": after_listener,
                "changes": changes,
            })

    return {
        "added": [after_listeners[key] for key in sorted(added_keys)],
        "removed": [before_listeners[key] for key in sorted(removed_keys)],
        "changed": changed,
    }


def network_listener_changes(before_listener, after_listener):
    fields = ["Protocol", "LocalAddress", "LocalPort", "State", "OwningProcess", "ProcessName", "ProcessPath", "ServiceNames"]
    changes = {}

    for field in fields:
        before_value = before_listener.get(field)
        after_value = after_listener.get(field)
        if before_value != after_value:
            changes[field] = {
                "before": before_value,
                "after": after_value,
            }

    return changes
