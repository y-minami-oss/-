"""project_sheet パッケージのテスト(APIキー・OAuth不要、合成データ)。

実行: python -m unittest tests.test_project_sheet -v
"""

from __future__ import annotations

import datetime as dt
import unittest

from project_sheet import master, report
from project_sheet.aggregate import aggregate_dc_rows


def _row(date, plays, likes=0, comments=0, shares=0, saves=0, prof=0, reach=0, fol=0):
    return {
        "投稿日": date,
        "再生回数": plays,
        "いいね": likes,
        "コメント": comments,
        "シェア": shares,
        "保存数": saves,
        "プロフィール閲覧数": prof,
        "リーチ数": reach,
        "フォロワー増加数": fol,
    }


class AggregateTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            _row(dt.datetime(2026, 5, 3), 1000, likes=30, comments=5, shares=3, saves=2, prof=100, reach=900, fol=10),
            _row("2026/05/20", 2000, likes=40, comments=0, shares=0, saves=10, prof=200, reach=1800, fol=20),
            _row(dt.datetime(2026, 4, 28), 9999, prof=999, reach=9999, fol=99),  # 別の月は除外
            _row("", 5000),  # 日付なしは除外
        ]

    def test_filters_by_month(self):
        kpi = aggregate_dc_rows(self.rows, 2026, 5)
        self.assertEqual(kpi.posts, 2)
        self.assertEqual(kpi.plays, 3000)
        self.assertEqual(kpi.profile_views, 300)
        self.assertEqual(kpi.reach, 2700)
        self.assertEqual(kpi.follower_gain, 30)

    def test_engagement_rate(self):
        kpi = aggregate_dc_rows(self.rows, 2026, 5)
        # (70 likes + 5 comments + 3 shares + 12 saves) / 3000 * 100
        self.assertAlmostEqual(kpi.engagement_rate, 90 / 3000 * 100, places=4)

    def test_empty_month(self):
        kpi = aggregate_dc_rows(self.rows, 2026, 1)
        self.assertEqual(kpi.posts, 0)
        self.assertEqual(kpi.engagement_rate, 0.0)

    def test_handles_comma_strings(self):
        rows = [_row("2026/05/01", "1,234")]
        self.assertEqual(aggregate_dc_rows(rows, 2026, 5).plays, 1234)


class MasterTest(unittest.TestCase):
    def _grid(self):
        return [
            ["メモ"],
            ["No.", "クライアント名", "CS担当", "SSP担当", "TSP担当", "CC担当", "ステータス", "PJシート"],
            ["1", "A社", "田中", "三並", "", "佐藤", "アクティブ", "A社_PJ"],
            ["2", "B社", "三並", "", "", "", "終了済", "B社_PJ"],
            ["3", "C社", "", "鈴木", "", "", "アクティブ", "C社_PJ"],
            ["", "", "", "", "", "", "", ""],  # 空行は無視
        ]

    def test_parse_and_filter(self):
        recs = master.parse_master_grid(self._grid())
        self.assertEqual(len(recs), 3)
        active = master.active_clients_for(recs, "三並")
        names = [r.client for r in active]
        self.assertEqual(names, ["A社"])  # B社は終了済、C社は三並ではない
        self.assertEqual(active[0].roles_of("三並"), ["SSP担当"])


class ReportTest(unittest.TestCase):
    def test_block_contains_numbers_and_placeholders(self):
        rows = [_row("2026/05/01", 1000, prof=100, fol=10)]
        kpi = aggregate_dc_rows(rows, 2026, 5)
        block = report.format_client_block("A社", kpi, no="1", roles=["SSP担当"])
        self.assertIn("A社", block)
        self.assertIn("再生数", block)
        self.assertIn("1,000", block)
        self.assertIn(report.NEEDS_INPUT, block)  # 採用数などは要手入力


if __name__ == "__main__":
    unittest.main()
