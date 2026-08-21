# -*- coding: utf-8 -*-
"""notes/*.md から Google ドキュメント用のまとめ本文を組み立てる。
   リスキリング／助成金に関する記述は除外する。"""
import re, sys, pathlib, datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE = re.compile(r'リスキリング|助成金|補助金')

def sections(path, level='## '):
    """見出し単位に分割して (見出し, 本文) を返す。"""
    lines = (BASE/path).read_text(encoding='utf-8').split('\n')
    idx = [i for i,l in enumerate(lines) if l.startswith(level)]
    if not idx:
        return [('', '\n'.join(lines))]
    out = [('', '\n'.join(lines[:idx[0]]))]
    for a,b in zip(idx, idx[1:]+[len(lines)]):
        out.append((lines[a][len(level):].strip(), '\n'.join(lines[a:b]).rstrip()))
    return out

def clean(path, level='### '):
    """指定レベルの見出しブロックのうち、除外語を含むものを落とす。"""
    kept, dropped = [], []
    for title, body in sections(path, level):
        if title and EXCLUDE.search(title):
            dropped.append(title); continue
        # 見出しは無関係でも本文の大半が除外対象なら落とす
        hits = len(EXCLUDE.findall(body))
        if title and hits >= 3:
            dropped.append(title); continue
        kept.append(body)
    return '\n\n'.join(k for k in kept if k.strip()), dropped

def strip_lines(text):
    """残った単発の言及を行単位で落とす。"""
    out, drop = [], 0
    for l in text.split('\n'):
        if EXCLUDE.search(l):
            drop += 1; continue
        out.append(l)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)), drop


# ---------------------------------------------------------------
# Googleドキュメント用の中間形式（Apps Scriptがそのまま流し込める）
# ---------------------------------------------------------------
import json

BOLD = re.compile(r'\*\*(.+?)\*\*', re.S)
CODE = re.compile(r'`([^`]*)`')
LINK = re.compile(r'\[([^\]]*)\]\([^)]*\)')

def inline(s):
    """**強調** を外して、太字にすべき範囲を [start, end) で返す。"""
    s = LINK.sub(r'\1', s)
    s = CODE.sub(r'\1', s)
    out, spans, pos = [], [], 0
    cur = 0
    for m in BOLD.finditer(s):
        out.append(s[pos:m.start()]); cur += m.start() - pos
        txt = m.group(1)
        spans.append([cur, cur + len(txt)])
        out.append(txt); cur += len(txt)
        pos = m.end()
    out.append(s[pos:])
    return ''.join(out), spans

