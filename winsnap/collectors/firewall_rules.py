import ctypes
from ctypes import wintypes
import winreg

# ---------------------------------------------------------------------------
# Native firewall rule collection from the Windows Defender Firewall local
# store registry (SharedAccess\Parameters\FirewallPolicy\FirewallRules).
#
# Replaces the previous Get-NetFirewallRule / Get-NetFirewallPortFilter /
# Get-NetFirewallApplicationFilter PowerShell round-trip. Each value name is
# the rule's internal name (RuleName) and its data is a "v2.33|Key=Value|..."
# string. Display names are resolved from "@dll,-id" indirect strings.
# ---------------------------------------------------------------------------

_FIREWALL_RULES_KEY = (
    r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"
)

_PROTOCOL_NAMES = {1: "ICMPv4", 6: "TCP", 17: "UDP", 58: "ICMPv6", 256: "Any"}
_PROFILE_ORDER = ["Domain", "Private", "Public"]

# Canonical names exposed by the NetSecurity CIM provider for the named
# ports stored in the registry (local-port / remote-port keywords).
_NAMED_PORTS = {
    "RPC": "RPC",
    "RPC-EPMap": "RPCEPMap",
    "Ply2Disc": "PlayToDiscovery",
    "IPHTTPSIn": "IPHTTPSIn",
    "IPTLSIn": "IPTLSIn",
    "IPHTTPSOut": "IPHTTPSOut",
    "IPTLSOut": "IPTLSOut",
    "Teredo": "Teredo",
}

_shlwapi = ctypes.windll.shlwapi
_shlwapi.SHLoadIndirectString.argtypes = [
    wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, ctypes.c_void_p,
]
_shlwapi.SHLoadIndirectString.restype = ctypes.c_long


def _resolve_display_name(name):
    """Resolve an "@dll,-id" indirect string, leaving "@{...}" and plain text."""
    if not name or name.startswith("@{") or not name.startswith("@"):
        return name
    buf = ctypes.create_unicode_buffer(1024)
    try:
        hr = _shlwapi.SHLoadIndirectString(name, buf, 1024, None)
    except Exception:
        return name
    if hr == 0 and buf.value:
        return buf.value
    return name


def _parse_rule(text):
    """Parse a rule data string into {key: [values]} (Profile/LPort can repeat)."""
    pairs = {}
    for part in text.split("|"):
        if "=" in part:
            key, value = part.split("=", 1)
            pairs.setdefault(key, []).append(value)
    return pairs


def _first(pairs, key):
    values = pairs.get(key)
    return values[0] if values else None


def _named_port(value):
    return _NAMED_PORTS.get(value, value)


def _direction(pairs):
    return "Inbound" if _first(pairs, "Dir") == "In" else "Outbound"


def _action(pairs):
    return _first(pairs, "Action") or "Allow"


def _enabled(pairs):
    return str(_first(pairs, "Active") or "").upper() == "TRUE"


def _protocol(pairs):
    raw = _first(pairs, "Protocol")
    if raw is None:
        return "Any"
    try:
        number = int(raw)
    except ValueError:
        return raw
    return _PROTOCOL_NAMES.get(number, str(number))


def _local_port(pairs):
    if "LPort" in pairs:
        return ",".join(_named_port(v) for v in pairs["LPort"])
    if "LPort2_10" in pairs or "LPort2_20" in pairs:
        values = pairs.get("LPort2_10", []) + pairs.get("LPort2_20", [])
        return _named_port(values[-1])
    if "ICMP4" in pairs or "ICMP6" in pairs:
        return "RPC"
    return "Any"


def _remote_port(pairs):
    if "RPort" in pairs:
        return ",".join(_named_port(v) for v in pairs["RPort"])
    if "RPort2_10" in pairs:
        return _named_port(pairs["RPort2_10"][-1])
    return "Any"


def _program(pairs):
    app = _first(pairs, "App")
    if not app:
        return "Any"
    if app == "System":
        return "System"
    try:
        return winreg.ExpandEnvironmentStrings(app)
    except Exception:
        return app


def _profiles(pairs):
    present = set(pairs.get("Profile") or [])
    if not present:
        return "Any"
    ordered = [p for p in _PROFILE_ORDER if p in present]
    return ", ".join(ordered)


def collect_firewall_rules():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _FIREWALL_RULES_KEY, 0, winreg.KEY_READ)
    except OSError:
        return []

    results = []
    with key:
        index = 0
        while True:
            try:
                rule_name, data, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            pairs = _parse_rule(data)
            display_name = _resolve_display_name(_first(pairs, "Name") or rule_name)
            results.append({
                "Name": display_name,
                "RuleName": rule_name,
                "Direction": _direction(pairs),
                "Action": _action(pairs),
                "Enabled": _enabled(pairs),
                "Protocol": _protocol(pairs),
                "LocalPort": _local_port(pairs),
                "RemotePort": _remote_port(pairs),
                "Program": _program(pairs),
                "Profiles": _profiles(pairs),
            })

    results.sort(key=lambda r: (r["Direction"], r["Action"], r["Name"].lower()))
    return results
