from winsnap.collectors.powershell import run_powershell_json


SERVICE_COLLECTION_TIMEOUT_SECONDS = 30


def collect_services():
    return run_powershell_json(
        "Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,Status,StartMode,StartName,PathName,ProcessId | ConvertTo-Json",
        SERVICE_COLLECTION_TIMEOUT_SECONDS,
    )
