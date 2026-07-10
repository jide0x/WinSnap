import json
from pathlib import Path
import re


SNAPSHOT_DIR = Path("snapshots")
SNAPSHOT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def ensure_snapshot_dir():
    SNAPSHOT_DIR.mkdir(exist_ok=True)


def validate_snapshot_name(name):
    if not SNAPSHOT_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            f'Invalid snapshot name: "{name}". Use letters, numbers, dashes, or underscores.'
        )


def snapshot_path(name):
    validate_snapshot_name(name)
    return SNAPSHOT_DIR / f"{name}.json"


def save_snapshot(snapshot):
    ensure_snapshot_dir()
    path = snapshot_path(snapshot["name"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    return path


def load_snapshot(name):
    path = snapshot_path(name)

    if not path.exists():
        raise FileNotFoundError(f'Snapshot "{name}" not found.')

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots():
    ensure_snapshot_dir()
    return sorted(SNAPSHOT_DIR.glob("*.json"))


def delete_snapshot(name):
    path = snapshot_path(name)

    if not path.exists():
        raise FileNotFoundError(f'Snapshot "{name}" not found.')

    path.unlink()
