import unittest

from winsnap.artifacts import ARTIFACTS_BY_KEY
from winsnap.commands.diff import compatibility_report, diff_if_compatible
from winsnap.differ import diff_network_listeners, diff_registry_autoruns, diff_scheduled_tasks, diff_services, diff_startup_folders


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


class RegistryAutorunDiffTests(unittest.TestCase):
    def test_diff_registry_autoruns_added_removed_and_changed(self):
        before = {
            "registry_autoruns": [
                registry_autorun("OldValue"),
                registry_autorun("ChangedValue", Value="old.exe"),
            ]
        }
        after = {
            "registry_autoruns": [
                registry_autorun("NewValue"),
                registry_autorun("ChangedValue", Value="new.exe"),
            ]
        }

        diff = diff_registry_autoruns(before, after)

        self.assertEqual([autorun["ValueName"] for autorun in diff["added"]], ["NewValue"])
        self.assertEqual([autorun["ValueName"] for autorun in diff["removed"]], ["OldValue"])
        self.assertEqual(diff["changed"][0]["after"]["ValueName"], "ChangedValue")
        self.assertEqual(
            diff["changed"][0]["changes"]["Value"],
            {"before": "old.exe", "after": "new.exe"},
        )


class StartupFolderDiffTests(unittest.TestCase):
    def test_diff_startup_folders_added_removed_and_changed(self):
        before = {
            "startup_folders": [
                startup_item("OldItem.lnk"),
                startup_item("ChangedItem.lnk", TargetPath="old.exe"),
            ]
        }
        after = {
            "startup_folders": [
                startup_item("NewItem.lnk"),
                startup_item("ChangedItem.lnk", TargetPath="new.exe"),
            ]
        }

        diff = diff_startup_folders(before, after)

        self.assertEqual([item["Name"] for item in diff["added"]], ["NewItem.lnk"])
        self.assertEqual([item["Name"] for item in diff["removed"]], ["OldItem.lnk"])
        self.assertEqual(diff["changed"][0]["after"]["Name"], "ChangedItem.lnk")
        self.assertEqual(
            diff["changed"][0]["changes"]["TargetPath"],
            {"before": "old.exe", "after": "new.exe"},
        )


class NetworkListenerDiffTests(unittest.TestCase):
    def test_diff_network_listeners_added_removed_and_changed(self):
        before = {
            "network_listeners": [
                network_listener("TCP", "0.0.0.0", 8080, 100),
                network_listener("TCP", "127.0.0.1", 9000, 200, ProcessName="old.exe"),
            ]
        }
        after = {
            "network_listeners": [
                network_listener("UDP", "0.0.0.0", 5353, 300),
                network_listener("TCP", "127.0.0.1", 9000, 200, ProcessName="new.exe"),
            ]
        }

        diff = diff_network_listeners(before, after)

        self.assertEqual([listener["LocalPort"] for listener in diff["added"]], [5353])
        self.assertEqual([listener["LocalPort"] for listener in diff["removed"]], [8080])
        self.assertEqual(diff["changed"][0]["after"]["LocalPort"], 9000)
        self.assertEqual(
            diff["changed"][0]["changes"]["ProcessName"],
            {"before": "old.exe", "after": "new.exe"},
        )


class CompatibilityTests(unittest.TestCase):
    def test_compatibility_report_marks_missing_before_collectors_as_skipped(self):
        before = {"processes": []}
        after = {
            "processes": [],
            "services": [],
            "scheduled_tasks": [],
            "registry_autoruns": [],
            "startup_folders": [],
            "network_listeners": [],
        }

        report = compatibility_report(before, after)

        self.assertEqual(report[0], {"label": "Processes", "status": "compared"})
        self.assertEqual(
            report[1],
            {"label": "Services", "status": "skipped", "reason": "not present in before snapshot"},
        )
        self.assertEqual(
            report[2],
            {"label": "Scheduled Tasks", "status": "skipped", "reason": "not present in before snapshot"},
        )
        self.assertEqual(
            report[3],
            {"label": "Registry Autoruns", "status": "skipped", "reason": "not present in before snapshot"},
        )
        self.assertEqual(
            report[4],
            {"label": "Startup Folders", "status": "skipped", "reason": "not present in before snapshot"},
        )
        self.assertEqual(
            report[5],
            {"label": "Network Listeners", "status": "skipped", "reason": "not present in before snapshot"},
        )

    def test_diff_if_compatible_skips_missing_collector(self):
        before = {}
        after = {"services": [service("newsvc")]}

        diff = diff_if_compatible(before, after, ARTIFACTS_BY_KEY["services"])

        self.assertEqual(diff, {"added": [], "removed": [], "changed": []})

    def test_diff_if_compatible_dispatches_registered_diff(self):
        before = {"services": [service("oldsvc")]}
        after = {"services": [service("newsvc")]}

        diff = diff_if_compatible(before, after, ARTIFACTS_BY_KEY["services"])

        self.assertEqual([svc["Name"] for svc in diff["added"]], ["newsvc"])
        self.assertEqual([svc["Name"] for svc in diff["removed"]], ["oldsvc"])


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


def registry_autorun(name, **overrides):
    data = {
        "Hive": "HKCU",
        "KeyPath": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "ValueName": name,
        "Value": "C:\\Program Files\\Example\\example.exe",
    }
    data.update(overrides)
    return data


def startup_item(name, **overrides):
    data = {
        "Scope": "User",
        "FolderPath": "C:\\Users\\Example\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
        "Name": name,
        "FullName": f"C:\\Users\\Example\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{name}",
        "Extension": ".lnk",
        "Length": 123,
        "LastWriteTimeUtc": "2026-07-10T00:00:00.0000000Z",
        "TargetPath": "C:\\Program Files\\Example\\example.exe",
        "Arguments": "",
        "WorkingDirectory": "C:\\Program Files\\Example",
    }
    data.update(overrides)
    return data


def network_listener(protocol, address, port, pid, **overrides):
    data = {
        "Protocol": protocol,
        "LocalAddress": address,
        "LocalPort": port,
        "State": "Listen" if protocol == "TCP" else None,
        "OwningProcess": pid,
        "ProcessName": "example.exe",
        "ProcessPath": "C:\\Program Files\\Example\\example.exe",
        "ServiceNames": ["ExampleService"],
    }
    data.update(overrides)
    return data


if __name__ == "__main__":
    unittest.main()
