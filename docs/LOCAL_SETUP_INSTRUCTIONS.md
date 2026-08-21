# ローカル実行 指示書

Mac のローカル Claude Code セッションで実行するための指示。
**この章立てのまま上から順に実行できる。** 各章は独立しているので、必要な章だけ実行してもよい。

信頼度の表記はいただいた総まとめ資料の慣例に合わせる。

- **◎ 一次情報** = 公式ドキュメント / 公式スキルで検証済み。そのまま従ってよい。
- **○ 二次情報** = 方向性は妥当だが、数値や仕様を鵜呑みにしない。

---

## 0. この指示書の使い方

リモートセッション(Claude Code on the web)では以下が**できなかった**ため、ローカルに引き継ぐ。

| できなかったこと | 理由 |
|---|---|
| 画像・動画・音声生成の検証(13件) | `~/.claude/.env.local` がコンテナに無い(秘密情報なので当然) |
| スキルの永続設置 | コンテナは使い捨て |
| 自動スキル実行の hook 設置 | 同上。設定はローカルの `~/.claude/` に置くべきもの |

**ローカルには API キーがある**ので、上記すべて実行できる。

---

## 1. スキルの設置 ◎

`ai-knowhow-skill.zip` を Downloads に保存してから:

```bash
cd ~/Downloads
unzip ai-knowhow-skill.zip          # ai-knowhow/ フォルダが1つできる

mkdir -p ~/.claude/skills
cp -R ~/Downloads/ai-knowhow ~/.claude/skills/
```

確認:

```bash
ls ~/.claude/skills/ai-knowhow/          # SKILL.md と references/ があること
```

Claude Code を開き直して `/ai-knowhow` で呼び出せれば設置完了。`/context` でも読み込み状況が見える。

### 特定リポジトリだけで使う場合

```bash
mkdir -p /path/to/repo/.claude/skills
cp -R ~/Downloads/ai-knowhow /path/to/repo/.claude/skills/
```

---

## 2. 自動スキル実行の仕組み

### まず前提: スキルは既に自動起動する ◎

**「自動スキル実行の仕組みを作る」必要は、実は半分ありません。** 公式の設計はこうなっている:

> Skills extend Claude's knowledge with information specific to your project, team, or domain.
> **Claude applies them automatically when relevant**, or you can invoke them directly with `/skill-name`.

起動時にシステムプロンプトへ載るのは各スキルの `name` と `description` **だけ**。
本文はタスクが description に一致したときに初めて読まれる(progressive disclosure)。
つまり**自動起動の精度を決めているのは description**であり、そこが第一の改善レバー。

`disable-model-invocation: true` を書くと自動起動を**切れる**(副作用のある手順書に使う)。
逆に言えば、書かなければ自動が既定。

### 4層の使い分け ◎(公式ドキュメントの整理と一致)

| 仕組み | 性質 | 使いどころ |
|---|---|---|
| **CLAUDE.md** | 毎回のプロンプトに常時ロード | 常時のプロジェクト方針。**短く保つ** |
| **Skills** | description が一致したときオンデマンド | 領域固有の知識・手順 |
| **Hooks** | ライフサイクルで発火する決定的なシェル処理 | **強制したいこと**(モデルの判断に委ねない) |
| **Subagents** | 独自の文脈窓・ツール権限を持つ分身 | 委譲の境界。読み込みの重い調査を隔離 |

**一行ルール: 強制事項 → Hooks / 文脈知識 → Skills / 委譲境界 → Subagents / 常時方針 → CLAUDE.md(短く)。**

公式が明言している重要点:

> CLAUDE.md is loaded every session, so only include things that apply broadly.
> For domain knowledge or workflows that are only relevant sometimes, **use skills instead.**
> Claude loads them on demand without bloating every conversation.

### 手順A: description を磨く(効果が最も大きい) ◎

自動起動が外れるのは、ほぼ description の書き方が原因。**自分が実際に打つ日本語のフレーズを入れる。**

```bash
head -5 ~/.claude/skills/ai-knowhow/SKILL.md
```

現状の description は「議事録の要約やタスク化、リサーチ・競合分析、営業メール…」という列挙型。
自分の口癖に合わせて足す。例:

```yaml
description: 社内AIノウハウ集。「議事録まとめて」「競合調べて」「営業メール書いて」
  「広告コピー」「この資料どう思う?」「どのモデル使う?」「著作権大丈夫?」
  「画像/動画作りたい」等で起動。プロンプトの型・業務プロンプト集・モデル選定・
  設計チェックリスト・生成AIツール早見表を収録。
```

