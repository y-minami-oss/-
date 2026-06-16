# -*- coding: utf-8 -*-
"""デコボコベース 採用・集客 マーケ投資プラン（50名版）1枚PDF"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
font_manager.fontManager.addfont(FONT)
matplotlib.rcParams["font.family"] = "IPAGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

NAVY = "#1b2a4a"; NAVY2 = "#27406b"; RED = "#e8462e"; REDBG = "#fdecea"
GRAY = "#5b6470"; LGRAY = "#eef1f5"; GREEN = "#1f9d6b"; BLUE = "#2f6db0"; BLUEBG = "#eaf1f9"

fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 140); ax.axis("off")


def box(x, y, w, h, fc, ec="none", lw=0, rounded=0.0):
    if rounded:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounded}",
                     fc=fc, ec=ec, lw=lw, mutation_aspect=1))
    else:
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))


def t(x, y, s, size, color="black", ha="left", va="center", weight="normal"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, weight=weight)


# ===== ヘッダー =====
box(0, 128, 100, 12, NAVY); box(0, 126.5, 100, 1.5, RED)
t(5, 135.5, "デコボコベース  採用・集客 マーケ投資プラン", 17, "white", weight="bold")
t(5, 130.6, "マーケ担当ドラフト / SNS効果測定データに基づく設計（50名拡大版）", 10, "#c9d4e6")
t(95, 135, "リスキリング", 8, "#9fb0cc", ha="right")
t(95, 131.3, "50名 / 実質352.5万円", 12.5, RED, ha="right", weight="bold")

# ===== 1. 現状診断（実データ）=====
t(5, 124, "① 現状診断 — SNS効果測定の実データ（TikTok @decobocobase / 月5.5万円）", 10.5, NAVY, weight="bold")
box(4, 106, 92, 16.5, LGRAY, rounded=0.5)
stats = [("月間再生", "12.9万回"), ("リーチ", "11.6万"), ("保存(平均)", "47件"),
         ("遷移率", "0.85%"), ("目標遷移率", "5.0%"), ("フォロワー増", "+66/月")]
for i, (k, v) in enumerate(stats):
    x = 7 + (i % 6) * 15
    t(x, 119.5, k, 7.8, GRAY)
    t(x, 116.3, v, 12, NAVY, weight="bold")
box(6, 107.5, 88, 6.2, REDBG, ec=RED, lw=1, rounded=0.4)
t(8, 111.7, "診断", 8, RED, weight="bold")
t(16, 111.7, "認知（リーチ）は強い。だが①遷移率0.85%＝獲得への誘導が弱い  ②応募/問合せのCV計測が未整備", 8.3, "#7a2a1c")
t(16, 108.6, "→ “SNS単体ではハードルが高い”。下流（獲得・採用・計測）の補強が必要。", 8.3, "#7a2a1c", weight="bold")

# ===== 2. ファネル別チャネル戦略 =====
t(5, 102.5, "② ファネル別チャネル戦略 — 既存SNS依存から“面”の設計へ", 10.5, NAVY, weight="bold")
funnel = [
    ("認知 (TOFU)", BLUEBG, BLUE, "SNS(TikTok/IG)＋YouTube", "既存の強みを拡張。\n保護者向け＝集客の鉱脈。\nYouTubeで採用ブランディング。"),
    ("獲得 (MOFU)", "#eef7f0", GREEN, "Web広告＋計測基盤/LP", "Indeed/Meta/リスティング。\n測定可能で即効性。\nまず計測の土台を整備。"),
    ("採用 (BOFU)", REDBG, RED, "RPO＋スカウト/リファラル", "採用代行で母集団形成と\n歩留まり改善。\n内製ハードルを外注で補完。"),
]
fw = 29
for i, (ph, bg, ec, ch, desc) in enumerate(funnel):
    x = 5 + i * (fw + 1.7)
    box(x, 87, fw, 13.5, bg, ec=ec, lw=1.3, rounded=0.6)
    t(x + 2, 98.3, ph, 9.5, ec, weight="bold")
    t(x + 2, 95.2, ch, 8.3, NAVY, weight="bold")
    t(x + 2, 91.2, desc, 7.5, GRAY)

# ===== 3. 50名 トラック配分 =====
t(5, 84, "③ リスキリング50名の配分 — “増えた26名”は下流（獲得・採用・計測）へ", 10.5, NAVY, weight="bold")
tracks = [
    ("採用マーケ/HR ＋ RPO連携運用", "採用代行ディレクション・スカウト・歩留まり設計", 12, "採用"),
    ("SNS/動画 制作（遷移率改善）", "CTA統一・保護者向け拡充・前回比+10名で量産", 10, "認知"),
    ("Web広告運用", "Indeed/Meta/リスティング・CPA管理", 8, "獲得"),
    ("生成AI活用（横断）", "コンテンツ量産・広告クリエイティブ・問合せ対応", 8, "横断"),
    ("計測・データ基盤 / CRO", "CV計測整備・LP改善（現状の最大の穴）", 6, "計測"),
    ("YouTube 採用ブランディング", "会社紹介/社員IV/1日密着・内製でコスト圧縮", 6, "認知"),
]
maxn = 12; rowh = 4.5; top = 78
for i, (name, desc, n, tag) in enumerate(tracks):
    y = top - i * (rowh + 0.5)
    box(4, y, 92, rowh, "#f6f8fb" if i % 2 else LGRAY, rounded=0.3)
    t(6, y + rowh - 1.5, name, 9, NAVY, weight="bold")
    t(6, y + 1.4, desc, 7.3, GRAY)
    box(50, y + rowh / 2 - 1.3, 8, 2.6, NAVY2, rounded=0.5)
    t(54, y + rowh / 2, tag, 7, "white", ha="center", weight="bold")
    bx, bw = 61, 22
    box(bx, y + rowh / 2 - 1.1, bw, 2.2, "#dde3ec", rounded=0.2)
    box(bx, y + rowh / 2 - 1.1, bw * n / maxn, 2.2, RED, rounded=0.2)
    t(bx + bw + 2, y + rowh / 2, f"{n}名", 10, RED, ha="left", weight="bold")
yt = top - 6 * (rowh + 0.5)
box(4, yt, 92, 4.2, NAVY, rounded=0.3)
t(6, yt + 2.1, "合計 育成人数", 10, "white", weight="bold")
t(66, yt + 2.1, "50名", 13, "white", ha="center", weight="bold")
t(94, yt + 2.1, "実質 352.5万円（前回24名+183.3万）", 9.5, "#ffd2c8", ha="right", weight="bold")

# ===== 4. チャネル投資ガイド & 期待成果 =====
t(5, 42.5, "④ チャネル投資ガイド（月額目安・ベンチ）", 10, NAVY, weight="bold")
box(4, 24, 45, 17, "#f6f8fb", ec="#d7deea", lw=1, rounded=0.5)
ch = [("RPO（採用代行）", "月20〜40万 / 初期は固定+成果報酬"),
      ("Web広告", "月30〜50万 / 採用課金10〜30万・人"),
      ("YouTube", "内製でランニング極小（人件費中心）"),
      ("既存SNS(TikTok)", "月5.5万 継続＋内製で投稿強化")]
for i, (k, v) in enumerate(ch):
    yy = 38 - i * 3.4
    t(6, yy, "●", 7, RED); t(8.5, yy, k, 8, NAVY, weight="bold"); t(8.5, yy - 1.5, v, 7.2, GRAY)

t(54, 42.5, "⑤ 期待成果・KPI（90日）", 10, NAVY, weight="bold")
box(51, 24, 45, 17, "#eaf7f0", ec=GREEN, lw=1, rounded=0.5)
kpi = [("プロフィール遷移率", "0.85% → 1.5% → 3.0%"),
       ("応募・問合せ", "“要確認” → まず計測可能化"),
       ("採用単価", "30〜50万 → 内製+RPOで圧縮"),
       ("費用対効果(KGI)", "年600万円相当を継続")]
for i, (k, v) in enumerate(kpi):
    yy = 38 - i * 3.4
    t(53, yy, "▶", 7, GREEN); t(55.5, yy, k, 8, "#1d5e42", weight="bold"); t(55.5, yy - 1.5, v, 7.2, "#1d5e42")

# ===== まとめ帯 =====
box(4, 13, 92, 8.5, NAVY, rounded=0.5)
t(6, 19, "マーケ担当の結論", 9, "#ffd2c8", weight="bold")
t(6, 15.4,
  "SNSは“認知エンジン”として機能済み。50名拡大の主眼は『計測基盤→Web広告→RPO』で獲得・採用の\n"
  "下流を内製化し、リーチを“応募・問い合わせ・採用”へ変換すること。SNS単体依存からファネル設計へ転換する。",
  8.2, "white")

t(5, 9, "■ 段階案：堅め40名（実質282万）/ 推奨50名（352.5万）/ 上限拡張60名（423万）", 8.3, GRAY)
t(5, 2.5, "デコボコベース株式会社 / 採用・集客マーケ投資プラン（ドラフト）", 7.3, GRAY)
t(95, 2.5, "作成日 2026-06-16", 7.3, GRAY, ha="right")

fig.savefig("/home/user/-/reskilling_plan_v2.pdf", format="pdf")
fig.savefig("/home/user/-/_preview2.png", format="png", dpi=110)
print("saved v2")
