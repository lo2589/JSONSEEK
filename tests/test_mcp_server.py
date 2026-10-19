import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jsonseek.mcp_server import TOOLS, _dispatch


def call(name, **arguments):
    response = _dispatch({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    return response["result"]


class TestMcpServer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp.name, "data.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump({"users": [{"name": "a"}, {"name": "b"}], "cfg": {"x": 1}}, f)
        self.jsonl_path = os.path.join(self.tmp.name, "data.jsonl")
        with open(self.jsonl_path, "w", encoding="utf-8") as f:
            f.write('{"id": 1}\n{"id": 2,\n{"id": 3}\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_initialize_and_list(self):
        init = _dispatch({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                          "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(init["result"]["serverInfo"]["name"], "jsonseek")
        listed = _dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertEqual(names, {tool["name"] for tool in TOOLS})
        self.assertIn("shape", names)

    def test_notification_gets_no_response(self):
        self.assertIsNone(_dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_get(self):
        result = call("get", file=self.json_path, path="users[1].name")
        self.assertFalse(result["isError"])
        self.assertEqual(json.loads(result["content"][0]["text"]), "b")

    def test_set_writes_file(self):
        result = call("set", file=self.json_path, path="cfg.x", value="42")
        self.assertFalse(result["isError"])
        self.assertEqual(result["structuredContent"]["after"], 42)
        with open(self.json_path, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["cfg"]["x"], 42)

    def test_dry_run_leaves_file(self):
        call("delete", file=self.json_path, path="users[0]", dry_run=True)
        with open(self.json_path, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["users"]), 2)

    def test_broken_jsonl_reported_then_repaired(self):
        broken = call("shape", file=self.jsonl_path)
        self.assertTrue(broken["isError"])
        self.assertIn("Line 2", broken["content"][0]["text"])
        call("replace_line", file=self.jsonl_path, line=2, content='{"id": 2}')
        self.assertFalse(call("shape", file=self.jsonl_path)["isError"])

    def test_missing_path_is_error(self):
        result = call("get", file=self.json_path, path="nope")
        self.assertTrue(result["isError"])

    def test_unknown_tool(self):
        response = _dispatch({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                              "params": {"name": "nope", "arguments": {}}})
        self.assertEqual(response["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
