import re
import unittest

from winsnap.collectors.local_users import _format_last_logon


class LocalUserHelperTests(unittest.TestCase):
    def test_zero_returns_none(self):
        self.assertIsNone(_format_last_logon(0))

    def test_none_returns_none(self):
        self.assertIsNone(_format_last_logon(None))

    def test_valid_timestamp_is_iso(self):
        result = _format_last_logon(1755700000)
        self.assertIsNotNone(result)
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()
