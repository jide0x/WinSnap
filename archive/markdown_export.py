from collections import Counter
from datetime import datetime
from pathlib import Path

from archive.risk_hints import service_risk_hints
from winsnap.views.diff_view import service_name
from winsnap.version import VERSION


# Archived prototype. This module is intentionally not wired into the active CLI.


REPORT_DIR = Path("reports")


def default_diff_report_path(before_name, after_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    before = safe_filename(before_name or "before")
    after = safe_filename(after_name or "after")
    return REPORT_DIR / f"{before}_vs_{after}_{timestamp}.md"


def export_diff_markdown(before, after, diff, export_path):
    path = Path(export_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(render_diff_markdown(before, after, diff), encoding="utf-8")
    return path


def render_diff_markdown(before, after, diff):
    process_diff = diff["processes"]
    service_diff = diff["services"]
    added_processes = process_diff["added"]
    removed_processes = process_diff["removed"]
    added_services = service_diff["added"]
    removed_services = service_diff["removed"]
    changed_services = service_diff["changed"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# WinSnap Difference Report",
        "",
        f"Before: {md_inline(before.get('name', 'Unknown'))}",
        f"After: {md_inline(after.get('name', 'Unknown'))}",
        "",
        "Generated",
        f"- Date: {generated_at}",
        f"- WinSnap Version: {VERSION}",
        f"- Collector(s): {collector_list(after)}",
        "",
        "---",
        "",
        "# Executive Summary",
        "",
        "Overall Changes",
        "",
        "| Category | Added | Removed | Changed |",
        "|----------|------:|--------:|--------:|",
        f"| Processes | {len(added_processes)} | {len(removed_processes)} | - |",
        f"| Services | {len(added_services)} | {len(removed_services)} | {len(changed_services)} |",
        "",
        "Most Significant Changes",
        "",
    ]

    significant_changes = most_significant_changes(diff)
    if significant_changes:
        lines.extend(f"- {change}" for change in significant_changes)
    else:
        lines.append("- No process or service changes detected.")

    lines.extend([
        "",
        "---",
        "",
        "# Risk Indicators",
        "",
    ])
    lines.extend(risk_indicator_section(diff))

    append_services(lines, "# Added Services", added_services)
    append_services(lines, "# Removed Services", removed_services)
    append_changed_services(lines, changed_services)
    append_processes(lines, "# Added Processes", added_processes)
    append_processes(lines, "# Removed Processes", removed_processes)
    append_metadata(lines, before, after)
    append_lab_notes(lines)

    return "\n".join(lines).rstrip() + "\n"


def collector_list(snapshot):
    collectors = snapshot.get("collector") or snapshot.get("collectors") or []
    if not collectors:
        return "Unknown"
    return ", ".join(str(collector).title() for collector in collectors)


def most_significant_changes(diff):
    changes = []
    service_diff = diff["services"]
    process_diff = diff["processes"]

    for service in service_diff["added"][:5]:
        changes.append(f"New service installed: {service_name(service)}")

    for item in service_diff["changed"][:5]:
        fields = ", ".join(item["changes"].keys())
        changes.append(f"Service changed: {service_name(item['after'])} ({fields})")

    added_counts = Counter(process_name(process) for process in process_diff["added"])
    removed_counts = Counter(process_name(process) for process in process_diff["removed"])
    changed_process_names = sorted(
        added_counts.keys() | removed_counts.keys(),
        key=lambda name: (-(added_counts[name] + removed_counts[name]), name.lower()),
    )

    for name in changed_process_names[:5]:
        added = added_counts[name]
        removed = removed_counts[name]
        if added and removed:
            changes.append(f"{name} process instances changed (+{added} / -{removed}).")
        elif added:
            changes.append(f"{name} process count increased by {added}.")
        else:
            changes.append(f"{name} process count decreased by {removed}.")

    return changes[:10]


def risk_indicator_section(diff):
    lines = []
    services = list(diff["services"]["added"])
    services.extend(item["after"] for item in diff["services"]["changed"])

    risky_services = [(service, service_risk_hints(service)) for service in services]
    risky_services = [(service, hints) for service, hints in risky_services if hints]

    if not risky_services:
        return ["No service risk indicators found.", ""]

    for service, hints in risky_services:
        lines.extend([
            f"## {md_inline(service_name(service))}",
            "",
        ])
        lines.extend(f"- Warning: {hint}" for hint in hints)
        lines.extend([
            "",
            "Reason",
            "",
            risk_reason(hints),
            "",
            "---",
            "",
        ])

    return lines


def risk_reason(hints):
    reasons = []
    if "Auto-start service" in hints:
        reasons.append("is configured to start automatically")
    if "Runs as LocalSystem" in hints:
        reasons.append("executes using the LocalSystem account")
    if "Path in user-writable location" in hints:
        reasons.append("runs from a user-writable path")
    if "Missing/unknown PathName" in hints:
        reasons.append("has a missing or unknown service path")

    if not reasons:
        return "This service has properties that may deserve closer review."

    return "This service " + join_reasons(reasons) + "."


def join_reasons(reasons):
    if len(reasons) == 1:
        return reasons[0]
    if len(reasons) == 2:
        return f"{reasons[0]} and {reasons[1]}"
    return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"


def append_services(lines, title, services):
    lines.extend(["---", "", title, ""])
    if not services:
        lines.extend(["No services.", ""])
        return

    for service in services:
        lines.extend([
            f"## {md_inline(service_name(service))}",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| Name | {md_table(service.get('Name') or 'Unknown')} |",
            f"| State | {md_table(service.get('State') or 'Unknown')} |",
            f"| Start Mode | {md_table(service.get('StartMode') or 'Unknown')} |",
            f"| Account | {md_table(service.get('StartName') or 'Unknown')} |",
            f"| Path | {md_table(service.get('PathName') or 'Unknown')} |",
            "",
        ])


def append_changed_services(lines, changed_services):
    lines.extend(["---", "", "# Changed Services", ""])
    if not changed_services:
        lines.extend(["No changed services.", ""])
        return

    for item in changed_services:
        lines.extend([
            f"## {md_inline(service_name(item['after']))}",
            "",
            "### Before",
            "",
        ])
        append_change_table(lines, item["changes"], "before")
        lines.extend(["", "### After", ""])
        append_change_table(lines, item["changes"], "after")
        lines.append("")


def append_change_table(lines, changes, side):
    lines.extend([
        "| Property | Value |",
        "|----------|-------|",
    ])
    for field, values in changes.items():
        lines.append(f"| {md_table(field)} | {md_table(values[side])} |")


def append_processes(lines, title, processes):
    lines.extend(["---", "", title, ""])
    if not processes:
        lines.extend(["No processes.", ""])
        return

    for process in processes:
        lines.extend([
            f"## {md_inline(process_name(process))}",
            "",
            "PID",
            f": {md_inline(process.get('ProcessId', 'Unknown'))}",
            "",
            "Parent PID",
            f": {md_inline(process.get('ParentProcessId', 'Unknown'))}",
            "",
            "Path",
            f": {md_inline(process.get('ExecutablePath') or 'Unknown')}",
            "",
            "Command",
            "",
            "```text",
            str(process.get("CommandLine") or "Unknown"),
            "```",
            "",
        ])


def append_metadata(lines, before, after):
    lines.extend([
        "---",
        "",
        "# Metadata",
        "",
        "Before Snapshot",
        "",
    ])
    append_snapshot_metadata(lines, before)
    lines.extend(["", "After Snapshot", ""])
    append_snapshot_metadata(lines, after)
    lines.append("")


def append_snapshot_metadata(lines, snapshot):
    lines.extend([
        f"- Hostname: {md_inline(snapshot.get('hostname') or 'Unknown')}",
        f"- Username: {md_inline(snapshot.get('username') or 'Unknown')}",
        f"- Windows Version: {md_inline(snapshot.get('windows_version') or 'Unknown')}",
        f"- Note: {md_inline(snapshot.get('note') or '')}",
    ])


def append_lab_notes(lines):
    lines.extend([
        "---",
        "",
        "# Lab Notes",
        "",
        "Purpose",
        "",
        "Expected Changes",
        "",
        "Unexpected Findings",
        "",
        "Questions",
        "",
    ])


def process_name(process):
    return process.get("Name") or "Unknown"


def md_inline(value):
    return str(value).replace("\n", " ")


def md_table(value):
    return md_inline(value).replace("|", "\\|")


def safe_filename(value):
    safe = []
    for character in str(value):
        if character.isalnum() or character in {"-", "_"}:
            safe.append(character)
        else:
            safe.append("_")
    return "".join(safe).strip("_") or "snapshot"
