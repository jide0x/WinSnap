import unittest

from winsnap.schema import validate_snapshot


class SnapshotValidationTests(unittest.TestCase):
    def test_valid_minimal_snapshot(self):
        snapshot = {"name": "ok", "created_at": "2026-01-01T00:00:00", "collectors": []}
        validate_snapshot(snapshot)  # should not raise

    def test_missing_required_field_raises(self):
        with self.assertRaises(ValueError):
            validate_snapshot({"created_at": "now"})

    def test_bad_collectors_type_raises(self):
        with self.assertRaises(ValueError):
            validate_snapshot({"name": "x", "created_at": "now", "collectors": "bad"})


if __name__ == "__main__":
    unittest.main()
