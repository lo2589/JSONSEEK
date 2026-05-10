import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.commands.add_cmd import patch_json_add
from jsonseek.commands.set_cmd import patch_json_set
from jsonseek.commands.del_cmd import patch_json_del
from jsonseek.commands.append_cmd import patch_json_append
from jsonseek.errors import PatchError


class TestPatchJson(unittest.TestCase):
    def test_add_object(self):
        data = {"a": 1}
        patch_json_add(data, "b", 2)
        self.assertEqual(data["b"], 2)

    def test_add_duplicate_raises(self):
        data = {"a": 1}
        with self.assertRaises(PatchError):
            patch_json_add(data, "a", 2)

    def test_set_existing(self):
        data = {"a": 1}
        patch_json_set(data, "a", 99)
        self.assertEqual(data["a"], 99)

    def test_set_create_missing(self):
        data = {"a": 1}
        patch_json_set(data, "b", 99, create_missing=True)
        self.assertEqual(data["b"], 99)

    def test_set_missing_raises(self):
        data = {"a": 1}
        with self.assertRaises(PatchError):
            patch_json_set(data, "b", 99)

    def test_del_object(self):
        data = {"a": 1}
        patch_json_del(data, "a")
        self.assertNotIn("a", data)

    def test_del_missing_raises(self):
        data = {"a": 1}
        with self.assertRaises(PatchError):
            patch_json_del(data, "b")

    def test_append_array(self):
        data = {"items": [1, 2]}
        patch_json_append(data, "items", 3)
        self.assertEqual(data["items"], [1, 2, 3])

    def test_set_array_index(self):
        data = {"items": [1, 2]}
        patch_json_set(data, "items[0]", 99)
        self.assertEqual(data["items"][0], 99)

    def test_del_array_index(self):
        data = {"items": [1, 2, 3]}
        patch_json_del(data, "items[1]")
        self.assertEqual(data["items"], [1, 3])

    def test_set_bracket_key(self):
        data = {"meta": {"count": 1}}
        patch_json_set(data, "meta[count]", 99)
        self.assertEqual(data["meta"]["count"], 99)

    def test_add_bracket_key(self):
        data = {"a": {"b": 1}}
        patch_json_add(data, "a[c]", 2)
        self.assertEqual(data["a"]["c"], 2)

    def test_del_bracket_key(self):
        data = {"a": {"b": 1, "c": 2}}
        patch_json_del(data, "a[c]")
        self.assertEqual(data["a"], {"b": 1})

    def test_nested_bracket_keys(self):
        data = {"a": {"b": {"c": 1}}}
        patch_json_set(data, "a[b][c]", 99)
        self.assertEqual(data["a"]["b"]["c"], 99)


if __name__ == "__main__":
    unittest.main()
