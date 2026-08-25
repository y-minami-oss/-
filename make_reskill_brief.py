# -*- coding: utf-8 -*-
"""リスキリング 現状整理（会議用）1枚PDF"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrow

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
box(0,128,100,12,NAVY); box(0,126.5,100,1.5,PURP)
t(5,135.3,"AIリスキリング 現状整理",16,"white",weight="bold")
t(5,130.6,"会議準備シート（社内用）／ 人材開発支援助成金の活用",9.5,"#c9d4e6")
t(95,135,"2026-08-25",9,"#9fb0cc",ha="right")
t(95,131,"主管：金山さん／申請：三並×南さん",7.5,"#9fb0cc",ha="right")

# ① 制度の要点
t(5,124,"① 制度の要点（人材開発支援助成金）",10.5,NAVY,weight="bold")
box(4,110.5,92,12,PURPBG,ec=PURP,lw=1.1,r=0.5)
pts=[("助成率","経費助成 75%（中小）＋ 賃金助成 1,000円 × 研修時間"),
     ("研修","12時間（4時間 × 3回）／ベース料金 33万円（10名想定の1単位）"),
     ("実質負担","1人あたり 約7.05万円（＝通常33万の25% − 賃金助成1.2万）")]
for i,(k,v) in enumerate(pts):
    yy=119.5-i*3.0
    t(6,yy,k,7.8,PURP,weight="bold"); t(22,yy,v,7.8,NAVY)

# ② お金の流れ・スケジュール
t(5,107,"② 手続きの流れ（時系列）",10.5,NAVY,weight="bold")
steps=[("事前申請","研修開始の45日前"),("研修実施","12時間 実施"),
       ("支払い","一括 / 3分割 可"),("支給申請","最終支払い後"),("助成金 入金","実施後6〜10ヶ月")]
sw=17.4
for i,(h,s) in enumerate(steps):
    x=4.5+i*(sw+0.9)
    box(x,95.5,sw,9,"white",ec=PURP,lw=1.1,r=0.4)
    t(x+sw/2,101.7,h,7.8,PURP,ha="center",weight="bold")
    t(x+sw/2,97.7,s,6.6,NAVY,ha="center")
    if i<4:
        ax.annotate("",xy=(x+sw+0.9,100),xytext=(x+sw,100),
                    arrowprops=dict(arrowstyle="-|>",color=PURP,lw=1.4))

# ③ 価格ラダー（抜粋）
t(5,92,"③ 価格ラダー（抜粋・税込）",10.5,NAVY,weight="bold")
box(4,68,92,22,LGRAY,r=0.5)
cols=["人数","通常価格","助成額","実質負担","プラン内容"]
cx=[8,24,40,56,72]
box(4,84.5,92,4,NAVY)
for c,x in zip(cols,cx): t(x,86.5,c,7.8,"white",weight="bold")
rows=[("10名","330万","259.5万","70.5万","研修（本社向け）"),
      ("20名","660万","519.0万","141.0万","研修（サロン＋本社）"),
      ("30名","990万","778.5万","211.5万","SNS運用6ヶ月＋研修"),
      ("40名","1,320万","1,038万","282.0万","SNS運用7ヶ月＋研修"),
      ("50名","1,650万","1,297.5万","352.5万","SNS運用7ヶ月＋研修＋AI導入"),
      ("60名","1,980万","1,557万","423.0万","SNS運用8ヶ月＋研修＋AI導入")]
for i,r in enumerate(rows):
    yy=82.3-i*2.7
    if r[0]=="60名":
        box(4.5,yy-1.15,91,2.5,"#e7dff2",r=0.2)
    for v,x in zip(r,cx):
        w="bold" if r[0]=="60名" else "normal"
        col=PURP if r[0]=="60名" else NAVY
        t(x,yy,v,7.2,col,weight=w)

# ④ デコボコへの適用（推奨60名）
t(5,65,"④ デコボコベースへの適用（推奨：60名）",10.5,NAVY,weight="bold")
box(4,50,92,14,GREENBG,ec=GREEN,lw=1.2,r=0.5)
t(6,61.3,"60名プラン：通常1,980万 → 助成1,557万 → 実質負担 423万円",8.6,"#1d5e42",weight="bold")
ap=["内容：SNS運用8ヶ月 ＋ AI×SNS研修 ＋ AI導入サポート（各店舗）",
    "対象者：全国300事業所の支援員等 → 助成対象の母数は十分",
    "支払い：一括／3分割が可能。助成金は実施後6〜10ヶ月で入金"]
for i,a in enumerate(ap):
    t(6,57.8-i*2.5,"・"+a,7.6,"#1d5e42")

# ⑤ 提案の作法・コンプラ注意
t(5,47,"⑤ 提案の作法・コンプライアンス注意",10.5,RED,weight="bold")
box(4,32,92,14,REDBG,ec=RED,lw=1.1,r=0.5)
cp=["SNS運用費とリスキリング費は「別建て」で提示・請求（相殺しない＝審査上安全）",
    "会計検査院の監査が厳格化／虚偽・不適切運用は違約金20%",
    "事前申請は研修開始の45日前／必要書類の整備が必須",
    "主管：金山さん／申請サポート：三並さん×南さん"]
for i,c in enumerate(cp):
    t(6,44-i*3.0,"・"+c,7.6,"#7a2a1c")

# ⑥ 今日の確認事項
t(5,29,"⑥ 今日の確認事項",10.5,NAVY,weight="bold")
box(4,8,92,19.5,"#f6f8fb",ec="#d7deea",lw=1,r=0.5)
todo=["ラダー内の「SNS運用（8ヶ月）」と“別建て請求”方針の整合（最重要・要確認）",
      "対象人数の確定（推奨60名／40・50名も選択肢）",
      "提示タイミング：現行契約の更新・ビハインド解消との順序",
      "スケジュール逆算：研修開始日 −45日 で事前申請／支払い方法の決定"]
for i,d in enumerate(todo):
    yy=24.5-i*4.0
    box(6,yy-1.3,2.6,2.6,"white",ec=NAVY,lw=1.1,r=0.2)
    t(11,yy,d,7.8,NAVY,va="center")

t(5,4.5,"※ 本シートは社内会議準備用。金額・要件は最新の助成金要綱と金山さんの確認を優先。",6.8,GRAY)
t(95,4.5,"AIリスキリング 現状整理 / トレプロ",6.8,GRAY,ha="right")

fig.savefig("/home/user/-/reskilling_brief.pdf",format="pdf")
fig.savefig("/home/user/-/_rb.png",format="png",dpi=110)
print("saved reskilling brief")
