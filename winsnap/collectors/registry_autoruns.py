from winsnap.collectors.powershell import run_powershell_json


REGISTRY_AUTORUN_COLLECTION_TIMEOUT_SECONDS = 30


def collect_registry_autoruns():
    return run_powershell_json(
        "$keys = @(" \
        "@{Hive='HKCU';Path='HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'}," \
        "@{Hive='HKCU';Path='HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'}," \
        "@{Hive='HKLM';Path='HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'}," \
        "@{Hive='HKLM';Path='HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'}," \
        "@{Hive='HKLM';Path='HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run'}," \
        "@{Hive='HKLM';Path='HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\RunOnce'}" \
        "); " \
        "$results = @(); " \
        "foreach ($key in $keys) { " \
        "if (Test-Path $key.Path) { " \
        "$props = Get-ItemProperty -Path $key.Path; " \
        "foreach ($prop in $props.PSObject.Properties) { " \
        "if ($prop.Name -notlike 'PS*') { " \
        "$results += [pscustomobject]@{Hive=$key.Hive;KeyPath=$key.Path.Replace(':','');ValueName=$prop.Name;Value=[string]$prop.Value} " \
        "} } } }; " \
        "$results | ConvertTo-Json -Depth 4",
        REGISTRY_AUTORUN_COLLECTION_TIMEOUT_SECONDS,
    )
