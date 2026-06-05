"""Google スプレッドシートへの接続(ライブ取得)。

gspread + OAuth を使う。初回だけブラウザ認証が走り、token.json に
セッションが保存される(2回目以降は自動)。読み取り専用スコープ。

必要ファイル(.gitignore 済み):
  - credentials.json … Google Cloud で発行した OAuth クライアント
  - token.json       … 初回認証後に自動生成される
詳しい取得手順は docs/PROJECT_SHEET.md を参照。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_client(credentials_path: str = "credentials.json", token_path: str = "token.json") -> Any:
    """認証済みの gspread クライアントを返す。"""
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    token = Path(token_path)
    if token.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_path).exists():
                raise FileNotFoundError(
                    f"{credentials_path} がありません。"
                    " docs/PROJECT_SHEET.md の手順で OAuth クライアントを作成してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json(), encoding="utf-8")
    return gspread.authorize(creds)


def find_spreadsheet_id_by_title(client: Any, keyword: str) -> str | None:
    """タイトルに keyword を含むスプレッドシートを1件探して ID を返す。"""
    files = client.list_spreadsheet_files()
    for f in files:
        if keyword in f.get("name", ""):
            return f.get("id")
    return None
