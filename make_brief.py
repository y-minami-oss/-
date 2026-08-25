# -*- coding: utf-8 -*-
"""デコボコベース 現状整理（会議用・社内）1枚PDF"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

FONT="/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
font_manager.fontManager.addfont(FONT)
matplotlib.rcParams["font.family"]="IPAGothic"
matplotlib.rcParams["axes.unicode_minus"]=False

NAVY="#1b2a4a"; RED="#e8462e"; REDBG="#fdecea"; GRAY="#5b6470"; LGRAY="#eef1f5"
GREEN="#1f9d6b"; GREENBG="#eaf7f0"; BLUE="#2f6db0"; BLUEBG="#eaf1f9"; GOLD="#c98a1a"; GOLDBG="#fbf2e0"
PURP="#6b4ea0"; PURPBG="#f0eaf7"

fig=plt.figure(figsize=(8.27,11.69),dpi=150)
ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,140); ax.axis("off")

def box(x,y,w,h,fc,ec="none",lw=0,r=0.0):
    if r: ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",fc=fc,ec=ec,lw=lw,mutation_aspect=1))
    else: ax.add_patch(Rectangle((x,y),w,h,fc=fc,ec=ec,lw=lw))
def t(x,y,s,size,color="black",ha="left",va="center",weight="normal"):
    ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,weight=weight)

# ヘッダー
box(0,128,100,12,NAVY); box(0,126.5,100,1.5,RED)
t(5,135.3,"デコボコベース 現状整理",16,"white",weight="bold")
t(5,130.6,"会議準備シート（社内用）／ 担当：三並",9.5,"#c9d4e6")
t(95,135,"2026-08-25",9,"#9fb0cc",ha="right")
t(95,131,"出典：Notion / Slack",7.5,"#9fb0cc",ha="right")

# ① 基本情報 + KPI
t(5,124,"① 基本情報とSNS実績",10.5,NAVY,weight="bold")
box(4,107.5,54,15,LGRAY,r=0.5)
info=[("業種","就労支援・教育福祉／全国300事業所"),
      ("運用","TikTok @decobocobase（IG・YT横展開）"),
      ("現行契約","TikTok運用 月額5.5万円（66万/年）"),
      ("契約開始","2024-01-17／継続レベルA"),
      ("KGI","年間費用対効果 600万円（月50万相当）")]
for i,(k,v) in enumerate(info):
    yy=120.5-i*2.7
    t(6,yy,k,7.6,BLUE,weight="bold"); t(19,yy,v,7.6,NAVY)
# KPIタイル
kpis=[("月間再生","12.9万",GREEN),("リーチ","11.6万",GREEN),
      ("遷移率","0.85%",RED),("フォロワー","+66",BLUE)]
tw=9.2
for i,(k,v,c) in enumerate(kpis):
    x=60+i*9.4
    box(x,107.5,tw,15,"white",ec=c,lw=1.1,r=0.4)
    t(x+tw/2,119.5,k,6.8,GRAY,ha="center")
    t(x+tw/2,114.5,v,11,c,ha="center",weight="bold")
    if k=="遷移率": t(x+tw/2,109.5,"目標5%",6,GRAY,ha="center")
    else: t(x+tw/2,109.5,"/月",6,GRAY,ha="center")

# ② 最重要論点
t(5,104,"② 【最重要】今日の論点",10.5,RED,weight="bold")
cards=[("契約更新 未締結","6月末で契約満了、継続承諾が未取得。担当者引き継ぎで手続きが停滞中。"),
       ("納品ビハインド 90本","未納品90本を月5.5万で運用しつつ消化。IG・YTショートへ無償横展開でカバー。"),
       ("CV計測 未整備","採用応募・問い合わせが測れず効果を示せない。遷移率も0.85%と低い。")]
cw=29.3
for i,(h,b) in enumerate(cards):
    x=4+i*(cw+1.2)
    box(x,88,cw,15,REDBG,ec=RED,lw=1.2,r=0.5)
    box(x,99,cw,4,RED)
    t(x+cw/2,101,h,8,"white",ha="center",weight="bold")
    # wrap body
    import textwrap
    for j,line in enumerate(textwrap.wrap(b,20)[:5]):
        t(x+1.5,96.5-j*2.4,line,6.6,"#7a2a1c",va="top")

# ③ 提案の選択肢
t(5,84,"③ 提案の選択肢（次の一手）",10.5,NAVY,weight="bold")
box(4,60.5,92,22,BLUEBG,ec=BLUE,lw=1.1,r=0.5)
opts=[("A","現行継続","TikTok運用 月5.5万（66万/年）。まず契約を締結し関係を維持",GRAY),
      ("B","アップセル","全社アカウント運用＋内製化支援 月50万（660万/年）",BLUE),
      ("C","AIリスキリング","60名＝通常1,980万→助成1,557万→実質423万（別建て・助成75%）",PURP),
      ("D","+20%成長プラン","業界ポータル/MEO/LP分離/LINE/PR（マテリアル連携）で採用・集客+20%",GREEN)]
for i,(k,name,desc,c) in enumerate(opts):
    yy=78-i*4.6
    box(6,yy-1.8,5,3.6,c,r=0.3); t(8.5,yy,k,10,"white",ha="center",weight="bold")
    t(13,yy+0.9,name,8.4,c,weight="bold"); t(13,yy-1.6,desc,7.2,NAVY)

# ④ リスキリング要点
t(5,56.5,"④ リスキリング（AI×SNS・助成金）の要点",10.5,NAVY,weight="bold")
box(4,40,92,15,PURPBG,ec=PURP,lw=1.1,r=0.5)
rk=["経費助成75%＋賃金助成（12時間×1,000円）／研修12時間（4h×3回）",
    "事前申請＝研修開始の45日前／助成金の支給＝実施後6〜10ヶ月",
    "SNS運用費とリスキリング費は「別建て」で請求（助成金審査上 安全）",
    "監査が厳格化・虚偽申請は違約金20% → 適正手続きが必須（金山さん主管）"]
for i,r in enumerate(rk):
    t(6,52-i*3.1,"・"+r,7.6,"#3d2c63",va="center")

# ⑤ 本日決めたいこと
t(5,36,"⑤ 本日決めたいこと",10.5,NAVY,weight="bold")
box(4,14,92,20.5,"#f6f8fb",ec="#d7deea",lw=1,r=0.5)
todo=["契約継続の可否と締結時期（最優先）",
      "納品ビハインド90本の処理方針（納期・横展開・巻き取り）",
      "アップセル（660万）／リスキリング（60名）の提示可否とタイミング",
      "+20%施策の優先順位と予算感（次回提案の宿題化）"]
for i,d in enumerate(todo):
    yy=31-i*4.0
    box(6,yy-1.3,2.6,2.6,"white",ec=NAVY,lw=1.1,r=0.2)
    t(11,yy,d,8,NAVY,va="center")

t(5,10,"※ 本シートは社内会議準備用（先方共有は別途クライアント版を作成）",7,GRAY)
t(5,7,"デコボコベース 現状整理 / トレプロ",7,GRAY)
t(95,7,"2026-08-25",7,GRAY,ha="right")

fig.savefig("/home/user/-/decoboco_brief.pdf",format="pdf")
fig.savefig("/home/user/-/_brief.png",format="png",dpi=110)
print("saved brief")
