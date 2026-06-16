# -*- coding: utf-8 -*-
"""デコボコベース 採用・集客 +20%成長プラン（統合版・2ページ）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
font_manager.fontManager.addfont(FONT)
matplotlib.rcParams["font.family"] = "IPAGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

NAVY="#1b2a4a"; RED="#e8462e"; REDBG="#fdecea"; GRAY="#5b6470"; LGRAY="#eef1f5"
GREEN="#1f9d6b"; GREENBG="#eaf7f0"; BLUE="#2f6db0"; BLUEBG="#eaf1f9"; GOLD="#c98a1a"; GOLDBG="#fbf2e0"
PURP="#6b4ea0"; PURPBG="#f0eaf7"

def new_page():
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,140); ax.axis("off")
    return fig, ax

def box(ax,x,y,w,h,fc,ec="none",lw=0,r=0.0):
    if r:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",fc=fc,ec=ec,lw=lw,mutation_aspect=1))
    else:
        ax.add_patch(Rectangle((x,y),w,h,fc=fc,ec=ec,lw=lw))

def t(ax,x,y,s,size,color="black",ha="left",va="center",weight="normal"):
    ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,weight=weight)

def header(ax,title,sub,tag):
    box(ax,0,128,100,12,NAVY); box(ax,0,126.5,100,1.5,RED)
    t(ax,5,135.3,title,15.5,"white",weight="bold")
    t(ax,5,130.6,sub,9.5,"#c9d4e6")
    t(ax,95,135,"目標",8,"#9fb0cc",ha="right")
    t(ax,95,131.3,tag,11.5,RED,ha="right",weight="bold")

def drow(ax,x,y,name,effect,tag,tagc):
    t(ax,x,y,name,8.2,NAVY,weight="bold")
    t(ax,x,y-2.2,effect,7.2,GRAY)
    box(ax,x+62,y-1.4,11,3.0,tagc,r=0.4)
    t(ax,x+67.5,y+0.1,tag,7,"white",ha="center",weight="bold")

pdf = PdfPages("/home/user/-/growth_plan.pdf")

# =================== PAGE 1 : マスタープラン ===================
fig, ax = new_page()
header(ax,"デコボコベース 採用・集客 +20%成長プラン",
       "業界特化・多拠点モデル / 12ヶ月（リスキリング除く）","採用・集客 +20%")

# ① 戦略の柱
t(ax,5,124,"① 戦略の柱 — 福祉×多拠点（約300拠点）の勝ち筋",10.5,NAVY,weight="bold")
box(ax,4,111.5,92,11.5,LGRAY,r=0.5)
t(ax,6,120,"直接ドライバー：①業界ポータル ②MEO ③地域連携営業 ④リファラル採用",8.4,NAVY,weight="bold")
t(ax,6,116.6,"増幅：PR（マテリアル連携／データPR・アーンドメディア）で信頼と指名検索を底上げ",8.2,PURP,weight="bold")
t(ax,6,113.3,"補完：SNS・Web広告・YouTube（素材化）・オウンド（凸凹ガイド）",8.2,GRAY)

# ② 集客ドライバー
t(ax,5,108.5,"② 集客ドライバー",10.5,NAVY,weight="bold")
box(ax,4,82.5,92,24,GREENBG,ec=GREEN,lw=1.1,r=0.5)
cd=[("業界ポータル掲載（LITALICO発達ナビ）","拠点あたり年約40問い合わせ・契約率約90%（他社事例）","直接",GREEN),
    ("MEO 多拠点一括最適化（カンリー等）","「地域名＋児発/就労移行」検索→見学に直結","直接",GREEN),
    ("地域連携営業（相談支援専門員・学校）","計画相談からの紹介。広告費ほぼ0","直接",GREEN),
    ("医療・ハローワーク連携（就労移行）","当事者の確度高い送客源","直接",GREEN),
    ("LP分離（集客/採用）＋LINE＋計測","各チャネルのCVR底上げ・取りこぼし防止","基盤",BLUE),
    ("SNS・Web広告（Indeed/Meta）","認知の上乗せ・補完","補完",GRAY)]
for i,(n,e,tg,c) in enumerate(cd):
    drow(ax,7,103-i*3.6,n,e,tg,c)

# ③ 採用ドライバー
t(ax,5,79,"③ 採用ドライバー",10.5,NAVY,weight="bold")
box(ax,4,57,92,20.5,REDBG,ec=RED,lw=1.1,r=0.5)
ad=[("リファラル採用の仕組化（MyRefer等）","採用単価1/3（他社事例）。有資格者に有効","直接",RED),
    ("LITALICO仕事ナビ（成果報酬10%）","紹介会社手数料80〜120万を回避","直接",RED),
    ("社員アドボカシー広報（note等）","採用コスト600万円削減・定着改善（他社事例）","直接",RED),
    ("RPO／Indeed最適化","母集団形成","補完",GRAY),
    ("採用LP＋LINE＋面接設計","応募→入社の歩留まり改善","基盤",BLUE)]
for i,(n,e,tg,c) in enumerate(ad):
    drow(ax,7,73.5-i*3.6,n,e,tg,c)

# ④ +20%ブリッジ
t(ax,5,53.5,"④ +20%の積み上げ（成長ブリッジ）— 安全マージン込み設計",10.5,NAVY,weight="bold")
drivers=[("業界ポータル＋MEO（集客）",8,GREEN),
         ("地域・医療・ハローワーク連携営業（集客）",6,GREEN),
         ("リファラル＋仕事ナビ＋採用広報（採用）",8,RED),
         ("LP分離・LINE・計測（CVR基盤／両方）",5,BLUE),
         ("PR（マテリアル）＋SNS/広告/YouTube（増幅）",4,PURP)]
maxv=10; bx=58; bw=27; top=49
for i,(n,v,c) in enumerate(drivers):
    y=top-i*3.8
    t(ax,6,y,n,7.8,NAVY)
    box(ax,bx,y-1.1,bw,2.2,"#dde3ec",r=0.2); box(ax,bx,y-1.1,bw*v/maxv,2.2,c,r=0.2)
    t(ax,bx+bw+1.5,y,f"+{v}pt",8,c,ha="left",weight="bold")
box(ax,4,25,92,4,NAVY,r=0.3)
t(ax,6,27,"設計値 合計 +31pt",9,"white",weight="bold")
t(ax,94,27,"ロス・季節変動を控除 → 目標 +20% を確保",9,"#ffd2c8",ha="right",weight="bold")

# まとめ帯
box(ax,4,13,92,8,NAVY,r=0.5)
t(ax,6,18.4,"要点",8.5,"#ffd2c8",weight="bold")
t(ax,14,18.4,"認知は十分。鍵は「業界ポータル・MEO・地域連携・リファラル」を本部のスケールで一括展開。",8.1,"white")
t(ax,14,15.2,"PR（マテリアル連携）で信頼を増幅し、各施策のCVR・採用歩留まりの係数を押し上げる。",8.1,"white")
t(ax,5,7,"デコボコベース株式会社 / 採用・集客 +20%成長プラン（統合版）  1/2",7.2,GRAY)
t(ax,95,7,"作成日 2026-06-16",7.2,GRAY,ha="right")
pdf.savefig(fig);
if True:
    fig.savefig("/home/user/-/_p1.png",dpi=110)

# =================== PAGE 2 : 実行シート ===================
fig, ax = new_page()
header(ax,"実行プラン：ロードマップ / PR / クイックウィン / コンプラ",
       "本部主導でスケール展開 / マテリアルグループ連携","12ヶ月で +20%")

# ① ロードマップ
t(ax,5,124,"① 12ヶ月ロードマップ",10.5,NAVY,weight="bold")
qs=[("Q1 (1-3月)","土台＋クイックウィン",BLUE,BLUEBG,
     ["計測基盤・LP分離・LINE構築","発達ナビ全拠点掲載／MEO一括導入","リファラル報奨金 規程改定","マテリアル:ブランド設計＋データPR企画","コンプラ監査体制を整備","累計 ±0%"]),
    ("Q2 (4-6月)","連携営業＋獲得",GREEN,GREENBG,
     ["相談支援員/学校/医療/HW連携の仕組化","Web広告テスト／LINEステップ配信","マテリアル:データPR第1弾 配信・露出","社員アドボカシー記事 開始","","累計 +6%"]),
    ("Q3 (7-9月)","拡大",GOLD,GOLDBG,
     ["ポータル・広告スケール","RPO母集団／リファラル全社浸透","マテリアル:TV/全国紙 刈取＋第2弾","YouTube素材をLP/求人に実装","","累計 +13%"]),
    ("Q4 (10-12月)","最適化・刈り取り",RED,REDBG,
     ["歩留まり改善・面接設計","全チャネル配分最適化","露出をLP/ポータルに実装し変換","指名検索・応募の質を測定","","累計 +20%"])]
cw=22
for i,(q,th,c,bg,items) in enumerate(qs):
    x=4+i*(cw+1.3)
    box(ax,x,98,cw,24.5,bg,ec=c,lw=1.1,r=0.5)
    box(ax,x,118,cw,4.5,c)
    t(ax,x+cw/2,120.2,q,7.8,"white",ha="center",weight="bold")
    t(ax,x+cw/2,115.6,th,8,c,ha="center",weight="bold")
    for j,it in enumerate(items[:-1]):
        if it: t(ax,x+1.3,112-j*2.7,"・"+it,6.3,NAVY,va="top")
    box(ax,x+1.3,99,cw-2.6,3,"white",ec=c,lw=0.8,r=0.3)
    t(ax,x+cw/2,100.5,items[-1],7.6,c,ha="center",weight="bold")

# ② PR(マテリアル)
t(ax,5,94.5,"② PR施策 — マテリアルグループ連携（フルサービス活用）",10.5,NAVY,weight="bold")
box(ax,4,70,92,22.5,PURPBG,ec=PURP,lw=1.1,r=0.5)
t(ax,6,89.5,"優先順位（推奨）",8.4,PURP,weight="bold")
pr=["① データPR（実態調査リリース）＝集客・採用の両取りで最も費用対効果が高い",
    "② ブランドストーリー設計（「凸凹は才能」）＝全施策のメッセージ基盤",
    "③ 採用ブランディングPR（認証取得・社員ストーリー）＝応募の質と定着",
    "④ メディア露出（TV/全国紙）＝上記が整った後に刈り取り"]
for i,p in enumerate(pr):
    t(ax,6,86-i*2.6,p,7.6,"#3d2c63")
box(ax,5.5,71,89,4.2,"white",ec=PURP,lw=0.9,r=0.4)
t(ax,7,73.1,"データPR第1弾案：「発達障害のある大人の就労・働きづらさ実態調査」→ ディーキャリア集客＋採用広報を同時に。調査設計〜記者リレーション〜コンプラ監修をマテリアルに委任。",6.9,"#3d2c63")

# ③ クイックウィン
t(ax,5,67,"③ クイックウィン（90日／本部主導で即着手）",10.5,NAVY,weight="bold")
box(ax,4,50,92,15.5,"#f6f8fb",ec="#d7deea",lw=1,r=0.5)
qw=[("1〜30日","発達ナビ 全約300拠点 一括掲載＋ページ改修（空き枠・教材写真・自己評価結果）"),
    ("31〜60日","MEO一括管理ツール導入＋300拠点の基本情報を標準化（GA4/UTMでCV計測に接続）"),
    ("61〜90日","リファラル報奨金 規程改定＋給与明細同送キャンペーン（正社員10〜15万/パート3万目安）")]
for i,(d,s) in enumerate(qw):
    yy=62-i*4.0
    box(ax,6,yy-1.4,9,3,RED,r=0.3); t(ax,10.5,yy+0.1,d,7,"white",ha="center",weight="bold")
    t(ax,17,yy,s,7.5,NAVY)

# ④ コンプラ
t(ax,5,47,"④ コンプラ・ガードレール（Q1で必ず整備）",10.5,NAVY,weight="bold")
box(ax,4,24,92,21.5,"#fff6f4",ec=RED,lw=1,r=0.5)
cp=["誇大広告の禁止（障害者総合支援法29条の4・景表法）：「No.1」「必ず改善」「100%就職」「不安を煽る表現」はNG",
    "個人情報：児童・利用者の顔写真は書面同意必須。無ければモザイク/後ろ姿で個人を特定不可に",
    "ステマ規制（景表法）：口コミに対価（粗品・金券）を提供して好意的評価を誘導する行為はNG",
    "自己評価結果の公表義務：未公表は基本報酬の減算対象。本部が全FC加盟店を巡回監査",
    "PR実績の開示：就職実績・定着率は集計期間・対象拠点の算定根拠付きでのみ表示"]
for i,c in enumerate(cp):
    t(ax,6,42-i*3.4,"▶ "+c,7.4,"#7a2a1c",va="center")

box(ax,4,13,92,7,NAVY,r=0.5)
t(ax,6,18,"進め方",8.3,"#ffd2c8",weight="bold")
t(ax,17,18,"Q1のクイックウィン3つとコンプラ整備を即着手 → 効果を測りながらQ2以降で連携営業・PR・広告を積み上げ。",8,"white")
t(ax,17,15,"月次でKPIレビュー＆予算リバランス。マテリアル連携でPRを主役級ドライバーに格上げ。",8,"white")
t(ax,5,7,"デコボコベース株式会社 / 採用・集客 +20%成長プラン（統合版）  2/2",7.2,GRAY)
t(ax,95,7,"作成日 2026-06-16",7.2,GRAY,ha="right")
pdf.savefig(fig)
fig.savefig("/home/user/-/_p2.png",dpi=110)
pdf.close()
print("saved 2-page growth_plan")
