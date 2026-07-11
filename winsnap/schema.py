from __future__ import annotations

from typing import Any, Dict, List


SCHEMA_VERSION = 1


def snapshot_collectors(snapshot: Dict[str, Any]) -> List[str]:
    # Support older snapshots that used singular 'collector'
    collectors = snapshot.get("collectors")
    if isinstance(collectors, list):
        return collectors
    legacy = snapshot.get("collector")
    if isinstance(legacy, list):
        return legacy
    return []


def validate_snapshot(snapshot: Dict[str, Any]) -> None:
    # Minimal validation for v1: ensure required header fields exist and types make sense.
    # Do not raise on every minor issue; only on clearly malformed snapshots.
    required_keys = ["name", "created_at"]
    for key in required_keys:
        if key not in snapshot:
            raise ValueError(f"Snapshot missing required field: {key}")

    # Validate collectors presence
    collectors = snapshot_collectors(snapshot)
    if not isinstance(collectors, list):
        raise ValueError("Snapshot collectors must be a list")

    # Validate schema version when present
    schema_version = snapshot.get("schema_version")
    if schema_version is not None and not isinstance(schema_version, int):
        raise ValueError("schema_version must be an integer when present")
    # For now we accept snapshots without schema_version (pre-v1) and treat them as schema 0


def migrate_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder for future migrations. For schema v1, we return as-is.
    return snapshot
