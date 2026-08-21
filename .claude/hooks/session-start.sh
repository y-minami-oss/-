#!/bin/bash
# SessionStart hook — Claude Code on the web で「検証手段(テスト)」を最初から使える状態にする。
# 検証済みノウハウ:「検証できる手段がないタスクは、まず検証方法を作るところから始める」
#   出典: https://code.claude.com/docs/en/best-practices
set -euo pipefail

# web セッション以外(手元のMac等)では何もしない。ローカルは README の venv 手順に従う。
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# 冪等。playwright のブラウザ本体はダウンロードしない
# (TeamSpirit は社内ログインが必要でクラウドから操作しないため。テストにも不要)
python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore -r requirements.txt
