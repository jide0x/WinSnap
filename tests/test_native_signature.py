import os
import tempfile
import unittest

from winsnap.files.signature import (
    _hr,
    _status_from_hr,
    verify_signature,
    verify_signatures_bulk,
    CERT_E_UNTRUSTEDROOT,
    TRUST_E_BAD_DIGEST,
    TRUST_E_NOSIGNATURE,
    TRUST_E_SUBJECT_FORM_UNKNOWN,
)


class SignatureStatusMappingTests(unittest.TestCase):
    def test_verified(self):
        self.assertEqual(_status_from_hr(0), "verified")

    def test_unsigned(self):
        self.assertEqual(_status_from_hr(_hr(TRUST_E_NOSIGNATURE)), "unsigned")
        self.assertEqual(_status_from_hr(_hr(TRUST_E_SUBJECT_FORM_UNKNOWN)), "unsigned")

    def test_invalid(self):
        self.assertEqual(_status_from_hr(_hr(TRUST_E_BAD_DIGEST)), "invalid")

    def test_untrusted(self):
        self.assertEqual(_status_from_hr(_hr(CERT_E_UNTRUSTEDROOT)), "untrusted")

    def test_unavailable(self):
        self.assertEqual(_status_from_hr(_hr(0x80004005)), "unavailable")


class NativeSignatureTests(unittest.TestCase):
    def test_unsigned_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "unsigned.bin")
            with open(path, "wb") as f:
                f.write(b"MZ" + b"\x00" * 4096)
            result = verify_signature(path)
            self.assertEqual(result["status"], "unsigned")
            self.assertIsNone(result["publisher"])

    def test_bulk_returns_entry_for_each_path(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "a.bin")
            p2 = os.path.join(d, "b.bin")
            with open(p1, "wb") as f:
                f.write(b"MZ" + b"\x00" * 4096)
            result = verify_signatures_bulk([p1, p2])
            self.assertEqual(set(result.keys()), {p1, p2})
            self.assertEqual(result[p1]["status"], "unsigned")

    def test_bulk_empty(self):
        self.assertEqual(verify_signatures_bulk([]), {})


if __name__ == "__main__":
    unittest.main()
