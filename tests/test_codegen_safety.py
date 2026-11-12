import unittest
from pathlib import Path

from app.codegen import CodeGenerationError, _parse_json, _redact, _safe_relative_path


class CodeGenerationSafetyTests(unittest.TestCase):
    def test_accepts_relative_source_path(self):
        self.assertEqual(_safe_relative_path("src/main.py"), Path("src/main.py"))

    def test_rejects_parent_traversal(self):
        with self.assertRaises(CodeGenerationError):
            _safe_relative_path("../outside.py")

    def test_rejects_environment_file(self):
        with self.assertRaises(CodeGenerationError):
            _safe_relative_path(".env")

    def test_redacts_api_key_assignment(self):
        redacted = _redact('api_key="super-secret-value"')
        self.assertNotIn("super-secret-value", redacted)
        self.assertIn("REDACTED", redacted)

    def test_parses_json_object(self):
        self.assertEqual(_parse_json('{"content":"print(1)"}')["content"], "print(1)")


if __name__ == "__main__":
    unittest.main()
