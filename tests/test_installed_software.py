import unittest

from winsnap.collectors.installed_software import (
    _parse_install_date,
    _should_skip,
    _win32_key_path,
)


class InstalledSoftwareHelperTests(unittest.TestCase):
    def test_parse_install_date_eight_digits(self):
        self.assertEqual(_parse_install_date("20260710"), "2026-07-10")

    def test_parse_install_date_int(self):
        self.assertEqual(_parse_install_date(20260710), "2026-07-10")

    def test_parse_install_date_iso(self):
        self.assertEqual(_parse_install_date("2026-07-10"), "2026-07-10")

    def test_parse_install_date_empty(self):
        self.assertIsNone(_parse_install_date(""))

    def test_parse_install_date_none(self):
        self.assertIsNone(_parse_install_date(None))

    def test_parse_install_date_garbage(self):
        self.assertIsNone(_parse_install_date("not-a-date"))

    def test_should_skip_empty_display_name(self):
        self.assertTrue(_should_skip({"DisplayName": ""}))

    def test_should_skip_system_component(self):
        self.assertTrue(_should_skip({"DisplayName": "App", "SystemComponent": 1}))

    def test_should_skip_system_component_string(self):
        self.assertTrue(_should_skip({"DisplayName": "App", "SystemComponent": "1"}))

    def test_should_skip_release_type_update(self):
        self.assertTrue(_should_skip({"DisplayName": "App", "ReleaseType": "Security Update"}))

    def test_should_skip_release_type_hotfix(self):
        self.assertTrue(_should_skip({"DisplayName": "App", "ReleaseType": "Hotfix"}))

    def test_should_not_skip_normal(self):
        self.assertFalse(_should_skip({"DisplayName": "App", "SystemComponent": 0, "ReleaseType": "Software"}))

    def test_win32_key_path_reconstruction(self):
        self.assertEqual(
            _win32_key_path(
                "HKEY_LOCAL_MACHINE",
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                "{GUID}",
            ),
            r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\{GUID}",
        )


if __name__ == "__main__":
    unittest.main()
