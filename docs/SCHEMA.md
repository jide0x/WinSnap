Snapshot Schema (v1)
====================

Header
------

```json
{
  "schema_version": 1,
  "winsnap_version": "1.0.0rc1",
  "snapshot_id": "uuid-value",
  "name": "before",
  "created_at": "2026-07-10T20:56:00",
  "hostname": "DESKTOP-123",
  "username": "user",
  "windows_version": "Windows-11-...",
  "collectors": ["processes", "services", ...],
  "collector_status": {
    "processes": {"status": "success", "count": 261, "duration_ms": 110}
  },
  "note": "optional"
}
```

Collectors
----------

The collector set is frozen for v1.0:

- processes
- services
- scheduled_tasks
- registry_autoruns
- startup_folders
- local_users
- local_groups
- installed_software
- network_listeners
- firewall_rules

File Metadata
-------------

Artifacts may include a `file` object with:

```json
{
  "file": {
    "path": "C:\\Program Files\\Example\\example.exe",
    "exists": true,
    "sha256": "...",
    "size": 102400,
    "modified_at": "2026-07-10T21:30:00",
    "hash_status": "success",
    "signature": {
      "status": "verified",
      "publisher": "Microsoft Corporation",
      "subject": "CN=...",
      "issuer": "...",
      "thumbprint": "...",
      "timestamped": true,
      "error": null
    }
  }
}
```

Collector Status
----------------

Each collector’s result is summarized under `collector_status`:

- status: `success`, `failed`, `partial`, or `skipped`
- count: number of items collected
- duration_ms: integer
- error: message when failed

Compatibility
-------------

During diff, collectors are compared only when present and successful in both snapshots. Failures and missing collectors are reported as "skipped" with reasons.
