import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hexwise as hw


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.task = hw.load(ROOT / "examples/create.task.json")
        self.candidate = hw.load(ROOT / "examples/create.candidate.json")
        self.update = hw.load(ROOT / "examples/update.task.json")
        self.patch = hw.load(ROOT / "examples/update.candidate.json")
        self.base = bytes.fromhex(self.candidate["hex"])

    def test_create_and_update_behavior(self):
        created = hw.materialize(self.task, self.candidate)
        updated = hw.materialize(self.update, self.patch, created)
        self.assertEqual(hw.evaluate(self.task, created)["status"], "pass")
        self.assertEqual(hw.evaluate(self.update, updated)["status"], "pass")
        self.assertEqual(created, self.base)
        self.assertNotEqual(created, updated)

    def test_semantic_error_is_not_structural_success(self):
        data = hw.materialize(self.task, {**self.candidate, "hex": "c0035fd6"})
        self.assertEqual(hw.evaluate(self.task, data)["status"], "fail")

    def test_wraparound(self):
        result = hw.evaluate(self.task, self.base)
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["cases"], 11)

    def test_task_change_invalidates_candidate(self):
        for field, value in [("addend", 2), ("requirement", "changed"), ("task_id", "other")]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                hw.materialize({**self.task, field: value}, self.candidate)

    def test_unknown_fields_and_wrong_types(self):
        for candidate in [{**self.candidate, "command": "run"},
                          {**self.candidate, "hex": 100}]:
            with self.assertRaises(ValueError):
                hw.materialize(self.task, candidate)
        with self.assertRaises(ValueError):
            hw.validate_task({**self.task, "addend": True})

    def test_bad_hex(self):
        for value in ["", "0", "AA", "0x00", "00 00", "gg", "00\n", "a" * 8194]:
            with self.subTest(value=value[:10]), self.assertRaises(ValueError):
                hw.decode(value)

    def test_base_identity(self):
        with self.assertRaisesRegex(ValueError, "base hash"):
            hw.materialize(self.update, self.patch, b"\0" * 8)

    def test_patch_preconditions(self):
        original = self.patch["edits"][0]
        bad_edits = [
            [{**original, "before": "00000000"}],
            [{**original, "offset": 2}],
            [{**original, "offset": True}],
            [{**original, "offset": 8}],
            [{**original, "after": original["after"] * 2}],
            [original, original],
            [],
            [{**original, "before": "00", "after": "01"}],
        ]
        for edits in bad_edits:
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                hw.materialize(self.update, {**self.patch, "edits": edits}, self.base)

    def test_unknown_instructions_and_early_return(self):
        for data in [b"\0" * 8, bytes.fromhex("c0035fd6c0035fd6"),
                     bytes.fromhex("20040091c0035fd6")]:
            with self.assertRaises(ValueError):
                hw.inspect_payload(data)

    def test_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):
                hw.load(path)

    def test_cli_retains_failure_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = folder / "candidate.json"
            candidate.write_text(json.dumps({**self.candidate, "hex": "c0035fd6"}))
            out = folder / "run"
            command = [sys.executable, str(ROOT / "hexwise.py"),
                       str(ROOT / "examples/create.task.json"), str(candidate), "--out", str(out)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            self.assertEqual(hw.load(out / "report.json")["behavior"]["status"], "fail")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual((out / "candidate.bin").read_bytes(), bytes.fromhex("c0035fd6"))

    def test_invalid_candidate_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = folder / "candidate.json"
            candidate.write_text(json.dumps({**self.candidate, "task_sha256": "0" * 64}))
            out = folder / "run"
            result = subprocess.run([sys.executable, str(ROOT / "hexwise.py"),
                                     str(ROOT / "examples/create.task.json"), str(candidate),
                                     "--out", str(out)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
