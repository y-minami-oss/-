"""APIキー無しで動く自動テスト。

Claude APIは「偽クライアント」に差し替えてロジックだけ検証します。
実行:  python -m pytest -q   または  python -m unittest -v
"""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from src import extract_receipt as ex
from src.config import load_config
from src.extract_receipt import (
    _build_content_block,
    extract_receipt,
    mock_extract,
)
from src.models import Receipt
from src.run import find_receipts

# 最小の有効なPNG(1x1 透明)とダミーPDFのバイト列
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"

CATEGORIES = ["旅費交通費", "会議費", "消耗品費", "雑費"]


class FakeMessages:
    """client.messages.parse を模倣する。送られた引数を記録する。"""

    def __init__(self, receipt: Receipt):
        self._receipt = receipt
        self.last_kwargs: dict | None = None

    def parse(self, **kwargs):
        self.last_kwargs = kwargs

        class _Resp:
            parsed_output = self._receipt
            stop_reason = "end_turn"

        return _Resp()


class FakeClient:
    def __init__(self, receipt: Receipt):
        self.messages = FakeMessages(receipt)


class ContentBlockTests(unittest.TestCase):
    def test_png_becomes_image_block(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.png"
            p.write_bytes(PNG_BYTES)
            block = _build_content_block(p)
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["media_type"], "image/png")
        # base64 がデコードして元バイトに戻ること
        self.assertEqual(
            base64.b64decode(block["source"]["data"]), PNG_BYTES
        )

    def test_jpg_media_type(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.JPG"  # 大文字でも判定できること
            p.write_bytes(PNG_BYTES)
            block = _build_content_block(p)
        self.assertEqual(block["source"]["media_type"], "image/jpeg")

    def test_pdf_becomes_document_block(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.pdf"
            p.write_bytes(PDF_BYTES)
            block = _build_content_block(p)
        self.assertEqual(block["type"], "document")
        self.assertEqual(block["source"]["media_type"], "application/pdf")

    def test_unsupported_extension_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.txt"
            p.write_bytes(b"hello")
            with self.assertRaises(ValueError):
                _build_content_block(p)


class ExtractTests(unittest.TestCase):
    def _make_receipt(self) -> Receipt:
        return Receipt(
            date="2026-05-30",
            amount=2300,
            vendor="テスト商店",
            category="会議費",
            description="打合せ",
        )

    def test_extract_passes_through_and_builds_request(self):
        receipt = self._make_receipt()
        client = FakeClient(receipt)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.png"
            p.write_bytes(PNG_BYTES)
            result = extract_receipt(p, CATEGORIES, client=client)

        self.assertEqual(result.amount, 2300)
        kw = client.messages.last_kwargs
        # 正しいモデル・構造化出力指定
        self.assertEqual(kw["model"], ex.MODEL)
        self.assertIs(kw["output_format"], Receipt)
        # システムプロンプトに科目候補が含まれ、キャッシュ指定がある
        sys_text = kw["system"][0]["text"]
        self.assertIn("会議費", sys_text)
        self.assertEqual(kw["system"][0]["cache_control"], {"type": "ephemeral"})
        # ユーザーメッセージに画像ブロックとテキストが入っている
        content = kw["messages"][0]["content"]
        self.assertEqual(content[0]["type"], "image")
        self.assertEqual(content[1]["type"], "text")

    def test_extract_raises_when_parse_returns_none(self):
        client = FakeClient(None)  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.png"
            p.write_bytes(PNG_BYTES)
            with self.assertRaises(RuntimeError):
                extract_receipt(p, CATEGORIES, client=client)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            extract_receipt("does/not/exist.png", CATEGORIES, client=FakeClient(None))  # type: ignore[arg-type]


class MockAndModelTests(unittest.TestCase):
    def test_mock_extract_returns_valid_receipt(self):
        r = mock_extract("inbox/foo.jpg", CATEGORIES)
        self.assertIsInstance(r, Receipt)
        self.assertEqual(r.category, CATEGORIES[0])
        self.assertGreater(r.amount, 0)

    def test_receipt_defaults(self):
        r = Receipt(date="2026-01-01", amount=100, vendor="A", category="雑費", description="x")
        self.assertEqual(r.currency, "JPY")
        self.assertIsNone(r.tax_amount)
        self.assertEqual(r.confidence, 0.0)


class ConfigAndDiscoveryTests(unittest.TestCase):
    def test_config_loads_example(self):
        cfg = load_config()
        self.assertIn("expense_categories", cfg)
        self.assertIn("paths", cfg)
        self.assertTrue(cfg["behavior"]["draft_only"])  # 既定は下書き保存で安全

    def test_find_receipts_filters_by_suffix(self):
        with tempfile.TemporaryDirectory() as d:
            inbox = Path(d)
            (inbox / "a.png").write_bytes(b"x")
            (inbox / "b.pdf").write_bytes(b"x")
            (inbox / "c.txt").write_bytes(b"x")  # 対象外
            (inbox / ".gitkeep").write_bytes(b"")  # 対象外
            found = {p.name for p in find_receipts(inbox, [])}
        self.assertEqual(found, {"a.png", "b.pdf"})

    def test_find_receipts_explicit_files(self):
        found = find_receipts(Path("inbox"), ["x/y.jpg", "z.pdf"])
        self.assertEqual([p.name for p in found], ["y.jpg", "z.pdf"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
