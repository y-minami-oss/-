"""TeamSpirit(Salesforce基盤)へのブラウザ自動操作。

このモジュールは Playwright で TeamSpirit を開き、経費明細を入力します。

★重要(フェーズ2で完成させる部分):
  経費入力フォームの「どの入力欄に何を入れるか」(セレクタ)は、
  実際の画面を見ないと確定できません。下の `fill_expense_form` 内の
  セレクタは仮置き(TODO)です。Mac で `inspect_form.py` を実行して
  実画面の構造を吸い出し、docs/DOM_MAPPING.md に記録してから埋めます。

設計方針:
  - ログイン状態は storage_state.json に保存し、次回以降は再ログイン不要。
  - 最終「申請」は既定では押さず、下書き保存で止める(安全第一)。
"""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from .models import Receipt

# 経費申請画面の直接URL
EXPENSE_URL = (
    "https://teamspirit-4739.lightning.force.com/lightning/n/"
    "teamspirit__AtkEmpExpTab"
)

# ログインセッションの保存先
STORAGE_STATE = Path("storage_state.json")


class TeamSpiritClient:
    """TeamSpirit を操作するためのラッパ。with 文で使う。"""

    def __init__(self, show_browser: bool = True):
        self.show_browser = show_browser
        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None

    def __enter__(self) -> "TeamSpiritClient":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=not self.show_browser)
        # 保存済みのログイン状態があれば読み込む
        if STORAGE_STATE.exists():
            self._context = self._browser.new_context(
                storage_state=str(STORAGE_STATE)
            )
        else:
            self._context = self._browser.new_context()
        self.page = self._context.new_page()
        return self

    def __exit__(self, *exc) -> None:
        # ログイン状態を保存しておく(次回の再ログインを省く)
        if self._context is not None:
            self._context.storage_state(path=str(STORAGE_STATE))
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()

    # ------------------------------------------------------------------
    # ログイン
    # ------------------------------------------------------------------
    def ensure_logged_in(self) -> None:
        """ログイン済みでなければ ID/パスワードでログインする。"""
        assert self.page is not None
        self.page.goto(EXPENSE_URL, wait_until="domcontentloaded")

        # ログインページに飛ばされたか(URLに login や my.salesforce が含まれる)で判定
        if "login" in self.page.url or self._is_login_page():
            self._do_login()

    def _is_login_page(self) -> bool:
        assert self.page is not None
        # Salesforce 標準ログイン画面には id="username" の入力欄がある
        return self.page.locator("#username").count() > 0

    def _do_login(self) -> None:
        assert self.page is not None
        username = os.environ.get("TS_USERNAME")
        password = os.environ.get("TS_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                "TS_USERNAME / TS_PASSWORD が未設定です。.env を確認してください。"
            )

        # Salesforce 標準ログインフォーム
        self.page.fill("#username", username)
        self.page.fill("#password", password)
        self.page.click("#Login")

        # ログイン後、経費画面に到達するまで待つ
        self.page.wait_for_load_state("networkidle")
        if self._is_login_page():
            raise RuntimeError(
                "ログインに失敗しました。ID/パスワードを確認してください。"
                "(MFAが有効な場合はこの自動ログインは使えません)"
            )

    # ------------------------------------------------------------------
    # 経費入力
    # ------------------------------------------------------------------
    def open_expense_page(self) -> None:
        assert self.page is not None
        self.page.goto(EXPENSE_URL, wait_until="networkidle")

    def fill_expense_form(self, receipt: Receipt, draft_only: bool = True) -> None:
        """経費明細1件を入力する。

        ★★★ ここがフェーズ2で完成させる中核部分 ★★★
        以下のセレクタはすべて仮置きです。実画面を inspect_form.py で調べ、
        正しいセレクタに置き換えてください。TeamSpirit の経費画面は
        iframe(Visualforce)内にある可能性が高いため、その場合は
        `frame = self.page.frame_locator("iframe")` 経由で操作します。
        """
        assert self.page is not None

        raise NotImplementedError(
            "経費フォームの入力は未実装です。\n"
            "フェーズ2で、実画面の構造を inspect_form.py で確認し、\n"
            "docs/DOM_MAPPING.md に基づいてこの関数を実装します。\n\n"
            f"読み取り済みデータ:\n{receipt.model_dump_json(indent=2, exclude_none=True)}"
        )

        # ↓↓↓ フェーズ2で有効化する実装の雛形(セレクタは要差し替え) ↓↓↓
        #
        # frame = self.page.frame_locator("iframe")  # Visualforce iframe の場合
        #
        # # 「新規」ボタンを押す
        # frame.locator("TODO: 新規ボタンのセレクタ").click()
        #
        # # 日付
        # frame.locator("TODO: 日付欄").fill(receipt.date)
        # # 金額
        # frame.locator("TODO: 金額欄").fill(str(receipt.amount))
        # # 科目(プルダウン)
        # frame.locator("TODO: 科目select").select_option(label=receipt.category)
        # # 支払先 / 摘要
        # frame.locator("TODO: 摘要欄").fill(
        #     f"{receipt.vendor} / {receipt.description}"
        # )
        #
        # # 領収書ファイルの添付
        # # frame.locator("TODO: ファイル入力").set_input_files(str(receipt_path))
        #
        # if draft_only:
        #     frame.locator("TODO: 保存(下書き)ボタン").click()
        # else:
        #     frame.locator("TODO: 申請ボタン").click()
