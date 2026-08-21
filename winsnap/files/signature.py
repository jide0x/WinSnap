from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Native Authenticode signature verification via WinVerifyTrust (Wintrust.dll)
# plus catalog fallback (CryptCATAdmin*) for catalog-signed files.
#
# This replaces the previous PowerShell `Get-AuthenticodeSignature` round-trip
# with direct Win32 calls, removing the per-process PowerShell startup cost.
# ---------------------------------------------------------------------------

# --- Trust / crypto constants ---

WTD_UI_NONE = 2
WTD_REVOKE_NONE = 0
WTD_CHOICE_FILE = 1
WTD_CHOICE_CATALOG = 2
WTD_STATEACTION_VERIFY = 1
WTD_STATEACTION_CLOSE = 2

CERT_NAME_SIMPLE_DISPLAY_TYPE = 4
X509_ASN_ENCODING = 1
CERT_X500_NAME_STR = 3

CALG_SHA1 = 0x00008004

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80

WINTRUST_ACTION_GENERIC_VERIFY_V2 = (
    0x00AAC56B,
    0xCD44,
    0x11D0,
    (0x8C, 0xC2, 0x00, 0xC0, 0x4F, 0xC2, 0x95, 0xEE),
)

# --- HRESULT trust verdicts ---

TRUST_E_NOSIGNATURE = 0x800B0100
TRUST_E_SUBJECT_FORM_UNKNOWN = 0x800B0003
TRUST_E_PROVIDER_UNKNOWN = 0x800B0001
TRUST_E_BAD_DIGEST = 0x80096010
TRUST_E_EXPLICIT_DISTRUST = 0x800B0111
CERT_E_UNTRUSTEDROOT = 0x800B0109
CERT_E_CHAINING = 0x800B010A
CERT_E_REVOKED = 0x800B010C
CERT_E_EXPIRED = 0x800B0101
CERT_E_VALIDITYPERIODNESTING = 0x800B0102
CERT_E_WRONG_USAGE = 0x800B0110
CERT_E_PURPOSE = 0x800B0106
CERT_E_CN_NO_MATCH = 0x800B010F
TRUST_E_BASIC_CONSTRAINTS = 0x80096019

def _hr(hr: int) -> int:
    """Normalise a 32-bit HRESULT to its signed value for comparisons."""
    return hr if hr < 0x80000000 else hr - 0x100000000


_UNTRUSTED_CODES = {
    _hr(CERT_E_UNTRUSTEDROOT),
    _hr(CERT_E_CHAINING),
    _hr(CERT_E_REVOKED),
    _hr(CERT_E_EXPIRED),
    _hr(CERT_E_VALIDITYPERIODNESTING),
    _hr(CERT_E_WRONG_USAGE),
    _hr(CERT_E_PURPOSE),
    _hr(CERT_E_CN_NO_MATCH),
    _hr(TRUST_E_EXPLICIT_DISTRUST),
    _hr(TRUST_E_BASIC_CONSTRAINTS),
}


# --- Win32 structure definitions ---


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


class _WINTRUST_FILE_INFO(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pcwszFilePath", wintypes.LPCWSTR),
        ("hFile", wintypes.HANDLE),
        ("pgKnownSubject", ctypes.POINTER(_GUID)),
    ]


class _WINTRUST_CATALOG_INFO(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("dwCatalogVersion", wintypes.DWORD),
        ("pcwszCatalogFilePath", wintypes.LPCWSTR),
        ("pcwszMemberTag", ctypes.POINTER(ctypes.c_ubyte)),
        ("pcwszMemberFilePath", wintypes.LPCWSTR),
        ("hMemberFile", wintypes.HANDLE),
        ("pbCalculatedFileHash", ctypes.POINTER(ctypes.c_ubyte)),
        ("cbCalculatedFileHash", wintypes.DWORD),
        ("pcCatalogContext", ctypes.c_void_p),
        ("hCatAdmin", wintypes.HANDLE),
    ]