**判定基準: 自分が普段打つ言い方が description に入っているか。** 入っていなければ起動しない。

### 手順B: 決定的に起動させる hook(モデル判断に委ねない) ◎

description は「モデルが判断する」仕組みなので外れることがある。
**絶対に参照させたいなら hook を使う。** 以下は検証済みの契約に基づく実装。

```bash
mkdir -p ~/.claude/hooks
cat > ~/.claude/hooks/route-skill.py <<'PY'
#!/usr/bin/env python3
"""UserPromptSubmit hook — プロンプトに応じて参照すべきスキルを決定的に指示する。

契約(公式ドキュメントで確認済み):
  入力: stdin に JSON。プロンプト本文は "user_input" キー。
  出力: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                "additionalContext": "..."}}
  exit 0 で成功。既定タイムアウトは30秒。
"""
import json
import sys

# キーワード → 読ませる参照ファイル
ROUTES = [
    (("議事録", "要約", "まとめて", "文字起こし", "タスク化", "メール", "コピー",
      "LP", "広告", "SNS", "投稿", "ネタ", "批評", "添削", "リサーチ", "競合"),
     "references/prompt-templates.md"),
    (("モデル", "コスト", "トークン", "料金", "価格", "どれ使", "キャッシュ"),
     "references/model-selection.md"),
    (("RAG", "MCP", "自動化", "エージェント設計", "権限", "著作権", "商用",
      "ライセンス", "納品", "法務"),
     "references/design-checklists.md"),
    (("画像", "動画", "スライド", "サムネ", "音声", "アバター", "生成AI"),
     "references/media-generation.md"),
    (("実装", "リファクタ", "テスト", "レビュー", "バグ", "直して", "plan"),
     "references/agent-workflow.md"),
]

SKILL = "~/.claude/skills/ai-knowhow"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # 壊れた入力でプロンプトを止めない

    prompt = payload.get("user_input") or ""
    hits = [path for words, path in ROUTES if any(w in prompt for w in words)]
    if not hits:
        return 0  # 該当なし。何も注入しない

    files = "\n".join(f"  - {SKILL}/{p}" for p in dict.fromkeys(hits))
    context = (
        "このタスクは ai-knowhow スキルの対象です。回答の前に必ず読むこと:\n"
        f"{files}\n"
        "読んだ内容の型・チェックリストに従って回答すること。"
    )
    json.dump(
        {"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }},
        sys.stdout,
        ensure_ascii=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
chmod +x ~/.claude/hooks/route-skill.py
```

`~/.claude/settings.json` に登録(既存の `hooks` があればマージする):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/route-skill.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**設置前に必ず単体で動作確認する**(hook が壊れていると全プロンプトに影響する):

```bash
# 該当するケース
echo '{"user_input":"議事録まとめて"}' | ~/.claude/hooks/route-skill.py; echo " <- exit=$?"
# 該当しないケース(何も出力されないこと)
echo '{"user_input":"今日は何曜日?"}' | ~/.claude/hooks/route-skill.py; echo " <- exit=$?"
# 壊れた入力(落ちないこと)
echo 'not json' | ~/.claude/hooks/route-skill.py; echo " <- exit=$?"
```

3つすべて exit=0 で、1つ目だけ JSON を吐けば正常。
登録後は `/hooks` で設定を確認できる。

> ⚠️ hook は**全プロンプトで発火する**。キーワードを広げすぎると毎回無関係な参照を注入して
> 文脈を汚し、かえって性能が落ちる。狭く始めて、外れたときだけ足す。

### 手順C: この仕組み自体を検証する

hook 設置後、実際に効いているかを確かめる:

1. 新しいセッションで「議事録まとめて」と打つ
2. Claude が `references/prompt-templates.md` を読んだか確認する
3. 読んでいなければ hook が発火していない → 上の単体テストに戻る

**「設置した」で終わらせず、実際の起動を確認する。** これは検証済みノウハウ③そのもの。

---

## 3. 未検証13件の検証手順

リモートで ❌ 判定になった生成AI系。**ローカルには鍵があるので実行できる。**

### 前提の確認

```bash
ls -la ~/.claude/.env.local && cut -d= -f1 ~/.claude/.env.local
```

`GEMINI_API_KEY` / `OPENAI_API_KEY` が並んでいれば準備完了。

### 検証の進め方

**13件を一度にやらない。1件ずつ、無料枠か最小コストで1本作って結果を見る。**

