# analytics.md — GA4 イベント設計書

対象：恭子ママ採用LP（`lp/yasukomama/index.html` ＋ `analytics.js`）
最終更新：2026-06-06

---

## 1. 計測の基本設計

- **タグ方式**：gtag.js（GA4）。`analytics.js` に集約。
- **無効化**：`LP_CONFIG.GA_ID` が未設定（`G-XXXXXXXXXX` のまま）の場合は**タグを読み込まず**、イベントはコンソール出力のみ。誤計測・404を防止。
- **アトリビューション**：初回流入時の `utm_*` / `v`（動画ID）を `localStorage("lp_attr")` に保存し、**全イベントに付与**。これによりTikTok動画別・UTM別の貢献を全イベントで追跡可能。

### 設定箇所（index.html）
```js
window.LP_CONFIG = {
  LINE_URL: "https://lin.ee/6VX0gci",
  DM_URL:   "https://www.tiktok.com/@towamembers",
  GA_ID:    "G-XXXXXXXXXX"   // ←ここに測定IDを入れると計測開始
};
```

---

## 2. イベント一覧

| イベント名 | 種別 | 発火タイミング | 主なパラメータ | 重複防止 |
|---|---|---|---|---|
| `page_view` | 標準＋明示 | LP表示時 | `page_location`, 流入パラメータ | — |
| `first_visit` | 標準＋独自 | 初回訪問時のみ | 流入パラメータ | localStorage |
| `scroll_50` | カスタム | スクロール50%到達 | 流入パラメータ | フラグ |
| `scroll_90` | カスタム | スクロール90%到達 | 流入パラメータ | フラグ |
| `line_add_click` | カスタム★CV | LINE追加ボタン押下 | `location`(mid/sticky) | — |
| `dm_click` | カスタム | TikTok DM導線押下 | — | — |

### 全イベント共通パラメータ（自動付与）
| パラメータ | 内容 | 例 |
|---|---|---|
| `utm_source` | 流入元 | `tiktok` |
| `utm_medium` | 媒体 | `bio` / `social` |
| `utm_campaign` | 施策 | `recruit_2606` |
| `utm_content` | 区分 | `pinned1` |
| `landing_video` | TikTok動画ID（`?v=`） | `7646308872185007378` |

---

## 3. 推奨URL付与ルール（運用）

TikTokプロフィール／各動画から飛ばすリンクには、流入元を識別するパラメータを付ける。

```
https://<LP_URL>/?utm_source=tiktok&utm_medium=bio&utm_campaign=recruit&v=<動画ID>
```

- `utm_medium=bio` … プロフリンク経由
- `utm_medium=comment` … 固定コメント経由
- `v=<動画ID>` … どの動画から来たか（動画別分析の要）

---

## 4. GA4 側の必須設定（測定ID投入後）

1. **キーイベント登録**：管理 → イベント → `line_add_click` を「キーイベント（コンバージョン）」にマーク
2. **カスタムディメンション登録**（イベントスコープ）：`landing_video`, `location` を登録 → 探索で使用可能に
3. **データ保持期間**：管理 → データ設定 → データ保持 を「14ヶ月」に延長推奨

---

## 5. デバッグ手順

- `LP_CONFIG.GA_ID` を本物に設定 → GA4「管理 → DebugView」で発火確認
- 未設定のままでもブラウザのコンソールに `[analytics:disabled] <event>` が出るので**ロジックの動作確認は可能**
- スクロール／クリックを行い、各イベントの発火を確認
