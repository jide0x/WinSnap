from winsnap.collectors.powershell import run_powershell_json


LOCAL_USERS_COLLECTION_TIMEOUT_SECONDS = 30


def collect_local_users():
    """
    Collect local user accounts.

    Fields: Name, SID, Enabled, LocalAccount, PasswordRequired, PasswordExpires, LastLogon (ISO), Description
    Prefer Get-LocalUser; fallback to WMI for basic fields if necessary.
    """
    script = (
        "$results = @(); "
        "if (Get-Command Get-LocalUser -ErrorAction SilentlyContinue) { "
        "  Get-LocalUser | ForEach-Object { "
        "    $last = $null; if ($_.LastLogon) { try { $last = ([datetime]$_.LastLogon).ToString('yyyy-MM-ddTHH:mm:ss') } catch { $last = $null } } "
        "    $results += [pscustomobject]@{ "
        "      Name=$_.Name; SID=$_.SID.Value; Enabled=[bool]$_.Enabled; LocalAccount=$true; "
        "      PasswordRequired=[bool]$_.PasswordRequired; PasswordExpires=[bool]$_.PasswordExpires; "
        "      LastLogon=$last; Description=$_.Description "
        "    } "
        "  } "
        "} else { "
        "  Get-WmiObject Win32_UserAccount -Filter 'LocalAccount=True' | ForEach-Object { "
        "    $results += [pscustomobject]@{ "
        "      Name=$_.Name; SID=$_.SID; Enabled=(-not [bool]$_.Disabled); LocalAccount=$true; "
        "      PasswordRequired=$null; PasswordExpires=$null; LastLogon=$null; Description=$_.Description "
        "    } "
        "  } "
        "} ; "
        "$results | Sort-Object Name | ConvertTo-Json -Depth 4"
    )

    return run_powershell_json(script, LOCAL_USERS_COLLECTION_TIMEOUT_SECONDS)