class _WINTRUST_DATA_UNION(ctypes.Union):
    _fields_ = [
        ("pFile", ctypes.POINTER(_WINTRUST_FILE_INFO)),
        ("pCatalog", ctypes.POINTER(_WINTRUST_CATALOG_INFO)),
    ]


class _WINTRUST_DATA(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pPolicyCallbackData", wintypes.LPVOID),
        ("pSIPClientData", wintypes.LPVOID),
        ("dwUIChoice", wintypes.DWORD),
        ("fdwRevocationChecks", wintypes.DWORD),
        ("dwUnionChoice", wintypes.DWORD),
        ("u", _WINTRUST_DATA_UNION),
        ("dwStateAction", wintypes.DWORD),
        ("hWVTStateData", wintypes.HANDLE),
        ("pwszURLReference", wintypes.LPWSTR),
        ("dwProvFlags", wintypes.DWORD),
        ("dwUIContext", wintypes.DWORD),
        ("pSignatureSettings", wintypes.LPVOID),
    ]


class _CRYPT_DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class _CRYPT_ALGORITHM_IDENTIFIER(ctypes.Structure):
    _fields_ = [
        ("pszObjId", wintypes.LPSTR),
        ("Parameters", _CRYPT_DATA_BLOB),
    ]


class _CERT_INFO(ctypes.Structure):
    _fields_ = [
        ("dwVersion", wintypes.DWORD),
        ("SerialNumber", _CRYPT_DATA_BLOB),
        ("SignatureAlgorithm", _CRYPT_ALGORITHM_IDENTIFIER),
        ("Issuer", _CRYPT_DATA_BLOB),
        ("NotBefore", _FILETIME),
        ("NotAfter", _FILETIME),
        ("Subject", _CRYPT_DATA_BLOB),
    ]


class _CERT_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("dwCertEncodingType", wintypes.DWORD),
        ("pbCertEncoded", ctypes.POINTER(ctypes.c_ubyte)),
        ("cbCertEncoded", wintypes.DWORD),
        ("pCertInfo", ctypes.POINTER(_CERT_INFO)),
        ("hCertStore", wintypes.HANDLE),
    ]


class _CRYPT_PROVIDER_CERT(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pCert", ctypes.POINTER(_CERT_CONTEXT)),
    ]


class _CRYPT_PROVIDER_SGNR(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("sftVerifyAsOf", _FILETIME),
        ("csCertChain", wintypes.DWORD),
        ("pasCertChain", ctypes.POINTER(_CRYPT_PROVIDER_CERT)),
    ]


class _CRYPT_PROVIDER_DATA(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pWintrustData", ctypes.c_void_p),
        ("fOpenedFile", wintypes.BOOL),
        ("hWndParent", wintypes.HWND),
        ("pgActionID", ctypes.c_void_p),
        ("hProv", ctypes.c_void_p),
        ("dwError", wintypes.DWORD),
        ("dwRegSecuritySettings", wintypes.DWORD),
        ("dwRegPolicySettings", wintypes.DWORD),
        ("psPfns", ctypes.c_void_p),
        ("cdwTrustStepErrors", wintypes.DWORD),
        ("padwTrustStepErrors", ctypes.c_void_p),
        ("chStores", wintypes.DWORD),
        ("pahStores", ctypes.c_void_p),
        ("dwEncoding", wintypes.DWORD),
        ("hMsg", ctypes.c_void_p),
        ("csSigners", wintypes.DWORD),
        ("pasSigners", ctypes.POINTER(_CRYPT_PROVIDER_SGNR)),
    ]


class _CATALOG_INFO(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("wszCatalogFile", ctypes.c_wchar * 260),
    ]


# --- DLL binding ---

_wintrust = ctypes.windll.wintrust
_crypt32 = ctypes.windll.crypt32
_kernel32 = ctypes.windll.kernel32

