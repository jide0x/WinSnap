import ctypes
from ctypes import wintypes
from datetime import datetime

# ---------------------------------------------------------------------------
# Native local user collection via Netapi32 (NetUserEnum level 3) plus
# advapi32 SID translation (LookupAccountNameW / ConvertSidToStringSidW).
#
# Replaces the previous Get-LocalUser / WMI PowerShell round-trip.
# ---------------------------------------------------------------------------

FILTER_NORMAL_ACCOUNT = 0x0002
MAX_PREFERRED_LENGTH = 0xFFFFFFFF

UF_ACCOUNTDISABLE = 0x0002
UF_PASSWD_NOTREQD = 0x0020
UF_DONT_EXPIRE_PASSWD = 0x10000


class _USER_INFO_3(ctypes.Structure):
    _fields_ = [
        ("usri3_name", wintypes.LPWSTR),
        ("usri3_password", wintypes.LPWSTR),
        ("usri3_password_age", wintypes.DWORD),
        ("usri3_priv", wintypes.DWORD),
        ("usri3_home_dir", wintypes.LPWSTR),
        ("usri3_comment", wintypes.LPWSTR),
        ("usri3_flags", wintypes.DWORD),
        ("usri3_script_path", wintypes.LPWSTR),
        ("usri3_auth_flags", wintypes.DWORD),
        ("usri3_full_name", wintypes.LPWSTR),
        ("usri3_usr_comment", wintypes.LPWSTR),
        ("usri3_parms", wintypes.LPWSTR),
        ("usri3_workstations", wintypes.LPWSTR),
        ("usri3_last_logon", wintypes.DWORD),
        ("usri3_last_logoff", wintypes.DWORD),
        ("usri3_acct_expires", wintypes.DWORD),
        ("usri3_max_storage", wintypes.DWORD),
        ("usri3_units_per_week", wintypes.DWORD),
        ("usri3_logon_hours", ctypes.POINTER(ctypes.c_ubyte)),
        ("usri3_bad_pw_count", wintypes.DWORD),
        ("usri3_num_logons", wintypes.DWORD),
        ("usri3_logon_server", wintypes.LPWSTR),
        ("usri3_country_code", wintypes.DWORD),
        ("usri3_code_page", wintypes.DWORD),
        ("usri3_user_id", wintypes.DWORD),
        ("usri3_primary_group_id", wintypes.DWORD),
        ("usri3_profile", wintypes.LPWSTR),
        ("usri3_home_dir_drive", wintypes.LPWSTR),
        ("usri3_password_expired", wintypes.DWORD),
    ]


_netapi32 = ctypes.windll.netapi32
_advapi32 = ctypes.windll.advapi32
_kernel32 = ctypes.windll.kernel32

_netapi32.NetUserEnum.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
    ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(ctypes.c_size_t),
]
_netapi32.NetUserEnum.restype = wintypes.DWORD
_netapi32.NetApiBufferFree.argtypes = [ctypes.c_void_p]
_netapi32.NetApiBufferFree.restype = wintypes.DWORD

_advapi32.LookupAccountNameW.argtypes = [
    wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p,
    ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
]
_advapi32.LookupAccountNameW.restype = wintypes.BOOL
_advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
_advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL

_kernel32.LocalFree.argtypes = [ctypes.c_void_p]
_kernel32.LocalFree.restype = ctypes.c_void_p


def _account_sid(name):
    """Resolve a local account name to its string SID, or None."""
    cb_sid = wintypes.DWORD()
    cb_domain = wintypes.DWORD()
    use = wintypes.DWORD()
    _advapi32.LookupAccountNameW(
        None, name, None, ctypes.byref(cb_sid), None, ctypes.byref(cb_domain), ctypes.byref(use)
    )
    if not cb_sid.value:
        return None
    sid = (ctypes.c_ubyte * cb_sid.value)()
    domain = ctypes.create_unicode_buffer(cb_domain.value)
    if not _advapi32.LookupAccountNameW(
        None, name, sid, ctypes.byref(cb_sid), domain, ctypes.byref(cb_domain), ctypes.byref(use)
    ):
        return None
    str_sid = wintypes.LPWSTR()
    if not _advapi32.ConvertSidToStringSidW(sid, ctypes.byref(str_sid)):
        return None
    result = str_sid.value
    _kernel32.LocalFree(str_sid)
    return result


def _format_last_logon(seconds):
    if not seconds:
        return None
    try:
        return datetime.fromtimestamp(seconds).strftime("%Y-%m-%dT%H:%M:%S")
    except (OSError, ValueError, OverflowError):
        return None


def collect_local_users():
    bufptr = ctypes.POINTER(ctypes.c_ubyte)()
    entriesread = wintypes.DWORD()
    totalentries = wintypes.DWORD()
    resume = ctypes.c_size_t(0)

    ret = _netapi32.NetUserEnum(
        None, 3, FILTER_NORMAL_ACCOUNT, ctypes.byref(bufptr),
        MAX_PREFERRED_LENGTH, ctypes.byref(entriesread), ctypes.byref(totalentries),
        ctypes.byref(resume),
    )
    if ret != 0 or not bufptr:
        return []

    results = []
    try:
        size = ctypes.sizeof(_USER_INFO_3)
        for i in range(entriesread.value):
            entry = _USER_INFO_3.from_address(ctypes.addressof(bufptr.contents) + i * size)
            flags = entry.usri3_flags
            results.append({
                "Name": entry.usri3_name,
                "SID": _account_sid(entry.usri3_name),
                "Enabled": not (flags & UF_ACCOUNTDISABLE),
                "LocalAccount": True,
                "PasswordRequired": not (flags & UF_PASSWD_NOTREQD),
                "PasswordExpires": not (flags & UF_DONT_EXPIRE_PASSWD),
                "LastLogon": _format_last_logon(entry.usri3_last_logon),
                "Description": entry.usri3_comment or "",
            })
    finally:
        _netapi32.NetApiBufferFree(bufptr)

    results.sort(key=lambda r: r["Name"].lower())
    return results
