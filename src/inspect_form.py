"""経費入力フォームの構造を調べるための調査ツール(フェーズ2用)。

ブラウザで TeamSpirit の経費画面を開き、入力欄・ボタン・iframe の一覧を
ファイルに書き出します。この出力を見ながら docs/DOM_MAPPING.md に
正しいセレクタを記録し、teamspirit.py の fill_expense_form を完成させます。

使い方(Mac で):
    source .venv/bin/activate
    python -m src.inspect_form

実行するとブラウザが立ち上がります。必要なら手動でログイン/画面遷移し、
経費の「新規入力」画面まで進めてから、ターミナルで Enter を押してください。
そのときの画面構造を form_dump.txt と form_dump.html に保存します。
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from .teamspirit import TeamSpiritClient


def _dump_controls(scope, label: str) -> list[str]:
    """ある scope(page か frame)の入力欄・ボタンを列挙する。"""
    lines = [f"\n===== {label} ====="]
    js = """
    () => {
      const out = [];
      const els = document.querySelectorAll(
        'input, select, textarea, button, a[role=button]'
      );
      for (const el of els) {
        out.push({
          tag: el.tagName,
          type: el.getAttribute('type') || '',
          id: el.id || '',
          name: el.getAttribute('name') || '',
          placeholder: el.getAttribute('placeholder') || '',
          label: (el.getAttribute('aria-label') ||
                  el.title || el.innerText || '').trim().slice(0, 40),
          dataField: el.getAttribute('data-field') || '',
        });
      }
      return out;
    }
    """
    try:
        controls = scope.evaluate(js)
    except Exception as e:  # frame がまだ無い等
        return lines + [f"(取得できませんでした: {e})"]

    for c in controls:
        lines.append(
            f"<{c['tag'].lower()} type={c['type']!r} id={c['id']!r} "
            f"name={c['name']!r} placeholder={c['placeholder']!r} "
            f"label={c['label']!r} data-field={c['dataField']!r}>"
        )
    return lines


def main() -> None:
    load_dotenv()
    out_txt = Path("form_dump.txt")
    out_html = Path("form_dump.html")

    with TeamSpiritClient(show_browser=True) as ts:
        ts.ensure_logged_in()
        ts.open_expense_page()

        print("\nブラウザで経費の『新規入力』画面まで進めてください。")
        input("準備ができたら、このターミナルで Enter を押してください...")

        page = ts.page
        assert page is not None

        lines: list[str] = []
        # メインページの要素
        lines += _dump_controls(page, "メインページ (page)")

        # iframe があれば、その中も調べる
        frames = page.frames
        lines.append(f"\n----- frame 数: {len(frames)} -----")
        for i, fr in enumerate(frames):
            lines.append(f"frame[{i}] url = {fr.url}")
            lines += _dump_controls(fr, f"frame[{i}]")

        out_txt.write_text("\n".join(lines), encoding="utf-8")
        out_html.write_text(page.content(), encoding="utf-8")

        print(f"\n保存しました:\n  - {out_txt} (入力欄・ボタンの一覧)")
        print(f"  - {out_html} (画面のHTML全体)")
        print("この内容を共有してもらえれば、セレクタの特定を一緒に進められます。")


if __name__ == "__main__":
    main()
