"""普段使っている Google Chrome から、UPSIDER のログイン状態をコピーする(Mac)。

スクリプト用の Chrome(専用プロファイル)は普段の Chrome とは別物なので、
そのままだとログインし直しになります。そこで、普段の Chrome のプロファイルのうち
up-sider.com の Cookie を持っているものを探し、ログインに必要なデータ
(Cookie / Local Storage / IndexedDB)だけを専用プロファイルにコピーします。

- 普段の Chrome のデータは「読むだけ」で、一切変更しません。
- Mac の Chrome は Cookie をキーチェーンの鍵で暗号化していますが、同じ Mac・同じ
  Chrome アプリで開くので、コピー先でもそのまま使えます。
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

CHROME_USER_DATA = Path.home() / "Library/Application Support/Google/Chrome"
SITE = "up-sider.com"


def _cookie_count(cookies_db: Path, site: str = SITE) -> int:
    return _cookie_stats(cookies_db, site)[0]


def _cookie_stats(cookies_db: Path, site: str = SITE) -> tuple[int, int]:
    """(Cookie の数, 最後に使われた時刻) を返す。時刻は Chrome 形式(大きいほど新しい)。"""
    try:
        con = sqlite3.connect(f"file:{cookies_db}?mode=ro&immutable=1", uri=True)
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(cookies)")}
            last = "MAX(last_access_utc)" if "last_access_utc" in cols else "0"
            n, t = con.execute(
                f"SELECT COUNT(*), {last} FROM cookies WHERE host_key LIKE ?", (f"%{site}",)
            ).fetchone()
            return int(n or 0), int(t or 0)
        finally:
            con.close()
    except Exception:
        return 0, 0


def find_profile_with_login(user_data: Path = CHROME_USER_DATA, site: str = SITE) -> Path | None:
    """up-sider.com に一番最近アクセスしたプロファイルのフォルダを返す。"""
    if not user_data.exists():
        return None
    best: tuple[tuple[int, int], Path] | None = None
    for prof in sorted(user_data.iterdir()):
        cookies = prof / "Cookies"
        if not cookies.exists():
            cookies = prof / "Network" / "Cookies"
        if not cookies.exists():
            continue
        n, last = _cookie_stats(cookies, site)
        if n and (best is None or (last, n) > best[0]):
            best = ((last, n), prof)
    return best[1] if best else None


def _copy_sqlite(src: Path, dst: Path) -> None:
    """使用中の SQLite でも壊さずにコピーする(読み取り専用で開いてバックアップ)。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    last: Exception | None = None
    # Chrome が起動中でロックされている場合に備え、immutable 指定でも試す
    for mode in ("mode=ro", "mode=ro&immutable=1"):
        try:
            s = sqlite3.connect(f"file:{src}?{mode}", uri=True)
            d = sqlite3.connect(dst)
            try:
                s.backup(d)
                return
            finally:
                s.close()
                d.close()
        except sqlite3.Error as e:
            last = e
    raise RuntimeError(f"{src} を読めませんでした({last})。Chrome を終了してから再実行してください。")


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("LOCK"))


def chrome_is_running() -> bool:
    """普段の Google Chrome が起動しているか(Mac)。"""
    import subprocess

    try:
        out = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True, text=True)
        return out.returncode == 0
    except Exception:
        return False


def import_login(dest_user_data: Path, user_data: Path = CHROME_USER_DATA, site: str = SITE) -> str | None:
    """ログイン状態をコピーする。コピーしたプロファイル名(例: 'Profile 1')を返す。"""
    prof = find_profile_with_login(user_data, site)
    if prof is None:
        return None
    dest = dest_user_data / "Default"
    dest.mkdir(parents=True, exist_ok=True)

    for rel in ("Network/Cookies", "Cookies"):
        if (prof / rel).exists():
            _copy_sqlite(prof / rel, dest / rel)
    if (prof / "Local Storage").exists():
        _copy_tree(prof / "Local Storage", dest / "Local Storage")
    idb = prof / "IndexedDB"
    if idb.exists():
        for d in idb.glob(f"*{site.replace('.', '_')}*"):
            _copy_tree(d, dest / "IndexedDB" / d.name)
    return prof.name
