#!/bin/bash
# ダブルクリックで実行: inbox/ の領収書を UPSIDER のカード明細に自動で添付します。
# (初回だけ: Finder で右クリック →「開く」で実行を許可してください)

CARD_URL="https://up-sider.com/user-cards/22a2d767-436b-49a9-9829-1f7805ffc0d1/?yearMonth=202607"
CARD_LAST4="9382"

cd "$(dirname "$0")" || exit 1
echo "▶ 最新版を取得しています..."
git pull -q origin claude/charming-knuth-ldxhzf || echo "  (取得できませんでした。手元の版で続けます)"

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

echo "▶ 実行します。Chrome にログイン画面が出たら、ログインだけしてください。"
python -m src.upsider_attach --url "$CARD_URL" --card-last4 "$CARD_LAST4" --yes

echo
read -n 1 -s -r -p "終わりました。何かキーを押すとこの画面を閉じます。"
