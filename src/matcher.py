"""領収書と UPSIDER のカード明細を突き合わせるロジック。

ブラウザ操作から切り離してあるので、APIキーやログイン無しでテストできます。

突き合わせの考え方:
  1. 金額が一致すること(必須)
  2. 日付の差が許容日数以内であること(カードの計上日は数日ずれることがある)
  3. 候補が複数あれば、日付の近さ + 支払先名の似ている度合いで順位づけ
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from .models import Receipt


@dataclass
class Transaction:
    """UPSIDER のカード明細1件。"""

    index: int  # 一覧での並び順(0始まり)
    date: date | None
    amount: int
    merchant: str
    has_receipt: bool = False
    raw: str = ""  # 一覧の行テキスト(画面上で同じ行を探し直すのに使う)
    source_url: str = ""  # この明細が載っている一覧ページのURL(月ごと)

    def label(self) -> str:
        d = self.date.isoformat() if self.date else "????-??-??"
        mark = " [添付済]" if self.has_receipt else ""
        return f"{d}  ¥{self.amount:>9,}  {self.merchant}{mark}"


@dataclass
class Candidate:
    tx: Transaction
    day_diff: int
    name_score: float  # 0.0〜1.0

    @property
    def score(self) -> float:
        # 日付差1日ごとに減点、支払先が似ていれば加点
        return self.name_score * 2.0 - self.day_diff * 0.5


@dataclass
class MatchResult:
    receipt_index: int
    candidates: list[Candidate] = field(default_factory=list)
    chosen: Candidate | None = None  # 自動で1件に決まった場合
    reason: str = ""


# ----------------------------------------------------------------------
# 文字列の正規化・解析
# ----------------------------------------------------------------------
def normalize(text: str) -> str:
    """全角/半角・大文字小文字・記号の差を吸収した比較用文字列。"""
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"(株式会社|\(株\)|有限会社|合同会社|inc\.?|co\.,?\s*ltd\.?|llc)", "", t)
    return re.sub(r"[\s\-_・/.,'\"()*]", "", t)


def name_similarity(a: str, b: str) -> float:
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def parse_year_month(value: str) -> tuple[int, int]:
    """'202607' / '2026-07' / '2026/7' → (2026, 7)"""
    m = re.fullmatch(r"(\d{4})[-/]?(\d{1,2})", value.strip())
    if not m:
        raise ValueError(f"年月の形式が不正です: {value!r}(例: 202607)")
    return int(m.group(1)), int(m.group(2))


def parse_date(text: str, default_year: int | None = None) -> date | None:
    t = unicodedata.normalize("NFKC", text)
    m = re.search(r"(\d{4})\s*[/\-.年]\s*(\d{1,2})\s*[/\-.月]\s*(\d{1,2})", t)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.search(r"(?<!\d)(\d{1,2})\s*[/月]\s*(\d{1,2})(?!\d)", t)
        if not m or default_year is None:
            return None
        y, (mo, d) = default_year, map(int, m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


_AMOUNT_PATTERNS = [
    re.compile(r"[¥￥]\s*(-?[\d,]+)"),
    re.compile(r"(-?[\d,]+)\s*円"),
    re.compile(r"JPY\s*(-?[\d,]+)", re.I),
]


def parse_amount(text: str) -> int | None:
    t = unicodedata.normalize("NFKC", text)
    for pat in _AMOUNT_PATTERNS:
        m = pat.search(t)
        if m:
            digits = m.group(1).replace(",", "")
            if digits.lstrip("-").isdigit():
                return abs(int(digits))
    return None


def parse_row_text(
    index: int,
    text: str,
    year_month: tuple[int, int] | None = None,
    receipt_attached_keywords: list[str] | None = None,
) -> Transaction | None:
    """一覧の1行分のテキストから明細を組み立てる。日付か金額が無ければ None。"""
    year = year_month[0] if year_month else None
    d = parse_date(text, default_year=year)
    amount = parse_amount(text)
    if d is None or amount is None:
        return None

    # 日付・金額・ステータスっぽい行を除いた一番長い行を「利用先」とみなす
    keywords = receipt_attached_keywords or []
    has_receipt = any(k and k in text for k in keywords)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    merchant_lines = [
        ln
        for ln in lines
        if parse_date(ln, default_year=year) is None
        and parse_amount(ln) is None
        and not re.fullmatch(r"[\d,.\s:/\-¥￥円]+", ln)
        and not any(k and k in ln for k in keywords)
    ]
    merchant = max(merchant_lines, key=len) if merchant_lines else ""
    return Transaction(index, d, amount, merchant, has_receipt, raw=text)


# ----------------------------------------------------------------------
# CSV(UPSIDER の明細エクスポート)から読み込み
# ----------------------------------------------------------------------
_CSV_COLUMNS = {
    "date": ["利用日", "日付", "決済日", "取引日", "date"],
    "amount": ["利用金額", "金額", "決済金額", "請求金額", "amount"],
    "merchant": ["利用先", "加盟店", "加盟店名", "店舗名", "摘要", "merchant", "description"],
}


def _pick(row: dict[str, str], keys: list[str]) -> str:
    for k in keys:
        for col, val in row.items():
            if col and col.strip().lower() == k.lower():
                return val or ""
    return ""


def load_transactions_csv(path: str | Path) -> list[Transaction]:
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp932"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"CSVの文字コードを判別できません: {path}")

    txs: list[Transaction] = []
    for i, row in enumerate(csv.DictReader(text.splitlines())):
        d = parse_date(_pick(row, _CSV_COLUMNS["date"]))
        amt_text = _pick(row, _CSV_COLUMNS["amount"]).replace(",", "").strip()
        amt_text = re.sub(r"[¥￥円\s]", "", amt_text)
        if d is None or not amt_text.lstrip("-").isdigit():
            continue
        merchant = _pick(row, _CSV_COLUMNS["merchant"])
        txs.append(Transaction(i, d, abs(int(amt_text)), merchant, raw=merchant))
    return txs


# ----------------------------------------------------------------------
# 突き合わせ
# ----------------------------------------------------------------------
def _receipt_date(receipt: Receipt) -> date | None:
    return parse_date(receipt.date) if receipt.date else None


def find_candidates(
    receipt: Receipt,
    transactions: list[Transaction],
    date_tolerance_days: int = 3,
    exclude: set[int] | None = None,
) -> list[Candidate]:
    exclude = exclude or set()
    r_date = _receipt_date(receipt)
    out: list[Candidate] = []
    for tx in transactions:
        if tx.index in exclude or tx.has_receipt or tx.amount != receipt.amount:
            continue
        if r_date and tx.date:
            diff = abs((tx.date - r_date).days)
            if diff > date_tolerance_days:
                continue
        else:
            diff = date_tolerance_days  # 日付不明なら最も遠い扱い
        out.append(Candidate(tx, diff, name_similarity(receipt.vendor, tx.merchant)))
    out.sort(key=lambda c: c.score, reverse=True)
    return out


def _interchangeable(a: Candidate, b: Candidate) -> bool:
    return (
        a.tx.date == b.tx.date
        and a.tx.amount == b.tx.amount
        and normalize(a.tx.merchant) == normalize(b.tx.merchant)
    )


def plan_matches(
    receipts: list[Receipt],
    transactions: list[Transaction],
    date_tolerance_days: int = 3,
) -> list[MatchResult]:
    """各領収書に対応する明細を決める。

    全体を見て「一番確からしい組み合わせ」から順に確定させていきます
    (同じ金額の乗車が続く日でも、日付が近いもの同士がペアになる)。
    - 1位の候補が2位より明確に良い(日付が1日以上近い/支払先がより似ている)→ 自動決定
    - 同日・同額・同じ支払先で区別がつかない → どれでも同じなので自動決定
    - それ以外 → chosen=None(人に選んでもらう)
    """
    results = [MatchResult(i) for i in range(len(receipts))]
    used: set[int] = set()
    pending = set(range(len(receipts)))
    ambiguous: set[int] = set()

    while True:
        best: tuple[float, int, list[Candidate]] | None = None
        for i in pending - ambiguous:
            cands = find_candidates(receipts[i], transactions, date_tolerance_days, used)
            if not cands:
                continue
            if best is None or cands[0].score > best[0]:
                best = (cands[0].score, i, cands)
        if best is None:
            break
        _, i, cands = best
        res = results[i]
        if len(cands) == 1:
            res.reason = "金額・日付が一致"
        elif cands[0].score - cands[1].score >= 0.5:
            res.reason = "候補複数のうち日付・支払先が最も近い"
        elif _interchangeable(cands[0], cands[1]):
            # 例: 同日に同額のタクシー2回。どれに付けても内容は同じ。
            res.reason = "同日・同額・同じ支払先の明細から順に割り当て"
        else:
            ambiguous.add(i)
            continue
        res.chosen, res.candidates = cands[0], cands
        used.add(cands[0].tx.index)
        pending.discard(i)

    for i in pending:
        res = results[i]
        res.candidates = find_candidates(receipts[i], transactions, date_tolerance_days, used)
        if not res.candidates:
            res.reason = "金額・日付が一致する明細がありません"
        else:
            res.reason = f"候補が{len(res.candidates)}件あり自動で決められません"
    return results
