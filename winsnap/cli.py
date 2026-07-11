import argparse
import sys

from winsnap.commands import (
    create_snapshot,
    diff_snapshots,
    inspect_snapshot,
    list_all_snapshots,
    search_snapshots,
    show_snapshot,
    remove_snapshot,
)
from winsnap.snapshot_store import list_snapshots
from winsnap.views.ui import error, info
from winsnap.version import VERSION


class WinSnapArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def build_parser():
    parser = WinSnapArgumentParser(
        prog="winsnap",
        description="WinSnap - lightweight Windows snapshot and change analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  winsnap create before --note "clean system"
  winsnap create after --note "after install"
  winsnap diff before after
  winsnap diff before after --details

Examples:
  winsnap list
  winsnap show before
  winsnap inspect before firefox
  winsnap inspect before LocalSystem --details
  winsnap search firefox
  winsnap search LocalSystem --details

Collectors:
  processes
  services
  scheduled tasks
  registry autoruns
  startup folders
  local users
  local groups
  installed software
  firewall rules
  network listeners
""",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"WinSnap {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", parser_class=WinSnapArgumentParser)

    create_parser = subparsers.add_parser("create", help="Create a process/service/scheduled task/registry autorun/startup folder/local users/local groups/installed software/network listener/firewall rule snapshot")
    create_parser.add_argument("name")
    create_parser.add_argument("--note", default="", help="Add a note to the snapshot")
    create_parser.add_argument("--profile", choices=["full", "core"], default="full", help="Select collector profile (default: full)")

    diff_parser = subparsers.add_parser("diff", help="Compare two snapshots")
    diff_parser.add_argument("before")
    diff_parser.add_argument("after")
    diff_parser.add_argument("--details", action="store_true", help="Show detailed process changes")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect matching processes/services/scheduled tasks/registry autoruns/startup items/network listeners in one snapshot")
    inspect_parser.add_argument("snapshot")
    inspect_parser.add_argument("query")
    inspect_parser.add_argument("--details", action="store_true", help="Show detailed matching entries")

    search_parser = subparsers.add_parser("search", help="Search all snapshots for processes/services/scheduled tasks/registry autoruns/startup items/network listeners")
    search_parser.add_argument("query")
    search_parser.add_argument("--details", action="store_true", help="Show detailed matches across snapshots")

    show_parser = subparsers.add_parser("show", help="Show snapshot summary")
    show_parser.add_argument("name")

    delete_parser = subparsers.add_parser("delete", help="Delete a snapshot")
    delete_parser.add_argument("name")

    subparsers.add_parser("list", help="List saved snapshots")
    subparsers.add_parser("version", help="Show WinSnap version")
    subparsers.add_parser("help", help="Show this help menu")

    return parser


def print_existing_snapshots():
    snapshots = list_snapshots()
    if not snapshots:
        return

    print()
    print("Existing snapshots:")
    print()
    for snapshot in snapshots:
        print(snapshot.stem)
    print()


def configure_output():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def run_command(args, parser):
    if args.command in {None, "help"}:
        parser.print_help()
        return

    if args.command == "version":
        print(info(f"WinSnap {VERSION}"))
        return

    if args.command == "create":
        create_snapshot(args.name, note=args.note, profile=args.profile)
        return

    if args.command == "diff":
        diff_snapshots(args.before, args.after, details=args.details)
        return

    if args.command == "inspect":
        inspect_snapshot(args.snapshot, args.query, details=args.details)
        return

    if args.command == "search":
        search_snapshots(args.query, details=args.details)
        return

    if args.command == "list":
        list_all_snapshots()
        return

    if args.command == "show":
        show_snapshot(args.name)
        return

    if args.command == "delete":
        remove_snapshot(args.name)


def main():
    configure_output()
    parser = build_parser()

    try:
        args = parser.parse_args()
        run_command(args, parser)
    except FileNotFoundError as e:
        print(error(f"Error: {e}"))
        print_existing_snapshots()
    except ValueError as e:
        print(error(f"Error: {e}"))
    except KeyboardInterrupt:
        print(error("\nOperation cancelled."))
    except Exception as e:
        print(error(f"Error: {e}"))


if __name__ == "__main__":
    main()
