"""対象月のKPIを集計する(データソースに依存しない純粋ロジック)。

入力は「列名 -> 値」の辞書のリスト(= 簡単DC の各行)。
gspread でも openpyxl でも、同じ形に整えてここに渡せば集計できる。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any

from . import dc


@dataclass
class MonthlyKPI:
    """対象月の集計結果。"""

    year: int
    month: int
    posts: int = 0
    plays: int = 0
    profile_views: int = 0
    reach: int = 0
    follower_gain: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    sums: dict[str, float] = field(default_factory=dict)

    @property
    def engagement_rate(self) -> float:
        """エンゲージメント率(%) = (いいね+コメント+シェア+保存) / 再生回数 * 100。"""
        if not self.plays:
            return 0.0
        return (self.likes + self.comments + self.shares + self.saves) / self.plays * 100


def _to_number(value: Any) -> float:
    """セルの値を数値に。カンマ・空・文字混じりも許容して 0 に倒す。"""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(value: Any) -> _dt.date | None:
    """投稿日セルを date に。datetime / 文字列(YYYY/MM/DD・YYYY-MM-DD)に対応。"""
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return _dt.datetime.strptime(text.split(" ")[0], fmt.split(" ")[0]).date()
        except ValueError:
            continue
    return None


def aggregate_dc_rows(rows: list[dict[str, Any]], year: int, month: int) -> MonthlyKPI:
    """簡単DC の行から、指定した年月に投稿されたものだけを集計する。"""
    kpi = MonthlyKPI(year=year, month=month)
    sums: dict[str, float] = {f: 0.0 for f in dc.SUM_FIELDS}

    for row in rows:
        d = _parse_date(row.get(dc.POSTED_AT))
        if d is None or d.year != year or d.month != month:
            continue
        kpi.posts += 1
        for f in dc.SUM_FIELDS:
            sums[f] += _to_number(row.get(f))

    kpi.sums = sums
    kpi.plays = int(sums[dc.PLAYS])
    kpi.profile_views = int(sums[dc.PROFILE_VIEWS])
    kpi.reach = int(sums[dc.REACH])
    kpi.follower_gain = int(sums[dc.FOLLOWER_GAIN])
    kpi.likes = int(sums[dc.LIKES])
    kpi.comments = int(sums[dc.COMMENTS])
    kpi.shares = int(sums[dc.SHARES])
    kpi.saves = int(sums[dc.SAVES])
    return kpi
