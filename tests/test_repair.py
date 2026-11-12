import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.repair import repair_generated_workspace


class RepairWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "generation-report.json").write_text("{}", encoding="utf-8")
        (self.root / "app.py").write_text("print('old')", encoding="utf-8")
        self.generation = {"output_path": str(self.root), "generated_files": [{"path": "app.py"}]}

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, changes):
        answer = json.dumps({"summary": "Fix mismatch", "changes": changes, "blocked": []})
        with patch("app.repair._provider_settings", return_value=("ollama", "test", "ollama", "http://localhost/v1")), \
             patch("app.repair._chat", return_value=answer):
            return repair_generated_workspace(self.generation, {"overall_status": "MISMATCH"}, 3)

    def test_applies_patch_and_keeps_backup(self):
        result = self._run([{"path": "app.py", "reason": "Correct response", "content": "print('new')"}])
        self.assertEqual(result["status"], "PATCHED_AWAITING_RETEST")
        self.assertEqual((self.root / "app.py").read_text(encoding="utf-8"), "print('new')")
        self.assertTrue((Path(result["history_path"]) / "backup" / "app.py").is_file())

    def test_rejects_path_not_in_generation_manifest(self):
        with self.assertRaises(Exception):
            self._run([{"path": "README.md", "reason": "x", "content": "new"}])

    def test_rejects_secret_like_content(self):
        with self.assertRaises(Exception):
            self._run([{"path": "app.py", "reason": "x", "content": "sk-abcdefghijklmnopqrstuvwxyz1234567890"}])

    def test_empty_change_list_does_not_claim_success(self):
        result = self._run([])
        self.assertEqual(result["status"], "NO_SAFE_PATCH")
        self.assertTrue(result["retest_required"])


if __name__ == "__main__":
    unittest.main()
