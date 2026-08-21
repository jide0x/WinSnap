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
    script = """
$rules = @(Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction SilentlyContinue)
$ports = @{}; foreach ($p in @(Get-NetFirewallPortFilter -PolicyStore ActiveStore -ErrorAction SilentlyContinue)) { $ports[$p.InstanceID] = $p }
$apps = @{}; foreach ($a in @(Get-NetFirewallApplicationFilter -PolicyStore ActiveStore -ErrorAction SilentlyContinue)) { $apps[$a.InstanceID] = $a }
$results = @(foreach ($rule in $rules) {
  $id = $rule.InstanceID
  $pf = $ports[$id]
  $af = $apps[$id]
  [pscustomobject]@{
    Name       = if ($rule.DisplayName) { $rule.DisplayName } else { $rule.Name }
    RuleName   = $rule.Name
    Direction  = if ($rule.Direction) { $rule.Direction.ToString() } else { $null }
    Action     = if ($rule.Action) { $rule.Action.ToString() } else { $null }
    Enabled    = [bool]$rule.Enabled
    Protocol   = if ($pf -and $pf.Protocol) { $pf.Protocol.ToString() } else { 'Any' }
    LocalPort  = if ($pf -and $pf.LocalPort) { ($pf.LocalPort -join ',') } else { 'Any' }
    RemotePort = if ($pf -and $pf.RemotePort) { ($pf.RemotePort -join ',') } else { 'Any' }
    Program    = if ($af -and $af.Program) { $af.Program } else { $null }
    Profiles   = if ($rule.Profile) { $rule.Profile.ToString() } else { 'Any' }
  }
})
$results | Sort-Object Direction,Action,Name | ConvertTo-Json -Depth 5
"""

    return run_powershell_json(script, FIREWALL_RULES_COLLECTION_TIMEOUT_SECONDS)
