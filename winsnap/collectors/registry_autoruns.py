import winreg

# (Hive label, winreg root, registry path). KeyPath is emitted as "Hive\\path"
# to match the previous PowerShell collector's output format.
_AUTORUN_KEYS = [
    ("HKCU", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKCU", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ("HKLM", winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ("HKLM", winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
]


def _coerce_str(value):
    """Coerce a registry value to string, mirroring PowerShell's [string] cast."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return str(value)


def collect_registry_autoruns():
    """Collect Run/RunOnce values from the standard HKCU/HKLM autorun keys."""
    results = []
    for hive_label, hive, subkey in _AUTORUN_KEYS:
        try:
            key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
        except OSError:
            continue
        with key:
            index = 0
            while True:
                try:
                    value_name, value, value_type = winreg.EnumValue(key, index)
                except OSError:
                    break
                if value_type == winreg.REG_EXPAND_SZ and isinstance(value, str):
                    try:
                        value = winreg.ExpandEnvironmentStrings(value)
                    except Exception:
                        pass
                results.append({
                    "Hive": hive_label,
                    "KeyPath": f"{hive_label}\\{subkey}",
                    "ValueName": value_name,
                    "Value": _coerce_str(value),
                })
                index += 1

    results.sort(key=lambda r: (r["Hive"], r["KeyPath"], r["ValueName"]))
    return results
