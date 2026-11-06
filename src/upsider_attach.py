"""inbox の領収書を、UPSIDER の該当カード明細に1件ずつ添付する。

使い方(Mac で):
    source .venv/bin/activate
    python -m src.upsider_attach                 # config.yaml の card_url の月を処理
    python -m src.upsider_attach --url "https://up-sider.com/user-cards/<カードID>/?yearMonth=202607"
    python -m src.upsider_attach --dry-run       # 突き合わせ結果を表示するだけ(アップロードしない)
    python -m src.upsider_attach --transactions-csv meisai.csv --dry-run
                                                 # ブラウザを使わず、CSVの明細で突き合わせだけ試す
    python -m src.upsider_attach --inspect       # 画面構造を upsider_dump.txt/html に書き出す

流れ:
  1. 領収書を Claude で読み取る(日付・金額・支払先)
  2. UPSIDER の明細一覧を読み込む(初回は手動ログイン)
  3. 金額一致 + 日付が近い明細を探し、対応表を表示
  4. 1件ずつ確認 → 明細を開いて領収書をアップロード → processed/ へ移動
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

from .config import load_config
from .extract_receipt import extract_receipt, mock_extract
from .matcher import (
    Candidate,
    MatchResult,
    Transaction,
    load_transactions_csv,
    parse_year_month,
    plan_matches,
)
from .models import Receipt
from .run import find_receipts
from .text_extract import extract_from_text


def year_month_from_url(url: str) -> str | None:
    values = parse_qs(urlparse(url).query).get("yearMonth")
    return values[0] if values else None


def url_for_month(url: str, ym: tuple[int, int]) -> str:
    """URL の yearMonth パラメータを差し替える。"""
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query["yearMonth"] = [f"{ym[0]:04d}{ym[1]:02d}"]
    return urlunparse(parts._replace(query=urlencode(query, doseq=True)))


def months_for_receipts(receipts: list[Receipt], tolerance_days: int) -> list[tuple[int, int]]:
    """領収書の日付が含まれる月(+ 月末付近なら翌月)を列挙する。"""
    from datetime import date, timedelta

    months: set[tuple[int, int]] = set()
    for r in receipts:
        try:
            d = date.fromisoformat(r.date)
        except ValueError:
            continue
        for delta in (0, tolerance_days):
            dd = d + timedelta(days=delta)
            months.add((dd.year, dd.month))
    return sorted(months)


def print_plan(
    items: list[tuple[Path, Receipt]], results: list[MatchResult]
) -> None:
    print("\n" + "=" * 70)
    print(" 突き合わせ結果")
    print("=" * 70)
    for res in results:
        path, r = items[res.receipt_index]
        print(f"\n📄 {path.name}")
        print(f"   領収書: {r.date} {r.time or '--:--'}  ¥{r.amount:,}  {r.vendor}")
        if res.chosen:
            print(f"   ✅ → {res.chosen.tx.label()}  ({res.reason})")
        elif res.candidates:
            print(f"   ❓ {res.reason}:")
            for n, c in enumerate(res.candidates, 1):
                print(f"      {n}. {c.tx.label()}")
        else:
            print(f"   ✗ {res.reason}")
    print()


def choose_candidate(res: MatchResult, used: set[int]) -> Candidate | None:
    """候補が複数ある場合に、人に番号で選んでもらう。"""
    cands = [c for c in res.candidates if c.tx.index not in used]
    if not cands:
        return None
    for n, c in enumerate(cands, 1):
        print(f"      {n}. {c.tx.label()}")
    ans = input("   どの明細に添付しますか? 番号 / Enter でスキップ: ").strip()
    if ans.isdigit() and 1 <= int(ans) <= len(cands):
        return cands[int(ans) - 1]
    return None


def main() -> int:
    load_dotenv()
    cfg = load_config()
    up_cfg = cfg.get("upsider", {}) or {}
    behavior = cfg.get("behavior", {})

    parser = argparse.ArgumentParser(description="UPSIDER カード明細に領収書を添付")
    parser.add_argument("files", nargs="*", help="処理する領収書(省略時は inbox 全部)")
    parser.add_argument("--url", default=up_cfg.get("card_url"), help="カード明細一覧のURL")
    parser.add_argument("--year-month", help="対象年月(例: 202607)。省略時はURLから")
    parser.add_argument("--dry-run", action="store_true", help="突き合わせ結果の表示のみ")
    parser.add_argument("--transactions-csv", help="明細をCSVから読む(ブラウザを使わない)")
    parser.add_argument("--mock", action="store_true", help="Claudeを呼ばずダミーデータで読み取る")
    parser.add_argument("--inspect", action="store_true", help="画面構造を書き出して終了")
    parser.add_argument(
        "--only-url-month",
        action="store_true",
        help="URLの月だけ処理する(既定は領収書の日付から必要な月を全部読む)",
    )
    parser.add_argument(
        "--card-last4",
        default=str(up_cfg.get("card_last4") or "") or None,
        help="このカードの末尾4桁(例: 9382)。別カードで払った領収書は除外する",
    )
    parser.add_argument("--yes", action="store_true", help="自動で決まった明細は確認せず添付")
    args = parser.parse_args()

    if not args.transactions_csv and not args.url:
        parser.error(
            "--url を指定するか、config.yaml の upsider.card_url を設定してください。"
        )

    ym_text = args.year_month or (year_month_from_url(args.url) if args.url else None)
    year_month = parse_year_month(ym_text) if ym_text else None
    tolerance = int(up_cfg.get("date_tolerance_days", 3))
    show_browser = behavior.get("show_browser", True)
    confirm_each = behavior.get("confirm_each", True) and not args.yes

    # --inspect: 画面構造を書き出すだけ
    if args.inspect:
        from .upsider import UpsiderClient

        with UpsiderClient(args.url, show_browser=True, selectors=up_cfg.get("selectors")) as up:
            up.ensure_logged_in()
            input("\n調べたい画面(一覧 or 明細詳細)を表示したら Enter を押してください... ")
            txt, html = up.dump()
            print(f"書き出しました: {txt} / {html}")
        return 0

    # 1. 領収書の読み取り
    inbox = Path(cfg["paths"]["inbox"])
    processed = Path(cfg["paths"]["processed"])
    paths = find_receipts(inbox, args.files)
    if not paths:
        print(f"処理対象がありません。{inbox}/ に領収書(画像/PDF)を入れてください。")
        return 0

    extract = mock_extract if args.mock else extract_receipt
    if args.mock:
        print("⚠ モックモード: ダミーデータで読み取ります(Claudeは呼びません)。\n")

    items: list[tuple[Path, Receipt]] = []
    for path in paths:
        print(f"📄 読み取り中: {path.name}")
        try:
            r = None if args.mock else extract_from_text(path, cfg["expense_categories"])
            r = r or extract(path, cfg["expense_categories"])
        except Exception as e:
            print(f"  ✗ 読み取り失敗: {e}")
            continue
        card = f"  ****{r.card_last4}" if r.card_last4 else ""
        print(f"   {r.date} {r.time or '--:--'}  ¥{r.amount:,}  {r.vendor}{card}")
        items.append((path, r))
    if not items:
        return 1

    # 別のカードで支払った領収書は、このカードの明細には出てこないので除外
    other_card: list[tuple[Path, Receipt]] = []
    if args.card_last4:
        other_card = [
            (p, r) for p, r in items if r.card_last4 and r.card_last4 != args.card_last4
        ]
        items = [(p, r) for p, r in items if (p, r) not in other_card]
        if other_card:
            print(f"\n💳 別カードで支払った領収書 {len(other_card)} 件は対象外にします:")
            for p, r in other_card:
                print(f"   - {p.name}  ¥{r.amount:,}  (****{r.card_last4})")
        if not items:
            print("このカード(****%s)の領収書がありません。" % args.card_last4)
            return 0

    # 2. 明細の取得 → 3. 突き合わせ
    if args.transactions_csv:
        txs = load_transactions_csv(args.transactions_csv)
        print(f"\nCSV から明細 {len(txs)} 件を読み込みました。")
        results = plan_matches([r for _, r in items], txs, tolerance)
        print_plan(items, results)
        if not args.dry_run:
            print("CSV モードはアップロードしません(--url で実行してください)。")
        return 0

    from .upsider import UpsiderClient  # Playwright 未導入でも上の処理は動くよう遅延 import

    uploaded: list[str] = []
    skipped: list[str] = []
    with UpsiderClient(
        args.url, show_browser=show_browser, selectors=up_cfg.get("selectors")
    ) as up:
        up.ensure_logged_in()
        if args.only_url_month or year_month is None:
            months = [year_month]
        else:
            months = months_for_receipts([r for _, r in items], tolerance)
        txs = []
        for ym in months:
            url = url_for_month(args.url, ym) if ym else args.url
            month_txs = up.list_transactions(ym, url)
            label = f"{ym[0]}年{ym[1]}月" if ym else "URLの月"
            print(f"   {label}: 明細 {len(month_txs)} 件")
            # 月をまたいでも一意になるよう index を振り直す(画面上の行探しは raw テキストで行う)
            for t in month_txs:
                t.index = len(txs)
                txs.append(t)
        attached = sum(t.has_receipt for t in txs)
        print(f"\n明細 {len(txs)} 件を読み込みました(うち添付済み {attached} 件)。")
        if not txs:
            print("明細が読み取れませんでした。`--inspect` で画面構造を確認してください。")
            return 1

        results = plan_matches([r for _, r in items], txs, tolerance)
        print_plan(items, results)
        if args.dry_run:
            print("--dry-run のため、アップロードせず終了します。")
            return 0

        used = {res.chosen.tx.index for res in results if res.chosen}
        for res in results:
            path, r = items[res.receipt_index]
            print(f"\n📄 {path.name}  (¥{r.amount:,} {r.vendor})")

            target: Transaction | None = None
            if res.chosen:
                target = res.chosen.tx
                print(f"   → {target.label()}")
                if confirm_each:
                    ans = input("   この明細に添付しますか? [y/N] ").strip().lower()
                    if ans not in ("y", "yes"):
                        target = None
            elif res.candidates:
                c = choose_candidate(res, used)
                if c:
                    target = c.tx
                    used.add(target.index)
            else:
                print(f"   ✗ {res.reason}")

            if target is None:
                skipped.append(path.name)
                print("   → スキップしました。")
                continue

            try:
                up.attach_receipt(target, path)
            except Exception as e:
                print(f"   ✗ アップロード失敗: {e}")
                skipped.append(path.name)
                continue
            if not up.verify_attached(target):
                print("   ⚠ アップロード操作はしましたが、一覧で「添付済み」になったことを確認できませんでした。")
                print("     (画面を upsider_fail.png に保存しました。UPSIDER の画面でも確認してください)")
                up._save_failure_snapshot()
                skipped.append(path.name)
                continue
            print("   ✓ アップロードし、一覧で添付済みになったことを確認しました。")

            processed.mkdir(exist_ok=True)
            shutil.move(str(path), str(processed / path.name))
            uploaded.append(path.name)

    print("\n" + "=" * 70)
    print(f" 完了: 添付 {len(uploaded)} 件 / スキップ {len(skipped)} 件")
    if other_card:
        print(f"   (別カードのため対象外: {len(other_card)} 件)")
    for name in skipped:
        print(f"   - 未添付: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
