# -*- coding: utf-8 -*-
"""公開リポジトリから、リスキリング／助成金・補助金に関する記述を切り出して
   PRIVATE/ に退避する。労働局の調査対象になっている論点のため、公開版には残さない。"""
import re, glob, io, os, pathlib

EX = re.compile(r'リスキリング|助成金|補助金|トレデミー')
BASE = pathlib.Path(__file__).resolve().parent.parent
moved = []

def process(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    # ## セクション単位に分割
    idx = [i for i, l in enumerate(lines) if l.startswith('## ')]
    if not idx:
        blocks = [(None, lines)]
    else:
        blocks = [(None, lines[:idx[0]])]
        for a, b in zip(idx, idx[1:] + [len(lines)]):
            blocks.append((lines[a][3:].strip(), lines[a:b]))

    kept, cut = [], []
    for title, body in blocks:
        text = '\n'.join(body)
        # 節まるごと落とすのは、見出し自体が助成金の話のときだけ
        if title and title != '目次' and EX.search(title):
            cut.append((title, text)); moved.append((path, title)); continue
        # 残りは ### 単位で見る
        if title == '目次':
            kept += [l for l in body if not EX.search(l)]
            continue
        sub = [i for i, l in enumerate(body) if l.startswith('### ')]
        if sub:
            out = body[:sub[0]]
            for a, b in zip(sub, sub[1:] + [len(body)]):
                chunk = body[a:b]; t = body[a][4:].strip()
                # 小見出しごと落とすのは、見出し自体が助成金の話のときだけ。
                # それ以外は該当行だけ抜く（節の骨格は残す）。
                if EX.search(t):
                    cut.append((t, '\n'.join(chunk))); moved.append((path, t)); continue
                hit = [l for l in chunk if EX.search(l)]
                if hit:
                    cut.append((t + '（該当行のみ）', '\n'.join(hit)))
                    chunk = [l for l in chunk if not EX.search(l)]
                out += chunk
            body = out
        # 行単位の取りこぼし
        body = [l for l in body if not EX.search(l)]
        kept += body

    new = re.sub(r'\n{3,}', '\n\n', '\n'.join(kept)).rstrip() + '\n'
    # 目次に残った該当行も落とす
    new = '\n'.join(l for l in new.split('\n') if not (l.startswith('- ') and EX.search(l)))
    open(path, 'w', encoding='utf-8').write(new.rstrip() + '\n')
    return cut

allcut = []
for f in sorted(glob.glob(str(BASE / 'notes' / '*.md'))):
    allcut += [(f, t, b) for t, b in process(f)]

if allcut:
    p = BASE / 'PRIVATE' / '助成金関連_退避.md'
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write('# 助成金・リスキリング関連（公開版から退避）\n\n')
        f.write('> ⚠️ 労働局の調査対象となっている論点のため、公開リポジトリから切り出した。\n')
        f.write('> ここは社内限定。外部に出さないこと。\n\n---\n\n')
        for path, title, body in allcut:
            f.write('## [%s] %s\n\n%s\n\n---\n\n' % (os.path.basename(path), title or '(冒頭)', body))
    print('退避先:', p, p.stat().st_size, 'bytes')
print('切り出した節:', len(allcut))
for path, t in moved:
    print('  -', os.path.basename(path), '/', t)
