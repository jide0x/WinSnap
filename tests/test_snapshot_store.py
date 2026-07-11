import os
import unittest
from pathlib import Path

from winsnap.snapshot_store import save_snapshot, load_snapshot, delete_snapshot, snapshot_path


class SnapshotStoreTests(unittest.TestCase):
    def test_save_and_load_snapshot(self):
        name = "unittest_snapshot"
        path = snapshot_path(name)
        if path.exists():
            path.unlink()

        data = {"name": name, "created_at": "2026-01-01T00:00:00", "collectors": []}
        save_snapshot(data)
        self.assertTrue(path.exists())

        loaded = load_snapshot(name)
        self.assertEqual(loaded["name"], name)

        delete_snapshot(name)
        self.assertFalse(path.exists())

    def test_invalid_snapshot_name(self):
        with self.assertRaises(ValueError):
            snapshot_path("../../evil")

    def test_missing_snapshot_raises(self):
        name = "does_not_exist"
        with self.assertRaises(FileNotFoundError):
            load_snapshot(name)


if __name__ == "__main__":
    unittest.main()
