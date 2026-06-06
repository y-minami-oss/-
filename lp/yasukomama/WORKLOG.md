# WORKLOG — 採用LP 分析基盤構築

## 2026-06-06

### フェーズ1：環境調査
- GA操作ツール：**無し**（mcp__google_analytics 系なし）
- Google API（GA Admin）：**不可**
- Drive API：MCP有（検索/読取/DL/コピー/権限**閲覧**）。共有**付与は不可**
- GitHub権限：MCP有（`y-minami-oss/-` にスコープ）。コミット/プッシュ可
- Vercel権限：**無し**＋実行環境の外部通信遮断によりデプロイ不可
- LP構成：`lp/yasukomama/index.html` 単一ファイル → 計測を `analytics.js` へ分離

### フェーズ2：GA4実装
- `analytics.js` 作成：page_view / first_visit / scroll_50 / scroll_90 / line_add_click / dm_click
- 測定ID未設定時は無効化（コンソール出力のみ）、UTM/動画IDをlocalStorage保存し全イベント付与
- `index.html` をリファクタ（`LP_CONFIG` 化、analytics.js読込）
- `analytics.md` 作成（イベント設計書）

### フェーズ3：権限管理
- `ANALYTICS_ACCESS.md` 作成（管理者/編集者/閲覧者・付与/削除/緊急対応手順）
- 付与は環境制約で自動実行不可 → 「人間が2分で実施する手順」を明記

### フェーズ4：コンバージョン設計
- KPIツリー＋イベント→KPI対応表を `REPORT_DESIGN.md` に作成

### フェーズ5：レポート構築
- `REPORT_DESIGN.md` にGA4探索①流入②動画別③CTA④コンバージョンを設計

### 成果物
- index.html（改修）/ analytics.js / analytics.md / ANALYTICS_ACCESS.md / REPORT_DESIGN.md / WORKLOG.md
