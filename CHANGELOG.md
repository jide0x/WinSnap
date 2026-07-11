# Changelog

## 1.0.0

- Stable release based on 1.0.0-rc1 with no functional changes beyond version updates.
- See 1.0.0-rc1 notes for full details on schema v1, filtering, hashing/signatures, partial-failure resilience, CI, and documentation.

## 1.0.0-rc1

- Schema v1 header: `schema_version`, `winsnap_version`, `snapshot_id`, `collectors`, and `collector_status` per artifact.
- Filtering (presentation-only):
  - Routine process churn is reduced by default; `--all` restores full output.
  - Ephemeral localhost listeners are deprioritized unless bind-all, service-associated, or paired with new inbound firewall rules.
  - Trusted signed Microsoft-only FileHash changes are deprioritized (evidence preserved), not hidden.
- Hashing & Signatures:
  - Executable file metadata attached (sha256, size, mtime, status) and Authenticode signature (publisher/status).
  - Deduplicated hashing/signature checks via in-snapshot cache.
  - Diffs highlight binary content changes.
- Partial failures:
  - Collector retries (`--retries`) and timeout factor (`--timeout-factor`) improve resilience.
  - Diffs skip failed collectors and report reasons.
- Performance & ergonomics:
  - Profiles: `full` (default) and `core`.
  - Parallel collectors; tune with `--workers` and `--timings`.
  - Optional `--no-hash` and `--no-signature` for troubleshooting.
- CI:
  - Windows, Python 3.10/3.12; compile, tests, CLI smoke, and wheel build; wheel-install smoke in a fresh venv.
- Docs & policy: LICENSE, CONTRIBUTING, SECURITY, schema docs.

## 0.9.1

- Snapshot performance
  - Added collector profiles to `winsnap create`:
    - `full` (default): all collectors
    - `core`: processes, services, scheduled tasks, registry autoruns, startup folders, local users, local groups
  - Parallelized collectors during snapshot creation to reduce wall time.
  - Snapshot metadata records the selected collectors in order.
  - Failures in individual collectors no longer abort snapshot creation; they record an empty list and a warning.

## 0.9.0

- New collectors
  - Local Users: Name, SID, Enabled, LocalAccount, PasswordRequired, PasswordExpires, LastLogon, Description. LastLogon is not used for diff to avoid noise but is shown in inspect/details.
  - Local Groups: Membership for key groups (Administrators, Users, Remote Desktop Users, Backup Operators, Hyper-V Administrators, Remote Management Users). No AD recursion.
- Diff
  - Local Users: track changes to Enabled, PasswordRequired, PasswordExpires, Description.
  - Local Groups: track membership changes (added/removed members shown in details).
- Registry order
  - Reordered artifacts per spec: Processes, Services, Scheduled Tasks, Registry Autoruns, Startup Folders, Local Users, Local Groups, Installed Software, Network Listeners, Firewall Rules.

## 0.8.0

- New collectors
  - Installed Software: Win32 Uninstall registry + UWP apps. Captures Name, Version, Publisher, Install date (ISO where parseable), Install location, Uninstall command. Excludes SystemComponent entries and Windows Updates/Hotfixes by default.
  - Firewall Rules: Active Windows Defender Firewall rules with Name, Direction, Action, Enabled, Protocol, Local/Remote ports, Program, Profiles.
- Inspect/Search
  - Both new collectors are included automatically via the artifact registry.
  - Firewall Rules: `Enabled` is searchable and summarized in Inspect.
- Diff
  - Added/Removed/Changed sections for Installed Software and Firewall Rules.
  - Pairing: highlights new Allow Inbound firewall rules that align with new network listeners.
- Notes
  - Snapshot JSON schema remains lists of dicts; existing snapshots are fully compatible and show "skipped" for collectors not present.

## 0.7.1

- Refactor: introduce a central artifact registry that drives snapshot creation, diff dispatch, inspect, and search. Adding a new collector now requires a single registration instead of edits across commands and views.
- UX: snapshot summary/list labels and counts are registry-driven for consistency.
- Fix: detailed diff printing for changed Startup Items; cleaned up Network Listener detailed changes.
- Compatibility: no snapshot JSON schema changes; older snapshots remain fully comparable and searchable.

## 0.7

- Added TCP listening port and UDP endpoint collection.
- Added network listener counts to `show` and `list`.
- Added network listener changes to `diff` summary and detailed output.
- Added neutral correlation for new services with new listeners.
- Expanded `inspect` and `search` to include network listeners.
- Added network listener diff tests and compatibility reporting.

## 0.6

- Added startup folder collection for user and machine-wide Startup folders.
- Added startup folder counts to `show` and `list`.
- Added startup folder changes to `diff` summary and detailed output.
- Expanded `inspect` and `search` to include startup folder entries.
- Added startup folder diff tests and compatibility reporting.

## 0.5.2

- Archived risk-hint output while filtering is developed to reduce noise.
- Kept the previous risk-hint prototype under `archive/risk_hints.py` for later reuse.
- Removed active risk-hint tests and documentation from the main CLI behavior.

## 0.5.1

- Packaged WinSnap as an installable Python project with a `winsnap` console command.
- Renamed the import package from `src` to `winsnap`.
- Added `python -m winsnap` support.
- Added package install and CLI smoke checks to CI.
- Moved risk-hint logic out of terminal rendering code.

## 0.5

- Reorganized command handlers into `src/commands/` and terminal rendering into `src/views/`.
- Reorganized collectors into dedicated modules under `src/collectors/`.
- Added scheduled task collection.
- Added registry autorun collection for Run and RunOnce persistence keys.
- Added diff compatibility reporting and skipped comparisons for collectors missing from older snapshots.
- Added a Windows `winsnap.cmd` launcher for direct `winsnap ...` command usage.
- Added scheduled task counts to `show` and `list`.
- Added scheduled task changes to `diff` summary output.
- Added scheduled task entries to `diff --details`.
- Added scheduled task risk hints for enabled tasks, SYSTEM tasks, logon/startup triggers, command/script hosts, and user-writable action paths.
- Added registry autorun risk hints for Run/RunOnce persistence, machine-wide autoruns, command/script hosts, user-writable paths, and missing commands.
- Expanded `inspect` to search processes, services, scheduled tasks, and registry autoruns.
- Expanded `search` to search processes, services, scheduled tasks, and registry autoruns across snapshots.

## 0.4

- Archived the Markdown diff export prototype before release.
- Added Windows service collection.
- Added service counts to `show` and `list`.
- Added service changes to `diff` summary output.
- Added service entries to `diff --details`.
- Added service risk hints for auto-start services, LocalSystem services, user-writable paths, and missing paths.
- Expanded `inspect` to search processes and services.
- Expanded `search` to search processes and services across snapshots.
- Switched CLI parsing to `argparse`.
- Improved old snapshot display by showing missing collectors as `Not collected` / `N/C`.

## 0.3

- Split view/rendering code out of `main.py`.
- Added `inspect` command.
- Added `search` command.
- Added snapshot notes with `create --note`.

## 0.2

- Added formatted CLI output.
- Added snapshot metadata fields.
- Added overwrite protection.
- Added improved error handling.
- Added color helpers.

## 0.1

- Initial process snapshot support.
- Added snapshot create/list/show/delete.
- Added process diffing.
