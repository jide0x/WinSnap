WinSnap
=======

WinSnap is a Windows command-line tool that captures system state as JSON snapshots and diffs them to show what changed between two points in time.

Current version: `1.3.1`

Install
-------

```bash
pip install WinSnap
```

Or from a checkout:

```bash
python -m pip install .
```

Verify with `winsnap --version`. From a checkout you can also run `python -m winsnap ...` or `.\winsnap.cmd ...` without installing.

Collectors
----------

WinSnap captures ten areas of system state:

- Processes (PID, parent, name, path, command line)
- Services (name, state, start mode, account, path)
- Scheduled tasks (name, path, state, author, run-as user, triggers, actions)
- Registry autoruns (Run and RunOnce, HKCU and HKLM including WOW6432Node)
- Startup folders (user and machine, including .lnk target, arguments, working directory)
- Local users (name, SID, enabled, account flags, last logon)
- Local groups (key group membership)
- Installed software (Win32 uninstall entries and UWP packages)
- Network listeners (TCP/UDP, local address and port, owning process, services)
- Firewall rules (direction, action, enabled, protocol, ports, program, profiles)

Quick start
-----------

```bash
winsnap create before --note "clean system"
winsnap create after  --note "after install"
winsnap diff before after
winsnap diff before after --details
```

Commands
--------

```bash
winsnap create <name>                      create a snapshot
winsnap create <name> --note "..."         add a note
winsnap create <name> --profile core       core collectors only
winsnap create <name> --fast               skip hashing and signatures
winsnap create <name> --cache              reuse cached hashes/signatures
winsnap create <name> --workers 8          tune parallelism

winsnap list                               list snapshots
winsnap show <name>                        snapshot summary
winsnap diff <before> <after>              compare two snapshots
winsnap diff <before> <after> --all        show unfiltered changes
winsnap diff <before> <after> --details    full detail
winsnap inspect <snapshot> <query>         search one snapshot
winsnap search <query>                     search all snapshots
winsnap delete <name>                      delete a snapshot
winsnap version                            show the version
```

`--fast` is shorthand for `--no-hash --no-signature`.

Profiles
--------

- `full` (default): all collectors.
- `core`: processes, services, scheduled tasks, registry autoruns, startup folders, local users, and local groups.

Diff and filtering
------------------

By default `winsnap diff` suppresses routine churn so real changes stand out. Use `--all` to see everything.

- Process identity is the executable, not the command line, so a process whose arguments change is not reported as added and removed.
- Service process IDs are ignored, since they change on every restart.
- Ephemeral UDP listeners from shared service hosts (svchost.exe) are deprioritized unless they pair with a new inbound firewall rule.
- Trusted, signed Microsoft-only binary content changes are deprioritized.

Filtered items are never dropped. They remain in the diff internally and return with `--all`.

Storage
-------

Snapshots are JSON files in `snapshots/`, relative to the current directory. Names may contain only letters, numbers, dashes, and underscores.

Caching
-------

`winsnap create <name> --cache` stores file hashes and signatures in `snapshots/.hashcache.json` and reuses them when a file's size and mtime are unchanged.

Caching is opt-in and off by default. Size and mtime can be spoofed, so an attacker who edits a binary and resets its timestamp could evade detection while caching is enabled. Re-hash without `--cache` for high-assurance comparisons.

Permissions
-----------

Some collectors need elevation to return complete data (for example, firewall rules). WinSnap records collector status and skips categories that failed to collect.

Schema
------

Snapshots carry a schema version and per-collector status. See `docs/SCHEMA.md` for the layout.
