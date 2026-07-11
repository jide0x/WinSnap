from collections import Counter

from winsnap.views.process_view import print_process
from winsnap.views.ui import success, error, info, bold, rule


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
    autorun_diff = diff["registry_autoruns"]
    startup_diff = diff["startup_folders"]
    listener_diff = diff["network_listeners"]
    firewall_diff = diff.get("firewall_rules", {"added": [], "removed": [], "changed": []})
    software_diff = diff.get("installed_software", {"added": [], "removed": [], "changed": []})
    user_diff = diff.get("local_users", {"added": [], "removed": [], "changed": []})
    group_diff = diff.get("local_groups", {"added": [], "removed": [], "changed": []})
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
    print_compatibility(diff)

    print(bold("Summary"))
    print(f"  {'Added process instances':<27} {len(added)}")
    print(f"  {'Removed process instances':<27} {len(removed)}")
    print(f"  {'Added services':<27} {len(service_diff['added'])}")
    print(f"  {'Removed services':<27} {len(service_diff['removed'])}")
    print(f"  {'Changed services':<27} {len(service_diff['changed'])}")
    print(f"  {'Added scheduled tasks':<27} {len(task_diff['added'])}")
    print(f"  {'Removed scheduled tasks':<27} {len(task_diff['removed'])}")
    print(f"  {'Changed scheduled tasks':<27} {len(task_diff['changed'])}")
    print(f"  {'Added registry autoruns':<27} {len(autorun_diff['added'])}")
    print(f"  {'Removed registry autoruns':<27} {len(autorun_diff['removed'])}")
    print(f"  {'Changed registry autoruns':<27} {len(autorun_diff['changed'])}")
    print(f"  {'Added startup items':<27} {len(startup_diff['added'])}")
    print(f"  {'Removed startup items':<27} {len(startup_diff['removed'])}")
    print(f"  {'Changed startup items':<27} {len(startup_diff['changed'])}")
    print(f"  {'Added local users':<27} {len(user_diff['added'])}")
    print(f"  {'Removed local users':<27} {len(user_diff['removed'])}")
    print(f"  {'Changed local users':<27} {len(user_diff['changed'])}")
    print(f"  {'Added local groups':<27} {len(group_diff['added'])}")
    print(f"  {'Removed local groups':<27} {len(group_diff['removed'])}")
    print(f"  {'Changed local groups':<27} {len(group_diff['changed'])}")
    print(f"  {'Added listeners':<27} {len(listener_diff['added'])}")
    print(f"  {'Removed listeners':<27} {len(listener_diff['removed'])}")
    print(f"  {'Changed listeners':<27} {len(listener_diff['changed'])}")
    print(f"  {'Added software':<27} {len(software_diff['added'])}")
    print(f"  {'Added firewall rules':<27} {len(firewall_diff['added'])}")
    print(f"  {'Removed software':<27} {len(software_diff['removed'])}")
    print(f"  {'Removed firewall rules':<27} {len(firewall_diff['removed'])}")
    print(f"  {'Changed software':<27} {len(software_diff['changed'])}")
    print(f"  {'Changed firewall rules':<27} {len(firewall_diff['changed'])}")
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

    print(bold("Registry Autorun Changes"))
    if autorun_diff["added"] or autorun_diff["removed"] or autorun_diff["changed"]:
        for autorun in autorun_diff["added"][:10]:
            print(f"  + {autorun_name(autorun)}")
        for autorun in autorun_diff["removed"][:10]:
            print(f"  - {autorun_name(autorun)}")
        for item in autorun_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {autorun_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()

    print(bold("Startup Folder Changes"))
    if startup_diff["added"] or startup_diff["removed"] or startup_diff["changed"]:
        for item in startup_diff["added"][:10]:
            print(f"  + {startup_item_name(item)}")
        for item in startup_diff["removed"][:10]:
            print(f"  - {startup_item_name(item)}")
        for item in startup_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {startup_item_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()

    print(bold("Network Listener Changes"))
    if listener_diff["added"] or listener_diff["removed"] or listener_diff["changed"]:
        for listener in listener_diff["added"][:10]:
            print(f"  + {network_listener_name(listener)}")
        for listener in listener_diff["removed"][:10]:
            print(f"  - {network_listener_name(listener)}")
        for item in listener_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {network_listener_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()
    print(bold("Installed Software Changes"))
    if software_diff["added"] or software_diff["removed"] or software_diff["changed"]:
        for item in software_diff["added"][:10]:
            print(f"  + {software_name(item)}")
        for item in software_diff["removed"][:10]:
            print(f"  - {software_name(item)}")
        for item in software_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {software_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()
    print(bold("Local User Changes"))
    if user_diff["added"] or user_diff["removed"] or user_diff["changed"]:
        for item in user_diff["added"][:10]:
            print(f"  + {local_user_name(item)}")
        for item in user_diff["removed"][:10]:
            print(f"  - {local_user_name(item)}")
        for item in user_diff["changed"][:10]:
            fields = ", ".join(item["changes"].keys())
            print(f"  ~ {local_user_name(item['after'])} ({fields})")
    else:
        print("  None")
    print()

    print(bold("Local Group Membership Changes"))
    if group_diff["added"] or group_diff["removed"] or group_diff["changed"]:
        for item in group_diff["added"][:10]:
            print(f"  + {local_group_name(item)}")
        for item in group_diff["removed"][:10]:
            print(f"  - {local_group_name(item)}")
        for item in group_diff["changed"][:10]:
            print(f"  ~ {local_group_name(item['after'])} (Members)")
    else:
        print("  None")
    print()

    print(bold("New Services With New Listeners"))
    correlations = new_services_with_new_listeners(service_diff, listener_diff)
    if correlations:
        for service, listener in correlations[:10]:
            print(f"  + {service_name(service)} -> {network_listener_name(listener)}")
    else:
        print("  None")
    print()
    print(bold("New Allow Inbound Rules With New Listeners"))
    fw_listener_corr = new_allow_inbound_rules_with_new_listeners(firewall_diff, listener_diff)
    if fw_listener_corr:
        for rule, listener in fw_listener_corr[:10]:
            print(f"  + {firewall_rule_name(rule)} -> {network_listener_name(listener)}")
    else:
        print("  None")
    print()
    print(bold("Use --details to view full process, service, scheduled task, registry autorun, startup folder, installed software, firewall rule, and network listener entries."))
    print()

# Prints detailed diff report (full process entries)
def print_detailed_diff(before, after, diff):
    print_diff_header(before, after)
    print_compatibility(diff)

    process_diff = diff["processes"]
    service_diff = diff["services"]
    task_diff = diff["scheduled_tasks"]
    autorun_diff = diff["registry_autoruns"]
    startup_diff = diff["startup_folders"]
    listener_diff = diff["network_listeners"]
    software_diff = diff.get("installed_software", {"added": [], "removed": [], "changed": []})
    firewall_diff = diff.get("firewall_rules", {"added": [], "removed": [], "changed": []})
    user_diff = diff.get("local_users", {"added": [], "removed": [], "changed": []})
    group_diff = diff.get("local_groups", {"added": [], "removed": [], "changed": []})

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

    print()
    print(success(f"Added Registry Autoruns ({len(autorun_diff['added'])})"))
    print()
    for autorun in autorun_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_registry_autorun(autorun)
        print()

    print()
    print(error(f"Removed Registry Autoruns ({len(autorun_diff['removed'])})"))
    print()
    for autorun in autorun_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_registry_autorun(autorun)
        print()

    print()
    print(bold(f"Changed Registry Autoruns ({len(autorun_diff['changed'])})"))
    print()
    for item in autorun_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_registry_autorun(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()

    print()
    print(success(f"Added Startup Items ({len(startup_diff['added'])})"))
    print()
    for item in startup_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_startup_item(item)
        print()

    print()
    print(error(f"Removed Startup Items ({len(startup_diff['removed'])})"))
    print()
    for item in startup_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_startup_item(item)
        print()

    print()
    print(bold(f"Changed Startup Items ({len(startup_diff['changed'])})"))
    print()
    for item in startup_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_startup_item(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()

    print()
    print(success(f"Added Network Listeners ({len(listener_diff['added'])})"))
    print()
    for listener in listener_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_network_listener(listener)
        print()

    print()
    print(error(f"Removed Network Listeners ({len(listener_diff['removed'])})"))
    print()
    for listener in listener_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_network_listener(listener)
        print()

    print()
    print(bold(f"Changed Network Listeners ({len(listener_diff['changed'])})"))
    print()
    for item in listener_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()

    print()
    print(success(f"Added Installed Software ({len(software_diff['added'])})"))
    print()
    for item in software_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_installed_software(item)
        print()

    print()
    print(error(f"Removed Installed Software ({len(software_diff['removed'])})"))
    print()
    for item in software_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_installed_software(item)
        print()

    print()
    print(bold(f"Changed Installed Software ({len(software_diff['changed'])})"))
    print()
    for item in software_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_installed_software(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()

    print()
    print(success(f"Added Local Users ({len(user_diff['added'])})"))
    print()
    for item in user_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_user(item)
        print()

    print()
    print(error(f"Removed Local Users ({len(user_diff['removed'])})"))
    print()
    for item in user_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_user(item)
        print()

    print()
    print(bold(f"Changed Local Users ({len(user_diff['changed'])})"))
    print()
    for item in user_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_user(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()

    print()
    print(success(f"Added Local Groups ({len(group_diff['added'])})"))
    print()
    for item in group_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_group(item)
        print()

    print()
    print(error(f"Removed Local Groups ({len(group_diff['removed'])})"))
    print()
    for item in group_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_group(item)
        print()

    print()
    print(bold(f"Changed Local Groups ({len(group_diff['changed'])})"))
    print()
    for item in group_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_local_group(item["after"])
        print()
        print(bold(" Changes"))
        # Show member diffs if present
        members_change = item.get("changes", {}).get("Members")
        if isinstance(members_change, dict):
            before_members = set(members_change.get("before", []))
            after_members = set(members_change.get("after", []))
            added_m = sorted(after_members - before_members)
            removed_m = sorted(before_members - after_members)
            if added_m:
                print("  Added Members")
                for m in added_m:
                    print(f"    + {m}")
            if removed_m:
                print("  Removed Members")
                for m in removed_m:
                    print(f"    - {m}")
        print()
    print()
    print(success(f"Added Firewall Rules ({len(firewall_diff['added'])})"))
    print()
    for rule_item in firewall_diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_firewall_rule(rule_item)
        print()

    print()
    print(error(f"Removed Firewall Rules ({len(firewall_diff['removed'])})"))
    print()
    for rule_item in firewall_diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_firewall_rule(rule_item)
        print()

    print()
    print(bold(f"Changed Firewall Rules ({len(firewall_diff['changed'])})"))
    print()
    for item in firewall_diff["changed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_firewall_rule(item["after"])
        print()
        print(bold(" Changes"))
        for field, values in item["changes"].items():
            print(f"  {field}")
            print(f"    Before: {values['before']}")
            print(f"    After : {values['after']}")
        print()


def print_compatibility(diff):
    print(bold("Compatibility"))
    for item in diff.get("compatibility", []):
        if item["status"] == "compared":
            print(f"  {item['label']} compared")
        else:
            print(f"  {item['label']} skipped: {item['reason']}")
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

def autorun_name(autorun):
    value_name = autorun.get("ValueName") or "Unknown"
    key_path = autorun.get("KeyPath") or "Unknown"
    return f"{key_path}\\{value_name}"


def print_registry_autorun(autorun):
    print(bold(autorun_name(autorun)))
    print()
    print(f" Hive        {autorun.get('Hive') or 'Unknown'}")
    print(f" Key Path    {autorun.get('KeyPath') or 'Unknown'}")
    print(f" Value Name  {autorun.get('ValueName') or 'Unknown'}")
    print(f" Value       {autorun.get('Value') or 'Unknown'}")


def startup_item_name(item):
    scope = item.get("Scope") or "Unknown"
    name = item.get("Name") or "Unknown"
    return f"{scope}: {name}"


def print_startup_item(item):
    print(bold(startup_item_name(item)))
    print()
    print(f" Scope       {item.get('Scope') or 'Unknown'}")
    print(f" Name        {item.get('Name') or 'Unknown'}")
    print(f" Folder      {item.get('FolderPath') or 'Unknown'}")
    print(f" Full Path   {item.get('FullName') or 'Unknown'}")
    print(f" Extension   {item.get('Extension') or 'Unknown'}")
    print(f" Size        {item.get('Length') if item.get('Length') is not None else 'Unknown'}")
    print(f" Modified    {item.get('LastWriteTimeUtc') or 'Unknown'}")
    print(f" Target      {item.get('TargetPath') or 'Unknown'}")
    print(f" Arguments   {item.get('Arguments') or 'None'}")
    print(f" Working Dir {item.get('WorkingDirectory') or 'Unknown'}")


def network_listener_name(listener):
    protocol = listener.get("Protocol") or "Unknown"
    address = listener.get("LocalAddress") or "Unknown"
    port = listener.get("LocalPort") if listener.get("LocalPort") is not None else "Unknown"
    return f"{protocol} {address}:{port}"


def print_network_listener(listener):
    print(bold(network_listener_name(listener)))
    print()
    print(f" Protocol    {listener.get('Protocol') or 'Unknown'}")
    print(f" Address     {listener.get('LocalAddress') or 'Unknown'}")
    print(f" Port        {listener.get('LocalPort') if listener.get('LocalPort') is not None else 'Unknown'}")
    print(f" State       {listener.get('State') or 'Unknown'}")
    print(f" PID         {listener.get('OwningProcess') if listener.get('OwningProcess') is not None else 'Unknown'}")
    print(f" Process     {listener.get('ProcessName') or 'Unknown'}")
    print(f" Path        {listener.get('ProcessPath') or 'Unknown'}")
    print(f" Services    {format_listener_value(listener.get('ServiceNames'))}")


def local_user_name(user):
    return user.get("Name") or "Unknown"


def print_local_user(user):
    print(bold(local_user_name(user)))
    print()
    print(f" Name        {user.get('Name') or 'Unknown'}")
    print(f" SID         {user.get('SID') or 'Unknown'}")
    print(f" Enabled     {user.get('Enabled')}")
    print(f" Local       {user.get('LocalAccount')}")
    print(f" Pwd Req     {user.get('PasswordRequired')}")
    print(f" Pwd Expires {user.get('PasswordExpires')}")
    print(f" Last Logon  {user.get('LastLogon') or 'Unknown'}")
    print(f" Description {user.get('Description') or 'Unknown'}")


def local_group_name(item):
    return item.get("Group") or "Unknown"


def print_local_group(item):
    print(bold(local_group_name(item)))
    print()
    members = item.get("Members") or []
    if not members:
        print(" Members     None")
    else:
        print(" Members")
        for m in members:
            print(f"  - {m}")


def firewall_rule_name(rule):
    return rule.get("Name") or "Unknown"


def print_firewall_rule(rule):
    print(bold(firewall_rule_name(rule)))
    print()
    print(f" Direction   {rule.get('Direction') or 'Unknown'}")
    print(f" Action      {rule.get('Action') or 'Unknown'}")
    print(f" Enabled     {rule.get('Enabled')}")
    print(f" Protocol    {rule.get('Protocol') or 'Unknown'}")
    print(f" Local Port  {rule.get('LocalPort') or 'Unknown'}")
    print(f" Remote Port {rule.get('RemotePort') or 'Unknown'}")
    print(f" Program     {rule.get('Program') or 'Unknown'}")
    print(f" Profiles    {rule.get('Profiles') or 'Unknown'}")


def software_name(item):
    name = item.get("DisplayName") or "Unknown"
    version = item.get("DisplayVersion")
    return f"{name} ({version})" if version else name


def print_installed_software(item):
    print(bold(software_name(item)))
    print()
    print(f" Name        {item.get('DisplayName') or 'Unknown'}")
    print(f" Version     {item.get('DisplayVersion') or 'Unknown'}")
    print(f" Publisher   {item.get('Publisher') or 'Unknown'}")
    print(f" Install Date {item.get('InstallDate') or 'Unknown'}")
    print(f" Location    {item.get('InstallLocation') or 'Unknown'}")
    print(f" Uninstall   {item.get('UninstallString') or 'Unknown'}")


def new_services_with_new_listeners(service_diff, listener_diff):
    correlations = []
    added_services = service_diff.get("added", [])
    added_listeners = listener_diff.get("added", [])

    for service in added_services:
        service_name_value = service.get("Name")
        service_pid = service.get("ProcessId")
        for listener in added_listeners:
            service_names = listener_values(listener.get("ServiceNames"))
            listener_pid = listener.get("OwningProcess")
            name_matches = service_name_value and service_name_value in service_names
            pid_matches = service_pid and service_pid != 0 and service_pid == listener_pid
            if name_matches or pid_matches:
                correlations.append((service, listener))

    return correlations

def task_values(value):
    if value is None or value == "":
        return ["None"]
    if isinstance(value, list):
        return [str(item) for item in value] or ["None"]
    return [str(value)]


def format_task_value(value):
    return "; ".join(task_values(value))


def listener_values(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def format_listener_value(value):
    values = listener_values(value)
    if not values:
        return "None"
    return ", ".join(values)


def new_allow_inbound_rules_with_new_listeners(firewall_diff, listener_diff):
    pairs = []
    added_rules = firewall_diff.get("added", [])
    added_listeners = listener_diff.get("added", [])

    for rule_item in added_rules:
        if (rule_item.get("Direction") or "").lower() != "inbound":
            continue
        if (rule_item.get("Action") or "").lower() != "allow":
            continue
        rule_proto = (rule_item.get("Protocol") or "Any").upper()
        rule_port_spec = (rule_item.get("LocalPort") or "Any")
        for listener in added_listeners:
            if firewall_listener_matches(rule_proto, rule_port_spec, listener):
                pairs.append((rule_item, listener))
    return pairs


def firewall_listener_matches(rule_proto, rule_port_spec, listener):
    lst_proto = (listener.get("Protocol") or "").upper()
    if rule_proto not in ("ANY", lst_proto):
        return False
    lst_port_val = listener.get("LocalPort")
    try:
        port = int(lst_port_val) if lst_port_val is not None else None
    except Exception:
        port = None
    spec = str(rule_port_spec or "Any")
    if spec.lower() == "any":
        return True
    for token in spec.split(','):
        token = token.strip()
        if not token:
            continue
        if '-' in token:
            a, b = token.split('-', 1)
            try:
                start = int(a); end = int(b)
            except Exception:
                continue
            if port is not None and start <= port <= end:
                return True
        else:
            try:
                if port is not None and int(token) == port:
                    return True
            except Exception:
                continue
    return False
