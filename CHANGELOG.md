# Changelog

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
