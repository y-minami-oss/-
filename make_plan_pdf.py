# -*- coding: utf-8 -*-
"""デコボコベース 次回リスキリング 施策設計 1枚絵PDF生成"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
font_manager.fontManager.addfont(FONT)
matplotlib.rcParams["font.family"] = "IPAGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

# カラーパレット
NAVY = "#1b2a4a"
NAVY2 = "#27406b"
RED = "#e8462e"
REDBG = "#fdecea"
GRAY = "#5b6470"
LGRAY = "#eef1f5"
GREEN = "#1f9d6b"

fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4 portrait
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 140)
ax.axis("off")


def box(x, y, w, h, fc, ec="none", lw=0, rounded=0.0, alpha=1.0):
    if rounded:
        p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounded}",
                           fc=fc, ec=ec, lw=lw, alpha=alpha, mutation_aspect=1)
    else:
        p = Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, alpha=alpha)
    ax.add_patch(p)


def text(x, y, s, size, color="black", weight="normal", ha="left", va="center"):
    ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va=va)


# ===== ヘッダー =====
box(0, 128, 100, 12, NAVY)
box(0, 126.5, 100, 1.5, RED)
text(5, 135.5, "デコボコベース  次回リスキリング 施策設計", 19, "white", "bold")
text(5, 130.5, "採用・集客の内製化プラン（1枚まとめ） / 助成金活用", 11, "#c9d4e6")
text(95, 134, "手出し上限", 8.5, "#9fb0cc", ha="right")
text(95, 130.8, "1,717,000円", 14, RED, "bold", ha="right")

# ===== 事業前提 =====
text(5, 122.5, "■ 事業前提", 11, NAVY, "bold")
facts = [
    ("事業", "発達障害支援のFC本部\n（凸凹が活きる社会を創る）"),
    ("拠点", "約300拠点 → 1,000拠点へ\n拡大フェーズ"),
    ("既存コスト", "外部委託 55万×12\n= 660万円/年（毎年発生）"),
]
fw = 30
for i, (k, v) in enumerate(facts):
    x = 5 + i * (fw + 2.5)
    box(x, 110, fw, 10, LGRAY, rounded=0.6)
    text(x + 2, 117.6, k, 9, RED, "bold")
    text(x + 2, 113.2, v, 8.3, GRAY)

# ===== 最優先ターゲット =====
text(5, 105.5, "■ 今回の最優先ターゲット（FC加盟開発は今回見送り）", 11, NAVY, "bold")
targets = [
    ("③ 人材採用の強化", "支援員・児発管・サビ管の採用難＆定着。\n1,000拠点拡大の最大ボトルネックを解消。"),
    ("① 利用者集客", "各拠点の稼働率＝売上の源泉。\n凸凹ガイド/Web/SNSで送客を内製化。"),
]
tw = 45
for i, (k, v) in enumerate(targets):
    x = 5 + i * (tw + 4)
    box(x, 94, tw, 9.5, REDBG, ec=RED, lw=1.4, rounded=0.7)
    text(x + 2.5, 100.7, k, 11.5, RED, "bold")
    text(x + 2.5, 96.5, v, 8.3, "#7a2a1c")

# ===== 5トラック × 人数配分 =====
text(5, 90, "■ 育成5トラックと人数配分（採用＋利用者集客に最適化）", 11, NAVY, "bold")
tracks = [
    ("B 採用マーケ / HR", "採用広報・スカウト・リファラル・定着設計", 7, "③採用"),
    ("A デジタルマーケ内製化", "SEO・Web広告・LP / CRO（凸凹ガイド強化）", 6, "①集客"),
    ("C SNS / 動画コンテンツ", "Instagram/TikTok/YouTube・採用広報＆口コミ", 5, "①③両方"),
    ("D データ分析・MA/CRM", "見学→契約・応募→入社の歩留まり可視化", 3, "①③両方"),
    ("E 生成AI活用（横断）", "コンテンツ量産・広告制作・問合せ効率化", 3, "横断"),
]
maxn = 7
rowh = 7.2
top = 80
for i, (name, desc, n, tag) in enumerate(tracks):
    y = top - i * (rowh + 0.6)
    box(4, y, 92, rowh, LGRAY if i % 2 else "#f6f8fb", rounded=0.4)
    text(6, y + rowh - 2.2, name, 10.5, NAVY, "bold")
    text(6, y + 2.0, desc, 8.2, GRAY)
    # タグ
    box(52, y + rowh / 2 - 1.6, 9, 3.2, NAVY2, rounded=0.6)
    text(56.5, y + rowh / 2, tag, 7.5, "white", "bold", ha="center")
    # バー
    bx, bw = 64, 22
    box(bx, y + rowh / 2 - 1.4, bw, 2.8, "#dde3ec", rounded=0.3)
    box(bx, y + rowh / 2 - 1.4, bw * n / maxn, 2.8, RED, rounded=0.3)
    text(bx + bw + 2, y + rowh / 2, f"{n}名", 11, RED, "bold", ha="left")

# 合計バー
yt = top - 5 * (rowh + 0.6)
box(4, yt, 92, 5.2, NAVY, rounded=0.4)
text(6, yt + 2.6, "合計　育成人数", 11, "white", "bold")
text(70, yt + 2.6, "24名", 15, "white", "bold", ha="center")
text(94, yt + 2.6, "実質 169.2万円", 11, "#ffd2c8", "bold", ha="right")

# ===== 予算サマリ =====
text(5, 38.5, "■ 申請サマリ（手出し1,717,000円から逆算）", 11, NAVY, "bold")
kpis = [
    ("申請人数", "24名", "予算内の最大"),
    ("実質負担", "169.2万円", "7.05万円/名"),
    ("助成率", "約78.6%", "75%＋賃金助成"),
    ("予算残", "約2.5万円", "171.7万−169.2万"),
]
kw = 22
for i, (k, v, sub) in enumerate(kpis):
    x = 4 + i * (kw + 1.5)
    box(x, 26, kw, 9, "#f6f8fb", ec="#d7deea", lw=1, rounded=0.6)
    text(x + kw / 2, 32.7, k, 8.5, GRAY, "bold", ha="center")
    text(x + kw / 2, 29.5, v, 13.5, NAVY, "bold", ha="center")
    text(x + kw / 2, 27.0, sub, 7, GRAY, ha="center")

# ===== ROI =====
box(4, 13, 92, 10, "#eaf7f0", ec=GREEN, lw=1.2, rounded=0.6)
text(6, 20.4, "■ なぜ効くか（ROIの考え方）", 9.5, GREEN, "bold")
text(6, 15.8,
     "外部委託は毎年660万円が発生。リスキリングは手出し169.2万円の一度の投資で、採用・集客を\n"
     "内製化する人材を24名育成。1年以内に外部委託コストの回収が見込め、以降は継続的に内製運用。",
     8.4, "#1d5e42")

# ===== 候補（堅め）=====
box(4, 6, 92, 5, LGRAY, rounded=0.5)
text(6, 8.5, "代替案：堅めに進めるなら 20名（実質141.0万円／予算に約30万円の余裕）も選択可。",
     8.5, GRAY)

# フッター
text(5, 2.3, "デコボコベース株式会社 / リスキリング施策設計", 7.5, GRAY)
text(95, 2.3, "作成日 2026-06-16", 7.5, GRAY, ha="right")

fig.savefig("/home/user/-/reskilling_plan.pdf", format="pdf")
print("saved reskilling_plan.pdf")
