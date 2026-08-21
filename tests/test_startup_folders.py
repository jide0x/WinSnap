import re
import unittest

from winsnap.collectors.startup_folders import _format_o


class StartupFolderHelperTests(unittest.TestCase):
    def test_format_o_round_trip(self):
        result = _format_o(1755700000123456789)
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}Z$")

    def test_format_o_zero_fraction(self):
        result = _format_o(1755700000000000000)
        self.assertTrue(result.endswith(".0000000Z"))


if __name__ == "__main__":
    unittest.main()
