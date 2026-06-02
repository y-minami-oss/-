# 経費入力フォームのセレクタ対応表(フェーズ2で記入)

`src/inspect_form.py` を実行して得た `form_dump.txt` を見ながら、
TeamSpirit 経費入力画面の各要素のセレクタをここに記録します。
これをもとに `src/teamspirit.py` の `fill_expense_form` を実装します。

## 調査メモ

- 経費画面は iframe(Visualforce)の中か? : ( 未確認 / はい / いいえ )
- iframe の場合のセレクタ: `iframe[ ... ]`
- フレームのURL:

## 入力欄・ボタンの対応

| 項目 | 役割 | セレクタ | 入力方法 | 備考 |
|------|------|----------|----------|------|
| 新規入力ボタン | 明細追加 | `TODO` | `.click()` | |
| 日付 | receipt.date | `TODO` | `.fill()` | 日付ピッカーの形式に注意 |
| 金額 | receipt.amount | `TODO` | `.fill()` | カンマ要否を確認 |
| 科目 | receipt.category | `TODO` | `.select_option(label=...)` | プルダウンの選択肢名 |
| 摘要 | vendor + description | `TODO` | `.fill()` | |
| 支払先 | receipt.vendor | `TODO` | `.fill()` | 科目により欄が出る場合あり |
| 領収書添付 | ファイル | `TODO` | `.set_input_files()` | アップロードUIの確認 |
| 保存(下書き) | — | `TODO` | `.click()` | |
| 申請 | — | `TODO` | `.click()` | 既定では押さない |

## 科目プルダウンの選択肢(実物)

inspect 時に確認した、実際にプルダウンに表示される科目名を列挙:

- (ここに記入)

→ この一覧を `config.yaml` の `expense_categories` に反映する。
