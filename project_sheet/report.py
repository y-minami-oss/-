"""集計結果を、プロジェクトシートに「コピペできる形」に整形する。

プロジェクトシートの「月次の目標と実績」に並ぶ項目に合わせて出力する:
  KGI:採用数 / KPI:リンククリック数 / KPI:プロフィール閲覧数 /
  KPI:フォロワー数 / KPI:再生数 / KPI:エンゲージメント率

このうち効果測定シート(簡単DC)から自動で出せるのは
  再生数・プロフィール閲覧数・フォロワー増加数・エンゲージメント率
の4つ。残りは手入力(出所が別)なので「▼要手入力」として枠だけ出す。
"""

from __future__ import annotations

from .aggregate import MonthlyKPI

NEEDS_INPUT = "▼要手入力"


def format_client_block(client: str, kpi: MonthlyKPI, *, no: str = "", roles: list[str] | None = None) -> str:
    """1クライアント分の記入内容ブロック(Markdown)。"""
    role_txt = ("/".join(roles)) if roles else ""
    head = f"### {client}"
    if no or role_txt:
        head += f"  (No.{no} {role_txt})".rstrip()

    lines = [
        head,
        f"対象月: {kpi.year}年{kpi.month}月  / 投稿本数: {kpi.posts}本",
        "",
        "【月次の目標と実績｜結果欄に貼る数字】",
        f"- KGI:採用数            … {NEEDS_INPUT}(商談・入塾・採用などの実績)",
        f"- KPI:リンククリック数   … {NEEDS_INPUT}(LINE/計測ツールの数値)",
        f"- KPI:プロフィール閲覧数 … {kpi.profile_views:,}",
        f"- KPI:フォロワー数      … +{kpi.follower_gain:,}(今月の増加。合計は前月実績+増加)",
        f"- KPI:再生数            … {kpi.plays:,}",
        f"- KPI:エンゲージメント率 … {kpi.engagement_rate:.2f}%",
        "",
        "【振り返りレポート用 参考値】",
        f"- リーチした数: {kpi.reach:,}",
        f"- いいね {kpi.likes:,} / コメント {kpi.comments:,} / シェア {kpi.shares:,} / 保存 {kpi.saves:,}",
        f"- LINE登録数: {NEEDS_INPUT}",
        f"- Googleアナリティクス(セッション/CV等): {NEEDS_INPUT}",
    ]
    return "\n".join(lines)


def format_report(month_label: str, blocks: list[str], *, errors: list[str] | None = None) -> str:
    """全クライアント分をまとめた出力。"""
    out = [f"# プロジェクトシート 記入内容 — {month_label}", ""]
    out.extend(b + "\n" for b in blocks)
    if errors:
        out.append("---")
        out.append("## 取得できなかったクライアント(要確認)")
        out.extend(f"- {e}" for e in errors)
    return "\n".join(out)
