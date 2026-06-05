# 業務自動化ツール集

このリポジトリには2つのツールが入っています。

| ツール | 概要 | ドキュメント |
| --- | --- | --- |
| TeamSpirit 経費申請 自動化 | 領収書を読み取って経費明細に入力 | このREADME(以下) |
| **プロジェクトシート 毎月更新** | 効果測定シートから毎月のKPIを集計し、プロジェクトシートに貼る数字をコピペ用に出力 | **[docs/PROJECT_SHEET.md](docs/PROJECT_SHEET.md)** |

---

# TeamSpirit 経費申請 自動化ツール

領収書のファイル(写真・PDF)を `inbox/` に入れて実行すると、
Claude が内容を読み取り、TeamSpirit の経費明細に自動入力するツールです。

> ⚠️ ご自身のPC(Mac)で動かすことを前提にしています。
> 会社のTeamSpirit(社内ログインが必要)を操作するため、クラウド上ではなく
> 手元のMacで実行します。

## 全体の流れ

```
inbox/ に領収書を入れる
   ↓ ① Claude が読み取り(金額・日付・支払先・科目・摘要)
   ↓ ② ターミナルに内容を表示 → 人が確認
   ↓ ③ Playwright が TeamSpirit にログイン → 経費明細を入力 → 領収書を添付
   ↓ ④ 既定では「下書き保存」で停止(人が最終確認して申請ボタンを押す)
```

## 安全に関する方針

- 経費申請は会社へのお金の申請です。**既定では最終「申請」まで自動化せず、
  入力・添付して下書きで止めます**(`config.yaml` の `draft_only: true`)。
- 認証情報(APIキー・ログインID/パスワード)は `.env` に置き、Git管理から除外します。
- 領収書ファイル自体もコミットされません(個人情報のため `.gitignore` 済み)。

---

## セットアップ(Mac・初回のみ)

```bash
# 1. Python 仮想環境を作る
python3 -m venv .venv
source .venv/bin/activate

# 2. 依存パッケージをインストール
pip install -r requirements.txt
playwright install chromium

# 3. 認証情報を設定
cp .env.example .env
#   → .env をエディタで開き、ANTHROPIC_API_KEY / TS_USERNAME / TS_PASSWORD を記入

# 4. 設定ファイルを用意
cp config.example.yaml config.yaml
#   → expense_categories を、自社TeamSpiritで実際に使う科目名に書き換え
```

---

## 使い方

### APIキーがまだ無い場合 — モックモードで流れだけ試す

Claudeを呼ばずダミーデータで全体の流れを確認できます(APIキー不要):

```bash
source .venv/bin/activate
# inbox/ に適当な画像かPDFを1枚入れてから:
python -m src.run --mock --extract-only
```

### まず「読み取りだけ」を試す(TeamSpiritには触りません)

`inbox/` に領収書の写真かPDFを入れて:

```bash
source .venv/bin/activate
python -m src.run --extract-only
```

金額・日付・科目などが正しく読み取れるか、ここで確認します。
読み取り精度は `config.yaml` の科目候補やプロンプト調整で改善できます。

### TeamSpirit への入力まで行う

```bash
python -m src.run
```

ブラウザが立ち上がり、ログイン → 経費入力 → 下書き保存まで行います。
1件ごとに入力するか確認します(`confirm_each: true`)。

> ⏳ **TeamSpirit への入力部分はフェーズ2で完成します**(下記参照)。

---

## 開発フェーズ

このツールは2段階で作っています。

### フェーズ1(完了)— 土台
- ✅ 領収書の読み取り(Claude Vision / 画像・PDF対応)
- ✅ 設定・認証情報の仕組み
- ✅ TeamSpirit ログイン処理
- ✅ 画面構造の調査ツール(`inspect_form.py`)
- ✅ CLI(読み取り → 確認 → 入力 の流れ)

### フェーズ2(これから・実画面を見ながら)— 入力の完成
TeamSpirit の経費入力フォームの「どの欄に何を入れるか」は、実際の画面を
見ないと確定できません。以下の手順で特定します。

```bash
python -m src.inspect_form
```

1. ブラウザが開くので、経費の「新規入力」画面まで進める
2. ターミナルで Enter → `form_dump.txt` / `form_dump.html` が出力される
3. その内容をもとに `docs/DOM_MAPPING.md` にセレクタを記録
4. `src/teamspirit.py` の `fill_expense_form()` を実装

`form_dump.txt` を共有してもらえれば、セレクタ特定と実装を一緒に進められます。

---

## テスト

APIキー無しで動く自動テストがあります(Claudeは偽クライアントで差し替え):

```bash
source .venv/bin/activate
python -m unittest tests.test_logic -v
```

## ファイル構成

```
.
├── README.md              このファイル
├── requirements.txt       依存パッケージ
├── .env.example           認証情報のテンプレ(コピーして .env を作る)
├── config.example.yaml    設定のテンプレ(コピーして config.yaml を作る)
├── inbox/                 ここに領収書を入れる
├── processed/             処理済みの領収書の移動先
├── docs/
│   └── DOM_MAPPING.md      経費フォームのセレクタ対応表(フェーズ2で記入)
└── src/
    ├── models.py          抽出データの構造定義
    ├── extract_receipt.py 領収書の読み取り(Claude)
    ├── teamspirit.py      TeamSpirit のブラウザ自動操作
    ├── inspect_form.py    画面構造の調査ツール
    ├── config.py          設定読み込み
    └── run.py             メイン処理(CLI)
```

## よくある注意点

- **MFA(二段階認証)が有効になった場合**、自動ログインは使えません。
  その場合は手動でログインし、`storage_state.json` にセッションを保存して
  再利用する運用に切り替えます(相談してください)。
- TeamSpirit の画面仕様が変わると、セレクタの修正が必要になることがあります。
