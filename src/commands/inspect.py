from src.snapshot_store import load_snapshot
from src.views.inspect_view import print_process_inspection


def inspect_snapshot(name, query, details=False):
    snapshot = load_snapshot(name)
    print_process_inspection(snapshot, query, details=details)
