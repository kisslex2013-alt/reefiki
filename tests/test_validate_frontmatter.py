import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_frontmatter.py"
SPEC = importlib.util.spec_from_file_location("validate_frontmatter", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class FrontmatterValidatorTests(unittest.TestCase):
    def test_json_output_reports_rule_codes_and_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "project" / "wiki" / "concepts" / "broken.md"
            path.parent.mkdir(parents=True)
            path.write_text("No frontmatter\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = validator.main(["--format", "json", str(path)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(1, code)
        self.assertEqual("fail", payload["outcome"])
        self.assertEqual("frontmatter.missing", payload["errors"][0]["code"])
        self.assertTrue(payload["errors"][0]["path"].endswith("broken.md"))

    def test_json_output_reports_location_expected_and_actual(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "project" / "wiki" / "concepts" / "bad-type.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                """---
id: bad-type
type: weird
title: "Bad Type"
tags: [memory]
useful_when:
  - "check diagnostics"
date_added: 2026-05-31
use_count: 0
last_used: null
---
Body.
""",
                encoding="utf-8",
            )

            report = validator.validate_file_report(path)

        item = next(error for error in report if error["code"] == "frontmatter.unknown_type")
        self.assertEqual(3, item["line"])
        self.assertEqual(1, item["column"])
        self.assertEqual("weird", item["actual"])
        self.assertIn("concept", item["expected"])


if __name__ == "__main__":
    unittest.main()
