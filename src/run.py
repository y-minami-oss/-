"""メイン処理: inbox の領収書を読み取り → 確認 → TeamSpirit に入力。

使い方(Mac で):
    source .venv/bin/activate
    python -m src.run                # inbox の中身を全部処理
    python -m src.run --extract-only # 読み取りだけ(TeamSpiritは触らない)
    python -m src.run path/to/a.jpg  # 特定ファイルだけ処理

フェーズ1の現状:
  - 読み取り(--extract-only)は今すぐ動きます。
  - TeamSpirit への入力はフェーズ2で fill_expense_form を実装後に動きます。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

from .config import load_config
from .extract_receipt import IMAGE_MEDIA_TYPES, extract_receipt, mock_extract
from .models import Receipt

SUPPORTED_SUFFIXES = set(IMAGE_MEDIA_TYPES) | {".pdf"}


def find_receipts(inbox: Path, explicit: list[str]) -> list[Path]:
    if explicit:
        return [Path(p) for p in explicit]
    return sorted(
        p
        for p in inbox.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )


def print_receipt(receipt: Receipt) -> None:
    print("  ┌─ 読み取り結果 " + "─" * 40)
    print(f"  │ 日付   : {receipt.date}")
    print(f"  │ 金額   : {receipt.amount:,} {receipt.currency}")
    print(f"  │ 支払先 : {receipt.vendor}")
    print(f"  │ 科目   : {receipt.category}")
    print(f"  │ 摘要   : {receipt.description}")
    if receipt.tax_amount is not None:
        print(f"  │ 消費税 : {receipt.tax_amount:,}")
    if receipt.payment_method:
        print(f"  │ 支払方法: {receipt.payment_method}")
    print(f"  │ 自信度 : {receipt.confidence:.0%}")
    if receipt.notes:
        print(f"  │ ⚠ 備考 : {receipt.notes}")
    print("  └" + "─" * 54)


def main() -> None:
    load_dotenv()
    cfg = load_config()

    parser = argparse.ArgumentParser(description="TeamSpirit 経費申請 自動化")
    parser.add_argument("files", nargs="*", help="処理する領収書(省略時は inbox 全部)")
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="読み取りだけ行い、TeamSpirit には入力しない",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Claudeを呼ばずダミーデータで動かす(APIキー不要・動作確認用)",
    )
    args = parser.parse_args()

    # 読み取り関数を選ぶ(モック or 本物)
    extract = mock_extract if args.mock else extract_receipt
    if args.mock:
        print("⚠ モックモード: ダミーデータで動作確認します(Claudeは呼びません)。\n")

    inbox = Path(cfg["paths"]["inbox"])
    processed = Path(cfg["paths"]["processed"])
    categories = cfg["expense_categories"]
    behavior = cfg.get("behavior", {})

    receipts = find_receipts(inbox, args.files)
    if not receipts:
        print(f"処理対象がありません。{inbox}/ に領収書(画像/PDF)を入れてください。")
        return

    print(f"{len(receipts)} 件の領収書を処理します。\n")

    # まず全部読み取る
    extracted: list[tuple[Path, Receipt]] = []
    for path in receipts:
        print(f"📄 読み取り中: {path.name}")
        try:
            receipt = extract(path, categories)
        except Exception as e:
            print(f"  ✗ 読み取り失敗: {e}\n")
            continue
        print_receipt(receipt)
        extracted.append((path, receipt))
        print()

    if args.extract_only:
        print("--extract-only 指定のため、ここで終了します。")
        return

    # TeamSpirit へ入力(フェーズ2で fill_expense_form 実装後に動作)
    from .teamspirit import TeamSpiritClient  # 遅延 import(Playwright未導入でも読み取りは動く)

    draft_only = behavior.get("draft_only", True)
    confirm_each = behavior.get("confirm_each", True)
    show_browser = behavior.get("show_browser", True)

    print("\nTeamSpirit にログインします...")
    with TeamSpiritClient(show_browser=show_browser) as ts:
        ts.ensure_logged_in()
        for path, receipt in extracted:
            if confirm_each:
                ans = input(f"\n『{path.name}』を入力しますか? [y/N/skip] ").strip().lower()
                if ans not in ("y", "yes"):
                    print("  → スキップしました。")
                    continue
            ts.open_expense_page()
            ts.fill_expense_form(receipt, draft_only=draft_only)
            print(f"  ✓ 入力完了({'下書き保存' if draft_only else '申請'})")

            # 処理済みフォルダへ移動
            processed.mkdir(exist_ok=True)
            shutil.move(str(path), str(processed / path.name))

    print("\n完了しました。TeamSpirit の画面で内容を確認してください。")


if __name__ == "__main__":
    sys.exit(main())
