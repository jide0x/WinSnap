import ctypes
from ctypes import wintypes
import re
import subprocess

from winsnap.collectors import taskscheduler

# ---------------------------------------------------------------------------
# Scheduled task collection: definitions are parsed from a single
# `schtasks /query /xml` dump (author, run-as user, triggers, actions), while
# the runtime Ready/Disabled/Running state comes from the Task Scheduler COM
# API (taskscheduler.enumerate_tasks). Replaces the previous Get-ScheduledTask
# PowerShell round-trip.
# ---------------------------------------------------------------------------

_SCHTASKS_TIMEOUT = 30

_TASK_STATE_NAMES = {
    0: "Unknown",
    1: "Disabled",
    2: "Queued",
    3: "Ready",
    4: "Running",
}

_WELL_KNOWN_TRIGGER_CLASS = {
    "BootTrigger": "MSFT_TaskBootTrigger",
    "LogonTrigger": "MSFT_TaskLogonTrigger",
    "IdleTrigger": "MSFT_TaskIdleTrigger",
    "RegistrationTrigger": "MSFT_TaskRegistrationTrigger",
    "SessionStateChangeTrigger": "MSFT_TaskSessionStateChangeTrigger",
    "EventTrigger": "MSFT_TaskEventTrigger",
    "TimeTrigger": "MSFT_TaskTimeTrigger",
    "WnfStateChangeTrigger": "MSFT_TaskTrigger",
}

_advapi32 = ctypes.windll.advapi32
_kernel32 = ctypes.windll.kernel32
_shlwapi = ctypes.windll.shlwapi

_advapi32.ConvertStringSidToSidW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]
_advapi32.ConvertStringSidToSidW.restype = wintypes.BOOL
_advapi32.LookupAccountSidW.argtypes = [
    wintypes.LPCWSTR, ctypes.c_void_p, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
]
_advapi32.LookupAccountSidW.restype = wintypes.BOOL
_kernel32.LocalFree.argtypes = [ctypes.c_void_p]
_kernel32.LocalFree.restype = ctypes.c_void_p

_shlwapi.SHLoadIndirectString.argtypes = [
    wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, ctypes.c_void_p,
]
_shlwapi.SHLoadIndirectString.restype = wintypes.HRESULT


def _trigger_class(trigger_type, block):
    if trigger_type == "CalendarTrigger":
        if "ScheduleByDay" in block:
            return "MSFT_TaskDailyTrigger"
        if "ScheduleByWeek" in block:
            return "MSFT_TaskWeeklyTrigger"
        return "MSFT_TaskTrigger"
    return _WELL_KNOWN_TRIGGER_CLASS.get(trigger_type, "MSFT_TaskTrigger")


def _collapse(values):
    """Reproduce ConvertTo-Json's scalar/array/object collapse for a list."""
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return {"value": values, "Count": len(values)}


def _sid_to_name(sid):
    if not sid or not sid.startswith("S-1-"):
        return sid
    psid = ctypes.c_void_p()
    if not _advapi32.ConvertStringSidToSidW(sid, ctypes.byref(psid)):
        return sid
    try:
        name_size = wintypes.DWORD()
        domain_size = wintypes.DWORD()
        use = wintypes.DWORD()
        _advapi32.LookupAccountSidW(
            None, psid, None, ctypes.byref(name_size), None, ctypes.byref(domain_size), ctypes.byref(use)
        )
        if not name_size.value:
            return sid
        name = ctypes.create_unicode_buffer(name_size.value)
        domain = ctypes.create_unicode_buffer(domain_size.value)
        if not _advapi32.LookupAccountSidW(
            None, psid, name, ctypes.byref(name_size), domain, ctypes.byref(domain_size), ctypes.byref(use)
        ):
            return sid
        return name.value
    finally:
        _kernel32.LocalFree(psid)


def _resolve_author(author):
    """Resolve a "$(@dll,-id)" author string, leaving plain text and failures raw."""
    if not author:
        return None
    if author.startswith("$(@") and author.endswith(")"):
        inner = author[2:-1]
        buf = ctypes.create_unicode_buffer(1024)
        try:
            hr = _shlwapi.SHLoadIndirectString(inner, buf, 1024, None)
        except Exception:
            return author
        if hr == 0 and buf.value:
            return buf.value
    return author


def _split_task_path(path):
    idx = path.rfind("\\")
    return path[: idx + 1], path[idx + 1 :]


def _run_schtasks(args):
    result = subprocess.run(args, capture_output=True, timeout=_SCHTASKS_TIMEOUT)
    if result.returncode != 0:
        return ""
    raw = result.stdout
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def collect_scheduled_tasks():
    xml_text = _run_schtasks(["schtasks", "/query", "/xml"])

    state_by_path = {}
    for path, name, state in taskscheduler.enumerate_tasks():
        state_by_path[path] = state

    tasks = re.findall(r"<Task\b.*?</Task>", xml_text, re.DOTALL)

    results = []
    for task_xml in tasks:
        uri_match = re.search(r"<URI>(.*?)</URI>", task_xml)
        if not uri_match:
            continue
        full_path = uri_match.group(1)
        task_path, task_name = _split_task_path(full_path)

        author_match = re.search(r"<Author>(.*?)</Author>", task_xml, re.DOTALL)
        author = _resolve_author(author_match.group(1).strip()) if author_match else None

        run_as_user = None
        if not re.search(r"<GroupId>", task_xml):
            user_match = re.search(r"<UserId>(.*?)</UserId>", task_xml, re.DOTALL)
            if user_match:
                run_as_user = _sid_to_name(user_match.group(1).strip())

        trigger_classes = []
        for tm in re.finditer(r"<(\w+Trigger)\b([^>]*)>", task_xml):
            trigger_type = tm.group(1)
            if tm.group(2).rstrip().endswith("/"):
                block = ""
            else:
                close = task_xml.find("</" + trigger_type + ">", tm.end())
                block = task_xml[tm.start(): close + len(trigger_type) + 3] if close != -1 else ""
            trigger_classes.append(_trigger_class(trigger_type, block))

        action_strings = []
        for am in re.finditer(r"<Exec>.*?</Exec>", task_xml, re.DOTALL):
            block = am.group(0)
            cmd = re.search(r"<Command>(.*?)</Command>", block, re.DOTALL)
            if not cmd:
                continue
            value = cmd.group(1).strip()
            arg = re.search(r"<Arguments>(.*?)</Arguments>", block, re.DOTALL)
            if arg and arg.group(1).strip():
                value = f"{value} {arg.group(1).strip()}"
            action_strings.append(value)

        state_value = state_by_path.get(full_path)
        if state_value is not None:
            state = _TASK_STATE_NAMES.get(state_value, "Ready")
        else:
            state = "Disabled" if re.search(r"<Enabled>false</Enabled>", task_xml) else "Ready"

        results.append({
            "TaskName": task_name,
            "TaskPath": task_path,
            "State": state,
            "Author": author,
            "RunAsUser": run_as_user,
            "Triggers": _collapse(trigger_classes),
            "Actions": _collapse(action_strings) if action_strings else None,
        })

    results.sort(key=lambda r: (r["TaskPath"].lower(), r["TaskName"].lower()))
    return results
