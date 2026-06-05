"""「簡単DC」タブ(自動取得される投稿データ表)の列名定義。

効果測定シートには月別タブ(「5月」等)もあるが、2026年5月以降は
各投稿の数値が「簡単DC」タブに自動で溜まる運用に切り替わっている
(月別タブには「５月以降 数値は簡単DCを参照」と明記)。
このツールは「簡単DC」を1次データソースとして集計する。
"""

from __future__ import annotations

# 簡単DC の1行目(ヘッダー)に並ぶ列名。表記が変わったらここを直す。
POSTED_AT = "投稿日"
TITLE = "タイトル"
URL = "URL"
DURATION = "動画の秒数"
PLAYS = "再生回数"
LIKES = "いいね"
COMMENTS = "コメント"
SHARES = "シェア"
SAVES = "保存数"
PROFILE_VIEWS = "プロフィール閲覧数"
AVG_WATCH_TIME = "平均視聴時間"
FULL_VIEW_RATE = "フル視聴率"
REACH = "リーチ数"
FOLLOWER_GAIN = "フォロワー増加数"

# 集計で合計するカラム
SUM_FIELDS = [
    PLAYS,
    LIKES,
    COMMENTS,
    SHARES,
    SAVES,
    PROFILE_VIEWS,
    REACH,
    FOLLOWER_GAIN,
]

DEFAULT_SHEET_NAME = "簡単DC"
