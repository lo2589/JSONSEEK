import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.walkers.query_scan import scan_query_hits_in_tree


class TestQueryJson(unittest.TestCase):
    def test_key_match(self):
        data = {"name": "alice", "age": 30}
        hits = scan_query_hits_in_tree(data, "name", match_mode="key")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].match_type, "key")

    def test_value_match(self):
        data = {"name": "alice"}
        hits = scan_query_hits_in_tree(data, "alice", match_mode="value")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].match_type, "value")

    def test_both_match(self):
        data = {"title": "title"}
        hits = scan_query_hits_in_tree(data, "title", match_mode="both")
        self.assertEqual(len(hits), 2)  # key + value

    def test_parent_covers_child(self):
        data = {"a": {"b": {"c": 1}}}
        hits = scan_query_hits_in_tree(data, "a", match_mode="key")
        # Only root 'a' should be reported, not nested children
        paths = [h.path for h in hits]
        self.assertIn("a", paths)


if __name__ == "__main__":
    unittest.main()
