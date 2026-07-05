import unittest

from src.differ import diff_services
from src.diff_view import service_risk_hints


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


if __name__ == "__main__":
    unittest.main()
