WinSnap
=======

WinSnap is a lightweight Windows snapshot and change-analysis CLI.

It captures selected Windows system state, saves it as JSON, and helps you compare snapshots to understand what changed over time.

Current version: `0.5.1`

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

Service Risk Hints
------------------

Detailed service output can show risk hints such as:

- Auto-start service
- Runs as LocalSystem
- Path in user-writable location
- Missing/unknown PathName

These are not detections by themselves. They are context clues that help you decide what deserves closer inspection.

Registry Autorun Risk Hints
---------------------------

Detailed registry autorun output can show risk hints such as:

- Run key persistence location
- RunOnce persistence location
- Machine-wide autorun
- Executes command or scripting host
- Autorun path in user-writable location
- Missing/empty autorun command

These are not detections by themselves. They are context clues that help you decide what deserves closer inspection.

Scheduled Task Risk Hints
-------------------------

Detailed scheduled task output can show risk hints such as:

- Enabled scheduled task
- Runs as SYSTEM
- Runs at logon
- Runs at startup
- Executes command or scripting host
- Action path in user-writable location

These are not detections by themselves. They are context clues that help you decide what deserves closer inspection.

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

- Startup folders
- Network connections
- Defender settings
