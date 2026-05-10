import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.walkers.field_scan import scan_fields_in_tree


class TestFieldsJson(unittest.TestCase):
    def test_flat(self):
        data = {"name": "test", "count": 2}
        stats = scan_fields_in_tree(data)
        self.assertIn("name", stats)
        self.assertIn("count", stats)
        self.assertEqual(stats["name"].count, 1)
        self.assertEqual(stats["count"].count, 1)

    def test_nested(self):
        data = {"a": {"id": 1}, "b": {"id": 2}}
        stats = scan_fields_in_tree(data)
        self.assertEqual(stats["id"].count, 2)
        self.assertEqual(len(stats["id"].paths), 2)

    def test_types(self):
        data = {"flag": True, "num": 1, "text": "s"}
        stats = scan_fields_in_tree(data)
        self.assertIn("boolean", stats["flag"].types)
        self.assertIn("integer", stats["num"].types)
        self.assertIn("string", stats["text"].types)


if __name__ == "__main__":
    unittest.main()
