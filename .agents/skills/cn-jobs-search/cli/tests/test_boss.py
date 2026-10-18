import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import providers.boss as boss  # noqa: E402
from net import FetchError  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


class BossParseTest(unittest.TestCase):
    def test_search_parses_and_normalizes(self):
        jobs = boss.search(query="python", city_code="101010100", raw_file=str(FIX / "boss_search.json"))
        self.assertEqual(len(jobs), 2)
        j = jobs[0]
        self.assertEqual(j["title"], "Python 后端工程师")
        self.assertEqual(j["company"], "云启科技")
        self.assertEqual(j["salary"], "25-40K·14薪")
        self.assertEqual(j["city"], "北京")
        self.assertEqual(j["district"], "朝阳区·望京")
        self.assertIn("Python", j["tags"])
        self.assertIn("Docker", j["tags"])
        self.assertTrue(j["url"].endswith("/job_detail/enc-aaa.html"))
        self.assertTrue(j["posted_at"].startswith("20"))

    def test_blocked_code_raises_with_hint(self):
        with self.assertRaises(FetchError) as ctx:
            boss.search(query="x", city_code="101010100", raw_file=str(FIX / "boss_blocked.json"))
        self.assertEqual(ctx.exception.code, "BLOCKED")
        self.assertTrue(ctx.exception.hint)

    def test_detail_parses_description(self):
        job = boss.detail("sec-bbb", raw_file=str(FIX / "boss_detail.json"))
        self.assertEqual(job["title"], "大模型应用工程师")
        self.assertEqual(job["company"], "智源未来")
        self.assertIn("RAG 检索链路", job["description"])
        self.assertNotIn("alert", job["description"])
        self.assertEqual(job["experience"], "3-5年")

    def test_detail_url_security_id(self):
        url = "https://www.zhipin.com/job_detail/enc-bbb.html?securityId=sec-bbb"
        job = boss.detail(url, raw_file=str(FIX / "boss_detail.json"))
        self.assertEqual(job["id"], "enc-bbb")


if __name__ == "__main__":
    unittest.main()
