from __future__ import annotations

import ctypes
import socket
from ctypes import wintypes
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Native network listener collection.
#
# Replaces the previous Get-NetTCPConnection / Get-NetUDPEndpoint PowerShell
# round-trip with direct iphlpapi table enumeration (GetExtendedTcpTable /
# GetExtendedUdpTable). Process names come from a toolhelp snapshot, process
# paths from QueryFullProcessImageNameW, and service ownership from the
# Service Control Manager (EnumServicesStatusExW).
# ---------------------------------------------------------------------------

AF_INET = 2
AF_INET6 = 23
TCP_TABLE_OWNER_PID_ALL = 5
UDP_TABLE_OWNER_PID = 1
MIB_TCP_STATE_LISTEN = 2

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TH32CS_SNAPPROCESS = 0x00000002
MAX_PATH = 260

SC_MANAGER_ENUMERATE_SERVICE = 0x0004
SERVICE_WIN32 = 0x00000030
SC_ENUM_PROCESS_INFO = 0


# --- iphlpapi table structures ---


class _MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("dwState", wintypes.DWORD),
        ("dwLocalAddr", wintypes.DWORD),
        ("dwLocalPort", wintypes.DWORD),
        ("dwRemoteAddr", wintypes.DWORD),
        ("dwRemotePort", wintypes.DWORD),
        ("dwOwningPid", wintypes.DWORD),
    ]


class _MIB_TCP6ROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("ucLocalAddr", ctypes.c_ubyte * 16),
        ("dwLocalScopeId", wintypes.DWORD),
        ("dwLocalPort", wintypes.DWORD),
        ("ucRemoteAddr", ctypes.c_ubyte * 16),
        ("dwRemoteScopeId", wintypes.DWORD),
        ("dwRemotePort", wintypes.DWORD),
        ("dwState", wintypes.DWORD),
        ("dwOwningPid", wintypes.DWORD),
    ]


class _MIB_UDPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("dwLocalAddr", wintypes.DWORD),
        ("dwLocalPort", wintypes.DWORD),
        ("dwOwningPid", wintypes.DWORD),
    ]


class _MIB_UDP6ROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("ucLocalAddr", ctypes.c_ubyte * 16),
        ("dwLocalScopeId", wintypes.DWORD),
        ("dwLocalPort", wintypes.DWORD),
        ("dwOwningPid", wintypes.DWORD),
    ]


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * MAX_PATH),
    ]


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


# --- DLL binding ---

_iphlpapi = ctypes.windll.iphlpapi
_kernel32 = ctypes.windll.kernel32
_advapi32 = ctypes.windll.advapi32

_iphlpapi.GetExtendedTcpTable.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.BOOL,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
]
_iphlpapi.GetExtendedTcpTable.restype = wintypes.DWORD
_iphlpapi.GetExtendedUdpTable.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.BOOL,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
]
_iphlpapi.GetExtendedUdpTable.restype = wintypes.DWORD

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
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
_kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

_advapi32.OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
_advapi32.OpenSCManagerW.restype = wintypes.HANDLE
_advapi32.EnumServicesStatusExW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPCWSTR,
]
_advapi32.EnumServicesStatusExW.restype = wintypes.BOOL
_advapi32.CloseServiceHandle.argtypes = [wintypes.HANDLE]
_advapi32.CloseServiceHandle.restype = wintypes.BOOL

_INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


# --- Helpers ---


def _ipv4_to_str(addr: int) -> str:
    return socket.inet_ntop(socket.AF_INET, addr.to_bytes(4, "little"))


def _ipv6_to_str(addr, scope_id: int = 0) -> str:
    text = socket.inet_ntop(socket.AF_INET6, bytes(addr))
    if scope_id:
        text = f"{text}%{scope_id}"
    return text


def _port_to_int(port: int) -> int:
    return socket.ntohs(port & 0xFFFF)


def _tcp_rows():
    """Return (protocol, address, port, state, pid) rows for listening sockets."""
    rows = []
    for af, row_type in ((AF_INET, _MIB_TCPROW_OWNER_PID), (AF_INET6, _MIB_TCP6ROW_OWNER_PID)):
        size = wintypes.DWORD()
        _iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), False, af, TCP_TABLE_OWNER_PID_ALL, 0)
        if not size.value:
            continue
        buf = (ctypes.c_ubyte * size.value)()
        ret = _iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), False, af, TCP_TABLE_OWNER_PID_ALL, 0)
        if ret != 0:
            continue
        base = ctypes.addressof(buf)
        count = wintypes.DWORD.from_address(base).value
        first_row = base + 4
        row_size = ctypes.sizeof(row_type)
        for i in range(count):
            row = row_type.from_address(first_row + i * row_size)
            if row.dwState != MIB_TCP_STATE_LISTEN:
                continue
            if af == AF_INET:
                addr = _ipv4_to_str(row.dwLocalAddr)
            else:
                addr = _ipv6_to_str(row.ucLocalAddr, row.dwLocalScopeId)
            rows.append(("TCP", addr, _port_to_int(row.dwLocalPort), "Listen", row.dwOwningPid))
    return rows


