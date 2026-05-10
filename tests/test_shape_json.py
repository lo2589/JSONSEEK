import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.commands.shape_cmd import build_shape_tree
from jsonseek.types import ShapeNode


class TestShapeJson(unittest.TestCase):
    def test_simple_object(self):
        data = {"name": "test", "count": 2}
        shape = build_shape_tree(data)
        self.assertEqual(shape.node_kind, "object")
        self.assertEqual(len(shape.children), 2)
        paths = [c.path for c in shape.children]
        self.assertIn("name", paths)
        self.assertIn("count", paths)

    def test_nested_object(self):
        data = {"meta": {"ok": True}}
        shape = build_shape_tree(data)
        meta = [c for c in shape.children if c.path == "meta"][0]
        self.assertEqual(meta.node_kind, "object")
        self.assertEqual(len(meta.children), 1)
        self.assertEqual(meta.children[0].path, "meta.ok")

    def test_array_sample(self):
        data = {"items": [{"id": 1}, {"id": 2}]}
        shape = build_shape_tree(data, array_mode="sample")
        items = [c for c in shape.children if c.path == "items"][0]
        self.assertEqual(items.node_kind, "array")
        self.assertEqual(len(items.children), 1)
        self.assertEqual(items.children[0].path, "items[*]")
        self.assertEqual(items.children[0].count, 2)

    def test_max_depth(self):
        data = {"a": {"b": {"c": 1}}}
        shape = build_shape_tree(data, max_depth=1)
        a = [c for c in shape.children if c.path == "a"][0]
        self.assertEqual(len(a.children), 0)


if __name__ == "__main__":
    unittest.main()
