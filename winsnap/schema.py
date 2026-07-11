from __future__ import annotations

from typing import Any, Dict, List
from winsnap.artifacts import SUPPORTED_COLLECTORS


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
    # If explicit keys are present, enforce type
    if "collectors" in snapshot and not isinstance(snapshot.get("collectors"), list):
        raise ValueError("Snapshot collectors must be a list")
    if "collector" in snapshot and not isinstance(snapshot.get("collector"), list):
        raise ValueError("Snapshot collectors must be a list")

    # Enforce collectors subset and order (relative to supported list) when present
    cols = snapshot_collectors(snapshot)
    if cols:
        # Subset
        unknown = [c for c in cols if c not in SUPPORTED_COLLECTORS]
        if unknown:
            raise ValueError(f"Unknown collectors found: {unknown}")
        # Stable relative ordering
        indices = [SUPPORTED_COLLECTORS.index(c) for c in cols]
        if indices != sorted(indices):
            raise ValueError("Collectors are not in supported order")

    # Validate schema version when present
    schema_version = snapshot.get("schema_version")
    if schema_version is not None and not isinstance(schema_version, int):
        raise ValueError("schema_version must be an integer when present")
    if schema_version is not None and schema_version > SCHEMA_VERSION:
        raise ValueError(
            f"Snapshot schema version {schema_version} is newer than the supported "
            f"version {SCHEMA_VERSION}. Upgrade WinSnap to read this snapshot."
        )
    # For now we accept snapshots without schema_version (pre-v1) and treat them as schema 0


def migrate_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder for future migrations. For schema v1, we return as-is.
    return snapshot
