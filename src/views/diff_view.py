from collections import Counter

from src.views.process_view import print_process
from src.views.ui import success, error, info, bold, rule


DIFF_WIDTH = 46
TOP_CHANGED_LIMIT = 10

# Gets display name of process
def process_name(process):
    return process.get("Name") or "Unknown"

# Gets 
def executable_key(process):
    return (
        process_name(process).lower(),
        (process.get("ExecutablePath") or "").lower(),
    )

# Gets display label of process
def executable_label(process):
    return process_name(process)

# Gets a mapping of executable keys to display labels for a list of processes
def executable_map(processes):
    return {executable_key(process): executable_label(process) for process in processes}

# Prints header for diff report
def print_diff_header(before, after):
    print(info(rule(DIFF_WIDTH)))
    print()
    print(bold("Difference Report"))
    print()
    print(f"Before : {before.get('name')}")
    print(f"After  : {after.get('name')}")
    print()
    print(info(rule(DIFF_WIDTH)))
    print()

# prints summary of diff report (base command)
def print_diff_summary(before, after, diff):
    process_diff = diff["processes"]
    service_diff = diff["services"]
    task_diff = diff["scheduled_tasks"]
    added = process_diff["added"]
    removed = process_diff["removed"]
    added_counts = Counter(process_name(process) for process in added)
    removed_counts = Counter(process_name(process) for process in removed)
    changed_names = sorted(
        added_counts.keys() | removed_counts.keys(),
        key=lambda name: (-(added_counts[name] + removed_counts[name]), name.lower()),
    )
    before_executables = executable_map(before.get("processes", []))
    after_executables = executable_map(after.get("processes", []))
    new_executable_keys = after_executables.keys() - before_executables.keys()
    removed_executable_keys = before_executables.keys() - after_executables.keys()
    new_executables = sorted(
        {after_executables[key] for key in new_executable_keys},
        key=str.lower,
    )
    removed_executables = sorted(
        {before_executables[key] for key in removed_executable_keys},
        key=str.lower,
    )

    print_diff_header(before, after)
    print(bold("Summary"))
    print(f"  {'Added process instances':<27} {len(added)}")
    print(f"  {'Removed process instances':<27} {len(removed)}")
    print(f"  {'Added services':<27} {len(service_diff['added'])}")
    print(f"  {'Removed services':<27} {len(service_diff['removed'])}")
    print(f"  {'Changed services':<27} {len(service_diff['changed'])}")
    print(f"  {'Added scheduled tasks':<27} {len(task_diff['added'])}")
    print(f"  {'Removed scheduled tasks':<27} {len(task_diff['removed'])}")
    print(f"  {'Changed scheduled tasks':<27} {len(task_diff['changed'])}")
    print()

    print(bold("Top Changed Apps"))
    if changed_names:
        for name in changed_names[:TOP_CHANGED_LIMIT]:
            print(f"  {name:<27} +{added_counts[name]} / -{removed_counts[name]}")
    else:
        print("  None")
    print()

    print(bold("New Executables"))
    if new_executables:
        for name in new_executables:
            print(f"  {name}")
    else:
        print("  None")
    print()

    print(bold("Removed Executables"))
    if removed_executables:
        for name in removed_executables:
            print(f"  {name}")
    else:
        print("  None")
    print()

    print(bold("Service Changes"))
    if service_diff["added"] or service_diff["removed"] or service_diff["changed"]:
        for service in service_diff["added"][:10]:
            print(f"  + {service_name(service)}")
        for service in service_diff["removed"][:10]:
            print(f"  - {service_name(service)}")
        for item in service_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {service_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()

    print(bold("Scheduled Task Changes"))
    if task_diff["added"] or task_diff["removed"] or task_diff["changed"]:
        for task in task_diff["added"][:10]:
            print(f"  + {task_name(task)}")
        for task in task_diff["removed"][:10]:
            print(f"  - {task_name(task)}")
        for item in task_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {task_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()
    print(bold("Use --details to view full process, service, and scheduled task entries."))
    print()

# Prints detailed diff report (full process entries)
def print_detailed_diff(before, after, diff):
    print_diff_header(before, after)

    process_diff = diff["processes"]
    service_diff = diff["services"]
    task_diff = diff["scheduled_tasks"]

    print(success(f"Added Processes ({len(process_diff['added'])})"))
    print()
    for process in process_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_process(process)
        print()

    print()
    print(error(f"Removed Processes ({len(process_diff['removed'])})"))
    print()
    for process in process_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_process(process)
        print()

    print()
    print(success(f"Added Services ({len(service_diff['added'])})"))
    print()
    for service in service_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_service(service)
        print()

    print()
    print(error(f"Removed Services ({len(service_diff['removed'])})"))
    print()
    for service in service_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_service(service)
        print()

    print()
    print(bold(f"Changed Services ({len(service_diff['changed'])})"))
    print()
    for item in service_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_service(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()

    print()
    print(success(f"Added Scheduled Tasks ({len(task_diff['added'])})"))
    print()
    for task in task_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_scheduled_task(task)
        print()

    print()
    print(error(f"Removed Scheduled Tasks ({len(task_diff['removed'])})"))
    print()
    for task in task_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_scheduled_task(task)
        print()

    print()
    print(bold(f"Changed Scheduled Tasks ({len(task_diff['changed'])})"))
    print()
    for item in task_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_scheduled_task(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {format_task_value(values['before'])}")
            print(f"    After : {format_task_value(values['after'])}")
        print()


def service_name(service):
    name = service.get("Name") or "Unknown"
    display_name = service.get("DisplayName")
    if display_name and display_name != name:
        return f"{name} ({display_name})"
    return name


def print_service(service):
    print(bold(service_name(service)))
    print()
    print(f" Name         {service.get('Name') or 'Unknown'}")
    print(f" State        {service.get('State') or 'Unknown'}")
    print(f" Status       {service.get('Status') or 'Unknown'}")
    print(f" Start Mode   {service.get('StartMode') or 'Unknown'}")
    print(f" Account      {service.get('StartName') or 'Unknown'}")
    print(f" Process ID   {service.get('ProcessId')}")
    print(f" Path         {service.get('PathName') or 'Unknown'}")

    hints = service_risk_hints(service)
    if hints:
        print()
        print(bold(" Risk Hints"))
        for hint in hints:
            print(f"  ! {hint}")


def service_risk_hints(service):
    hints = []
    start_mode = (service.get("StartMode") or "").lower()
    start_name = (service.get("StartName") or "").lower()
    path_name = service.get("PathName")
    normalized_path = (path_name or "").lower().replace("/", "\\")

    if start_mode == "auto":
        hints.append("Auto-start service")

    if start_name in {"localsystem", "local system"}:
        hints.append("Runs as LocalSystem")

    if not path_name:
        hints.append("Missing/unknown PathName")
    elif is_user_writable_path(normalized_path):
        hints.append("Path in user-writable location")

    return hints


def is_user_writable_path(path):
    user_writable_markers = [
        "\\users\\",
        "\\appdata\\",
        "\\temp\\",
        "\\tmp\\",
        "\\programdata\\",
    ]
    return any(marker in path for marker in user_writable_markers)


def task_name(task):
    task_path = task.get("TaskPath") or ""
    task_name_value = task.get("TaskName") or "Unknown"
    return f"{task_path}{task_name_value}"


def print_scheduled_task(task):
    print(bold(task_name(task)))
    print()
    print(f" Task Name    {task.get('TaskName') or 'Unknown'}")
    print(f" Task Path    {task.get('TaskPath') or 'Unknown'}")
    print(f" State        {task.get('State') or 'Unknown'}")
    print(f" Author       {task.get('Author') or 'Unknown'}")
    print(f" Run As User  {task.get('RunAsUser') or 'Unknown'}")
    print(" Triggers")
    for trigger in task_values(task.get("Triggers")):
        print(f"  - {trigger}")
    print(" Actions")
    for action in task_values(task.get("Actions")):
        print(f"  - {action}")

    hints = scheduled_task_risk_hints(task)
    if hints:
        print()
        print(bold(" Risk Hints"))
        for hint in hints:
            print(f"  ! {hint}")


def scheduled_task_risk_hints(task):
    hints = []
    state = str(task.get("State") or "").lower()
    run_as_user = str(task.get("RunAsUser") or "").lower()
    triggers = " ".join(task_values(task.get("Triggers"))).lower()
    actions = " ".join(task_values(task.get("Actions"))).lower().replace("/", "\\")

    if state in {"ready", "running"}:
        hints.append("Enabled scheduled task")

    if run_as_user in {"system", "localsystem", "local system", "nt authority\\system"}:
        hints.append("Runs as SYSTEM")

    if "logon" in triggers:
        hints.append("Runs at logon")

    if "startup" in triggers or "boot" in triggers:
        hints.append("Runs at startup")

    if any(marker in actions for marker in suspicious_action_markers()):
        hints.append("Executes command or scripting host")

    if is_user_writable_path(actions):
        hints.append("Action path in user-writable location")

    return hints


def suspicious_action_markers():
    return [
        "powershell",
        "pwsh",
        "cmd.exe",
        "wscript",
        "cscript",
        "mshta",
        "rundll32",
        "regsvr32",
        "schtasks",
    ]


def task_values(value):
    if value is None or value == "":
        return ["None"]
    if isinstance(value, list):
        return [str(item) for item in value] or ["None"]
    return [str(value)]


def format_task_value(value):
    return "; ".join(task_values(value))
