import hashlib
import os
import tempfile
import unittest

from winsnap.files.hashing import file_metadata, sha256_file


class HashingTests(unittest.TestCase):
    def test_missing_file(self):
        meta = file_metadata("Z:/this/does/not/exist.exe")
        self.assertEqual(meta["hash_status"], "missing")

    def test_known_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "foo.bin")
            with open(p, "wb") as f:
                f.write(b"abc")
            from pathlib import Path
            h = sha256_file(Path(p))
            self.assertEqual(h, hashlib.sha256(b"abc").hexdigest())
            meta = file_metadata(p)
            self.assertEqual(meta["sha256"], h)
            self.assertEqual(meta["hash_status"], "success")


if __name__ == "__main__":
    unittest.main()
