import ctypes
from ctypes import wintypes

from winsnap.collectors.network_listeners import _PROCESSENTRY32W

# ---------------------------------------------------------------------------
# Native process collection via toolhelp snapshot (PID, parent PID, name),
# QueryFullProcessImageNameW (executable path), and NtQueryInformationProcess
# (command line). Replaces the previous Get-CimInstance Win32_Process
# PowerShell round-trip.
# ---------------------------------------------------------------------------

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

_PROCESS_COMMAND_LINE_INFORMATION = 60
_CMDLINE_BUFFER_SIZE = 0x10000


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", ctypes.c_void_p),
    ]


_kernel32 = ctypes.windll.kernel32
_ntdll = ctypes.windll.ntdll

_kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
_kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
_kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
_kernel32.Process32FirstW.restype = wintypes.BOOL
_kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
_kernel32.Process32NextW.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
]
_kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

_ntdll.NtQueryInformationProcess.argtypes = [
    wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG),
]
_ntdll.NtQueryInformationProcess.restype = ctypes.c_long

_INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def _enumerate_processes():
    entries = []
    snap = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == _INVALID_HANDLE_VALUE:
        return entries
    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
        if _kernel32.Process32FirstW(snap, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile
                if entry.th32ProcessID == 0 and name == "[System Process]":
                    name = "System Idle Process"
                entries.append((entry.th32ProcessID, entry.th32ParentProcessID, name))
                if not _kernel32.Process32NextW(snap, ctypes.byref(entry)):
                    break
    finally:
        _kernel32.CloseHandle(snap)
    return entries


def _process_details(pid):
    """Return (executable_path, command_line) for a process, or (None, None)."""
    handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None, None
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        executable_path = None
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            executable_path = buf.value

        command_line = None
        raw = (ctypes.c_ubyte * _CMDLINE_BUFFER_SIZE)()
        returned = wintypes.ULONG()
        status = _ntdll.NtQueryInformationProcess(
            handle, _PROCESS_COMMAND_LINE_INFORMATION, raw, _CMDLINE_BUFFER_SIZE, ctypes.byref(returned)
        )
        if status == 0:
            us = _UNICODE_STRING.from_buffer(raw)
            if us.Length:
                header = ctypes.sizeof(_UNICODE_STRING)
                command_line = bytes(raw[header:header + us.Length]).decode("utf-16-le", errors="replace")

        return executable_path, command_line
    finally:
        _kernel32.CloseHandle(handle)


def collect_processes():
    results = []
    for pid, ppid, name in _enumerate_processes():
        executable_path, command_line = _process_details(pid)
        results.append({
            "ProcessId": pid,
            "ParentProcessId": ppid,
            "Name": name,
            "ExecutablePath": executable_path,
            "CommandLine": command_line,
        })

    results.sort(key=lambda r: r["ProcessId"])
    return results
