WinSnap
=======

WinSnap is a lightweight Windows snapshot and change-analysis CLI.

It captures selected Windows system state, saves it as JSON, and helps you compare snapshots to understand what changed over time.

Current version: `0.6`

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

Core Workflow
-------------

```bash
winsnap create before --note "clean system"
winsnap create after --note "after install"
winsnap diff before after
winsnap diff before after --details
```

Without installing, you can run WinSnap from the project folder with `python -m winsnap ...` or `./winsnap.cmd ...`.

Commands
--------

Create a snapshot:

```bash
winsnap create <name>
```

Create a snapshot with a note:

```bash
winsnap create <name> --note "your note"
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

Snapshots still collect processes, services, scheduled tasks, registry autoruns, and startup folder entries. Diff, inspect, and search output continues to show raw changes and matching entries without risk-hint labels.

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

- Network connections
- Defender settings
