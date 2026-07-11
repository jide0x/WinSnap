WinSnap
=======

WinSnap is a lightweight Windows snapshot and change-analysis CLI.

It captures selected Windows system state, saves it as JSON, and helps you compare snapshots to understand what changed over time.

Current version: `0.9.1`

Installation
------------

From the project folder:

```bash
python -m pip install .
```

For development, install in editable mode:

```bash
python -m pip install -e .
```

After installation, run:

```bash
winsnap --help
```

Current collectors:

- Processes
- Services
- Scheduled tasks
- Registry autoruns
- Startup folders
- Local users
- Local groups
- Installed software
- Network listeners
- Firewall rules

Core Workflow
-------------

```bash
winsnap create before --note "clean system"
winsnap create after --note "after install"
winsnap diff before after
winsnap diff before after --details
```

Without installing, you can run WinSnap from the project folder with `python -m winsnap ...` or `./winsnap.cmd ...`.

Profiles
--------

Use profiles to control which collectors run during snapshot creation:

```bash
winsnap create <name> --profile full   # default, all collectors
winsnap create <name> --profile core   # core collectors only (processes, services, tasks, autoruns, startup, local users, local groups)
```

Commands
--------

Create a snapshot:

```bash
winsnap create <name>
```

Create a snapshot with a note:

```bash
winsnap create <name> --note "your note"
winsnap create <name> --profile core                 # run core collectors only
winsnap create <name> --no-hash --no-signature       # disable hashing/signature (troubleshooting)
winsnap create <name> --workers 8 --timings          # tune parallelism and print durations
```

List snapshots:

```bash
winsnap list
```

Show snapshot metadata:

```bash
winsnap show <name>
```

Compare snapshots:

```bash
winsnap diff <before> <after>
winsnap diff <before> <after> --all   # show all changes without filtering noise
```

Show detailed diff output:

```bash
winsnap diff <before> <after> --details
```

Inspect matching entries inside one snapshot:

```bash
winsnap inspect <snapshot> <query>
winsnap inspect <snapshot> <query> --details
```

Search all snapshots:

```bash
winsnap search <query>
winsnap search <query> --details
```

Delete a snapshot:

```bash
winsnap delete <name>
```

Show version:

```bash
winsnap version
winsnap --version
winsnap -v
```

Show help:

```bash
winsnap help
winsnap --help
winsnap -h
```

Risk Hints
----------

Risk hints are currently archived while filtering is developed to reduce noisy output.

Snapshots still collect processes, services, scheduled tasks, registry autoruns, startup folder entries, and network listeners. Diff, inspect, and search output continues to show raw changes and matching entries without risk-hint labels.

Scheduled Task Collection
-------------------------

Scheduled task snapshots currently collect:

- Task name
- Task path
- State
- Author
- Run as user
- Triggers
- Actions

Registry Autorun Collection
---------------------------

Registry autorun snapshots currently collect Run and RunOnce values from:

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce`
- `HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce`

Startup Folder Collection
-------------------------

Startup folder snapshots currently collect direct files from:

- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- `%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

Shortcut (`.lnk`) entries include target path, arguments, and working directory when available.

Network Listener Collection
---------------------------

Network listener snapshots currently collect:

- TCP listening ports
- UDP bound endpoints
- Local address and port
- Owning process ID
- Process name and path when available
- Service names associated with the owning process when available

Snapshot Storage
----------------

Snapshots are stored as JSON files in `snapshots/`.

Snapshot names may contain only:

- Letters
- Numbers
- Dashes
- Underscores

Project Direction
-----------------

WinSnap is being built toward local Windows security change analysis: capture system state before and after an event, then inspect what changed.

Planned future collectors may include:

- Defender settings
Filtering
---------

By default, `winsnap diff` reduces routine process churn to keep output readable. Use `--all` to see every change.

WinSnap never deletes evidence; filtered items remain in the diff internally.

Permissions
-----------

Some collectors may require elevated privileges to return complete data (e.g., firewall rules). WinSnap records collector status; diffs skip categories that failed to collect.

Schema
------

Snapshots include a schema version and collector status. See `docs/SCHEMA.md` for details.