_wintrust.WinVerifyTrust.argtypes = [wintypes.HWND, ctypes.POINTER(_GUID), ctypes.c_void_p]
_wintrust.WinVerifyTrust.restype = ctypes.c_long
_wintrust.WTHelperProvDataFromStateData.argtypes = [wintypes.HANDLE]
_wintrust.WTHelperProvDataFromStateData.restype = ctypes.POINTER(_CRYPT_PROVIDER_DATA)

_wintrust.CryptCATAdminAcquireContext2.argtypes = [
    ctypes.POINTER(wintypes.HANDLE),
    ctypes.POINTER(_GUID),
    wintypes.LPCWSTR,
    ctypes.c_void_p,
    wintypes.DWORD,
]
_wintrust.CryptCATAdminAcquireContext2.restype = wintypes.BOOL
_wintrust.CryptCATAdminCalcHashFromFileHandle2.argtypes = [
    wintypes.HANDLE,
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
    wintypes.DWORD,
]
_wintrust.CryptCATAdminCalcHashFromFileHandle2.restype = wintypes.BOOL
_wintrust.CryptCATAdminEnumCatalogFromHash.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.HANDLE),
]
_wintrust.CryptCATAdminEnumCatalogFromHash.restype = wintypes.HANDLE
_wintrust.CryptCATCatalogInfoFromContext.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(_CATALOG_INFO),
    wintypes.DWORD,
]
_wintrust.CryptCATCatalogInfoFromContext.restype = wintypes.BOOL
_wintrust.CryptCATAdminReleaseCatalogContext.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.DWORD]
_wintrust.CryptCATAdminReleaseCatalogContext.restype = wintypes.BOOL
_wintrust.CryptCATAdminReleaseContext.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_wintrust.CryptCATAdminReleaseContext.restype = wintypes.BOOL

