from collections import Counter

from winsnap.artifacts import ARTIFACTS, matching_items
from winsnap.views.snapshot_view import format_list_datetime
from winsnap.views.ui import error, info, bold, rule


SEARCH_WIDTH = 96


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
        matches = {
            artifact.key: matching_items(snapshot, artifact, query)
            for artifact in ARTIFACTS
        }
        if any(matches.values()):
            results.append({"snapshot": snapshot, "matches": matches})
    return results


def print_snapshot_search(snapshots, query, details=False):
    results = snapshot_matches(snapshots, query)

    print_search_header(query)

    if not results:
        print(error("No matching snapshots found."))
        print()
        return

    print(bold("Summary"))
    print(f"  {'Snapshots searched':<24} {len(snapshots)}")
    print(f"  {'Snapshots containing':<24} {len(results)}")
    for artifact in ARTIFACTS:
        print(f"  {artifact.matching_label:<24} {total_matches(results, artifact)}")
    for artifact in ARTIFACTS:
        print(f"  {'Unique ' + artifact.label.lower():<24} {len(name_counts(results, artifact))}")
    print()

    print_matching_snapshots(results)

    for artifact in ARTIFACTS:
        print_match_counts(artifact.label, name_counts(results, artifact), 50)

    if not details:
        labels = ", ".join(artifact.label.lower() for artifact in ARTIFACTS)
        print(bold(f"Use --details to view matching entries for {labels}."))
        print()
        return

    print_details(results)


def print_matching_snapshots(results):
    print(bold("Matching Snapshots"))
    columns = " ".join(f"{artifact.short_label:>5}" for artifact in ARTIFACTS)
    print(f"  {'Name':<20} {'Created':<20} {columns}  Top Matches")
    print("  " + "-" * (SEARCH_WIDTH - 2))
    for result in results:
        snapshot = result["snapshot"]
        counts = " ".join(f"{len(result['matches'][artifact.key]):>5}" for artifact in ARTIFACTS)
        top_names = ", ".join(top_match_names(result, limit=2))
        print(
            f"  {snapshot.get('name', 'Unknown'):<20} "
            f"{format_list_datetime(snapshot.get('created_at')):<20} "
            f"{counts}  "
            f"{top_names}"
        )
    print()


def print_details(results):
    print(bold("Details"))
    print()
    for result in results:
        snapshot = result["snapshot"]
        print(info(rule(SEARCH_WIDTH, "─")))
        print()
        print(bold(f"Snapshot: {snapshot.get('name', 'Unknown')}"))
        print(f"Created : {format_list_datetime(snapshot.get('created_at'))}")
        for artifact in ARTIFACTS:
            print(f"{artifact.label:<9}: {len(result['matches'][artifact.key])}")
        print()

        for artifact in ARTIFACTS:
            items = result["matches"][artifact.key]
            if not items:
                continue

            print(bold(artifact.label))
            print()
            for item in items:
                artifact.print_item(item)
                print()


def total_matches(results, artifact):
    return sum(len(result["matches"][artifact.key]) for result in results)


def name_counts(results, artifact):
    return Counter(
        artifact.name(item)
        for result in results
        for item in result["matches"][artifact.key]
    )


def top_match_names(result, limit):
    names = []
    for artifact in ARTIFACTS:
        counts = Counter(artifact.name(item) for item in result["matches"][artifact.key])
        names.extend(f"{name} ({count})" for name, count in counts.most_common(limit))
    return names


def print_match_counts(title, counter, width):
    if not counter:
        return

    print(bold(title))
    for name, count in counter.most_common():
        print(f"  {name:<{width}} {count}")
    print()


def print_process_search(snapshots, query, details=False):
    print_snapshot_search(snapshots, query, details=details)
