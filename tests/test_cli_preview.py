from __future__ import annotations

import unittest

from click.testing import CliRunner

from douban_assistant.cli import main


class PreviewCliTests(unittest.TestCase):
    def test_preview_command_requires_book_limit_or_specific_book(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["preview-tag-updates", "--user-id", "100654183"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Use --limit or --book-url", result.output)


if __name__ == "__main__":
    unittest.main()
