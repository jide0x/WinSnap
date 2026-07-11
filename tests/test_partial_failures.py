import unittest

from winsnap.commands.diff import compatibility_report, diff_if_compatible
from winsnap.artifacts import ARTIFACTS_BY_KEY


class PartialFailureTests(unittest.TestCase):
    def test_failed_collector_skips_diff(self):
        before = {
            "services": [{"Name": "svc"}],
            "collector_status": {"services": {"status": "failed"}},
        }
        after = {
            "services": [{"Name": "svc"}],
            "collector_status": {"services": {"status": "success", "count": 1, "duration_ms": 1}},
        }
        diff = diff_if_compatible(before, after, ARTIFACTS_BY_KEY["services"])  # should be empty due to failure in before
        self.assertEqual(diff, {"added": [], "removed": [], "changed": []})

    def test_compatibility_marks_failed(self):
        before = {"processes": [], "collector_status": {"processes": {"status": "success"}}}
        after = {"processes": [], "collector_status": {"processes": {"status": "failed"}}}
        report = compatibility_report(before, after)
        # Processes first in ordering
        self.assertEqual(report[0]["status"], "skipped")
        self.assertIn("collection failed in after snapshot", report[0]["reason"])  # reason mentions failure


if __name__ == "__main__":
    unittest.main()
