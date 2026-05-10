import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.path_parser import parse_path, normalize_path, is_parent_path
from jsonseek.types import KeyToken, IndexToken


class TestParsePath(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_path(""), [])

    def test_simple_keys(self):
        self.assertEqual(parse_path("a.b.c"), [KeyToken("a"), KeyToken("b"), KeyToken("c")])

    def test_index(self):
        self.assertEqual(parse_path("items[0]"), [KeyToken("items"), IndexToken(0)])

    def test_multiple_indices(self):
        self.assertEqual(parse_path("a[0].b[1]"), [KeyToken("a"), IndexToken(0), KeyToken("b"), IndexToken(1)])

    def test_leading_index(self):
        self.assertEqual(parse_path("[0]"), [IndexToken(0)])

    def test_bracket_string_keys(self):
        self.assertEqual(parse_path("a[key1][key2]"), [KeyToken("a"), KeyToken("key1"), KeyToken("key2")])

    def test_mixed_bracket_and_dot(self):
        self.assertEqual(parse_path("a[key1].b[key2]"), [KeyToken("a"), KeyToken("key1"), KeyToken("b"), KeyToken("key2")])

    def test_bracket_with_index(self):
        self.assertEqual(parse_path("a[0][1]"), [KeyToken("a"), IndexToken(0), IndexToken(1)])

    def test_deeply_nested_brackets(self):
        self.assertEqual(
            parse_path("a[b][c][d]"),
            [KeyToken("a"), KeyToken("b"), KeyToken("c"), KeyToken("d")]
        )

    def test_bracket_then_dot(self):
        self.assertEqual(
            parse_path("a[key].sub"),
            [KeyToken("a"), KeyToken("key"), KeyToken("sub")]
        )

    def test_invalid_empty_key(self):
        with self.assertRaises(Exception):
            parse_path("a..b")

    def test_invalid_unclosed_bracket(self):
        with self.assertRaises(Exception):
            parse_path("a[0")

    def test_invalid_empty_bracket(self):
        with self.assertRaises(Exception):
            parse_path("a[]")


class TestNormalizePath(unittest.TestCase):
    def test_roundtrip(self):
        tokens = [KeyToken("a"), KeyToken("b"), IndexToken(0)]
        self.assertEqual(normalize_path(tokens), "a.b[0]")


class TestIsParentPath(unittest.TestCase):
    def test_direct_parent(self):
        self.assertTrue(is_parent_path("a.b", "a.b.c"))

    def test_same_path(self):
        self.assertTrue(is_parent_path("a.b", "a.b"))

    def test_not_parent(self):
        self.assertFalse(is_parent_path("a.b", "a.c"))

    def test_empty_parent(self):
        self.assertTrue(is_parent_path("", "a.b"))


if __name__ == "__main__":
    unittest.main()
