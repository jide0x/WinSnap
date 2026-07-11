from winsnap.snapshot_store import load_snapshot
from winsnap.schema import validate_snapshot
from winsnap.views.inspect_view import print_process_inspection


def inspect_snapshot(name, query, details=False):
    snapshot = load_snapshot(name)
    validate_snapshot(snapshot)
    print_process_inspection(snapshot, query, details=details)
