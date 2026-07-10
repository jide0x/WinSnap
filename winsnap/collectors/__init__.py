from winsnap.collectors.processes import collect_processes
from winsnap.collectors.registry_autoruns import collect_registry_autoruns
from winsnap.collectors.scheduled_tasks import collect_scheduled_tasks
from winsnap.collectors.services import collect_services


__all__ = [
    "collect_processes",
    "collect_registry_autoruns",
    "collect_scheduled_tasks",
    "collect_services",
]
