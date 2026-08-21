# CLAUDE.md

TeamSpirit 経費申請の自動化ツール(Python + Playwright + Claude Vision)。
領収書を `inbox/` に置いて実行すると、読み取り → 確認 → TeamSpirit へ下書き入力まで行う。

## コマンド

```bash
python3 -m pip install -r requirements.txt   # 依存(テスト実行前に必須)
python3 -m unittest tests.test_logic -v      # テスト12件。APIキー不要
python -m src.run --mock --extract-only      # APIキー無しで流れを確認
python -m src.run --extract-only             # 読み取りのみ(TeamSpiritに触らない)
python -m src.inspect_form                   # フォーム構造の調査(フェーズ2用)
```

## このリポジトリの決めごと

- 経費申請は金銭申請。**既定では最終「申請」まで自動化しない**(`config.yaml` の `draft_only: true`)。この既定を勝手に変えない。
- `.env` / 領収書ファイル / `storage_state.json` は**絶対にコミットしない**(`.gitignore` 済み)。
- コード・コメント・ドキュメントは日本語。
- フェーズ2(`fill_expense_form()`)は実画面のセレクタが必要。憶測でセレクタを書かず、`docs/DOM_MAPPING.md` に記録されたものだけ使う。

## AIの使い方(検証済みルール)

出典と検証結果は `docs/AI_KNOWHOW_VALIDATION.md`。詳細な型・プロンプト集は `/ai-knowhow` スキルに置いてあり、必要なときだけ読み込む。

- **検証手段を先に用意する。** テスト・ビルド・スクリーンショットのいずれも無いタスクは、まず検証方法を作る。「できたはず」で終わらせず、実行結果を証拠として示す。
- **探索と実装を分ける。** 複数ファイルに触る/方針が不確かなときは plan mode で計画→レビュー→実装。1文で差分を説明できる小さな変更では計画を省く。
- **調査は subagent に逃がす。** 大量のファイルを読む調査で本文脈を埋めない。
- **無関係なタスクに移る前に `/clear`。** 同じ問題で2回修正しても直らなければ、文脈を捨てて具体的な指示で作り直す。
- **このファイルは短く保つ。** 各行に「消したらClaudeが間違えるか?」を問い、否なら削る。長いCLAUDE.mdは無視される。その都度の指示はここに書かない。
- **プロンプトは Role + Context + Task + Format のラベル付き構造で渡す。** 「step by step で考えて」は書かない(最新の推論モデルでは逆効果)。
