"""UPSIDER 添付機能のテスト(APIキー・ログイン不要)。

- 突き合わせロジック(matcher)
- PDFテキストからの読み取り(text_extract)
- ダミーの明細画面(ローカルHTML)に対するブラウザ操作(Playwright があれば)
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.matcher import (
    Transaction,
    load_transactions_csv,
    name_similarity,
    parse_amount,
    parse_date,
    parse_row_text,
    parse_year_month,
    plan_matches,
)
from src.models import Receipt
from src.text_extract import parse_receipt_text
from src.upsider_attach import months_for_receipts, url_for_month


def receipt(d: str, amount: int, vendor: str = "GO株式会社") -> Receipt:
    return Receipt(date=d, amount=amount, vendor=vendor, category="旅費交通費", description="")


GO_TEXT = """領収書
株式会社トレプロ 様
 ￥3,200-
10%対象小計：¥3,200（うち消費税額¥291）
タクシー利用料金（GO）として、正に領収いたしました。
（GO Pay（クレジットカード ****1005）にてお支払い）
  利用日         2026/07/01(水)
  乗車場所        東京都小金井市本町6丁目
  降車場所        東京都東久留米市滝山1丁目
発行日：2026/11/06 （再発行）
GO株式会社
"""


class ParseTests(unittest.TestCase):
    def test_parse_helpers(self):
        self.assertEqual(parse_year_month("202607"), (2026, 7))
        self.assertEqual(parse_year_month("2026-7"), (2026, 7))
        self.assertEqual(parse_date("2026/07/03"), date(2026, 7, 3))
        self.assertEqual(parse_date("7月3日", default_year=2026), date(2026, 7, 3))
        self.assertEqual(parse_amount("¥3,200"), 3200)
        self.assertEqual(parse_amount("-3,200円"), 3200)
        self.assertEqual(parse_amount("ＪＰＹ 1,000"), 1000)
        self.assertGreater(name_similarity("GO株式会社", "ＧＯ"), 0.9)

    def test_parse_row_text(self):
        tx = parse_row_text(0, "07/01\nGO\n¥3,200\n添付済", (2026, 7), ["添付済"])
        self.assertEqual(tx.date, date(2026, 7, 1))
        self.assertEqual(tx.amount, 3200)
        self.assertEqual(tx.merchant, "GO")
        self.assertTrue(tx.has_receipt)
        self.assertIsNone(parse_row_text(1, "合計", (2026, 7)))

    def test_go_receipt_text(self):
        r = parse_receipt_text(GO_TEXT, ["旅費交通費", "雑費"])
        self.assertEqual(r.date, "2026-07-01")  # 発行日ではなく利用日
        self.assertEqual(r.amount, 3200)
        self.assertEqual(r.tax_amount, 291)
        self.assertEqual(r.vendor, "GO株式会社")
        self.assertIn("小金井市", r.description)

    def test_unknown_issuer_falls_back(self):
        self.assertIsNone(parse_receipt_text("領収書 ¥1,000- 利用日 2026/07/01"))

    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.csv"
            p.write_text("利用日,利用先,利用金額\n2026/07/01,GO,\"3,200\"\n", encoding="cp932")
            txs = load_transactions_csv(p)
        self.assertEqual((txs[0].date, txs[0].amount, txs[0].merchant), (date(2026, 7, 1), 3200, "GO"))

    def test_months_and_url(self):
        ms = months_for_receipts([receipt("2026-07-30", 1), receipt("2026-08-10", 1)], 3)
        self.assertEqual(ms, [(2026, 7), (2026, 8)])
        self.assertEqual(
            url_for_month("https://up-sider.com/user-cards/x/?yearMonth=202607", (2026, 10)),
            "https://up-sider.com/user-cards/x/?yearMonth=202610",
        )


class MatchTests(unittest.TestCase):
    def setUp(self):
        self.txs = [
            Transaction(0, date(2026, 7, 1), 3200, "GO"),
            Transaction(1, date(2026, 7, 2), 3200, "Amazon"),
            Transaction(2, date(2026, 7, 5), 1000, "GO", has_receipt=True),
            Transaction(3, date(2026, 7, 20), 2800, "GO"),
            Transaction(4, date(2026, 7, 20), 2800, "GO"),
            Transaction(5, date(2026, 7, 21), 9999, "ホテル"),
            Transaction(6, date(2026, 7, 21), 9999, "旅館"),
        ]

    def test_single_and_best_name(self):
        res = plan_matches([receipt("2026-07-01", 3200)], self.txs)
        self.assertEqual(res[0].chosen.tx.index, 0)

    def test_skip_already_attached(self):
        res = plan_matches([receipt("2026-07-05", 1000)], self.txs)
        self.assertIsNone(res[0].chosen)
        self.assertEqual(res[0].candidates, [])

    def test_same_day_same_amount_assigned_once_each(self):
        res = plan_matches([receipt("2026-07-20", 2800)] * 3, self.txs)
        self.assertEqual({r.chosen.tx.index for r in res[:2]}, {3, 4})
        self.assertIsNone(res[2].chosen)  # 3枚目は割り当て先なし

    def test_ambiguous_left_to_human(self):
        res = plan_matches([receipt("2026-07-21", 9999, vendor="出張宿泊")], self.txs, 3)
        self.assertIsNone(res[0].chosen)
        self.assertEqual(len(res[0].candidates), 2)

    def test_date_tolerance(self):
        self.assertEqual(plan_matches([receipt("2026-07-10", 3200)], self.txs)[0].candidates, [])


FAKE_PAGE = """<!doctype html><meta charset="utf-8">
<table><tbody>
  <tr><td>2026/07/01</td><td>GO</td><td>¥3,200</td><td class="st"></td></tr>
  <tr><td>2026/07/02</td><td>Amazon</td><td>¥1,500</td><td class="st">添付済</td></tr>
