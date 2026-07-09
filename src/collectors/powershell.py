import json
import subprocess


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
