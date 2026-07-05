# Changelog

## 0.4

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
