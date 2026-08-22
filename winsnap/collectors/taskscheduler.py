import ctypes
import uuid
from ctypes import wintypes

# ---------------------------------------------------------------------------
# Minimal Task Scheduler 2.0 COM binding (ctypes) for enumerating registered
# tasks and reading their runtime state + definition XML. These interfaces are
# IDispatch-derived (dual) vtable interfaces; we call the vtable slots directly
# and never go through IDispatch::Invoke.
#
# vtable slot indices are 0-based and follow IUnknown (0-2) + IDispatch (3-6).
# ---------------------------------------------------------------------------

CLSID_TaskScheduler = "{0F87369F-A4E5-4CFC-BD3E-73E6154572DD}"
IID_ITaskService = "{2FABA4C7-4DA9-4013-9697-20CC3FD40F85}"

CLSCTX_INPROC_SERVER = 1
COINIT_MULTITHREADED = 0x0

S_OK = 0
TASK_ENUM_HIDDEN = 0x1

VT_EMPTY = 0
VT_I4 = 3

# vtable indices (after IUnknown[0-2] + IDispatch[3-6])
_IDX_RELEASE = 2

_ITaskService_GetFolder = 7
_ITaskService_Connect = 10

_ITaskFolder_get_Name = 7
_ITaskFolder_get_Path = 8
_ITaskFolder_GetFolders = 10
_ITaskFolder_GetTasks = 14

_ITaskFolderCollection_get_Count = 7
_ITaskFolderCollection_get_Item = 8

_IRegisteredTaskCollection_get_Count = 7
_IRegisteredTaskCollection_get_Item = 8

_IRegisteredTask_get_Name = 7
_IRegisteredTask_get_Path = 8
_IRegisteredTask_get_State = 9


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _VARIANT_UNION(ctypes.Union):
    _fields_ = [
        ("llVal", ctypes.c_longlong),
        ("lVal", ctypes.c_long),
        ("bstrVal", ctypes.c_void_p),
    ]


class VARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", ctypes.c_ushort),
        ("wReserved1", ctypes.c_ushort),
        ("wReserved2", ctypes.c_ushort),
        ("wReserved3", ctypes.c_ushort),
        ("_union", _VARIANT_UNION),
    ]


_ole32 = ctypes.oledll.ole32
_oleaut32 = ctypes.windll.oleaut32

_ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
_ole32.CoInitializeEx.restype = ctypes.c_long
_ole32.CoCreateInstance.argtypes = [
    ctypes.POINTER(GUID), ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p),
]
_ole32.CoCreateInstance.restype = ctypes.c_long
_ole32.CoUninitialize.argtypes = []
_ole32.CoUninitialize.restype = None
_oleaut32.SysFreeString.argtypes = [ctypes.c_void_p]
_oleaut32.SysFreeString.restype = None
_oleaut32.SysAllocString.argtypes = [ctypes.c_wchar_p]
_oleaut32.SysAllocString.restype = ctypes.c_void_p


def _parse_guid(text):
    u = uuid.UUID(text)
    b = u.bytes
    return GUID(
        int.from_bytes(b[0:4], "big"),
        int.from_bytes(b[4:6], "big"),
        int.from_bytes(b[6:8], "big"),
        (ctypes.c_ubyte * 8)(*b[8:16]),
    )


_CLSID_TASK_SCHEDULER = _parse_guid(CLSID_TaskScheduler)
_IID_TASK_SERVICE = _parse_guid(IID_ITaskService)


def _call(iface_ptr, idx, restype, argtypes, *args):
    vtbl = ctypes.cast(iface_ptr, ctypes.POINTER(ctypes.c_void_p))[0]
    fn_addr = ctypes.cast(vtbl, ctypes.POINTER(ctypes.c_void_p))[idx]
    proto = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    fn = proto(fn_addr)
    return fn(iface_ptr, *args)


def _release(iface_ptr):
    if iface_ptr:
        _call(iface_ptr, _IDX_RELEASE, ctypes.c_ulong, [])


def _get_bstr(iface_ptr, idx):
    b = ctypes.c_void_p()
    hr = _call(iface_ptr, idx, ctypes.c_long, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(b))
    if hr != S_OK or not b.value:
        return None
    text = ctypes.cast(b.value, ctypes.c_wchar_p).value
    _oleaut32.SysFreeString(b.value)
    return text


def _get_long(iface_ptr, idx):
    n = ctypes.c_long()
    hr = _call(iface_ptr, idx, ctypes.c_long, [ctypes.POINTER(ctypes.c_long)], ctypes.byref(n))
    return n.value if hr == S_OK else None


def _empty_variant():
    return VARIANT(VT_EMPTY, 0, 0, 0)


def _i4_variant(value):
    v = VARIANT(VT_I4, 0, 0, 0)
    v._union.lVal = value
    return v


