# -*- coding: utf-8 -*-
"""デコボコベース 採用・集客 +20%成長プラン（12ヶ月）1枚PDF"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
font_manager.fontManager.addfont(FONT)
matplotlib.rcParams["font.family"] = "IPAGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

NAVY="#1b2a4a"; NAVY2="#27406b"; RED="#e8462e"; REDBG="#fdecea"
GRAY="#5b6470"; LGRAY="#eef1f5"; GREEN="#1f9d6b"; GREENBG="#eaf7f0"
BLUE="#2f6db0"; BLUEBG="#eaf1f9"; GOLD="#c98a1a"

fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,140); ax.axis("off")

def box(x,y,w,h,fc,ec="none",lw=0,rounded=0.0):
    if rounded:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={rounded}",
                     fc=fc,ec=ec,lw=lw,mutation_aspect=1))
    else:
        ax.add_patch(Rectangle((x,y),w,h,fc=fc,ec=ec,lw=lw))

def t(x,y,s,size,color="black",ha="left",va="center",weight="normal"):
    ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,weight=weight)

# ===== ヘッダー =====
box(0,128,100,12,NAVY); box(0,126.5,100,1.5,RED)
t(5,135.5,"デコボコベース  採用・集客 +20% 成長プラン",17,"white",weight="bold")
t(5,130.6,"12ヶ月ロードマップ / SNS効果測定データに基づく設計（リスキリング除く）",10,"#c9d4e6")
t(95,135,"目標",8,"#9fb0cc",ha="right")
t(95,131.3,"採用・集客 +20% / 12ヶ月",12,RED,ha="right",weight="bold")

# ===== ① 目標 & 現状診断 =====
t(5,124,"① 目標と現状（実データ）",10.5,NAVY,weight="bold")
box(4,108.5,45,14,GREENBG,ec=GREEN,lw=1.2,rounded=0.6)
t(6,120,"ゴール（12ヶ月後）",8.5,GREEN,weight="bold")
t(6,116.3,"集客（問い合わせ・見学・契約） +20%",8,"#1d5e42",weight="bold")
t(6,113.2,"採用（応募・入社） +20%",8,"#1d5e42",weight="bold")
t(6,110.3,"※ KGI＝費用対効果 年600万円相当を維持",7.2,"#1d5e42")
box(51,108.5,45,14,REDBG,ec=RED,lw=1.2,rounded=0.6)
t(53,120,"現状診断（最大の課題）",8.5,RED,weight="bold")
t(53,116.3,"認知◎ 月12.9万再生・リーチ11.6万",8,"#7a2a1c")
t(53,113.2,"遷移率0.85%（目標5%）・CV計測 未整備",8,"#7a2a1c")
t(53,110.3,"→「測れないものは改善できない」",7.6,"#7a2a1c",weight="bold")

# ===== ② KPIツリー =====
t(5,105,"② KPIツリー — どこを動かせば+20%になるか",10.5,NAVY,weight="bold")
box(4,93.5,92,10,LGRAY,rounded=0.5)
t(6,100.7,"集客",8.5,BLUE,weight="bold")
t(13,100.7,"問い合わせ ＝ リーチ × プロフィール遷移率 × サイト誘導率 × 問い合わせCVR → 見学 → 契約",8,NAVY)
t(6,95.7,"採用",8.5,RED,weight="bold")
t(13,95.7,"入社数 ＝ 応募数 × 書類通過 × 面接通過 × 内定承諾（RPOで母集団と歩留まりを補強）",8,NAVY)

# ===== ③ 4四半期ロードマップ =====
t(5,90,"③ 12ヶ月ロードマップ — Q1で土台、Q2-Q4で積み上げ",10.5,NAVY,weight="bold")
quarters = [
    ("Q1 (1-3月)","計測と土台", BLUE, BLUEBG,
     ["GA4/UTM・経路タグで計測整備","動画末尾CTA統一・導線最適化","集客/採用LPを制作"], "±0%\nベースライン確定"),
    ("Q2 (4-6月)","獲得チャネル投入", GREEN, GREENBG,
     ["Web広告テスト(Indeed/Meta)","CPA最適化・勝ちパターン量産","保護者向けコンテンツ強化"], "+6%"),
    ("Q3 (7-9月)","拡大", GOLD, "#fbf2e0",
     ["広告スケール・YouTube本格化","RPOで採用母集団形成","リファラル/口コミ設計"], "+13%"),
    ("Q4 (10-12月)","刈り取り・最適化", RED, REDBG,
     ["歩留まり改善・面接設計","全チャネル配分最適化","勝ち施策に予算集中"], "+20%"),
]
cw = 22
for i,(q,theme,c,bg,items,cum) in enumerate(quarters):
    x = 4 + i*(cw+1.3)
    box(x,64,cw,23,bg,ec=c,lw=1.2,rounded=0.6)
    box(x,82.5,cw,4.5,c,rounded=0.0)
    t(x+cw/2,84.7,q,8,"white",ha="center",weight="bold")
    t(x+cw/2,80.3,theme,8.5,c,ha="center",weight="bold")
    for j,it in enumerate(items):
        t(x+1.5,77-j*3.0,"・"+it,6.6,NAVY,va="top")
    box(x+1.5,65,cw-3,3.0,"white",ec=c,lw=0.8,rounded=0.3)
    t(x+cw/2,66.5,"累計 "+cum.split(chr(10))[0],8,c,ha="center",weight="bold")

# ===== ④ +20%の積み上げ（成長ブリッジ） =====
t(5,60.5,"④ +20%の積み上げ（成長ドライバー）— 安全マージン込みで設計",10.5,NAVY,weight="bold")
drivers = [
    ("導線・LP / CVR改善（遷移率0.85%→1.5%）", 10, BLUE),
    ("コンテンツ最適化（勝ちパターン量産→リーチ増）", 5, GREEN),
    ("新規チャネル（Web広告・YouTube流入）", 8, GOLD),
    ("採用歩留まり改善（RPO・面接設計）", 5, RED),
]
maxv=12; bx=52; bw=30; row=58
for i,(name,v,c) in enumerate(drivers):
    y = row - i*4.2
    t(6,y,name,8,NAVY)
    box(bx,y-1.1,bw,2.2,"#dde3ec",rounded=0.2)
    box(bx,y-1.1,bw*v/maxv,2.2,c,rounded=0.2)
    t(bx+bw+1.5,y,f"+{v}pt",8.5,c,ha="left",weight="bold")
box(4,38,92,4.2,NAVY,rounded=0.3)
t(6,40.1,"設計値 合計 +28pt",9,"white",weight="bold")
t(94,40.1,"ロス・季節変動を控除 → 目標 +20% を確保",9,"#ffd2c8",ha="right",weight="bold")

# ===== ⑤ 投資ガイド & 前提 =====
t(5,34,"⑤ 投資ガイド（月額目安）",10,NAVY,weight="bold")
box(4,17.5,45,15.5,"#f6f8fb",ec="#d7deea",lw=1,rounded=0.5)
inv=[("Web広告","月30〜50万（採用課金10〜30万/人）"),("RPO（採用代行）","月20〜40万 / 初期=固定+成果"),
     ("計測基盤・LP","初期30〜50万＋月3〜5万"),("YouTube/動画","内製中心（外注なら月20〜40万）"),
     ("既存SNS(TikTok)","月5.5万 継続")]
for i,(k,v) in enumerate(inv):
    yy=30.5-i*2.7
    t(6,yy,"●",6.5,RED); t(8.3,yy,k,7.6,NAVY,weight="bold"); t(8.3,yy-1.2,v,6.8,GRAY)

t(54,34,"⑥ 前提・リスク管理",10,NAVY,weight="bold")
box(51,17.5,45,15.5,"#fff6f4",ec=RED,lw=1,rounded=0.5)
risk=["Q1の計測整備が必達（無いと+20%は証明不可）","SNSアルゴリズム変動 → 複数チャネルに分散",
      "広告CPA高騰 → CVR改善で吸収","採用は人材市場依存 → RPOで母集団補完","月次でKPIレビュー&予算リバランス"]
for i,r in enumerate(risk):
    t(53,31-i*2.7,"▶ "+r,7.2,"#7a2a1c",va="center")

# ===== まとめ帯 =====
box(4,7.5,92,7.5,NAVY,rounded=0.5)
t(6,12.7,"結論",8.5,"#ffd2c8",weight="bold")
t(13,12.7,"認知は十分。+20%の鍵は「計測 → 導線/LPでCVR改善 → 広告/RPOで獲得・採用を上乗せ」。",8.2,"white")
t(13,9.6,"Q1で土台を固め、Q2以降で積み上げれば、リーチ横ばいでも+20%は到達可能。",8.2,"white")
t(5,3,"デコボコベース株式会社 / 採用・集客 +20%成長プラン（ドラフト）",7.2,GRAY)
t(95,3,"作成日 2026-06-16",7.2,GRAY,ha="right")

fig.savefig("/home/user/-/growth_plan.pdf",format="pdf")
fig.savefig("/home/user/-/_pre3.png",format="png",dpi=110)
print("saved growth_plan")
