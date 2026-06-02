"""領収書ファイル(画像/PDF)を Claude で読み取り、構造化データにする。

- 画像(JPG/PNG/GIF/WebP): base64 の image ブロックで送信
- PDF: document ブロックで送信(Claude はPDFを直接読める)

使い方(単体テスト):
    python -m src.extract_receipt inbox/sample.jpg
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import anthropic

from .models import Receipt

# スキル(claude-api)の指針に従い、最新かつ最も高性能なモデルを既定にする。
MODEL = "claude-opus-4-8"

# 拡張子 → MIME タイプ
IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _build_system_prompt(categories: list[str]) -> str:
    """科目候補を埋め込んだシステムプロンプトを作る。"""
    cat_list = "\n".join(f"  - {c}" for c in categories)
    return (
        "あなたは日本の経費精算を補助する、領収書読み取りの専門家です。\n"
        "渡された領収書の画像またはPDFから、経費申請に必要な項目を正確に抽出してください。\n"
        "\n"
        "重要な指示:\n"
        "- 金額は税込の合計金額を整数で。3桁区切りのカンマは除く(例: 1,500 → 1500)。\n"
        "- 日付は YYYY-MM-DD 形式に正規化する。和暦は西暦に直す。\n"
        "- 科目(category)は、必ず次の候補の中から最も適切なものを1つ選ぶ:\n"
        f"{cat_list}\n"
        "- 判断に迷う、または文字が不鮮明で読み取れない場合は、推測で埋めず\n"
        "  notes にその旨を書き、confidence を低めにする。\n"
        "- 領収書に無い情報は捏造しない。"
    )


def _build_content_block(file_path: Path) -> dict:
    """ファイルの種類に応じて image / document ブロックを作る。"""
    suffix = file_path.suffix.lower()
    data = base64.standard_b64encode(file_path.read_bytes()).decode("utf-8")

    if suffix == ".pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": data,
            },
        }

    media_type = IMAGE_MEDIA_TYPES.get(suffix)
    if media_type is None:
        raise ValueError(
            f"対応していないファイル形式です: {suffix} "
            f"(対応: {', '.join(IMAGE_MEDIA_TYPES)} と .pdf)"
        )
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        },
    }


def extract_receipt(
    file_path: str | Path,
    categories: list[str],
    client: anthropic.Anthropic | None = None,
) -> Receipt:
    """領収書ファイル1件を読み取って Receipt を返す。"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    client = client or anthropic.Anthropic()
    system_prompt = _build_system_prompt(categories)

    response = client.messages.parse(
        model=MODEL,
        max_tokens=2000,
        # システムプロンプトはファイル間で共通なのでキャッシュ対象にしておく。
        # (短い場合はキャッシュ最小サイズ未満で効かないこともあるが、害はない)
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    _build_content_block(file_path),
                    {
                        "type": "text",
                        "text": "この領収書から経費申請用の項目を抽出してください。",
                    },
                ],
            }
        ],
        output_format=Receipt,
    )

    receipt = response.parsed_output
    if receipt is None:
        raise RuntimeError(
            f"領収書の読み取りに失敗しました(stop_reason={response.stop_reason})。"
            f"画像が不鮮明か、安全上の理由で拒否された可能性があります。"
        )
    return receipt


if __name__ == "__main__":
    # 単体動作確認用: python -m src.extract_receipt <ファイル>
    if len(sys.argv) < 2:
        print("使い方: python -m src.extract_receipt <領収書ファイル>")
        sys.exit(1)

    # サンプルの科目候補(本番は config.yaml から渡す)
    demo_categories = ["旅費交通費", "会議費", "接待交際費", "消耗品費", "通信費", "雑費"]
    result = extract_receipt(sys.argv[1], demo_categories)
    print(result.model_dump_json(indent=2, exclude_none=False))