def to_items(md):
    items = []
    def add(style, text, indent=0):
        text = text.rstrip()
        if not text and style != 'hr':
            return
        t, spans = inline(text)
        it = {'s': style, 't': t}
        if spans: it['b'] = spans
        if indent: it['i'] = indent
        items.append(it)

    in_table = False
    for raw in md.split('\n'):
        line = raw.rstrip()
        if not line.strip():
            in_table = False
            continue
        if re.match(r'^\s*(-{3,}|\*{3,}|={3,})\s*$', line):
            items.append({'s': 'hr', 't': ''}); in_table = False; continue
        m = re.match(r'^(#{1,4})\s+(.*)$', line)
        if m:
            add('h%d' % len(m.group(1)), m.group(2)); in_table = False; continue
        if line.lstrip().startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                in_table = True; continue
            add('tr' if in_table else 'th', '　｜　'.join(cells))
            in_table = True
            continue
        if line.lstrip().startswith('>'):
            add('q', line.lstrip()[1:].lstrip()); continue
        m = re.match(r'^(\s*)[-*]\s+(.*)$', line)
        if m:
            add('li', m.group(2), indent=len(m.group(1)) // 2); continue
        m = re.match(r'^(\s*)\d+[.)]\s+(.*)$', line)
        if m:
            add('nli', m.group(2), indent=len(m.group(1)) // 2); continue
        add('p', line.strip())
    return items

PARTS = [
    ("第1部　テーマ別ノウハウ", [
        'notes/01_営業ノウハウ_商談分析.md',
        'notes/02_社内オペレーション_マネジメント.md',
        'notes/03_分析レポーティングとアップセル.md',
        'notes/04_クライアント対応_継続防衛.md',
        'notes/05_撮影制作の現場ノウハウ.md',
        'notes/06_企画コンテンツ設計.md',
        'notes/07_採用ファネル分析と逆算設計.md',
    ]),
    ("第2部　制作フォーマット", ['notes/11_制作フォーマット集.md']),
    ("第2部の2　社内ナレッジ共有会と社内定例", ['notes/14_社内_ナレッジ共有会と社内定例.md']),
    ("第3部　社内運営とユニットエコノミクス", ['notes/12_社内運営とユニットエコノミクス.md']),
    ("第4部　営業台帳959商談の全量分析", ['notes/13_営業台帳959商談の全量分析.md']),
]
LOGS = ['notes/08_実録_商談と定例_2026-02_04.md',
        'notes/09_実録_商談と定例_2026-05_06.md',
        'notes/10_実録_商談と定例_2026-07_08.md']

def main():
    today = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    doc, dropped_all = [], []

    doc.append("# 社内ノウハウ抽出　まとめ")
    doc.append("")
    doc.append("**最終更新：%s**　／　毎週日曜23:00に自動追記" % today)
    doc.append("")
    doc.append("会議ログ（Meet Recordings の文字起こしとGeminiメモ）78件と、営業商談台帳959件を"
               "横断して読み込み、社内に散っていたノウハウを構造化したものです。"
               "引用はすべて実際の発言です。")
    doc.append("")
    doc.append("・クライアント企業名と個人名は業種別の記号に置き換えています（A社／営業担当X など）。")
    doc.append("・自社の原価と契約単価の実額は記号化しています（標準単価をPとした倍率）。")
    doc.append("・リスキリング／助成金・補助金に関する記述は、本ドキュメントからは除外しています。")
    doc.append("・打ち合わせ1回ごとの実録77本の全文は、末尾の索引と社内リポジトリを参照してください。")
    doc.append("")
    doc.append("---")
    doc.append("")

    for part, paths in PARTS:
        doc.append("# " + part); doc.append("")
        for p in paths:
            body, dr = clean(p)
            body, n = strip_lines(body)
            dropped_all += dr
            doc.append(body.strip()); doc.append("")
        doc.append("---"); doc.append("")

    # 実録の索引
    doc.append("# 第5部　打ち合わせ実録の索引"); doc.append("")
    doc.append("各行が1回の打ち合わせに対応します。末尾の★は再利用価値の目安"
               "（★★★＝そのまま型として使える）。本文は社内リポジトリの notes/08〜10 にあります。")
    doc.append("")
    n = 0
    for p in LOGS:
        label = {'08':'2026年2月〜4月','09':'2026年5月〜6月','10':'2026年7月〜8月'}[pathlib.Path(p).name[:2]]
        doc.append("## " + label)
        doc.append("")
        for title, _ in sections(p):
            if not title or title == '目次':
                continue
            if EXCLUDE.search(title):
                dropped_all.append(title); continue
            n += 1
            doc.append("%d. %s" % (n, title))
        doc.append("")

    doc.append("---"); doc.append("")
    doc.append("# 申し送り")
    doc.append("")
    doc.append("抽出の過程で、ノウハウとして再利用してはいけない内容が複数見つかっています。"
               "内容が内容なので本ドキュメントには書かず、社内限定ファイル "
               "knowledge/PRIVATE/12_社内運営とユニットエコノミクス_FULL.md の【E】節にまとめてあります。"
               "採用成果の作り方に関わる重大なものを含むため、必ず目を通してください。")

    body = '\n'.join(doc)
    outdir = BASE/'work'; outdir.mkdir(exist_ok=True)
    md_path = outdir/'google_doc_body.md'
    md_path.write_text(body, encoding='utf-8')

    items = to_items(body)
    json_path = outdir/'google_doc_body.json'
    json_path.write_text(json.dumps(items, ensure_ascii=False, separators=(',', ':')),
                         encoding='utf-8')
    print("書き出し:", json_path, json_path.stat().st_size, "bytes /", len(items), "段落")

    import markdown as _md
    conv = _md.Markdown(extensions=["tables", "sane_lists"])
    html_path = outdir/'google_doc_body.html'
    html_path.write_text(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<title>社内ノウハウ抽出 まとめ</title></head><body>'
        + conv.convert(body) + '</body></html>', encoding='utf-8')
    print("書き出し:", md_path, md_path.stat().st_size, "bytes")
    print("書き出し:", html_path, html_path.stat().st_size, "bytes")
    print("実録の索引:", n, "本")
    print("除外した節:", len(dropped_all))
    for d in dropped_all:
        print("  -", d)

if __name__ == '__main__':
    main()
