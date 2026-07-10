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


def scheduled_task_risk_hints(task):
    hints = []
    state = str(task.get("State") or "").lower()
    run_as_user = str(task.get("RunAsUser") or "").lower()
    triggers = " ".join(list_values(task.get("Triggers"))).lower()
    actions = " ".join(list_values(task.get("Actions"))).lower().replace("/", "\\")

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


def registry_autorun_risk_hints(autorun):
    hints = []
    hive = str(autorun.get("Hive") or "").upper()
    key_path = str(autorun.get("KeyPath") or "").lower()
    value = str(autorun.get("Value") or "").lower().replace("/", "\\")

    if "\\runonce" in key_path:
        hints.append("RunOnce persistence location")
    elif "\\run" in key_path:
        hints.append("Run key persistence location")

    if hive == "HKLM":
        hints.append("Machine-wide autorun")

    if not value:
        hints.append("Missing/empty autorun command")
    elif any(marker in value for marker in suspicious_action_markers()):
        hints.append("Executes command or scripting host")

    if is_user_writable_path(value):
        hints.append("Autorun path in user-writable location")

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


def list_values(value):
    if value is None or value == "":
        return ["None"]
    if isinstance(value, list):
        return [str(item) for item in value] or ["None"]
    return [str(value)]
