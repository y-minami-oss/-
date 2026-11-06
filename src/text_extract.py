"""文字情報を持つPDF領収書を、Claude を使わずに読み取る。

GO(タクシー)などの電子領収書は PDF に文字が埋め込まれているので、
テキストを取り出して正規表現で日付・金額・発行元を拾えば十分です。
読み取れなかった場合は None を返し、呼び出し側で Claude 読み取りにフォールバックします。
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .models import Receipt


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader  # 遅延 import

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# 既知の発行元: (テキスト中の目印, 支払先名, 科目, 摘要)
KNOWN_ISSUERS = [
    ("GO株式会社", "GO株式会社", "旅費交通費", "タクシー利用料金(GO)"),
]

_DATE = r"(\d{4})\s*[/\-年]\s*(\d{1,2})\s*[/\-月]\s*(\d{1,2})"


def parse_receipt_text(text: str, categories: list[str] | None = None) -> Receipt | None:
    t = unicodedata.normalize("NFKC", text)

    # 金額: 「¥3,200-」の形(領収書の大きな金額表示)→ 無ければ「合計 ¥…」
    m = re.search(r"¥\s*([\d,]+)\s*-", t) or re.search(
        r"(?:合計|総額|ご請求額|領収金額)[^\d¥]*¥?\s*([\d,]+)", t
    )
    if not m:
        return None
    amount = int(m.group(1).replace(",", ""))

    # 日付: 「利用日」「ご利用日」を優先。発行日(再発行日)は使わない。
    m = re.search(r"(?:ご?利用日|乗車日|取引日|お支払日)\s*:?\s*" + _DATE, t)
    if not m:
        candidates = [
            mm for mm in re.finditer(_DATE, t)
            if "発行日" not in t[max(0, mm.start() - 8): mm.start()]
        ]
        if not candidates:
            return None
        m = candidates[0]
    y, mo, d = (int(x) for x in m.groups()[-3:])
    date = f"{y:04d}-{mo:02d}-{d:02d}"

    issuer = next((k for k in KNOWN_ISSUERS if k[0] in t), None)
    if issuer is None:
        return None  # 発行元が分からないものは Claude に任せる
    _, vendor, category, description = issuer
    if categories and category not in categories:
        category = categories[0]

    tax = re.search(r"消費税額?\s*¥?\s*([\d,]+)", t)
    route = re.search(r"乗車場所\s*(\S+).*?降車場所\s*(\S+)", t, re.S)
    if route:
        description += f" {route.group(1)}→{route.group(2)}"

    return Receipt(
        date=date,
        amount=amount,
        currency="JPY",
        vendor=vendor,
        category=category,
        description=description,
        tax_amount=int(tax.group(1).replace(",", "")) if tax else None,
        payment_method="クレジットカード" if "クレジットカード" in t else None,
        confidence=0.95,
        notes="PDFのテキストから読み取り",
    )


def extract_from_text(path: str | Path, categories: list[str]) -> Receipt | None:
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        return None
    try:
        return parse_receipt_text(pdf_text(path), categories)
    except Exception:
        return None
