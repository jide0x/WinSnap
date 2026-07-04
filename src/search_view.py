from collections import Counter

from src.inspect_view import matching_processes, process_name
from src.process_view import print_process
from src.snapshot_view import format_list_datetime
from src.ui import error, info, bold, rule


SEARCH_WIDTH = 80


def print_search_header(query):
    print(info(rule(SEARCH_WIDTH)))
    print()
    print(bold("Snapshot Search"))
    print()
    print(f"Query : {query}")
    print()
    print(info(rule(SEARCH_WIDTH)))
    print()


def snapshot_matches(snapshots, query):
    results = []
    for snapshot in snapshots:
        matches = matching_processes(snapshot, query)
        if matches:
            results.append((snapshot, matches))
    return results


def print_process_search(snapshots, query, details=False):
    results = snapshot_matches(snapshots, query)

    print_search_header(query)

    if not results:
        print(error("No matching snapshots found."))
        print()
        return

    total_matches = sum(len(matches) for _, matches in results)
    names = Counter(
        process_name(process)
        for _, matches in results
        for process in matches
    )

    print(bold("Summary"))
    print(f"  {'Snapshots searched':<24} {len(snapshots)}")
    print(f"  {'Snapshots containing':<24} {len(results)}")
    print(f"  {'Matching instances':<24} {total_matches}")
    print(f"  {'Unique process names':<24} {len(names)}")
    print()

    print(bold("Matching Snapshots"))
    print(f"  {'Name':<20} {'Created':<20} {'Matches':>7}  Top Names")
    print("  " + "-" * (SEARCH_WIDTH - 2))
    for snapshot, matches in results:
        snapshot_names = Counter(process_name(process) for process in matches)
        top_names = ", ".join(
            f"{name} ({count})"
            for name, count in snapshot_names.most_common(3)
        )
        print(
            f"  {snapshot.get('name', 'Unknown'):<20} "
            f"{format_list_datetime(snapshot.get('created_at')):<20} "
            f"{len(matches):>7}  "
            f"{top_names}"
        )
    print()

    print(bold("Process Names"))
    for name, count in names.most_common():
        print(f"  {name:<30} {count}")
    print()

    if not details:
        print(bold("Use --details to view matching process entries."))
        print()
        return

    print(bold("Details"))
    print()
    for snapshot, matches in results:
        print(info(rule(SEARCH_WIDTH, "─")))
        print()
        print(bold(f"Snapshot: {snapshot.get('name', 'Unknown')}"))
        print(f"Created : {format_list_datetime(snapshot.get('created_at'))}")
        print(f"Matches : {len(matches)}")
        print()

        for process in matches:
            print_process(process)
            print()
