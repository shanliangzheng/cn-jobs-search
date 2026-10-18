import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cookies  # noqa: E402


class CookieTest(unittest.TestCase):
    def test_normalize_string(self):
        self.assertEqual(cookies.from_string("a=1; b=2"), "a=1; b=2")
        self.assertEqual(cookies.from_string("Cookie: a=1;b=2"), "a=1; b=2")

    def test_netscape_file(self):
        content = ("# Netscape HTTP Cookie File\n"
                   ".zhipin.com\tTRUE\t/\tFALSE\t0\t__zp_stoken__\tabc\n"
                   ".example.com\tTRUE\t/\tFALSE\t0\tother\tzzz\n")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            got = cookies.from_netscape(path, domain="zhipin.com")
            self.assertEqual(got, "__zp_stoken__=abc")
        finally:
            os.unlink(path)

    def test_resolve_prefers_explicit(self):
        os.environ["CN_JOBS_COOKIE"] = "env=1"
        try:
            self.assertEqual(cookies.resolve("cli=1", None, "boss", "zhipin.com"), "cli=1")
        finally:
            del os.environ["CN_JOBS_COOKIE"]


if __name__ == "__main__":
    unittest.main()
