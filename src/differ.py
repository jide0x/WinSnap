from collections import Counter, defaultdict


def process_key(proc):
    return f"{proc.get('Name')}|{proc.get('ExecutablePath')}|{proc.get('CommandLine')}"


def group_processes(processes):
    grouped = defaultdict(list)
    for process in processes:
        grouped[process_key(process)].append(process)
    return grouped


def diff_processes(before, after):
    before_grouped = group_processes(before.get("processes", []))
    after_grouped = group_processes(after.get("processes", []))
    before_counts = Counter({key: len(items) for key, items in before_grouped.items()})
    after_counts = Counter({key: len(items) for key, items in after_grouped.items()})

    added = []
    removed = []

    for key in sorted(after_counts.keys() | before_counts.keys()):
        added_count = after_counts[key] - before_counts[key]
        removed_count = before_counts[key] - after_counts[key]

        if added_count > 0:
            added.extend(after_grouped[key][:added_count])
        if removed_count > 0:
            removed.extend(before_grouped[key][:removed_count])

    return {
        "added": added,
        "removed": removed,
    }
