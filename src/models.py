"""領収書から抽出するデータの構造定義。

Claude の構造化出力(structured outputs)で、この形に沿った JSON を返させます。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Receipt(BaseModel):
    """1枚の領収書から読み取る項目。"""

    date: str = Field(
        description="領収書の日付。ISO 8601 形式 (YYYY-MM-DD)。読み取れない場合は空文字。"
    )
    amount: int = Field(
        description="合計金額(税込)。通貨の最小単位ではなく、表示金額の整数。例: 1500円なら 1500。"
    )
    currency: str = Field(
        default="JPY",
        description="通貨コード (ISO 4217)。日本円なら JPY。",
    )
    vendor: str = Field(
        description="支払先・店名・会社名。例: 'スターバックス 渋谷店'。"
    )
    category: str = Field(
        description="経費科目。提示された候補一覧の中から最も適切なものを1つ選ぶ。"
    )
    description: str = Field(
        description="適用・摘要。何の支払いか簡潔に。例: '打ち合わせ時の飲食代'。"
    )
    tax_amount: int | None = Field(
        default=None,
        description="消費税額。領収書に明記されていれば整数で。なければ null。",
    )
    payment_method: str | None = Field(
        default=None,
        description="支払方法。例: '現金' / 'クレジットカード' / '交通系IC'。不明なら null。",
    )
    confidence: float = Field(
        default=0.0,
        description="読み取り全体の自信度を 0.0〜1.0 で。金額や日付が不鮮明なら低く。",
    )
    notes: str = Field(
        default="",
        description="読み取りで迷った点・人間が確認すべき点があれば書く。なければ空文字。",
    )
