"""メイン処理(CLI)。

毎月の使い方:
    python -m project_sheet.run                # 先月分を集計して出力
    python -m project_sheet.run --month 2026-05 # 月を指定
    python -m project_sheet.run --client 廣記   # 特定クライアントだけ

出力は「プロジェクトシートに貼る数字」のコピペ用テキスト。
"""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
from typing import Any

import yaml

from . import gsheets, master, report, sources
from .aggregate import aggregate_dc_rows


def _load_config(path: str) -> dict[str, Any]:
    for name in (path, "project_sheet/config.example.yaml"):
        p = Path(name)
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("config.yaml が見つかりません。config.example.yaml をコピーしてください。")


def _previous_month(today: _dt.date) -> tuple[int, int]:
    first = today.replace(day=1)
    last_prev = first - _dt.timedelta(days=1)
    return last_prev.year, last_prev.month


def _parse_month(arg: str | None) -> tuple[int, int]:
    if not arg:
        return _previous_month(_dt.date.today())
    y, m = arg.split("-")
    return int(y), int(m)


def _resolve_koka_id(cfg: dict, client_obj: Any, client_name: str) -> str | None:
    ids = cfg.get("koka_spreadsheet_ids", {}) or {}
    if ids.get(client_name):
        return ids[client_name]
    # タイトル検索フォールバック
    overrides = cfg.get("search_keyword_overrides", {}) or {}
    keyword = overrides.get(client_name) or client_name.strip().lstrip("株式会社").strip()
    return gsheets.find_spreadsheet_id_by_title(client_obj, keyword)


def main() -> None:
    ap = argparse.ArgumentParser(description="プロジェクトシート 毎月更新ツール")
    ap.add_argument("--month", help="対象月 YYYY-MM(既定:先月)")
    ap.add_argument("--owner", help="担当者名(既定:config の owner)")
    ap.add_argument("--client", help="クライアント名の部分一致で絞り込み")
    ap.add_argument("--config", default="project_sheet/config.yaml", help="設定ファイル")
    args = ap.parse_args()

    cfg = _load_config(args.config)
    owner = args.owner or cfg.get("owner", "三並")
    year, month = _parse_month(args.month)
    dc_sheet = cfg.get("dc_sheet_name", "簡単DC")

    client = gsheets.get_client()

    grid = master.read_master_grid_from_gsheet(
        client, cfg["master_spreadsheet_id"], cfg.get("master_sheet_name", "全体シート")
    )
    records = master.parse_master_grid(grid)
    targets = master.active_clients_for(records, owner)
    if args.client:
        targets = [r for r in targets if args.client in r.client]

    blocks, errors = [], []
    for rec in targets:
        koka_id = _resolve_koka_id(cfg, client, rec.client)
        if not koka_id:
            errors.append(f"{rec.client}: 効果測定シートが見つかりません(config に ID を登録してください)")
            continue
        try:
            rows = sources.read_dc_rows_from_gsheet(client, koka_id, dc_sheet)
            kpi = aggregate_dc_rows(rows, year, month)
            blocks.append(report.format_client_block(
                rec.client, kpi, no=rec.no, roles=rec.roles_of(owner)))
        except Exception as e:  # noqa: BLE001 — 1件失敗しても他は続行
            errors.append(f"{rec.client}: 取得エラー {e}")

    print(report.format_report(f"{year}年{month}月", blocks, errors=errors))


if __name__ == "__main__":
    main()
