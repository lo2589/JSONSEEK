import unittest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.commands.diff_cmd import diff_values, filter_by_mode, load_side, handle_diff
from jsonseek.formatters import format_diff_result


def _kinds(diffs):
    return sorted((d["kind"], d["path"]) for d in diffs)


class TestDiffValues(unittest.TestCase):
    def test_identical(self):
        a = {"x": 1, "y": [1, 2], "z": {"k": "v"}}
        self.assertEqual(diff_values(a, dict(a)), [])

    def test_value_changed(self):
        diffs = diff_values({"x": 1}, {"x": 2})
        self.assertEqual(_kinds(diffs), [("value_changed", "x")])
        self.assertEqual(diffs[0]["before"], 1)
        self.assertEqual(diffs[0]["after"], 2)

    def test_added_removed(self):
        diffs = diff_values({"a": 1}, {"b": 2})
        self.assertEqual(_kinds(diffs), [("added", "b"), ("removed", "a")])

    def test_type_changed_no_recurse(self):
        diffs = diff_values({"x": {"deep": 1}}, {"x": [1, 2, 3]})
        self.assertEqual(_kinds(diffs), [("type_changed", "x")])

    def test_int_float_same_kind(self):
        # 1 == 1.0 且同属 number -> 无差异
        self.assertEqual(diff_values({"x": 1}, {"x": 1.0}), [])
        # 1 vs 2.0 -> 值变化，不是类型变化
        diffs = diff_values({"x": 1}, {"x": 2.0})
        self.assertEqual(_kinds(diffs), [("value_changed", "x")])

    def test_nested_path_syntax(self):
        diffs = diff_values({"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 9}}})
        self.assertEqual(diffs[0]["path"], "a.b.c")

    def test_array_index_and_length(self):
        diffs = diff_values([1, 2, 3], [1, 9])
        self.assertEqual(_kinds(diffs), [("removed", "[2]"), ("value_changed", "[1]")])

    def test_array_added(self):
        diffs = diff_values([1], [1, 2, 3])
        self.assertEqual(_kinds(diffs), [("added", "[1]"), ("added", "[2]")])

    def test_root_scalar(self):
        diffs = diff_values(1, 2)
        self.assertEqual(diffs[0]["path"], "")
        self.assertEqual(diffs[0]["kind"], "value_changed")

    def test_subtree_collapses(self):
        # 整棵新子树折叠成一条 added，不逐叶展开
        diffs = diff_values({}, {"sub": {"a": 1, "b": 2}})
        self.assertEqual(_kinds(diffs), [("added", "sub")])


class TestFilterByMode(unittest.TestCase):
    def setUp(self):
        # a 改 b：删 a.gone、加 a.new、a.val 改值、a.ty 改类型
        self.a = {"gone": 1, "val": "x", "ty": 1}
        self.b = {"new": 9, "val": "y", "ty": "now-string"}
        self.diffs = diff_values(self.a, self.b)

    def test_structure_hides_value_changes(self):
        kinds = {d["kind"] for d in filter_by_mode(self.diffs, "structure")}
        self.assertEqual(kinds, {"added", "removed", "type_changed"})

    def test_content_hides_add_remove(self):
        kinds = {d["kind"] for d in filter_by_mode(self.diffs, "content")}
        self.assertEqual(kinds, {"value_changed", "type_changed"})

    def test_both_keeps_all(self):
        kinds = {d["kind"] for d in filter_by_mode(self.diffs, "both")}
        self.assertEqual(kinds, {"added", "removed", "value_changed", "type_changed"})


class TestFormatDiff(unittest.TestCase):
    def test_identical_pretty(self):
        out = format_diff_result([], "a.json", "b.json", mode="both", output="pretty")
        self.assertIn("Files are identical.", out)

    def test_json_output_structure(self):
        diffs = diff_values({"x": 1}, {"x": 2, "y": 3})
        out = format_diff_result(diffs, "a.json", "b.json", mode="both", output="json")
        obj = json.loads(out)
        self.assertFalse(obj["identical"])
        self.assertEqual(obj["summary"]["changed"], 1)
        self.assertEqual(obj["summary"]["added"], 1)
        self.assertEqual(len(obj["diffs"]), 2)


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestHandleDiff(unittest.TestCase):
    def _write(self, tmp, name, text):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def test_handle_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write(tmp, "a.json", json.dumps({"x": 1, "drop": True}))
            b = self._write(tmp, "b.json", json.dumps({"x": 2, "add": 5}))
            args = _Args(file_a=a, file_b=b, mode="both", kind=None,
                         output="json", encoding=None, max_results=None)
            rc = handle_diff(args)
            self.assertEqual(rc, 0)

    def test_handle_jsonl_index(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write(tmp, "a.jsonl", '{"id":1,"v":"a"}\n{"id":2,"v":"b"}\n')
            b = self._write(tmp, "b.jsonl", '{"id":1,"v":"a"}\n{"id":2,"v":"CHANGED"}\n')
            data_a = load_side(a, None, None)
            data_b = load_side(b, None, None)
            diffs = diff_values(data_a, data_b)
            self.assertEqual(_kinds(diffs), [("value_changed", "[1].v")])


if __name__ == "__main__":
    unittest.main()
