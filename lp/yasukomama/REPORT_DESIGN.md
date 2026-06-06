# REPORT_DESIGN.md — コンバージョン設計 ＆ GA4探索レポート設計

対象：恭子ママ採用LP
最終更新：2026-06-06

---

## 1. KPIツリー（採用ファネル全体）

```
TikTok再生 → プロフ閲覧 → ★LP訪問 → ★LINEクリック → LINE登録 → 応募 → 採用
              (TikTok)     (GA4)        (GA4)          (LINE/シート)
```

| 階層 | KPI | 定義 | データ源 |
|---|---|---|---|
| 集客 | **LP訪問数** | `page_view`（セッション/ユーザー） | GA4 |
| 集客 | **TikTok動画別流入** | `landing_video` 別の訪問 | GA4 |
| 集客 | **UTM別成果** | `utm_source/medium/campaign` 別 | GA4 |
| 行動 | **LINEクリック率** | `line_add_click` ÷ `page_view` | GA4 |
| 転換 | **LINE登録率** | LINE登録 ÷ `line_add_click` | LINE＋GA4 |
| 成果 | **CVR** | LINE登録（=CV）÷ LP訪問 | GA4＋LINE |
| 成果 | 応募/採用 | 月次の応募・採用数 | LINEログ/効果測定シート |

---

## 2. イベント → KPI 対応表

| イベント | 直接算出できるKPI | 計算式 |
|---|---|---|
| `page_view` | LP訪問数 | 件数 |
| `first_visit` | 新規訪問数・リピート率 | first_visit ÷ page_view |
| `scroll_50` | 中間到達率（関心度） | scroll_50 ÷ page_view |
| `scroll_90` | 読了率（情報十分性） | scroll_90 ÷ page_view |
| `line_add_click` | **LINEクリック率（主要CV手前）** | line_add_click ÷ page_view |
| `line_add_click` × `location` | CTA位置別効果 | mid vs sticky |
| `line_add_click` × `landing_video` | **動画別CV貢献** | 動画別 line_add_click |
| `dm_click` | 代替導線貢献 | dm_click ÷ page_view |

> GA4側で計測できるのは `line_add_click`（LINE遷移）まで。**実際のLINE登録/応募/採用はLINE・効果測定シートと突合**して算出する（境界はLINEドメインのため）。

---

## 3. GA4 探索（Exploration）レポート設計

### ① 流入分析（どこから来たか）
- 手法：自由形式
- 行：`utm_source`, `utm_medium`, `utm_campaign`
- 値：`page_view`（総数）、ユーザー数、`line_add_click`、CVR（line_add_click÷page_view）
- 目的：UTM別にLP訪問とCVを評価。広告/オーガニック/プロフ/コメントの貢献比較

### ② 動画別分析（どの動画が効くか）
- 手法：自由形式
- 行：`landing_video`（カスタムディメンション）
- 値：`page_view`、`line_add_click`、CVR
- 目的：**TikTok動画別にLP送客→CV貢献を特定 → 勝ち筋動画を量産**（効果測定シートの月次へ反映）

### ③ CTA分析（どのボタンが押されるか）
- 手法：自由形式
- 行：`location`（mid / sticky）
- 値：`line_add_click`、`scroll_50`、`scroll_90`
- 目的：CTA位置別の効果、スクロール到達とクリックの関係。LP構成最適化の判断材料

### ④ コンバージョン分析（ファネルのどこで落ちるか）
- 手法：**目標到達プロセス（ファネル）データ探索**
- ステップ：`page_view` → `scroll_50` → `scroll_90` → `line_add_click`
- 内訳ディメンション：`utm_source` または `landing_video`
- 目的：LP内のどの段階で離脱しているかを可視化。前回特定の「プロフ→LINE 0.03%」改善を定量追跡

---

## 4. ダッシュボード化（任意・推奨）

- **Looker Studio** にGA4を接続し、上記①〜④をスコアカード＋時系列で常設
- 効果測定シート（応募・採用）も同ダッシュボードに統合 → **再生〜採用まで一気通貫**で可視化
- 3アドレス（ANALYTICS_ACCESS.md）に閲覧共有

---

## 5. 月次レビュー運用

| 頻度 | 見る指標 | アクション |
|---|---|---|
| 週次 | LINEクリック率、CTA位置別 | 不調ならCTA文言/位置を調整 |
| 月次 | 動画別CV貢献、UTM別CVR | 勝ち筋動画を量産、弱い導線を改善 |
| 月次 | ファネル離脱段階 | 離脱箇所のLP改修（プロフ→LINEの穴を継続改善） |
