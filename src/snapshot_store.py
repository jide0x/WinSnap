import json
from pathlib import Path


SNAPSHOT_DIR = Path("snapshots")


def ensure_snapshot_dir():
    SNAPSHOT_DIR.mkdir(exist_ok=True)


def snapshot_path(name):
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
        raise FileNotFoundError(f"Snapshot not found: {name}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots():
    ensure_snapshot_dir()
    return sorted(SNAPSHOT_DIR.glob("*.json"))


def delete_snapshot(name):
    path = snapshot_path(name)

    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {name}")

    path.unlink()