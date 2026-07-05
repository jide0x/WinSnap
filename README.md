WinSnap
=======

WinSnap is a lightweight Windows snapshot and change-analysis CLI.

It captures selected Windows system state, saves it as JSON, and helps you compare snapshots to understand what changed over time.

Current version: `0.4`

Current collectors:

- Processes
- Services

Core Workflow
-------------

```bash
python winsnap create before --note "clean system"
python winsnap create after --note "after install"
python winsnap diff before after
python winsnap diff before after --details
```

Commands
--------

Create a snapshot:

```bash
python winsnap create <name>
```

Create a snapshot with a note:

```bash
python winsnap create <name> --note "your note"
```

List snapshots:

```bash
python winsnap list
```

Show snapshot metadata:

```bash
python winsnap show <name>
```

Compare snapshots:

```bash
python winsnap diff <before> <after>
```

Show detailed diff output:

```bash
python winsnap diff <before> <after> --details
```

Inspect matching entries inside one snapshot:

```bash
python winsnap inspect <snapshot> <query>
python winsnap inspect <snapshot> <query> --details
```

Search all snapshots:

```bash
python winsnap search <query>
python winsnap search <query> --details
```

Delete a snapshot:

```bash
python winsnap delete <name>
```

Show version:

```bash
python winsnap version
python winsnap --version
python winsnap -v
```

Show help:

```bash
python winsnap help
python winsnap --help
python winsnap -h
```

Service Risk Hints
------------------

Detailed service output can show risk hints such as:

- Auto-start service
- Runs as LocalSystem
- Path in user-writable location
- Missing/unknown PathName

These are not detections by themselves. They are context clues that help you decide what deserves closer inspection.

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

- Scheduled tasks
- Registry run keys
- Startup folders
- Network connections
- Defender settings
