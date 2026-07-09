from collections import Counter

from src.views.diff_view import print_scheduled_task, print_service, service_name, task_name
from src.views.inspect_view import matching_processes, matching_scheduled_tasks, matching_services, process_name
from src.views.process_view import print_process
from src.views.snapshot_view import format_list_datetime
from src.views.ui import error, info, bold, rule


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
        process_matches = matching_processes(snapshot, query)
        service_matches = matching_services(snapshot, query)
        task_matches = matching_scheduled_tasks(snapshot, query)
        if process_matches or service_matches or task_matches:
            results.append((snapshot, process_matches, service_matches, task_matches))
    return results


def print_process_search(snapshots, query, details=False):
    results = snapshot_matches(snapshots, query)

    print_search_header(query)

    if not results:
        print(error("No matching snapshots found."))
        print()
        return

    total_process_matches = sum(len(processes) for _, processes, _, _ in results)
    total_service_matches = sum(len(services) for _, _, services, _ in results)
    total_task_matches = sum(len(tasks) for _, _, _, tasks in results)
    names = Counter(
        process_name(process)
        for _, processes, _, _ in results
        for process in processes
    )
    services = Counter(
        service_name(service)
        for _, _, service_matches, _ in results
        for service in service_matches
    )
    tasks = Counter(
        task_name(task)
        for _, _, _, task_matches in results
        for task in task_matches
    )

    print(bold("Summary"))
    print(f"  {'Snapshots searched':<24} {len(snapshots)}")
    print(f"  {'Snapshots containing':<24} {len(results)}")
    print(f"  {'Matching processes':<24} {total_process_matches}")
    print(f"  {'Matching services':<24} {total_service_matches}")
    print(f"  {'Matching tasks':<24} {total_task_matches}")
    print(f"  {'Unique process names':<24} {len(names)}")
    print(f"  {'Unique services':<24} {len(services)}")
    print(f"  {'Unique tasks':<24} {len(tasks)}")
    print()

    print(bold("Matching Snapshots"))
    print(f"  {'Name':<20} {'Created':<20} {'Proc':>5} {'Svc':>5} {'Task':>5}  Top Matches")
    print("  " + "-" * (SEARCH_WIDTH - 2))
    for snapshot, process_matches, service_matches, task_matches in results:
        snapshot_process_names = Counter(process_name(process) for process in process_matches)
        snapshot_service_names = Counter(service_name(service) for service in service_matches)
        snapshot_task_names = Counter(task_name(task) for task in task_matches)
        top_process_names = [
            f"{name} ({count})"
            for name, count in snapshot_process_names.most_common(2)
        ]
        top_service_names = [
            f"{name} ({count})"
            for name, count in snapshot_service_names.most_common(2)
        ]
        top_task_names = [
            f"{name} ({count})"
            for name, count in snapshot_task_names.most_common(2)
        ]
        top_names = ", ".join(top_process_names + top_service_names + top_task_names)
        print(
            f"  {snapshot.get('name', 'Unknown'):<20} "
            f"{format_list_datetime(snapshot.get('created_at')):<20} "
            f"{len(process_matches):>5} "
            f"{len(service_matches):>5} "
            f"{len(task_matches):>5}  "
            f"{top_names}"
        )
    print()

    if names:
        print(bold("Process Names"))
        for name, count in names.most_common():
            print(f"  {name:<30} {count}")
        print()

    if services:
        print(bold("Services"))
        for name, count in services.most_common():
            print(f"  {name:<50} {count}")
        print()

    if tasks:
        print(bold("Scheduled Tasks"))
        for name, count in tasks.most_common():
            print(f"  {name:<50} {count}")
        print()

    if not details:
        print(bold("Use --details to view matching process, service, and scheduled task entries."))
        print()
        return

    print(bold("Details"))
    print()
    for snapshot, process_matches, service_matches, task_matches in results:
        print(info(rule(SEARCH_WIDTH, "─")))
        print()
        print(bold(f"Snapshot: {snapshot.get('name', 'Unknown')}"))
        print(f"Created : {format_list_datetime(snapshot.get('created_at'))}")
        print(f"Processes: {len(process_matches)}")
        print(f"Services : {len(service_matches)}")
        print(f"Tasks    : {len(task_matches)}")
        print()

        if process_matches:
            print(bold("Processes"))
            print()
            for process in process_matches:
                print_process(process)
                print()

        if service_matches:
            print(bold("Services"))
            print()
            for service in service_matches:
                print_service(service)
                print()

        if task_matches:
            print(bold("Scheduled Tasks"))
            print()
            for task in task_matches:
                print_scheduled_task(task)
                print()
