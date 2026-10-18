import json
import subprocess
import sys
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "src" / "cli.py"


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *args],
                          capture_output=True, text=True, timeout=60)


class CliTest(unittest.TestCase):
    def test_missing_query(self):
        p = run("search", "--provider", "boss", "--raw", "/nonexistent")
        self.assertEqual(p.returncode, 2)
        self.assertIn("MISSING_REQUIRED", p.stderr)

    def test_providers_json(self):
        p = run("providers")
        self.assertEqual(p.returncode, 0)
        names = {x["name"] for x in json.loads(p.stdout)}
        self.assertEqual(names, {"boss", "demo"})

    def test_search_demo_json(self):
        p = run("search", "-q", "llm", "--provider", "demo", "-f", "json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(data["count"], 1)
        self.assertTrue(any("大模型" in j["title"] for j in data["jobs"]))

    def test_search_demo_table(self):
        p = run("search", "-q", "python", "--provider", "demo")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Python 后端工程师", p.stdout)

    def test_detail_demo(self):
        p = run("detail", "demo-embedded", "--provider", "demo")
        self.assertEqual(p.returncode, 0)
        self.assertIn("ESP32", p.stdout)

    def test_detail_demo_json(self):
        p = run("detail", "demo-llm-app", "--provider", "demo", "-f", "json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["job"]["title"], "大模型应用工程师")

    def test_limit(self):
        p = run("search", "--provider", "demo", "--limit", "2", "-f", "json")
        self.assertEqual(len(json.loads(p.stdout)["jobs"]), 2)


if __name__ == "__main__":
    unittest.main()
