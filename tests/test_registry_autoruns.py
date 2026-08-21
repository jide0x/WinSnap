import unittest

from winsnap.collectors.registry_autoruns import _coerce_str


class RegistryAutorunHelperTests(unittest.TestCase):
    def test_coerce_str_none(self):
        self.assertEqual(_coerce_str(None), "")

    def test_coerce_str_string(self):
        self.assertEqual(_coerce_str("C:\\app.exe"), "C:\\app.exe")

    def test_coerce_str_int(self):
        self.assertEqual(_coerce_str(123), "123")

    def test_coerce_str_list_joins_with_space(self):
        self.assertEqual(_coerce_str(["a", "b"]), "a b")

    def test_coerce_str_tuple_joins_with_space(self):
        self.assertEqual(_coerce_str(("x", "y")), "x y")


if __name__ == "__main__":
    unittest.main()
