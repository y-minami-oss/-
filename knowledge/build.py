import markdown, re, html, pathlib, json

NOTES = [
    ("overview",  "全体像と出典",        "README.md"),
    ("sales",     "営業ノウハウ",        "notes/01_営業ノウハウ_商談分析.md"),
    ("ops",       "社内オペレーション",  "notes/02_社内オペレーション_マネジメント.md"),
    ("analytics", "分析とアップセル",    "notes/03_分析レポーティングとアップセル.md"),
    ("retention", "継続防衛",            "notes/04_クライアント対応_継続防衛.md"),
    ("shoot",     "撮影・制作",          "notes/05_撮影制作の現場ノウハウ.md"),
    ("planning",  "企画・コンテンツ",    "notes/06_企画コンテンツ設計.md"),
    ("funnel",    "採用ファネル",        "notes/07_採用ファネル分析と逆算設計.md"),
    ("log0204",   "実録 02–04月",        "notes/08_実録_商談と定例_2026-02_04.md"),
    ("log0506",   "実録 05–06月",        "notes/09_実録_商談と定例_2026-05_06.md"),
    ("log0708",   "実録 07–08月",        "notes/10_実録_商談と定例_2026-07_08.md"),
    ("formats",   "制作フォーマット",    "notes/11_制作フォーマット集.md"),
    ("unitecon",  "社内運営と原価構造",  "notes/12_社内運営とユニットエコノミクス.md"),
    ("ledger",    "営業台帳959商談",     "notes/13_営業台帳959商談の全量分析.md"),
    ("internal",  "社内ナレッジ共有会",  "notes/14_社内_ナレッジ共有会と社内定例.md"),
]

md = markdown.Markdown(extensions=["tables", "attr_list", "sane_lists"])

def slug(sid, n):
    return f"{sid}-{n:02d}"

def convert(path, sid):
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    lines = raw.split("\n")
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]
    else:
        title = ""
    body = "\n".join(lines).strip()
    md.reset()
    out = md.convert(body)
    out = out.replace("\U0001F534 ", '<span class="flag" aria-label="重要"></span>')
    out = out.replace("\U0001F534", '<span class="flag" aria-label="重要"></span>')
    out = re.sub(r"<table>", '<div class="tw"><table>', out)
    out = re.sub(r"</table>", "</table></div>", out)

    # h2 に id を振る
    heads = []
    def stamp(m):
        heads.append(re.sub(r"<[^>]+>", "", m.group(1)).strip())
        return '<h2 id="%s">%s</h2>' % (slug(sid, len(heads)), m.group(1))
    out = re.sub(r"<h2>(.*?)</h2>", stamp, out, flags=re.S)

    # 冒頭の「目次」リストをアンカー化
    def linkify(m):
        item = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        for i, h in enumerate(heads, 1):
            if h == item:
                return '<li><a href="#%s">%s</a></li>' % (slug(sid, i), m.group(1))
        return m.group(0)
    tocm = re.search(r"<h2 id=\"[^\"]+\">目次</h2>\s*<ul>(.*?)</ul>", out, re.S)
    if tocm:
        block = re.sub(r"<li>(.*?)</li>", linkify, tocm.group(1), flags=re.S)
        out = out[:tocm.start()] + '<div class="toc"><p class="toc-h">この章の内容</p><ul>' + block + "</ul></div>" + out[tocm.end():]
        heads = heads  # 目次見出し自体はidを持ったままだが非表示

    # h2 ごとに article で包み、検索用テキストを持たせる
    parts = re.split(r'(?=<h2 id=")', out)
    wrapped = []
    for part in parts:
        if part.startswith('<h2 id="'):
            txt = re.sub(r"<[^>]+>", " ", part)
            txt = re.sub(r"\s+", " ", txt).strip()
            wrapped.append('<article class="entry" data-q="%s">%s</article>' % (html.escape(txt[:4000], quote=True), part))
        else:
            wrapped.append(part)
    return title, "".join(wrapped)

sections = []
navitems = []
for sid, label, path in NOTES:
    title, body = convert(path, sid)
    sections.append(f'<section id="{sid}" class="sec">\n<header class="sec-h"><p class="eyebrow">{html.escape(label)}</p><h2>{html.escape(title)}</h2></header>\n{body}\n</section>')
    navitems.append(f'<li><a href="#{sid}">{html.escape(label)}</a></li>')

