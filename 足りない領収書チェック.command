#!/bin/bash
# ダブルクリックで実行: アップロードはせず、「領収書が足りない明細」の一覧だけを出します。
CARD_URL="https://up-sider.com/user-cards/22a2d767-436b-49a9-9829-1f7805ffc0d1/?yearMonth=202607"
CARD_LAST4="9382"

cd "$(dirname "$0")" || exit 1
git pull -q origin claude/charming-knuth-ldxhzf || true
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

python -m src.upsider_attach --url "$CARD_URL" --card-last4 "$CARD_LAST4" --yes --dry-run
open "領収書が足りない明細.csv" 2>/dev/null

echo
read -n 1 -s -r -p "終わりました。何かキーを押すとこの画面を閉じます。"
