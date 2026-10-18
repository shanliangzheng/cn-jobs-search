import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import providers.liepin as liepin  # noqa: E402
from net import FetchError  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


class LiepinSearchTest(unittest.TestCase):
    def test_parse_cards(self):
        jobs = liepin.search(query="实车测试", city_name="成都",
                             raw_file=str(FIX / "liepin_search.json"))
        self.assertEqual(len(jobs), 2)
        j = jobs[0]
        self.assertEqual(j["source"], "liepin")
        self.assertEqual(j["id"], "1001")
        self.assertEqual(j["title"], "实车测试工程师")
        self.assertEqual(j["company"], "某汽车科技")
        self.assertEqual(j["salary"], "15-25k")
        self.assertEqual(j["city"], "成都")
        self.assertEqual(j["experience"], "3-5年")
        self.assertEqual(j["degree"], "本科")
        self.assertIn("ADAS", j["tags"])
        self.assertIn("/job/1001.shtml", j["url"])
        self.assertEqual(j["posted_at"], "2026-10-17")

    def test_blocked_maps_to_fetch_error(self):
        with self.assertRaises(FetchError) as ctx:
            liepin.search(query="x", raw_file=str(FIX / "liepin_blocked.json"))
        self.assertEqual(ctx.exception.code, "BLOCKED")
        self.assertTrue(ctx.exception.hint)

    def test_city_codes(self):
        self.assertEqual(liepin.CITY_CODES["成都"], "280020")
        self.assertEqual(liepin.CITY_CODES["北京"], "010")


class LiepinDetailTest(unittest.TestCase):
    def test_jsonld_detail(self):
        job = liepin.detail("1001", raw_file=str(FIX / "liepin_detail.html"))
        self.assertEqual(job["title"], "实车测试工程师")
        self.assertEqual(job["company"], "某汽车科技")
        self.assertEqual(job["city"], "成都")
        self.assertEqual(job["district"], "龙泉驿区")
        self.assertIn("测试用例执行", job["description"])
        self.assertNotIn("alert", job["description"])
        self.assertEqual(job["salary"], "15-25K")

    def test_id_from_url(self):
        self.assertEqual(liepin._job_id("https://www.liepin.com/job/1001.shtml"), "1001")
        self.assertEqual(liepin._job_id("1002"), "1002")

    def test_bad_id(self):
        with self.assertRaises(FetchError) as ctx:
            liepin._job_id("not-a-job")
        self.assertEqual(ctx.exception.code, "PARAM")


if __name__ == "__main__":
    unittest.main()
