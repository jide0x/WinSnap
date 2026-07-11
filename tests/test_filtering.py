import unittest

from winsnap.filtering.engine import apply_filters


class FilteringTests(unittest.TestCase):
    def test_process_churn_filtered(self):
        before = {}
        after = {}
        diff = {
            "processes": {
                "added": [
                    {"Name": "firefox.exe", "ExecutablePath": "C:/Program Files/Mozilla Firefox/firefox.exe", "ProcessId": 100},
                ],
                "removed": [
                    {"Name": "firefox.exe", "ExecutablePath": "C:/Program Files/Mozilla Firefox/firefox.exe", "ProcessId": 200},
                ],
            }
        }
        filtered = apply_filters(before, after, diff, mode="default")
        self.assertEqual(len(filtered["processes"]["added"]), 0)
        self.assertEqual(len(filtered["processes"]["removed"]), 0)
        self.assertEqual(len(filtered["processes"]["_filtered"]["added"]), 1)
        self.assertEqual(len(filtered["processes"]["_filtered"]["removed"]), 1)

    def test_all_mode_preserves(self):
        diff = {
            "processes": {
                "added": [{"Name": "x", "ExecutablePath": "x"}],
                "removed": [{"Name": "x", "ExecutablePath": "x"}],
            }
        }
        out = apply_filters({}, {}, diff, mode="all")
        self.assertEqual(len(out["processes"]["added"]), 1)
        self.assertEqual(len(out["processes"]["removed"]), 1)


if __name__ == "__main__":
    unittest.main()
