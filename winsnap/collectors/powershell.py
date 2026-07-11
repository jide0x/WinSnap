import json
import subprocess
import os


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

    # Allow a global timeout factor override (set by create --timeout-factor)
    try:
        factor = float(os.environ.get("WINSNAP_TIMEOUT_FACTOR", "1.0"))
    except Exception:
        factor = 1.0
    effective_timeout = max(1, int(timeout * factor))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=effective_timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    if not result.stdout.strip():
        return []

    data = json.loads(result.stdout)

    if isinstance(data, dict):
        data = [data]

    return data