_crypt32.CertGetNameStringW.argtypes = [
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
_crypt32.CertGetNameStringW.restype = wintypes.DWORD
_crypt32.CertNameToStrW.argtypes = [
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
_crypt32.CertNameToStrW.restype = wintypes.DWORD
_crypt32.CryptHashCertificate.argtypes = [
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.POINTER(wintypes.DWORD),
]
_crypt32.CryptHashCertificate.restype = wintypes.BOOL

_kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
_kernel32.CreateFileW.restype = wintypes.HANDLE
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL

_INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

_GENERIC_VERIFY_V2 = _GUID(
    WINTRUST_ACTION_GENERIC_VERIFY_V2[0],
    WINTRUST_ACTION_GENERIC_VERIFY_V2[1],
    WINTRUST_ACTION_GENERIC_VERIFY_V2[2],
    (ctypes.c_ubyte * 8)(*WINTRUST_ACTION_GENERIC_VERIFY_V2[3]),
)


# --- Helpers ---


def _cert_simple_name(pcert: "_CERT_CONTEXT") -> str:
    size = _crypt32.CertGetNameStringW(pcert, CERT_NAME_SIMPLE_DISPLAY_TYPE, 0, None, None, 0)
    if size <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(size)
    _crypt32.CertGetNameStringW(pcert, CERT_NAME_SIMPLE_DISPLAY_TYPE, 0, None, buf, size)
    return buf.value or ""


def _cert_name_str(pcert: "_CERT_CONTEXT", which: str) -> str:
    p_info = pcert.contents.pCertInfo
    if not p_info:
        return ""
    blob = p_info.contents.Subject if which == "subject" else p_info.contents.Issuer
    size = _crypt32.CertNameToStrW(X509_ASN_ENCODING, ctypes.byref(blob), CERT_X500_NAME_STR, None, 0)
    if size <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(size)
    _crypt32.CertNameToStrW(X509_ASN_ENCODING, ctypes.byref(blob), CERT_X500_NAME_STR, buf, size)
    return buf.value or ""


def _cert_thumbprint(pcert: "_CERT_CONTEXT") -> str:
    pc = pcert.contents
    size = wintypes.DWORD(20)
    digest = (ctypes.c_ubyte * 20)()
    ok = _crypt32.CryptHashCertificate(
        0,
        CALG_SHA1,
        0,
        pc.pbCertEncoded,
        pc.cbCertEncoded,
        digest,
        ctypes.byref(size),
    )
    if not ok:
        return ""
    return bytes(digest[: size.value]).hex().upper()


def _extract_cert_info(h_state_data: int) -> Dict[str, Any]:
    """Extract publisher/subject/issuer/thumbprint from a trust state handle."""
    cpd = _wintrust.WTHelperProvDataFromStateData(h_state_data)
    if not cpd:
        return {}
    try:
        if not cpd.contents.csSigners:
            return {}
        sgnr = cpd.contents.pasSigners[0]
        if sgnr.csCertChain < 1 or not sgnr.pasCertChain:
            return {}
        pcert = sgnr.pasCertChain[0].pCert
        if not pcert:
            return {}
        return {
            "publisher": _cert_simple_name(pcert),
            "subject": _cert_name_str(pcert, "subject"),
            "issuer": _cert_name_str(pcert, "issuer"),
            "thumbprint": _cert_thumbprint(pcert),
        }
    except Exception:
        return {}


def _run_wintrust(path: str, choice: int, catalog_info: Optional["_WINTRUST_CATALOG_INFO"] = None):
    """Run WinVerifyTrust for a file (or catalog), returning (hr, cert_info)."""
    data = _WINTRUST_DATA()
    data.cbStruct = ctypes.sizeof(_WINTRUST_DATA)
    data.dwUIChoice = WTD_UI_NONE
    data.fdwRevocationChecks = WTD_REVOKE_NONE
    data.dwUnionChoice = choice
    data.dwStateAction = WTD_STATEACTION_VERIFY

    file_info = None
    if choice == WTD_CHOICE_FILE:
        file_info = _WINTRUST_FILE_INFO()
        file_info.cbStruct = ctypes.sizeof(_WINTRUST_FILE_INFO)
        file_info.pcwszFilePath = path
        data.u.pFile = ctypes.pointer(file_info)
    else:
        data.u.pCatalog = ctypes.pointer(catalog_info)

    try:
        hr = _wintrust.WinVerifyTrust(None, ctypes.byref(_GENERIC_VERIFY_V2), ctypes.byref(data))
    except Exception:
        return _hr(TRUST_E_PROVIDER_UNKNOWN), {}

    cert_info = {}
    if hr == 0 and data.hWVTStateData:
        cert_info = _extract_cert_info(data.hWVTStateData)

    if data.hWVTStateData:
        data.dwStateAction = WTD_STATEACTION_CLOSE
        try:
            _wintrust.WinVerifyTrust(None, ctypes.byref(_GENERIC_VERIFY_V2), ctypes.byref(data))
        except Exception:
            pass

    return _hr(hr), cert_info


def _status_from_hr(hr: int) -> str:
    if hr == 0:
        return "verified"
    if hr in (_hr(TRUST_E_NOSIGNATURE), _hr(TRUST_E_SUBJECT_FORM_UNKNOWN)):
        return "unsigned"
    if hr == _hr(TRUST_E_BAD_DIGEST):
        return "invalid"
    if hr in _UNTRUSTED_CODES:
        return "untrusted"
    return "unavailable"


def _verify_via_catalog(path: str, h_admin: int):
    """Look up the covering catalog(s) and verify against them.

    Returns (hr, cert_info) or None when the file cannot be opened or has no
    covering catalog (in which case the caller should treat it as unsigned).
    """
    h_file = _kernel32.CreateFileW(
        path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if h_file == _INVALID_HANDLE_VALUE:
        return None

    try:
        cb_hash = wintypes.DWORD()
        _wintrust.CryptCATAdminCalcHashFromFileHandle2(h_admin, h_file, ctypes.byref(cb_hash), None, 0)
        if not cb_hash.value:
            return None
        pb_hash = (ctypes.c_ubyte * cb_hash.value)()
        if not _wintrust.CryptCATAdminCalcHashFromFileHandle2(h_admin, h_file, ctypes.byref(cb_hash), pb_hash, 0):
            return None

        catalog_paths = []
        prev = wintypes.HANDLE()
        while True:
            cat = _wintrust.CryptCATAdminEnumCatalogFromHash(
                h_admin, pb_hash, cb_hash.value, 0, ctypes.byref(prev)
            )
            if not cat:
                break
            info = _CATALOG_INFO()
            info.cbStruct = ctypes.sizeof(_CATALOG_INFO)
            if _wintrust.CryptCATCatalogInfoFromContext(cat, ctypes.byref(info), 0):
                catalog_paths.append(info.wszCatalogFile)
            prev.value = cat

        if not catalog_paths:
            return None

        member_tag = ctypes.create_string_buffer(bytes(pb_hash[: cb_hash.value]))
        last_hr = _hr(TRUST_E_NOSIGNATURE)
        cert_info = {}
        for catalog_path in catalog_paths:
            catalog_info = _WINTRUST_CATALOG_INFO()
            catalog_info.cbStruct = ctypes.sizeof(_WINTRUST_CATALOG_INFO)
            catalog_info.dwCatalogVersion = 0
            catalog_info.pcwszCatalogFilePath = catalog_path
            catalog_info.pcwszMemberTag = ctypes.cast(member_tag, ctypes.POINTER(ctypes.c_ubyte))
            catalog_info.pcwszMemberFilePath = path
            catalog_info.hMemberFile = h_file
            catalog_info.pbCalculatedFileHash = ctypes.cast(member_tag, ctypes.POINTER(ctypes.c_ubyte))
            catalog_info.cbCalculatedFileHash = cb_hash.value
            catalog_info.hCatAdmin = h_admin

            last_hr, cert_info = _run_wintrust(path, WTD_CHOICE_CATALOG, catalog_info)
            if last_hr == 0:
                return 0, cert_info

        return last_hr, cert_info
    finally:
        _kernel32.CloseHandle(h_file)


def _verify_one(path: str, h_admin: Optional[int]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "unavailable",
        "publisher": None,
        "subject": None,
        "issuer": None,
        "thumbprint": None,
        "timestamped": False,
        "error": None,
    }

    try:
        hr, cert_info = _run_wintrust(path, WTD_CHOICE_FILE)
    except Exception:
        hr = _hr(TRUST_E_PROVIDER_UNKNOWN)
        cert_info = {}

    # Catalog fallback for files without an embedded signature.
    if hr == _hr(TRUST_E_NOSIGNATURE) and h_admin is not None:
        try:
            catalog_result = _verify_via_catalog(path, h_admin)
        except Exception:
            catalog_result = None
        if catalog_result is None:
            hr = _hr(TRUST_E_NOSIGNATURE)
        else:
            hr, cert_info = catalog_result

    result["status"] = _status_from_hr(hr)
    if cert_info:
        result.update(cert_info)
    return result


def verify_signatures_bulk(paths: List[str]) -> Dict[str, Dict[str, Any]]:
    """Verify Authenticode signatures for many files in-process.

    Returns a mapping {path: normalized signature dict}. On failure, every path
    maps to an error result so no caller has to special-case exceptions.
    """
    paths = [str(p) for p in paths if p]
    if not paths:
        return {}

    h_admin = wintypes.HANDLE()
    has_catalog = bool(_wintrust.CryptCATAdminAcquireContext2(ctypes.byref(h_admin), None, None, None, 0))
    admin_handle = h_admin.value if has_catalog else None

    result: Dict[str, Dict[str, Any]] = {}
    try:
        for path in paths:
            result[path] = _verify_one(path, admin_handle)
    finally:
        if has_catalog and admin_handle:
            _wintrust.CryptCATAdminReleaseContext(admin_handle, 0)

    return result


def verify_signature(path: str) -> Dict[str, Any]:
    """Verify Authenticode signature for a single file."""
    return verify_signatures_bulk([path]).get(path, {"status": "unavailable"})