def _folder_get_folders(folder_ptr):
    pp = ctypes.c_void_p()
    hr = _call(folder_ptr, _ITaskFolder_GetFolders, ctypes.c_long,
               [ctypes.c_long, ctypes.POINTER(ctypes.c_void_p)], TASK_ENUM_HIDDEN, ctypes.byref(pp))
    return pp.value if hr == S_OK else None


def _folder_get_tasks(folder_ptr):
    pp = ctypes.c_void_p()
    hr = _call(folder_ptr, _ITaskFolder_GetTasks, ctypes.c_long,
               [ctypes.c_long, ctypes.POINTER(ctypes.c_void_p)], TASK_ENUM_HIDDEN, ctypes.byref(pp))
    return pp.value if hr == S_OK else None


def _folder_collection_count(coll_ptr):
    n = ctypes.c_long()
    hr = _call(coll_ptr, _ITaskFolderCollection_get_Count, ctypes.c_long,
               [ctypes.POINTER(ctypes.c_long)], ctypes.byref(n))
    return n.value if hr == S_OK else 0


def _folder_collection_item(coll_ptr, index):
    pp = ctypes.c_void_p()
    v = _i4_variant(index)
    hr = _call(coll_ptr, _ITaskFolderCollection_get_Item, ctypes.c_long,
               [ctypes.POINTER(VARIANT), ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(v), ctypes.byref(pp))
    return pp.value if hr == S_OK else None


def _task_collection_count(coll_ptr):
    n = ctypes.c_long()
    hr = _call(coll_ptr, _IRegisteredTaskCollection_get_Count, ctypes.c_long,
               [ctypes.POINTER(ctypes.c_long)], ctypes.byref(n))
    return n.value if hr == S_OK else 0


def _task_collection_item(coll_ptr, index):
    pp = ctypes.c_void_p()
    v = _i4_variant(index)
    hr = _call(coll_ptr, _IRegisteredTaskCollection_get_Item, ctypes.c_long,
               [ctypes.POINTER(VARIANT), ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(v), ctypes.byref(pp))
    return pp.value if hr == S_OK else None


def _collect_folder(folder_ptr, results):
    """Recursively collect (path, name, state) from a folder.

    Task Scheduler collections are 1-based, so enumerate from index 1.
    """
    tasks_ptr = _folder_get_tasks(folder_ptr)
    if tasks_ptr:
        try:
            count = _task_collection_count(tasks_ptr)
            for i in range(1, count + 1):
                task_ptr = _task_collection_item(tasks_ptr, i)
                if not task_ptr:
                    continue
                try:
                    name = _get_bstr(task_ptr, _IRegisteredTask_get_Name)
                    path = _get_bstr(task_ptr, _IRegisteredTask_get_Path)
                    state = _get_long(task_ptr, _IRegisteredTask_get_State)
                    results.append((path, name, state))
                finally:
                    _release(task_ptr)
        finally:
            _release(tasks_ptr)

    folders_ptr = _folder_get_folders(folder_ptr)
    if folders_ptr:
        try:
            count = _folder_collection_count(folders_ptr)
            for i in range(1, count + 1):
                sub = _folder_collection_item(folders_ptr, i)
                if sub:
                    try:
                        _collect_folder(sub, results)
                    finally:
                        _release(sub)
        finally:
            _release(folders_ptr)


def enumerate_tasks():
    """Enumerate all registered tasks, returning [(path, name, state)]."""
    hr = _ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
    if hr < 0:
        return []

    service = ctypes.c_void_p()
    results = []
    try:
        hr = _ole32.CoCreateInstance(
            ctypes.byref(_CLSID_TASK_SCHEDULER), None, CLSCTX_INPROC_SERVER,
            ctypes.byref(_IID_TASK_SERVICE), ctypes.byref(service),
        )
        if hr != S_OK or not service:
            return []

        empty = _empty_variant()
        hr = _call(service.value, _ITaskService_Connect, ctypes.c_long,
                   [ctypes.POINTER(VARIANT), ctypes.POINTER(VARIANT), ctypes.POINTER(VARIANT), ctypes.POINTER(VARIANT)],
                   ctypes.byref(empty), ctypes.byref(empty), ctypes.byref(empty), ctypes.byref(empty))

        root = ctypes.c_void_p()
        path_bstr = _oleaut32.SysAllocString("\\")
        try:
            hr = _call(service.value, _ITaskService_GetFolder, ctypes.c_long,
                       [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], path_bstr, ctypes.byref(root))
        finally:
            _oleaut32.SysFreeString(path_bstr)
        if hr != S_OK or not root.value:
            return []
        try:
            _collect_folder(root.value, results)
        finally:
            _release(root.value)
        return results
    finally:
        _ole32.CoUninitialize()
