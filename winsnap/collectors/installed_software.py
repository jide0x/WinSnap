from winsnap.collectors.powershell import run_powershell_json


INSTALLED_SOFTWARE_COLLECTION_TIMEOUT_SECONDS = 45


def collect_installed_software():
    """
    Collect installed software from:
    - Win32: Uninstall registry (HKLM/HKCU, 32/64-bit views)
    - UWP: Get-AppxPackage

    Fields:
    - DisplayName, DisplayVersion, Publisher, InstallDate (ISO yyyy-MM-dd if parseable), InstallLocation, UninstallString
    - Type ('Win32'|'UWP') and identity (KeyPath for Win32, PackageId for UWP)

    Filters:
    - Skip entries with empty DisplayName
    - Skip SystemComponent=1
    - Skip ReleaseType matching Update/Hotfix/Security Update
    """
    script = (
        "$results = @(); "
        "$uninstallRoots = @('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall', 'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall', 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall'); "
        "foreach ($root in $uninstallRoots) { "
        "  if (Test-Path -LiteralPath $root) { "
        "    Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue | ForEach-Object { "
        "      $keyPath = $_.Name; "
        "      $props = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction SilentlyContinue; "
        "      $name = $props.DisplayName; if (-not $name) { continue }; "
        "      $sysComp = $props.SystemComponent; if ($sysComp -and [int]$sysComp -eq 1) { continue }; "
        "      $releaseType = [string]$props.ReleaseType; if ($releaseType -match '(?i)update|hotfix|security update') { continue }; "
        "      $rawDate = [string]$props.InstallDate; $isoDate = $null; "
        "      if ($rawDate -match '^[0-9]{8}$') { "
        "        try { $isoDate = ([datetime]::ParseExact($rawDate, 'yyyyMMdd', $null)).ToString('yyyy-MM-dd') } catch { $isoDate = $null } "
        "      } elseif ($rawDate) { try { $isoDate = ([datetime]$rawDate).ToString('yyyy-MM-dd') } catch { $isoDate = $null } } "
        "      $results += [pscustomobject]@{ "
        "        Type='Win32'; "
        "        KeyPath=$keyPath; "
        "        DisplayName=$name; "
        "        DisplayVersion=$props.DisplayVersion; "
        "        Publisher=$props.Publisher; "
        "        InstallDate=$isoDate; "
        "        InstallLocation=$props.InstallLocation; "
        "        UninstallString=$props.UninstallString "
        "      } "
        "    } "
        "  } "
        "} "
        
        "Get-AppxPackage -ErrorAction SilentlyContinue | ForEach-Object { "
        "  $results += [pscustomobject]@{ "
        "    Type='UWP'; "
        "    PackageId=$_.PackageFamilyName; "
        "    DisplayName=$_.Name; "
        "    DisplayVersion=($_.Version.ToString()); "
        "    Publisher=$_.Publisher; "
        "    InstallDate=$null; "
        "    InstallLocation=$_.InstallLocation; "
        "    UninstallString=$null "
        "  } "
        "} ; "
        "$results | Sort-Object Type,DisplayName,DisplayVersion | ConvertTo-Json -Depth 5"
    )

    return run_powershell_json(script, INSTALLED_SOFTWARE_COLLECTION_TIMEOUT_SECONDS)
