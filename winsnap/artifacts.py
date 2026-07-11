from dataclasses import dataclass, field

from winsnap.collectors import collect_network_listeners, collect_processes, collect_registry_autoruns, collect_scheduled_tasks, collect_services, collect_startup_folders
from winsnap.collectors.installed_software import collect_installed_software
from winsnap.collectors.firewall_rules import collect_firewall_rules
from winsnap.differ import diff_firewall_rules, diff_installed_software, diff_network_listeners, diff_processes, diff_registry_autoruns, diff_scheduled_tasks, diff_services, diff_startup_folders
from winsnap.views.diff_view import autorun_name, network_listener_name, print_firewall_rule, print_installed_software, print_network_listener, print_registry_autorun, print_scheduled_task, print_service, print_startup_item, process_name, service_name, software_name, startup_item_name, task_name, firewall_rule_name
from winsnap.views.process_view import print_process


@dataclass(frozen=True)
class Artifact:
    key: str
    label: str
    short_label: str
    matching_label: str
    inspect_section_label: str
    detail_section_label: str
    collect: object
    diff: object
    search_fields: tuple[str, ...]
    name: object
    print_item: object
    summary_fields: tuple[tuple[str, str], ...] = field(default_factory=tuple)


ARTIFACTS = [
    Artifact(
        key="processes",
        label="Processes",
        short_label="Proc",
        matching_label="Matching processes",
        inspect_section_label="Process Names",
        detail_section_label="Process Instances",
        collect=collect_processes,
        diff=diff_processes,
        search_fields=("Name", "ExecutablePath", "CommandLine"),
        name=process_name,
        print_item=print_process,
    ),
    Artifact(
        key="services",
        label="Services",
        short_label="Svc",
        matching_label="Matching services",
        inspect_section_label="Services",
        detail_section_label="Service Entries",
        collect=collect_services,
        diff=diff_services,
        search_fields=("Name", "DisplayName", "State", "Status", "StartMode", "StartName", "PathName"),
        name=service_name,
        print_item=print_service,
        summary_fields=(("Service States", "State"), ("Service Start Modes", "StartMode")),
    ),
    Artifact(
        key="scheduled_tasks",
        label="Scheduled Tasks",
        short_label="Task",
        matching_label="Matching tasks",
        inspect_section_label="Scheduled Tasks",
        detail_section_label="Scheduled Task Entries",
        collect=collect_scheduled_tasks,
        diff=diff_scheduled_tasks,
        search_fields=("TaskName", "TaskPath", "State", "Author", "RunAsUser", "Triggers", "Actions"),
        name=task_name,
        print_item=print_scheduled_task,
        summary_fields=(("Scheduled Task States", "State"),),
    ),
    Artifact(
        key="registry_autoruns",
        label="Registry Autoruns",
        short_label="Run",
        matching_label="Matching autoruns",
        inspect_section_label="Registry Autoruns",
        detail_section_label="Registry Autorun Entries",
        collect=collect_registry_autoruns,
        diff=diff_registry_autoruns,
        search_fields=("Hive", "KeyPath", "ValueName", "Value"),
        name=autorun_name,
        print_item=print_registry_autorun,
        summary_fields=(("Registry Autorun Hives", "Hive"),),
    ),
    Artifact(
        key="startup_folders",
        label="Startup Folders",
        short_label="Start",
        matching_label="Matching startup",
        inspect_section_label="Startup Items",
        detail_section_label="Startup Folder Entries",
        collect=collect_startup_folders,
        diff=diff_startup_folders,
        search_fields=("Scope", "FolderPath", "Name", "FullName", "Extension", "TargetPath", "Arguments", "WorkingDirectory"),
        name=startup_item_name,
        print_item=print_startup_item,
        summary_fields=(("Startup Item Scopes", "Scope"),),
    ),
    Artifact(
        key="installed_software",
        label="Installed Software",
        short_label="Soft",
        matching_label="Matching software",
        inspect_section_label="Installed Software",
        detail_section_label="Installed Software Entries",
        collect=collect_installed_software,
        diff=diff_installed_software,
        search_fields=("DisplayName", "DisplayVersion", "Publisher", "InstallLocation", "UninstallString", "KeyPath", "PackageId"),
        name=software_name,
        print_item=print_installed_software,
        summary_fields=(("Publishers", "Publisher"),),
    ),
    Artifact(
        key="firewall_rules",
        label="Firewall Rules",
        short_label="FW",
        matching_label="Matching firewall rules",
        inspect_section_label="Firewall Rules",
        detail_section_label="Firewall Rule Entries",
        collect=collect_firewall_rules,
        diff=diff_firewall_rules,
        search_fields=("Name", "Direction", "Action", "Protocol", "LocalPort", "RemotePort", "Program", "Profiles"),
        name=firewall_rule_name,
        print_item=print_firewall_rule,
        summary_fields=(("Directions", "Direction"), ("Actions", "Action")),
    ),
    Artifact(
        key="network_listeners",
        label="Network Listeners",
        short_label="Net",
        matching_label="Matching listeners",
        inspect_section_label="Network Listeners",
        detail_section_label="Network Listener Entries",
        collect=collect_network_listeners,
        diff=diff_network_listeners,
        search_fields=("Protocol", "LocalAddress", "LocalPort", "State", "OwningProcess", "ProcessName", "ProcessPath", "ServiceNames"),
        name=network_listener_name,
        print_item=print_network_listener,
        summary_fields=(("Network Listener Protocols", "Protocol"),),
    ),
]

ARTIFACTS_BY_KEY = {artifact.key: artifact for artifact in ARTIFACTS}


def artifact_matches(artifact, item, query):
    query = query.lower()
    return any(query in str(item.get(field)).lower() for field in artifact.search_fields if item.get(field) is not None)


def matching_items(snapshot, artifact, query):
    return [
        item
        for item in snapshot.get(artifact.key, [])
        if artifact_matches(artifact, item, query)
    ]
