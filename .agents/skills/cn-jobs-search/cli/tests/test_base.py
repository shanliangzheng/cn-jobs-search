import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import base  # noqa: E402


class CityTest(unittest.TestCase):
    def test_chinese_name(self):
        self.assertEqual(base.resolve_city("北京"), ("101010100", "北京"))

    def test_pinyin(self):
        self.assertEqual(base.resolve_city("shenzhen"), ("101280600", "深圳"))

    def test_raw_code(self):
        self.assertEqual(base.resolve_city("101020100")[0], "101020100")

    def test_default_is_nationwide(self):
        self.assertEqual(base.resolve_city(None), ("100010000", "全国"))
        self.assertEqual(base.resolve_city("全国"), ("100010000", "全国"))

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            base.resolve_city("火星")


class TextTest(unittest.TestCase):
    def test_strip_html_keeps_text_drops_script(self):
        text = base.strip_html("<p>你好</p><ul><li>一</li><li>二</li></ul><script>x</script>")
        self.assertIn("你好", text)
        self.assertIn("• 一", text)
        self.assertNotIn("alert", text)

    def test_display_width(self):
        self.assertEqual(base.dw("abc"), 3)
        self.assertEqual(base.dw("中文"), 4)
        self.assertEqual(base.dw("⭐"), 2)

    def test_clip(self):
        self.assertEqual(base.clip("abcdef", 4), "abc…")
        self.assertEqual(base.clip("ab", 4), "ab")


class FormatTest(unittest.TestCase):
    def test_table_headers(self):
        jobs = [base.norm_job(source="t", job_id="1", title="后端", company="A",
                              salary="10K", city="北京", tags=["Python"])]
        out = base.fmt_table(jobs)
        for h in ("标题", "公司", "薪资"):
            self.assertIn(h, out)

    def test_plain_includes_description(self):
        job = base.norm_job(source="t", job_id="1", title="T", company="C",
                            description="一段描述")
        self.assertIn("一段描述", base.fmt_plain(job))


if __name__ == "__main__":
    unittest.main()