CSS = """
:root{
  --paper:#F4F6F5; --surface:#FFFFFF; --ink:#101715; --muted:#5B6764;
  --rule:#DCE3E0; --rule-soft:#E9EEEC; --accent:#1F5F5B; --accent-soft:#E4EFEC;
  --signal:#A8712A; --signal-soft:#F5EBDC; --shadow:0 1px 2px rgba(16,23,21,.05);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#0D1211; --surface:#151D1B; --ink:#E7EDEA; --muted:#93A29E;
    --rule:#26302E; --rule-soft:#1D2725; --accent:#5FB3A8; --accent-soft:#152826;
    --signal:#D8A45C; --signal-soft:#241C11; --shadow:0 1px 2px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --paper:#0D1211; --surface:#151D1B; --ink:#E7EDEA; --muted:#93A29E;
  --rule:#26302E; --rule-soft:#1D2725; --accent:#5FB3A8; --accent-soft:#152826;
  --signal:#D8A45C; --signal-soft:#241C11; --shadow:0 1px 2px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Noto Sans JP","Hiragino Sans","Yu Gothic UI",system-ui,sans-serif;
  font-size:16px; line-height:1.85; font-feature-settings:"palt" 1;
  -webkit-font-smoothing:antialiased;
}
.wrap{display:grid; grid-template-columns:15.5rem minmax(0,1fr); gap:3.5rem;
  max-width:74rem; margin:0 auto; padding:0 1.75rem 8rem;}
@media (max-width:900px){ .wrap{grid-template-columns:1fr; gap:0; padding:0 1.25rem 5rem} }

/* ---- masthead ---- */
.mast{grid-column:1/-1; padding:4.5rem 0 2.5rem; border-bottom:1px solid var(--rule);}
.mast .kicker{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem;
  letter-spacing:.16em; text-transform:uppercase; color:var(--signal); margin:0 0 1.1rem}
.mast h1{font-family:"Shippori Mincho","Yu Mincho",serif; font-weight:600;
  font-size:clamp(2rem,4.6vw,3.1rem); line-height:1.28; letter-spacing:.01em;
  margin:0 0 1.1rem; text-wrap:balance}
.mast .lede{max-width:44rem; color:var(--muted); margin:0; font-size:1.0125rem}
.stats{display:flex; flex-wrap:wrap; gap:0 2.5rem; margin:2.25rem 0 0; padding:0; list-style:none}
.stats li{font-family:"IBM Plex Mono",ui-monospace,monospace; font-variant-numeric:tabular-nums}
.stats b{display:block; font-size:1.6rem; font-weight:500; color:var(--accent); line-height:1.2}
.stats span{font-family:"Noto Sans JP",sans-serif; font-size:.75rem; color:var(--muted); letter-spacing:.05em}

/* ---- nav rail ---- */
nav{position:sticky; top:0; align-self:start; padding:2.75rem 0; max-height:100vh; overflow-y:auto}
@media (max-width:900px){ nav{position:static; max-height:none; padding:2rem 0 0; border-bottom:1px solid var(--rule)} }
nav p{font-family:"IBM Plex Mono",monospace; font-size:.66rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--muted); margin:0 0 .9rem}
nav ol{list-style:none; margin:0; padding:0; counter-reset:n}
nav li{counter-increment:n; border-top:1px solid var(--rule-soft)}
nav li:last-child{border-bottom:1px solid var(--rule-soft)}
nav a{display:flex; gap:.7rem; align-items:baseline; padding:.6rem 0; color:var(--ink);
  text-decoration:none; font-size:.875rem; line-height:1.45}
nav a::before{content:counter(n,decimal-leading-zero);
  font-family:"IBM Plex Mono",monospace; font-size:.68rem; color:var(--muted);
  font-variant-numeric:tabular-nums}
nav a:hover{color:var(--accent)} nav a:hover::before{color:var(--accent)}
nav a:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

/* ---- content ---- */
main{min-width:0; padding-top:2.75rem}
.sec{padding:0 0 4.5rem}
.sec-h{margin:0 0 2rem; padding-top:1.5rem}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:.68rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--signal); margin:0 0 .55rem}
.sec-h h2{font-family:"Shippori Mincho",serif; font-weight:600; font-size:1.85rem;
  line-height:1.4; margin:0; text-wrap:balance; letter-spacing:.01em}
main h3{font-family:"Shippori Mincho",serif; font-weight:600; font-size:1.28rem;
  margin:3rem 0 1rem; padding-top:1.25rem; border-top:1px solid var(--rule);
  line-height:1.5; text-wrap:balance}
main h4{font-size:1rem; font-weight:700; margin:2rem 0 .7rem; color:var(--accent); letter-spacing:.01em}
main h5{font-size:.9rem; font-weight:700; margin:1.5rem 0 .5rem; color:var(--muted)}
main p{margin:0 0 1.1rem; max-width:44rem}
main ul,main ol{margin:0 0 1.2rem; padding-left:1.3rem; max-width:44rem}
main li{margin:0 0 .42rem}
main li::marker{color:var(--muted)}
main strong{font-weight:700}
main a{color:var(--accent)}
main hr{border:0; border-top:1px solid var(--rule); margin:2.75rem 0}
main code{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.85em;
  background:var(--accent-soft); padding:.1em .38em; border-radius:3px}

/* transcript pulls */
blockquote{margin:1.4rem 0; padding:.9rem 0 .9rem 1.35rem;
  border-left:2px solid var(--signal); background:linear-gradient(90deg,var(--signal-soft),transparent 85%);
  max-width:46rem}
blockquote p{margin:0 0 .55rem; font-family:"Shippori Mincho",serif; font-size:1.02rem; line-height:1.9}
blockquote p:last-child{margin:0}
blockquote code{background:transparent; padding:0; color:var(--signal)}

pre{background:var(--surface); border:1px solid var(--rule); border-radius:4px;
  padding:1rem 1.1rem; overflow-x:auto; box-shadow:var(--shadow)}
pre code{background:transparent; padding:0; font-size:.8rem; line-height:1.7}

.tw{overflow-x:auto; margin:1.4rem 0; border:1px solid var(--rule); border-radius:4px; background:var(--surface)}
table{border-collapse:collapse; width:100%; font-size:.875rem; line-height:1.65}
th,td{text-align:left; padding:.6rem .85rem; border-bottom:1px solid var(--rule-soft); vertical-align:top}
thead th{background:var(--accent-soft); color:var(--accent); font-weight:700;
  font-size:.75rem; letter-spacing:.04em; white-space:nowrap; border-bottom:1px solid var(--rule)}
tbody tr:last-child td{border-bottom:0}
td{font-variant-numeric:tabular-nums}

.flag{display:inline-block; width:.42rem; height:.42rem; border-radius:50%;
  background:var(--signal); margin-right:.5rem; vertical-align:.15em; flex:none}

footer{grid-column:1/-1; border-top:1px solid var(--rule); padding:2rem 0 0; margin-top:2rem;
  color:var(--muted); font-size:.8rem}
@media (prefers-reduced-motion:reduce){ *{animation:none!important; transition:none!important; scroll-behavior:auto!important} }
html{scroll-behavior:smooth}

/* ---- 章内目次 ---- */
.toc{border:1px solid var(--rule); border-radius:10px; background:var(--surface);
     padding:1.1rem 1.3rem; margin:1.6rem 0 2.4rem; box-shadow:var(--shadow)}
.toc-h{font-family:"IBM Plex Mono",monospace; font-size:.64rem; letter-spacing:.16em;
       text-transform:uppercase; color:var(--muted); margin:0 0 .6rem}
.toc ul{list-style:none; margin:0; padding:0; display:grid; gap:.15rem}
.toc li{margin:0}
.toc a{display:block; padding:.32rem .1rem; color:var(--ink); text-decoration:none;
       font-size:.9rem; line-height:1.45; border-bottom:1px solid var(--rule-soft)}
.toc li:last-child a{border-bottom:0}
.toc a:hover{color:var(--accent)}

/* ---- 検索 ---- */
.finder{position:sticky; top:0; z-index:20; background:var(--paper);
        padding:.9rem 0; border-bottom:1px solid var(--rule); margin-bottom:1.5rem}
.finder input{width:100%; box-sizing:border-box; font:inherit; font-size:.95rem;
        padding:.7rem .9rem; border:1px solid var(--rule); border-radius:8px;
        background:var(--surface); color:var(--ink)}
.finder input:focus{outline:2px solid var(--accent); outline-offset:1px; border-color:var(--accent)}
.finder .count{font-family:"IBM Plex Mono",monospace; font-size:.7rem; color:var(--muted);
        margin:.45rem 0 0; min-height:1em}
.entry.hide, .sec.hide, .toc.hide{display:none}
"""

