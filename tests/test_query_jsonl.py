import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.walkers.query_scan import scan_query_hits_in_record
from jsonseek.types import JsonlRecord


class TestQueryJsonl(unittest.TestCase):
    def test_record_meta(self):
        record = JsonlRecord(record_index=5, line_number=10, data={"name": "alice"})
        hits = scan_query_hits_in_record(record, "alice", match_mode="value")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].record_index, 5)
        self.assertEqual(hits[0].line_number, 10)

    def test_record_id_field(self):
        record = JsonlRecord(record_index=0, line_number=1, data={"id": "r1", "name": "bob"})
        hits = scan_query_hits_in_record(record, "bob", match_mode="value", record_id_field="id")
        self.assertEqual(hits[0].record_id, "r1")


if __name__ == "__main__":
    unittest.main()
