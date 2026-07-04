import ctypes
from datetime import datetime
import getpass
import platform
import shutil
import shlex
import socket
import textwrap

from src.collectors import collect_processes
from src.snapshot_store import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
    snapshot_path,
)
from src.differ import diff_processes
from src.ui import success, error, warning, info, bold


BOX_WIDTH = 38
LIST_WIDTH = 60
DIFF_WIDTH = 46
FIELD_LABEL_WIDTH = 12
ARG_LABEL_WIDTH = 18


def rule(width=BOX_WIDTH, char="═"):
    return char * width


def terminal_width():
    return min(shutil.get_terminal_size(fallback=(100, 20)).columns, 120)


def process_count(snapshot):
    return len(snapshot.get("processes", []))


def snapshot_collectors(snapshot):
    return snapshot.get("collector") or snapshot.get("collectors", [])


def parse_created_at(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_full_datetime(value):
    created_at = parse_created_at(value)
    if not created_at:
        return value or "Unknown"

    return f"{created_at:%Y-%m-%d} {created_at:%I:%M %p}"


def format_list_datetime(value):
    created_at = parse_created_at(value)
    if not created_at:
        return value or "Unknown"

    return f"{created_at:%b} {created_at.day} {created_at:%I:%M %p}"


def print_snapshot_summary(snapshot):
    print()
    print(info(rule()))
    print(bold("WinSnap".center(BOX_WIDTH)))
    print(info(rule()))
    print()
    print(f"Snapshot Name : {snapshot.get('name')}")
    print()
    print(f"Created       : {format_full_datetime(snapshot.get('created_at'))}")
    print()
    print(f"Processes     : {process_count(snapshot)}")
    print()
    print(bold("Collector(s)"))
    print()
    for collector in snapshot_collectors(snapshot):
        print(success(f" • {collector.title()}"))
    print()
    print(info(rule()))
    print()


def print_process(process, marker=""):
    name = process.get("Name") or "Unknown"
    print(bold(name if not marker else f"{marker} {name}"))
    print()

    print_field("PID", process.get("ProcessId"))
    print_field("Parent PID", process.get("ParentProcessId"))
    print_field("Path", process.get("ExecutablePath") or "Unknown")

    command_line = process.get("CommandLine") or "Unknown"
    print_command(command_line)


def parse_command_line(command_line):
    if not command_line or command_line == "Unknown":
        return []

    try:
        argc = ctypes.c_int()
        command_line_to_argv = ctypes.windll.shell32.CommandLineToArgvW
        command_line_to_argv.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        command_line_to_argv.restype = ctypes.POINTER(ctypes.c_wchar_p)

        argv = command_line_to_argv(command_line, ctypes.byref(argc))
        if not argv:
            return []
        parts = [clean_argument(argv[i]) for i in range(argc.value)]
        ctypes.windll.kernel32.LocalFree(argv)
        return parts
    except Exception:
        try:
            return [clean_argument(part) for part in shlex.split(command_line, posix=False)]
        except ValueError:
            return []


def clean_argument(argument):
    if len(argument) >= 2 and argument[0] == argument[-1] == '"':
        return argument[1:-1]
    return argument


def print_command(command_line):
    parts = parse_command_line(command_line)
    if not parts:
        print_field("Command", command_line)
        return

    print()
    print(bold(" Command"))
    print_field("  Exe", parts[0])

    args = parts[1:]
    if not args:
        return

    print("  Args")
    for label, value in command_arguments(args):
        print_argument(label, value)


def command_arguments(args):
    parsed = []
    index = 0

    while index < len(args):
        arg = args[index]

        if arg == "-" and index + 1 < len(args):
            parsed.append(("Argument", " ".join(args[index:])))
            break

        if is_flag(arg) and "=" in arg:
            label, value = arg.split("=", 1)
            parsed.append((label, value))
            index += 1
            continue

        if is_flag(arg) and ":" in arg and index + 1 >= len(args):
            label, value = arg.split(":", 1)
            parsed.append((label, value))
            index += 1
            continue

        if is_flag(arg) and index + 1 < len(args) and not is_flag(args[index + 1]):
            parsed.append((arg, args[index + 1]))
            index += 2
            continue

        parsed.append((arg, None))
        index += 1

    return parsed


def is_flag(argument):
    return argument not in {"-", "--"} and argument.startswith(("-", "/"))


def print_argument(label, value):
    if value is None:
        print(f"    {label}")
        return

    label_text = f"    {label:<{ARG_LABEL_WIDTH}} "
    indent = " " * len(label_text)
    width = max(40, terminal_width() - len(label_text))
    lines = wrap_value(value, width)

    print(f"{label_text}{lines[0]}")
    for line in lines[1:]:
        print(f"{indent}{line}")


def print_field(label, value):
    label_text = f" {label:<{FIELD_LABEL_WIDTH}} "
    indent = " " * len(label_text)
    width = max(40, terminal_width() - len(label_text))
    lines = wrap_value(value, width)

    print(f"{label_text}{lines[0]}")
    for line in lines[1:]:
        print(f"{indent}{line}")


def wrap_value(value, width):
    return textwrap.wrap(
        str(value),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or ["Unknown"]


def create_snapshot(name):
    if snapshot_path(name).exists():
        print(warning(f'Snapshot "{name}" already exists.'))
        print()
        print("Overwrite?")
        print()
        response = input("[y/N] ").strip().lower()
        if response != "y":
            print(warning("Snapshot not overwritten."))
            return

    snapshot = {
        "name": name,
        "version": "0.2",
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "windows_version": platform.platform(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "collector": ["processes"],
        "processes": collect_processes(),
    }

    save_snapshot(snapshot)
    print_snapshot_summary(snapshot)


def show_snapshot(name):
    snapshot = load_snapshot(name)
    print_snapshot_summary(snapshot)


def list_all_snapshots():
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]

    if not snapshots:
        print(warning("No snapshots found."))
        return

    print()
    print(info(rule(LIST_WIDTH)))
    print()
    print(bold("Snapshots"))
    print()
    print(f"{'Name':<13} {'Created':<22} {'Processes':>9}")
    print()
    print("-" * LIST_WIDTH)
    print()
    for snap in snapshots:
        print(
            f"{snap.get('name', 'Unknown'):<13} "
            f"{format_list_datetime(snap.get('created_at')):<22} "
            f"{process_count(snap):>9}"
        )
    print()
    print(info(rule(LIST_WIDTH)))
    print()


def remove_snapshot(name):
    delete_snapshot(name)
    print(success(f"Deleted snapshot: {name}"))


def diff_snapshots(before_name, after_name):
    before = load_snapshot(before_name)
    after = load_snapshot(after_name)

    diff = diff_processes(before, after)

    print(info(rule(DIFF_WIDTH)))
    print()
    print(bold("Difference Report"))
    print()
    print(f"Before : {before.get('name')}")
    print(f"After  : {after.get('name')}")
    print()
    print(info(rule(DIFF_WIDTH)))
    print()

    print(success(f"Added Processes ({len(diff['added'])})"))
    print()
    for process in diff["added"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_process(process)
        print()

    print()
    print(error(f"Removed Processes ({len(diff['removed'])})"))
    print()
    for process in diff["removed"]:
        print(info(rule(DIFF_WIDTH, "─")))
        print()
        print_process(process)
        print()
