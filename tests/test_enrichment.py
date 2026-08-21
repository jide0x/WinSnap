import unittest
import os
import tempfile

from winsnap.enrichment import (
    attach_file_metadata,
    dedupe_paths,
    discover_referenced_paths,
    enrich_unique_paths,
)


class EnrichmentDiscoveryTests(unittest.TestCase):
    def test_discover_and_dedupe(self):
        snapshot = {
            "processes": [
                {"Name": "a.exe", "ExecutablePath": "C:/bin/a.exe"},
                {"Name": "b.exe", "ExecutablePath": None},
            ],
            "services": [
                {"PathName": '"C:/bin/svc.exe" --flag'},
            ],
            "registry_autoruns": [
                {"Value": "C:/bin/a.exe"},
            ],
            "firewall_rules": [
                {"Program": None},
            ],
        }
        discovered = discover_referenced_paths(snapshot)
        paths = [p for _, _, p in discovered]
        self.assertIn("C:/bin/a.exe", paths)
        self.assertIn("C:/bin/svc.exe", paths)
        self.assertNotIn(None, paths)

        unique = dedupe_paths(discovered)
        self.assertEqual(unique, ["C:/bin/a.exe", "C:/bin/svc.exe"])

    def test_attach_metadata(self):
        discovered = [
            ("processes", {"Name": "a.exe"}, "C:/bin/a.exe"),
            ("services", {"Name": "svc"}, "C:/bin/a.exe"),
        ]
        enriched = {"C:/bin/a.exe": {"path": "C:/bin/a.exe", "sha256": "abc"}}
        attach_file_metadata(discovered, enriched)
        self.assertEqual(discovered[0][1]["file"]["sha256"], "abc")
        self.assertEqual(discovered[1][1]["file"]["sha256"], "abc")

    def test_enrich_unique_paths_hashes_existing_files(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "app.exe")
            with open(p, "wb") as f:
                f.write(b"binary-content")
            enriched = enrich_unique_paths([p], no_signature=True, workers=2)
            self.assertEqual(enriched[p]["hash_status"], "success")
            self.assertEqual(enriched[p]["signature"], None)

    def test_enrich_unique_paths_no_hash_omits(self):
        enriched = enrich_unique_paths(["C:/does/not/matter.exe"], no_hash=True, workers=2)
        self.assertEqual(enriched, {})

    def test_missing_file_has_no_signature(self):
        enriched = enrich_unique_paths(["Z:/missing/file.exe"], workers=2)
        self.assertEqual(enriched["Z:/missing/file.exe"]["hash_status"], "missing")
        self.assertIsNone(enriched["Z:/missing/file.exe"]["signature"])


if __name__ == "__main__":
    unittest.main()
