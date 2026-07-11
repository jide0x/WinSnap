from winsnap.collectors.powershell import run_powershell_json


FIREWALL_RULES_COLLECTION_TIMEOUT_SECONDS = 60


def collect_firewall_rules():
    """
    Collect active Windows Defender Firewall rules from the local machine.

    Fields:
    - Name: display name of the rule
    - RuleName: system/internal rule name (stable key)
    - Direction: Inbound|Outbound
    - Action: Allow|Block
    - Enabled: True|False
    - Protocol: TCP|UDP|Any
    - LocalPort: string (e.g., "Any", "80", "80,443", "8000-8010")
    - RemotePort: string
    - Program: fully-qualified path (if any)
    - Profiles: comma-separated profiles (Domain,Private,Public) or "Any"
    """
    script = (
        "$results = @(); "
        "Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction SilentlyContinue | ForEach-Object { "
        "  $rule = $_; "
        "  $pf = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue; "
        "  $af = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue; "
        "  $protocol = if ($pf.Protocol) { $pf.Protocol.ToString() } else { 'Any' }; "
        "  $localPort = if ($pf.LocalPort) { ($pf.LocalPort -join ',') } else { 'Any' }; "
        "  $remotePort = if ($pf.RemotePort) { ($pf.RemotePort -join ',') } else { 'Any' }; "
        "  $program = if ($af.Program) { $af.Program } else { $null }; "
        "  $profiles = if ($rule.Profile) { $rule.Profile.ToString() } else { 'Any' }; "
        "  $direction = if ($rule.Direction) { $rule.Direction.ToString() } else { $null }; "
        "  $action = if ($rule.Action) { $rule.Action.ToString() } else { $null }; "
        "  $enabled = [bool]$rule.Enabled; "
        "  $displayName = if ($rule.DisplayName) { $rule.DisplayName } else { $rule.Name }; "
        "  $results += [pscustomobject]@{ "
        "    Name=$displayName; "
        "    RuleName=$rule.Name; "
        "    Direction=$direction; "
        "    Action=$action; "
        "    Enabled=$enabled; "
        "    Protocol=$protocol; "
        "    LocalPort=$localPort; "
        "    RemotePort=$remotePort; "
        "    Program=$program; "
        "    Profiles=$profiles "
        "  } "
        "} ; "
        "$results | Sort-Object Direction,Action,Name | ConvertTo-Json -Depth 5"
    )

    return run_powershell_json(script, FIREWALL_RULES_COLLECTION_TIMEOUT_SECONDS)
