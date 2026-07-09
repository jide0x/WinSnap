import unittest

from src.differ import diff_scheduled_tasks, diff_services
from src.views.diff_view import scheduled_task_risk_hints, service_risk_hints


class ServiceDiffTests(unittest.TestCase):
    def test_diff_services_added_removed_and_changed(self):
        before = {
            "services": [
                service("oldsvc"),
                service("changedsvc", State="Stopped"),
            ]
        }
        after = {
            "services": [
                service("newsvc"),
                service("changedsvc", State="Running"),
            ]
        }

        diff = diff_services(before, after)

        self.assertEqual([svc["Name"] for svc in diff["added"]], ["newsvc"])
        self.assertEqual([svc["Name"] for svc in diff["removed"]], ["oldsvc"])
        self.assertEqual(diff["changed"][0]["after"]["Name"], "changedsvc")
        self.assertEqual(
            diff["changed"][0]["changes"]["State"],
            {"before": "Stopped", "after": "Running"},
        )


class ServiceRiskHintTests(unittest.TestCase):
    def test_service_risk_hints(self):
        hints = service_risk_hints(
            service(
                "suspicioussvc",
                StartMode="Auto",
                StartName="LocalSystem",
                PathName="C:\\Users\\Public\\svc.exe",
            )
        )

        self.assertIn("Auto-start service", hints)
        self.assertIn("Runs as LocalSystem", hints)
        self.assertIn("Path in user-writable location", hints)

    def test_missing_path_hint(self):
        hints = service_risk_hints(service("missingpath", PathName=None))

        self.assertIn("Missing/unknown PathName", hints)


class ScheduledTaskDiffTests(unittest.TestCase):
    def test_diff_scheduled_tasks_added_removed_and_changed(self):
        before = {
            "scheduled_tasks": [
                scheduled_task("OldTask"),
                scheduled_task("ChangedTask", State="Ready"),
            ]
        }
        after = {
            "scheduled_tasks": [
                scheduled_task("NewTask"),
                scheduled_task("ChangedTask", State="Disabled"),
            ]
        }

        diff = diff_scheduled_tasks(before, after)

        self.assertEqual([task["TaskName"] for task in diff["added"]], ["NewTask"])
        self.assertEqual([task["TaskName"] for task in diff["removed"]], ["OldTask"])
        self.assertEqual(diff["changed"][0]["after"]["TaskName"], "ChangedTask")
        self.assertEqual(
            diff["changed"][0]["changes"]["State"],
            {"before": "Ready", "after": "Disabled"},
        )


class ScheduledTaskRiskHintTests(unittest.TestCase):
    def test_scheduled_task_risk_hints(self):
        hints = scheduled_task_risk_hints(
            scheduled_task(
                "SuspiciousTask",
                RunAsUser="SYSTEM",
                Triggers=["At logon"],
                Actions=["C:\\Users\\Public\\runner.exe"],
            )
        )

        self.assertIn("Enabled scheduled task", hints)
        self.assertIn("Runs as SYSTEM", hints)
        self.assertIn("Runs at logon", hints)
        self.assertIn("Action path in user-writable location", hints)

    def test_scheduled_task_command_host_hint(self):
        hints = scheduled_task_risk_hints(
            scheduled_task("CommandTask", Actions=["powershell.exe -EncodedCommand abc"])
        )

        self.assertIn("Executes command or scripting host", hints)


def service(name, **overrides):
    data = {
        "Name": name,
        "DisplayName": name,
        "State": "Stopped",
        "Status": "OK",
        "StartMode": "Manual",
        "StartName": "LocalService",
        "PathName": "C:\\Windows\\System32\\svchost.exe -k netsvcs",
        "ProcessId": 0,
    }
    data.update(overrides)
    return data


def scheduled_task(name, **overrides):
    data = {
        "TaskName": name,
        "TaskPath": "\\",
        "State": "Ready",
        "Author": "Microsoft Corporation",
        "RunAsUser": "SYSTEM",
        "Triggers": ["At log on"],
        "Actions": ["C:\\Windows\\System32\\cmd.exe /c echo test"],
    }
    data.update(overrides)
    return data


if __name__ == "__main__":
    unittest.main()
