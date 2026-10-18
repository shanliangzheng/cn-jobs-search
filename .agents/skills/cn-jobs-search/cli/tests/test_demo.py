import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import providers.demo as demo  # noqa: E402
from net import FetchError  # noqa: E402


class DemoTest(unittest.TestCase):
    def test_search_all(self):
        self.assertEqual(len(demo.search()), 6)

    def test_search_filters_by_keyword(self):
        jobs = demo.search(query="esp32")
        self.assertEqual([j["id"] for j in jobs], ["demo-embedded"])

    def test_search_filters_by_city(self):
        jobs = demo.search(city_code="101020100")
        self.assertEqual([j["city"] for j in jobs], ["上海"])

    def test_pagination(self):
        first = demo.search(page=1, page_size=4)
        second = demo.search(page=2, page_size=4)
        self.assertEqual(len(first), 4)
        self.assertEqual(len(second), 2)
        self.assertNotEqual(first[0]["id"], second[0]["id"])

    def test_detail(self):
        job = demo.detail("demo-data")
        self.assertEqual(job["title"], "数据分析师")
        self.assertIn("SQL", job["tags"])

    def test_detail_missing(self):
        with self.assertRaises(FetchError) as ctx:
            demo.detail("nope")
        self.assertEqual(ctx.exception.code, "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