優先順(費用対効果が高い順):

| 順 | 対象 | 使うもの | 判定したいこと |
|---|---|---|---|
| 1 | スライド生成 | `/s-base1-trepro`(Gemini) | 実務で使える初稿が出るか |
| 2 | 画像: 文字入り | Nano Banana Pro | 早見表の「テキスト精度」の主張が本当か |
| 3 | 画像: 図解 | GPT-image-2 | 「小さな文字/UIに強い」が本当か |
| 4 | 動画 | 無料枠のあるツール | そもそも実務品質に達するか |

各件が終わったら、結果を反映する:

```bash
# 実測結果で「未検証」マークを置き換える
$EDITOR ~/.claude/skills/ai-knowhow/references/media-generation.md
```

**書き換えるときのルール:** 出典の主張ではなく**自分が観測した結果**を書く。
「CTR約4倍」のような他社の数値は、自分の案件で計測した数字に置き換えるか、
出典の主張だと明記したまま残す。

### 検証できない場合の扱い

課金が必要で試さないと決めたものは、**「未検証」のまま残す。**
消したり、検証したことにしたりしない。判定が空欄であること自体が情報。

---

## 4. 新しい総まとめ資料の反映

いただいた「最先端AIノウハウ 総まとめ(2026年8月21日)」は、
既存の Notion DB より**出典が明確で、信頼度マークが付いている**点で上位互換。反映すべき。

### 4-1. スキルに足すべき章(現状の references に無いもの)

| 追加する参照ファイル | 元にする章 | 理由 |
|---|---|---|
| `references/security.md` | §9 OWASP LLM Top 10 2026 | **現状ゼロ。最大の欠落。** LLM03「過剰な権限」の急上昇は、エージェント設計に直結する |
| `references/evals.md` | §8 評価・品質管理 | 「検証手段を先に用意する」の具体的な実装方法。LLM-as-a-Judge の注意点3点は実務的 |
| `references/governance.md` | §10 法規制 + §13 公的PDF | 既存の `design-checklists.md` の商用利用チェックを、公的PDFの直リンクで裏打ちできる |
| `references/agent-patterns.md` | §4 5つのワークフローパターン | 「エージェントにする前に立ち止まる」4判定基準は既存の references に無い |

### 4-2. 既存ファイルの更新

| ファイル | 更新内容 |
|---|---|
| `references/model-selection.md` | Claude のモデル表を差し替え(下記 §5 の検証済み表を使う)。**API仕様の節を新設**(adaptive thinking / effort / キャッシュ / プリフィル廃止) |
| `references/agent-workflow.md` | §5 の「カスタマイズ4層」の表を追加。`AGENTS.md` との違いも |
| `references/design-checklists.md` | §10 の公的PDF直リンクを追記。§6 の「プロンプト → RAG → ファインチューニング」決定木を追加 |
| `SKILL.md` | 上記の追加ファイルを索引に追加 |

### 4-3. SKILL.md のサイズに注意 ○

**「スキル本体は500トークン以下に抑える」という指針がある**(二次情報)。
公式は数値を出していないが「短く保ち、長い参照は別ファイルにする」とは明言している ◎。

現状の `SKILL.md` は日本語34行で、おそらく1,000〜1,800トークン。**上記の追加で索引が伸びるので、
本文を削って索引だけにする**のが正しい方向。全体原則5つは残し、説明文を削る。

### 4-4. 反映しないほうがよいもの

| 対象 | 理由 |
|---|---|
| §2 の二次情報のモデル名 | 資料自身が警告している通り、記事間で世代番号が矛盾している(GPT-5.4/5.5/5.6が併存) |
| §7 の製品名・バージョン | すべて二次情報。実際に触って確認したものだけ書く(§3の手順) |
| §1 の統計数値 | 調査主体と定義で数字が全く違う(個人58.8% / 企業86.4% / 活用率34.5%)。使うときは定義とセットで |

---

## 5. リモート検証の訂正事項

**先に報告した内容のうち、2件を訂正する。**

### 訂正1: F-4「モデルIDが存在しない懸念」は取り下げ ◎

`src/extract_receipt.py` の `MODEL = "claude-opus-4-8"` は**実在する正規のモデルID**だった。
公式のモデル表で確認済み: Claude Opus 4.8 / `claude-opus-4-8` / 1M文脈 / $5.00・$25.00 per 1M。
**リポジトリは壊れていない。**

