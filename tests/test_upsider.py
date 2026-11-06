"""UPSIDER 添付機能のテスト(APIキー・ログイン不要)。

- 突き合わせロジック(matcher)
- PDFテキストからの読み取り(text_extract)
- ダミーの明細画面(ローカルHTML)に対するブラウザ操作(Playwright があれば)
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, time
from pathlib import Path

from src.matcher import (
    Transaction,
    load_transactions_csv,
    name_similarity,
    parse_amount,
    parse_date,
    parse_row_text,
    parse_time,
    parse_year_month,
    plan_matches,
)
from src.models import Receipt
from src.text_extract import parse_receipt_text
from src.upsider_attach import months_for_receipts, url_for_month


def receipt(d: str, amount: int, vendor: str = "GO株式会社", t: str | None = None) -> Receipt:
    return Receipt(
        date=d, time=t, amount=amount, vendor=vendor, category="旅費交通費", description=""
    )


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
        self.assertEqual(r.card_last4, "1005")

    def test_time_from_filename(self):
        r = parse_receipt_text(GO_TEXT, filename="GO領収書_20260701_1338.pdf")
        self.assertEqual(r.time, "13:38")
        # ファイル名の日付が利用日と違う場合は時刻を採用しない
        r = parse_receipt_text(GO_TEXT, filename="GO領収書_20260702_1338.pdf")
        self.assertIsNone(r.time)

    def test_time_parsing(self):
        self.assertEqual(parse_time("2026/07/01 13:38"), time(13, 38))
        self.assertEqual(parse_time("9時05分"), time(9, 5))
        self.assertEqual(parse_time("9月3日 15時3分"), time(15, 3))  # UPSIDER は分が1桁のことがある
        self.assertIsNone(parse_time("¥3,200"))
        tx = parse_row_text(0, "07/01 13:40\nGO\n¥3,200", (2026, 7))
        self.assertEqual((tx.time, tx.merchant), (time(13, 40), "GO"))

    def test_unknown_issuer_falls_back(self):
        self.assertIsNone(parse_receipt_text("領収書 ¥1,000- 利用日 2026/07/01"))

    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.csv"
            p.write_text(
                "利用日,利用先,利用金額\n2026/07/01 13:40,GO,\"3,200\"\n", encoding="cp932"
            )
            txs = load_transactions_csv(p)
        self.assertEqual(
            (txs[0].date, txs[0].time, txs[0].amount, txs[0].merchant),
            (date(2026, 7, 1), time(13, 40), 3200, "GO"),
        )

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

    def test_time_picks_right_ride_on_same_day(self):
        # 同日・同額のタクシー3回を、時刻で正しく振り分ける
        txs = [
            Transaction(0, date(2026, 10, 20), 2800, "GO", time=time(20, 58)),
            Transaction(1, date(2026, 10, 20), 2800, "GO", time=time(14, 36)),
            Transaction(2, date(2026, 10, 20), 2800, "GO", time=time(17, 41)),
        ]
        rs = [receipt("2026-10-20", 2800, t=t) for t in ("14:33", "17:38", "20:55")]
        res = plan_matches(rs, txs)
        self.assertEqual([r.chosen.tx.index for r in res], [1, 2, 0])

    def test_time_near_midnight_crosses_date(self):
        txs = [
            Transaction(0, date(2026, 7, 2), 3000, "GO", time=time(0, 10)),
            Transaction(1, date(2026, 7, 1), 3000, "GO", time=time(9, 0)),
        ]
        res = plan_matches([receipt("2026-07-01", 3000, t="23:55")], txs)
        self.assertEqual(res[0].chosen.tx.index, 0)

    def test_different_times_far_apart_go_to_human(self):
        txs = [
            Transaction(0, date(2026, 7, 1), 3000, "GO", time=time(8, 0)),
            Transaction(1, date(2026, 7, 1), 3000, "GO", time=time(20, 0)),
        ]
        res = plan_matches([receipt("2026-07-01", 3000, t="14:00")], txs)
        self.assertIsNone(res[0].chosen)

    def test_date_tolerance(self):
        self.assertEqual(plan_matches([receipt("2026-07-10", 3200)], self.txs)[0].candidates, [])


# UPSIDER の画面(利用履歴の一覧 → 明細詳細ページ)を模したダミー
FAKE_LIST = """<!doctype html><meta charset="utf-8">
<h2>利用履歴 <span>2026年07月</span></h2><div>計 ￥86,810</div><div>11 件</div>
<div class="list">
  <a class="card" href="detail.html?id=a"><div>申請ID：+</div>
    <div><span>7月28日 19時59分</span><span>📄 <b>なし</b></span></div>
    <div><span>GO(TAXI APP)</span><span>￥4,400</span></div></a>
  <a class="card" href="detail.html?id=b"><div>申請ID：+</div>
    <div><span>7月28日 2時40分</span><span>📄 <b>1</b></span></div>
    <div><span>ｴ-ｴﾇｴ-ｳｴﾌﾞ (ANA WEB)</span><span>￥11,680</span></div></a>
</div>
<script>
for (const b of document.querySelectorAll('b'))
  if (b.textContent === 'なし' && localStorage.getItem('up_a')) b.textContent = '1';
