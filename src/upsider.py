"""UPSIDER(カード明細画面)へのブラウザ自動操作。

ログインは自動化しません。初回はブラウザが開いたら手動でログインしてください
(2段階認証もそのまま通せます)。ログイン状態は .auth/upsider/ に保存され、
次回以降はログイン済みで開きます。

画面の要素(セレクタ)は config.yaml の `upsider.selectors` で上書きできます。
UPSIDER の画面が変わって動かなくなったら、`--inspect` で画面構造を書き出し、
セレクタを調整してください。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright

from .matcher import Transaction, parse_row_text

PROFILE_DIR = Path(".auth/upsider")
CDP_PROFILE_DIR = Path(".auth/upsider-chrome")
CDP_PORT = 9223

MAC_CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]


def find_mac_chrome() -> str | None:
    if sys.platform != "darwin":
        return None
    return next((p for p in MAC_CHROME_PATHS if Path(p).exists()), None)

DEFAULT_SELECTORS: dict[str, Any] = {
    # 明細一覧の1行。上から順に試し、見つかったものを使う。
    # "auto" = 「日付(7月28日 など)と金額(¥)を1つずつ含む最小の要素」を行とみなす。
    # UPSIDER の利用履歴はカード型の一覧なので、これで拾える。
    "row": [
        "auto",
        "table tbody tr",
        "[role='row']:has([role='cell'])",
        "[data-testid*='transaction']",
        "li:has-text('¥')",
    ],
    # 明細詳細で、領収書アップロードを開くボタン(ファイル入力が隠れている場合)
    "upload_button_text": r"領収書|証憑|アップロード|添付|ファイルを選択",
    # 一覧の行テキストにこれが含まれていれば「添付済み」とみなしてスキップ
    "receipt_attached_keywords": ["添付済", "領収書あり", "提出済"],
    # 行の中にこの文字だけの行があれば「領収書が未添付」(UPSIDER は 📄 なし と表示)。
    # これが無い行は添付済みとみなす。
    "receipt_missing_keywords": ["なし"],
    # 詳細を閉じるボタン(無ければ Escape キー → 一覧URLへ戻る)
    "close_button_text": r"^(閉じる|×|✕)$",
}


AUTO_ROW_ATTR = "data-claude-row"

_MARK_ROWS_JS = """
(attr) => {
  document.querySelectorAll('[' + attr + ']').forEach(e => e.removeAttribute(attr));
  const dateRe = /\\d{1,2}月\\d{1,2}日|\\d{4}[\\/\\-.]\\d{1,2}[\\/\\-.]\\d{1,2}/g;
  const amtRe = /[¥￥]\\s*[\\d,]+/;
  const ok = el => {
    const t = el.textContent || '';
    if (!amtRe.test(t)) return false;
    const m = t.match(dateRe);
    return m && m.length === 1;
  };
  const all = [...document.querySelectorAll('body *')].filter(ok);
  const set = new Set(all);
  // 子孫に条件を満たす要素を持たない「最小」の要素 = 明細1件
  const rows = all.filter(el => ![...el.querySelectorAll('*')].some(c => set.has(c)))
                  .filter(el => el.getClientRects().length > 0);
  rows.forEach((el, i) => el.setAttribute(attr, String(i)));
  return rows.length;
}
"""


class UpsiderClient:
    """UPSIDER を操作するラッパ。with 文で使う。"""

    def __init__(
        self,
        list_url: str,
        show_browser: bool = True,
        selectors: dict[str, Any] | None = None,
        import_login: bool = True,
    ):
        self.import_login = import_login
        self.list_url = list_url
        self.show_browser = show_browser
        self.sel = {**DEFAULT_SELECTORS, **(selectors or {})}
        self._pw = None
        self._context = None
        self.page: Page | None = None
        self._row_selector: str | None = None

    def __enter__(self) -> "UpsiderClient":
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._chrome_proc = None
        self._browser = None
        # Mac に Google Chrome があれば「普通の Chrome」を起動し、ログイン後に接続する方式。
        # 自動操作用ブラウザだとログイン時の「Verify you are human」で止まることがあるため。
        chrome = None if os.environ.get("UPSIDER_NO_CDP") else find_mac_chrome()
        if chrome:
            self._start_normal_chrome(chrome)
            return self
        # 永続プロファイル: ログイン状態(Cookie等)がフォルダに残る
        self._context = self._launch()
        self.page = (
            self._context.pages[0] if self._context.pages else self._context.new_page()
        )
        return self

    # ------------------------------------------------------------------
    # 普通の Chrome を起動 → ログイン後に接続(Mac)
    # ------------------------------------------------------------------
    def _cdp_alive(self) -> bool:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1
            ) as r:
                json.load(r)
            return True
        except Exception:
            return False

    def _start_normal_chrome(self, chrome: str) -> None:
        CDP_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        if not self._cdp_alive():
            if self.import_login:
                from .chrome_login import import_login

                try:
                    name = import_login(CDP_PROFILE_DIR)
                except Exception as e:
                    name = None
                    print(f"⚠ 普段の Chrome のログイン状態をコピーできませんでした: {e}")
                if name:
                    print(f"🔑 普段の Chrome(プロファイル『{name}』)の UPSIDER ログイン状態を使います。")
                else:
                    print("⚠ 普段の Chrome に UPSIDER のログイン状態が見つかりませんでした。")
            self._chrome_proc = subprocess.Popen(
                [
                    chrome,
                    f"--remote-debugging-port={CDP_PORT}",
                    f"--user-data-dir={CDP_PROFILE_DIR.resolve()}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    self.list_url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(40):
                if self._cdp_alive():
                    break
                time.sleep(0.5)
        self._cdp_pending = True

    def _connect_cdp(self) -> None:
        assert self._pw is not None
        if not self._cdp_alive():
            raise RuntimeError(
                "Chrome が閉じられたようです。Chrome のウィンドウは最後まで閉じずに、"
                "もう一度実行し直してください。"
            )
        self._browser = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        self._context = self._browser.contexts[0]
        pages = [p for p in self._context.pages if "up-sider.com" in p.url]
        self.page = pages[0] if pages else (
            self._context.pages[0] if self._context.pages else self._context.new_page()
        )
        self._cdp_pending = False

    def _launch(self):
        """ブラウザを起動する。

        1. 環境変数 CHROMIUM_PATH があればそれを使う
        2. Mac/PC に入っている Google Chrome(channel="chrome")を使う
           → 追加ダウンロード不要で、ログイン時の Cloudflare の確認も通りやすい
        3. 無ければ Playwright 同梱の Chromium(`playwright install chromium` が必要)
        """
        assert self._pw is not None
        common = dict(
            headless=not self.show_browser,
            locale="ja-JP",
            viewport={"width": 1400, "height": 900},
        )
        path = os.environ.get("CHROMIUM_PATH")
        if path:
            return self._pw.chromium.launch_persistent_context(
                str(PROFILE_DIR), executable_path=path, **common
            )
        errors = []
        for opts in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
            try:
                return self._pw.chromium.launch_persistent_context(
                    str(PROFILE_DIR), **opts, **common
                )
            except Exception as e:  # そのブラウザが入っていない
                errors.append(f"{opts or '同梱Chromium'}: {str(e).splitlines()[0]}")
        raise RuntimeError(
            "ブラウザを起動できませんでした。Google Chrome をインストールするか、\n"
            "`python -m playwright install chromium` を実行してください。\n  "
            + "\n  ".join(errors)
        )

    def __exit__(self, *exc) -> None:
        if getattr(self, "_browser", None) is not None:
            try:
                self._browser.close()  # 接続を切るだけ
            except Exception:
                pass
        elif self._context is not None:
            self._context.close()
        if getattr(self, "_chrome_proc", None) is not None:
            self._chrome_proc.terminate()
        if self._pw is not None:
            self._pw.stop()

    # ------------------------------------------------------------------
    # ログイン(手動)
    # ------------------------------------------------------------------
    def _ensure_page(self) -> None:
        """ウィンドウ(タブ)が閉じられていたら開き直す。"""
        assert self._context is not None
        if self.page is None or self.page.is_closed():
            try:
                pages = [p for p in self._context.pages if not p.is_closed()]
                self.page = pages[0] if pages else self._context.new_page()
            except Exception as e:
                raise RuntimeError(
                    "ブラウザが閉じられました。スクリプトが開いた Chrome のウィンドウは、"
                    "処理が終わるまで閉じずにそのままにしてください。もう一度実行し直してください。"
                ) from e

    def open_list(self, url: str | None = None) -> None:
        self._ensure_page()
        assert self.page is not None
        self.page.goto(url or self.list_url, wait_until="domcontentloaded")
        self._wait_settled()
        self._row_selector = None
        # 一覧の描画を少し待つ(SPA で後から行が出てくる場合がある)
        for _ in range(10):
            if self._find_row_selector() is not None:
                break
            self.page.wait_for_timeout(500)

    def ensure_logged_in(self) -> None:
        """明細一覧が表示されるまで、手動ログインを待つ。"""
        if getattr(self, "_cdp_pending", False):
            # ログインが終わるまでは一切ブラウザに触らない(普通の Chrome として操作してもらう)
            input(
                "\n🔐 Chrome が開きました。カード明細の一覧が出ていればそのまま Enter。\n"
                "   ログイン画面が出ている場合は、その画面でログインしてから Enter。\n"
                "   ※入力は Chrome の画面で。ここには何も打たないでください\n"
                "   ※Chrome のウィンドウは最後まで閉じないでください\n"
                "   カード明細の一覧が表示されたら、ここで Enter だけ押してください... "
            )
            self._connect_cdp()
        self.open_list()
        while self._find_row_selector() is None:
            input(
                "\n🔐 開いた Chrome のウィンドウで UPSIDER にログインしてください。\n"
                "   ※メールアドレス・パスワードは Chrome の画面に入力します(ここには入力しません)\n"
                "   ※Chrome のウィンドウは最後まで閉じないでください\n"
                "   カード明細の一覧が表示されたら、ここで Enter だけ押してください... "
            )
            self._ensure_page()
            if self.list_url.split("?")[0] not in self.page.url:
                self.open_list()
            if self._find_row_selector() is None:
                ans = input(
                    "   明細の行が見つかりません。このまま続けますか? [y/N] "
                ).strip().lower()
                if ans in ("y", "yes"):
                    break

    # ------------------------------------------------------------------
    # 明細一覧の読み取り
    # ------------------------------------------------------------------
    def _wait_settled(self) -> None:
        assert self.page is not None
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

    def _find_row_selector(self) -> str | None:
        assert self.page is not None
        rows = self.sel["row"]
        for s in [rows] if isinstance(rows, str) else rows:
            try:
                if s == "auto":
                    if self.page.evaluate(_MARK_ROWS_JS, AUTO_ROW_ATTR) > 0:
                        self._row_selector = s
                        return s
                    continue
                if self.page.locator(s).count() > 0:
                    self._row_selector = s
                    return s
            except Exception:
                continue
        return None

    def _rows(self) -> Locator:
        assert self.page is not None
        s = self._row_selector or self._find_row_selector()
        if s == "auto":
            # スクロールで行が増える・再描画されるので毎回付け直す
            self.page.evaluate(_MARK_ROWS_JS, AUTO_ROW_ATTR)
            return self.page.locator(f"[{AUTO_ROW_ATTR}]")
        if s is None:
            raise RuntimeError(
                "明細一覧の行が見つかりません。`--inspect` で画面構造を書き出し、"
                "config.yaml の upsider.selectors.row を調整してください。"
            )
        return self.page.locator(s)

    def _load_all_rows(self) -> None:
        """無限スクロールの一覧に備えて、行数が増えなくなるまでスクロールする。"""
        assert self.page is not None
        last = -1
        for _ in range(30):
            count = self._rows().count()
            if count == last:
                break
            last = count
            self._rows().last.scroll_into_view_if_needed()
            self.page.mouse.wheel(0, 5000)
            self.page.wait_for_timeout(800)
            # 「もっと見る」ボタンがあれば押す
            more = self.page.get_by_role("button", name=re.compile("もっと見る|さらに表示"))
            if more.count() > 0 and more.first.is_visible():
                more.first.click()
                self._wait_settled()

    def list_transactions(
        self, year_month: tuple[int, int] | None, url: str | None = None
    ) -> list[Transaction]:
        """指定URL(省略時は list_url)の明細一覧を読み取る。"""
        url = url or self.list_url
        self.open_list(url)
        if self._find_row_selector() is None:
            return []  # その月は明細なし
        self._load_all_rows()
        texts = self._rows().all_inner_texts()
        txs: list[Transaction] = []
        for i, text in enumerate(texts):
            tx = parse_row_text(
                i,
                text,
                year_month,
                self.sel["receipt_attached_keywords"],
                self.sel.get("receipt_missing_keywords"),
            )
            if tx is not None:
                tx.source_url = url
                txs.append(tx)
        return txs

    # ------------------------------------------------------------------
    # 領収書の添付
    # ------------------------------------------------------------------
    def _locate_row(self, tx: Transaction) -> Locator:
        """一覧から、その明細の行を探し直す(並び替え・再読込に強いようテキストで照合)。"""
        rows = self._rows()
        texts = rows.all_inner_texts()
        if tx.raw in texts:
            return rows.nth(texts.index(tx.raw))
        if tx.index < len(texts):
            return rows.nth(tx.index)
        raise RuntimeError(f"一覧で明細が見つかりません: {tx.label()}")

    def attach_receipt(self, tx: Transaction, file_path: Path) -> None:
        """明細を開いて領収書ファイルをアップロードする。"""
        assert self.page is not None
        page = self.page

        self.open_list(tx.source_url or None)
        self._load_all_rows()
        row = self._locate_row(tx)
        row.scroll_into_view_if_needed()
        before = page.url
        self._return_url = before
        row.click()
        # UPSIDER は明細詳細が別ページ(/transactions/<決済ID>/)。遷移を待つ
        try:
            page.wait_for_url(lambda u: u != before, timeout=10000)
        except Exception:
            pass  # 同じページ内でパネルが開く画面の場合
        self._wait_settled()
        page.wait_for_timeout(800)

        file_inputs = page.locator("input[type='file']")
        if file_inputs.count() > 0:
            # 非表示の input でも set_input_files は使える。最後に出現したもの=詳細画面のもの
            file_inputs.last.set_input_files(str(file_path))
        else:
            button = page.get_by_role(
                "button", name=re.compile(self.sel["upload_button_text"])
            )
            if button.count() == 0:
                button = page.get_by_text(re.compile(self.sel["upload_button_text"]))
            if button.count() == 0:
                raise RuntimeError(
                    "領収書のアップロード欄が見つかりません。明細詳細を開いた状態で "
                    "`--inspect` を実行し、画面構造を確認してください。"
                )
            with page.expect_file_chooser(timeout=10000) as fc:
                button.first.click()
            fc.value.set_files(str(file_path))

        self._wait_settled()
        page.wait_for_timeout(1500)

        # アップロードの確定ボタンがある画面に備える
        confirm = page.get_by_role("button", name=re.compile(r"^(保存|アップロード|登録|確定|OK)$"))
        if confirm.count() > 0 and confirm.first.is_visible():
            confirm.first.click()
            self._wait_settled()

    def close_detail(self) -> None:
        assert self.page is not None
        # 詳細が別ページ(UPSIDER は /transactions/<決済ID>/)なら一覧に戻る
        back = getattr(self, "_return_url", None)
        if back and self.page.url != back:
            self.page.goto(back, wait_until="domcontentloaded")
            self._wait_settled()
            return
        close = self.page.get_by_role(
            "button", name=re.compile(self.sel["close_button_text"])
        )
        if close.count() > 0 and close.first.is_visible():
            close.first.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    # ------------------------------------------------------------------
    # 調査用
    # ------------------------------------------------------------------
    def dump(self, out_prefix: str = "upsider_dump") -> tuple[Path, Path]:
        """今の画面の HTML と、ボタン・入力欄・行候補の一覧を書き出す。"""
        assert self.page is not None
        html_path = Path(f"{out_prefix}.html")
        txt_path = Path(f"{out_prefix}.txt")
        html_path.write_text(self.page.content(), encoding="utf-8")

        info = self.page.evaluate(
            """() => {
              const pick = el => ({
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || '',
                role: el.getAttribute('role') || '',
                testid: el.getAttribute('data-testid') || '',
                cls: (el.className && el.className.baseVal === undefined
                      ? el.className : '').toString().slice(0, 60),
                text: (el.getAttribute('aria-label') || el.innerText || '')
                        .trim().replace(/\\s+/g, ' ').slice(0, 80),
              });
              return {
                controls: [...document.querySelectorAll(
                  'button, input, a[role=button], [role=button]')].map(pick),
                rows: [...document.querySelectorAll(
                  'tr, [role=row], li, [data-testid]')]
                  .filter(el => /[¥￥]|円/.test(el.innerText || ''))
                  .slice(0, 40).map(pick),
              };
            }"""
        )
        lines = [f"URL: {self.page.url}", "", "===== ボタン・入力欄 ====="]
        lines += [
            f"<{c['tag']} type={c['type']!r} role={c['role']!r} "
            f"testid={c['testid']!r} class={c['cls']!r}> {c['text']}"
            for c in info["controls"]
        ]
        lines += ["", "===== 金額を含む行の候補 ====="]
        lines += [
            f"<{c['tag']} role={c['role']!r} testid={c['testid']!r} "
            f"class={c['cls']!r}> {c['text']}"
            for c in info["rows"]
        ]
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        return txt_path, html_path
