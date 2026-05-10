import unittest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.types import JsonlRecord, KeyToken
from jsonseek.path_parser import parse_path
from jsonseek.commands.add_cmd import patch_jsonl_record_add
from jsonseek.commands.set_cmd import patch_jsonl_record_set
from jsonseek.commands.del_cmd import patch_jsonl_record_del
from jsonseek.io.rewrite import rewrite_jsonl_file
from jsonseek.io.jsonl_file import iter_jsonl_records


class TestPatchJsonl(unittest.TestCase):
    def test_record_add(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"name": "alice"})
        keep, new_data = patch_jsonl_record_add(record, 0, parse_path("tags"), "vip")
        self.assertTrue(keep)
        self.assertEqual(new_data["tags"], "vip")

    def test_record_set(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"name": "alice"})
        keep, new_data = patch_jsonl_record_set(record, 0, parse_path("name"), "bob")
        self.assertTrue(keep)
        self.assertEqual(new_data["name"], "bob")

    def test_record_del_field(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"name": "alice", "age": 30})
        keep, new_data = patch_jsonl_record_del(record, 0, parse_path("name"))
        self.assertTrue(keep)
        self.assertNotIn("name", new_data)

    def test_record_del_whole(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"name": "alice"})
        keep, new_data = patch_jsonl_record_del(record, 0, [])
        self.assertFalse(keep)
        self.assertIsNone(new_data)

    def test_rewrite_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            f.write(json.dumps({"name": "a"}) + "\n")
            f.write(json.dumps({"name": "b"}) + "\n")
            path = f.name

        try:
            rewrite_jsonl_file(
                path,
                transform_record=lambda rec: patch_jsonl_record_set(rec, 0, parse_path("name"), "A")
            )
            records = list(iter_jsonl_records(path))
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].data["name"], "A")
            self.assertEqual(records[1].data["name"], "b")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
