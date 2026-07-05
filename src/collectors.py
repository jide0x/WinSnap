import json
import subprocess


PROCESS_COLLECTION_TIMEOUT_SECONDS = 30
SERVICE_COLLECTION_TIMEOUT_SECONDS = 30


def run_powershell_json(command_text, timeout):
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_text,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    if not result.stdout.strip():
        return []

    data = json.loads(result.stdout)

    if isinstance(data, dict):
        data = [data]

    return data


# Collect running processes on Windows using Powershell
def collect_processes():
    return run_powershell_json(
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json",
        PROCESS_COLLECTION_TIMEOUT_SECONDS,
    )


def collect_services():
    return run_powershell_json(
        "Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,Status,StartMode,StartName,PathName,ProcessId | ConvertTo-Json",
        SERVICE_COLLECTION_TIMEOUT_SECONDS,
    )
