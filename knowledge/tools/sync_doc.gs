/**
 * 社内ノウハウ抽出 → Googleドキュメント 同期スクリプト
 *
 * GitHub 上の google_doc_body.json を取得し、
 * このスクリプトが紐づいているドキュメントの本文を丸ごと書き換える。
 *
 * 【初回セットアップ】
 *   1. 対象のドキュメントを開く
 *   2. 拡張機能 → Apps Script
 *   3. このファイルの中身をすべて貼り付けて保存
 *   4. 関数 syncNow を選んで実行（初回だけ権限の承認を求められる）
 *   5. 関数 installWeeklyTrigger を実行 → 毎週日曜23時（日本時間）に自動更新される
 *
 * 【注意】実行のたびに本文は全置換される。ドキュメントに直接書いた内容は消える。
 *         メモを残したい場合はコメント機能を使うか、別ドキュメントに書くこと。
 */

var SOURCE_URL =
  'https://raw.githubusercontent.com/y-minami-oss/-/' +
  'claude/internal-knowledge-extraction-8s4sca/' +
  'knowledge/docs/google_doc_body.json';

/** 毎週日曜23時（日本時間）のトリガーを仕掛ける。二重登録はしない。 */
function installWeeklyTrigger() {
  var handler = 'syncNow';
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === handler) ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger(handler)
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(23)
    .inTimezone('Asia/Tokyo')
    .create();
  Logger.log('毎週日曜23:00（JST）の自動更新を設定しました。');
}

/** トリガーを解除する。 */
function removeWeeklyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncNow') ScriptApp.deleteTrigger(t);
  });
  Logger.log('自動更新を解除しました。');
}

/** 本体。取得 → 本文を全置換。 */
function syncNow() {
  var res = UrlFetchApp.fetch(SOURCE_URL, { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) {
    throw new Error('取得に失敗しました（HTTP ' + res.getResponseCode() + '）: ' + SOURCE_URL);
  }
  var items = JSON.parse(res.getContentText());

  var body = DocumentApp.getActiveDocument().getBody();
  body.clear();

  var HEADING = {
    h1: DocumentApp.ParagraphHeading.HEADING1,
    h2: DocumentApp.ParagraphHeading.HEADING2,
    h3: DocumentApp.ParagraphHeading.HEADING3,
    h4: DocumentApp.ParagraphHeading.HEADING4
  };

  for (var i = 0; i < items.length; i++) {
    var it = items[i];

    if (it.s === 'hr') {
      body.appendHorizontalRule();
      continue;
    }

    var el;
    if (it.s === 'li') {
      el = body.appendListItem(it.t).setGlyphType(DocumentApp.GlyphType.BULLET);
      if (it.i) el.setNestingLevel(Math.min(it.i, 3));
    } else if (it.s === 'nli') {
      el = body.appendListItem(it.t).setGlyphType(DocumentApp.GlyphType.NUMBER);
      if (it.i) el.setNestingLevel(Math.min(it.i, 3));
    } else {
      el = body.appendParagraph(it.t);
      if (HEADING[it.s]) el.setHeading(HEADING[it.s]);
    }

    var text = el.editAsText();

    // 引用は左インデントとグレー、表の見出し行は太字にする
    if (it.s === 'q') {
      el.setIndentStart(28).setIndentFirstLine(28);
      if (it.t.length) text.setForegroundColor(0, it.t.length - 1, '#5B6764');
    } else if (it.s === 'th') {
      if (it.t.length) text.setBold(0, it.t.length - 1, true);
    } else if (it.s === 'tr') {
      el.setIndentStart(14);
    }

    // **強調** の範囲を太字に戻す
    if (it.b) {
      for (var j = 0; j < it.b.length; j++) {
        var s = it.b[j][0], e = it.b[j][1] - 1;
        if (e >= s && e < it.t.length) text.setBold(s, e, true);
      }
    }
  }

  body.appendParagraph('')
      .appendText('最終同期：' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm'))
      .setForegroundColor('#5B6764');

  Logger.log('同期しました：' + items.length + ' 段落');
}
