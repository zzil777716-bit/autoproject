"""
========================================================================================
🧪 [CI/CD UNIT TEST: DATA INTEGRITY & HTS FILTERS]
Tests Pure Stock regex filters and dynamic HTS 0659 / 0198 / 0184 datasets.
========================================================================================
"""

import unittest
from collectors.hts_theme_collector import HTSThemeCollector, is_pure_individual_stock

class TestDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.collector = HTSThemeCollector()
        self.market_data = self.collector.collect_all()

    def test_pure_stock_filter_excludes_etfs(self):
        self.assertFalse(is_pure_individual_stock("KODEX 200", "069500"))
        self.assertFalse(is_pure_individual_stock("TIGER 미국S&P500", "360750"))
        self.assertFalse(is_pure_individual_stock("ACE 2차전지&친환경", "415580"))
        self.assertFalse(is_pure_individual_stock("삼성전자우", "005935"))
        self.assertFalse(is_pure_individual_stock("하나29호스팩", "430290"))

    def test_pure_stock_filter_allows_individual_stocks(self):
        self.assertTrue(is_pure_individual_stock("삼성전자", "005930"))
        self.assertTrue(is_pure_individual_stock("SK하이닉스", "000660"))
        self.assertTrue(is_pure_individual_stock("한미반도체", "042700"))
        self.assertTrue(is_pure_individual_stock("코나아이", "052400"))
        self.assertTrue(is_pure_individual_stock("S-Oil", "010950"))
        self.assertTrue(is_pure_individual_stock("다날", "064260"))

    def test_hts_0659_theme_ranks(self):
        themes = self.market_data["themes_0659"]
        self.assertEqual(len(themes), 3)
        self.assertEqual(themes[0]["rank"], 1)
        self.assertEqual(themes[1]["rank"], 2)
        self.assertEqual(themes[2]["rank"], 3)
        for t in themes:
            self.assertTrue(len(t["theme_name"]) > 0)
            self.assertTrue(len(t["top3_stocks"]) > 0)
            for s in t["top3_stocks"]:
                self.assertGreater(s["price"], 0)

    def test_kospi_kosdaq_separation(self):
        kospi = self.market_data["kospi_0184"]
        kosdaq = self.market_data["kosdaq_0184"]
        self.assertEqual(len(kospi), 20)
        self.assertEqual(len(kosdaq), 20)
        for s in kospi:
            self.assertEqual(s["market"], "KOSPI")
            self.assertGreater(s["price"], 0)
        for s in kosdaq:
            self.assertEqual(s["market"], "KOSDAQ")
            self.assertGreater(s["price"], 0)

if __name__ == "__main__":
    unittest.main()