ただし公式の既定方針は「ユーザーが明示しない限り `claude-opus-5` を使う」なので、
**更新を検討する価値はある**(強制ではない):

```python
# src/extract_receipt.py
MODEL = "claude-opus-5"   # 現行の既定。1M文脈 / $5.00・$25.00 per 1M
```

⚠️ **移行時の注意:** Opus 5 は **thinking が既定でオン**(4.8 は既定オフ)。
領収書読み取りは単純な抽出なのでコストとレイテンシが上がる可能性がある。
その場合は `output_config={"effort": "low"}` を添える。

### 訂正2: `output_format` は非推奨ではなかった ◎

`output_format` が非推奨なのは `messages.create()` の場合**だけ**。
`client.messages.parse(..., output_format=PydanticModel)` は**現行の推奨API**。
`src/extract_receipt.py` の書き方は正しい。修正不要。

### 検証済みAPI仕様(いただいた資料の §2 と一致 ◎)

| 項目 | 現行の正しい書き方 | 古い書き方の結果 |
|---|---|---|
| 拡張思考 | `thinking={"type": "adaptive"}` | `budget_tokens` は Fable 5 / Opus 5 / 4.8 / 4.7 / Sonnet 5 で **400エラー** |
| 深さ制御 | `output_config={"effort": "..."}` | `low`/`medium`/`high`/`xhigh`/`max`。既定は `high`。コーディング・エージェントは `xhigh` |
| 構造化出力 | `.parse(output_format=Model)` または `.create(output_config={"format": {...}})` | `.create(output_format=...)` は非推奨 |
| プリフィル | 使えない。構造化出力で代替 | Opus 5 / 4.8 / 4.7 / 4.6 / Fable 5 / Sonnet 5・4.6 で **400エラー** |
| キャッシュ | 静的な内容を先頭、変動する内容を末尾 | 先頭に `datetime.now()` を置くと毎回無効化。`usage.cache_read_input_tokens` が0なら失敗 |

### モデル表(公式・2026-06-24時点のキャッシュ値)

| モデル | モデルID | 文脈 | 入力 $/1M | 出力 $/1M |
|---|---|---|---|---|
| Claude Fable 5 | `claude-fable-5` | 1M | $10.00 | $50.00 |
| Claude Opus 5 | `claude-opus-5` | 1M | $5.00 | $25.00 |
| Claude Opus 4.8 | `claude-opus-4-8` | 1M | $5.00 | $25.00 |
| Claude Opus 4.7 | `claude-opus-4-7` | 1M | $5.00 | $25.00 |
| Claude Opus 4.6 | `claude-opus-4-6` | 1M | $5.00 | $25.00 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | $3.00 | $15.00 |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 1M | $3.00 | $15.00 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | $1.00 | $5.00 |

> いただいた資料の表には `claude-opus-4-7` / `claude-opus-4-6` が抜けている。
> また Sonnet 5 には期間限定の導入価格があるため、**価格は必ず当日確認する。**
> モデルIDは**そのままの文字列を使う**。日付サフィックスを付けない。

---

## 6. まだ残っている作業(Notion DB側)

リモートセッションで見つけたが、書き込みになるため実行しなかったもの。

| # | 内容 | 対象 |
|---|---|---|
| 1 | 実在しない社内スキル名6件の修正 | `ai-video-studio` `higgsfield-promo-video` `image-studio` `s-brand-slide` `deep-research` `schedule` → 実在するのは `s-base1-trepro` `s-base2-trepro` `nanobanana-slide-generator-v3-flash` |
| 2 | 本文が空の2ページに加筆 | `コーディングagentの実務フロー` / `Context rot対策` |
| 3 | 市場情報74件の鮮度更新 | 特に Sora の提供状況、モデル価格、EU AI Act |
| 4 | 公式の新機構を追加 | `/goal` 条件、Stop hook、`/rewind`、`/btw`、agent teams |
| 5 | セキュリティ章の新設 | OWASP LLM Top 10 2026(DB に該当項目が無い) |

---

## 7. 実行順のおすすめ

1. **§1 スキル設置** — 5分。まずこれだけで使える状態になる
2. **§2 手順A description 磨き** — 10分。自動起動の精度が最も上がる
3. **§2 手順B hook** — 30分。単体テストまで含めて。決定的に効かせたいなら
4. **§4-1 security.md の追加** — 最大の欠落を埋める
5. **§3 生成AI検証** — 1件ずつ。急がない
6. **§5 の訂正をリポジトリに反映** — モデルID更新は任意

