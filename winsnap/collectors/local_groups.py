import ctypes
from ctypes import wintypes

# ---------------------------------------------------------------------------
# Native local group membership collection via Netapi32
# (NetLocalGroupGetMembers level 2).
#
# Replaces the previous Get-LocalGroupMember PowerShell round-trip.
# ---------------------------------------------------------------------------

MAX_PREFERRED_LENGTH = 0xFFFFFFFF

GROUP_NAMES = [
    "Administrators",
    "Users",
    "Remote Desktop Users",
    "Backup Operators",
    "Hyper-V Administrators",
    "Remote Management Users",
]


class _LOCALGROUP_MEMBERS_INFO_2(ctypes.Structure):
    _fields_ = [
        ("lgrmi2_sid", ctypes.c_void_p),
        ("lgrmi2_sidusage", wintypes.DWORD),
        ("lgrmi2_domainandname", wintypes.LPWSTR),
    ]


_netapi32 = ctypes.windll.netapi32

_netapi32.NetLocalGroupGetMembers.argtypes = [
    wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(ctypes.c_size_t),
]
_netapi32.NetLocalGroupGetMembers.restype = wintypes.DWORD
_netapi32.NetApiBufferFree.argtypes = [ctypes.c_void_p]
_netapi32.NetApiBufferFree.restype = wintypes.DWORD


def _group_members(group_name):
    bufptr = ctypes.POINTER(ctypes.c_ubyte)()
    entriesread = wintypes.DWORD()
    totalentries = wintypes.DWORD()
    resume = ctypes.c_size_t(0)

    ret = _netapi32.NetLocalGroupGetMembers(
        None, group_name, 2, ctypes.byref(bufptr), MAX_PREFERRED_LENGTH,
        ctypes.byref(entriesread), ctypes.byref(totalentries), ctypes.byref(resume),
    )
    if ret != 0 or not bufptr:
        return []

    members = []
    try:
        size = ctypes.sizeof(_LOCALGROUP_MEMBERS_INFO_2)
        for i in range(entriesread.value):
            entry = _LOCALGROUP_MEMBERS_INFO_2.from_address(
                ctypes.addressof(bufptr.contents) + i * size
            )
            if entry.lgrmi2_domainandname:
                members.append(entry.lgrmi2_domainandname)
    finally:
        _netapi32.NetApiBufferFree(bufptr)

    return sorted(set(members), key=str.lower)


def collect_local_groups():
    results = []
    for group_name in GROUP_NAMES:
        results.append({
            "Group": group_name,
            "Members": _group_members(group_name),
        })
    return results
