from src.snapshot_store import list_snapshots, load_snapshot
from src.views.search_view import print_process_search


def search_snapshots(query, details=False):
    snapshots = [load_snapshot(path.stem) for path in list_snapshots()]
    print_process_search(snapshots, query, details=details)
