import re
import winreg
from datetime import datetime

from winsnap.collectors.powershell import run_powershell_json


INSTALLED_SOFTWARE_COLLECTION_TIMEOUT_SECONDS = 45

_UNINSTALL_ROOTS = [
    ("HKEY_LOCAL_MACHINE", winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKEY_LOCAL_MACHINE", winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ("HKEY_CURRENT_USER", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
]

_RELEASE_TYPE_SKIP = re.compile(r"(?i)update|hotfix|security update")

_UWP_SCRIPT = (
    "Get-AppxPackage -ErrorAction SilentlyContinue | ForEach-Object { "
    "[pscustomobject]@{ "
    "Type='UWP'; "
    "PackageId=$_.PackageFamilyName; "
    "DisplayName=$_.Name; "
    "DisplayVersion=($_.Version.ToString()); "
    "Publisher=$_.Publisher; "
    "InstallDate=$null; "
    "InstallLocation=$_.InstallLocation; "
    "UninstallString=$null "
    "} } | ConvertTo-Json -Depth 5"
)


def _should_skip(props):
    """Replicate the PowerShell collector's Win32 skip rules."""
    name = props.get("DisplayName")
    if not name:
        return True
    sys_comp = props.get("SystemComponent")
    if sys_comp is not None:
        try:
            if int(sys_comp) == 1:
                return True
        except (TypeError, ValueError):
            pass
    release_type = str(props.get("ReleaseType") or "")
    if _RELEASE_TYPE_SKIP.search(release_type):
        return True
    return False


def _parse_install_date(raw):
    """Convert a Win32 InstallDate to ISO yyyy-MM-dd, or None when unparseable."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if re.fullmatch(r"[0-9]{8}", text):
        try:
            return datetime.strptime(text, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(text).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _win32_key_path(hive_name, root, leaf):
    """Reconstruct the full registry path PowerShell used as KeyPath."""
    return f"{hive_name}\\{root}\\{leaf}"


def _read_win32_items():
    items = []
    for hive_name, hive, root in _UNINSTALL_ROOTS:
        try:
            root_key = winreg.OpenKey(hive, root, 0, winreg.KEY_READ)
        except OSError:
            continue
        with root_key:
            index = 0
            while True:
                try:
                    leaf = winreg.EnumKey(root_key, index)
                except OSError:
                    break
                index += 1
                props = {}
                try:
                    with winreg.OpenKey(hive, f"{root}\\{leaf}", 0, winreg.KEY_READ) as key:
                        value_index = 0
                        while True:
                            try:
                                name, value, value_type = winreg.EnumValue(key, value_index)
                            except OSError:
                                break
                            if value_type == winreg.REG_EXPAND_SZ and isinstance(value, str):
                                try:
                                    value = winreg.ExpandEnvironmentStrings(value)
                                except Exception:
                                    pass
                            props[name] = value
                            value_index += 1
                except OSError:
                    continue
                if _should_skip(props):
                    continue
                items.append({
                    "Type": "Win32",
                    "KeyPath": _win32_key_path(hive_name, root, leaf),
                    "DisplayName": props.get("DisplayName"),
                    "DisplayVersion": props.get("DisplayVersion"),
                    "Publisher": props.get("Publisher"),
                    "InstallDate": _parse_install_date(props.get("InstallDate")),
                    "InstallLocation": props.get("InstallLocation"),
                    "UninstallString": props.get("UninstallString"),
                })
    return items


def _collect_uwp_packages():
    return run_powershell_json(_UWP_SCRIPT, INSTALLED_SOFTWARE_COLLECTION_TIMEOUT_SECONDS)


def collect_installed_software():
    """
    Collect installed software from:
    - Win32: Uninstall registry (HKLM/HKCU, 32/64-bit views) via winreg
    - UWP: Get-AppxPackage (PowerShell)

    Fields:
    - DisplayName, DisplayVersion, Publisher, InstallDate (ISO yyyy-MM-dd if parseable), InstallLocation, UninstallString
    - Type ('Win32'|'UWP') and identity (KeyPath for Win32, PackageId for UWP)
    """
    items = _read_win32_items() + _collect_uwp_packages()
    items.sort(key=lambda r: (
        r.get("Type") or "",
        (r.get("DisplayName") or "").lower(),
        (r.get("DisplayVersion") or "").lower(),
    ))
    return items