def _udp_rows():
    """Return (protocol, address, port, state, pid) rows for bound UDP endpoints."""
    rows = []
    for af, row_type in ((AF_INET, _MIB_UDPROW_OWNER_PID), (AF_INET6, _MIB_UDP6ROW_OWNER_PID)):
        size = wintypes.DWORD()
        _iphlpapi.GetExtendedUdpTable(None, ctypes.byref(size), False, af, UDP_TABLE_OWNER_PID, 0)
        if not size.value:
            continue
        buf = (ctypes.c_ubyte * size.value)()
        ret = _iphlpapi.GetExtendedUdpTable(buf, ctypes.byref(size), False, af, UDP_TABLE_OWNER_PID, 0)
        if ret != 0:
            continue
        base = ctypes.addressof(buf)
        count = wintypes.DWORD.from_address(base).value
        first_row = base + 4
        row_size = ctypes.sizeof(row_type)
        for i in range(count):
            row = row_type.from_address(first_row + i * row_size)
            if af == AF_INET:
                addr = _ipv4_to_str(row.dwLocalAddr)
            else:
                addr = _ipv6_to_str(row.ucLocalAddr, row.dwLocalScopeId)
            rows.append(("UDP", addr, _port_to_int(row.dwLocalPort), None, row.dwOwningPid))
    return rows


def _process_names() -> Dict[int, str]:
    snap = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == _INVALID_HANDLE_VALUE:
        return {}
    names: Dict[int, str] = {}
    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
        if _kernel32.Process32FirstW(snap, ctypes.byref(entry)):
            while True:
                names[entry.th32ProcessID] = entry.szExeFile
                if not _kernel32.Process32NextW(snap, ctypes.byref(entry)):
                    break
    finally:
        _kernel32.CloseHandle(snap)
    return names


def _process_path(pid: int) -> Optional[str]:
    if not pid:
        return None
    handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
        return None
    finally:
        _kernel32.CloseHandle(handle)


def _service_names_by_pid() -> Dict[int, List[str]]:
    scm = _advapi32.OpenSCManagerW(None, None, SC_MANAGER_ENUMERATE_SERVICE)
    if not scm:
        return {}
    mapping: Dict[int, List[str]] = {}
    try:
        needed = wintypes.DWORD()
        returned = wintypes.DWORD()
        resume = wintypes.DWORD()
        _advapi32.EnumServicesStatusExW(
            scm, SC_ENUM_PROCESS_INFO, SERVICE_WIN32, 3, None, 0,
            ctypes.byref(needed), ctypes.byref(returned), ctypes.byref(resume), None,
        )
        if not needed.value:
            return mapping
        buf = (ctypes.c_ubyte * needed.value)()
        ok = _advapi32.EnumServicesStatusExW(
            scm, SC_ENUM_PROCESS_INFO, SERVICE_WIN32, 3, buf, needed.value,
            ctypes.byref(needed), ctypes.byref(returned), ctypes.byref(resume), None,
        )
        if not ok:
            return mapping
        base = ctypes.addressof(buf)
        size = ctypes.sizeof(_ENUM_SERVICE_STATUS_PROCESS)
        for i in range(returned.value):
            entry = _ENUM_SERVICE_STATUS_PROCESS.from_address(base + i * size)
            pid = entry.ServiceStatusProcess.dwProcessId
            if pid and entry.lpServiceName:
                mapping.setdefault(pid, []).append(entry.lpServiceName)
    finally:
        _advapi32.CloseServiceHandle(scm)
    return mapping


def collect_network_listeners():
    rows = _tcp_rows() + _udp_rows()

    pids = {row[4] for row in rows if row[4]}
    names = _process_names()
    services_by_pid = _service_names_by_pid()

    paths: Dict[int, Optional[str]] = {}
    for pid in pids:
        paths[pid] = _process_path(pid)

    results = []
    for protocol, addr, port, state, pid in rows:
        service_names = services_by_pid.get(pid, [])
        results.append({
            "Protocol": protocol,
            "LocalAddress": addr,
            "LocalPort": port,
            "State": state,
            "OwningProcess": pid,
            "ProcessName": names.get(pid),
            "ProcessPath": paths.get(pid),
            "ServiceNames": sorted(service_names),
        })

    results.sort(key=lambda r: (r["Protocol"], r["LocalAddress"], r["LocalPort"], r["OwningProcess"]))
    return results
