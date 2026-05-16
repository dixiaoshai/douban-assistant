from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from douban_assistant.douban import load_cookie


class LoadCookieTests(unittest.TestCase):
    def test_load_cookie_reads_raw_cookie_header_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cookie_file = Path(tmpdir) / "douban_cookie.txt"
            cookie_file.write_text('bid=abc; dbcl2="123:xyz"', encoding="utf-8")

            result = load_cookie(cookie=None, cookie_file=str(cookie_file))

        self.assertEqual(result, 'bid=abc; dbcl2="123:xyz"')

    def test_load_cookie_reads_tabular_cookie_export_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cookie_file = Path(tmpdir) / "cookie.md"
            cookie_file.write_text(
                'bid\tabc\t.douban.com\t/\n'
                'dbcl2\t"123:xyz"\t.douban.com\t/\n',
                encoding="utf-8",
            )

            result = load_cookie(cookie=None, cookie_file=str(cookie_file))

        self.assertEqual(result, 'bid=abc; dbcl2="123:xyz"')


if __name__ == "__main__":
    unittest.main()
