from winsnap.collectors.powershell import run_powershell_json


LOCAL_GROUPS_COLLECTION_TIMEOUT_SECONDS = 30

GROUP_NAMES = [
    "Administrators",
    "Users",
    "Remote Desktop Users",
    "Backup Operators",
    "Hyper-V Administrators",
    "Remote Management Users",
]


def collect_local_groups():
    """
    Collect members of key local groups without recursion.

    Fields: Group, Members (sorted list of names as returned by Get-LocalGroupMember.Name)
    """
    script = (
        "$groupNames = @('Administrators','Users','Remote Desktop Users','Backup Operators','Hyper-V Administrators','Remote Management Users'); "
        "$results = @(); "
        "foreach ($g in $groupNames) { "
        "  $members = @(); "
        "  try { $m = Get-LocalGroupMember -Name $g -ErrorAction Stop } catch { $m = @() } "
        "  foreach ($item in $m) { if ($item.Name) { $members += $item.Name } } "
        "  $members = $members | Sort-Object -Unique; "
        "  $results += [pscustomobject]@{ Group=$g; Members=$members } "
        "} ; "
        "$results | ConvertTo-Json -Depth 4"
    )

    return run_powershell_json(script, LOCAL_GROUPS_COLLECTION_TIMEOUT_SECONDS)
