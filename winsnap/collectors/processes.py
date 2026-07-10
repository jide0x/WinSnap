from winsnap.collectors.powershell import run_powershell_json


PROCESS_COLLECTION_TIMEOUT_SECONDS = 30


def collect_processes():
    return run_powershell_json(
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json",
        PROCESS_COLLECTION_TIMEOUT_SECONDS,
    )