</tbody></table>
<div id="detail" hidden>
  <button id="up">領収書をアップロード</button>
  <input type="file" id="f" hidden>
  <button id="close">閉じる</button>
</div>
<script>
let current = null;
document.querySelectorAll('tbody tr').forEach(tr => tr.onclick = () => {
  current = tr; document.getElementById('detail').hidden = false;
});
document.getElementById('up').onclick = () => document.getElementById('f').click();
document.getElementById('f').onchange = e => {
  current.querySelector('.st').textContent = '添付済 ' + e.target.files[0].name;
  localStorage.setItem('uploaded', e.target.files[0].name);
};
document.getElementById('close').onclick = () => document.getElementById('detail').hidden = true;
</script>"""


class BrowserTests(unittest.TestCase):
    def test_attach_on_fake_page(self):
        try:
            import playwright  # noqa: F401
            from src import upsider
        except ImportError:
            self.skipTest("playwright 未導入")

        with tempfile.TemporaryDirectory() as d:
            page_path = Path(d) / "list.html"
            page_path.write_text(FAKE_PAGE, encoding="utf-8")
            pdf = Path(d) / "r.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%%EOF")
            upsider.PROFILE_DIR = Path(d) / "profile"
            url = page_path.as_uri() + "?yearMonth=202607"
            try:
                client = upsider.UpsiderClient(url, show_browser=False)
                client.__enter__()
            except Exception as e:  # ブラウザ本体が無い環境
                self.skipTest(f"Chromium を起動できません: {e}")
            try:
                txs = client.list_transactions((2026, 7), url)
                self.assertEqual(len(txs), 2)
                self.assertFalse(txs[0].has_receipt)
                self.assertTrue(txs[1].has_receipt)
                client.attach_receipt(txs[0], pdf)
                status = client.page.locator("tbody tr").first.inner_text()
                self.assertIn("r.pdf", status)
                client.close_detail()
                self.assertTrue(client.page.locator("#detail").is_hidden())
            finally:
                client.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