</script>"""

FAKE_DETAIL = """<!doctype html><meta charset="utf-8">
<h2>ｺﾞ-(ﾀｸｼ-ｱﾌﾟﾘ) (GO(TAXI APP))</h2><div>2026年07月28日 19時59分 ￥4,400</div>
<div>証憑</div><button id="up">ファイルをアップロード</button>
<input type="file" id="f" style="display:none"><div id="files"></div>
<script>
document.getElementById('up').onclick = () => document.getElementById('f').click();
document.getElementById('f').onchange = e => {
  document.getElementById('files').textContent = e.target.files[0].name;
  localStorage.setItem('up_a', e.target.files[0].name);
};
</script>"""


class BrowserTests(unittest.TestCase):
    def test_attach_on_fake_page(self):
        try:
            import playwright  # noqa: F401
            from src import upsider
        except ImportError:
            self.skipTest("playwright 未導入")

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "list.html").write_text(FAKE_LIST, encoding="utf-8")
            (Path(d) / "detail.html").write_text(FAKE_DETAIL, encoding="utf-8")
            pdf = Path(d) / "r.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%%EOF")
            upsider.PROFILE_DIR = Path(d) / "profile"
            url = (Path(d) / "list.html").as_uri() + "?yearMonth=202607"
            try:
                client = upsider.UpsiderClient(url, show_browser=False)
                client.__enter__()
            except Exception as e:  # ブラウザ本体が無い環境
                self.skipTest(f"Chromium を起動できません: {e}")
            try:
                txs = client.list_transactions((2026, 7), url)
                self.assertEqual(len(txs), 2)  # 見出しの「計 ￥86,810」は行に含めない
                go, ana = txs
                self.assertEqual((go.date, go.time, go.amount), (date(2026, 7, 28), time(19, 59), 4400))
                self.assertEqual(go.merchant, "GO(TAXI APP)")
                self.assertFalse(go.has_receipt)  # 📄 なし
                self.assertTrue(ana.has_receipt)  # 📄 1
                res = plan_matches([receipt("2026-07-28", 4400, t="19:42")], txs)
                self.assertIs(res[0].chosen.tx, go)

                client.attach_receipt(go, pdf)
                self.assertIn("detail.html", client.page.url)
                self.assertEqual(client.page.locator("#files").inner_text(), "r.pdf")
                client.close_detail()
                self.assertIn("list.html", client.page.url)
                # 一覧に戻ると添付済みになっている
                after = client.list_transactions((2026, 7), url)
                self.assertTrue(after[0].has_receipt)
            finally:
                client.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()


class ChromeLoginTests(unittest.TestCase):
    def _profile(self, root: Path, name: str, hosts: list[str]) -> None:
        import sqlite3

        prof = root / name / "Network"
        prof.mkdir(parents=True)
        con = sqlite3.connect(prof / "Cookies")
        con.execute("CREATE TABLE cookies (host_key TEXT, name TEXT, value TEXT)")
        con.executemany("INSERT INTO cookies VALUES (?, 'k', 'v')", [(h,) for h in hosts])
        con.commit()
        con.close()
        (root / name / "Local Storage" / "leveldb").mkdir(parents=True)
        (root / name / "Local Storage" / "leveldb" / "000003.log").write_text("x")
        (root / name / "Local Storage" / "leveldb" / "LOCK").write_text("")

    def test_picks_profile_with_upsider_cookie_and_copies(self):
        from src.chrome_login import find_profile_with_login, import_login

        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "chrome", Path(d) / "dst"
            self._profile(src, "Default", ["google.com"])
            self._profile(src, "Profile 1", [".up-sider.com", "up-sider.com"])
            self.assertEqual(find_profile_with_login(src).name, "Profile 1")
            self.assertEqual(import_login(dst, src), "Profile 1")
            self.assertTrue((dst / "Default/Network/Cookies").exists())
            self.assertTrue((dst / "Default/Local Storage/leveldb/000003.log").exists())
            self.assertFalse((dst / "Default/Local Storage/leveldb/LOCK").exists())

    def test_no_login_found(self):
        from src.chrome_login import import_login

        with tempfile.TemporaryDirectory() as d:
            self._profile(Path(d) / "chrome", "Default", ["google.com"])
            self.assertIsNone(import_login(Path(d) / "dst", Path(d) / "chrome"))


# 実画面に近い詳細ページ: 2秒遅れて描画 / タイルは div / input はクリック時に動的生成
FAKE_DETAIL_SLOW = """<!doctype html><meta charset="utf-8"><div id="root"></div>
<script>
setTimeout(() => {
  document.getElementById('root').innerHTML =
    '<h3>証憑</h3><div class="tile" id="tile"><span>ファイルをアップ</span><span>ロード</span></div>' +
    '<div id="files"></div>';
  document.getElementById('tile').onclick = () => {
    const inp = document.createElement('input');
    inp.type = 'file';
    inp.onchange = e => {
      document.getElementById('files').textContent = e.target.files[0].name;
      setTimeout(() => localStorage.setItem('up_a', e.target.files[0].name), 1500);
    };
    inp.click();
  };
}, 2000);
</script>"""


class SlowDetailBrowserTests(unittest.TestCase):
    def test_upload_via_tile_and_verify(self):
        try:
            from src import upsider
        except ImportError:
            self.skipTest("playwright 未導入")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "list.html").write_text(FAKE_LIST, encoding="utf-8")
            (Path(d) / "detail.html").write_text(FAKE_DETAIL_SLOW, encoding="utf-8")
            pdf = Path(d) / "r.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%%EOF")
            upsider.PROFILE_DIR = Path(d) / "profile"
            url = (Path(d) / "list.html").as_uri() + "?yearMonth=202607"
            try:
                client = upsider.UpsiderClient(url, show_browser=False)
                client.__enter__()
            except Exception as e:
                self.skipTest(f"Chromium を起動できません: {e}")
            try:
                go = client.list_transactions((2026, 7), url)[0]
                self.assertFalse(go.has_receipt)
                client.attach_receipt(go, pdf)
                self.assertEqual(client.page.locator("#files").inner_text(), "r.pdf")
                self.assertTrue(client.verify_attached(go))
            finally:
                client.__exit__(None, None, None)
