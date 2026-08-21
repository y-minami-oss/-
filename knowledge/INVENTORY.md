# インベントリ（このリポジトリに何が入っているか）

| パス | 中身 | サイズ目安 |
|---|---|---|
| `README.md` | 全体像・データソースの棚卸し・カバレッジ・提言 | 5KB |
| `notes/01`〜`07` | テーマ別のノウハウ抽出（営業／社内運営／分析／継続防衛／撮影／企画／採用ファネル） | 計 85KB |
| `notes/08`〜`10` | 打ち合わせ1回ごとの実録 77本（2026年2月〜8月） | 計 730KB |
| `notes/11` | 制作フォーマット集（編集指示書／文字起こし整備基準） | 25KB |
| `notes/12` | 社内運営とユニットエコノミクス（公開版・実額は伏せ） | 18KB |
| `notes/13` | 営業台帳959商談の全量分析（公開版・自社単価は記号化） | 24KB |
| `社内ノウハウ抽出_統合版.md` | 上記すべてを1ファイルに結合 | 909KB |
| `knowledge-base.html` | 全ノートを1ページに統合した読み物版（章内目次＋キーワード検索） | 1.8MB |
| `build.py` | `notes/*.md` から `knowledge-base.html` を生成するスクリプト | 13KB |
| `work/memo.py` | Geminiメモ部分だけを取り出す補助スクリプト | 1KB |
| `docs/google_doc_body.md` | Googleドキュメント用のまとめ本文（リスキリング／助成金は除外） | 163KB |
| `docs/google_doc_body.json` | 同上をApps Script用に段落単位へ変換したもの | 197KB |
| `docs/匿名ラベル一覧.md` | クライアントの記号と照合の手掛かり（実名は含まない） | 3KB |
| `docs/週次更新の仕組み.md` | 週次自動更新の全体像とセットアップ手順 | 3KB |
| `tools/build_doc.py` | `notes/*.md` → `docs/google_doc_body.*` を生成 | 9KB |
| `tools/sync_doc.gs` | Googleドキュメント側のApps Script（毎週日曜23時に本文を全置換） | 4KB |

## リポジトリに含まれないもの（`PRIVATE/`・`.gitignore` 済み）
| パス | なぜ含めないか |
|---|---|
| `PRIVATE/additions_FULL.md` | 実録77本の原本（匿名化前の中間生成物を含む） |
| `PRIVATE/12_..._FULL.md` | 原価・利益構造の実額、業務委託先の処分に関する議論、記録すべきでない発言の全文 |
| `PRIVATE/13_..._FULL.md` | 自社の契約単価の実額 |
| `PRIVATE/raw/` | 会議の生の文字起こし（個人名・実額をそのまま含む） |
| `PRIVATE/anon.py` | 匿名化スクリプト。**実名→記号の対応表そのもの**なので公開できない |
| `PRIVATE/manifest.tsv` | 精読した78議事録のDriveファイルIDと実名ラベル |

## 再生成の手順
```bash
cd knowledge
python3 build.py                        # notes/*.md -> knowledge-base.html
python3 tools/build_doc.py $(date +%F)  # notes/*.md -> Googleドキュメント用の本文
cp work/google_doc_body.json work/google_doc_body.md docs/
```

週次自動更新の仕組みは `docs/週次更新の仕組み.md` を参照。

## 匿名化のかけ方
```bash
python3 PRIVATE/anon.py <入力.md> <出力.md>
```
新しい議事録を追加したら、**必ず `PRIVATE/anon.py` を通してから** `notes/` に置くこと。
`anon.py` の辞書に載っていない固有名詞は素通りするため、追加後は必ず目視とgrepで確認する。
（`anon.py` は実名と記号の対応表そのものなので、リポジトリには含めない。）
