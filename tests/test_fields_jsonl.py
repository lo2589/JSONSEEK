import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.types import JsonlRecord
from jsonseek.walkers.field_scan import scan_fields_in_record, merge_field_stats, finalize_jsonl_field_stats


class TestFieldsJsonl(unittest.TestCase):
    def test_record_scan(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"name": "alice", "age": 30})
        stats = scan_fields_in_record(record)
        self.assertIn("name", stats)
        self.assertIn("age", stats)

    def test_merge_and_finalize(self):
        stats = {}
        s1 = scan_fields_in_record(JsonlRecord(record_index=0, line_number=1, data={"name": "a", "age": 1}))
        s2 = scan_fields_in_record(JsonlRecord(record_index=1, line_number=2, data={"name": "b"}))
        merge_field_stats(stats, s1)
        merge_field_stats(stats, s2)
        result = finalize_jsonl_field_stats(stats, 2)
        name_stat = [r for r in result if r.field == "name"][0]
        age_stat = [r for r in result if r.field == "age"][0]
        self.assertEqual(name_stat.record_count, 2)
        self.assertEqual(age_stat.record_count, 1)
        self.assertEqual(name_stat.coverage, 1.0)
        self.assertEqual(age_stat.coverage, 0.5)


if __name__ == "__main__":
    unittest.main()
