import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from winsnap.files import cache as cache_mod
from winsnap.files.cache import cache_key
from winsnap.files.hashing import file_metadata
from winsnap.enrichment import enrich_unique_paths


class HashCacheTests(unittest.TestCase):
    def test_load_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / ".hashcache.json"
            with mock.patch.object(cache_mod, "cache_path", return_value=target):
                entries = {
                    "C:\\foo.exe": {
                        "size": 10,
                        "mtime_ns": 123,
                        "sha256": "abc",
                        "modified_at": "2026-01-01T00:00:00",
                        "hash_status": "success",
                        "signature": {"status": "verified"},
                    }
                }
                cache_mod.save_cache(entries)
                loaded = cache_mod.load_cache()
                self.assertEqual(loaded, entries)

    def test_load_cache_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "nope.json"
            with mock.patch.object(cache_mod, "cache_path", return_value=target):
                self.assertEqual(cache_mod.load_cache(), {})

    def test_cache_hit_returns_cached_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "app.exe")
            with open(p, "wb") as f:
                f.write(b"content")
            st = os.stat(p)
            key = cache_key(p)
            cache = {
                key: {
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "sha256": "deadbeef",
                    "modified_at": "2026-01-01T00:00:00",
                    "hash_status": "success",
                    "signature": None,
                }
            }
            meta = file_metadata(p, cache)
            self.assertEqual(meta["sha256"], "deadbeef")

    def test_cache_miss_on_size_change_rehashes(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "app.exe")
            with open(p, "wb") as f:
                f.write(b"content")
            cache = {}
            meta1 = file_metadata(p, cache)
            self.assertEqual(meta1["hash_status"], "success")
            with open(p, "wb") as f:
                f.write(b"longer content")
            meta2 = file_metadata(p, cache)
            self.assertNotEqual(meta2["sha256"], meta1["sha256"])

    def test_changed_file_invalidates_cached_signature(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "app.exe")
            with open(p, "wb") as f:
                f.write(b"v1")
            cache = {}
            file_metadata(p, cache)
            key = cache_key(p)
            cache[key]["signature"] = {"status": "verified"}
            with open(p, "wb") as f:
                f.write(b"v22")
            file_metadata(p, cache)
            self.assertIsNone(cache[key]["signature"])

    def test_signature_reused_from_cache(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "app.exe")
            content = b"binary content"
            with open(p, "wb") as f:
                f.write(content)
            st = os.stat(p)
            key = cache_key(p)
            cache = {
                key: {
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "modified_at": "2026-01-01T00:00:00",
                    "hash_status": "success",
                    "signature": {"status": "verified", "publisher": "Test Corp"},
                }
            }
            with mock.patch(
                "winsnap.enrichment.verify_signatures_bulk",
                side_effect=AssertionError("signature verification should be skipped"),
            ):
                enriched = enrich_unique_paths([p], cache=cache, workers=1)
            self.assertEqual(enriched[p]["signature"]["publisher"], "Test Corp")


if __name__ == "__main__":
    unittest.main()
