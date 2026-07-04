import json
import subprocess


PROCESS_COLLECTION_TIMEOUT_SECONDS = 30

# Collect running processes on Windows using Powershell
def collect_processes():
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=PROCESS_COLLECTION_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    if not result.stdout.strip():
        return []

    data = json.loads(result.stdout)

    if isinstance(data, dict):
        data = [data]

    return data