doc = f"""<title>社内ナレッジ台帳</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Noto+Sans+JP:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
  <header class="mast">
    <p class="kicker">Internal Knowledge Ledger &nbsp;/&nbsp; 2026.08.21</p>
    <h1>会議ログから掘り起こした、<br>社内に散らばっていたノウハウ</h1>
    <p class="lede">tldv と Google Meet に溜まっていた商談・打ち合わせの記録を横断し、
    営業トーク、社内オペレーション、レポーティング、撮影、企画、採用設計に構造化したうえで、
    打ち合わせ1回ごとの実録77本と、営業台帳959商談の全量分析を添えています。
    引用はすべて実際の発言です。<b>公開版のため、企業名・個人名は記号に置き換え、原価と契約単価の実額は伏せています。</b></p>
    <ul class="stats">
      <li><b>78</b><span>議事録を精読</span></li>
      <li><b>959</b><span>商談ログを全量分析</span></li>
      <li><b>77</b><span>打ち合わせ実録</span></li>
      <li><b>13</b><span>ノウハウ分野</span></li>
    </ul>
  </header>
  <nav aria-label="目次">
    <p>Contents</p>
    <ol>{''.join(navitems)}</ol>
  </nav>
  <main>
    <div class="finder">
      <input id="q" type="search" placeholder="キーワードで絞り込む（例：継続 / 失注 / 撮影 / インタビュー）" aria-label="キーワード検索">
      <p class="count" id="qc"></p>
    </div>
    {''.join(sections)}
  </main>
  <footer>
    <p>出典：Google Drive「Meet Recordings」フォルダ（2026/02–08）、営業研修資料.xlsx、商談管理コックピット。
    tldv.io 本体は組織のエグレスポリシーにより到達不可（CONNECT 403）のため、Drive上の二次データから抽出しています。</p>
  </footer>
</div>
<script>
(function(){{
  var q=document.getElementById('q'), qc=document.getElementById('qc');
  var entries=[].slice.call(document.querySelectorAll('.entry'));
  var secs=[].slice.call(document.querySelectorAll('.sec'));
  var tocs=[].slice.call(document.querySelectorAll('.toc'));
  var nav=[].slice.call(document.querySelectorAll('nav a'));
  entries.forEach(function(e){{ e._q=(e.dataset.q||'').toLowerCase(); }});
  function run(){{
    var v=q.value.trim().toLowerCase();
    if(!v){{
      entries.forEach(function(e){{e.classList.remove('hide')}});
      secs.forEach(function(s){{s.classList.remove('hide')}});
      tocs.forEach(function(t){{t.classList.remove('hide')}});
      nav.forEach(function(a){{a.parentNode.style.display=''}});
      qc.textContent=''; return;
    }}
    var terms=v.split(/\s+/), n=0;
    entries.forEach(function(e){{
      var ok=terms.every(function(t){{return e._q.indexOf(t)>-1}});
      e.classList.toggle('hide',!ok); if(ok) n++;
    }});
    tocs.forEach(function(t){{t.classList.add('hide')}});
    secs.forEach(function(s){{
      var any=s.querySelector('.entry:not(.hide)');
      s.classList.toggle('hide',!any);
      var id=s.id, a=document.querySelector('nav a[href="#'+id+'"]');
      if(a) a.parentNode.style.display= any ? '' : 'none';
    }});
    qc.textContent=n+' 件が一致';
  }}
  q.addEventListener('input',run);
}})();
</script>
"""
pathlib.Path("/home/user/-/knowledge/knowledge-base.html").write_text(doc, encoding="utf-8")
print("bytes:", len(doc.encode()))
