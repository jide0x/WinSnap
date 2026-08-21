import ctypes
from ctypes import wintypes

# ---------------------------------------------------------------------------
# Native service collection via the Service Control Manager (advapi32).
#
# Replaces the previous `Get-CimInstance Win32_Service` PowerShell round-trip
# with EnumServicesStatusExW (name, display name, state, pid) plus
# QueryServiceConfigW (start type, start name, binary path) per service.
# ---------------------------------------------------------------------------

SC_MANAGER_ENUMERATE_SERVICE = 0x0004
SERVICE_QUERY_CONFIG = 0x0001
SC_ENUM_PROCESS_INFO = 0
SERVICE_WIN32 = 0x30
SERVICE_STATE_ALL = 0x3

SERVICE_STOPPED = 1
SERVICE_START_PENDING = 2
SERVICE_STOP_PENDING = 3
SERVICE_RUNNING = 4
SERVICE_CONTINUE_PENDING = 5
SERVICE_PAUSE_PENDING = 6
SERVICE_PAUSED = 7

SERVICE_BOOT_START = 0
SERVICE_SYSTEM_START = 1
SERVICE_AUTO_START = 2
SERVICE_DEMAND_START = 3
SERVICE_DISABLED = 4

_STATE_NAMES = {
    SERVICE_STOPPED: "Stopped",
    SERVICE_START_PENDING: "Start Pending",
    SERVICE_STOP_PENDING: "Stop Pending",
    SERVICE_RUNNING: "Running",
    SERVICE_CONTINUE_PENDING: "Continue Pending",
    SERVICE_PAUSE_PENDING: "Pause Pending",
    SERVICE_PAUSED: "Paused",
}

_START_MODE_NAMES = {
    SERVICE_BOOT_START: "Boot",
    SERVICE_SYSTEM_START: "System",
    SERVICE_AUTO_START: "Auto",
    SERVICE_DEMAND_START: "Manual",
    SERVICE_DISABLED: "Disabled",
}


class _SERVICE_STATUS_PROCESS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD),
        ("dwProcessId", wintypes.DWORD),
        ("dwServiceFlags", wintypes.DWORD),
    ]


class _ENUM_SERVICE_STATUS_PROCESS(ctypes.Structure):
    _fields_ = [
        ("lpServiceName", wintypes.LPWSTR),
        ("lpDisplayName", wintypes.LPWSTR),
        ("ServiceStatusProcess", _SERVICE_STATUS_PROCESS),
    ]


class _QUERY_SERVICE_CONFIG(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwStartType", wintypes.DWORD),
        ("dwErrorControl", wintypes.DWORD),
        ("lpBinaryPathName", wintypes.LPWSTR),
        ("lpLoadOrderGroup", wintypes.LPWSTR),
        ("dwTagId", wintypes.DWORD),
        ("lpDependencies", wintypes.LPWSTR),
        ("lpServiceStartName", wintypes.LPWSTR),
        ("lpDisplayName", wintypes.LPWSTR),
    ]


_advapi32 = ctypes.windll.advapi32

_advapi32.OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
_advapi32.OpenSCManagerW.restype = wintypes.HANDLE
_advapi32.EnumServicesStatusExW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
    ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), wintypes.LPCWSTR,
]
_advapi32.EnumServicesStatusExW.restype = wintypes.BOOL
_advapi32.OpenServiceW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
_advapi32.OpenServiceW.restype = wintypes.HANDLE
_advapi32.QueryServiceConfigW.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
]
_advapi32.QueryServiceConfigW.restype = wintypes.BOOL
_advapi32.CloseServiceHandle.argtypes = [wintypes.HANDLE]
_advapi32.CloseServiceHandle.restype = wintypes.BOOL


def _service_config(scm, name):
    """Return (start_type, start_name, path_name) for a service, or None."""
    handle = _advapi32.OpenServiceW(scm, name, SERVICE_QUERY_CONFIG)
    if not handle:
        return None
    try:
        needed = wintypes.DWORD()
        _advapi32.QueryServiceConfigW(handle, None, 0, ctypes.byref(needed))
        if not needed.value:
            return None
        buf = (ctypes.c_ubyte * needed.value)()
        if not _advapi32.QueryServiceConfigW(handle, buf, needed.value, ctypes.byref(needed)):
            return None
        cfg = _QUERY_SERVICE_CONFIG.from_address(ctypes.addressof(buf))
        return (cfg.dwStartType, cfg.lpServiceStartName, cfg.lpBinaryPathName)
    finally:
        _advapi32.CloseServiceHandle(handle)


def collect_services():
    scm = _advapi32.OpenSCManagerW(None, None, SC_MANAGER_ENUMERATE_SERVICE)
    if not scm:
        return []
    try:
        needed = wintypes.DWORD()
        returned = wintypes.DWORD()
        resume = wintypes.DWORD()
        _advapi32.EnumServicesStatusExW(
            scm, SC_ENUM_PROCESS_INFO, SERVICE_WIN32, SERVICE_STATE_ALL,
            None, 0, ctypes.byref(needed), ctypes.byref(returned),
            ctypes.byref(resume), None,
        )
        if not needed.value:
            return []
        buf = (ctypes.c_ubyte * needed.value)()
        if not _advapi32.EnumServicesStatusExW(
            scm, SC_ENUM_PROCESS_INFO, SERVICE_WIN32, SERVICE_STATE_ALL,
            buf, needed.value, ctypes.byref(needed), ctypes.byref(returned),
            ctypes.byref(resume), None,
        ):
            return []

        base = ctypes.addressof(buf)
        size = ctypes.sizeof(_ENUM_SERVICE_STATUS_PROCESS)
        results = []
        for i in range(returned.value):
            entry = _ENUM_SERVICE_STATUS_PROCESS.from_address(base + i * size)
            name = entry.lpServiceName
            display_name = entry.lpDisplayName
            state = _STATE_NAMES.get(entry.ServiceStatusProcess.dwCurrentState, "Unknown")
            pid = entry.ServiceStatusProcess.dwProcessId

            cfg = _service_config(scm, name)
            if cfg is None:
                start_mode, start_name, path_name = "Unknown", None, None
            else:
                start_type, start_name, path_name = cfg
                start_mode = _START_MODE_NAMES.get(start_type, "Unknown")
                if not start_name:
                    start_name = None

            results.append({
                "Name": name,
                "DisplayName": display_name,
                "State": state,
                "Status": "OK",
                "StartMode": start_mode,
                "StartName": start_name,
                "PathName": path_name,
                "ProcessId": pid,
            })

        results.sort(key=lambda r: r["Name"].lower())
        return results
    finally:
        _advapi32.CloseServiceHandle(scm)
