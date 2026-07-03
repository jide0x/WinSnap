def process_key(proc):
    return f"{proc.get('Name')}|{proc.get('ExecutablePath')}|{proc.get('CommandLine')}"


def diff_processes(before, after):
    before_processes = {process_key(p): p for p in before.get("processes", [])}
    after_processes = {process_key(p): p for p in after.get("processes", [])}

    added_keys = after_processes.keys() - before_processes.keys()
    removed_keys = before_processes.keys() - after_processes.keys()

    return {
        "added": [after_processes[key] for key in added_keys],
        "removed": [before_processes[key] for key in removed_keys],
    }