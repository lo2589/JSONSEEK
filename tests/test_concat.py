import json
import os
import tempfile
import unittest

from jsonseek.commands.concat_cmd import handle_concat


class TestConcat(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def _make_json(self, name, data):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_concat_multiple_files(self):
        self._make_json("a.json", {"id": 1, "name": "alice"})
        self._make_json("b.json", {"id": 2, "name": "bob"})

        out_path = os.path.join(self.tmpdir, "out.jsonl")
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "*.json"),
            "output_file": out_path,
            "encoding": None,
            "no_sort": False,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 0)

        with open(out_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0]), {"id": 1, "name": "alice"})
        self.assertEqual(json.loads(lines[1]), {"id": 2, "name": "bob"})

    def test_concat_sorted_by_filename(self):
        self._make_json("z.json", {"letter": "z"})
        self._make_json("a.json", {"letter": "a"})
        self._make_json("m.json", {"letter": "m"})

        out_path = os.path.join(self.tmpdir, "out.jsonl")
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "*.json"),
            "output_file": out_path,
            "encoding": None,
            "no_sort": False,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 0)

        with open(out_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        letters = [json.loads(l)["letter"] for l in lines]
        self.assertEqual(letters, ["a", "m", "z"])

    def test_concat_no_sort(self):
        self._make_json("z.json", {"letter": "z"})
        self._make_json("a.json", {"letter": "a"})

        out_path = os.path.join(self.tmpdir, "out.jsonl")
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "*.json"),
            "output_file": out_path,
            "encoding": None,
            "no_sort": True,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 0)

        with open(out_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        # glob order is filesystem-dependent; just verify both records are present
        letters = {json.loads(l)["letter"] for l in lines}
        self.assertEqual(letters, {"a", "z"})

    def test_concat_single_file(self):
        self._make_json("solo.json", {"only": True})

        out_path = os.path.join(self.tmpdir, "out.jsonl")
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "solo.json"),
            "output_file": out_path,
            "encoding": None,
            "no_sort": False,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 0)

        with open(out_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0]), {"only": True})

    def test_concat_invalid_json(self):
        bad_path = os.path.join(self.tmpdir, "bad.json")
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("{not valid}")

        out_path = os.path.join(self.tmpdir, "out.jsonl")
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "*.json"),
            "output_file": out_path,
            "encoding": None,
            "no_sort": False,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 1)
        self.assertFalse(os.path.exists(out_path))

    def test_concat_no_match(self):
        args = type("Args", (), {
            "pattern": os.path.join(self.tmpdir, "*.missing"),
            "output_file": None,
            "encoding": None,
            "no_sort": False,
        })()

        ret = handle_concat(args)
        self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main()
