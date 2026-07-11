from winsnap.snapshot_store import list_snapshots, load_snapshot
from winsnap.schema import validate_snapshot
from winsnap.views.search_view import print_process_search


def search_snapshots(query, details=False):
    snapshots = []
    for path in list_snapshots():
        snap = load_snapshot(path.stem)
        try:
            validate_snapshot(snap)
        except Exception:
            # Keep permissive for search; skip invalid snapshots
            continue
        snapshots.append(snap)
    print_process_search(snapshots, query, details=details)
