from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from douban_assistant.cli import main


class ApplyCliTests(unittest.TestCase):
    def test_apply_command_requires_literal_yes_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / "plan.json"
            plan_file.write_text("[]", encoding="utf-8")

            runner = CliRunner()
            result = runner.invoke(main, ["apply-tag-updates", "--plan-file", str(plan_file)])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Pass --confirm YES", result.output)


if __name__ == "__main__":
    unittest.main()
