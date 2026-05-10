import unittest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.commands.shape_cmd import build_shape_tree_from_jsonl


class TestShapeJsonl(unittest.TestCase):
    def test_sample_records(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            f.write(json.dumps({"name": "alice", "age": 30}) + "\n")
            f.write(json.dumps({"name": "bob", "age": 25}) + "\n")
            path = f.name

        try:
            shape = build_shape_tree_from_jsonl(path, sample_size=100, max_depth=None, array_mode="sample")
            self.assertEqual(shape.node_kind, "array")
            paths = [c.path for c in shape.children]
            self.assertIn("age", paths)
            self.assertIn("name", paths)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
